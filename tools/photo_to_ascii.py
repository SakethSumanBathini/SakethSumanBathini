#!/usr/bin/env python3
"""
Converts a photo into ASCII art for profile-grid.svg.

Produces exactly the grid the card expects — 55 lines of 120 characters,
using the same density ramp as the original — then rewrites the checksum in
tools/make_profile_grid.py so the card will build with the new art.

    python tools/photo_to_ascii.py path/to/your-photo.jpg

Options:
    --invert        light subject on dark background (default assumes this)
    --contrast 1.4  push contrast before conversion (default 1.35)
    --preview       print the result to the terminal

Tips for a good result:
  * Use a head-and-shoulders shot with clear separation from the background.
  * A plain or blurred background converts far better than a busy one.
  * Portrait orientation. The panel is tall, so a square or 3:4 crop works
    best; very wide images lose the face.
"""
import argparse
import hashlib
import os
import re
import sys

try:
    from PIL import Image, ImageEnhance, ImageOps
except ImportError:
    sys.exit("Pillow is required:  pip install pillow --break-system-packages")

COLS, ROWS = 120, 55
# Same characters the uploaded card used, ordered light -> dark.
RAMP = " .:-=+*#%@"
CELL_AR = 2.1          # a cell renders ~2.1x taller than wide at scale(0.42,0.88)

GRID = "tools/grid_art.txt"
GEN = "tools/make_profile_grid.py"


def convert(path, contrast, invert):
    im = Image.open(path).convert("L")

    # Fit to the character grid, compensating for non-square cells
    target_w = COLS
    target_h = ROWS
    src_ar = im.width / im.height
    grid_ar = (target_w) / (target_h * CELL_AR)

    if src_ar > grid_ar:            # too wide -> crop sides
        new_w = int(im.height * grid_ar)
        left = (im.width - new_w) // 2
        im = im.crop((left, 0, left + new_w, im.height))
    else:                           # too tall -> crop top/bottom, favour the face
        new_h = int(im.width / grid_ar)
        top = int((im.height - new_h) * 0.25)
        im = im.crop((0, top, im.width, top + new_h))

    im = ImageOps.autocontrast(im, cutoff=2)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = im.resize((target_w, target_h), Image.LANCZOS)

    px = im.load()
    lines = []
    for y in range(target_h):
        row = []
        for x in range(target_w):
            v = px[x, y]
            if invert:
                v = 255 - v
            idx = min(int((255 - v) / 256 * len(RAMP)), len(RAMP) - 1)
            row.append(RAMP[idx])
        lines.append("".join(row).ljust(COLS)[:COLS])
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--contrast", type=float, default=1.35)
    ap.add_argument("--invert", action="store_true", default=True)
    ap.add_argument("--no-invert", dest="invert", action="store_false")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.photo):
        sys.exit(f"No such file: {a.photo}")

    lines = convert(a.photo, a.contrast, a.invert)
    assert len(lines) == ROWS and all(len(l) == COLS for l in lines)

    body = "\n".join(lines)
    open(GRID, "w", encoding="utf-8").write(body)
    sha = hashlib.sha256(body.encode()).hexdigest()[:32]

    # keep the generator's guard in sync with the new art
    g = open(GEN, encoding="utf-8").read()
    g = re.sub(r'ART_SHA = "[0-9a-f]{32}"', f'ART_SHA = "{sha}"', g)
    open(GEN, "w", encoding="utf-8").write(g)

    print(f"Wrote {GRID}  ({COLS}x{ROWS})")
    print(f"Updated ART_SHA -> {sha}")
    print("\nNow run:  python tools/make_profile_grid.py")

    if a.preview:
        print()
        for l in lines:
            print(l)


if __name__ == "__main__":
    main()
