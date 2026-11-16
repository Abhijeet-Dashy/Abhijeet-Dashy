"""Builds the static profile assets into ./assets (dark + light variants).

    pip install fonttools brotli
    python scripts/build_assets.py

Character theme: Chrollo Lucilfer (Hunter x Hunter) - the Phantom Troupe leader.
The hero is a dithered portrait generated from a reference still
(see scripts/portrait.py), styled after the CUI docs hero. Only a coarse tone grid
derived from it is stored in scripts/portrait.json.
"""
from __future__ import annotations

import base64
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (OUT, THEMES, chip, dither, esc, icon, measure, smooth, spider, svg, web, words, write)  # noqa: E402


# ---------------------------------------------------------------- hero (dithered portrait)

PORTRAIT = json.loads((Path(__file__).parent / "portrait.json").read_text(encoding="utf-8"))
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def portrait_layers(name: str, ox: int, oy: int) -> str:
    """Ordered-dither the stored tone grid into 2x2 dots, grouped into tone layers (like the CUI docs hero)."""
    P = PORTRAIT
    gw, gh, cell = P["w"], P["h"], P["cell"]
    gray = base64.b64decode(P["gray"])
    cls = base64.b64decode(P["cls"])
    dark = name == "dark"
    # dots sit where the image is bright: light dots on the dark page, ink dots on the light page.
    tones = (["#4a4a4a", "#7a7a7a", "#b4b4b4", "#f2f2f2"] if dark else ["#c8c8c8", "#8c8c8c", "#4a4a4a", "#0b0b0b"])
    green, teal = ("#7fbf5f", "#5fd3cf") if dark else ("#2f7d32", "#0f8f8a")
    layers: dict[str, list] = {k: [] for k in (*tones, green, teal)}
    for gy in range(gh):
        for gx in range(gw):
            i = gy * gw + gx
            v = gray[i] / 255
            x, y = gx * cell, gy * cell
            # fade the portrait into the page on its left edge so the headline sits on clean ground
            edge = smooth(0, 150, x) * (1 - .0 * smooth(300, 380, y))
            # same mapping in both themes: bright areas (face, shirt, tie) get the dots, the black suit and hair stay quiet
            d = max(0.0, min(1.0, (v - .12) / .88)) ** 1.1 * edge
            if cls[i] == 1:
                layers[green].append((x, y))
                continue
            if d > (BAYER[gy % 4][gx % 4] + .5) / 16:
                t = 3 if d > .62 else 2 if d > .38 else 1 if d > .18 else 0
                layers[tones[t]].append((x, y))
    # earrings: small discs of teal dots, placed over whatever the dither put underneath
    for ex, ey, er in P["ears"]:
        for gy in range(gh):
            for gx in range(gw):
                x, y = gx * cell, gy * cell
                if (x + 1 - ex) ** 2 + (y + 1 - ey) ** 2 <= er * er:
                    layers[teal].append((x, y))
    # one dot per cell, so drop a cell from the tone layers when an accent covers it
    taken = {c for k in (green, teal) for c in layers[k]}
    for k in tones:
        layers[k] = [c for c in layers[k] if c not in taken]
    out = []
    for n, (col, cells) in enumerate(layers.items()):
        if not cells:
            continue
        px = py = 0
        parts = []
        for x, y in cells:
            parts.append(f"m{x - px} {y - py}h2v2h-2z")
            px, py = x, y
        accent = col in (green, teal)
        cls_ = "fadein pulse" if accent and col == teal else "fadein"
        delay = .15 + n * .08
        out.append(f'<g class="{cls_}" style="animation-delay:{delay:.2f}s"><path fill="{col}" d="M{cells[0][0]} {cells[0][1]}h2v2h-2z'
                   + "".join(parts[1:]) + '"/></g>')
    return f'<g transform="translate({ox} {oy})">' + "".join(out) + "</g>"


