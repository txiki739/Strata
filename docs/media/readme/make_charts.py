#!/usr/bin/env python3
"""docs/media/readme/make_charts.py - the README's charts as static SVG, a light and a dark file each.

GitHub shows a README's images without scripts or page styles, so every chart is drawn here: horizontal bars with
their values written at the end (the light lime is under 3:1 on white, so the numbers carry it), a legend whenever
there are two series, and the README picks the light or dark file with <picture>. Palettes checked with the
dataviz validator (CVD separation, normal-vision floor, contrast) on GitHub's surfaces (#ffffff, #0d1117).

    python3 docs/media/readme/make_charts.py      # rewrites the *.svg beside it
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
THEME = {
    "light": {"ink": "#1f2328", "ink2": "#59636e", "grid": "#d1d9e0", "one": "#97c425", "two": "#1b9247",
              "single": "#1b9247", "m1": "#2a78d6", "m2": "#eb6834", "r128": "#4a3aa7", "r64": "#eda100", "surface": "#ffffff"},
    "dark": {"ink": "#f0f6fc", "ink2": "#9198a1", "grid": "#3d444d", "one": "#79a200", "two": "#00762c",
             "single": "#00762c", "m1": "#3987e5", "m2": "#d95926", "r128": "#9085e9", "r64": "#c98500", "surface": "#0d1117"},
}
GPU = [("one", "RTX 3090"), ("two", "RTX 3090 + RTX 5060 Ti")]

# ---- the measurements (Ryzen 7 5700X, 128 GB DDR4-3200; decode = six-prompt geometric mean, tokens/s) ----
PROMPTS = ["Spanish chat", "Reasoning", "After an 18K document", "Code", "Edit (3.3K script)", "After a 5K prompt"]
DECODE = {  # prompt order as PROMPTS; mean of every run of this code and these settings (2-6 per config)
    "iq4": {"one": [86.0, 87.7, 69.9, 88.5, 114.8, 63.5], "two": [114.9, 113.2, 98.1, 118.7, 165.2, 68.5]},
    "q4": {"one": [62.5, 69.8, 54.8, 68.1, 87.9, 49.1], "two": [86.1, 81.6, 73.7, 84.6, 118.1, 52.7]},
}
MEAN = {"iq4": {"one": 83.6, "two": 109.4}, "q4": {"one": 64.2, "two": 80.5}}
PREFILL_LABELS = ["18,076 tokens", "5,296 tokens", "3,340 tokens"]
PREFILL = {"iq4": {"one": [1787, 1131, 811], "two": [1800, 1461, 1036]},
           "q4": {"one": [1702, 869, 637], "two": [1716, 1066, 765]}}
STEPS = [("eddoursul custom + fixes", 77.3), ("+ IQ4_XS AVX-2 kernel", 78.0), ("+ AVX2 gather (IQ3_S)", 80.9),
         ("+ --adapt-decay 0.92", 83.3),
         ("+ upstream PRs #863, #851, #606", 83.6)]
DECAY = [(0.7, 76.8), (0.85, 82.1), (0.92, 83.6), (0.95, 81.0), (0.97, 81.3), (0.99, 70.8)]
# 64 GB PC emulated on the same machine (the current engine; the 128 GB column is the README's runs): the engine (and its page cache) limited to 60 GiB with a cgroup; UD-Q4_K_XL
# (71.7 GiB of experts) then reads its experts from the NVMe through --mmap-experts.  None until measured.
RAM_CATS = ["UD-IQ4_XS · RTX 3090", "UD-IQ4_XS · 3090 + 5060 Ti", "UD-Q4_K_XL · RTX 3090", "UD-Q4_K_XL · 3090 + 5060 Ti"]
RAM64 = {"128": [83.6, 109.4, 64.2, 80.5],
         "64": [81.5, 104.7, 21.4, 25.2]}
DECODE64 = {"iq4": {"one": [83.2, 87.5, 67.8, 85.3, 114.8, 61.0], "two": [95.5, 106.9, 98.0, 119.5, 164.8, 68.0]}, "q4": {"one": [24.0, 24.3, 20.4, 26.2, 32.7, 10.5], "two": [33.0, 36.4, 36.1, 17.6, 65.0, 5.1]}}
PREFILL64 = {"iq4": {"one": [1619, 1059, 676], "two": [1177, 1287, 1038]}, "q4": {"one": [300, 106, 94], "two": [521, 188, 52]}}
# decode right after a long prompt (128 tokens of answer), UD-IQ4_XS: one GPU / two
LONG_CATS = ["after 32K tokens", "after 64K", "after 120K", "after 200K"]
LONG_DEC_Q4 = {"one": [51.8, 64.3, 47.4, 45.8], "two": [83.3, 93.3, 68.3, 68.2]}
LONG_DEC = {"one": [67.0, 87.0, 61.5, 54.9], "two": [92.1, 96.8, 98.9, 97.6]}
WORKERS = {"UD-IQ4_XS": [(4, 73.8), (5, 75.7), (6, 81.8), (7, 83.6)], "UD-Q4_K_XL": [(3, 64.8), (4, 64.2), (5, 64.6), (6, 63.7)]}


def num(v, d=1):
    return f"{v:,.{d}f}"


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{label}" font-family="{FONT}">\n<title>{label}</title>\n{body}</svg>\n')


def bar(x0, y, w, h):
    """A bar anchored at x0 whose data end is rounded (4 px)."""
    r = min(4, w / 2, h / 2)
    return f"M{x0:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} a{r},{r} 0 0 1 {-r},{r} h{-(w - r):.1f} z"


def legend(items, t, x=0, y=14):
    out, cx = [], x
    for key, text in items:
        out.append(f'<rect x="{cx}" y="{y - 10}" width="12" height="12" rx="3" fill="{t[key]}"/>')
        out.append(f'<text x="{cx + 18}" y="{y}" font-size="13" fill="{t["ink2"]}">{text}</text>')
        cx += 18 + 7.4 * len(text) + 22
    return "\n".join(out)


def ticks(vmax):
    for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if vmax / step <= 6:
            return step
    return 2000


def grouped(name, cats, series, label, t, vmax=None, dec=1, lab_w=180, w=760, title=None):
    """Horizontal grouped bars: one group per category, one bar per series (2 px gap inside a group); `title`, the
    chart's own name above the legend, for the charts that differ only by model."""
    bh, gap, ggap, top = 14, 2, 16, 34 + (24 if title else 0)
    n = len(series)
    gh = n * bh + (n - 1) * gap
    h = top + len(cats) * (gh + ggap) + 26
    vmax = vmax or max(max(v) for _, _, v in series)
    step = ticks(vmax)
    vmax = (int(vmax / step) + 1) * step
    pw = w - lab_w - 60
    X = lambda v: lab_w + v / vmax * pw
    body = [f'<text x="0" y="16" font-size="15" font-weight="600" fill="{t["ink"]}">{title}</text>' if title else "",
            legend([(k, s) for k, s, _ in series], t, y=38 if title else 14) if n > 1 else ""]
    for i in range(0, int(vmax) + 1, step):
        x = X(i)
        body.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{h - 22}" stroke="{t["grid"]}" stroke-width="1"/>')
        body.append(f'<text x="{x:.1f}" y="{h - 6}" font-size="11" fill="{t["ink2"]}" text-anchor="middle">{num(i, 0)}</text>')
    for ci, cat in enumerate(cats):
        y0 = top + ci * (gh + ggap)
        body.append(f'<text x="{lab_w - 10}" y="{y0 + gh / 2 + 4.5:.1f}" font-size="13" fill="{t["ink"]}" '
                    f'text-anchor="end">{cat}</text>')
        for si, (key, _, vals) in enumerate(series):
            y = y0 + si * (bh + gap)
            v = vals[ci]
            body.append(f'<path d="{bar(lab_w, y, X(v) - lab_w, bh)}" fill="{t[key]}"/>')
            body.append(f'<text x="{X(v) + 6:.1f}" y="{y + bh - 3}" font-size="12" fill="{t["ink2"]}">{num(v, dec)}</text>')
    return svg(w, h, "\n".join(body), label)


