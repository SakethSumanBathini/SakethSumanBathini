#!/usr/bin/env python3
"""
Generates an animated contribution-grid SVG that spells SAKETH.
Zero external dependencies, zero rate limits — the file lives in the repo.
"""
import random

FONT = {
    "S": [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
}

WORD = "SAKETH"
ROWS = 7
CELL = 12
GAP = 3
PITCH = CELL + GAP
TOTAL_COLS = 53          # a real contribution year is 53 weeks
RADIUS = 2.5

# Brand palette
BG = "#020205"
# cool greys only — orange is reserved for the name, so the letters always win
NOISE = ["#0e0e13", "#14141b", "#1a1a23", "#20202b"]
LETTER = ["#FF5C00", "#FF6E1A", "#FF8A3D", "#FFA05C"]

random.seed(2026)

# ---- build letter mask ------------------------------------------------------
letter_w = len(FONT[WORD[0]][0])
word_w = len(WORD) * letter_w + (len(WORD) - 1)      # 1 col gap between letters
start_col = (TOTAL_COLS - word_w) // 2

mask = set()
for li, ch in enumerate(WORD):
    base = start_col + li * (letter_w + 1)
    for r, line in enumerate(FONT[ch]):
        for c, px in enumerate(line):
            if px == "#":
                mask.add((base + c, r))

# ---- emit svg ---------------------------------------------------------------
W = TOTAL_COLS * PITCH + GAP
H = ROWS * PITCH + GAP

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'width="{W}" height="{H}" role="img" '
    f'aria-label="SAKETH spelled out in a contribution graph">',
    "<style>",
    "  .c{opacity:1;animation:pop .55s ease-out both}",
    "  .l{opacity:1;animation:pop .55s ease-out both,glow 3.2s ease-in-out infinite}",
    "  @keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:scale(1)}}",
    "  @keyframes glow{0%,100%{opacity:1}50%{opacity:.72}}",
    "  rect{transform-box:fill-box;transform-origin:center}",
    "</style>",
    f'<rect width="{W}" height="{H}" fill="{BG}" rx="10"/>',
]

for col in range(TOTAL_COLS):
    for row in range(ROWS):
        x = GAP + col * PITCH
        y = GAP + row * PITCH
        is_letter = (col, row) in mask
        # left-to-right sweep, so the name writes itself on load
        delay = round(col * 0.022 + row * 0.012, 3)

        if is_letter:
            fill = LETTER[col % len(LETTER)]
            cls = "l"
            style = f"animation-delay:{delay}s,{round(delay + 0.6, 3)}s"
        else:
            fill = random.choice(NOISE)
            cls = "c"
            style = f"animation-delay:{delay}s"

        parts.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="{RADIUS}" fill="{fill}" style="{style}"/>'
        )

parts.append("</svg>")

out = "\n".join(parts)
with open("/home/claude/gh/assets/name-heatmap.svg", "w", encoding="utf-8") as f:
    f.write(out)

print(f"Wrote name-heatmap.svg  ({W}x{H}px, {len(mask)} lit cells, {TOTAL_COLS*ROWS} total)")
