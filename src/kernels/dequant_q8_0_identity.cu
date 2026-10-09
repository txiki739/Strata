// src/kernels/dequant_q8_0_identity.cu - the coalesced Q8_0 dequant (upstream #1720) against the per-block kernel it
// replaces: an output 16-byte aligned takes the new kernel, one shifted by an element takes the old one, and the
// two must be the same bytes in BF16, FP16 and FP32.  Prints each path's time.  Exit 0 when all three match.
#include "strata/kernels/dequant_bf16.hpp"
#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include <cstdio>
#include <cstring>
#include <random>
#include <vector>

int main() {
    const int64_t rows = 3072, cols = 2560, gpr = cols / 32, rb = gpr * 34;
    std::vector<uint8_t> h((size_t) (rows * rb));
    std::mt19937 rng(7);
    for (int64_t r = 0; r < rows; ++r)
        for (int64_t g = 0; g < gpr; ++g) {
            uint8_t* b = h.data() + r * rb + g * 34;
            const __half d = __float2half((float) (rng() % 20000) / 1e6f + 1e-4f);
            std::memcpy(b, &d, 2);
            for (int k = 0; k < 32; ++k) b[2 + k] = (uint8_t) rng();
        }
    uint8_t* db = nullptr;
    if (cudaMalloc(&db, h.size()) != cudaSuccess) { std::fprintf(stderr, "no device memory\n"); return 2; }
    cudaMemcpy(db, h.data(), h.size(), cudaMemcpyHostToDevice);
    const size_t n = (size_t) (rows * cols);
    auto run = [&](int kind, uint8_t* out) {
        if (kind == 0) strata::kernels::dequant_bf16(8, db, 0, rows, cols, (uint16_t*) out, nullptr);
        if (kind == 1) strata::kernels::dequant_f16(8, db, 0, rows, cols, (uint16_t*) out, nullptr);
        if (kind == 2) strata::kernels::dequant_f32(8, db, 0, rows, cols, (float*) out, nullptr);
    };
    int bad = 0;
    for (int kind = 0; kind < 3; ++kind) {
        const size_t es = kind == 2 ? 4 : 2;
        uint8_t* o = nullptr;
        cudaMalloc(&o, (n + 16) * es);
        std::vector<uint8_t> a(n * es), b(n * es);
        float ms[2] = {0, 0};
        cudaEvent_t e0, e1;
        cudaEventCreate(&e0);
        cudaEventCreate(&e1);
        for (int pass = 0; pass < 2; ++pass) {   // pass 1: misaligned, the old kernel
            uint8_t* out = o + (pass ? es : 0);
            cudaMemset(o, 0, (n + 16) * es);
            run(kind, out);
            cudaDeviceSynchronize();
            cudaMemcpy(pass ? b.data() : a.data(), out, n * es, cudaMemcpyDeviceToHost);
            cudaEventRecord(e0);
            for (int it = 0; it < 50; ++it) run(kind, out);
            cudaEventRecord(e1);
            cudaEventSynchronize(e1);
            cudaEventElapsedTime(&ms[pass], e0, e1);
        }
        const bool same = std::memcmp(a.data(), b.data(), n * es) == 0;
        bad += same ? 0 : 1;
        std::printf("%s: %s | coalesced %.3f ms, per block %.3f ms (x%.1f)\n",
                    kind == 0 ? "BF16" : kind == 1 ? "FP16" : "FP32", same ? "identical" : "DIFFERENT", ms[0] / 50,
                    ms[1] / 50, ms[1] / ms[0]);
        cudaEventDestroy(e0);
        cudaEventDestroy(e1);
        cudaFree(o);
    }
    cudaFree(db);
    return bad;
}
