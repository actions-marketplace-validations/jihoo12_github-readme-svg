#!/usr/bin/env python3
"""Animated SVG banner generator for GitHub READMEs.

Uses only the Python standard library.
GitHub renders README SVGs through <img>, so JavaScript does not run,
but CSS animations and SMIL (<animate>) do. This script uses only those two.

Examples:
    python3 generate.py --style synthwave --name "Jihoo" --line "I build things with Nix & Python"
    python3 generate.py --style contrib-city --user jihoo12 --palette neon
    python3 generate.py --style all --user jihoo12
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import contrib
import creative
import spectacle
from common import MONO, SANS, THEMES, esc
from common import stars as _stars
from common import text_width as _text_width

WIDTH = 900
HEIGHT = 260
FONT_SIZE = 22
CHAR_W = FONT_SIZE * 0.6  # approximate monospace glyph width

def text_width(s: str) -> float:
    return _text_width(s, FONT_SIZE)


def stars(n: int, rng: random.Random, w: float = WIDTH, h: float = HEIGHT * 0.75) -> str:
    return _stars(n, rng, w, h)


def wave_path(amp: float, base: float, wavelength: float) -> str:
    # wave twice the canvas width, so translating by one width loops seamlessly
    d = [f"M0 {base}"]
    x = 0.0
    while x < WIDTH * 2:
        d.append(f"q {wavelength / 4} {-amp} {wavelength / 2} 0 t {wavelength / 2} 0")
        x += wavelength
    d.append(f"V {HEIGHT} H 0 Z")
    return " ".join(d)


def typing_lines(lines: list[str], y: float, type_speed: float, hold: float) -> tuple[str, float]:
    """Loop several lines with SMIL: type -> pause -> erase."""
    slots = []
    for line in lines:
        n = len(line)
        t_type = n * type_speed
        t_erase = n * type_speed * 0.5
        slots.append((line, t_type, hold, t_erase))
    total = sum(a + b + c for _, a, b, c in slots) + 0.4 * len(slots)

    parts = []
    start = 0.0
    for idx, (line, t_type, t_hold, t_erase) in enumerate(slots):
        widths = [text_width(line[:i]) for i in range(len(line) + 1)]
        full = widths[-1]
        x0 = (WIDTH - full) / 2

        # (time, width) keyframes: type -> hold -> erase -> hidden
        frames: list[tuple[float, float]] = [(0.0, 0.0)]
        if start > 0:
            frames.append((start, 0.0))
        for i in range(1, len(line) + 1):
            frames.append((start + i * (t_type / len(line)), widths[i]))
        end_hold = start + t_type + t_hold
        frames.append((end_hold, full))
        for i in range(len(line) - 1, -1, -1):
            frames.append((end_hold + (len(line) - i) * (t_erase / len(line)), widths[i]))
        frames.append((total, 0.0))

        # keyTimes must increase monotonically, start at 0 and end at 1
        kt, vals, last = [], [], -1.0
        for t, w in frames:
            k = min(max(t / total, 0.0), 1.0)
            if k <= last:
                k = last + 1e-6
            kt.append(k)
            vals.append(w)
            last = k
        kt[-1] = 1.0
        key_times = ";".join(f"{k:.6f}" for k in kt)
        w_vals = ";".join(f"{w:.1f}" for w in vals)
        cur_vals = ";".join(f"{x0 + w:.1f}" for w in vals)
        # in discrete mode each value holds until the next keyTime, so the cursor must be
        # hidden on the frame where erasing ends (width 0), or it lingers
        vis = ";".join("1" if (start <= t < end_hold + t_erase) else "0" for t, _ in frames)

        parts.append(f"""
  <clipPath id="clip{idx}">
    <rect x="{x0:.1f}" y="{y - FONT_SIZE}" height="{FONT_SIZE * 1.6}" width="0">
      <animate attributeName="width" dur="{total:.2f}s" repeatCount="indefinite"
        calcMode="discrete" keyTimes="{key_times}" values="{w_vals}"/>
    </rect>
  </clipPath>
  <text x="{x0:.1f}" y="{y}" class="type" clip-path="url(#clip{idx})">{esc(line)}</text>
  <rect class="cursor" x="{x0:.1f}" y="{y - FONT_SIZE + 2}" width="3" height="{FONT_SIZE + 4}" opacity="0">
    <animate attributeName="x" dur="{total:.2f}s" repeatCount="indefinite"
      calcMode="discrete" keyTimes="{key_times}" values="{cur_vals}"/>
    <animate attributeName="opacity" dur="{total:.2f}s" repeatCount="indefinite"
      calcMode="discrete" keyTimes="{key_times}" values="{vis}"/>
  </rect>""")
        start = end_hold + t_erase + 0.4
    return "".join(parts), total


def build_banner(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    bg, (c1, c2, c3) = THEMES[theme]
    rng = random.Random(seed)
    typing, _ = typing_lines(lines, y=150, type_speed=0.08, hold=1.6)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{esc(name)}">
  <title>{esc(name)}</title>
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{c1}"><animate attributeName="stop-color" values="{c1};{c2};{c3};{c1}" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="50%" stop-color="{c2}"><animate attributeName="stop-color" values="{c2};{c3};{c1};{c2}" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="{c3}"><animate attributeName="stop-color" values="{c3};{c1};{c2};{c3}" dur="8s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="0%" r="80%">
      <stop offset="0%" stop-color="{c1}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{WIDTH}" height="{HEIGHT}" rx="18"/></clipPath>
  </defs>
  <style>
    .title {{ font: 800 56px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: url(#grad);
             animation: rise 1.2s cubic-bezier(.2,.8,.2,1) both; }}
    .type  {{ font: 500 {FONT_SIZE}px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #e6edf3; }}
    .cursor {{ fill: {c2}; }}
    .star  {{ fill: #fff; animation: twinkle ease-in-out infinite; }}
    .wave  {{ animation: drift linear infinite; }}
    .orb   {{ animation: float 6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes rise    {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes twinkle {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
    @keyframes drift   {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-{WIDTH}px); }} }}
    @keyframes float   {{ 0%,100% {{ transform: translateY(0) scale(1); }} 50% {{ transform: translateY(-14px) scale(1.08); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{WIDTH}" height="{HEIGHT}" fill="{bg}"/>
    <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#glow)"/>
    {stars(60, rng)}
    <circle class="orb" cx="90" cy="70" r="38" fill="{c1}" opacity=".18"/>
    <circle class="orb" cx="{WIDTH - 110}" cy="60" r="26" fill="{c3}" opacity=".22" style="animation-delay:-2s"/>
    <path class="wave" style="animation-duration:14s" d="{wave_path(10, HEIGHT - 52, 300)}" fill="{c1}" opacity=".25"/>
    <path class="wave" style="animation-duration:9s"  d="{wave_path(8, HEIGHT - 36, 225)}" fill="{c2}" opacity=".25"/>
    <path class="wave" style="animation-duration:6s"  d="{wave_path(6, HEIGHT - 20, 180)}" fill="{c3}" opacity=".3"/>
  </g>

  <text x="50%" y="95" text-anchor="middle" class="title">{esc(name)}</text>
  {typing}
</svg>
"""