def hero(name: str) -> str:
    t = THEMES[name]
    W, H = 880, 380
    dark = name == "dark"
    px, py = W - 460, 0
    cmd = "open abhijeet-dash.vercel.app"
    cmd_w = measure("m", "$ " + cmd, 12.5) + 28 + 34
    badge_a, badge_b = "Abhijeet-Dashy", "B.Tech CSE | 2027"
    wa, wb = measure("s", badge_a, 12.5), measure("s", badge_b, 12.5)
    bw = 14 + 11 + wa + 9 + 3 + 9 + wb + 16
    defs = f"""
<clipPath id="f"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<linearGradient id="clear" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['bg']}" stop-opacity=".96"/><stop offset=".62" stop-color="{t['bg']}" stop-opacity=".9"/><stop offset="1" stop-color="{t['bg']}" stop-opacity="0"/></linearGradient>
"""
    body = f"""
<g clip-path="url(#f)">
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
{portrait_layers(name, px, py)}
<rect width="520" height="{H}" fill="url(#clear)"/>
<g class="rise"><rect x="48" y="50" width="{bw:.1f}" height="28" rx="14" fill="{t['bg']}" fill-opacity=".82" stroke="{t['border']}"/><circle cx="62" cy="64" r="3.2" fill="{t['accent']}"/><text x="73" y="68.5" class="s" font-size="12.5" fill="{t['text2']}">{badge_a}</text><circle cx="{73 + wa + 9:.1f}" cy="64" r="1.5" fill="{t['text2']}" opacity=".6"/><text x="{73 + wa + 18:.1f}" y="68.5" class="s" font-size="12.5" fill="{t['text2']}">{badge_b}</text></g>
{words('Abhijeet Dash', 46, 142, 54, t['fg'], tracking=-2.0, delay=.15)}
{words('Full-Stack Developer.', 46, 192, 38, t['text2'], tracking=-1.3, delay=.36)}
<text x="48" y="238" class="s rise" style="animation-delay:.4s" font-size="15.5" fill="{t['text2']}">Production-ready web apps and scalable systems,</text><text x="48" y="261" class="s rise" style="animation-delay:.46s" font-size="15.5" fill="{t['text2']}">built for real-world problems and developer productivity.</text>
<g class="rise" style="animation-delay:.55s"><rect x="48" y="292" width="{cmd_w:.1f}" height="36" rx="18" fill="{t['bg']}" fill-opacity=".78" stroke="{t['border']}"/><text x="62" y="314.5" class="m" font-size="12.5" fill="{t['text3']}">$ <tspan fill="{t['text2']}">{cmd}</tspan></text><g transform="translate({48 + cmd_w - 30:.1f} 303)" fill="none" stroke="{t['text3']}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><rect x="0" y="3" width="9" height="10" rx="2"/><path d="M3 1.5v-.5a1.5 1.5 0 0 1 1.5-1.5h5.5a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5h-.5" transform="translate(0 1)"/></g></g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" fill="none" stroke="{t['border']}"/>
"""
    label = ("Abhijeet Dash. Full-Stack Developer. B.Tech CSE, 2027. Production-ready web apps and scalable systems. "
             "A dithered portrait of Chrollo Lucilfer from Hunter x Hunter in a black suit, green headband and teal earrings.")
    return svg(W, H, label, body, defs)


# ---------------------------------------------------------------- small pieces


def header(name: str, num: str, kicker: str, title: str, sub: str) -> str:
    t = THEMES[name]
    W, H = 600, 116
    kt = f"{num}  /  {kicker}"
    kw = measure("m", kt, 12.5, 2.4)
    body = f"""
<g class="rise" style="animation-delay:0s">
<text x="300" y="26" text-anchor="middle" class="m" font-size="12.5" letter-spacing="2.4" fill="{t['accent']}">{esc(kt)}</text>
<rect x="{300 - kw / 2 - 20 - 80:.1f}" y="21.5" width="80" height="1" fill="{t['border']}" class="growc"/>
<rect x="{300 + kw / 2 + 20:.1f}" y="21.5" width="80" height="1" fill="{t['border']}" class="growc"/>
</g>
{words(title, 300, 72, 36, t['fg'], tracking=-1.2, anchor='middle', delay=.1)}
<text x="300" y="102" text-anchor="middle" class="s rise" style="animation-delay:.45s" font-size="16.5" fill="{t['text2']}">{esc(sub)}</text>
"""
    return svg(W, H, f"{title}. {sub}", body)


def divider(name: str) -> str:
    t = THEMES[name]
    W, H = 880, 44
    body = f"""
<defs>
<linearGradient id="l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['border']}" stop-opacity="0"/><stop offset="1" stop-color="{t['thread']}" stop-opacity=".9"/></linearGradient>
<linearGradient id="r" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t['thread']}" stop-opacity=".9"/><stop offset="1" stop-color="{t['border']}" stop-opacity="0"/></linearGradient>
</defs>
<rect x="120" y="21.5" width="298" height="1" fill="url(#l)" class="grow" style="transform-origin:right"/>
<rect x="462" y="21.5" width="298" height="1" fill="url(#r)" class="grow"/>
<g class="rise">{spider(440, 17, 1.7, t['accent'])}</g>
"""
    return svg(W, H, "Decorative divider with a small crimson spider", body)


