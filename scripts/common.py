"""Shared pieces for the profile SVGs.

Visual language: the CUI design system (github.com/yappologistic/CUI). Neutral
surfaces (page #121212, each layer a step lighter), hairline borders, 18/14/10
radii, Geist at weight 500 with tight tracking, words that blur in, pill chips,
ordered-dither halftone. Colour is spent sparingly: one crimson accent, plus the
green and teal that come from the hero portrait. Every asset is built twice: dark and light.

Everything here is static SVG + CSS animation. No scripts, no external requests.
Fonts are subset per file and embedded as base64 woff2, because an SVG shown
through <img> cannot load external fonts.
"""
from __future__ import annotations

import base64
import io
import math
import re
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
ICONS = Path(__file__).resolve().parent / "icons"
OUT = ROOT / "assets"

THEMES = {
    "dark": {
        "bg": "#121212", "surface": "#181818", "raised": "#1f1f1f",
        "border": "#2b2b2b", "fg": "#f2f2f2", "text2": "#b4b4b4", "text3": "#8c8c8c",
        "accent": "#d9283b", "accent2": "#7d1522", "thread": "#8a8892",
        "dot": "#f2f2f2", "glow": "#2a1519", "glow_op": ".7",
        "coat": "#060609", "coat_edge": "#2c2c36", "fur": "#ece7dc", "fur_shade": "#a39c8e",
        "face_lit": "#cbc5ba", "face_mid": "#7d7a80", "face_dark": "#3c3b44",
        "hair": "#040406", "hair_hi": "#41414d",
        "ink_on_fg": "#121212",
    },
    "light": {
        "bg": "#ffffff", "surface": "#f8f8f8", "raised": "#f3f3f3",
        "border": "#e3e3e3", "fg": "#0b0b0b", "text2": "#585858", "text3": "#767676",
        "accent": "#b5172a", "accent2": "#e3a3aa", "thread": "#6d6b73",
        "dot": "#0b0b0b", "glow": "#f4dcdf", "glow_op": ".8",
        "coat": "#060609", "coat_edge": "#3a3a46", "fur": "#faf6ec", "fur_shade": "#8d867a",
        "face_lit": "#d6d0c5", "face_mid": "#8d8a90", "face_dark": "#48474f",
        "hair": "#040406", "hair_hi": "#4a4a56",
        "ink_on_fg": "#ffffff",
    },
}

FONT_FILES = {"d": "Geist-Medium.woff2", "s": "Geist-Regular.woff2", "m": "GeistMono-Regular.woff2"}
FAMILY = {"d": "GDisplay", "s": "GSans", "m": "GMono"}
FALLBACK = {
    "d": "Geist,Inter,system-ui,sans-serif",
    "s": "Geist,Inter,system-ui,sans-serif",
    "m": "'Geist Mono',ui-monospace,SFMono-Regular,Menlo,monospace",
}
EASE = "cubic-bezier(.22,1,.36,1)"

BASE_CSS = f"""
.d{{font-family:'GDisplay',{FALLBACK['d']};font-weight:500;}}
.s{{font-family:'GSans',{FALLBACK['s']};}}
.m{{font-family:'GMono',{FALLBACK['m']};}}
.rise{{animation:rise 720ms {EASE} both;}}
@keyframes rise{{0%{{opacity:0;transform:translateY(14px);}}}}
.word{{animation:word 900ms {EASE} both;}}
@keyframes word{{0%{{opacity:0;transform:translateY(.32em);filter:blur(10px);}}}}
.fadein{{animation:fadein 1400ms {EASE} both;}}
@keyframes fadein{{0%{{opacity:0;}}}}
.grow{{transform-box:fill-box;transform-origin:left;animation:grow 1200ms {EASE} both;}}
.growc{{transform-box:fill-box;transform-origin:center;animation:grow 1400ms {EASE} both;}}
@keyframes grow{{0%{{transform:scaleX(0);}}}}
.draw{{stroke-dasharray:1;animation:draw 2600ms {EASE} both;}}
@keyframes draw{{0%{{stroke-dashoffset:1;}}}}
.pulse{{animation:pulse 4.2s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{opacity:.45;}}50%{{opacity:1;}}}}
.float{{animation:float 9s ease-in-out infinite;}}
@keyframes float{{0%{{opacity:0;transform:translateY(8px);}}30%{{opacity:.9;}}100%{{opacity:0;transform:translateY(-34px);}}}}
.sway{{transform-box:view-box;transform-origin:var(--ox) 0;animation:sway 7s ease-in-out infinite;}}
@keyframes sway{{0%,100%{{transform:rotate(-1.6deg);}}50%{{transform:rotate(1.6deg);}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important;}}}}
"""


