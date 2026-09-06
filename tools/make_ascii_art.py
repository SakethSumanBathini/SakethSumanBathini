#!/usr/bin/env python3
"""
Generates the ASCII art panel for assets/card-terminal.svg.

Draws a neural network graph — four layers of nodes with weighted edges.
Chosen over the orbital motif because it stays legible at the 80x46
character grid the card allows, and it matches what the profile is about.

Original geometry, drawn in code. Nothing is traced from a photograph.

    python tools/make_ascii_art.py
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

import sys
# Two consumers: the terminal card (80x46) and profile-grid.svg (120x55).
if "--grid" in sys.argv:
    COLS, ROWS, CELL_AR, OUT = 120, 55, 2.1, "tools/grid_art.txt"
else:
    COLS, ROWS, CELL_AR, OUT = 80, 46, 2.6, "tools/ascii_art.txt"
SS = 8
W = COLS * SS
H = int(ROWS * SS * CELL_AR)

RAMP = " .:-=+*#%@"           # index 0 is a space -> empty background

random.seed(2026)
img = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(img)

# ── layer geometry ───────────────────────────────────────────────────────
LAYERS = [3, 5, 5, 2]         # nodes per layer, input -> output
x_pad, y_pad = W * 0.14, H * 0.13
xs = [x_pad + i * (W - 2 * x_pad) / (len(LAYERS) - 1) for i in range(len(LAYERS))]

nodes = []
for xi, count in zip(xs, LAYERS):
    span = H - 2 * y_pad
    if count == 1:
        ys = [H / 2]
    else:
        ys = [y_pad + j * span / (count - 1) for j in range(count)]
    nodes.append([(xi, y) for y in ys])

# ── edges first, so nodes draw on top ────────────────────────────────────
for a, b in zip(nodes, nodes[1:]):
    for (x1, y1) in a:
        for (x2, y2) in b:
            # vary weight so the graph reads as trained, not uniform
            w = random.random()
            if w < 0.22:
                continue                       # pruned connection
            bright = int(60 + 120 * w)
            d.line([(x1, y1), (x2, y2)], fill=bright,
                   width=max(2, int(SS * (0.30 + 0.45 * w))))

# ── nodes ────────────────────────────────────────────────────────────────
for li, layer in enumerate(nodes):
    for (x, y) in layer:
        for r_mult, val in ((2.6, 130), (1.9, 205), (1.15, 255)):
            r = SS * r_mult
            d.ellipse([x - r, y - r, x + r, y + r], fill=val)

# ── faint activation trace along the top and bottom ─────────────────────
for sign, base in ((1, y_pad * 0.42), (-1, H - y_pad * 0.42)):
    pts = []
    for i in range(0, W + 1, 4):
        t = i / W * math.pi * 3
        pts.append((i, base + sign * math.sin(t) * H * 0.028))
    d.line(pts, fill=95, width=max(2, SS // 3))

img = img.filter(ImageFilter.GaussianBlur(radius=SS * 0.28))

# ── downsample to the character grid ─────────────────────────────────────
small = img.resize((COLS, ROWS), Image.LANCZOS)
px = small.load()

lines = []
for y in range(ROWS):
    row = []
    for x in range(COLS):
        idx = min(int(px[x, y] / 256 * len(RAMP)), len(RAMP) - 1)
        row.append(RAMP[idx])
    lines.append("".join(row).ljust(COLS))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Wrote {OUT}  ({COLS} cols x {ROWS} rows)")
print()
if "--quiet" not in sys.argv:
    for ln in lines:
        print(ln)
