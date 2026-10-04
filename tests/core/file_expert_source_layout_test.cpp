// Standalone CPU regression for the file-backed source. No GPU or model is required.
// Build from the repository root (CUDA headers only, no CUDA runtime is linked):
// c++ -std=c++17 -O1 -ffunction-sections -fdata-sections -Iinclude \
//   -I/opt/cuda/targets/x86_64-linux/include \
//   tests/core/file_expert_source_layout_test.cpp src/core/expert_source.cpp \
//   -Wl,--gc-sections -o /tmp/file_expert_source_layout_test
// /tmp/file_expert_source_layout_test
//
// Inject already-validated layouts at the reader boundary. Parsing GGUF formats is
// deliberately outside this test; all file mapping and expert reads use production code.
#include "strata/core/expert_source.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#include <unistd.h>

namespace strata::kernels::cpu {
static ExpertLayout fixture_layout;
const ExpertLayout& expert_layout() { return fixture_layout; }
}

namespace {
using strata::core::FileExpertSource;
using strata::kernels::cpu::BLOB;
using strata::kernels::cpu::fixture_layout;
int failures = 0;
void check(bool ok, const std::string& message) {
    if (!ok) { ++failures; std::fprintf(stderr, "FAIL: %s\n", message.c_str()); }
}
struct Pack {
    std::filesystem::path dir;
    Pack() {
        char name[] = "/tmp/strata-file-source-XXXXXX";
        const char* p = mkdtemp(name);
        if (!p) throw std::runtime_error("mkdtemp failed");
        dir = p;
    }
    ~Pack() { std::error_code ec; std::filesystem::remove_all(dir, ec); }
    void write(const std::vector<uint8_t>& bytes) {
        std::ofstream out(dir / "experts.bin", std::ios::binary | std::ios::trunc);
        out.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());
        if (!out) throw std::runtime_error("fixture write failed");
    }
};
uint8_t pattern(int layer, int expert, size_t byte) {
    return static_cast<uint8_t>(layer * 61 + expert * 29 + byte * 17 + (byte / 251));
}
std::vector<uint8_t> configure(bool native, std::vector<uint64_t> sizes, int experts = 3) {
    fixture_layout = {};
    fixture_layout.native = native;
    fixture_layout.n_layers = sizes.size();
    fixture_layout.n_expert = experts;
    fixture_layout.bytes = sizes;
    fixture_layout.max_blob = *std::max_element(sizes.begin(), sizes.end());
    uint64_t total = 0;
    for (auto size : sizes) {
        fixture_layout.offset.push_back(total);
        total += size * experts;
    }
    fixture_layout.total = total;
    std::vector<uint8_t> data(total);
    for (size_t l = 0; l < sizes.size(); ++l)
        for (int e = 0; e < experts; ++e)
            for (size_t i = 0; i < sizes[l]; ++i)
                data[fixture_layout.offset[l] + e * sizes[l] + i] = pattern(l, e, i);
    return data;
}
void verify_reads(FileExpertSource& source, const std::vector<uint8_t>& data,
                  const std::string& label) {
    const auto& lay = fixture_layout;
    int64_t reads = source.reads();
    for (int64_t l = 0; l < lay.n_layers; ++l) {
        for (int64_t e = 0; e < lay.n_expert; ++e) {
            const auto* p = source.blob(l, e);
            check(p != nullptr, label + ": valid expert pointer");
            if (p) {
                const size_t offset = lay.offset[l] + e * lay.bytes[l];
                // Compare only inside the mapping even against the broken canonical
                // stride; a wrong pointer is a test failure, never an out-of-bounds read.
                const auto* base = source.blob(0, 0);
                ++reads;
                const auto actual_offset = static_cast<size_t>(p - base);
                check(actual_offset == offset, label + ": exact offset layer " +
                      std::to_string(l) + " expert " + std::to_string(e));
                if (actual_offset <= data.size() && lay.bytes[l] <= data.size() - actual_offset)
                    check(std::equal(p, p + lay.bytes[l], data.data() + offset),
                          label + ": byte-exact expert layer " + std::to_string(l) +
                          " expert " + std::to_string(e));
                else check(false, label + ": complete expert must fit inside mapping");
            }
            ++reads;
        }
    }
    check(source.reads() == reads, label + ": reads counter");
    for (auto indices : {std::pair<int64_t,int64_t>{-1, 0}, {0, -1},
                         {lay.n_layers, 0}, {0, lay.n_expert},
                         {lay.n_layers - 1, lay.n_expert},
                         {std::numeric_limits<int64_t>::max(), 0}})
        check(source.blob(indices.first, indices.second) == nullptr, label + ": invalid axes refused");
    check(source.reads() == reads, label + ": invalid reads do not increment counter");
}
void exercise(const std::string& label, bool native, const std::vector<uint64_t>& sizes) {
    Pack pack;
    auto data = configure(native, sizes);
    pack.write(data);
    FileExpertSource source;
    std::string err;
    check(source.blob(0, 0) == nullptr, label + ": unopened source");
    const bool opened = source.open(pack.dir.string(), sizes.size(), 3, err);
    check(opened, label + ": opens valid pack: " + err);
    if (opened) {
        check(source.mapped() && source.blobs() == static_cast<int64_t>(sizes.size() * 3),
              label + ": mapped geometry");
        verify_reads(source, data, label);
        source.close();
        check(!source.mapped() && source.blobs() == 0 && source.reads() == 0,
              label + ": close resets state");
        check(source.blob(0, 0) == nullptr, label + ": closed source");
        source.close();
        check(source.open(pack.dir.string(), sizes.size(), 3, err), label + ": reopen");
        if (source.mapped()) verify_reads(source, data, label + " reopened");
    }
    source.close();
    for (int delta : {-1, 1}) {
        auto wrong = data;
        wrong.resize(data.size() + delta);
        pack.write(wrong);
        err.clear();
        check(!source.open(pack.dir.string(), sizes.size(), 3, err), label + ": size mismatch refused");
        check(!err.empty() && !source.mapped() && source.blob(0, 0) == nullptr,
              label + ": failed open is unreadable with diagnostic");
    }
    pack.write(data);
    check(!source.open(pack.dir.string(), 0, 3, err), label + ": empty layers refused");
    check(!source.open(pack.dir.string(), sizes.size(), 0, err), label + ": empty experts refused");
}
}
int main() {
    try {
        exercise("canonical", false, {BLOB, BLOB});
        // Unlike canonical BLOB, native IQ4 / mixed K-quant formats vary by layer.
        exercise("native unequal total", true, {117, 303, 521});
        // Same total size defeats a fix that updates only the file-size check.
        exercise("native canonical total", true, {BLOB / 2, BLOB, BLOB + BLOB / 2});
    } catch (const std::exception& e) { check(false, e.what()); }
    if (failures) std::fprintf(stderr, "%d assertion(s) failed\n", failures);
    else std::puts("PASS: FileExpertSource canonical/native byte-exact layouts, bounds, size checks and reopen");
    return failures ? 1 : 0;
}
