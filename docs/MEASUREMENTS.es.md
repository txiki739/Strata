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
  este código y estos ajustes: 5 (UD-IQ4_XS, 1 GPU), 4 (UD-IQ4_XS, 2 GPU), 6 (UD-Q4_K_XL, 1 GPU), 2 (UD-Q4_K_XL, 2 GPU).
- Sesiones de agente: 18 turnos a través de `serve/server.py`, con la conversación creciendo hasta ~31K tokens
  (ficheros de código pegados, documentación, cambios de tema), 600 tokens por respuesta, tres rondas por variante.

## Resultados

Velocidad de generación (tokens/s):

| Texto | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| es_chat | 86,0 | 114,9 | 62,5 | 86,1 |
| es_think | 87,7 | 113,2 | 69,8 | 81,6 |
| es_doc (tras 18K) | 69,9 | 98,1 | 54,8 | 73,7 |
| code | 88,5 | 118,7 | 68,1 | 84,6 |
| edit | 114,8 | 165,2 | 87,9 | 118,1 |
| proto5k (tras 5K) | 63,5 | 68,5 | 49,1 | 52,7 |
| **Media geométrica** | **83,6** | **109,4** | **64,2** | **80,5** |

Lectura del prompt (prefill, tokens/s):

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| 18.076 tokens | 1.787 | 1.800 | 1.702 | 1.716 |
| 5.296 tokens | 1.131 | 1.461 | 869 | 1.066 |
| 3.340 tokens | 811 | 1.036 | 637 | 765 |

- La segunda gráfica suma **+31 %** a UD-IQ4_XS y **+25 %** a UD-Q4_K_XL: guarda ~14,5 GB más de expertos y calcula su
  parte de cada capa mientras la CPU calcula la suya. Apenas cambia el prefill de 18K, limitado por el enlace x8 de la
  3090.
- Aciertos de expertos en VRAM: 80,7 % / 89,2 % (UD-IQ4_XS, 1 / 2 GPU), 77,8 % / 83,3 % (UD-Q4_K_XL). Aceptación de
  los borradores ~89 %.
- Sesiones de agente (una gráfica): UD-IQ4_XS 78,1 tok/s, UD-Q4_K_XL 59,9 tok/s.
- Aquí UD-IQ4_XS es más rápido que UD-Q4_K_XL (+30 % con una gráfica, +36 % con dos): cada experto ocupa menos, así
  que caben más en VRAM, y sus kernels de CPU, limitados por cálculo, aprovechan los 7 workers. UD-Q4_K_XL es el
  cuantizado más grande de los dos.

## Prompts largos

Prompts de 32K a 200K tokens distintos (prosa, luego la documentación y el código de este repositorio), 128 tokens de respuesta,
una ronda cada uno.

| Prompt | Lectura (prefill tok/s) UD-IQ4_XS 1 / 2 GPU | UD-Q4_K_XL 1 / 2 GPU | Generación después: UD-IQ4_XS 1 / 2 GPU | UD-Q4_K_XL 1 / 2 GPU |
|---|---:|---:|---:|---:|
| 32.022 tokens | 13,4 s (2.382) / 13,7 s (2.342) | 13,7 s (2.337) / 14,1 s (2.270) | 67,0 / 92,1 | 51,8 / 83,3 |
| 64.022 tokens | 26,6 s (2.410) / 26,3 s (2.437) | 27,0 s (2.368) / 27,1 s (2.359) | 87,0 / 96,8 | 64,3 / 93,3 |
| 120.019 tokens | 50,9 s (2.360) / 49,2 s (2.439) | 51,7 s (2.321) / 51,0 s (2.354) | 61,5 / 98,9 | 47,4 / 68,3 |
| 200.019 tokens | 89,5 s (2.234) / 84,6 s (2.365) | 91,8 s (2.178) / 88,8 s (2.252) | 54,9 / 97,6 | 45,8 / 68,2 |

## Con 64 GB de RAM

El mismo PC con el motor limitado a 60 GiB (lo que deja libre un PC de 64 GB) con un cgroup de systemd (`MemoryMax=60G`;
la memoria del motor y la caché de disco de los ficheros que lee contaban en él, y llegó al techo en todas las rondas).
Los 71,7 GiB de expertos de UD-Q4_K_XL no caben: va con un pack con `experts.bin` (`iq_pack.py --experts-bin`) y
`--mmap-experts`, leyendo del NVMe (Crucial P3 Plus). Antes de cada ronda se vaciaba la caché de los ficheros del modelo.
Rondas: UD-IQ4_XS 3 (1 GPU) y 2 (2 GPU), UD-Q4_K_XL 2 y 1.

| Generación, tokens/s | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| Chat en español | 83,2 | 95,5 | 24,0 | 33,0 |
| Razonamiento | 87,5 | 106,9 | 24,3 | 36,4 |
| Tras un documento de 18K | 67,8 | 98,0 | 20,4 | 36,1 |
| Código | 85,3 | 119,5 | 26,2 | 17,6 |
| Edición | 114,8 | 164,8 | 32,7 | 65,0 |
| Tras un prompt de 5K | 61,0 | 68,0 | 10,5 | 5,1 |
| **Media geométrica** | **81,5** | **104,7** | **21,4** | **25,2** |
| **Media geométrica** (128 GB) | 83,6 | 109,4 | 64,2 | 80,5 |

