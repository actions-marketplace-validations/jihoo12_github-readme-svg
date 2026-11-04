"""Animated SVGs built from a GitHub contribution graph.

Data is fetched without a token from the public page https://github.com/users/<user>/contributions.
"""

from __future__ import annotations

import datetime as dt
import html
import math
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

# (background, empty cell, levels 1..4)
PALETTES = {
    "green": ("#0d1117", "#161b22", ["#0e4429", "#006d32", "#26a641", "#39d353"]),
    "halloween": ("#0d1117", "#161b22", ["#631c03", "#bd561d", "#fa7a18", "#fddf68"]),
    "ice": ("#0b1020", "#151c2e", ["#0a3069", "#0969da", "#54aeff", "#b6e3ff"]),
    "neon": ("#0b0221", "#1b0b35", ["#5a0f62", "#a3179d", "#ff3df2", "#ffd1fb"]),
}


@dataclass
class Day:
    date: dt.date
    level: int
    count: int


@dataclass
class Calendar:
    user: str
    days: list[Day]

    @property
    def total(self) -> int:
        return sum(d.count for d in self.days)

    @property
    def best(self) -> Day:
        return max(self.days, key=lambda d: d.count)

    @property
    def longest_streak(self) -> int:
        best = cur = 0
        for d in self.days:
            cur = cur + 1 if d.count > 0 else 0
            best = max(best, cur)
        return best

    @property
    def current_streak(self) -> int:
        days = list(self.days)
        if days and days[-1].count == 0:  # today may not be over yet, so count from yesterday
            days.pop()
        n = 0
        for d in reversed(days):
            if d.count == 0:
                break
            n += 1
        return n


# ---------------------------------------------------------------- data fetching

def fetch_html(user: str) -> str:
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "github-readme-svg"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse(user: str, page: str) -> Calendar:
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        text = html.unescape(m.group(2)).strip()
        n = re.match(r"([\d,]+) contribution", text)
        tips[m.group(1)] = int(n.group(1).replace(",", "")) if n else 0

    days = []
    for m in re.finditer(r"<td\b[^>]*ContributionCalendar-day[^>]*>", page):
        tag = m.group(0)
        date = re.search(r'data-date="([\d-]+)"', tag)
        level = re.search(r'data-level="(\d)"', tag)
        cid = re.search(r'\bid="([^"]+)"', tag)
        if not (date and level):
            continue
        lvl = int(level.group(1))
        count = tips.get(cid.group(1), lvl) if cid else lvl
        days.append(Day(dt.date.fromisoformat(date.group(1)), lvl, count))
    if not days:
        raise SystemExit(f"no contribution data found for '{user}' (check the username)")
    days.sort(key=lambda d: d.date)
    return Calendar(user, days)


def load(user: str, html_file: str | None = None) -> Calendar:
    page = Path(html_file).read_text(encoding="utf-8") if html_file else fetch_html(user)
    return parse(user, page)


def grid_pos(cal: Calendar, day: Day) -> tuple[int, int]:
    """(week index, weekday index; Sunday = 0)"""
    first_sunday = cal.days[0].date - dt.timedelta(days=cal.days[0].date.isoweekday() % 7)
    return (day.date - first_sunday).days // 7, day.date.isoweekday() % 7


# ---------------------------------------------------------------- shared pieces

def esc(s: str) -> str:
    return html.escape(s, quote=True)


def fmt(n: int) -> str:
    return f"{n:,}"