def build_synthwave(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Retro synthwave: self-drawing neon title + striped sun + approaching perspective grid."""
    W, H, horizon = 900, 300, 200
    rng = random.Random(seed)
    cx = W / 2

    # perspective grid: verticals fanning from the vanishing point + ease-in horizontal rows
    verticals = "\n    ".join(
        f'<line x1="{cx}" y1="{horizon}" x2="{cx + i * 90}" y2="{H}"/>' for i in range(-16, 17)
    )
    n_rows, row_dur = 8, 4.0
    rows = "\n    ".join(
        f'<line class="row" x1="0" y1="{horizon}" x2="{W}" y2="{horizon}" '
        f'style="animation-delay:-{i * row_dur / n_rows:.2f}s"/>'
        for i in range(n_rows)
    )
    # horizontal stripes across the lower sun (thicker toward the bottom)
    stripes = "\n      ".join(
        f'<rect x="0" y="{horizon - 62 + i * 13 + i * i * 0.4:.1f}" width="{W}" height="{1.5 + i * 1.3:.1f}" fill="#000"/>'
        for i in range(6)
    )
    subtitle = esc(lines[0]) if lines else ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(name)}">
  <title>{esc(name)}</title>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0b0221"/><stop offset=".7" stop-color="#2b0a4a"/><stop offset="1" stop-color="#5a0f62"/>
    </linearGradient>
    <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe86b"/><stop offset=".5" stop-color="#ff7a59"/><stop offset="1" stop-color="#ff2a8a"/>
    </linearGradient>
    <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1a0433"/><stop offset="1" stop-color="#05010d"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".35" stop-color="#fff" stop-opacity="1"/>
    </linearGradient>
    <mask id="sunMask">
      <rect width="{W}" height="{H}" fill="#fff"/>
      {stripes}
    </mask>
    <mask id="floorFade"><rect y="{horizon}" width="{W}" height="{H - horizon}" fill="url(#fade)"/></mask>
    <filter id="neon" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b1"/>
      <feGaussianBlur stdDeviation="9" result="b2"/>
      <feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="sunGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <clipPath id="aboveHorizon"><rect width="{W}" height="{horizon}"/></clipPath>
  </defs>
  <style>
    .star  {{ fill: #fff; animation: twinkle ease-in-out infinite; }}
    .grid  {{ stroke: #ff3df2; stroke-width: 1.4; opacity: .85; }}
    .row   {{ animation: approach {row_dur}s cubic-bezier(.55,0,1,.45) infinite; }}
    .sun   {{ animation: pulse 5s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .draw  {{ font: 900 72px {SANS}; fill: none; stroke: #4df3ff; stroke-width: 2;
             stroke-dasharray: 420; animation: draw 9s ease-in-out infinite; }}
    .fill  {{ font: 900 72px {SANS}; fill: #e9fdff; animation: fillIn 9s ease-in-out infinite; }}
    .neon  {{ animation: flicker 9s linear infinite; }}
    .sub   {{ font: 600 18px {MONO}; fill: #ffe3fa; letter-spacing: 4px; paint-order: stroke; stroke: #1a0433; stroke-width: 5px; stroke-linejoin: round; animation: fadeUp 9s ease-out infinite; }}
    .scan  {{ animation: scan 7s linear infinite; }}
    @keyframes twinkle {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
    @keyframes approach {{ from {{ transform: translateY(0); opacity: 0; }} 15% {{ opacity: 1; }} to {{ transform: translateY({H - horizon}px); opacity: 1; }} }}
    @keyframes pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.04); }} }}
    @keyframes draw {{ 0% {{ stroke-dashoffset: 420; }} 30% {{ stroke-dashoffset: 0; }} 90% {{ stroke-dashoffset: 0; opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
    @keyframes fillIn {{ 0%,28% {{ opacity: 0; }} 38%,90% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
    @keyframes flicker {{ 0%,40%,44%,46%,70%,72%,100% {{ opacity: 1; }} 42%,45%,71% {{ opacity: .35; }} }}
    @keyframes fadeUp {{ 0%,35% {{ opacity: 0; transform: translateY(8px); }} 45%,90% {{ opacity: 1; transform: none; }} 100% {{ opacity: 0; }} }}
    @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY({H}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .draw {{ stroke-dashoffset: 0; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    {stars(45, rng, W, horizon - 40)}
    <g clip-path="url(#aboveHorizon)">
      <circle cx="{cx}" cy="{horizon - 10}" r="105" fill="#ff4f9a" opacity=".55" filter="url(#sunGlow)"/>
      <circle class="sun" cx="{cx}" cy="{horizon - 10}" r="95" fill="url(#sun)" mask="url(#sunMask)"/>
    </g>
    <rect y="{horizon}" width="{W}" height="{H - horizon}" fill="url(#floor)"/>
    <g class="grid" mask="url(#floorFade)">
    {verticals}
    {rows}
    </g>
    <line x1="0" y1="{horizon}" x2="{W}" y2="{horizon}" stroke="#ff8af5" stroke-width="2" filter="url(#neon)"/>
    <rect class="scan" width="{W}" height="40" fill="#fff" opacity=".04"/>
  </g>

  <g class="neon" filter="url(#neon)">
    <text x="50%" y="118" text-anchor="middle" class="draw">{esc(name)}</text>
    <text x="50%" y="118" text-anchor="middle" class="fill">{esc(name)}</text>
  </g>
  <text x="50%" y="160" text-anchor="middle" class="sub">{subtitle}</text>
</svg>
"""


# katakana renders as boxes without a Japanese font, so use only characters every monospace font has
MATRIX_CHARS = "0123456789ABCDEFXZ<>{}[]()=+*#$%&@/\\|;:"


def build_matrix(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Matrix code rain + glitch title + typewriter subtitle."""
    W, H = WIDTH, HEIGHT
    rng = random.Random(seed)

    cols = []
    x = 6.0
    while x < W:
        size = rng.choice([12, 14, 16, 18])
        n = rng.randint(10, 20)
        chars = "".join(rng.choice(MATRIX_CHARS) for _ in range(n))
        col_h = n * size * 1.1
        dur = rng.uniform(3.5, 8) * (18 / size)  # smaller glyphs = farther away = slower
        tspans = "".join(f'<tspan x="{x:.0f}" dy="{size * 1.1:.1f}">{esc(c)}</tspan>' for c in chars)
        cols.append(
            f'<text class="rain" font-size="{size}" opacity="{size / 18:.2f}" y="0" '
            f'style="--h:{col_h:.0f}px;animation-duration:{dur:.2f}s;animation-delay:-{rng.uniform(0, dur):.2f}s">{tspans}</text>'
        )
        x += size * 1.05
    rain = "\n    ".join(cols)
    typing, _ = typing_lines(lines, y=178, type_speed=0.07, hold=1.6)
    t = esc(name)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{t}">
  <title>{t}</title>
  <defs>
    <linearGradient id="trail" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#00ff6a" stop-opacity="0"/>
      <stop offset=".8" stop-color="#00ff6a" stop-opacity=".9"/>
      <stop offset="1" stop-color="#d7ffe6"/>
    </linearGradient>
    <radialGradient id="vignette" cx="50%" cy="50%" r="60%">
      <stop offset="0" stop-color="#000" stop-opacity=".85"/>
      <stop offset=".55" stop-color="#000" stop-opacity=".55"/>
      <stop offset="1" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-10%" y="-30%" width="120%" height="160%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <clipPath id="slice">
      <rect x="0" y="40" width="{W}" height="14">
        <animate attributeName="y" dur="3s" repeatCount="indefinite" calcMode="discrete"
          values="40;70;52;84;46;62" keyTimes="0;.2;.4;.6;.8;.9"/>
      </rect>
    </clipPath>
  </defs>
  <style>
    .rain  {{ font-family: {MONO}; fill: url(#trail); animation: fall linear infinite; }}
    .title {{ font: 900 64px {MONO}; letter-spacing: 2px; }}
    .main  {{ fill: #eafff1; }}
    .r     {{ fill: #ff2a6d; opacity: .75; animation: glitchR 3s steps(1) infinite; }}
    .c     {{ fill: #05d9e8; opacity: .75; animation: glitchC 3s steps(1) infinite; }}
    .cut   {{ fill: #eafff1; animation: shift 3s steps(1) infinite; }}
    .type  {{ font: 500 {FONT_SIZE}px {MONO}; fill: #8dffb8; }}
    .cursor {{ fill: #00ff6a; }}
    @keyframes fall {{ from {{ transform: translateY(calc(-1 * var(--h))); }} to {{ transform: translateY({H}px); }} }}
    @keyframes glitchR {{ 0%,100% {{ transform: none; }} 86% {{ transform: translate(-4px, 1px); }} 89% {{ transform: translate(3px,-2px); }} 92% {{ transform: translate(-2px, 0); }} 95% {{ transform: none; }} }}
    @keyframes glitchC {{ 0%,100% {{ transform: none; }} 86% {{ transform: translate(4px,-1px); }} 89% {{ transform: translate(-3px, 2px); }} 92% {{ transform: translate(2px, 0); }} 95% {{ transform: none; }} }}
    @keyframes shift {{ 0%,100% {{ transform: none; opacity: 0; }} 86% {{ transform: translateX(14px); opacity: 1; }} 89% {{ transform: translateX(-10px); opacity: 1; }} 92% {{ transform: translateX(6px); opacity: 1; }} 95% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="#000"/>
    {rain}
    <rect width="{W}" height="{H}" fill="url(#vignette)"/>
  </g>

  <g class="title" text-anchor="middle">
    <text x="50%" y="118" class="r">{t}</text>
    <text x="50%" y="118" class="c">{t}</text>
    <text x="50%" y="118" class="main" filter="url(#glow)">{t}</text>
    <g clip-path="url(#slice)"><text x="50%" y="118" class="cut">{t}</text></g>
  </g>
  {typing}
</svg>
"""


def build_orbit(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Banner with tech-stack tags orbiting the name on 3D-style orbits."""
    W, H = 900, 320
    bg, (c1, c2, c3) = THEMES[theme]
    rng = random.Random(seed)
    cx, cy = W / 2, H / 2
    rings = [(255, 72, 16), (345, 102, 24), (425, 134, 34)]  # (rx, ry, seconds per revolution)

    ring_svg, tag_svg = [], []
    for i, (rx, ry, _) in enumerate(rings):
        ring_svg.append(
            f'<ellipse class="ring" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'style="animation-duration:{10 + i * 6}s"/>'
        )
    colors = [c1, c2, c3]
    per_ring = [tags[i::len(rings)] for i in range(len(rings))]
    for ri, ring_tags in enumerate(per_ring):
        rx, ry, dur = rings[ri]
        # elliptical path starting at the right, going clockwise (front/bottom first)
        path = f"M{cx + rx},{cy} A{rx},{ry} 0 1,1 {cx - rx},{cy} A{rx},{ry} 0 1,1 {cx + rx},{cy}"
        for ti, tag in enumerate(ring_tags):
            offset = dur * ti / max(len(ring_tags), 1) + ri * 2.3
            w = text_width(tag) * (14 / FONT_SIZE) + 26
            col = colors[(ri + ti) % 3]
            # scale/opacity follow path progress 0 -> .25 (front) -> .5 -> .75 (back) -> 1 for depth
            tag_svg.append(f"""
    <g>
      <animateMotion dur="{dur}s" begin="-{offset:.2f}s" repeatCount="indefinite" path="{path}"/>
      <g>
        <animateTransform attributeName="transform" type="scale" dur="{dur}s" begin="-{offset:.2f}s" repeatCount="indefinite"
          values="0.9;1.15;0.9;0.65;0.9" keyTimes="0;.25;.5;.75;1" calcMode="spline"
          keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>
        <animate attributeName="opacity" dur="{dur}s" begin="-{offset:.2f}s" repeatCount="indefinite"
          values=".85;1;.85;.35;.85" keyTimes="0;.25;.5;.75;1"/>
        <rect x="{-w / 2:.1f}" y="-14" width="{w:.1f}" height="28" rx="14" fill="{bg}" stroke="{col}" stroke-width="1.5"/>
        <circle cx="{-w / 2 + 12:.1f}" cy="0" r="3.5" fill="{col}"/>
        <text x="6" y="5" text-anchor="middle" class="tag">{esc(tag)}</text>
      </g>
    </g>""")

    subtitle = esc(lines[0]) if lines else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(name)}">
  <title>{esc(name)}</title>
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="60%">
      <stop offset="0" stop-color="{c1}" stop-opacity=".28"/>
      <stop offset="1" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{c1}"><animate attributeName="stop-color" values="{c1};{c2};{c3};{c1}" dur="8s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="{c3}"><animate attributeName="stop-color" values="{c3};{c1};{c2};{c3}" dur="8s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <filter id="soft" x="-100%" y="-200%" width="300%" height="500%"><feGaussianBlur stdDeviation="22"/></filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .star   {{ fill: #fff; animation: twinkle ease-in-out infinite; }}
    .ring   {{ fill: none; stroke: #8b9cff; stroke-opacity: .28; stroke-width: 1.2; stroke-dasharray: 4 8; animation: flow linear infinite; }}
    .tag    {{ font: 600 14px {SANS}; fill: #e6edf3; }}
    .name   {{ font: 800 46px {SANS}; fill: url(#grad); }}
    .sub    {{ font: 500 15px {MONO}; fill: #9aa7b8; letter-spacing: 1px; }}
    .ripple {{ fill: none; stroke: {c2}; stroke-width: 1.5; animation: ripple 4s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
    .core   {{ animation: breathe 4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes twinkle {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
    @keyframes flow    {{ to {{ stroke-dashoffset: -120; }} }}
    @keyframes ripple  {{ from {{ transform: scale(.4); opacity: .7; }} to {{ transform: scale(2.1); opacity: 0; }} }}
    @keyframes breathe {{ 0%,100% {{ opacity: .45; transform: scale(1); }} 50% {{ opacity: .75; transform: scale(1.15); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{bg}"/>
    <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
    {stars(70, rng, W, H)}
    {"".join(ring_svg)}
    <ellipse class="core" cx="{cx}" cy="{cy}" rx="170" ry="40" fill="{c1}" filter="url(#soft)"/>
    <ellipse class="ripple" cx="{cx}" cy="{cy}" rx="110" ry="31"/>
    <ellipse class="ripple" cx="{cx}" cy="{cy}" rx="110" ry="31" style="animation-delay:-2s"/>
    {"".join(tag_svg)}
  </g>

  <text x="50%" y="{cy + 12}" text-anchor="middle" class="name">{esc(name)}</text>
  <text x="50%" y="{cy + 40}" text-anchor="middle" class="sub">{subtitle}</text>
</svg>
"""


STYLES = {
    "banner": build_banner,
    "synthwave": build_synthwave,
    "matrix": build_matrix,
    "orbit": build_orbit,
    **creative.STYLES,
    **spectacle.STYLES,
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--style", choices=[*STYLES, *contrib.STYLES, "all"], default="banner",
                   help=" | ".join([*STYLES, *contrib.STYLES, "all"]))
    p.add_argument("--name", default="Hi, I'm Jihoo")
    p.add_argument("--line", action="append", dest="lines",
                   help="subtitle line, repeatable (synthwave/orbit use only the first)")
    p.add_argument("--tag", action="append", dest="tags", help="tag orbiting in the orbit style, repeatable")
    p.add_argument("--theme", choices=THEMES, default="aurora")
    p.add_argument("--seed", type=int, default=42, help="random seed for stars / code rain")
    p.add_argument("--user", help="contrib-* styles: GitHub username")
    p.add_argument("--palette", choices=contrib.PALETTES, default="green", help="contrib-* styles: color palette")
    p.add_argument("--contrib-html", help="contrib-* styles: saved contributions HTML (offline use)")
    p.add_argument("--out", help="output path (default: assets/<style>.svg)")
    a = p.parse_args()

    lines = a.lines or ["Welcome to my GitHub!", "I love building cool stuff", "Let's code together :)"]
    tags = a.tags or ["Python", "Nix", "Linux", "Git", "Rust", "TypeScript", "Docker", "Neovim", "Bash"]
    if a.style == "all":
        styles = list(STYLES) + (list(contrib.STYLES) if a.user else [])
    else:
        styles = [a.style]
    if a.out and len(styles) > 1:
        p.error("--out cannot be used with --style all")
    needs_cal = any(s in contrib.STYLES for s in styles)
    if needs_cal and not a.user:
        p.error("contrib-* styles require --user")
    cal = contrib.load(a.user, a.contrib_html) if needs_cal else None

    for style in styles:
        out = Path(a.out or f"assets/{style}.svg")
        out.parent.mkdir(parents=True, exist_ok=True)
        if style in contrib.STYLES:
            svg = contrib.STYLES[style](cal, a.palette)
        else:
            svg = STYLES[style](a.name, lines, tags, a.theme, a.seed)
        out.write_text(svg, encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
