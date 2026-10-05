# Measurements: Ryzen 7 5700X + RTX 3090 + RTX 5060 Ti (Linux)

Speeds of this branch (`custom-plus`) with unsloth's UD-IQ4_XS and UD-Q4_K_XL, on one GPU and on two. The configs
are in [examples/r7-5700x](../examples/r7-5700x/). Spanish version: [MEASUREMENTS.es.md](MEASUREMENTS.es.md).

## The machine

| | |
|---|---|
| CPU | AMD Ryzen 7 5700X: 8 cores / 16 threads, Zen 3, AVX2 (no AVX-512) |
| RAM | 128 GB DDR4-3200 CL22 (4 x 32 GB), ~36 GB/s read (STREAM) |
| Main GPU | NVIDIA RTX 3090 24 GB, PCIe 4.0 x8, power limit 250 W |
| Second GPU (expert tier) | NVIDIA RTX 5060 Ti 16 GB, PCIe 4.0 x8, power limit 150 W |
| Software | Linux (kernel 7.2), NVIDIA driver 615.71, CUDA 13.4, engine built with `CMAKE_CUDA_ARCHITECTURES=86;120` |

At the cards' stock power limits (350 W and 180 W) the speeds were the same (UD-Q4_K_XL: 63.5 -> 63.8 tok/s on the
3090, 80.9 -> 80.3 with both cards): the engine is bound by the CPU, the RAM and PCIe, not by the GPUs' power.

## The models

Qwen3.8-Flash-Next (48 layers x 512 routed experts), unsloth's GGUF files. The experts stay in RAM and the engine
keeps the most used ones in VRAM (an adaptive cache); the CPU computes the rest.

| | UD-IQ4_XS | UD-Q4_K_XL |
|---|---|---|
| GGUF files | 3 | 4 |
| Expert weights | 55.4 GiB | 71.7 GiB |
| Expert formats (gate/up · down) | IQ3_S (47 layers), IQ4_XS (1) · IQ4_NL (43), Q8_0 (5) | Q4_K (47), Q5_K (1) · Q5_1 (43), Q8_0 (5) |
| RAM taken by the engine | ~58 GiB | ~81 GB |
| CPU expert kernels | compute-bound: scale with cores | bandwidth-bound: DDR4 saturates at ~4 cores |

Both: 200,192 tokens of context, int8 KV cache, the MTP draft layer with a Spanish draft vocabulary
(`data/draft_vocab_es.bin`) plus prompt lookup, greedy verification (the speculation never changes the output).

## Settings

| | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| `--pool-workers` | 7 | 7 | 4 | 4 |
| `--adapt-swaps` | 192 | 192 | 96 | 96 |
| `--adapt-decay` | 0.92 | 0.7 | 0.7 | 0.7 |
| `STRATA_IQ256_GATHER` | 1 | 1 | - | - |
| `--pcie-frac` (kernel) | 0 | 0 | 0.3 | 0 |
| Second GPU | - | `--second-gpu 0`, 512 MiB reserve, 6 MB prefetch, `--head-split 0.45` | - | same as IQ4_XS |

## How it was measured

- The engine driven through its own `--serve` protocol, prompt cache off (every prompt read in full), greedy,
  speculation on (`--spec 4 --spec-lookup 16`).
- Six fixed prompts, mostly in Spanish: `es_chat` (71-token question, 400 tokens out), `es_think` (133 tokens, 700
  out, reasoning on), `es_doc` (an 18,076-token document, then 400 out), `code` (62 tokens, 600 out), `edit` (a
  3,340-token script returned edited, ~2,600 out), `proto5k` (a 5,296-token prompt, 256 out). The long texts are
  private notes and are not published.
- Decode speed = the geometric mean of the six; each config is the mean of every run of this code and these
  settings: 4 (UD-IQ4_XS, 1 GPU), 6 (UD-IQ4_XS, 2 GPUs), 4 (UD-Q4_K_XL, 1 GPU), 3 (UD-Q4_K_XL, 2 GPUs).
- Agent sessions: 18 turns through `serve/server.py`, the conversation growing to ~31K tokens (pasted source files,
  docs, topic changes), 600 tokens per answer, three runs per variant.

## Results

