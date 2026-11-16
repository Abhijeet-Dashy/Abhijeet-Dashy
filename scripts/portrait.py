"""Turns the reference still into a small tone grid for the hero's dithered portrait.

    python scripts/portrait.py path/to/reference.png

Writes scripts/portrait.json: a downsampled grayscale grid plus a colour-class
grid (teal earrings; the green headband in the source is painted out as forehead). build_assets.py dithers that grid per theme.
The source image itself is not stored in the repo, only this coarse derived grid.
"""
from __future__ import annotations

import base64
import colorsys
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

ZOOM = 1.25         # crop tightness around the head
EARRINGS = [(299, 106), (410, 119)]   # source-image px
EAR_R = 6.5
CELL = 3            # px per dither cell in the hero
PW, PH = 460, 380   # portrait box in the hero (px)
OUT = Path(__file__).resolve().parent / "portrait.json"


def keep_clusters(cls, gw, gh, code, keep, max_box):
    """Keep only the largest compact blobs of one colour class; drop stray highlights."""
    seen, blobs = set(), []
    for start in range(len(cls)):
        if cls[start] != code or start in seen:
            continue
        stack, cells = [start], []
        seen.add(start)
        while stack:
            i = stack.pop()
            cells.append(i)
            x, y = i % gw, i // gw
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    j = ny * gw + nx
                    if 0 <= nx < gw and 0 <= ny < gh and cls[j] == code and j not in seen:
                        seen.add(j)
                        stack.append(j)
        xs, ys = [c % gw for c in cells], [c // gw for c in cells]
        if max(xs) - min(xs) < max_box and max(ys) - min(ys) < max_box and len(cells) >= 3:
            blobs.append(cells)
    blobs.sort(key=len, reverse=True)
    keepset = {c for b in blobs[:keep] for c in b}
    return [code if i in keepset else (0 if v == code else v) for i, v in enumerate(cls)]


def main(src: str) -> None:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    # keep the full height, centre the crop on the head
    ch = round(h / ZOOM)
    cw = round(ch * PW / PH)
    cx = round(w * 0.49)
    x0 = max(0, min(w - cw, cx - cw // 2))
    im = im.crop((x0, 0, x0 + cw, ch))
    gw, gh = PW // CELL, PH // CELL
    full = im.resize((PW, PH), Image.LANCZOS)
    small = full.resize((gw, gh), Image.LANCZOS)

    # tone: stretch, lift the shadows (the scene is low-key), then sharpen so eyes, collar and tie edges survive dithering
    gray = ImageOps.autocontrast(full.convert("L"), cutoff=(1, 0.5))
    gray = gray.point(lambda v: int(255 * (v / 255) ** 0.6))
    gray = gray.filter(ImageFilter.UnsharpMask(radius=2.5, percent=260, threshold=1)).resize((gw, gh), Image.LANCZOS)
    g = list(gray.tobytes())
    # accents: the green headband (found by colour inside a box) and the two teal earrings (placed by position).
    # coordinates are in the source image; map them through the crop.
    scale = PW / cw
    def to_cell(sx, sy):
        return (sx - x0) * scale / CELL, sy * scale / CELL
    hb0 = to_cell(306, 58)
    hb1 = to_cell(390, 100)
    mask = [False] * (gw * gh)
    for i, (r, gr, b) in enumerate(zip(*[iter(small.tobytes())] * 3)):
        x, y = i % gw, i // gw
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, gr / 255, b / 255)
        if hb0[0] <= x <= hb1[0] and hb0[1] <= y <= hb1[1] and ss > 0.22 and vv > 0.22 and 65 <= hh * 360 <= 155:
            mask[i] = True
    # remove the headband: grow the mask a little, then repaint it as forehead (tone sampled just below the band)
    grown = mask[:]
    for i, m in enumerate(mask):
        if m:
            x, y = i % gw, i // gw
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if 0 <= x + dx < gw and 0 <= y + dy < gh:
                        grown[(y + dy) * gw + x + dx] = True
    ys = [i // gw for i, m in enumerate(mask) if m]
    xs = [i % gw for i, m in enumerate(mask) if m]
    below = sorted(g[(y) * gw + x] for y in range(max(ys) + 3, max(ys) + 6) for x in range(min(xs) + 6, max(xs) - 6)
                   if not grown[y * gw + x])
    skin = below[len(below) // 2]
    # upper part becomes a ragged hair fringe, the rest forehead with a soft top-to-bottom light falloff
    gys = [i // gw for i, m in enumerate(grown) if m]
    y0g, y1g = min(gys), max(gys)
    for i, m in enumerate(grown):
        if not m:
            continue
        x, y = i % gw, i // gw
        t = (y - y0g) / max(1, y1g - y0g)
        fringe = 0.40 + 0.20 * math.sin(x * 1.9) + 0.08 * math.sin(x * 0.7 + 1)
        g[i] = 14 if t < fringe else int(skin * (0.70 + 0.30 * t))
    cls = [0] * (gw * gh)
    ears = []
    for sx, sy in EARRINGS:
        cx_, cy_ = to_cell(sx, sy)
        ears.append([round(cx_ * CELL), round(cy_ * CELL), round(EAR_R * scale)])
    OUT.write_text(json.dumps({
        "w": gw, "h": gh, "cell": CELL,
        "gray": base64.b64encode(bytes(g)).decode(),
        "cls": base64.b64encode(bytes(cls)).decode(),
        "ears": ears,
    }), encoding="utf-8")
    print(f"{gw}x{gh} cells, {sum(mask)} headband cells repainted (skin tone {skin}), earrings {ears} -> {OUT.name}")


if __name__ == "__main__":
    main(sys.argv[1])