def count_up(x: float, y: float, value: int, cls: str, cycle: float,
             start: float, dur: float, suffix: str = "", anchor: str = "start", frames: int = 24) -> str:
    """Count-up number. SVG cannot animate text content, so one <text> per value is shown in turn."""
    vals = []
    for i in range(frames + 1):
        v = round(value * (1 - (1 - i / frames) ** 3))  # easeOutCubic
        if not vals or v != vals[-1]:
            vals.append(v)
    if len(vals) == 1:
        return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{fmt(value)}{esc(suffix)}</text>'
    out = []
    step = dur / (len(vals) - 1)
    for i, v in enumerate(vals):
        t0 = (start + i * step) / cycle
        t1 = (start + (i + 1) * step) / cycle
        if i == 0:
            kt, vs = "0;" + f"{t1:.4f}", "1;0"
        elif i == len(vals) - 1:
            kt, vs = f"0;{t0:.4f}", "0;1"
        else:
            kt, vs = f"0;{t0:.4f};{t1:.4f}", "0;1;0"
        out.append(
            f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" opacity="0">{fmt(v)}{esc(suffix)}'
            f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{vs}"/></text>'
        )
    return "".join(out)


def stat_cards(cal: Calendar, x0: float, y: float, width: float, cycle: float, accent: str) -> str:
    best = cal.best
    items = [
        ("Total contributions", cal.total, "", f"{cal.days[0].date:%b %Y} – {cal.days[-1].date:%b %Y}"),
        ("Current streak", cal.current_streak, " days", "keep it going!" if cal.current_streak else "start today"),
        ("Longest streak", cal.longest_streak, " days", "past year"),
        ("Best day", best.count, "", f"{best.date:%b %-d, %Y}"),
    ]
    gap = 14
    cw = (width - gap * (len(items) - 1)) / len(items)
    out = []
    for i, (label, value, suffix, note) in enumerate(items):
        cx = x0 + i * (cw + gap)
        out.append(f"""
  <g class="card" style="animation-delay:{0.1 + i * 0.12:.2f}s">
    <rect x="{cx:.1f}" y="{y}" width="{cw:.1f}" height="64" rx="10" class="cardbg"/>
    <rect x="{cx:.1f}" y="{y}" width="3" height="64" rx="1.5" fill="{accent}"/>
    <text x="{cx + 16:.1f}" y="{y + 20}" class="label">{esc(label)}</text>
    {count_up(cx + 16, y + 44, value, "value", cycle, 0.3 + i * 0.12, 1.8, suffix)}
    <text x="{cx + 16:.1f}" y="{y + 58}" class="note">{esc(note)}</text>
  </g>""")
    return "".join(out)


BASE_CSS = f"""
    .title {{ font: 700 20px {SANS}; fill: #e6edf3; }}
    .sub   {{ font: 400 13px {SANS}; fill: #8b949e; }}
    .label {{ font: 600 11px {SANS}; fill: #8b949e; letter-spacing: .5px; text-transform: uppercase; }}
    .value {{ font: 800 20px {SANS}; fill: #e6edf3; }}
    .note  {{ font: 400 10px {SANS}; fill: #6e7681; }}
    .cardbg {{ fill: #ffffff; fill-opacity: .04; stroke: #ffffff; stroke-opacity: .08; }}
    .card  {{ animation: cardIn .8s cubic-bezier(.2,.8,.2,1) both; }}
    @keyframes cardIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
"""


# ---------------------------------------------------------------- style 1: 2D grid