Decode speed (tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| es_chat | 85.9 | 112.7 | 62.8 | 87.3 |
| es_think | 88.5 | 111.0 | 74.8 | 80.4 |
| es_doc (after 18K) | 70.0 | 99.1 | 54.7 | 72.7 |
| code | 87.4 | 119.5 | 67.6 | 84.1 |
| edit | 113.8 | 161.6 | 87.9 | 117.7 |
| proto5k (after 5K) | 62.4 | 66.4 | 48.8 | 53.8 |
| **Geometric mean** | **83.1** | **108.0** | **64.9** | **80.5** |

Prompt reading (prefill, tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| 18,076 tokens | 1,800 | 1,813 | 1,699 | 1,730 |
| 5,296 tokens | 1,131 | 1,463 | 869 | 1,067 |
| 3,340 tokens | 811 | 1,030 | 638 | 758 |

- The second GPU adds **+30%** to UD-IQ4_XS and **+24%** to UD-Q4_K_XL (it holds ~14.5 GB more experts and computes
  its share of each layer while the CPU computes its own). It barely changes the 18K prefill, which is bound by the
  3090's x8 link.
- Expert VRAM hit rate: 80.8% / 89.1% (UD-IQ4_XS, 1 / 2 GPUs), 77.8% / 83.4% (UD-Q4_K_XL). Draft acceptance ~89%.
- Agent sessions (one GPU): UD-IQ4_XS 77.8 tok/s, UD-Q4_K_XL 59.7 tok/s.
- UD-IQ4_XS is faster than UD-Q4_K_XL here (+28% on one GPU, +34% on two): fewer bytes per expert, so more of them fit
  in VRAM, and its compute-bound CPU kernels use all 7 workers. UD-Q4_K_XL is the larger quant of the two.

## With 64 GB of RAM

The same PC with the engine limited to 60 GiB (what a 64 GB PC leaves free), its file cache included, by a systemd
cgroup (`MemoryMax=60G`; the engine's memory and the mapped files were all charged to it). UD-Q4_K_XL's 71.7 GiB of
experts do not fit: it runs from a pack with `experts.bin` (`iq_pack.py --experts-bin`) through `--mmap-experts`,
reading from the NVMe (Crucial P3 Plus).

| 64 GB of RAM | Decode | Prefill 18K / 5K / 3K | Cache hits | With 128 GB |
|---|---:|---:|---:|---:|
| UD-IQ4_XS, 1 GPU | 83.5 | 1,790 / 1,132 / 813 | 81% | 83.1 |
| UD-IQ4_XS, 2 GPUs | 107.5 | 1,804 / 1,460 / 1,033 | 89% | 108.0 |
| UD-Q4_K_XL, 1 GPU (2 runs) | 24.4 | 432 / 154 / 133 | 54% | 64.9 |
| UD-Q4_K_XL, 2 GPUs | 37.1 | 532 / 195 / 155 | 78% | 80.5 |

## What the changes on top of eddoursul's `custom` gave

UD-IQ4_XS, one GPU, six-prompt geometric mean:

| Step | tok/s |
|---|---:|
| eddoursul `custom` + #2 + its follow-up + this branch's fixes (five runs) | 77.3 (76.8-77.8) |
| + the IQ4_XS AVX-2 multi-token kernel (Niko1221/Strata) | 78.0 (+1.3%) |
| + the AVX2 gather of the IQ3_S grid (`STRATA_IQ256_GATHER=1`) | 80.9 (+4.9%) |
| + `--adapt-decay 0.92` | 83.3 (+7.7%) |

In the agent sessions the same steps gave 75.0 -> 76.0 -> 77.8 (+3.7%). The gather is bit-exact (the parity tool's
output is identical with and without it); the draft acceptance and the prefill did not change.

`--adapt-decay` on UD-IQ4_XS (one GPU, with the gather): 0.85 81.2 · 0.92 82.4 · 0.95 82.6 · 0.97 81.1 ·
0.99 71.6 · 1.0 57.1 (the cache stops following the text). With the second GPU 0.92 cancels the gather's gain and
0.95 is -2%, and on UD-Q4_K_XL it gives nothing in the agent sessions, so those configs keep 0.7.

Other settings tried on this machine without a gain: more pool workers than 7 (UD-IQ4_XS) or 4 (UD-Q4_K_XL),
`--spec` 3/5/6, `--spec-min-p` 0.3/0.7, `--spec-lookup` 8/24, `--adapt-every 2`, `--adapt-swaps 192` on
UD-Q4_K_XL, `--pcie-frac` above 0.3, the GPUs' stock power limits.

On this SMT CPU the Linux fix in this branch (one pool worker per physical core) took UD-Q4_K_XL on the 3090 from
50.7 tok/s (15 workers on 16 logical processors) to 58.1 (7 workers on 7 cores), before the later tuning.
