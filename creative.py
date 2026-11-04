"""More unusual banner styles: split-flap board, firefly swarm, liquid chrome,
oscilloscope and blueprint plotter.

Every builder has the signature (name, lines, tags, theme, seed) -> svg string.
Like the rest of the project they use only CSS animations and SMIL, so they play on GitHub.
"""

from __future__ import annotations

import math
import random

import vecfont
from common import MONO, SANS, THEMES, esc, key_times

REDUCED = "@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} {extra} }}"


def reduced(extra: str = "") -> str:
    return REDUCED.format(extra=extra)


def svg_open(w: float, h: float, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{esc(label)}">\n  <title>{esc(label)}</title>'
    )


# ================================================================ split-flap board

FLAP_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _flap_row(text_events: list[tuple[float, str]], cols: int, x0: float, y0: float, cw: float, ch: float,
              gap: float, cycle: float, rng: random.Random, force: bool) -> str:
    """One row of split-flap cells. text_events = [(time, text)], the row flips at each time."""
    events = [(t, txt.upper().center(cols)[:cols]) for t, txt in text_events]
    flip = 0.065  # seconds per flap
    fs = ch * 0.62
    out = []
    for c in range(cols):
        # timeline of (time, char) for this cell; the cell starts on the final message's char
        timeline = [(0.0, events[-1][1][c])]
        flips = []
        prev = events[-1][1][c]
        for t, txt in events:
            target = txt[c]
            if target == prev and not force:
                continue
            start = t + 0.12 + c * 0.05 + rng.uniform(0, 0.06)
            n = rng.randint(3, 6) + c // 5
            seq = [rng.choice(FLAP_CHARS) for _ in range(n - 1)] + [target]
            for k, sym in enumerate(seq):
                tk = start + k * flip
                timeline.append((tk, sym))
                flips.append(tk)
            prev = target
        timeline.sort()
        x = x0 + c * (cw + gap)
        cx, mid = x + cw / 2, y0 + ch / 2

        # one <text> per distinct glyph, switched on and off with discrete opacity keyframes
        glyphs: dict[str, list[tuple[float, float]]] = {}
        for i, (t, sym) in enumerate(timeline):
            end = timeline[i + 1][0] if i + 1 < len(timeline) else cycle
            if sym.strip():
                glyphs.setdefault(sym, []).append((t, end))
        texts = []
        for sym, spans in glyphs.items():
            times, vals = [0.0], ["1" if spans[0][0] == 0 else "0"]
            for s, e in spans:
                if s > 0:
                    times.append(s), vals.append("1")
                if e < cycle:
                    times.append(e), vals.append("0")
            times.append(cycle), vals.append(vals[-1])
            texts.append(
                f'<text x="{cx:.1f}" y="{mid + fs * 0.36:.1f}" class="fc" font-size="{fs:.1f}" opacity="{vals[0]}">'
                f'{esc(sym)}<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="{key_times(times, cycle)}" values="{";".join(vals)}"/></text>'
            )

        # the falling top flap: a shade that collapses onto the hinge at every flip
        flap = ""
        if flips:
            times, vals = [0.0], ["1 0"]
            for tk in flips:
                times += [tk - 0.001, tk, tk + flip * 0.85]
                vals += ["1 0", "1 1", "1 0"]
            times.append(cycle), vals.append("1 0")
            flap = (
                f'<g transform="translate(0 {mid:.1f})"><g>'
                f'<animateTransform attributeName="transform" type="scale" dur="{cycle}s" repeatCount="indefinite" '
                f'keyTimes="{key_times(times, cycle)}" values="{";".join(vals)}"/>'
                f'<rect x="{x:.1f}" y="{-ch / 2:.1f}" width="{cw:.1f}" height="{ch / 2:.1f}" rx="3" fill="url(#flapShade)"/>'
                f'</g></g>'
            )
        out.append(
            f'<g><rect x="{x:.1f}" y="{y0:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="4" fill="url(#cell)"/>'
            + "".join(texts)
            + flap
            + f'<rect x="{x:.1f}" y="{mid - 0.8:.1f}" width="{cw:.1f}" height="1.6" fill="#000" opacity=".85"/>'
            f'<rect x="{x - 1.5:.1f}" y="{mid - 3:.1f}" width="2.5" height="6" rx="1" fill="#3a3a3a"/>'
            f'<rect x="{x + cw - 1:.1f}" y="{mid - 3:.1f}" width="2.5" height="6" rx="1" fill="#3a3a3a"/></g>'
        )
    return "\n    ".join(out)


