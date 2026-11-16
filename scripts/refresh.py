"""Builds the live stats panel from real GitHub data. Run daily by .github/workflows/profile.yml.

Writes to $DIST (default ./dist):
    stats-dark.svg, stats-light.svg
        contributions, current and longest streak, stars, contribution graph, top languages

Env: GITHUB_TOKEN (required), GH_USER (default: Abhijeet-Dashy), DIST
Nothing here invents numbers: if the API call fails the script exits non-zero
and the workflow keeps the previous published files.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import THEMES, esc, measure, svg, words, write  # noqa: E402

USER = os.environ.get("GH_USER", "Abhijeet-Dashy")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = Path(os.environ.get("DIST", Path(__file__).resolve().parent.parent / "dist"))

QUERY = """
query($login:String!){
  user(login:$login){
    followers{totalCount}
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
    repositories(ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC, first:100){
      totalCount
      nodes{
        stargazerCount
        languages(first:8, orderBy:{field:SIZE, direction:DESC}){edges{size node{name}}}
      }
    }
  }
}
"""

# markup and config files say little about what someone builds with
LANG_SKIP = {"HTML", "CSS", "SCSS", "Makefile", "Dockerfile", "Shell", "PowerShell", "Batchfile"}


def fetch() -> dict:
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is not set; refusing to render stats without real data.")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-refresh"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors") or not payload["data"]["user"]:
        sys.exit(f"GraphQL error: {payload.get('errors')}")
    return payload["data"]["user"]


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int]:
    """(current, longest) over the calendar window. Today may still be empty without breaking a streak."""
    longest = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    cur, seq = 0, days[:]
    if seq and seq[-1][1] == 0:
        seq = seq[:-1]
    for _, n in reversed(seq):
        if n == 0:
            break
        cur += 1
    return cur, longest


def analyse(user: dict) -> dict:
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    days = [d for d in days if d[0] <= dt.date.today()]
    cur, longest = streaks(days)
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"]]
    week_start = [dt.date.fromisoformat(w["contributionDays"][0]["date"]) for w in cal["weeks"]]
    langs: dict[str, int] = {}
    stars = 0
    for r in user["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            if e["node"]["name"] not in LANG_SKIP:
                langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {"total": cal["totalContributions"], "current": cur, "longest": longest, "weekly": weekly,
            "week_start": week_start, "stars": stars, "repos": user["repositories"]["totalCount"],
            "followers": user["followers"]["totalCount"], "langs": sorted(langs.items(), key=lambda kv: -kv[1])[:5]}


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def smooth_path(pts: list[tuple[float, float]]) -> str:
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx = (x0 + x1) / 2
        d += f"C{mx:.1f} {y0:.1f} {mx:.1f} {y1:.1f} {x1:.1f} {y1:.1f}"
    return d


def tiles(name: str, s: dict, pair: int) -> str:
    """Two stat tiles side by side, natural size 408x120. Two pairs make a row on desktop; they stack on phones."""
    t = THEMES[name]
    allt = [("CONTRIBUTIONS", fmt(s["total"]), "in the last year"),
            ("CURRENT STREAK", str(s["current"]), "day" if s["current"] == 1 else "days"),
            ("LONGEST STREAK", str(s["longest"]), "days, past year"),
            ("STARS EARNED", fmt(s["stars"]), f"across {s['repos']} public repos")]
    out = []
    for j in range(2):
        i = pair * 2 + j
        k, v, sub = allt[i]
        x = j * 208
        hot = i == 1 and s["current"] > 0
        out.append(f"""<g class="rise" style="animation-delay:{i * .08:.2f}s">