# ---------------------------------------------------------------- fonts


@lru_cache(maxsize=None)
def _font(key: str) -> TTFont:
    return TTFont(FONTS / FONT_FILES[key])


def measure(key: str, text: str, size: float, tracking: float = 0.0) -> float:
    f = _font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(ch), cmap[ord("?")])][0] for ch in text) * size / upm
    return w + tracking * len(text)


def _face(key: str, chars: str) -> str:
    font = TTFont(FONTS / FONT_FILES[key])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{FAMILY[key]}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w: float, h: float, label: str, body: str, defs: str = "", extra_css: str = "") -> str:
    """Wrap `body` in an <svg>, embedding only the font subsets it actually uses."""
    used = set()
    for cls in re.findall(r'class="([^"]*)"', body):
        used.update(t for t in cls.split() if t in FONT_FILES)
    chars = set("?")
    for t in re.findall(r">([^<>]+)</(?:text|tspan)>", body):
        chars.update(t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    faces = "".join(_face(k, "".join(sorted(chars))) for k in sorted(used))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
        f'role="img" aria-label="{esc(label)}">\n<title>{esc(label)}</title>\n'
        f"<defs><style>{faces}{BASE_CSS}{extra_css}</style>{defs}</defs>\n{body}\n</svg>\n"
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  {path}  {len(content) / 1024:.1f} KB")


# ---------------------------------------------------------------- primitives


def icon(name: str, x: float, y: float, size: float, fill: str) -> str:
    """Inline a simple-icons glyph (24x24 box) at x,y with the given size."""
    d = re.search(r' d="([^"]+)"', (ICONS / f"{name}.svg").read_text(encoding="utf-8")).group(1)
    s = size / 24
    return f'<path transform="translate({x:g} {y:g}) scale({s:.4f})" d="{d}" fill="{fill}"/>'


def spider(cx: float, cy: float, s: float, color: str, number: str | None = None, bg: str = "#000") -> str:
    """A small spider mark. The abdomen can carry a number (the Troupe's tattoo)."""
    legs = []
    for sign in (-1, 1):
        for i, y0 in enumerate((-2.6, -0.9, 0.9, 2.6)):
            spread = 5.2 + i * 0.5
            up = (-4.6, -2.2, 1.6, 4.6)[i]
            p = [(cx + sign * 1.4 * s, cy + y0 * s),
                 (cx + sign * spread * s, cy + (y0 + up * 0.55) * s),
                 (cx + sign * (spread + 3.2) * s, cy + (y0 + up * 0.55 + 4.4) * s)]
            legs.append("M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in p))
    out = (f'<path d="{"".join(legs)}" fill="none" stroke="{color}" stroke-width="{max(.8, s * .26):.2f}" '
           f'stroke-linecap="round" stroke-linejoin="round"/>'
           f'<ellipse cx="{cx:g}" cy="{cy + 2.9 * s:.1f}" rx="{3.3 * s:.1f}" ry="{4.2 * s:.1f}" fill="{color}"/>'
           f'<circle cx="{cx:g}" cy="{cy - 2.3 * s:.1f}" r="{2.2 * s:.1f}" fill="{color}"/>')
    if number:
        out += (f'<text x="{cx:g}" y="{cy + 4.7 * s:.1f}" text-anchor="middle" class="d" '
                f'font-size="{s * 4.4:.1f}" fill="{bg}">{number}</text>')
    return out


def dither(w: int, h: int, step: int, field, size: int = 2) -> str:
    """Ordered (Bayer 4x4) halftone from a 0..1 density field. Returns SVG path data."""
    bayer = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
    parts, px, py = [], 0, 0
    for gy in range(h // step + 1):
        for gx in range(w // step + 1):
            x, y = gx * step, gy * step
            if field(x, y) > (bayer[gy % 4][gx % 4] + .5) / 16:
                parts.append(f"m{x - px} {y - py}h{size}v{size}h-{size}z")
                px, py = x, y
    return "M0 0" + "".join(parts) if parts else ""


def smooth(a: float, b: float, v: float) -> float:
    t = min(1, max(0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def web(ax: float, ay: float, a0: float, a1: float, spokes: int, rings: list[float], color: str,
        op: float = .35, delay: float = 0.0) -> str:
    """Spider-web linework fanning from an anchor point. Rings sag between spokes."""
    angs = [a0 + (a1 - a0) * i / (spokes - 1) for i in range(spokes)]

    def pt(r, a):
        return ax + r * math.cos(math.radians(a)), ay + r * math.sin(math.radians(a))

    rmax = max(rings) * 1.04
    out = [f'<g fill="none" stroke="{color}" stroke-width="1" stroke-linecap="round" opacity="{op}">']
    for i, a in enumerate(angs):
        x, y = pt(rmax, a)
        out.append(f'<path class="draw" pathLength="1" style="animation-delay:{delay + i * .08:.2f}s" '
                   f'd="M{ax:g} {ay:g}L{x:.1f} {y:.1f}"/>')
    for j, r in enumerate(rings):
        x0, y0 = pt(r, angs[0])
        d = f"M{x0:.1f} {y0:.1f}"
        for a_prev, a in zip(angs, angs[1:]):
            cx, cy = pt(r * .9, (a_prev + a) / 2)
            x, y = pt(r, a)
            d += f"Q{cx:.1f} {cy:.1f} {x:.1f} {y:.1f}"
        out.append(f'<path class="draw" pathLength="1" style="animation-delay:{delay + .5 + j * .14:.2f}s" d="{d}"/>')
    out.append("</g>")
    return "".join(out)


def words(text: str, x: float, y: float, size: float, fill: str, key: str = "d", tracking: float = 0.0,
          anchor: str = "start", delay: float = 0.0, step: float = .07, extra: str = "") -> str:
    """Per-word blur-in text, positioned with real glyph metrics."""
    ws = text.split(" ")
    space = measure(key, " ", size, tracking)
    widths = [measure(key, w, size, tracking) for w in ws]
    total = sum(widths) + space * (len(ws) - 1)
    cx = x - (total / 2 if anchor == "middle" else total if anchor == "end" else 0)
    out = []
    for i, (wd, wt) in enumerate(zip(ws, widths)):
        out.append(f'<text x="{cx:.1f}" y="{y:g}" class="{key} word" style="animation-delay:{delay + i * step:.2f}s" '
                   f'font-size="{size:g}" letter-spacing="{tracking:g}" fill="{fill}" {extra}>{esc(wd)}</text>')
        cx += wt + space
    return "".join(out)


def chip(x: float, y: float, label: str, ico: str | None, t: dict, delay: float, h: int = 38, size: float = 15) -> tuple[str, float]:
    """A pill with an optional glyph. Returns (svg, width)."""
    pad, gap, isz = 14, 8, 16
    tw = measure("d", label, size, 0)
    w = pad * 2 + tw + (isz + gap if ico else 0)
    cy = y + h / 2
    g = [f'<g class="rise" style="animation-delay:{delay:.2f}s">',
         f'<rect x="{x:.1f}" y="{y:g}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t["surface"]}" stroke="{t["border"]}"/>']
    tx = x + pad
    if ico:
        g.append(icon(ico, tx, cy - isz / 2, isz, t["text2"]))
        tx += isz + gap
    g.append(f'<text x="{tx:.1f}" y="{cy + size * .35:.1f}" class="d" font-size="{size}" fill="{t["fg"]}">{esc(label)}</text></g>')
    return "".join(g), w
