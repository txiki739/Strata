# Mediciones: Ryzen 7 5700X + RTX 3090 + RTX 5060 Ti (Linux)

Velocidades de esta rama (`custom-plus`) con UD-IQ4_XS y UD-Q4_K_XL de unsloth, con una gráfica y con dos. Las
configuraciones están en [examples/r7-5700x](../examples/r7-5700x/). English version: [MEASUREMENTS.md](MEASUREMENTS.md).

## El equipo

| | |
|---|---|
| CPU | AMD Ryzen 7 5700X: 8 núcleos / 16 hilos, Zen 3, AVX2 (sin AVX-512) |
| RAM | 128 GB DDR4-3200 CL22 (4 x 32 GB), ~36 GB/s de lectura (STREAM) |
| Gráfica principal | NVIDIA RTX 3090 24 GB, PCIe 4.0 x8, límite de potencia 250 W |
| Segunda gráfica (nivel de expertos) | NVIDIA RTX 5060 Ti 16 GB, PCIe 4.0 x8, límite de potencia 150 W |
| Software | Linux (kernel 7.2), driver NVIDIA 615.71, CUDA 13.4, motor compilado con `CMAKE_CUDA_ARCHITECTURES=86;120` |

Con las gráficas a su potencia de serie (350 W y 180 W) las velocidades fueron las mismas (UD-Q4_K_XL: 63,5 -> 63,8
tok/s con la 3090, 80,9 -> 80,3 con las dos): al motor lo limitan la CPU, la RAM y el PCIe, no la potencia.

## Los modelos

Qwen3.8-Flash-Next (48 capas x 512 expertos), ficheros GGUF de unsloth. Los expertos viven en RAM y el motor guarda
en VRAM los más usados (una caché adaptativa); la CPU calcula el resto.

| | UD-IQ4_XS | UD-Q4_K_XL |
|---|---|---|
| Ficheros GGUF | 3 | 4 |
| Pesos de los expertos | 55,4 GiB | 71,7 GiB |
| Formatos de los expertos (gate/up · down) | IQ3_S (47 capas), IQ4_XS (1) · IQ4_NL (43), Q8_0 (5) | Q4_K (47), Q5_K (1) · Q5_1 (43), Q8_0 (5) |
| RAM que ocupa el motor | ~58 GiB | ~81 GB |
| Kernels de CPU de los expertos | limitados por cálculo: escalan con los núcleos | limitados por ancho de banda: la DDR4 se satura con ~4 núcleos |

En los dos: 200.192 tokens de contexto, caché KV int8, la capa de borrador MTP con vocabulario español
(`data/draft_vocab_es.bin`) y búsqueda en el prompt, verificación greedy (la especulación nunca cambia la salida).

## Ajustes

| | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| `--pool-workers` | 7 | 7 | 4 | 4 |
| `--adapt-swaps` | 192 | 192 | 96 | 96 |
| `--adapt-decay` | 0,92 | 0,7 | 0,7 | 0,7 |
| `STRATA_IQ256_GATHER` | 1 | 1 | - | - |
| `--pcie-frac` (kernel) | 0 | 0 | 0,3 | 0 |
| Segunda GPU | - | `--second-gpu 0`, reserva 512 MiB, prefetch 6 MB, `--head-split 0.45` | - | igual que IQ4_XS |

## Cómo se ha medido

- El motor directamente por su protocolo `--serve`, sin caché de prompt (cada prompt se lee entero), greedy, con
  especulación (`--spec 4 --spec-lookup 16`).
- Seis textos fijos, casi todos en español: `es_chat` (pregunta de 71 tokens, 400 de respuesta), `es_think` (133
  tokens, 700 de respuesta, con razonamiento), `es_doc` (un documento de 18.076 tokens y 400 de respuesta), `code`
  (62 tokens, 600 de respuesta), `edit` (un script de 3.340 tokens devuelto editado, ~2.600), `proto5k` (un prompt
  de 5.296 tokens, 256 de respuesta). Los textos largos son notas privadas y no se publican.
- Velocidad de generación = media geométrica de los seis; cada configuración es la media de todas las rondas de
  este código y estos ajustes: 4 (UD-IQ4_XS, 1 GPU), 6 (UD-IQ4_XS, 2 GPU), 4 (UD-Q4_K_XL, 1 GPU), 3 (UD-Q4_K_XL, 2 GPU).
- Sesiones de agente: 18 turnos a través de `serve/server.py`, con la conversación creciendo hasta ~31K tokens
  (ficheros de código pegados, documentación, cambios de tema), 600 tokens por respuesta, tres rondas por variante.

## Resultados

Velocidad de generación (tokens/s):

| Texto | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| es_chat | 85,9 | 112,7 | 62,8 | 87,3 |
| es_think | 88,5 | 111,0 | 74,8 | 80,4 |
| es_doc (tras 18K) | 70,0 | 99,1 | 54,7 | 72,7 |
| code | 87,4 | 119,5 | 67,6 | 84,1 |
| edit | 113,8 | 161,6 | 87,9 | 117,7 |
| proto5k (tras 5K) | 62,4 | 66,4 | 48,8 | 53,8 |
| **Media geométrica** | **83,1** | **108,0** | **64,9** | **80,5** |