<rect x="{x + .5}" y=".5" width="199" height="119" rx="16" fill="{t['surface']}" stroke="{t['border']}"/>
<text x="{x + 22}" y="32" class="m" font-size="11" letter-spacing="2" fill="{t['text3']}">{k}</text>
<text x="{x + 22}" y="80" class="d" font-size="46" letter-spacing="-1.8" fill="{t['accent'] if hot else t['fg']}">{v}</text>
<text x="{x + 22}" y="104" class="s" font-size="13.5" fill="{t['text2']}">{esc(sub)}</text>
</g>""")
    names = ", ".join(f"{allt[pair * 2 + j][0].title()} {allt[pair * 2 + j][1]} {allt[pair * 2 + j][2]}" for j in range(2))
    return svg(408, 120, f"GitHub stats for {USER}: {names}.", "".join(out))


def graph(name: str, s: dict) -> str:
    t = THEMES[name]
    W, H = 816, 196
    out = [f'<g class="rise"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t["surface"]}" stroke="{t["border"]}"/>'
           f'<text x="22" y="32" class="m" font-size="11.5" letter-spacing="2" fill="{t["text3"]}">CONTRIBUTION GRAPH</text>'
           f'<text x="{W - 22}" y="32" text-anchor="end" class="m" font-size="11.5" letter-spacing="1" fill="{t["text3"]}">WEEKLY TOTALS, LAST YEAR</text></g>']
    px0, px1, py0, py1 = 36, W - 36, 62, H - 38
    wk = s["weekly"]
    peak = max(max(wk), 1)
    n = len(wk)
    pts = [(px0 + (px1 - px0) * i / (n - 1), py1 - (py1 - py0) * v / peak) for i, v in enumerate(wk)]
    grid = "".join(f'<path d="M{px0} {py1 - (py1 - py0) * f:.1f}H{px1}" stroke="{t["border"]}" stroke-dasharray="2 5"/>' for f in (0, .5, 1))
    line = smooth_path(pts)
    area = f"{line}L{px1} {py1}L{px0} {py1}Z"
    months, last_m = "", None
    for (x, _), d in zip(pts, s["week_start"]):
        if d.month != last_m and d.day <= 7 and x < px1 - 24:
            months += f'<text x="{x:.1f}" y="{H - 14}" class="m" font-size="11" fill="{t["text3"]}">{d.strftime("%b").upper()}</text>'
        if d.day <= 7:
            last_m = d.month
    pi = wk.index(max(wk))
    ppx, ppy = pts[pi]
    anchor = "end" if ppx > W - 140 else "start"
    lx = ppx - 10 if anchor == "end" else ppx + 10
    out.append(f"""<g class="rise" style="animation-delay:.2s">
<defs><linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t['accent']}" stop-opacity=".30"/><stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></linearGradient></defs>
{grid}
<path d="{area}" fill="url(#ar)" class="fadein" style="animation-delay:1s"/>
<path d="{line}" fill="none" stroke="{t['accent']}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" pathLength="1" class="draw" style="animation-delay:.5s"/>
<circle cx="{ppx:.1f}" cy="{ppy:.1f}" r="4" fill="{t['bg']}" stroke="{t['accent']}" stroke-width="2"/>
<text x="{lx:.1f}" y="{max(ppy + 4, py0 - 4):.1f}" text-anchor="{anchor}" class="m" font-size="12" fill="{t['text2']}">peak week: {peak}</text>
{months}
</g>""")
    return svg(W, H, f"Contribution graph for {USER}: weekly contributions over the last year, peaking at {peak} in one week.", "".join(out))


def langs(name: str, s: dict) -> str:
    t = THEMES[name]
    W, H = 816, 104
    items = s["langs"]
    total = sum(v for _, v in items) or 1
    shades = [t["accent"], t["fg"], t["text2"], t["text3"], t["border"]]
    segs, x = [], 22.0
    for i, (nm, v) in enumerate(items):
        w = (W - 44) * v / total
        segs.append(f'<rect x="{x:.1f}" y="46" width="{max(w - 3, 2):.1f}" height="8" rx="4" fill="{shades[i]}"/>')
        x += w
    labels, lx = [], 22.0
    for i, (nm, v) in enumerate(items):
        lab = f"{nm} {v * 100 / total:.0f}%"
        labels.append(f'<circle cx="{lx + 4}" cy="80" r="4" fill="{shades[i]}"/>'
                      f'<text x="{lx + 14}" y="84.5" class="s" font-size="14" fill="{t["text2"]}">{esc(lab)}</text>')
        lx += 14 + measure("s", lab, 14) + 28
    body = (f'<g class="rise"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{t["surface"]}" stroke="{t["border"]}"/>'
            f'<text x="22" y="32" class="m" font-size="11.5" letter-spacing="2" fill="{t["text3"]}">TOP LANGUAGES</text>{"".join(segs)}{"".join(labels)}</g>')
    label = f"Top languages across public repositories of {USER}: " + ", ".join(f"{n} {v * 100 / total:.0f}%" for n, v in items) + "."
    return svg(W, H, label, body)


def main() -> None:
    s = analyse(fetch())
    DIST.mkdir(parents=True, exist_ok=True)
    for name in ("dark", "light"):
        write(DIST / f"stats-a-{name}.svg", tiles(name, s, 0))
        write(DIST / f"stats-b-{name}.svg", tiles(name, s, 1))
        write(DIST / f"graph-{name}.svg", graph(name, s))
        write(DIST / f"langs-{name}.svg", langs(name, s))


if __name__ == "__main__":
    main()