| Prefill, tokens/s | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| 18.076 tokens | 1.619 | 1.177 | 300 | 521 |
| 5.296 tokens | 1.059 | 1.287 | 106 | 188 |
| 3.340 tokens | 676 | 1.038 | 94 | 52 |

Prompts largos con 64 GB (una ronda cada uno): tiempo de lectura del prompt · generación justo después.

| Prompt | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| 32.022 tokens | 13,7 s · 59,5 | 13,6 s · 89,0 | 42,7 s · 17,8 | 44,1 s · 33,1 |
| 64.022 tokens | 26,6 s · 75,9 | 26,2 s · 96,1 | 2,7 min · 22,9 | 1,7 min · 50,0 |
| 120.019 tokens | 51,0 s · 61,0 | 49,0 s · 91,3 | 4,6 min · 2,7 | 72,1 s · 50,2 |
| 200.019 tokens | 89,4 s · 57,1 | 84,3 s · 97,7 | 43,8 min · 6,0 | 2,0 min · 8,2 |

Sesiones de agente con 64 GB (dos rondas cada una): UD-IQ4_XS 76,0 tok/s (128 GB: 78,1), UD-Q4_K_XL
25,1 (128 GB: 59,9).
UD-Q4_K_XL desde el NVMe varía mucho entre sesiones: una anterior en este PC dio 24,4 (1 GPU) y 37,1 (2 GPU).

## Lo que han aportado los cambios sobre `custom` de eddoursul

UD-IQ4_XS con una gráfica, media geométrica de los seis textos:

| Paso | tok/s |
|---|---:|
| `custom` de eddoursul + #2 + su continuación + los arreglos de esta rama (cinco rondas) | 77,3 (76,8-77,8) |
| + el kernel IQ4_XS AVX-2 multi-token (Niko1221/Strata) | 78,0 (+1,3 %) |
| + el gather AVX2 de la tabla de IQ3_S (`STRATA_IQ256_GATHER=1`) | 80,9 (+4,9 %) |
| + `--adapt-decay 0.92` | 83,3 (+7,7 %) |
| + los añadidos posteriores de PR del original (#863, #851, #606/#838) | 83,6 (+8,2 %) |

En las sesiones de agente los mismos pasos dieron 75,0 -> 76,0 -> 77,8 (+3,7 %). El gather da exactamente los mismos
números (la herramienta de paridad sale idéntica con y sin él); la aceptación y el prefill no cambiaron.

`--adapt-decay` en UD-IQ4_XS (una gráfica, con el gather; dos rondas cada uno, el motor actual): 0,7 76,8 · 0,85 82,1 · 0,92 83,6 · 0,95 81,0 · 0,97 81,3 · 0,99 70,8
(el 1,0 se rechaza desde el PR #591). Con la segunda gráfica 0,92 anula la ganancia del gather y
0,95 da -2 %, y en UD-Q4_K_XL no aporta en las sesiones de agente, así que esas configuraciones se quedan en 0,7.

### Añadidos posteriores (de pull requests abiertos del motor original)

- **Bloques q8_1 siempre finitos** (#606 y PR #838 del original, en los cinco cuantizadores de este fork): una
  activación enorme podía convertir en infinito la escala o la suma fp16 de un bloque, luego en NaN, y el modelo se
  quedaba repitiendo un token. Los mismos bits en todo bloque normal, sin coste de velocidad.
- **El gather AVX2 reorganizado** (PR #863 de Hardin22): UD-IQ4_XS con la 3090 83,1 -> 83,6 tok/s (cinco rondas), con las dos
  108,0 -> 109,4 (cuatro rondas). Su camino de un solo token para IQ3_S sigue apagado en AMD, donde el dot de ggml aún es
  algo más rápido para un token (0,322 frente a 0,334 ms por experto en el 5700X).
- **Un cuantizador AVX2 de activaciones Q8_K** (PR #851 de Hardin22): los mismos bytes que el de ggml; aquí no se nota.
- **`--adapt-decay` fuera de (0, 1) rechazado** (PR #591). UD-Q4_K_XL no cambia con ninguno de los cuatro.

Otros ajustes probados en este equipo sin ganancia: más workers que 7 (UD-IQ4_XS) o 4 (UD-Q4_K_XL), `--spec` 3/5/6,
`--spec-min-p` 0,3/0,7, `--spec-lookup` 8/24, `--adapt-every 2`, `--adapt-swaps 192` en UD-Q4_K_XL,
`--pcie-frac` por encima de 0,3 y las gráficas a su potencia de serie.

En esta CPU con SMT, el arreglo de Linux de esta rama (un worker por núcleo físico) llevó UD-Q4_K_XL con la 3090 de
50,7 tok/s (15 workers en 16 procesadores lógicos) a 58,1 (7 workers en 7 núcleos), antes del resto del afinado.