Lectura del prompt (prefill, tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| 18.076 tokens | 1.800 | 1.813 | 1.699 | 1.730 |
| 5.296 tokens | 1.131 | 1.463 | 869 | 1.067 |
| 3.340 tokens | 811 | 1.030 | 638 | 758 |

- La segunda gráfica suma **+30 %** a UD-IQ4_XS y **+24 %** a UD-Q4_K_XL: guarda ~14,5 GB más de expertos y calcula su
  parte de cada capa mientras la CPU calcula la suya. Apenas cambia el prefill de 18K, limitado por el enlace x8 de la
  3090.
- Aciertos de expertos en VRAM: 80,8 % / 89,1 % (UD-IQ4_XS, 1 / 2 GPU), 77,8 % / 83,4 % (UD-Q4_K_XL). Aceptación de
  los borradores ~89 %.
- Sesiones de agente (una gráfica): UD-IQ4_XS 77,8 tok/s, UD-Q4_K_XL 59,7 tok/s.
- Aquí UD-IQ4_XS es más rápido que UD-Q4_K_XL (+28 % con una gráfica, +34 % con dos): cada experto ocupa menos, así
  que caben más en VRAM, y sus kernels de CPU, limitados por cálculo, aprovechan los 7 workers. UD-Q4_K_XL es el
  cuantizado más grande de los dos.

## Con 64 GB de RAM

El mismo PC con el motor limitado a 60 GiB (lo que deja libre un PC de 64 GB), caché de disco incluida, con un cgroup de
systemd (`MemoryMax=60G`; toda la memoria del motor y los ficheros mapeados contaban en él). Los 71,7 GiB de expertos de
UD-Q4_K_XL no caben: va con un pack con `experts.bin` (`iq_pack.py --experts-bin`) y `--mmap-experts`, leyendo del NVMe
(Crucial P3 Plus).

| 64 GB de RAM | Generación | Prefill 18K / 5K / 3K | Aciertos de caché | Con 128 GB |
|---|---:|---:|---:|---:|
| UD-IQ4_XS, 1 GPU | 83,5 | 1.790 / 1.132 / 813 | 81 % | 83,1 |
| UD-IQ4_XS, 2 GPU | 107,5 | 1.804 / 1.460 / 1.033 | 89 % | 108,0 |
| UD-Q4_K_XL, 1 GPU (2 rondas) | 24,4 | 432 / 154 / 133 | 54 % | 64,9 |
| UD-Q4_K_XL, 2 GPU | 37,1 | 532 / 195 / 155 | 78 % | 80,5 |

## Lo que han aportado los cambios sobre `custom` de eddoursul

UD-IQ4_XS con una gráfica, media geométrica de los seis textos:

| Paso | tok/s |
|---|---:|
| `custom` de eddoursul + #2 + su continuación + los arreglos de esta rama (cinco rondas) | 77,3 (76,8-77,8) |
| + el kernel IQ4_XS AVX-2 multi-token (Niko1221/Strata) | 78,0 (+1,3 %) |
| + el gather AVX2 de la tabla de IQ3_S (`STRATA_IQ256_GATHER=1`) | 80,9 (+4,9 %) |
| + `--adapt-decay 0.92` | 83,3 (+7,7 %) |

En las sesiones de agente los mismos pasos dieron 75,0 -> 76,0 -> 77,8 (+3,7 %). El gather da exactamente los mismos
números (la herramienta de paridad sale idéntica con y sin él); la aceptación y el prefill no cambiaron.

`--adapt-decay` en UD-IQ4_XS (una gráfica, con el gather): 0,85 81,2 · 0,92 82,4 · 0,95 82,6 · 0,97 81,1 ·
0,99 71,6 · 1,0 57,1 (la caché deja de seguir el texto). Con la segunda gráfica 0,92 anula la ganancia del gather y
0,95 da -2 %, y en UD-Q4_K_XL no aporta en las sesiones de agente, así que esas configuraciones se quedan en 0,7.

Otros ajustes probados en este equipo sin ganancia: más workers que 7 (UD-IQ4_XS) o 4 (UD-Q4_K_XL), `--spec` 3/5/6,
`--spec-min-p` 0,3/0,7, `--spec-lookup` 8/24, `--adapt-every 2`, `--adapt-swaps 192` en UD-Q4_K_XL,
`--pcie-frac` por encima de 0,3 y las gráficas a su potencia de serie.

En esta CPU con SMT, el arreglo de Linux de esta rama (un worker por núcleo físico) llevó UD-Q4_K_XL con la 3090 de
50,7 tok/s (15 workers en 16 procesadores lógicos) a 58,1 (7 workers en 7 núcleos), antes del resto del afinado.