def build_grid(cal: Calendar, palette: str) -> str:
    bg, empty, levels = PALETTES[palette]
    W, H = 900, 300
    cell, gap = 12, 3
    pitch = cell + gap
    weeks = max(grid_pos(cal, d)[0] for d in cal.days) + 1
    gx = (W - weeks * pitch) / 2 + 10
    gy = 150
    cycle = 12.0
    beam_start, beam_dur = 3.0, 2.6
    beam_from, beam_to = gx - 60, gx + weeks * pitch + 20

    cells, flashes, months = [], [], []
    last_month = None
    for d in cal.days:
        w, wd = grid_pos(cal, d)
        x, y = gx + w * pitch, gy + wd * pitch
        color = levels[d.level - 1] if d.level else empty
        delay = (w + wd) * 0.03
        cells.append(
            f'<rect class="cell" x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{color}" '
            f'style="animation-delay:{delay:.2f}s"><title>{d.count} on {d.date}</title></rect>'
        )
        if d.level:
            # flash in sync with the moment the beam passes
            t = beam_start + beam_dur * (x + cell / 2 - beam_from - 60) / (beam_to - beam_from)  # timed to the beam's bright right edge
            flashes.append(
                f'<rect class="flash" x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                f'style="animation-delay:{t:.2f}s;--o:{0.35 + 0.15 * d.level:.2f}"/>'
            )
        if wd == 0 and d.date.month != last_month and d.date.day <= 7:
            months.append(f'<text x="{x:.1f}" y="{gy - 8}" class="axis">{d.date:%b}</text>')
            last_month = d.date.month
    weekdays = "".join(
        f'<text x="{gx - 8:.1f}" y="{gy + i * pitch + 10}" class="axis" text-anchor="end">{n}</text>'
        for i, n in [(1, "Mon"), (3, "Wed"), (5, "Fri")]
    )
    lx = gx + weeks * pitch - 5 * pitch - 70
    legend = (
        f'<text x="{lx:.1f}" y="{gy + 7 * pitch + 22}" class="axis">Less</text>'
        + "".join(
            f'<rect x="{lx + 30 + i * pitch:.1f}" y="{gy + 7 * pitch + 12}" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>'
            for i, c in enumerate([empty, *levels])
        )
        + f'<text x="{lx + 34 + 5 * pitch:.1f}" y="{gy + 7 * pitch + 22}" class="axis">More</text>'
    )
    beam_dx = beam_to - beam_from
    b0, b1 = beam_start / cycle * 100, (beam_start + beam_dur) / cycle * 100

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(cal.user)} contributions">
  <title>{esc(cal.user)}'s GitHub contributions</title>
  <defs>
    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{levels[3]}" stop-opacity="0"/>
      <stop offset=".85" stop-color="{levels[3]}" stop-opacity=".35"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity=".9"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <style>{BASE_CSS}
    .axis  {{ font: 400 10px {SANS}; fill: #6e7681; }}
    .cell  {{ animation: pop {cycle}s cubic-bezier(.2,.8,.2,1) infinite both; transform-box: fill-box; transform-origin: center; }}
    .flash {{ fill: #ffffff; opacity: 0; animation: flash {cycle}s ease-out infinite both; }}
    .beam  {{ animation: sweep {cycle}s linear infinite; }}
    @keyframes pop {{
      0% {{ transform: scale(0); opacity: 0; }}
      5% {{ transform: scale(1.25); opacity: 1; }}
      8%, 86% {{ transform: scale(1); opacity: 1; }}
      92%, 100% {{ transform: scale(0); opacity: 0; }}
    }}
    @keyframes flash {{ 0% {{ opacity: 0; }} .4% {{ opacity: var(--o); }} 6%, 100% {{ opacity: 0; }} }}
    @keyframes sweep {{
      0%, {b0:.1f}% {{ transform: translateX(0); opacity: 0; }}
      {b0 + 0.5:.1f}% {{ opacity: 1; }}
      {b1:.1f}% {{ transform: translateX({beam_dx:.0f}px); opacity: 1; }}
      {b1 + 0.5:.1f}%, 100% {{ transform: translateX({beam_dx:.0f}px); opacity: 0; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} text[opacity="0"] {{ display: none; }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{bg}"/>
    <text x="{gx - 40:.1f}" y="36" class="title">@{esc(cal.user)}</text>
    <text x="{gx - 40 + 12 * (len(cal.user) + 1) + 10:.1f}" y="36" class="sub">contributions in the last year</text>
    {stat_cards(cal, gx - 40, 52, weeks * pitch + 40, cycle, levels[2])}
    {"".join(months)}
    {weekdays}
    {"".join(cells)}
    {"".join(flashes)}
    <rect class="beam" x="{beam_from:.1f}" y="{gy - 6}" width="60" height="{7 * pitch + 9}" fill="url(#beam)" opacity="0"/>
    {legend}
  </g>
</svg>
"""


# ---------------------------------------------------------------- style 2: 3D city

def shade(hex_color: str, k: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{max(0, min(255, round(c * k))):02x}" for c in (r, g, b))


def build_city(cal: Calendar, palette: str) -> str:
    bg, empty, levels = PALETTES[palette]
    W, H = 900, 420
    ux, uy = 12.6, 2.4   # screen offset per week
    vx, vy = -7.0, 6.4   # screen offset per weekday
    max_h = 90
    weeks = max(grid_pos(cal, d)[0] for d in cal.days) + 1
    ox = (W - (weeks * ux - 7 * vx)) / 2 - 7 * vx
    oy = 228
    peak = max(1, cal.best.count)
    cycle = 12.0

    def pt(w: float, d: float, z: float = 0) -> tuple[float, float]:
        return ox + w * ux + d * vx, oy + w * uy + d * vy - z

    def poly(points, fill) -> str:
        return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="{fill}"/>'

    bars = []
    for d in sorted(cal.days, key=lambda d: (grid_pos(cal, d)[1], grid_pos(cal, d)[0])):
        w, wd = grid_pos(cal, d)
        p00, p10, p11, p01 = pt(w, wd), pt(w + .82, wd), pt(w + .82, wd + .82), pt(w, wd + .82)
        if not d.count:
            bars.append(poly([p00, p10, p11, p01], empty))
            continue
        z = 4 + max_h * math.sqrt(d.count / peak)
        top = [(x, y - z) for x, y in (p00, p10, p11, p01)]
        color = levels[d.level - 1]
        delay = 0.4 + (w + wd) * 0.032
        bars.append(
            f'<g class="bar" style="animation-delay:{delay:.2f}s"><title>{d.count} on {d.date}</title>'
            + poly([p01, p11, top[2], top[3]], shade(color, .62))   # front face
            + poly([p10, p11, top[2], top[1]], shade(color, .8))    # right face
            + poly(top, shade(color, 1.12))                         # top face
            + "</g>"
        )

    # base plate
    g0, g1, g2, g3 = pt(-0.6, -0.6), pt(weeks + 0.4, -0.6), pt(weeks + 0.4, 7.4), pt(-0.6, 7.4)
    base_depth = 10
    ground = (
        poly([g3, g2, (g2[0], g2[1] + base_depth), (g3[0], g3[1] + base_depth)], shade(empty, .7))
        + poly([g1, g2, (g2[0], g2[1] + base_depth), (g1[0], g1[1] + base_depth)], shade(empty, .9))
        + poly([g0, g1, g2, g3], shade(empty, 1.25))
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(cal.user)} contributions city">
  <title>{esc(cal.user)}'s GitHub contributions in 3D</title>
  <defs>
    <radialGradient id="sky" cx="50%" cy="85%" r="75%">
      <stop offset="0" stop-color="{levels[1]}" stop-opacity=".35"/>
      <stop offset="1" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#000" flood-opacity=".55"/>
    </filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <style>{BASE_CSS}
    .bar   {{ animation: grow {cycle}s cubic-bezier(.2,.9,.25,1.15) infinite both; transform-box: fill-box; transform-origin: 50% 100%; }}
    .float {{ animation: float 6s ease-in-out infinite; }}
    @keyframes grow {{
      0% {{ transform: scaleY(0); opacity: 0; }}
      1% {{ opacity: 1; }}
      7%, 85% {{ transform: scaleY(1); opacity: 1; }}
      92%, 100% {{ transform: scaleY(0); opacity: 0; }}
    }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} text[opacity="0"] {{ display: none; }} }}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{bg}"/>
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <text x="40" y="38" class="title">@{esc(cal.user)}</text>
    <text x="{40 + 12 * (len(cal.user) + 1) + 10}" y="38" class="sub">contributions in the last year</text>
    {stat_cards(cal, 40, 54, W - 80, cycle, levels[2])}
    <g class="float">
      <g filter="url(#shadow)">{ground}</g>
      {"".join(bars)}
    </g>
  </g>
</svg>
"""


STYLES = {"contrib-grid": build_grid, "contrib-city": build_city}
