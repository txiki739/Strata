# Configs for a Ryzen 7 5700X + RTX 3090 + RTX 5060 Ti (Linux)

The configs measured in [docs/MEASUREMENTS.md](../../docs/MEASUREMENTS.md), for `serve/server.py`:

- `ud-iq4_xs-3090.json`: unsloth's UD-IQ4_XS on the RTX 3090 alone (83 tok/s).
- `ud-iq4_xs-dual.json`: the same with the RTX 5060 Ti as a second expert tier (108 tok/s).
- `ud-q4_k_xl-3090.json` / `ud-q4_k_xl-dual.json`: unsloth's UD-Q4_K_XL (65 / 81 tok/s; with 64 GB of RAM it reads its experts from the NVMe: 24 / 37).

Their paths are relative to the Strata folder and follow setup's data layout (`../Strata-data`).

1. Build the engine from this branch for both cards (`86;120` is an RTX 30 card and an RTX 50 card):

       cmake -G Ninja -S . -B build -DCMAKE_BUILD_TYPE=Release -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF \
         "-DCMAKE_CUDA_ARCHITECTURES=86;120"
       cmake --build build --target strata

2. Download the model files into `../Strata-data/models/UD-IQ4_XS` (three `Qwen3.8-Flash-Next-UD-IQ4_XS-0000N-of-00003.gguf`)
   and/or `../Strata-data/models/UD-Q4_K_XL` (four files), and make each pack:

       .venv/bin/python tools/iq_pack.py --out ../Strata-data/packs/ud-iq4_xs \
         --gguf ../Strata-data/models/UD-IQ4_XS/Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf

3. The MTP draft layer: setup makes it in `../Strata-data/mtp/rt`. These configs use a copy with the Spanish draft
   vocabulary (`data/draft_vocab_es.bin`, see `tools/draft_vocab.py`); for English and code `mtp/rt` works as well:

       mkdir ../Strata-data/mtp/rt-es && cd ../Strata-data/mtp/rt-es
       ln -s ../rt/dense.bin ../rt/dense.txt ../rt/experts.bin .
       cp <Strata folder>/data/draft_vocab_es.bin draft_vocab.bin

4. GPU numbers are `nvidia-smi`'s: here the RTX 5060 Ti is 0 and the RTX 3090 is 1 (`--main-gpu 1`,
   `--second-gpu 0`). Change them to your cards'. The dual configs need the second card free (~15 GB).

5. Start it: `.venv/bin/python serve/server.py --engine strata --config examples/r7-5700x/ud-iq4_xs-3090.json --port 8092`
   (an OpenAI-compatible API at `http://127.0.0.1:8092/v1`, and the web page at `/`).

`STRATA_IQ256_GATHER=1` (in the IQ4_XS configs' `env`) assembles the IQ3_S grid with an AVX2 gather: +5% here on Zen 3.
It is opt-in upstream because the gather's speed depends on the CPU; measure it on yours.