def line(name, series, label, t, xlab, xs, ylo, yhi, ystep, xfmt, w=760, h=300, mark=None, ordinal=False):
    """Lines with 2 px strokes and 8 px markers; the last point of each series labeled directly."""
    l, r, top, bot = 54, 150, 30, 40
    pw, ph = w - l - r, h - top - bot
    xlo, xhi = xs[0], xs[-1]
    X = (lambda x: l + xs.index(x) / (len(xs) - 1) * pw) if ordinal else (lambda x: l + (x - xlo) / (xhi - xlo) * pw)
    Y = lambda y: top + (yhi - y) / (yhi - ylo) * ph
    body = []
    if len(series) > 1:
        body.append(legend([(k, s) for k, s, _ in series], t, x=l))
    for y in range(ylo, yhi + 1, ystep):
        body.append(f'<line x1="{l}" y1="{Y(y):.1f}" x2="{l + pw}" y2="{Y(y):.1f}" stroke="{t["grid"]}" stroke-width="1"/>')
        body.append(f'<text x="{l - 8}" y="{Y(y) + 4:.1f}" font-size="11" fill="{t["ink2"]}" text-anchor="end">{y}</text>')
    for x in xs:
        body.append(f'<text x="{X(x):.1f}" y="{h - 20}" font-size="11" fill="{t["ink2"]}" text-anchor="middle">{xfmt(x)}</text>')
    body.append(f'<text x="{l + pw / 2:.1f}" y="{h - 4}" font-size="12" fill="{t["ink2"]}" text-anchor="middle">{xlab}</text>')
    body.append(f'<text x="12" y="{top + ph / 2:.1f}" font-size="12" fill="{t["ink2"]}" text-anchor="middle" '
                f'transform="rotate(-90 12 {top + ph / 2:.1f})">tokens/s</text>')
    for key, name_, pts in series:
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(pts))
        body.append(f'<path d="{d}" fill="none" stroke="{t[key]}" stroke-width="2" stroke-linejoin="round"/>')
        for x, y in pts:
            body.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="4.5" fill="{t[key]}" stroke="{t["surface"]}" stroke-width="2"/>')
        lx, ly = pts[-1]
        body.append(f'<text x="{X(lx) + 10:.1f}" y="{Y(ly) + 4:.1f}" font-size="12" fill="{t["ink"]}">{name_} {num(ly)}</text>')
    if mark:
        mx, my, text = mark
        body.append(f'<text x="{X(mx):.1f}" y="{Y(my) - 12:.1f}" font-size="12" fill="{t["ink"]}" text-anchor="middle">{text}</text>')
    return svg(w, h, "\n".join(body), label)


