"""Builds the three live stat tiles from real GitHub data. Run daily by .github/workflows/profile.yml.

Writes to $DIST (default ./dist), each as -dark.svg and -light.svg:
    stat-total     contributions in the last year
    stat-current   current streak, in days
    stat-longest   longest streak in the last year, in days

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
from common import THEMES, esc, svg, write  # noqa: E402

USER = os.environ.get("GH_USER", "Abhijeet-Dashy")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = Path(os.environ.get("DIST", Path(__file__).resolve().parent.parent / "dist"))

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
  }
}
"""


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
    return payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int]:
    """(current, longest). Today may still be empty without breaking the current streak."""
    longest = run = 0
    for _, n in days:
        run = run + 1 if n > 0 else 0
        longest = max(longest, run)
    seq = days[:-1] if days and days[-1][1] == 0 else days
    cur = 0
    for _, n in reversed(seq):
        if n == 0:
            break
        cur += 1
    return cur, longest


def analyse(cal: dict) -> dict:
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    days = [d for d in days if d[0] <= dt.date.today()]
    cur, longest = streaks(days)
    return {"total": cal["totalContributions"], "current": cur, "longest": longest}


def fmt(n: int) -> str:
    return f"{n:,}"


def tile(name: str, kind: str, label: str, value: str, sub: str, delay: float, hot: bool = False) -> str:
    """One tile, natural size 270x120: three across on desktop, stacked on phones."""
    t = THEMES[name]
    body = f"""<g class="rise" style="animation-delay:{delay:.2f}s">
<rect x=".5" y=".5" width="269" height="119" rx="16" fill="{t['surface']}" stroke="{t['border']}"/>
<text x="24" y="34" class="m" font-size="11.5" letter-spacing="2" fill="{t['text3']}">{esc(label)}</text>
<text x="24" y="82" class="d" font-size="48" letter-spacing="-2" fill="{t['accent'] if hot else t['fg']}">{esc(value)}</text>
<text x="24" y="105" class="s" font-size="14" fill="{t['text2']}">{esc(sub)}</text>
</g>"""
    return svg(270, 120, f"{label.title()} for {USER} on GitHub: {value} {sub}.", body)


def main() -> None:
    s = analyse(fetch())
    for name in ("dark", "light"):
        write(DIST / f"stat-total-{name}.svg",
              tile(name, "total", "CONTRIBUTIONS", fmt(s["total"]), "in the last year", 0))
        write(DIST / f"stat-current-{name}.svg",
              tile(name, "current", "CURRENT STREAK", str(s["current"]), "day in a row" if s["current"] == 1 else "days in a row", .08, s["current"] > 0))
        write(DIST / f"stat-longest-{name}.svg",
              tile(name, "longest", "LONGEST STREAK", str(s["longest"]), "days in a row, past year", .16))


if __name__ == "__main__":
    main()
