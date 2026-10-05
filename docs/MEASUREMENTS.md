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
  settings: 5 (UD-IQ4_XS, 1 GPU), 4 (UD-IQ4_XS, 2 GPUs), 6 (UD-Q4_K_XL, 1 GPU), 2 (UD-Q4_K_XL, 2 GPUs).
- Agent sessions: 18 turns through `serve/server.py`, the conversation growing to ~31K tokens (pasted source files,
  docs, topic changes), 600 tokens per answer, three runs per variant.

## Results

Decode speed (tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| es_chat | 86.0 | 114.9 | 62.5 | 86.1 |
| es_think | 87.7 | 113.2 | 69.8 | 81.6 |
| es_doc (after 18K) | 69.9 | 98.1 | 54.8 | 73.7 |
| code | 88.5 | 118.7 | 68.1 | 84.6 |
| edit | 114.8 | 165.2 | 87.9 | 118.1 |
| proto5k (after 5K) | 63.5 | 68.5 | 49.1 | 52.7 |
| **Geometric mean** | **83.6** | **109.4** | **64.2** | **80.5** |

Prompt reading (prefill, tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| 18,076 tokens | 1,787 | 1,800 | 1,702 | 1,716 |
| 5,296 tokens | 1,131 | 1,461 | 869 | 1,066 |
| 3,340 tokens | 811 | 1,036 | 637 | 765 |

- The second GPU adds **+31%** to UD-IQ4_XS and **+25%** to UD-Q4_K_XL (it holds ~14.5 GB more experts and computes
  its share of each layer while the CPU computes its own). It barely changes the 18K prefill, which is bound by the
  3090's x8 link.
- Expert VRAM hit rate: 80.7% / 89.2% (UD-IQ4_XS, 1 / 2 GPUs), 77.8% / 83.3% (UD-Q4_K_XL). Draft acceptance ~89%.
- Agent sessions (one GPU): UD-IQ4_XS 78.1 tok/s, UD-Q4_K_XL 59.9 tok/s.
- UD-IQ4_XS is faster than UD-Q4_K_XL here (+30% on one GPU, +36% on two): fewer bytes per expert, so more of them fit
  in VRAM, and its compute-bound CPU kernels use all 7 workers. UD-Q4_K_XL is the larger quant of the two.

## Long prompts

Prompts of 32K to 200K distinct tokens (prose, then this repo's docs and source code), 128 tokens of answer, one run each.

| Prompt | Read in (prefill tok/s) UD-IQ4_XS 1 / 2 GPUs | UD-Q4_K_XL 1 / 2 GPUs | Decode after: UD-IQ4_XS 1 / 2 GPUs | UD-Q4_K_XL 1 / 2 GPUs |
|---|---:|---:|---:|---:|
| 32,022 tokens | 13.4 s (2,382) / 13.7 s (2,342) | 13.7 s (2,337) / 14.1 s (2,270) | 67.0 / 92.1 | 51.8 / 83.3 |
| 64,022 tokens | 26.6 s (2,410) / 26.3 s (2,437) | 27.0 s (2,368) / 27.1 s (2,359) | 87.0 / 96.8 | 64.3 / 93.3 |
| 120,019 tokens | 50.9 s (2,360) / 49.2 s (2,439) | 51.7 s (2,321) / 51.0 s (2,354) | 61.5 / 98.9 | 47.4 / 68.3 |
| 200,019 tokens | 89.5 s (2,234) / 84.6 s (2,365) | 91.8 s (2,178) / 88.8 s (2,252) | 54.9 / 97.6 | 45.8 / 68.2 |

## With 64 GB of RAM

The same PC with the engine limited to 60 GiB (what a 64 GB PC leaves free) by a systemd cgroup (`MemoryMax=60G`;
the engine's memory and the file cache of the files it reads were all charged to it, and it reached the cap in every
run). UD-Q4_K_XL's 71.7 GiB of experts do not fit: it runs from a pack with `experts.bin` (`iq_pack.py --experts-bin`)
through `--mmap-experts`, reading from the NVMe (Crucial P3 Plus). Before each run the model files were dropped from
the page cache. Runs: UD-IQ4_XS 3 (1 GPU) and 2 (2 GPUs), UD-Q4_K_XL 2 and 1.

| Decode, tokens/s | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| Spanish chat | 83.2 | 95.5 | 24.0 | 33.0 |
| Reasoning | 87.5 | 106.9 | 24.3 | 36.4 |
| After an 18K document | 67.8 | 98.0 | 20.4 | 36.1 |
| Code | 85.3 | 119.5 | 26.2 | 17.6 |
| Edit | 114.8 | 164.8 | 32.7 | 65.0 |
| After a 5K prompt | 61.0 | 68.0 | 10.5 | 5.1 |
| **Geometric mean** | **81.5** | **104.7** | **21.4** | **25.2** |
| **Geometric mean** (128 GB) | 83.6 | 109.4 | 64.2 | 80.5 |

| Prefill, tokens/s | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| 18,076 tokens | 1,619 | 1,177 | 300 | 521 |
| 5,296 tokens | 1,059 | 1,287 | 106 | 188 |
| 3,340 tokens | 676 | 1,038 | 94 | 52 |

Long prompts with 64 GB (one run each): time to read the prompt · decode right after it.

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPUs | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPUs |
|---|---:|---:|---:|---:|
| 32,022 tokens | 13.7 s · 59.5 | 13.6 s · 89.0 | 42.7 s · 17.8 | 44.1 s · 33.1 |
| 64,022 tokens | 26.6 s · 75.9 | 26.2 s · 96.1 | 2.7 min · 22.9 | 1.7 min · 50.0 |
| 120,019 tokens | 51.0 s · 61.0 | 49.0 s · 91.3 | 4.6 min · 2.7 | 72.1 s · 50.2 |
| 200,019 tokens | 89.4 s · 57.1 | 84.3 s · 97.7 | 43.8 min · 6.0 | 2.0 min · 8.2 |

Agent sessions with 64 GB (two runs each): UD-IQ4_XS 76.0 tok/s (128 GB: 78.1), UD-Q4_K_XL
25.1 (128 GB: 59.9).
UD-Q4_K_XL from the NVMe varies a lot between sessions: an earlier one on this PC gave 24.4 (1 GPU) and 37.1 (2 GPUs).

## What the changes on top of eddoursul's `custom` gave

UD-IQ4_XS, one GPU, six-prompt geometric mean:

| Step | tok/s |
|---|---:|
| eddoursul `custom` + #2 + its follow-up + this branch's fixes (five runs) | 77.3 (76.8-77.8) |
| + the IQ4_XS AVX-2 multi-token kernel (Niko1221/Strata) | 78.0 (+1.3%) |
| + the AVX2 gather of the IQ3_S grid (`STRATA_IQ256_GATHER=1`) | 80.9 (+4.9%) |
| + `--adapt-decay 0.92` | 83.3 (+7.7%) |
| + the later additions from upstream's PRs (#863, #851, #606/#838) | 83.6 (+8.2%) |

In the agent sessions the same steps gave 75.0 -> 76.0 -> 77.8 (+3.7%). The gather is bit-exact (the parity tool's
output is identical with and without it); the draft acceptance and the prefill did not change.

`--adapt-decay` on UD-IQ4_XS (one GPU, with the gather; two runs each, the current engine): 0.70 76.8 · 0.85 82.1 · 0.92 83.6 · 0.95 81.0 · 0.97 81.3 · 0.99 70.8
(1.0 is refused since PR #591). With the second GPU 0.92 cancels the gather's gain and
0.95 is -2%, and on UD-Q4_K_XL it gives nothing in the agent sessions, so those configs keep 0.7.

### Later additions (from upstream's open pull requests)

- **q8_1 blocks kept finite** (upstream #606, PR #838, at this fork's five quantizers): a massive activation could turn
  a block's fp16 scale or sum into inf, then NaN, and the model would answer one token forever. The same bits for
  every normal block, no speed cost.
- **The AVX2 gather reorganized** (PR #863 by Hardin22): UD-IQ4_XS on the 3090 83.1 -> 83.6 tok/s (five runs), with both cards
  108.0 -> 109.4 (four runs). Its one-token IQ3_S path stays off on AMD, where ggml's dot is still slightly faster for
  one token (0.322 vs 0.334 ms per expert on the 5700X).
- **An AVX2 Q8_K activation quantizer** (PR #851 by Hardin22): byte-identical to ggml's; no measurable change here.
- **`--adapt-decay` outside (0, 1) refused** (PR #591). UD-Q4_K_XL is unchanged by all four.

Other settings tried on this machine without a gain: more pool workers than 7 (UD-IQ4_XS) or 4 (UD-Q4_K_XL),
`--spec` 3/5/6, `--spec-min-p` 0.3/0.7, `--spec-lookup` 8/24, `--adapt-every 2`, `--adapt-swaps 192` on
UD-Q4_K_XL, `--pcie-frac` above 0.3, the GPUs' stock power limits.

On this SMT CPU the Linux fix in this branch (one pool worker per physical core) took UD-Q4_K_XL on the 3090 from
50.7 tok/s (15 workers on 16 logical processors) to 58.1 (7 workers on 7 cores), before the later tuning.