def main():
    for mode, t in THEME.items():
        charts = {
            "summary": grouped("summary", ["UD-IQ4_XS", "UD-Q4_K_XL"],
                               [(k, s, [MEAN["iq4"][k], MEAN["q4"][k]]) for k, s in GPU],
                               "Decode speed, six-prompt mean: one GPU or two", t, lab_w=120),
            "decode-iq4xs": grouped("d", PROMPTS, [(k, s, DECODE["iq4"][k]) for k, s in GPU],
                                    "UD-IQ4_XS decode speed per prompt", t, title="UD-IQ4_XS · decode per prompt (tokens/s)"),
            "decode-q4kxl": grouped("d", PROMPTS, [(k, s, DECODE["q4"][k]) for k, s in GPU],
                                    "UD-Q4_K_XL decode speed per prompt", t, vmax=max(DECODE["iq4"]["two"]),
                                    title="UD-Q4_K_XL · decode per prompt (tokens/s)"),
            "prefill-iq4xs": grouped("p", PREFILL_LABELS, [(k, s, PREFILL["iq4"][k]) for k, s in GPU],
                                     "UD-IQ4_XS prompt reading speed", t, dec=0, lab_w=120,
                                     title="UD-IQ4_XS · prompt reading (tokens/s)"),
            "prefill-q4kxl": grouped("p", PREFILL_LABELS, [(k, s, PREFILL["q4"][k]) for k, s in GPU],
                                     "UD-Q4_K_XL prompt reading speed", t, vmax=max(PREFILL["iq4"]["two"]), dec=0,
                                     lab_w=120, title="UD-Q4_K_XL · prompt reading (tokens/s)"),
            "steps": grouped("s", [s for s, _ in STEPS], [("single", "", [v for _, v in STEPS])],
                             "UD-IQ4_XS on the RTX 3090: what each change gave", t, lab_w=250),
            "decay": line("decay", [("single", "", DECAY)], "UD-IQ4_XS on the RTX 3090: --adapt-decay", t,
                          "--adapt-decay (the share of the routing counts kept after each cache update)",
                          [x for x, _ in DECAY], 60, 90, 10, lambda x: f"{x:.2f}", mark=(0.92, 83.6, "0.92 (used)"), ordinal=True),
            "workers": line("workers", [("m1", "UD-IQ4_XS", WORKERS["UD-IQ4_XS"]), ("m2", "UD-Q4_K_XL", WORKERS["UD-Q4_K_XL"])],
                            "Decode speed by CPU pool workers, RTX 3090 alone", t, "CPU pool workers (one per physical core)",
                            [3, 4, 5, 6, 7], 55, 90, 5, str),
        }
        lmax = max(LONG_DEC["two"] + LONG_DEC_Q4["two"])
        charts["longctx-iq4xs"] = grouped("l", LONG_CATS, [(k, n, LONG_DEC[k]) for k, n in GPU],
                                          "UD-IQ4_XS decode right after a long prompt", t, vmax=lmax, lab_w=150,
                                          title="UD-IQ4_XS · decode right after a long prompt (tokens/s)")
        charts["longctx-q4kxl"] = grouped("l", LONG_CATS, [(k, n, LONG_DEC_Q4[k]) for k, n in GPU],
                                          "UD-Q4_K_XL decode right after a long prompt", t, vmax=lmax, lab_w=150,
                                          title="UD-Q4_K_XL · decode right after a long prompt (tokens/s)")
        for m, nm in (("iq4", "UD-IQ4_XS"), ("q4", "UD-Q4_K_XL")):
            charts[f"decode-{'iq4xs' if m == 'iq4' else 'q4kxl'}-64"] = grouped(
                "d", PROMPTS, [(k, s, DECODE64[m][k]) for k, s in GPU], f"{nm} decode per prompt with 64 GB of RAM", t,
                vmax=max(DECODE["iq4"]["two"]), title=f"{nm} · decode per prompt, 64 GB of RAM (tokens/s)")
            charts[f"prefill-{'iq4xs' if m == 'iq4' else 'q4kxl'}-64"] = grouped(
                "p", PREFILL_LABELS, [(k, s, PREFILL64[m][k]) for k, s in GPU], f"{nm} prompt reading with 64 GB of RAM", t,
                vmax=max(PREFILL["iq4"]["two"]), dec=0, lab_w=120, title=f"{nm} · prompt reading, 64 GB of RAM (tokens/s)")
        if RAM64:
            charts["ram64"] = grouped("r", RAM_CATS, [("r128", "128 GB", RAM64["128"]), ("r64", "64 GB", RAM64["64"])],
                                      "Decode speed with 128 GB and with 64 GB of RAM", t, lab_w=210)
        for name, text in charts.items():
            (OUT / f"{name}-{mode}.svg").write_text(text, encoding="utf-8")
    print("charts written to", OUT)


if __name__ == "__main__":
    main()