def build_splitflap(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """An airport-style split-flap board: the name and each line clatter into place."""
    W = 900
    rng = random.Random(seed)
    _, (c1, c2, _c3) = THEMES[theme]
    lines = lines or [""]
    period = 4.8
    cycle = period * len(lines)

    cols0 = max(len(name) + 2, 12)
    gap0 = 5
    cw0 = min(46, (W - 70) / cols0 - gap0)
    ch0 = cw0 * 1.42
    cols1 = max(max(len(l) for l in lines) + 2, 16)
    gap1 = 3.5
    cw1 = min(29, (W - 70) / cols1 - gap1)
    ch1 = cw1 * 1.42
    y0 = 62
    y1 = y0 + ch0 + 20
    H = round(y1 + ch1 + 34)
    x0 = (W - (cols0 * (cw0 + gap0) - gap0)) / 2
    x1 = (W - (cols1 * (cw1 + gap1) - gap1)) / 2

    row0 = _flap_row([(0.0, name)], cols0, x0, y0, cw0, ch0, gap0, cycle, rng, force=True)
    row1 = _flap_row([(i * period, l) for i, l in enumerate(lines)], cols1, x1, y1, cw1, ch1, gap1, cycle, rng,
                     force=False)
    tagline = esc("  ·  ".join(t.upper() for t in tags[:5]))

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="cell" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2b2b2e"/><stop offset=".5" stop-color="#1f1f22"/>
      <stop offset=".5" stop-color="#18181a"/><stop offset="1" stop-color="#222225"/>
    </linearGradient>
    <linearGradient id="flapShade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#000" stop-opacity=".25"/><stop offset="1" stop-color="#000" stop-opacity=".75"/>
    </linearGradient>
    <linearGradient id="board" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#121214"/><stop offset="1" stop-color="#0a0a0b"/>
    </linearGradient>
    <radialGradient id="lamp" cx="50%" cy="0%" r="70%">
      <stop offset="0" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .fc    {{ font-family: {MONO}; font-weight: 700; fill: #f3f1e7; text-anchor: middle; }}
    .head  {{ font: 700 12px {SANS}; letter-spacing: 3px; fill: #c9c6b8; }}
    .tags  {{ font: 600 11px {MONO}; letter-spacing: 1.5px; fill: #77756c; }}
    .led   {{ fill: {c2}; animation: led 1.4s steps(1) infinite; }}
    .bar   {{ fill: {c1}; }}
    @keyframes led {{ 0%,60% {{ opacity: 1; }} 61%,100% {{ opacity: .2; }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#board)"/>
    <rect width="{W}" height="{H}" fill="url(#lamp)"/>
    <rect class="bar" x="0" y="0" width="{W}" height="4"/>
    <circle class="led" cx="36" cy="33" r="5"/>
    <text x="50" y="37.5" class="head">NOW SHOWING</text>
    <text x="{W - 34}" y="37.5" class="tags" text-anchor="end">{tagline}</text>
    <rect x="24" y="50" width="{W - 48}" height="1" fill="#2a2a2d"/>
    {row0}
    {row1}
  </g>
</svg>
"""


# ================================================================ firefly swarm

def _grass(rng: random.Random, W: float, H: float, n: int, color: str, hmin: float, hmax: float) -> str:
    clumps = []
    for i in range(n):
        cx = (i + rng.uniform(0, 1)) * W / n
        blades = []
        for _ in range(rng.randint(3, 6)):
            bx = cx + rng.uniform(-14, 14)
            bh = rng.uniform(hmin, hmax)
            lean = rng.uniform(-14, 14)
            w = rng.uniform(2, 4)
            blades.append(
                f"M{bx - w:.1f} {H} Q{bx + lean * 0.3:.1f} {H - bh * 0.6:.1f} {bx + lean:.1f} {H - bh:.1f} "
                f"Q{bx + lean * 0.3 + w * 0.5:.1f} {H - bh * 0.6:.1f} {bx + w:.1f} {H} Z"
            )
        clumps.append(
            f'<path class="sway" d="{" ".join(blades)}" fill="{color}" '
            f'style="animation-duration:{rng.uniform(3.5, 6):.2f}s;animation-delay:-{rng.uniform(0, 5):.2f}s"/>'
        )
    return "\n    ".join(clumps)


def build_swarm(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Fireflies drift over a meadow at night, swarm together to spell the name, then scatter."""
    W, H = 900, 290
    rng = random.Random(seed)
    cycle = 15.0
    size = min(9.0, (W - 120) / max(1, vecfont.width(name, 1)))
    tw = vecfont.width(name, size)
    tx, ty = (W - tw) / 2, 64

    targets = []
    for glyph in vecfont.strokes(name, size, tx, ty):
        for stroke in glyph:
            pts = vecfont.sample(stroke, size * 0.95)
            for p in pts:
                if all(math.dist(p, q) > size * 0.55 for q in targets[-12:]):
                    targets.append(p)

    def rand_pt() -> tuple[float, float]:
        return rng.uniform(20, W - 20), rng.uniform(20, H - 40)

    flies = []
    for (gx, gy) in targets:
        p0, p1, p2 = rand_pt(), rand_pt(), rand_pt()
        arrive = 0.30 + (gx - tx) / max(tw, 1) * 0.07 + rng.uniform(0, 0.04)
        leave = 0.68 + rng.uniform(0, 0.05)
        kt = [0, 0.15 + rng.uniform(0, 0.05), arrive, leave, 0.86 + rng.uniform(0, 0.04), 1]
        pts = [p0, p1, (gx, gy), (gx, gy), p2, p0]
        vals = ";".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        spl = ";".join([".45 0 .55 1"] * 5)
        blink = ";".join(f"{v:.2f}" for v in (.25, 1, .3, 1, 1, .9, .2, .25))
        bkt = [0, .08, .17, arrive, leave, leave + .06, .9, 1]
        flies.append(
            f'<g><animateMotion dur="{cycle}s" repeatCount="indefinite" calcMode="spline" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in kt)}" values="{vals}" keySplines="{spl}"/>'
            f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in bkt)}" values="{blink}"/>'
            f'<g class="hover" style="animation-delay:-{rng.uniform(0, 3):.2f}s">'
            f'<circle r="{size * 0.75:.1f}" fill="url(#halo)"/><circle r="{size * 0.2:.2f}" class="core"/></g></g>'
        )

    # loners that never join the swarm
    for _ in range(26):
        pts = [rand_pt() for _ in range(4)]
        pts.append(pts[0])
        dur = rng.uniform(10, 18)
        flies.append(
            f'<g><animateMotion dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite" '
            f'calcMode="spline" keyTimes="0;.25;.5;.75;1" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1" '
            f'values="{";".join(f"{x:.1f},{y:.1f}" for x, y in pts)}"/>'
            f'<g class="blink" style="animation-duration:{rng.uniform(1.6, 3.2):.2f}s;animation-delay:-{rng.uniform(0, 3):.2f}s">'
            f'<circle r="6" fill="url(#halo)"/><circle r="1.6" class="core"/></g></g>'
        )
    rng.shuffle(flies)

    hills = (
        f'<path d="M0 {H - 60} C 160 {H - 110} 300 {H - 70} 450 {H - 92} S 760 {H - 120} {W} {H - 74} V {H} H 0 Z" fill="#0a2221"/>'
        f'<path d="M0 {H - 40} C 200 {H - 70} 380 {H - 36} 560 {H - 58} S 820 {H - 64} {W} {H - 44} V {H} H 0 Z" fill="#071917"/>'
    )
    subtitle = esc(lines[0]) if lines else ""
    sub_in, sub_out = 0.42 * 100, 0.68 * 100

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="night" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#030812"/><stop offset=".65" stop-color="#0a1f2b"/><stop offset="1" stop-color="#0f2e2a"/>
    </linearGradient>
    <radialGradient id="halo">
      <stop offset="0" stop-color="#fff6a8" stop-opacity=".95"/>
      <stop offset=".25" stop-color="#e8ff6a" stop-opacity=".45"/>
      <stop offset="1" stop-color="#b6ff3a" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="moon" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#fdf7dc" stop-opacity=".9"/><stop offset=".18" stop-color="#fdf7dc" stop-opacity=".9"/>
      <stop offset=".22" stop-color="#cfe6ff" stop-opacity=".18"/><stop offset="1" stop-color="#cfe6ff" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .core  {{ fill: #fffde8; }}
    .hover {{ animation: hover 2.6s ease-in-out infinite; }}
    .blink {{ animation: blink ease-in-out infinite; }}
    .sway  {{ animation: sway ease-in-out infinite alternate; transform-box: fill-box; transform-origin: 50% 100%; }}
    .star  {{ fill: #cfe6ff; animation: twinkle ease-in-out infinite; }}
    .sub   {{ font: 500 16px {MONO}; fill: #e9f7c9; letter-spacing: 2px; animation: sub {cycle}s ease-in-out infinite; }}
    @keyframes hover {{ 0%,100% {{ transform: translate(0,0); }} 33% {{ transform: translate(1.2px,-1px); }} 66% {{ transform: translate(-1px,1.2px); }} }}
    @keyframes blink {{ 0%,100% {{ opacity: .15; }} 45%,55% {{ opacity: 1; }} }}
    @keyframes sway  {{ from {{ transform: skewX(-4deg); }} to {{ transform: skewX(5deg); }} }}
    @keyframes twinkle {{ 0%,100% {{ opacity: .1; }} 50% {{ opacity: .7; }} }}
    @keyframes sub {{ 0%,{sub_in - 4:.0f}% {{ opacity: 0; }} {sub_in:.0f}%,{sub_out:.0f}% {{ opacity: 1; }} {sub_out + 4:.0f}%,100% {{ opacity: 0; }} }}
    {reduced(".sub { opacity: 1; }")}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#night)"/>
    {_stars_small(rng, W, H * 0.55)}
    <circle cx="{W - 58}" cy="40" r="110" fill="url(#moon)"/>
    {hills}
    {_grass(rng, W, H, 34, "#06140f", 26, 60)}
    {"".join(flies)}
    {_grass(rng, W, H, 22, "#030a08", 16, 38)}
  </g>
  <text x="50%" y="{ty + 7 * size + 34:.0f}" text-anchor="middle" class="sub">{subtitle}</text>
</svg>
"""


def _stars_small(rng: random.Random, w: float, h: float, n: int = 40) -> str:
    return "".join(
        f'<circle class="star" cx="{rng.uniform(0, w):.1f}" cy="{rng.uniform(0, h):.1f}" r="{rng.uniform(.4, 1.1):.2f}" '
        f'style="animation-duration:{rng.uniform(2, 6):.1f}s;animation-delay:-{rng.uniform(0, 6):.1f}s"/>'
        for _ in range(n)
    )


# ================================================================ liquid chrome

def build_liquid(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Molten metal: the name is liquid, blobs rise out of a pool, melt into it and drip back."""
    W, H = 900, 300
    rng = random.Random(seed)
    bg, (c1, c2, c3) = THEMES[theme]
    fs = min(92, (W - 100) / max(1, len(name) * 0.62))
    ty = 132
    tw = len(name) * fs * 0.6
    tl = (W - tw) / 2
    pool = H - 34

    blobs = []
    # risers: leave the pool, swell, and sink into the letters
    for i in range(12):
        x = tl + rng.uniform(0, tw)
        r = rng.uniform(9, 22)
        dur = rng.uniform(5, 9)
        rise = pool - (ty - fs * 0.3) + rng.uniform(-10, 10)
        blobs.append(
            f'<circle class="rise" cx="{x:.0f}" cy="{pool + r:.0f}" r="{r:.1f}" '
            f'style="--y:-{rise:.0f}px;--x:{rng.uniform(-30, 30):.0f}px;animation-duration:{dur:.2f}s;animation-delay:-{rng.uniform(0, dur):.2f}s"/>'
        )
    # drips: bead under the letters, stretch, fall into the pool
    for i in range(10):
        x = tl + rng.uniform(fs * 0.2, tw - fs * 0.2)
        r = rng.uniform(5, 10)
        dur = rng.uniform(3.5, 6.5)
        blobs.append(
            f'<circle class="drip" cx="{x:.0f}" cy="{ty + 2:.0f}" r="{r:.1f}" '
            f'style="--y:{pool - ty:.0f}px;animation-duration:{dur:.2f}s;animation-delay:-{rng.uniform(0, dur):.2f}s"/>'
        )
    # wanderers drifting around the title
    for i in range(6):
        r = rng.uniform(12, 26)
        dur = rng.uniform(9, 15)
        blobs.append(
            f'<circle class="wander" cx="{rng.uniform(40, W - 40):.0f}" cy="{rng.uniform(50, pool - 40):.0f}" r="{r:.1f}" '
            f'style="--x:{rng.uniform(-120, 120):.0f}px;--y:{rng.uniform(-40, 40):.0f}px;animation-duration:{dur:.1f}s;animation-delay:-{rng.uniform(0, dur):.1f}s"/>'
        )

    wave = [f"M-20 {pool}"]
    x = -20.0
    while x < W * 2 + 40:
        wave.append(f"q 45 -14 90 0 t 90 0")
        x += 180
    wave.append(f"V {H + 40} H -20 Z")
    subtitle = esc(lines[0]) if lines else ""

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="molten" gradientUnits="userSpaceOnUse" x1="0" y1="40" x2="{W}" y2="{H}">
      <stop offset="0" stop-color="{c1}"><animate attributeName="stop-color" values="{c1};{c2};{c3};{c1}" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset=".5" stop-color="{c2}"><animate attributeName="stop-color" values="{c2};{c3};{c1};{c2}" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset="1" stop-color="{c3}"><animate attributeName="stop-color" values="{c3};{c1};{c2};{c3}" dur="10s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <filter id="goo" x="-5%" y="-20%" width="110%" height="140%" color-interpolation-filters="sRGB">
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur"/>
      <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 24 -10" result="goo"/>
      <feGaussianBlur in="goo" stdDeviation="3.5" result="bump"/>
      <feSpecularLighting in="bump" surfaceScale="7" specularConstant="1.2" specularExponent="26" lighting-color="#ffffff" result="spec">
        <fePointLight x="150" y="-60" z="260">
          <animate attributeName="x" values="150;{W - 150};150" dur="9s" repeatCount="indefinite"/>
        </fePointLight>
      </feSpecularLighting>
      <feComposite in="spec" in2="goo" operator="in" result="shine"/>
      <feDiffuseLighting in="bump" surfaceScale="5" diffuseConstant="1" lighting-color="#ffffff" result="shade">
        <feDistantLight azimuth="235" elevation="55"/>
      </feDiffuseLighting>
      <feComposite in="goo" in2="shade" operator="arithmetic" k1="1.15" k2="0" k3="0" k4="0" result="lit"/>
      <feComposite in="lit" in2="goo" operator="in" result="body"/>
      <feComposite in="body" in2="shine" operator="arithmetic" k1="0" k2="1" k3=".9" k4="0"/>
    </filter>
    <radialGradient id="glow" cx="50%" cy="45%" r="60%">
      <stop offset="0" stop-color="{c1}" stop-opacity=".22"/><stop offset="1" stop-color="{bg}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .metal  {{ fill: url(#molten); }}
    .name   {{ font: 900 {fs:.0f}px {SANS}; letter-spacing: 1px; }}
    .rise   {{ animation: rise ease-in infinite; }}
    .drip   {{ animation: drip ease-in infinite; transform-box: fill-box; transform-origin: 50% 0; }}
    .wander {{ animation: wander ease-in-out infinite alternate; }}
    .pool   {{ animation: slosh 7s linear infinite; }}
    .sub    {{ font: 600 15px {MONO}; fill: #f4f4f8; letter-spacing: 3px; opacity: .85;
              paint-order: stroke; stroke: {bg}; stroke-width: 6px; stroke-linejoin: round; }}
    @keyframes rise   {{ 0% {{ transform: translate(0,0) scale(.6); }} 70% {{ transform: translate(var(--x), calc(var(--y) * .8)) scale(1); }} 100% {{ transform: translate(var(--x), var(--y)) scale(.4); }} }}
    @keyframes drip   {{ 0% {{ transform: translateY(0) scale(.2, .2); }} 45% {{ transform: translateY(8px) scale(.9, 1.3); }} 100% {{ transform: translateY(var(--y)) scale(.7, 1.6); }} }}
    @keyframes wander {{ from {{ transform: translate(0,0); }} to {{ transform: translate(var(--x), var(--y)); }} }}
    @keyframes slosh  {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-180px); }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{bg}"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
    <g filter="url(#goo)">
      <g class="metal">
        {"".join(blobs)}
        <path class="pool" d="{" ".join(wave)}"/>
        <text x="50%" y="{ty}" text-anchor="middle" class="name">{esc(name)}</text>
      </g>
    </g>
  </g>
  <text x="50%" y="{ty + 50:.0f}" text-anchor="middle" class="sub">{subtitle}</text>
</svg>
"""


# ================================================================ oscilloscope

PHOSPHOR = {"aurora": "#6dff9a", "sunset": "#ffb648", "ocean": "#62e6ff"}


def _wave_shapes(n: int, x0: float, width: float, mid: float, amp: float, period: float) -> list[str]:
    """Several periodic waveforms with identical path structure, so SMIL can morph between them."""
    def sine(u): return math.sin(u)
    def square(u): return math.tanh(4 * math.sin(u))
    def saw(u): return 2 * ((u / (2 * math.pi)) % 1) - 1 if (u / (2 * math.pi)) % 1 < 0.92 else 1 - ((u / (2 * math.pi)) % 1 - 0.92) / 0.04
    def beat(u):
        f = (u / (2 * math.pi)) % 1
        return (-1.0 if 0.48 < f < 0.52 else 0.45 if 0.44 < f <= 0.48 or 0.52 <= f < 0.56 else 0.08 * math.sin(u * 3))
    def am(u): return math.sin(u * 4) * (0.35 + 0.65 * abs(math.sin(u / 2)))
    out = []
    for fn in (sine, square, beat, am, saw, sine):
        pts = []
        for i in range(n + 1):
            x = x0 + width * i / n
            pts.append(f"{x:.1f} {mid - amp * fn(2 * math.pi * (x - x0) / period):.1f}")
        out.append("M" + " L".join(pts))
    return out


def build_scope(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A CRT oscilloscope: the electron beam writes the name, while the trace morphs between waveforms."""
    W, H = 900, 300
    ph = PHOSPHOR.get(theme, PHOSPHOR["aurora"])
    sx, sy, sw, sh = 22, 22, 650, 256  # screen
    cycle = 12.0
    draw_start, draw_end, fade0, fade1 = 0.4, 5.2, 10.6, 11.6

    size = min(8.5, (sw - 80) / max(1, vecfont.width(name, 1)))
    tw = vecfont.width(name, size)
    tx, ty = sx + (sw - tw) / 2, sy + 52

    strokes = [s for g in vecfont.strokes(name, size, tx, ty) for s in g if len(s) > 1]
    lens = [max(vecfont.length(s), 0.01) for s in strokes]
    total = sum(lens)
    paths, acc = [], 0.0
    for s, L in zip(strokes, lens):
        t0 = draw_start + (draw_end - draw_start) * acc / total
        t1 = draw_start + (draw_end - draw_start) * (acc + L) / total
        acc += L
        paths.append(
            f'<path d="{vecfont.path_d(s)}" pathLength="1" class="beamtext">'
            f'<animate attributeName="stroke-dashoffset" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, t0, t1, cycle], cycle)}" values="1;1;0;0"/>'
            f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, t1, t1 + 1.2, fade0, fade1, cycle], cycle)}" values="1;1;.8;.8;0;0"/></path>'
        )
    motion_path = " ".join(vecfont.path_d(s) for s in strokes)

    gx = "".join(f'<line x1="{sx + sw * i / 10:.1f}" y1="{sy}" x2="{sx + sw * i / 10:.1f}" y2="{sy + sh}"/>' for i in range(1, 10))
    gy = "".join(f'<line x1="{sx}" y1="{sy + sh * i / 8:.1f}" x2="{sx + sw}" y2="{sy + sh * i / 8:.1f}"/>' for i in range(1, 8))
    ticks = "".join(
        f'<line x1="{sx + sw * i / 50:.1f}" y1="{sy + sh / 2 - 3}" x2="{sx + sw * i / 50:.1f}" y2="{sy + sh / 2 + 3}"/>'
        for i in range(1, 50)
    ) + "".join(
        f'<line x1="{sx + sw / 2 - 3}" y1="{sy + sh * i / 40:.1f}" x2="{sx + sw / 2 + 3}" y2="{sy + sh * i / 40:.1f}"/>'
        for i in range(1, 40)
    )

    period = sw / 4
    shapes = _wave_shapes(160, sx, sw + period, sy + sh * 0.74, 26, period)
    wave_vals = ";".join(shapes)
    wave_kt = ";".join(f"{i / (len(shapes) - 1):.3f}" for i in range(len(shapes)))
    spl = ";".join([".6 0 .4 1"] * (len(shapes) - 1))

    knobs = []
    px = 690
    for i, (label, rot) in enumerate([("VOLTS/DIV", 18), ("TIME/DIV", -30), ("TRIGGER", 60)]):
        ky = 70 + i * 74
        knobs.append(
            f'<g transform="translate({px + 70} {ky})">'
            f'<circle r="25" fill="url(#knob)" stroke="#000" stroke-opacity=".6"/>'
            f'<g class="knob" style="--r:{rot}deg;animation-delay:-{i * 1.7:.1f}s"><line x1="0" y1="-8" x2="0" y2="-21" stroke="#e8e8e8" stroke-width="3" stroke-linecap="round"/></g>'
            + "".join(f'<line x1="0" y1="-29" x2="0" y2="-33" transform="rotate({a})" stroke="#666" stroke-width="1.5"/>' for a in range(-135, 136, 27))
            + f'<text y="45" class="klabel" text-anchor="middle">{label}</text></g>'
        )
    sub = esc((lines[0] if lines else "").upper())

    return f"""{svg_open(W, H, name)}
  <defs>
    <radialGradient id="crt" cx="50%" cy="50%" r="70%">
      <stop offset="0" stop-color="{ph}" stop-opacity=".10"/><stop offset=".7" stop-color="#020a05" stop-opacity="1"/>
      <stop offset="1" stop-color="#000" stop-opacity="1"/>
    </radialGradient>
    <radialGradient id="knob" cx="35%" cy="30%" r="80%">
      <stop offset="0" stop-color="#5a5d63"/><stop offset=".6" stop-color="#26282c"/><stop offset="1" stop-color="#121315"/>
    </radialGradient>
    <linearGradient id="case" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2a2c30"/><stop offset="1" stop-color="#16171a"/>
    </linearGradient>
    <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#000" opacity=".35"/>
    </pattern>
    <filter id="phosphor" x="-10%" y="-30%" width="120%" height="160%">
      <feGaussianBlur stdDeviation="2.2" result="b1"/>
      <feGaussianBlur stdDeviation="7" result="b2"/>
      <feMerge><feMergeNode in="b2"/><feMergeNode in="b1"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="screen"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="22"/></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .grat  {{ stroke: {ph}; stroke-opacity: .13; stroke-width: 1; }}
    .tick  {{ stroke: {ph}; stroke-opacity: .25; }}
    .beamtext {{ fill: none; stroke: {ph}; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1 1; }}
    .wave  {{ fill: none; stroke: {ph}; stroke-width: 2; opacity: .85; animation: run 2.4s linear infinite; }}
    .read  {{ font: 600 12px {MONO}; fill: {ph}; opacity: .8; letter-spacing: 1px; }}
    .klabel {{ font: 700 9px {SANS}; fill: #9a9da3; letter-spacing: 1.5px; }}
    .knob  {{ animation: twist 7s ease-in-out infinite; }}
    .led   {{ animation: led 1.1s steps(1) infinite; }}
    .flick {{ animation: flick 5s linear infinite; }}
    .roll  {{ animation: roll 6s linear infinite; }}
    @keyframes run   {{ to {{ transform: translateX(-{period:.1f}px); }} }}
    @keyframes twist {{ 0%,100% {{ transform: rotate(var(--r)); }} 40% {{ transform: rotate(calc(var(--r) + 50deg)); }} 60% {{ transform: rotate(calc(var(--r) + 35deg)); }} }}
    @keyframes led   {{ 0%,50% {{ opacity: 1; }} 51%,100% {{ opacity: .15; }} }}
    @keyframes flick {{ 0%,100% {{ opacity: 1; }} 47% {{ opacity: .93; }} 48% {{ opacity: 1; }} 82% {{ opacity: .96; }} }}
    @keyframes roll  {{ from {{ transform: translateY(-60px); }} to {{ transform: translateY({H}px); }} }}
    {reduced(".beamtext { stroke-dasharray: none; } .pen { display: none; }")}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#case)"/>
    <rect x="{sx - 8}" y="{sy - 8}" width="{sw + 16}" height="{sh + 16}" rx="28" fill="#0b0c0d" stroke="#3a3c40"/>
    <g clip-path="url(#screen)">
      <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#crt)"/>
      <g class="grat">{gx}{gy}</g>
      <g class="tick">{ticks}</g>
      <g class="flick" filter="url(#phosphor)">
        {"".join(paths)}
        <g class="pen">
          <animateMotion dur="{cycle}s" repeatCount="indefinite" calcMode="linear" path="{motion_path}"
            keyPoints="0;0;1;1" keyTimes="{key_times([0, draw_start, draw_end, cycle], cycle)}"/>
          <animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete"
            keyTimes="{key_times([0, draw_start, draw_end, cycle], cycle)}" values="0;1;0;0"/>
          <circle r="3.2" fill="#fff"/>
        </g>
        <path class="wave" d="{shapes[0]}">
          <animate attributeName="d" dur="15s" repeatCount="indefinite" calcMode="spline" keyTimes="{wave_kt}" keySplines="{spl}" values="{wave_vals}"/>
        </path>
      </g>
      <text x="{sx + 18}" y="{sy + 22}" class="read">CH1 500mV</text>
      <text x="{sx + sw - 18}" y="{sy + 22}" class="read" text-anchor="end">M 1.00ms  ▲ TRIG</text>
      <text x="{sx + 18}" y="{sy + sh - 14}" class="read">f=1.337kHz</text>
      <text x="{sx + sw - 18}" y="{sy + sh - 14}" class="read" text-anchor="end">CH2 {sub}</text>
      <rect class="roll" x="{sx}" y="0" width="{sw}" height="60" fill="{ph}" opacity=".035"/>
      <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#scan)"/>
    </g>
    <g>
      {"".join(knobs)}
      <circle class="led" cx="{px + 22}" cy="274" r="4.5" fill="{ph}"/>
      <text x="{px + 34}" y="278" class="klabel">TRIG'D</text>
      <text x="{px + 118}" y="278" class="klabel" text-anchor="end">CH1</text>
    </g>
  </g>
</svg>
"""


# ================================================================ blueprint plotter

def build_blueprint(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """An engineering drawing: construction lines, then a pen plotter draws the name and dimensions it."""
    W, H = 900, 320
    cycle = 14.0
    size = min(10.0, (W - 200) / max(1, vecfont.width(name, 1)))
    tw = vecfont.width(name, size)
    th = 6 * size
    tx, ty = (W - tw) / 2, 104
    base = ty + th

    # construction lines first
    cons = []
    guides = [(tx - 40, ty, tx + tw + 40, ty), (tx - 40, base, tx + tw + 40, base),
              (tx - 40, ty + th / 2, tx + tw + 40, ty + th / 2)]
    for i, ch in enumerate(name):
        if ch.strip():
            gx = tx + i * vecfont.ADVANCE * size
            guides.append((gx, ty - 14, gx, base + 14))
    for i, (x1, y1, x2, y2) in enumerate(guides):
        t0 = 0.2 + i * 0.05
        cons.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" pathLength="1" class="cons">'
            f'<animate attributeName="stroke-dashoffset" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, t0, t0 + 0.6, cycle], cycle)}" values="1;1;0;0"/>'
            f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, 12.2, 13.0, cycle], cycle)}" values="1;1;0;0"/></line>'
        )

    # the name, plotted stroke by stroke
    draw0, draw1 = 1.6, 7.2
    strokes = [s for g in vecfont.strokes(name, size, tx, ty) for s in g if len(s) > 1]
    lens = [max(vecfont.length(s), 0.01) for s in strokes]
    total = sum(lens)
    ink, acc = [], 0.0
    for s, L in zip(strokes, lens):
        t0 = draw0 + (draw1 - draw0) * acc / total
        t1 = draw0 + (draw1 - draw0) * (acc + L) / total
        acc += L
        ink.append(
            f'<path d="{vecfont.path_d(s)}" pathLength="1" class="ink">'
            f'<animate attributeName="stroke-dashoffset" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, t0, t1, cycle], cycle)}" values="1;1;0;0"/>'
            f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
            f'keyTimes="{key_times([0, 12.2, 13.0, cycle], cycle)}" values="1;1;0;0"/></path>'
        )
    motion = " ".join(vecfont.path_d(s) for s in strokes)

    # dimension lines, appearing after the plot
    def appear(t0: float) -> str:
        return (f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
                f'keyTimes="{key_times([0, t0, t0 + 0.5, 12.2, 13.0, cycle], cycle)}" values="0;0;1;1;0;0"/>')

    dy = ty - 30
    dim_w = (
        f'<g class="dim" opacity="0">{appear(7.5)}'
        f'<line x1="{tx:.1f}" y1="{ty - 6:.1f}" x2="{tx:.1f}" y2="{dy - 8:.1f}"/>'
        f'<line x1="{tx + tw:.1f}" y1="{ty - 6:.1f}" x2="{tx + tw:.1f}" y2="{dy - 8:.1f}"/>'
        f'<line x1="{tx:.1f}" y1="{dy}" x2="{tx + tw:.1f}" y2="{dy}" marker-start="url(#arrow)" marker-end="url(#arrow)"/>'
        f'<rect x="{tx + tw / 2 - 34:.1f}" y="{dy - 9}" width="68" height="18" fill="#0b3a6e" stroke="none"/>'
        f'<text x="{tx + tw / 2:.1f}" y="{dy + 4}" class="dimtxt" text-anchor="middle">{tw:.1f}</text></g>'
    )
    lx = tx - 26
    dim_h = (
        f'<g class="dim" opacity="0">{appear(8.0)}'
        f'<line x1="{lx - 8:.1f}" y1="{ty:.1f}" x2="{tx - 6:.1f}" y2="{ty:.1f}"/>'
        f'<line x1="{lx - 8:.1f}" y1="{base:.1f}" x2="{tx - 6:.1f}" y2="{base:.1f}"/>'
        f'<line x1="{lx:.1f}" y1="{ty:.1f}" x2="{lx:.1f}" y2="{base:.1f}" marker-start="url(#arrow)" marker-end="url(#arrow)"/>'
        f'<text x="{lx - 6:.1f}" y="{ty + th / 2 + 4:.1f}" class="dimtxt" text-anchor="end">{th:.1f}</text></g>'
    )
    # detail callout circling the first letter
    r = size * 4.6
    ccx, ccy = tx + 2 * size, ty + th / 2
    callout = (
        f'<g class="dim" opacity="0">{appear(8.6)}'
        f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r:.1f}" stroke-dasharray="6 4"/>'
        f'<polyline points="{ccx + r * .7:.1f},{ccy + r * .7:.1f} {ccx + r * 1.2:.1f},{base + 46:.1f} {ccx + r * 1.2 + 70:.1f},{base + 46:.1f}" fill="none"/>'
        f'<text x="{ccx + r * 1.2 + 4:.1f}" y="{base + 41:.1f}" class="dimtxt">DETAIL A</text></g>'
    )

    grid_minor = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W, 10)) + \
        "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 10))
    grid_major = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W, 50)) + \
        "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 50))
    m = 16  # sheet margin
    zones = "".join(
        f'<text x="{m + (W - 2 * m) * (i + .5) / 8:.0f}" y="{m - 4}" class="zone" text-anchor="middle">{i + 1}</text>'
        f'<line x1="{m + (W - 2 * m) * i / 8:.0f}" y1="{m - 12}" x2="{m + (W - 2 * m) * i / 8:.0f}" y2="{m}"/>'
        for i in range(8)
    ) + "".join(
        f'<text x="{m - 8}" y="{m + (H - 2 * m) * (i + .5) / 4 + 4:.0f}" class="zone" text-anchor="middle">{"ABCD"[i]}</text>'
        for i in range(4)
    )
    # title block
    bw, bh = 300, 64
    bx, by = W - m - bw, H - m - bh
    sub = esc((lines[0] if lines else "").upper())
    title_block = f"""
    <g class="tb">
      <rect x="{bx}" y="{by}" width="{bw}" height="{bh}"/>
      <line x1="{bx}" y1="{by + 22}" x2="{bx + bw}" y2="{by + 22}"/>
      <line x1="{bx}" y1="{by + 44}" x2="{bx + bw}" y2="{by + 44}"/>
      <line x1="{bx + 200}" y1="{by + 44}" x2="{bx + 200}" y2="{by + bh}"/>
      <line x1="{bx + 100}" y1="{by + 44}" x2="{bx + 100}" y2="{by + bh}"/>
    </g>
    <text x="{bx + 8}" y="{by + 15}" class="tbtxt"><tspan class="tbk">TITLE </tspan>{esc(name.upper())}</text>
    <text x="{bx + 8}" y="{by + 37}" class="tbtxt"><tspan class="tbk">DESC </tspan>{sub}</text>
    <text x="{bx + 8}" y="{by + 58}" class="tbtxt"><tspan class="tbk">SCALE </tspan>1:1</text>
    <text x="{bx + 108}" y="{by + 58}" class="tbtxt"><tspan class="tbk">SHEET </tspan>1/1</text>
    <text x="{bx + 208}" y="{by + 58}" class="tbtxt"><tspan class="tbk">REV </tspan>A</text>"""
    stack = esc("  /  ".join(t.upper() for t in tags[:6]))

    return f"""{svg_open(W, H, name)}
  <defs>
    <radialGradient id="paper" cx="50%" cy="40%" r="75%">
      <stop offset="0" stop-color="#1557a0"/><stop offset="1" stop-color="#0b3a6e"/>
    </radialGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M0 1 L10 5 L0 9 Z" fill="#e8f1ff"/>
    </marker>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <style>
    .minor {{ stroke: #fff; stroke-opacity: .05; }}
    .major {{ stroke: #fff; stroke-opacity: .11; }}
    .border {{ fill: none; stroke: #e8f1ff; stroke-opacity: .7; stroke-width: 1.5; }}
    .zone  {{ font: 600 9px {MONO}; fill: #cfe0ff; opacity: .6; }}
    .zones line {{ stroke: #e8f1ff; stroke-opacity: .5; }}
    .cons  {{ stroke: #9fc3ff; stroke-width: .8; stroke-opacity: .55; stroke-dasharray: 1 1; }}
    .ink   {{ fill: none; stroke: #f4f8ff; stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1 1; }}
    .dim   {{ stroke: #e8f1ff; stroke-width: 1; fill: none; }}
    .dimtxt {{ font: 600 11px {MONO}; fill: #e8f1ff; stroke: none; letter-spacing: 1px; }}
    .tb    {{ fill: none; stroke: #e8f1ff; stroke-opacity: .7; }}
    .tbtxt {{ font: 600 10.5px {MONO}; fill: #f4f8ff; letter-spacing: .8px; }}
    .tbk   {{ fill: #9fc3ff; }}
    .stack {{ font: 600 10.5px {MONO}; fill: #cfe0ff; opacity: .75; letter-spacing: 1px; }}
    .pen   {{ fill: none; stroke: #ffd36b; stroke-width: 1.4; }}
    {reduced(".ink, .cons { stroke-dasharray: none; } .dim { opacity: 1; } .pen { display: none; }")}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#paper)"/>
    <g class="minor">{grid_minor}</g>
    <g class="major">{grid_major}</g>
    <rect x="{m}" y="{m}" width="{W - 2 * m}" height="{H - 2 * m}" class="border"/>
    <g class="zones">{zones}</g>
    {"".join(cons)}
    {"".join(ink)}
    {dim_w}
    {dim_h}
    {callout}
    <g class="pen">
      <animateMotion dur="{cycle}s" repeatCount="indefinite" calcMode="linear" path="{motion}"
        keyPoints="0;0;1;1" keyTimes="{key_times([0, draw0, draw1, cycle], cycle)}"/>
      <animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete"
        keyTimes="{key_times([0, draw0 - 0.3, draw1 + 0.3, cycle], cycle)}" values="0;1;0;0"/>
      <circle r="7"/><line x1="-13" y1="0" x2="-4" y2="0"/><line x1="4" y1="0" x2="13" y2="0"/>
      <line x1="0" y1="-13" x2="0" y2="-4"/><line x1="0" y1="4" x2="0" y2="13"/>
      <circle r="1.6" fill="#ffd36b"/>
    </g>
    <text x="{m + 14}" y="{H - m - 12}" class="stack">{stack}</text>
    {title_block}
  </g>
</svg>
"""


STYLES = {
    "splitflap": build_splitflap,
    "swarm": build_swarm,
    "liquid": build_liquid,
    "scope": build_scope,
    "blueprint": build_blueprint,
}