def button(name: str, label: str, ico: str | None, primary: bool, desc: str) -> str:
    t = THEMES[name]
    h, w, gap, isz, size = 44, 148, 10, 16, 15
    content = isz + gap + measure("d", label, size)
    x0 = (w - content) / 2
    fill, stroke, fg = (t["fg"], t["fg"], t["ink_on_fg"]) if primary else (t["surface"], t["border"], t["fg"])
    if ico == "mail":
        glyph = (f'<g transform="translate({x0:.1f} {h / 2 - 8})" fill="none" stroke="{fg}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round">'
                 f'<rect x="1" y="2.5" width="14" height="11" rx="2.5"/><path d="M1.6 4.2L8 9l6.4-4.8"/></g>')
    elif ico == "globe":
        glyph = (f'<g transform="translate({x0:.1f} {h / 2 - 8})" fill="none" stroke="{fg}" stroke-width="1.5" stroke-linecap="round">'
                 f'<circle cx="8" cy="8" r="6.6"/><path d="M1.4 8h13.2M8 1.4c2.6 2.4 2.6 10.8 0 13.2M8 1.4c-2.6 2.4-2.6 10.8 0 13.2"/></g>')
    else:
        glyph = icon(ico, x0, h / 2 - isz / 2, isz, fg)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{fill}" stroke="{stroke}"/>{glyph}'
            f'<text x="{x0 + isz + gap:.1f}" y="{h / 2 + size * .35:.1f}" class="d" font-size="{size}" fill="{fg}">{esc(label)}</text>')
    return svg(w, h, desc, body)


# ---------------------------------------------------------------- about


ABOUT = [
    ("EDUCATION", "B.Tech CSE", "Computer Science, graduating in 2027"),
    ("ROLE", "Full-Stack Developer", "Interfaces, APIs and data, end to end"),
    ("FOCUS", "Production-ready apps", "Built to ship and hold up under real use"),
    ("INTERESTS", "Scalable systems", "Developer productivity, real-world problems"),
]


def about(name: str, i: int) -> str:
    """One card. Natural size 408x132: two per row on desktop, stacked on phones."""
    t = THEMES[name]
    W, H = 408, 132
    k, title, sub = ABOUT[i]
    deco = ('<g clip-path="url(#c)" opacity=".55">' + web(W - 4, 2, 92, 180, 6, [50, 90, 130], t['thread'], .5, .6) + '</g>') if i == 0 else ''
    body = f"""<g class="rise" style="animation-delay:{i * .1:.2f}s">
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t['surface']}" stroke="{t['border']}"/>
{deco}
<text x="26" y="38" class="m" font-size="11.5" letter-spacing="2.2" fill="{t['accent']}">0{i + 1}  /  {k}</text>
<text x="26" y="78" class="d" font-size="27" letter-spacing="-.9" fill="{t['fg']}">{esc(title)}</text>
<text x="26" y="104" class="s" font-size="14.5" fill="{t['text2']}">{esc(sub)}</text>
</g>"""
    defs = f'<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
    return svg(W, H, f"{k.title()}: {title}. {sub}.", body, defs)


# ---------------------------------------------------------------- toolbox


TOOLBOX = [
    ("FRONTEND", [("React", "react"), ("Next.js", "nextdotjs"), ("TypeScript", "typescript"), ("JavaScript", "javascript"),
                  ("Tailwind CSS", "tailwindcss"), ("HTML", "html5"), ("CSS", "css3")]),
    ("BACKEND", [("Node.js", "nodedotjs"), ("Express", "express"), ("PostgreSQL", "postgresql"), ("MongoDB", "mongodb"),
                 ("Prisma", "prisma"), ("Firebase", "firebase")]),
    ("TOOLS & DEVOPS", [("Git", "git"), ("GitHub", "github"), ("Docker", "docker"), ("Linux", "linux"),
                        ("VS Code", "visualstudiocode"), ("Vercel", "vercel")]),
]


def toolbox(name: str, i: int) -> str:
    """One category card, natural size 268 wide. Chips wrap; all cards share one height."""
    t = THEMES[name]
    W, pad, gap, rowh, vgap = 268, 16, 8, 34, 8

    def layout(items):
        rows, row, w = [], [], 0.0
        for lbl, ico in items:
            cw = chip(0, 0, lbl, ico, t, 0, h=rowh, size=13.5)[1]
            if row and w + gap + cw > W - 2 * pad:
                rows.append(row)
                row, w = [], 0.0
            row.append((lbl, ico, cw))
            w += cw + (gap if len(row) > 1 else 0)
        rows.append(row)
        return rows

    nrows = max(len(layout(items)) for _, items in TOOLBOX)
    H = 56 + nrows * rowh + (nrows - 1) * vgap + 20
    cat, items = TOOLBOX[i]
    out = [f'<g class="rise" style="animation-delay:{i * .1:.2f}s"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t["bg"]}" stroke="{t["border"]}"/>'
           f'<text x="{pad + 4}" y="34" class="m" font-size="11.5" letter-spacing="2.2" fill="{t["accent"]}">0{i + 1}  /  {esc(cat)}</text></g>']
    delay = i * .1
    for r, row in enumerate(layout(items)):
        x = pad
        for lbl, ico, cw in row:
            delay += .04
            out.append(chip(x, 56 + r * (rowh + vgap), lbl, ico, t, delay, h=rowh, size=13.5)[0])
            x += cw + gap
    return svg(W, H, f"{cat.title()}: " + ", ".join(l for l, _ in items) + ".", "".join(out))


