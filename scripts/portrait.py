"""Turns the reference still into a small tone grid for the hero's dithered portrait.

    python scripts/portrait.py path/to/reference.png

Writes scripts/portrait.json: a downsampled grayscale grid plus a colour-class
grid (green headband, teal earrings). build_assets.py dithers that grid per theme.
The source image itself is not stored in the repo, only this coarse derived grid.
"""
from __future__ import annotations

import base64
import colorsys
import json
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
    cls = []
    for i, (r, gr, b) in enumerate(zip(*[iter(small.tobytes())] * 3)):
        x, y = i % gw, i // gw
        hh, ss, vv = colorsys.rgb_to_hsv(r / 255, gr / 255, b / 255)
        inbox = hb0[0] <= x <= hb1[0] and hb0[1] <= y <= hb1[1]
        cls.append(1 if inbox and ss > 0.22 and vv > 0.22 and 65 <= hh * 360 <= 155 else 0)
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
    print(f"{gw}x{gh} cells, {sum(1 for c in cls if c == 1)} headband cells, earrings {ears} -> {OUT.name}")


if __name__ == "__main__":
    main(sys.argv[1])
