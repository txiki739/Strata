<h1 align="center">Strata en un Ryzen 7 5700X + RTX 3090 + RTX 5060 Ti</h1>

<p align="center"><b>Qwen3.8-Flash-Next 125B (MoE) en un PC de escritorio: 83 tokens/s con una RTX 3090 y 108 tokens/s con una RTX 5060 Ti al lado</b><br>
UD-IQ4_XS y UD-Q4_K_XL de unsloth · 128 GB DDR4 · Linux · <a href="README.md">in English</a></p>

Esta es la rama `custom` de [eddoursul/Strata](https://github.com/eddoursul/Strata), un fork de
[Niko1221/Strata](https://github.com/Niko1221/Strata) afinado para una RTX 3090 con una segunda gráfica como nivel de
expertos, más algunos arreglos y varios cambios recientes del motor original, medida en un solo equipo con una gráfica
y con dos. El README original de Strata (qué es, instalación, todas las opciones) está en
[STRATA-README.md](STRATA-README.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/summary-dark.svg">
  <img alt="Velocidad de generación, media de seis textos. UD-IQ4_XS: 83,1 tok/s con la RTX 3090 y 108,0 con la RTX 5060 Ti. UD-Q4_K_XL: 64,9 y 80,5." src="docs/media/readme/summary-light.svg">
</picture>

| Generación, tokens/s | RTX 3090 | RTX 3090 + RTX 5060 Ti | con la segunda gráfica |
|---|---:|---:|---:|
| UD-IQ4_XS | **83,1** | **108,0** | +30 % |
| UD-Q4_K_XL | **64,9** | **80,5** | +24 % |

## El equipo

| | |
|---|---|
| CPU | AMD Ryzen 7 5700X: 8 núcleos / 16 hilos, Zen 3, AVX2 (sin AVX-512) |
| RAM | 128 GB DDR4-3200 CL22 (4 x 32 GB), ~36 GB/s de lectura (STREAM) |
| Gráfica principal | NVIDIA RTX 3090 24 GB, PCIe 4.0 x8, límite de potencia 250 W |
| Segunda gráfica (nivel de expertos) | NVIDIA RTX 5060 Ti 16 GB, PCIe 4.0 x8, límite de potencia 150 W |
| Disco | NVMe Crucial P3 Plus 2 TB |
| Software | Linux (kernel 7.2), driver NVIDIA 615.71, CUDA 13.4, motor compilado para `86;120` |

Con las gráficas a su potencia de serie (350 W y 180 W) las velocidades fueron las mismas: al motor lo limitan la CPU,
la RAM y el PCIe, no la potencia de las gráficas.

## Los modelos

Qwen3.8-Flash-Next tiene 48 capas de 512 expertos. Strata guarda los expertos en RAM, mantiene en VRAM los más usados
(una caché adaptativa) y calcula el resto en la CPU, así que la RAM, la CPU y el enlace PCIe marcan la velocidad.

| | UD-IQ4_XS | UD-Q4_K_XL |
|---|---|---|
| Ficheros GGUF de unsloth | 3 | 4 |
| Pesos de los expertos | 55,4 GiB | 71,7 GiB |
| Formatos de los expertos (gate/up · down) | IQ3_S (47 capas), IQ4_XS (1) · IQ4_NL (43), Q8_0 (5) | Q4_K (47), Q5_K (1) · Q5_1 (43), Q8_0 (5) |
| RAM que ocupa el motor | ~58 GiB | ~81 GB |
| Kernels de CPU de los expertos | limitados por cálculo: escalan con los núcleos | limitados por ancho de banda: la DDR4 se satura con ~4 núcleos |

Los dos van con 200.192 tokens de contexto, caché KV int8, la capa de borrador MTP con vocabulario español y búsqueda
en el prompt, y verificación greedy: la especulación nunca cambia la salida.

## Una gráfica o dos

La RTX 5060 Ti guarda ~14,5 GB más de expertos y calcula su parte de cada capa mientras la CPU calcula la suya.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/decode-iq4xs-dark.svg">
  <img alt="UD-IQ4_XS por texto, RTX 3090 frente a RTX 3090 + RTX 5060 Ti: chat en español 85,9/112,7, razonamiento 88,5/111,0, tras un documento de 18K 70,0/99,1, código 87,4/119,5, edición 113,8/161,6, tras un prompt de 5K 62,4/66,4." src="docs/media/readme/decode-iq4xs-light.svg">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/decode-q4kxl-dark.svg">
  <img alt="UD-Q4_K_XL por texto, RTX 3090 frente a RTX 3090 + RTX 5060 Ti: chat en español 62,8/87,3, razonamiento 74,8/80,4, tras un documento de 18K 54,7/72,7, código 67,6/84,1, edición 87,9/117,7, tras un prompt de 5K 48,8/53,8." src="docs/media/readme/decode-q4kxl-light.svg">
</picture>

La lectura del prompt (prefill) gana con la segunda gráfica en los prompts cortos; uno de 18K lo limita el enlace x8 de
la 3090 en los dos casos.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/prefill-iq4xs-dark.svg">
  <img alt="Prefill de UD-IQ4_XS, RTX 3090 frente a las dos: 18.076 tokens 1.800/1.813 tok/s, 5.296 tokens 1.131/1.463, 3.340 tokens 811/1.030." src="docs/media/readme/prefill-iq4xs-light.svg">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/prefill-q4kxl-dark.svg">
  <img alt="Prefill de UD-Q4_K_XL, RTX 3090 frente a las dos: 18.076 tokens 1.699/1.730 tok/s, 5.296 tokens 869/1.067, 3.340 tokens 638/758." src="docs/media/readme/prefill-q4kxl-light.svg">
</picture>

Aquí UD-IQ4_XS es el más rápido (+28 % con una gráfica, +34 % con dos): sus expertos ocupan menos, así que caben más
en VRAM (81 % / 89 % de aciertos frente a 78 % / 83 %), y sus kernels de CPU, limitados por cálculo, aprovechan los
siete workers. UD-Q4_K_XL es el cuantizado más grande y de más precisión.

## Con 64 GB de RAM

El mismo PC con el motor limitado a 60 GiB (lo que deja libre un PC de 64 GB), caché de disco incluida, con un cgroup.
UD-IQ4_XS sigue cabiendo y va igual de rápido. UD-Q4_K_XL no cabe (71,7 GiB de expertos): los lee del NVMe con
`--mmap-experts` y pierde más de la mitad de la velocidad.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/ram64-dark.svg">
  <img alt="Generación con 128 GB y con 64 GB de RAM: UD-IQ4_XS RTX 3090 83,1/83,5, UD-IQ4_XS con las dos 108,0/107,5, UD-Q4_K_XL RTX 3090 64,9/24,4, UD-Q4_K_XL con las dos 80,5/37,1." src="docs/media/readme/ram64-light.svg">
</picture>

| 64 GB de RAM | Generación | Prefill 18K / 5K / 3K | Aciertos de caché |
|---|---:|---:|---:|
| UD-IQ4_XS, RTX 3090 | 83,5 | 1.790 / 1.132 / 813 | 81 % |
| UD-IQ4_XS, las dos | 107,5 | 1.804 / 1.460 / 1.033 | 89 % |
| UD-Q4_K_XL, RTX 3090 | 24,4 | 432 / 154 / 133 | 54 % |
| UD-Q4_K_XL, las dos | 37,1 | 532 / 195 / 155 | 78 % |

Con 64 GB lo que hay que usar es UD-IQ4_XS; UD-Q4_K_XL necesita un PC de 96 GB o más (~81 GB para el motor más el
sistema).

## Sesiones largas de agente

18 turnos a través de `serve/server.py`, como los mandaría un agente de programación: ficheros de código pegados,
documentación, cambios de tema, la conversación creciendo hasta ~31K tokens y 600 tokens por respuesta. Con una gráfica:
**UD-IQ4_XS 77,8 tok/s**, UD-Q4_K_XL 59,7 tok/s (tres y dos rondas).

## Lo que han aportado los cambios sobre `custom` de eddoursul

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/steps-dark.svg">
  <img alt="UD-IQ4_XS con la RTX 3090: custom de eddoursul + arreglos 77,3, + kernel IQ4_XS AVX-2 78,0, + gather AVX2 80,9, + --adapt-decay 0.92 83,3 tok/s." src="docs/media/readme/steps-light.svg">
</picture>

- El **kernel IQ4_XS AVX-2 multi-token** (#415 del motor original): la única capa IQ4_XS ya no va token a token.
- El **gather AVX2 de la tabla de IQ3_S** (motor original, `STRATA_IQ256_GATHER=1`): da exactamente los mismos números,
  +4,9 % en Zen 3. En el original es opcional porque la velocidad del gather depende de la CPU.
- **`--adapt-decay 0.92`** (opción del motor original; 0,7 por defecto): la caché de VRAM recuerda más tiempo qué
  expertos se usaron. En las sesiones de agente los tres pasos dieron 75,0 -> 77,8 (+3,7 %).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/decay-dark.svg">
  <img alt="UD-IQ4_XS con la RTX 3090 según --adapt-decay: 0,70 80,9, 0,85 81,2, 0,92 82,4, 0,95 82,6, 0,97 81,1, 0,99 71,6, 1,00 57,1 tok/s." src="docs/media/readme/decay-light.svg">
</picture>

Por encima de 0,97 la caché deja de seguir el texto. Con la segunda gráfica 0,92 anula la ganancia del gather, y en
UD-Q4_K_XL no aporta en las sesiones de agente, así que esas configuraciones se quedan en 0,7.

Los arreglos, propuestos a eddoursul/Strata: el arreglo del bloqueo con dos gráficas del #2, de FlareP1, y
[una continuación](https://github.com/eddoursul/Strata/pull/2) para el congelamiento de la caché que provoca con 6 o
más workers; `--mmap-experts` con packs nativos ([#5](https://github.com/eddoursul/Strata/pull/5)); un worker por
núcleo físico en Linux ([#6](https://github.com/eddoursul/Strata/pull/6)); que el motor salga en cuanto recibe `QUIT`
([#7](https://github.com/eddoursul/Strata/pull/7)); el vocabulario de borrador en español
([#8](https://github.com/eddoursul/Strata/pull/8)).

## Workers de CPU

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/media/readme/workers-dark.svg">
  <img alt="Generación según los workers de CPU con la RTX 3090 sola: UD-IQ4_XS 65,6 con 4, 74,1 con 6, 76,6 con 7; UD-Q4_K_XL 63,5 con 4, 62,2 con 5, 61,6 con 6, 62,2 con 7." src="docs/media/readme/workers-light.svg">
</picture>

Descomprimir los expertos de UD-IQ4_XS cuesta (búsquedas en tablas, ~5 GB/s por núcleo), así que cada núcleo suma hasta
los siete que puede dar la CPU (uno es el hilo principal del motor). Los de UD-Q4_K_XL se descomprimen rápido y cuatro
núcleos ya leen la RAM tan deprisa como da. Medido antes de lo portado del motor original y del afinado final; la forma
es la misma.

## Ajustes y cómo usarlo

| | UD-IQ4_XS 1 GPU | UD-IQ4_XS 2 GPU | UD-Q4_K_XL 1 GPU | UD-Q4_K_XL 2 GPU |
|---|---:|---:|---:|---:|
| `--pool-workers` | 7 | 7 | 4 | 4 |
| `--adapt-swaps` | 192 | 192 | 96 | 96 |
| `--adapt-decay` | 0,92 | 0,7 | 0,7 | 0,7 |
| `STRATA_IQ256_GATHER` | 1 | 1 | - | - |
| `--pcie-frac` (kernel) | 0 | 0 | 0,3 | 0 |

Las cuatro configuraciones y los pasos para compilar y arrancarlas en Linux: [examples/r7-5700x](examples/r7-5700x/).

## Cómo se ha medido

- Seis textos fijos, casi todos en español: una pregunta de chat (400 tokens de respuesta), un problema de razonamiento
  (700, con razonamiento), un documento de 18.076 tokens para resumir (400), una tarea de código (600), un script de
  3.340 tokens devuelto editado (~2.600) y un prompt de 5.296 tokens (256). Los textos largos son notas privadas y no
  se publican.
- El motor directamente por su protocolo `--serve`, sin caché de prompt, greedy, con especulación. La velocidad de
  generación es la media geométrica de los seis textos; cada configuración es la media de una a seis rondas (a menos
  de un 3 % entre sí, salvo una ronda dual a -3 %), intercaladas con la base al comparar versiones.
- Tablas completas: [docs/MEASUREMENTS.es.md](docs/MEASUREMENTS.es.md).