# ---------------------------------------------------------------- footer


def footer(name: str) -> str:
    t = THEMES[name]
    W, H = 880, 270
    dark = name == "dark"
    cx = 440

    def bone(x, yv):
        d = math.hypot((x - cx) / 1.7, yv - 150)
        v = .5 * math.exp(-(d / 120) ** 2) * smooth(0, 90, yv + 20) + .07 * smooth(60, 270, yv)
        return v * (1 - .92 * smooth(150, 172, yv) * (1 - smooth(300, 420, abs(x - cx))))

    dots = dither(W, H, 6, bone)
    thread_y = 100
    defs = f"""
<clipPath id="f"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<radialGradient id="halo" cx="{cx}" cy="120" r="320" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{t['glow']}" stop-opacity="{t['glow_op']}"/><stop offset="1" stop-color="{t['glow']}" stop-opacity="0"/></radialGradient>
"""
    body = f"""
<g clip-path="url(#f)">
<rect width="{W}" height="{H}" fill="{t['bg']}"/>
<rect width="{W}" height="{H}" fill="url(#halo)"/>
{web(0, -10, 2, 84, 8, [80, 150, 230, 320], t['thread'], .3, .1)}
{web(880, -10, 96, 178, 8, [80, 150, 230, 320], t['thread'], .3, .1)}
<g class="fadein" style="animation-delay:.2s"><path fill="{t['dot']}" opacity="{.4 if dark else .28}" d="{dots}"/></g>
<g class="sway" style="--ox:{cx}px"><rect x="{cx - .5}" y="0" width="1" height="{thread_y}" fill="{t['thread']}" opacity=".8"/>{spider(cx, thread_y + 12, 3.1, t['accent'], '4', t['bg'])}</g>
{words('Thanks for stopping by.', cx, 196, 34, t['fg'], tracking=-1.2, anchor='middle', delay=.2)}
<text x="{cx}" y="226" text-anchor="middle" class="m rise" style="animation-delay:.9s" font-size="13" letter-spacing="2" fill="{t['text2']}">LET'S BUILD SOMETHING THAT SHIPS.</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{t['border']}"/>
"""
    return svg(W, H, "Thanks for stopping by. Let's build something that ships. A small crimson spider hangs from a thread "
                     "between two spider webs.", body, defs)


# ---------------------------------------------------------------- main


def main() -> None:
    for name in ("dark", "light"):
        print(name)
        write(OUT / f"hero-{name}.svg", hero(name))
        write(OUT / f"divider-{name}.svg", divider(name))
        write(OUT / f"h-about-{name}.svg", header(name, "01", "ABOUT", "Who I am", "Student by degree. Engineer by habit."))
        for i in range(len(ABOUT)):
            write(OUT / f"about-{i + 1}-{name}.svg", about(name, i))
        write(OUT / f"h-toolbox-{name}.svg", header(name, "02", "TOOLBOX", "What I build with", "The stack behind the products."))
        for i, key in enumerate(("frontend", "backend", "tools")):
            write(OUT / f"toolbox-{key}-{name}.svg", toolbox(name, i))
        write(OUT / f"h-activity-{name}.svg", header(name, "03", "ACTIVITY", "Proof of work", "Live from GitHub. Refreshed daily."))
        write(OUT / f"btn-portfolio-{name}.svg", button(name, "Portfolio", "globe", True, "Portfolio: abhijeet-dash.vercel.app"))
        write(OUT / f"btn-github-{name}.svg", button(name, "GitHub", "github", False, "GitHub: Abhijeet-Dashy"))
        write(OUT / f"btn-linkedin-{name}.svg", button(name, "LinkedIn", "linkedin", False, "LinkedIn: abhijeet-dashy"))
        write(OUT / f"btn-email-{name}.svg", button(name, "Email", "mail", False, "Email: dashabhijeet05@gmail.com"))
        write(OUT / f"footer-{name}.svg", footer(name))


if __name__ == "__main__":
    main()
