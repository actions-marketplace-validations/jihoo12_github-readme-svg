"""More banner styles: a neofetch terminal, northern lights, a rotating hologram, a circuit
board, a hyperspace jump, a music player with a live equalizer, falling cherry blossoms
and a summer-youth sky.

Same contract as creative.py: (name, lines, tags, theme, seed) -> svg string, using only CSS
animations and SMIL so the banners play on GitHub.
"""

from __future__ import annotations

import math
import random

import vecfont
from common import MONO, SANS, THEMES, esc, key_times, stars, text_width
from creative import reduced, svg_open


def _handle(name: str) -> str:
    """A login-like handle from the display name: 'Hi, I'm Jihoo' -> 'jihoo'."""
    words = ["".join(c for c in w if c.isalnum()) for w in name.split()]
    words = [w for w in words if w]
    return (words[-1] if words else "user").lower()


def _clip(s: str, n: int) -> str:
    return s if len(s) <= n else s[: max(0, n - 1)] + "…"


def _shown(t_on: float, t_off: float, cycle: float) -> str:
    """SMIL child that makes its parent visible between t_on and t_off on every loop."""
    return (
        f'<animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{key_times([0, t_on, t_off, cycle], cycle)}" values="0;1;0;0"/>'
    )


def _seg_dist(p, a, b) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


# ================================================================ neofetch terminal

def _pixel_glyph(ch: str, res: int = 2, thick: float = 0.62) -> list[tuple[int, int]]:
    """Rasterise a vecfont glyph into (row, col) cells, res cells per glyph unit."""
    glyph = vecfont.GLYPHS.get(ch.upper()) or vecfont.GLYPHS["?"]
    segs = [(a, b) for s in glyph for a, b in zip(s, s[1:])]
    cells = []
    for r in range(6 * res + 1):
        for c in range(4 * res + 1):
            p = (c / res, r / res)
            if min(_seg_dist(p, a, b) for a, b in segs) <= thick:
                cells.append((r, c))
    return cells


def build_terminal(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A terminal window: `neofetch` is typed, then a system-info card about you prints out."""
    bg, (c1, c2, c3) = THEMES[theme]
    W = 900
    fs, lh = 13.5, 19.5
    cw = fs * 0.6
    cycle = 15.0
    t_clear = cycle - 0.4
    handle = _handle(name)
    host = f"{handle}@github"
    bar = 34
    left = 26

    prompt_parts = [(host, c2), (" ~ ", c3), ("$ ", "#c9d1d9")]
    prompt_len = sum(len(s) for s, _ in prompt_parts)

    def prompt(y: float) -> str:
        spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in prompt_parts)
        return f'<text x="{left}" y="{y:.1f}" class="t" textLength="{prompt_len * cw:.1f}">{spans}</text>'

    def typed(cmd: str, y: float, t0: float, speed: float, t_enter: float, uid: str) -> str:
        """Typed command: a clip rect grows one cell per keystroke, the cursor follows it."""
        x = left + prompt_len * cw
        n = len(cmd)
        times = [0.0] + [t0 + k * speed for k in range(1, n + 1)] + [t_clear, cycle]
        widths = [0.0] + [k * cw for k in range(1, n + 1)] + [0.0, 0.0]
        kt = key_times(times, cycle)
        return (
            f'<clipPath id="{uid}"><rect x="{x:.1f}" y="{y - fs:.1f}" width="0" height="{fs * 1.6:.1f}">'
            f'<animate attributeName="width" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{";".join(f"{v:.1f}" for v in widths)}"/></rect></clipPath>'
            f'<text x="{x:.1f}" y="{y:.1f}" class="t cmd" textLength="{n * cw:.1f}" clip-path="url(#{uid})">'
            f'{esc(cmd)}</text>'
            f'<rect class="cur" y="{y - fs + 2:.1f}" width="{cw:.1f}" height="{fs * 1.2:.1f}" x="{x:.1f}" opacity="0">'
            f'<animate attributeName="x" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{";".join(f"{x + v:.1f}" for v in widths)}"/>'
            f'{_shown(0, t_enter, cycle)}</rect>'
        )

    y_prompt = bar + 30
    t_type, speed = 0.8, 0.1
    t_enter = t_type + len("neofetch") * speed + 0.35
    t_out = t_enter + 0.15
    y_out = y_prompt + lh * 1.5

    # left: the handle's initial as a pixel-art logo, printed row by row
    cells = _pixel_glyph(handle[0])
    px = 10.5
    logo_x, logo_y = left + 8, y_out - fs + 2
    logo = []
    for r, c in cells:
        t = t_out + r * 0.045
        logo.append(
            f'<rect x="{logo_x + c * px:.1f}" y="{logo_y + r * px:.1f}" width="{px - 1.5:.1f}" '
            f'height="{px - 1.5:.1f}" rx="1.5" fill="url(#logoGrad)" opacity="0">{_shown(t, t_clear, cycle)}</rect>'
        )
    logo_w = (4 * 2 + 1) * px
    logo_h = (6 * 2 + 1) * px

    # right: the info card
    info_x = logo_x + logo_w + 44
    max_chars = int((W - info_x - 30) / cw)
    rows: list[list[tuple[str, str]]] = [[(handle, c2), ("@", "#c9d1d9"), ("github", c2)], [("-" * len(host), "#6e7681")]]
    fields = [
        ("Name", name),
        ("Role", lines[0] if lines else ""),
        ("About", lines[1] if len(lines) > 1 else ""),
        ("Stack", ", ".join(tags[:4])),
        ("Tools", ", ".join(tags[4:8])),
        ("Motto", lines[2] if len(lines) > 2 else ""),
        ("Theme", theme),
    ]
    for k, v in fields:
        if v:
            rows.append([(f"{k}: ", c1), (_clip(v, max_chars - len(k) - 2), "#c9d1d9")])
    info = []
    for i, row in enumerate(rows):
        y = y_out + i * lh
        n = sum(len(s) for s, _ in row)
        bold = ' font-weight="700"'
        spans = "".join(f'<tspan fill="{c}"{bold if c == c1 else ""}>{esc(s)}</tspan>' for s, c in row)
        info.append(
            f'<text x="{info_x:.1f}" y="{y:.1f}" class="t" textLength="{n * cw:.1f}" opacity="0">{spans}'
            f'{_shown(t_out + i * 0.07, t_clear, cycle)}</text>'
        )
    y_sw = y_out + len(rows) * lh + 4
    t_sw = t_out + len(rows) * 0.07
    swatch_cols = [c1, c2, c3, "#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3", "#c9d1d9"]
    swatches = "".join(
        f'<rect x="{info_x + i * cw * 3:.1f}" y="{y_sw - fs + 1:.1f}" width="{cw * 3:.1f}" height="{fs + 3:.1f}" '
        f'fill="{col}"/>' for i, col in enumerate(swatch_cols)
    )
    swatches = f'<g opacity="0">{swatches}{_shown(t_sw, t_clear, cycle)}</g>'

    y_final = max(logo_y + logo_h, y_sw + 4) + lh * 1.6
    t_final = t_sw + 0.25
    H = round(y_final + 22)
    xf = left + prompt_len * cw
    final = (
        f'<g opacity="0">{prompt(y_final)}'
        f'<rect class="cur blink" x="{xf:.1f}" y="{y_final - fs + 2:.1f}" width="{cw:.1f}" height="{fs * 1.2:.1f}"/>'
        f'{_shown(t_final, t_clear, cycle)}</g>'
    )

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="win" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0f141b"/><stop offset="1" stop-color="{bg}"/>
    </linearGradient>
    <linearGradient id="logoGrad" gradientUnits="userSpaceOnUse" x1="0" y1="{logo_y}" x2="0" y2="{logo_y + logo_h}">
      <stop offset="0" stop-color="{c1}"/><stop offset=".55" stop-color="{c3}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="20%" cy="40%" r="60%">
      <stop offset="0" stop-color="{c1}" stop-opacity=".12"/><stop offset="1" stop-color="{c1}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>
  <style>
    .t     {{ font: 500 {fs}px {MONO}; fill: #c9d1d9; white-space: pre; }}
    .cmd   {{ fill: #f0f6fc; font-weight: 700; }}
    .title {{ font: 600 12px {SANS}; fill: #8b949e; }}
    .cur   {{ fill: {c2}; }}
    .blink {{ animation: blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 0%, 50% {{ opacity: 1; }} 51%, 100% {{ opacity: 0; }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#win)"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
    <rect width="{W}" height="{bar}" fill="#161b22"/>
    <rect y="{bar}" width="{W}" height="1" fill="#30363d"/>
    <circle cx="22" cy="{bar / 2}" r="6" fill="#ff5f57"/>
    <circle cx="42" cy="{bar / 2}" r="6" fill="#febc2e"/>
    <circle cx="62" cy="{bar / 2}" r="6" fill="#28c840"/>
    <text x="{W / 2}" y="{bar / 2 + 4}" text-anchor="middle" class="title">{esc(host)} — zsh — 120×{round(H / lh)}</text>
    <g opacity="1">{prompt(y_prompt)}{_shown(0, t_clear, cycle)}</g>
    {typed("neofetch", y_prompt, t_type, speed, t_enter, "type1")}
    {"".join(logo)}
    {"".join(info)}
    {swatches}
    {final}
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#30363d"/>
</svg>
"""


# ================================================================ northern lights

def _ridge(rng: random.Random, W: float, base: float, rough: float, step: float) -> list[tuple[float, float]]:
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    pts = []
    for i in range(int(W / step) + 2):
        x = i * step
        n = 0.5 + 0.3 * math.sin(x / 97 + ph[0]) + 0.2 * math.sin(x / 41 + ph[1]) + 0.12 * math.sin(x / 17 + ph[2])
        pts.append((x, base - rough * n - rng.uniform(0, rough * 0.22)))
    return pts


def _ribbon(W: float, base: float, amp: float, height: float, phase: float) -> tuple[str, str]:
    """One frame of an aurora curtain: (filled band, lower hem). Every frame has the same structure."""
    xs = [x * 15.0 for x in range(int(W / 15) + 2)]
    top, bot = [], []
    for x in xs:
        cy = base + amp * math.sin(x / 170 + phase) + amp * 0.5 * math.sin(x / 73 - phase * 1.7)
        h = height * (0.5 + 0.5 * math.sin(x / 115 + phase * 1.3 + 1)) + 14
        top.append((x, cy - h))
        bot.append((x, cy))
    fmt = lambda pts: " L".join(f"{x:.0f} {y:.1f}" for x, y in pts)
    band = f"M{fmt(top)} L{fmt(bot[::-1])}Z"
    hem = f"M{fmt(bot)}"
    return band, hem


def build_borealis(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Northern lights ripple over a mountain lake; the curtains and stars reflect in the water."""
    W, H = 900, 290
    rng = random.Random(seed)
    bg, (c1, c2, c3) = THEMES[theme]
    horizon = 212
    subtitle = esc(lines[0] if lines else "")

    curtains = []
    for i, (col, base, amp, height, dur) in enumerate([
        (c1, 72, 10, 46, 23), (c2, 104, 16, 70, 17), (c3, 128, 12, 50, 20),
    ]):
        p0 = rng.uniform(0, 6)
        frames = [_ribbon(W, base, amp, height, p0 + k * 1.1) for k in range(4)]
        frames.append(frames[0])
        bands = ";".join(f[0] for f in frames)
        hems = ";".join(f[1] for f in frames)
        spl = ";".join([".45 0 .55 1"] * 4)
        anim = f'dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.25;.5;.75;1" keySplines="{spl}"'
        curtains.append(
            f'<linearGradient id="cg{i}" gradientUnits="userSpaceOnUse" x1="0" y1="{base - height - amp - 20}" x2="0" y2="{base + amp}">'
            f'<stop offset="0" stop-color="{c1}" stop-opacity="0"/><stop offset=".55" stop-color="{col}" stop-opacity=".35"/>'
            f'<stop offset=".9" stop-color="{col}" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/>'
            f'</linearGradient>'
            f'<path d="{frames[0][0]}" fill="url(#cg{i})" mask="url(#rayMask)"><animate attributeName="d" {anim} values="{bands}"/></path>'
            f'<path d="{frames[0][1]}" fill="none" stroke="{col}" stroke-width="2.5" opacity=".9"><animate attributeName="d" {anim} values="{hems}"/></path>'
        )

    # rays: a drifting pattern of vertical streaks masks the curtains
    rays = ['<rect width="240" height="300" fill="#fff" opacity=".3"/>']
    x = 0.0
    while x < 240:
        w = rng.uniform(1.5, 6)
        rays.append(f'<rect x="{x:.1f}" width="{w:.1f}" height="300" fill="#fff" opacity="{rng.uniform(.3, 1):.2f}"/>')
        x += w + rng.uniform(1, 7)

    far = _ridge(rng, W, horizon - 6, 52, 14)
    near = _ridge(rng, W, horizon + 2, 26, 9)
    poly = lambda pts: "M0 " + f"{horizon + 4} " + " ".join(f"L{x:.0f} {y:.1f}" for x, y in pts) + f" L{W} {horizon + 4}Z"

    trees = []
    for _ in range(26):
        tx = rng.choice([rng.uniform(0, 260), rng.uniform(640, W)])
        th = rng.uniform(12, 30)
        tw = th * 0.32
        tiers = " ".join(
            f"M{tx - tw * (1 - k * 0.22):.1f} {horizon - th * k * 0.28:.1f} L{tx:.1f} {horizon - th * (k * 0.28 + 0.45):.1f} "
            f"L{tx + tw * (1 - k * 0.22):.1f} {horizon - th * k * 0.28:.1f}Z" for k in range(3)
        )
        trees.append(f'<path d="{tiers}"/>')

    ripples = "\n    ".join(
        f'<rect class="rip" x="{rng.uniform(-40, W - 80):.0f}" y="{horizon + 8 + i * 6.5:.1f}" width="{rng.uniform(80, 260):.0f}" '
        f'height="1" style="animation-duration:{rng.uniform(4, 8):.1f}s;animation-delay:-{rng.uniform(0, 6):.1f}s"/>'
        for i in range(11)
    )

    scene = f"""<g filter="url(#soft)">{"".join(curtains)}</g>"""

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#01030c"/><stop offset=".7" stop-color="{bg}"/><stop offset="1" stop-color="#0d2236"/>
    </linearGradient>
    <linearGradient id="lake" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#020611" stop-opacity=".35"/><stop offset="1" stop-color="#01030a" stop-opacity=".95"/>
    </linearGradient>
    <pattern id="rays" width="240" height="300" patternUnits="userSpaceOnUse">
      {"".join(rays)}
      <animateTransform attributeName="patternTransform" type="translate" from="0 0" to="240 0" dur="38s" repeatCount="indefinite"/>
    </pattern>
    <mask id="rayMask"><rect width="{W}" height="{H}" fill="url(#rays)"/></mask>
    <filter id="soft" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <filter id="blurR" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="2 5"/></filter>
    <filter id="tglow" x="-20%" y="-60%" width="140%" height="220%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="meteor" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/>
    </linearGradient>
    <clipPath id="sky-clip"><rect width="{W}" height="{horizon}"/></clipPath>
    <clipPath id="lake-clip"><rect y="{horizon}" width="{W}" height="{H - horizon}"/></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <g id="world">
      {stars(90, rng, W, horizon - 20)}
      {scene}
    </g>
  </defs>
  <style>
    .star  {{ fill: #fff; animation: twinkle ease-in-out infinite alternate; }}
    @keyframes twinkle {{ from {{ opacity: .15; }} to {{ opacity: .9; }} }}
    .name  {{ font: 300 46px {SANS}; fill: #f4fbff; letter-spacing: 7px; animation: arrive 3s ease-out both; }}
    .sub   {{ font: 500 14px {SANS}; fill: #cfe7ff; letter-spacing: 4px; opacity: .8; animation: arrive 3s 1s ease-out both; }}
    @keyframes arrive {{ from {{ opacity: 0; letter-spacing: 18px; }} }}
    .rip   {{ fill: #fff; opacity: .1; animation: rip ease-in-out infinite alternate; }}
    @keyframes rip {{ from {{ transform: translateX(-30px); opacity: .02; }} to {{ transform: translateX(30px); opacity: .14; }} }}
    .meteor {{ animation: meteor 11s ease-in infinite; opacity: 0; }}
    @keyframes meteor {{ 0%, 70% {{ transform: translate(0, 0); opacity: 0; }} 71% {{ opacity: 1; }}
                        77%, 100% {{ transform: translate(-260px, 90px); opacity: 0; }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <use href="#world" clip-path="url(#sky-clip)"/>
    <line class="meteor" x1="{W - 160}" y1="22" x2="{W - 100}" y2="2" stroke="url(#meteor)" stroke-width="1.6" stroke-linecap="round"/>
    <g clip-path="url(#lake-clip)">
      <g transform="translate(0 {2 * horizon}) scale(1 -1)" opacity=".55" filter="url(#blurR)">
        <use href="#world"/>
        <path d="{poly(far)}" fill="#081424"/><path d="{poly(near)}" fill="#03070f"/>
        <g fill="#03070f">{"".join(trees)}</g>
      </g>
      <rect y="{horizon}" width="{W}" height="{H - horizon}" fill="url(#lake)"/>
      {ripples}
    </g>
    <path d="{poly(far)}" fill="#081424"/>
    <path d="{poly(near)}" fill="#03070f"/>
    <g fill="#03070f">{"".join(trees)}</g>
    <rect y="{horizon + 3}" width="{W}" height="1" fill="{c2}" opacity=".18"/>
    <text x="{W / 2}" y="150" text-anchor="middle" class="name" filter="url(#tglow)">{esc(name)}</text>
    <text x="{W / 2}" y="180" text-anchor="middle" class="sub">{subtitle}</text>
  </g>
</svg>
"""


# ================================================================ hologram

def _geodesic() -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """A frequency-2 geodesic sphere (42 vertices, 120 edges), with one 5-fold vertex on the +y axis."""
    p = (1 + 5 ** 0.5) / 2
    V = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p), (0, -1, -p), (0, 1, -p),
         (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2),
         (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11),
         (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    norm = lambda v: tuple(c / math.sqrt(sum(k * k for k in v)) for c in v)
    verts = [norm(v) for v in V]
    cache: dict[tuple[int, int], int] = {}

    def mid(a: int, b: int) -> int:
        key = (min(a, b), max(a, b))
        if key not in cache:
            verts.append(norm(tuple((verts[a][i] + verts[b][i]) / 2 for i in range(3))))
            cache[key] = len(verts) - 1
        return cache[key]

    edges = set()
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
        for f in ((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)):
            for i in range(3):
                u, v = f[i], f[(i + 1) % 3]
                edges.add((min(u, v), max(u, v)))

    # rotate vertex 0 onto +y (Rodrigues), so spinning around y has 5-fold symmetry
    v0 = verts[0]
    axis = (v0[2], 0.0, -v0[0])  # v0 x (0, 1, 0)
    s = math.sqrt(sum(k * k for k in axis))
    k = tuple(c / s for c in axis)
    ang = math.acos(v0[1])
    ca, sa = math.cos(ang), math.sin(ang)

    def rot(v):
        kv = sum(k[i] * v[i] for i in range(3))
        cross = (k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0])
        return tuple(v[i] * ca + cross[i] * sa + k[i] * kv * (1 - ca) for i in range(3))

    return [rot(v) for v in verts], sorted(edges)


def _holo_frames(cx: float, cy: float, R: float, steps: int, tilt: float) -> tuple[list[str], list[str]]:
    """Path frames for a rotation of 72 degrees (one symmetry period): (all edges, front-facing parts)."""
    verts, edges = _geodesic()
    ct, st = math.cos(tilt), math.sin(tilt)
    back_frames, front_frames = [], []
    for f in range(steps + 1):
        th = 2 * math.pi / 5 * f / steps
        c, s = math.cos(th), math.sin(th)
        view = []
        for x, y, z in verts:
            x, z = x * c + z * s, -x * s + z * c  # spin around y
            y, z = y * ct - z * st, y * st + z * ct  # tilt toward the viewer
            view.append((x, y, z))
        scr = lambda v: (cx + R * v[0], cy - R * v[1])
        back, front = [], []
        for a, b in edges:
            A, B = view[a], view[b]
            pa, pb = scr(A), scr(B)
            back.append(f"M{pa[0]:.1f} {pa[1]:.1f}L{pb[0]:.1f} {pb[1]:.1f}")
            za, zb = A[2], B[2]
            if za >= 0 and zb >= 0:
                p, q = pa, pb
            elif za < 0 and zb < 0:
                p = q = pa if za > zb else pb  # zero length: invisible with butt caps
            else:
                t = za / (za - zb)
                m = scr(tuple(A[i] + t * (B[i] - A[i]) for i in range(3)))
                p, q = (pa, m) if za >= 0 else (m, pb)
            front.append(f"M{p[0]:.1f} {p[1]:.1f}L{q[0]:.1f} {q[1]:.1f}")
        back_frames.append("".join(back))
        front_frames.append("".join(front))
    return back_frames, front_frames


def build_hologram(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A holographic ID card: a wireframe globe spins above a projector next to a scanned profile."""
    W, H = 900, 280
    rng = random.Random(seed)
    _, (c1, c2, c3) = THEMES[theme]
    hc = c3
    cx, cy, R = 175, 118, 80
    back, front = _holo_frames(cx, cy, R, 12, math.radians(16))
    spin = 4.5
    base_y = 246

    tx = 360
    name_fs = min(40, (W - tx - 50) / max(1, len(name)) / 0.62)
    role = esc(_clip(lines[0], 46) if lines else "")
    skills = esc(_clip("  ".join(t.upper() for t in tags[:6]), 52))
    uid = f"{rng.randrange(16 ** 6):06X}"
    role_w = text_width("› " + (_clip(lines[0], 46) if lines else ""), 14)

    rings = []
    for i, (rx, ry, rot, dur) in enumerate([(R * 1.32, R * 0.3, -12, 9), (R * 1.18, R * 0.24, 9, 13)]):
        rings.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.1f}" ry="{ry:.1f}" transform="rotate({rot} {cx} {cy})" '
            f'class="ring" style="animation-duration:{dur}s;{"animation-direction:reverse" if i else ""}"/>'
        )

    corners = []
    x0, y0, x1, y1 = tx - 22, 34, W - 26, H - 34
    for (x, y, dx, dy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        corners.append(f'<path d="M{x} {y + 16 * dy} L{x} {y} L{x + 16 * dx} {y}"/>')

    return f"""{svg_open(W, H, name)}
  <defs>
    <radialGradient id="bg" cx="20%" cy="45%" r="80%">
      <stop offset="0" stop-color="#0b1b2b"/><stop offset="1" stop-color="#03070d"/>
    </radialGradient>
    <linearGradient id="cone" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="{hc}" stop-opacity=".45"/><stop offset="1" stop-color="{hc}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="core"><stop offset="0" stop-color="#fff" stop-opacity=".9"/>
      <stop offset=".25" stop-color="{hc}" stop-opacity=".6"/><stop offset="1" stop-color="{hc}" stop-opacity="0"/></radialGradient>
    <linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{hc}" stop-opacity="0"/><stop offset="1" stop-color="{hc}" stop-opacity=".55"/>
    </linearGradient>
    <pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1.4" fill="#000" opacity=".45"/></pattern>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="sphere"><circle cx="{cx}" cy="{cy}" r="{R + 1}"/></clipPath>
    <clipPath id="roleClip"><rect x="{tx}" y="120" width="0" height="26">
      <animate attributeName="width" dur="9s" repeatCount="indefinite" keyTimes="0;.1;.3;.9;1" values="0;0;{role_w + 10:.0f};{role_w + 10:.0f};0"/>
    </rect></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .holo  {{ animation: flicker 7s infinite; }}
    @keyframes flicker {{ 0%, 91%, 100% {{ opacity: 1; transform: none; }} 92% {{ opacity: .45; transform: translateX(4px) skewX(-6deg); }}
                         93% {{ opacity: 1; transform: none; }} 95% {{ opacity: .6; }} 96% {{ opacity: 1; }} }}
    .wire  {{ fill: none; stroke: {hc}; stroke-linecap: butt; }}
    .ring  {{ fill: none; stroke: {hc}; stroke-width: 1.2; stroke-dasharray: 3 7 26 7; opacity: .6; animation: ring linear infinite; }}
    @keyframes ring {{ to {{ stroke-dashoffset: -172; }} }}
    .scan  {{ animation: scan 3.2s linear infinite; }}
    @keyframes scan {{ from {{ transform: translateY(-{R + 30}px); }} to {{ transform: translateY({R + 10}px); }} }}
    .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 2.2s ease-in-out infinite; }}
    @keyframes pulse {{ 50% {{ transform: scale(1.35); opacity: .6; }} }}
    .lbl   {{ font: 600 11px {MONO}; fill: {hc}; letter-spacing: 2.5px; opacity: .75; }}
    .name  {{ font: 700 {name_fs:.1f}px {SANS}; fill: #e9fbff; letter-spacing: 2px; }}
    .role  {{ font: 500 14px {MONO}; fill: {hc}; }}
    .val   {{ font: 600 11px {MONO}; fill: #cfefff; letter-spacing: 1.5px; }}
    .brk   {{ fill: none; stroke: {hc}; stroke-width: 1.6; opacity: .8; }}
    .dot   {{ fill: {c2}; animation: blink 1.2s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: .15; }} }}
    .fill  {{ fill: {hc}; transform-box: fill-box; transform-origin: left; animation: sync 4.5s ease-in-out infinite; }}
    @keyframes sync {{ 0% {{ transform: scaleX(0); }} 70%, 100% {{ transform: scaleX(1); }} }}
    .cone  {{ animation: cone 2.6s ease-in-out infinite alternate; }}
    @keyframes cone {{ from {{ opacity: .55; }} to {{ opacity: 1; }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <g class="holo">
      <path class="cone" d="M{cx - 46} {base_y} L{cx - R - 6} {cy} A{R + 6} {R + 6} 0 0 1 {cx + R + 6} {cy} L{cx + 46} {base_y} Z" fill="url(#cone)" opacity=".7"/>
      <circle cx="{cx}" cy="{cy}" r="34" fill="url(#core)" class="pulse"/>
      <path class="wire" stroke-width=".9" opacity=".22" d="{back[0]}">
        <animate attributeName="d" dur="{spin}s" repeatCount="indefinite" values="{";".join(back)}"/>
      </path>
      <path class="wire" stroke-width="1.5" filter="url(#glow)" d="{front[0]}">
        <animate attributeName="d" dur="{spin}s" repeatCount="indefinite" values="{";".join(front)}"/>
      </path>
      <circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{hc}" stroke-opacity=".35"/>
      {"".join(rings)}
      <g clip-path="url(#sphere)"><rect class="scan" x="{cx - R}" y="{cy}" width="{2 * R}" height="22" fill="url(#scanG)"/></g>
      <rect x="{cx - R - 20}" y="{cy - R - 20}" width="{2 * R + 40}" height="{base_y - cy + R + 20}" fill="url(#lines)"/>
    </g>
    <ellipse cx="{cx}" cy="{base_y}" rx="58" ry="11" fill="#0e2233" stroke="{hc}" stroke-opacity=".6"/>
    <ellipse cx="{cx}" cy="{base_y}" rx="44" ry="7.5" fill="none" stroke="{hc}" stroke-opacity=".9" class="cone"/>
    <ellipse cx="{cx}" cy="{base_y + 9}" rx="66" ry="10" fill="none" stroke="{hc}" stroke-opacity=".2"/>

    <g class="brk">{"".join(corners)}</g>
    <text x="{tx}" y="64" class="lbl">◢ HOLOGRAPHIC ID · {uid}</text>
    <g class="holo"><text x="{tx}" y="{64 + name_fs + 6:.0f}" class="name" filter="url(#glow)">{esc(name)}</text></g>
    <text x="{tx}" y="138" class="role" clip-path="url(#roleClip)">› {role}</text>
    <text x="{tx}" y="178" class="lbl">SKILLS</text>
    <text x="{tx + 80}" y="178" class="val">{skills}</text>
    <text x="{tx}" y="202" class="lbl">STATUS</text>
    <circle cx="{tx + 85}" cy="198" r="4" class="dot"/>
    <text x="{tx + 96}" y="202" class="val">ONLINE</text>
    <text x="{tx}" y="226" class="lbl">SYNC</text>
    <rect x="{tx + 80}" y="219" width="300" height="6" rx="3" fill="{hc}" opacity=".15"/>
    <rect x="{tx + 80}" y="219" width="300" height="6" rx="3" class="fill"/>
  </g>
</svg>
"""


# ================================================================ circuit board

def build_circuit(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A circuit board: signal pulses race along copper traces into a chip that carries your name."""
    W, H = 900, 300
    rng = random.Random(seed)
    bg, (c1, c2, c3) = THEMES[theme]
    handle = _handle(name)
    name_fs = min(32, 420 / max(1, len(name)) / 0.6)
    cw = max(text_width(name, name_fs) + 90, 310)
    ch = 112
    cx, cy = W / 2, 146
    x0, x1, y0, y1 = cx - cw / 2, cx + cw / 2, cy - ch / 2, cy + ch / 2
    accents = [c1, c2, c3]

    traces = []  # (points from the far end to the pin, pin rect, side)
    pitch, fan, lead = 14, 22, 18
    for side in (-1, 1):
        for i in range(6):
            k = i - 2.5
            py = cy + k * pitch
            px = x0 if side < 0 else x1
            dy = k * fan
            end = rng.uniform(26, 96)
            end_x = end if side < 0 else W - end
            pts = [(px, py), (px + side * lead, py), (px + side * (lead + abs(dy)), py + dy), (end_x, py + dy)]
            traces.append((pts[::-1], (px - (6 if side < 0 else 0), py - 2.5, 6, 5), "side"))
    m = int((cw - 70) / 18) + 1
    for vside in (-1, 1):
        for j in range(m):
            kx = j - (m - 1) / 2
            px = cx + kx * 18
            py = y0 if vside < 0 else y1
            dx = kx * 3.5
            lead_v = rng.uniform(8, 16)
            end_y = rng.uniform(16, 38)
            end_y = end_y if vside < 0 else H - end_y
            pts = [(px, py), (px, py + vside * lead_v), (px + dx, py + vside * (lead_v + abs(dx))), (px + dx, end_y)]
            traces.append((pts[::-1], (px - 2.5, py - (6 if vside < 0 else 0), 5, 6), "v"))

    base, pulses, pads, vias = [], [], [], []
    for pts, (rx, ry, rw, rh), kind in traces:
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        dur = rng.uniform(3.2, 6.5)
        delay = rng.uniform(0, dur)
        col = rng.choice(accents)
        timing = f"animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"
        base.append(f'<path d="{d}"/>')
        pulses.append(f'<path d="{d}" pathLength="100" class="pulse" stroke="{col}" style="{timing}"/>')
        pads.append(f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{rw}" height="{rh}" class="pad" style="{timing};--c:{col}"/>')
        ex, ey = pts[0]
        vias.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4"/>')

    labels = []
    side_traces = [t for t in traces if t[2] == "side"]
    order = sorted(range(len(side_traces)), key=lambda i: -abs((i % 6) - 2.5))
    for tag, i in zip(tags, order):
        (ex, ey) = side_traces[i][0][0]
        left = ex < cx
        labels.append(
            f'<text x="{ex + (8 if left else -8):.1f}" y="{ey - 8:.1f}" class="silk" '
            f'text-anchor="{"start" if left else "end"}">{esc(tag.upper())}</text>'
        )

    holes = "".join(
        f'<circle cx="{x}" cy="{y}" r="7" class="hole"/><circle cx="{x}" cy="{y}" r="3.2" fill="#000"/>'
        for x, y in [(20, 20), (W - 20, 20), (20, H - 20), (W - 20, H - 20)]
    )
    sub = esc(_clip(lines[0], int((cw - 40) / 7.2)) if lines else "")

    return f"""{svg_open(W, H, name)}
  <defs>
    <pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="1" height="7" fill="{c2}" opacity=".06"/>
    </pattern>
    <radialGradient id="board" cx="50%" cy="50%" r="75%">
      <stop offset="0" stop-color="#0c1d18"/><stop offset="1" stop-color="{bg}"/>
    </radialGradient>
    <linearGradient id="chip" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#22262c"/><stop offset="1" stop-color="#121418"/>
    </linearGradient>
    <linearGradient id="nameG" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c1}"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{c3}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .base  {{ fill: none; stroke: #2f6b4f; stroke-opacity: .55; stroke-width: 2.4; stroke-linejoin: round; }}
    .pulse {{ fill: none; stroke-width: 3; stroke-linecap: round; stroke-dasharray: 9 200; stroke-dashoffset: 9;
             animation: run linear infinite; }}
    @keyframes run {{ 0% {{ stroke-dashoffset: 9; }} 50%, 100% {{ stroke-dashoffset: -100; }} }}
    .pad   {{ fill: #c9a24a; animation: hit linear infinite; }}
    @keyframes hit {{ 0%, 47% {{ fill: #c9a24a; }} 50% {{ fill: var(--c); }} 60%, 100% {{ fill: #c9a24a; }} }}
    .vias circle {{ fill: #07110d; stroke: #c9a24a; stroke-width: 2; }}
    .hole  {{ fill: none; stroke: #c9a24a; stroke-width: 2.5; opacity: .8; }}
    .silk  {{ font: 600 10px {MONO}; fill: #e6edf3; opacity: .55; letter-spacing: 1.5px; }}
    .name  {{ font: 800 {name_fs:.1f}px {MONO}; fill: url(#nameG); }}
    .sub   {{ font: 500 12px {MONO}; fill: #8b949e; }}
    .led   {{ fill: {c2}; animation: led 1.6s steps(1) infinite; }}
    @keyframes led {{ 50% {{ opacity: .2; }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#board)"/>
    <rect width="{W}" height="{H}" fill="url(#hatch)"/>
    {holes}
    <g class="base">{"".join(base)}</g>
    <g filter="url(#glow)">{"".join(pulses)}</g>
    <g class="vias">{"".join(vias)}</g>
    {"".join(labels)}
    <rect x="{x0 + 4}" y="{y0 + 5}" width="{cw}" height="{ch}" rx="6" fill="#000" opacity=".45"/>
    <rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="6" fill="url(#chip)" stroke="#3a3f47"/>
    {"".join(pads)}
    <circle cx="{x0 + 16}" cy="{y0 + 16}" r="5" fill="#0b0c0e" stroke="#3a3f47"/>
    <text x="{x0 + 28}" y="{y0 + 20}" class="silk">U1</text>
    <circle cx="{x1 - 16}" cy="{y0 + 16}" r="3.5" class="led"/>
    <text x="{cx}" y="{cy + name_fs * 0.3:.1f}" text-anchor="middle" class="name" filter="url(#glow)">{esc(name)}</text>
    <text x="{cx}" y="{y1 - 16}" text-anchor="middle" class="sub">{sub}</text>
    <text x="40" y="{H - 16}" class="silk">{esc(handle.upper())}-BOARD REV 1.0</text>
    <text x="{W - 40}" y="{H - 16}" class="silk" text-anchor="end">github.com/{esc(handle)}</text>
  </g>
</svg>
"""


# ================================================================ hyperspace warp

def build_warp(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A jump to hyperspace: star streaks rush past, your name zooms in, holds, then flies by."""
    W, H = 900, 260
    rng = random.Random(seed)
    _, (c1, c2, c3) = THEMES[theme]
    cx, cy = W / 2, H / 2
    cycle = 9.0
    name_fs = min(62, (W - 140) / max(1, len(name)) / 0.6)
    sub = esc(lines[0] if lines else "")
    dest = esc(" › ".join(t.upper() for t in tags[:4]))

    streaks = []
    for _ in range(170):
        a = rng.uniform(0, 2 * math.pi)
        r1 = rng.uniform(330, 560)
        ln = rng.uniform(40, 160)
        ca, sa = math.cos(a), math.sin(a)
        col = rng.choice(["#eaf2ff"] * 5 + [c1, c2, c3])
        dur = rng.uniform(0.9, 2.3)
        streaks.append(
            f'<line x1="{cx + ca * r1:.1f}" y1="{cy + sa * r1:.1f}" x2="{cx + ca * (r1 + ln):.1f}" y2="{cy + sa * (r1 + ln):.1f}" '
            f'stroke="{col}" stroke-width="{rng.uniform(1, 2.6):.1f}" class="s" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:-{rng.uniform(0, dur):.2f}s"/>'
        )

    hud = []
    for (x, y, dx, dy) in [(24, 24, 1, 1), (W - 24, 24, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)]:
        hud.append(f'<path d="M{x} {y + 18 * dy} L{x} {y} L{x + 18 * dx} {y}"/>')

    return f"""{svg_open(W, H, name)}
  <defs>
    <radialGradient id="space" cx="50%" cy="50%" r="65%">
      <stop offset="0" stop-color="{c1}" stop-opacity=".45"/><stop offset=".35" stop-color="#0a0c25"/>
      <stop offset="1" stop-color="#020208"/>
    </radialGradient>
    <radialGradient id="core">
      <stop offset="0" stop-color="#fff"/><stop offset=".2" stop-color="{c3}" stop-opacity=".7"/>
      <stop offset="1" stop-color="{c3}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="nameG" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c3}"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{c1}"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-50%" width="140%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .s     {{ stroke-linecap: round; transform-origin: {cx}px {cy}px; opacity: 0;
             animation: fly cubic-bezier(.6, 0, 1, .6) infinite; }}
    @keyframes fly {{ 0% {{ transform: scale(.03); opacity: 0; }} 30% {{ opacity: 1; }} 100% {{ transform: scale(1.05); opacity: 1; }} }}
    .core  {{ transform-origin: {cx}px {cy}px; animation: core 1.4s ease-in-out infinite alternate; }}
    @keyframes core {{ from {{ transform: scale(.8); opacity: .7; }} to {{ transform: scale(1.25); opacity: 1; }} }}
    .name, .sub {{ transform-box: fill-box; transform-origin: center; }}
    .name  {{ font: 800 {name_fs:.1f}px {SANS}; fill: url(#nameG); letter-spacing: 2px; animation: zoom {cycle}s infinite; }}
    @keyframes zoom {{
      0%   {{ transform: scale(.05); opacity: 0; animation-timing-function: cubic-bezier(.2, .9, .3, 1); }}
      13%  {{ transform: scale(1); opacity: 1; }}
      82%  {{ transform: scale(1.07); opacity: 1; animation-timing-function: cubic-bezier(.7, 0, 1, .5); }}
      92%  {{ transform: scale(6); opacity: 0; }}
      100% {{ transform: scale(.05); opacity: 0; }} }}
    .sub   {{ font: 600 15px {MONO}; fill: #dfe7ff; letter-spacing: 4px; animation: sub {cycle}s infinite; }}
    @keyframes sub {{ 0%, 15% {{ opacity: 0; transform: translateY(8px); }} 22%, 78% {{ opacity: .85; transform: none; }}
                     84%, 100% {{ opacity: 0; }} }}
    .flash {{ animation: flash {cycle}s infinite; }}
    @keyframes flash {{ 0%, 86% {{ opacity: 0; }} 89% {{ opacity: .4; }} 96%, 100% {{ opacity: 0; }} }}
    .hud   {{ fill: none; stroke: {c3}; stroke-width: 1.6; opacity: .7; }}
    .ht    {{ font: 600 10.5px {MONO}; fill: {c3}; letter-spacing: 2px; opacity: .8; }}
    .blink {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: .2; }} }}
    {reduced(".s { opacity: .6; transform: scale(.6); } .name { opacity: 1; } .sub { opacity: .85; }")}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#space)"/>
    <circle cx="{cx}" cy="{cy}" r="70" fill="url(#core)" class="core"/>
    {"".join(streaks)}
    <rect width="{W}" height="{H}" fill="#fff" class="flash" opacity="0"/>
    <text x="{cx}" y="{cy + name_fs * 0.3:.1f}" text-anchor="middle" class="name" filter="url(#glow)">{esc(name)}</text>
    <text x="{cx}" y="{cy + name_fs * 0.3 + 34:.1f}" text-anchor="middle" class="sub">{sub}</text>
    <g class="hud">{"".join(hud)}</g>
    <text x="34" y="42" class="ht blink">HYPERDRIVE // ENGAGED</text>
    <text x="{W - 34}" y="42" class="ht" text-anchor="end">WARP 9.{seed % 10}</text>
    <text x="34" y="{H - 32}" class="ht">DEST › {dest}</text>
    <text x="{W - 34}" y="{H - 32}" class="ht" text-anchor="end">{rng.randint(10, 99)}°{rng.randint(10, 59)}′N  {rng.randint(100, 179)}°{rng.randint(10, 59)}′E</text>
  </g>
</svg>
"""


# ================================================================ music player

def build_equalizer(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """A 'now playing' card: a spinning record, a live spectrum with reflection and a running clock."""
    W, H = 900, 270
    rng = random.Random(seed)
    bg, (c1, c2, c3) = THEMES[theme]
    ax, ay, asz = 36, 40, 190
    vx, vy, vr = ax + asz + 6, ay + asz / 2, 84
    rx = ax + asz + 110
    initial = esc(_handle(name)[:1].upper())
    title_fs = min(32, (W - rx - 150) / max(1, len(name)) / 0.58)
    artist = esc(lines[0] if lines else "")

    n = 44
    bw, gap = 8, 4.2
    base = 196
    bars = []
    for i in range(n):
        u = i / (n - 1)
        hmax = 58 * (0.32 + 0.68 * math.exp(-((u - 0.28) / 0.33) ** 2)) * rng.uniform(0.75, 1.05)
        x = rx + i * (bw + gap)
        bars.append(
            f'<rect x="{x:.1f}" y="{base - hmax:.1f}" width="{bw}" height="{hmax:.1f}" rx="2" class="b eq{rng.randrange(5)}" '
            f'style="animation-duration:{rng.uniform(.7, 1.5):.2f}s;animation-delay:-{rng.uniform(0, 1.5):.2f}s"/>'
        )
    bars_w = n * (bw + gap) - gap
    eq_keys = [
        (.25, 1, .45, .8, .3), (.6, .2, .9, .4, 1), (.4, .75, .3, 1, .5), (1, .5, .7, .2, .85), (.3, .9, .6, .35, .7),
    ]
    eq_css = "\n    ".join(
        f"@keyframes eq{k} {{ " + " ".join(f"{p * 25}% {{ transform: scaleY({v}); }}" for p, v in enumerate(vals))
        + " }" for k, vals in enumerate(eq_keys)
    ) + "\n    " + " ".join(f".eq{k} {{ animation-name: eq{k}; }}" for k in range(5))

    chips, cx_ = [], rx
    for t in tags[:4]:
        w = len(t) * 7 + 20
        chips.append(f'<rect x="{cx_}" y="128" width="{w}" height="20" rx="10" class="chip"/>'
                     f'<text x="{cx_ + w / 2}" y="142" text-anchor="middle" class="chipt">{esc(t)}</text>')
        cx_ += w + 8

    grooves = "".join(f'<circle cx="{vx}" cy="{vy}" r="{r}" />' for r in range(36, vr - 2, 5))
    dh, dfs = 16, 13
    py = 238
    pw = bars_w

    def digit(x: float, count: int, cls: str) -> str:
        col = "".join(f'<text x="{x}" y="{py + 16 + k * dh}" class="tm">{k % 10}</text>' for k in range(count + 1))
        return (f'<clipPath id="c{cls}"><rect x="{x - 1}" y="{py + 4}" width="10" height="{dh}"/></clipPath>'
                f'<g clip-path="url(#c{cls})"><g class="{cls}">{col}</g></g>')

    tx0 = rx
    clock = (
        digit(tx0, 4, "dm") + f'<text x="{tx0 + 8}" y="{py + 16}" class="tm">:</text>'
        + digit(tx0 + 15, 6, "dt") + digit(tx0 + 23, 10, "do")
    )

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="card" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#14121f"/><stop offset="1" stop-color="{bg}"/>
    </linearGradient>
    <linearGradient id="art" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/><stop offset=".55" stop-color="{c3}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="barG" gradientUnits="userSpaceOnUse" x1="{rx}" y1="0" x2="{rx + bars_w}" y2="0">
      <stop offset="0" stop-color="{c1}"/><stop offset=".5" stop-color="{c3}"/><stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="reflect"><rect x="{rx}" y="{base}" width="{bars_w}" height="30" fill="url(#fade)"/></mask>
    <radialGradient id="label"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="{c2}"/><stop offset="1" stop-color="{c1}"/></radialGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".18"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="38"/></filter>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="6" dy="8" stdDeviation="8" flood-opacity=".55"/></filter>
    <clipPath id="artClip"><rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" rx="10"/></clipPath>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  </defs>
  <style>
    .b     {{ fill: url(#barG); transform-box: fill-box; transform-origin: bottom;
             animation-timing-function: ease-in-out; animation-iteration-count: infinite; animation-direction: alternate; }}
    {eq_css}
    .vinyl {{ transform-origin: {vx}px {vy}px; animation: spin 2.4s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .grooves circle {{ fill: none; stroke: #2a2a33; stroke-width: 1; }}
    .aura  {{ transform-origin: {ax + asz / 2}px {ay + asz / 2}px; animation: aura .9s ease-in-out infinite alternate; }}
    @keyframes aura {{ from {{ transform: scale(.85); opacity: .45; }} to {{ transform: scale(1.1); opacity: .8; }} }}
    .np    {{ font: 700 11px {SANS}; fill: {c2}; letter-spacing: 3px; }}
    .title {{ font: 800 {title_fs:.1f}px {SANS}; fill: #fff; }}
    .artist {{ font: 500 15px {SANS}; fill: #b8b5c9; }}
    .chip  {{ fill: #fff; fill-opacity: .07; stroke: #fff; stroke-opacity: .15; }}
    .chipt {{ font: 600 11px {SANS}; fill: #d9d6e8; }}
    .mini  {{ fill: {c2}; transform-box: fill-box; transform-origin: bottom; animation: eq1 .8s ease-in-out infinite alternate; }}
    .tm    {{ font: 600 {dfs}px {MONO}; fill: #9d9ab0; }}
    .dm    {{ animation: dm 240s steps(4) infinite; }}
    .dt    {{ animation: dt 60s steps(6) infinite; }}
    .do    {{ animation: do 10s steps(10) infinite; }}
    @keyframes dm {{ to {{ transform: translateY(-{4 * dh}px); }} }}
    @keyframes dt {{ to {{ transform: translateY(-{6 * dh}px); }} }}
    @keyframes do {{ to {{ transform: translateY(-{10 * dh}px); }} }}
    .prog  {{ fill: url(#barG); transform-box: fill-box; transform-origin: left; animation: prog 240s linear infinite; }}
    @keyframes prog {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    .knob  {{ fill: #fff; animation: knob 240s linear infinite; }}
    @keyframes knob {{ to {{ transform: translateX({pw}px); }} }}
    .ctl   {{ fill: #e8e6f3; }}
    .art   {{ animation: hue 12s ease-in-out infinite alternate; }}
    @keyframes hue {{ to {{ transform: translate(-40px, -30px) rotate(25deg); }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#card)"/>
    <circle cx="{ax + asz / 2}" cy="{ay + asz / 2}" r="120" fill="{c1}" filter="url(#blur)" class="aura"/>
    <circle cx="{rx + bars_w * .3}" cy="{base}" r="90" fill="{c3}" opacity=".18" filter="url(#blur)"/>

    <g class="vinyl">
      <circle cx="{vx}" cy="{vy}" r="{vr}" fill="#0b0b0f"/>
      <g class="grooves">{grooves}</g>
      <circle cx="{vx}" cy="{vy}" r="30" fill="url(#label)"/>
      <text x="{vx}" y="{vy + 7}" text-anchor="middle" font-family="{SANS}" font-weight="800" font-size="20" fill="#101018">{initial}</text>
      <circle cx="{vx}" cy="{vy}" r="3" fill="#0b0b0f"/>
    </g>
    <path d="M{vx - vr * .7:.1f} {vy - vr * .7:.1f} A{vr} {vr} 0 0 1 {vx + vr * .7:.1f} {vy - vr * .7:.1f} L{vx} {vy}Z" fill="url(#shine)"/>

    <g filter="url(#shadow)"><rect x="{ax}" y="{ay}" width="{asz}" height="{asz}" rx="10" fill="url(#art)"/></g>
    <g clip-path="url(#artClip)">
      <g class="art">
        <circle cx="{ax + asz * .78}" cy="{ay + asz * .3}" r="{asz * .42:.0f}" fill="#fff" opacity=".13"/>
        <circle cx="{ax + asz * .2}" cy="{ay + asz * .85}" r="{asz * .5:.0f}" fill="#000" opacity=".16"/>
        <circle cx="{ax + asz * .78}" cy="{ay + asz * .3}" r="{asz * .22:.0f}" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="2"/>
      </g>
      <text x="{ax + 16}" y="{ay + asz - 20}" font-family="{SANS}" font-weight="900" font-size="88" fill="#fff" opacity=".9">{initial}</text>
      <text x="{ax + asz - 14}" y="{ay + 24}" text-anchor="end" font-family="{MONO}" font-size="10" fill="#fff" opacity=".8" letter-spacing="2">VOL.{seed % 9 + 1}</text>
    </g>

    <rect x="{rx}" y="40" width="3" height="10" class="mini" style="animation-duration:.6s"/>
    <rect x="{rx + 5}" y="40" width="3" height="10" class="mini" style="animation-duration:.9s"/>
    <rect x="{rx + 10}" y="40" width="3" height="10" class="mini" style="animation-duration:.7s"/>
    <text x="{rx + 22}" y="50" class="np">NOW PLAYING</text>
    <text x="{rx}" y="{84 + title_fs * 0.25:.0f}" class="title">{esc(name)}</text>
    <text x="{rx}" y="114" class="artist">{artist}</text>
    {"".join(chips)}
    <g transform="translate({W - 126} 44)" class="ctl">
      <path d="M0 0 h3 v16 h-3z M18 0 v16 l-14 -8z"/>
      <circle cx="44" cy="8" r="17" fill="#fff"/><path d="M38 0 h4 v16 h-4z M46 0 h4 v16 h-4z" fill="#14121f"/>
      <path d="M70 0 l14 8 l-14 8z M84 0 h3 v16 h-3z"/>
    </g>

    <g id="bars">{"".join(bars)}</g>
    <g mask="url(#reflect)"><use href="#bars" transform="translate(0 {2 * base + 2}) scale(1 -1)"/></g>

    <rect x="{rx}" y="{py - 3}" width="{pw}" height="4" rx="2" fill="#fff" opacity=".12"/>
    <rect x="{rx}" y="{py - 3}" width="{pw}" height="4" rx="2" class="prog"/>
    <circle cx="{rx}" cy="{py - 1}" r="6" class="knob"/>
    {clock}
    <text x="{rx + pw}" y="{py + 16}" text-anchor="end" class="tm">4:00</text>
  </g>
</svg>
"""


# ================================================================ cherry blossoms

# a notched sakura petal, centred on the origin, about 10 x 13 units
PETAL = "M0 6.5 C-5.5 3 -6 -3.5 -2.6 -6.5 L0 -4.6 L2.6 -6.5 C6 -3.5 5.5 3 0 6.5Z"


def _branch(rng: random.Random, x: float, y: float, ang: float, length: float, width: float, depth: int,
            segs: list, tips: list) -> None:
    """Recursive tapered branch; collects (polygon d) segments and blossom spots along it."""
    bend = rng.uniform(-0.25, 0.25)
    x1, y1 = x + math.cos(ang) * length, y + math.sin(ang) * length
    w1 = width * 0.62
    nx, ny = -math.sin(ang), math.cos(ang)
    mx, my = (x + x1) / 2 + nx * length * bend * 0.3, (y + y1) / 2 + ny * length * bend * 0.3
    segs.append(
        f"M{x + nx * width / 2:.1f} {y + ny * width / 2:.1f} "
        f"Q{mx + nx * (width + w1) / 4:.1f} {my + ny * (width + w1) / 4:.1f} {x1 + nx * w1 / 2:.1f} {y1 + ny * w1 / 2:.1f} "
        f"L{x1 - nx * w1 / 2:.1f} {y1 - ny * w1 / 2:.1f} "
        f"Q{mx - nx * (width + w1) / 4:.1f} {my - ny * (width + w1) / 4:.1f} {x - nx * width / 2:.1f} {y - ny * width / 2:.1f}Z"
        f"M{x1 + w1 / 2:.1f} {y1:.1f} a{w1 / 2:.1f} {w1 / 2:.1f} 0 1 0 0 .01Z"
    )
    if depth <= 2:
        for _ in range(rng.randint(1, 3)):
            t = rng.uniform(0.3, 1)
            tips.append((x + (x1 - x) * t + rng.uniform(-6, 6), y + (y1 - y) * t + rng.uniform(-6, 6)))
    if depth == 0:
        tips.append((x1, y1))
        return
    for da in (rng.uniform(-0.7, -0.3), rng.uniform(0.25, 0.6)):
        _branch(rng, x1, y1, ang + da, length * rng.uniform(0.58, 0.75), w1, depth - 1, segs, tips)


def _flower(x: float, y: float, r: float, rot: float, cls: str, delay: float) -> str:
    return (
        f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot:.0f}) scale({r / 7:.2f})">'
        f'<use href="#flower" class="{cls}" style="animation-delay:-{delay:.2f}s"/></g>'
    )


def build_sakura(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Cherry blossoms: branches sway, petals tumble down, and a gust of wind sweeps through now and then."""
    W, H = 900, 280
    rng = random.Random(seed)
    bg, (c1, _c2, c3) = THEMES[theme]
    dusk = {"aurora": "#3a2347", "sunset": "#6b2f45", "ocean": "#1f3560"}.get(theme, "#3a2347")
    serif = "'Noto Serif', 'Hiragino Mincho ProN', Georgia, 'Times New Roman', serif"

    branches = []
    for (bx, by, ang, ln, wd, depth, flip) in [(-14, 10, 0.2, 92, 14, 4, False), (W + 14, -8, 0.32, 78, 11, 3, True)]:
        segs: list[str] = []
        tips: list[tuple[float, float]] = []
        _branch(rng, 0, 0, ang, ln, wd, depth, segs, tips)
        flowers = []
        for (fx, fy) in tips:
            for _ in range(rng.randint(1, 2)):
                flowers.append(_flower(fx + rng.uniform(-9, 9), fy + rng.uniform(-9, 9), rng.uniform(5.5, 9.5),
                                       rng.uniform(0, 72), "fl", rng.uniform(0, 4)))
            if rng.random() < 0.5:
                flowers.append(f'<circle cx="{fx + rng.uniform(-12, 12):.1f}" cy="{fy + rng.uniform(-12, 12):.1f}" '
                               f'r="{rng.uniform(2, 3.4):.1f}" fill="#f06292"/>')
        mirror = " scale(-1 1)" if flip else ""
        branches.append(
            f'<g transform="translate({bx} {by}){mirror}"><g class="sway" style="animation-duration:{rng.uniform(5, 7):.1f}s">'
            f'<path d="{"".join(segs)}" fill="#2b1720"/>{"".join(flowers)}</g></g>'
        )

    def fall_path(x0: float, drift: float, amp: float, waves: float, y0: float = -20, y1: float = H + 20) -> str:
        pts = []
        for k in range(17):
            t = k / 16
            pts.append((x0 + drift * t + amp * math.sin(t * waves * 2 * math.pi), y0 + (y1 - y0) * t))
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    petals = []
    for _ in range(46):
        dur = rng.uniform(9, 17)
        size = rng.uniform(0.55, 1.15)
        path = fall_path(rng.uniform(-60, W), rng.uniform(40, 160), rng.uniform(10, 34), rng.uniform(1, 2.2))
        petals.append(
            f'<g><animateMotion dur="{dur:.1f}s" begin="-{rng.uniform(0, dur):.1f}s" repeatCount="indefinite" path="{path}"/>'
            f'<g transform="scale({size:.2f})"><use href="#pt" class="tumble" '
            f'style="animation-duration:{rng.uniform(2.4, 4.8):.1f}s;animation-delay:-{rng.uniform(0, 4):.1f}s;'
            f'opacity:{rng.uniform(.7, 1):.2f}"/></g></g>'
        )

    # a gust: a ribbon of petals races across the sky for the first part of every cycle
    gust_cycle = 13.0
    gust = []
    for i in range(24):
        y = H * 0.42 + rng.uniform(-45, 45)
        path = (f"M-40 {y:.0f} C{W * .3:.0f} {y - rng.uniform(30, 70):.0f} {W * .6:.0f} {y + rng.uniform(20, 60):.0f} "
                f"{W + 40} {y - rng.uniform(0, 40):.0f}")
        start = 0.05 + rng.uniform(0, 0.08)
        end = start + rng.uniform(0.13, 0.19)
        gust.append(
            f'<g><animateMotion dur="{gust_cycle}s" repeatCount="indefinite" path="{path}" rotate="auto" '
            f'keyPoints="0;0;1;1" keyTimes="0;{start:.3f};{end:.3f};1" calcMode="linear"/>'
            f'<g transform="scale({rng.uniform(.8, 1.3):.2f})"><use href="#pt" class="tumble" '
            f'style="animation-duration:{rng.uniform(.8, 1.4):.1f}s"/></g></g>'
        )

    pile = "".join(
        f'<use href="#pt" opacity="{rng.uniform(.45, .9):.2f}" '
        f'transform="translate({rng.uniform(0, W):.0f} {H - rng.uniform(2, 14):.0f}) rotate({rng.uniform(0, 360):.0f}) '
        f'scale({rng.uniform(.5, .9):.2f} {rng.uniform(.3, .5):.2f})"/>' for _ in range(70)
    )
    bokeh = "".join(
        f'<circle cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(20, H - 40):.0f}" r="{rng.uniform(8, 26):.0f}" class="bokeh" '
        f'style="animation-duration:{rng.uniform(6, 11):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>' for _ in range(14)
    )

    name_fs = min(50, 600 / max(1, len(name)) / 0.55)
    chars = "".join(
        f'<tspan class="ch" style="animation-delay:{0.3 + i * 0.09:.2f}s">{esc(c)}</tspan>' for i, c in enumerate(name)
    )
    sub = esc(lines[0] if lines else "")
    seal_ch = esc(_handle(name)[:1].upper())
    flower_petals = "".join(f'<path d="{PETAL}" transform="rotate({k * 72}) translate(0 -6.2)"/>' for k in range(5))
    tx, ty = W / 2, 138
    seal_x = tx + text_width(name, name_fs) * 0.45 + 16  # serif glyphs are narrower than the estimate

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{bg}"/><stop offset=".65" stop-color="{dusk}"/><stop offset="1" stop-color="#b56a8a"/>
    </linearGradient>
    <radialGradient id="moon"><stop offset="0" stop-color="#fff4f0"/><stop offset=".55" stop-color="#ffe3ea" stop-opacity=".9"/>
      <stop offset="1" stop-color="#ffd1dc" stop-opacity="0"/></radialGradient>
    <radialGradient id="petal" cx="50%" cy="80%" r="80%">
      <stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#ffd3e0"/><stop offset="1" stop-color="#f7a1bf"/>
    </radialGradient>
    <radialGradient id="bloom" cx="50%" cy="100%" r="100%">
      <stop offset="0" stop-color="#ff9fc0"/><stop offset=".45" stop-color="#ffe4ee"/><stop offset="1" stop-color="#fff"/>
    </radialGradient>
    <linearGradient id="nameG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#ffc9da"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-60%" width="140%" height="220%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="soft"><feGaussianBlur stdDeviation="6"/></filter>
    <path id="pt" d="{PETAL}" fill="url(#petal)"/>
    <g id="flower"><g fill="url(#bloom)">{flower_petals}</g><circle r="2.6" fill="#ff7aa8"/><circle r="1.2" fill="#ffe08a"/></g>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .sway   {{ animation: sway ease-in-out infinite alternate; }}
    @keyframes sway {{ from {{ transform: rotate(-1.2deg); }} to {{ transform: rotate(1.6deg); }} }}
    .fl     {{ animation: fl 4s ease-in-out infinite alternate; }}
    @keyframes fl {{ from {{ transform: scale(.92) rotate(-6deg); }} to {{ transform: scale(1.05) rotate(6deg); }} }}
    .tumble {{ animation: tumble linear infinite; }}
    @keyframes tumble {{ 0% {{ transform: rotate(0) scaleX(1); }} 25% {{ transform: rotate(90deg) scaleX(.15); }}
                        50% {{ transform: rotate(180deg) scaleX(-1); }} 75% {{ transform: rotate(270deg) scaleX(-.15); }}
                        100% {{ transform: rotate(360deg) scaleX(1); }} }}
    .bokeh  {{ fill: #ffc0d4; filter: url(#soft); animation: bokeh ease-in-out infinite alternate; }}
    @keyframes bokeh {{ from {{ opacity: .04; transform: translateY(6px); }} to {{ opacity: .2; transform: translateY(-10px); }} }}
    .name   {{ font: 500 {name_fs:.1f}px {serif}; fill: url(#nameG); letter-spacing: 3px; }}
    .ch     {{ animation: bloomIn 1.2s ease-out both; }}
    @keyframes bloomIn {{ from {{ opacity: 0; fill: #ff8fb4; }} }}
    .sub    {{ font: italic 500 15px {serif}; fill: #ffe3ec; letter-spacing: 3px; animation: subIn 2s 1.6s ease-out both; }}
    @keyframes subIn {{ from {{ opacity: 0; letter-spacing: 10px; }} }}
    .seal   {{ animation: subIn 1s 2.2s ease-out both; }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <circle cx="{W - 120}" cy="70" r="70" fill="url(#moon)" opacity=".85"/>
    <circle cx="{W - 120}" cy="70" r="34" fill="#fff6f2" opacity=".9"/>
    {bokeh}
    <path d="M0 {H - 34} Q{W * .25:.0f} {H - 60} {W * .5:.0f} {H - 40} T{W} {H - 46} V{H} H0Z" fill="#2b1726" opacity=".55"/>
    <path d="M0 {H - 16} Q{W * .3:.0f} {H - 34} {W * .62:.0f} {H - 18} T{W} {H - 22} V{H} H0Z" fill="#1d0f19" opacity=".8"/>
    {pile}
    {"".join(branches)}
    <text x="{tx}" y="{ty}" text-anchor="middle" class="name" filter="url(#glow)">{chars}</text>
    <text x="{tx}" y="{ty + 36}" text-anchor="middle" class="sub">{sub}</text>
    <g class="seal" transform="translate({seal_x:.0f} {ty - name_fs * .62:.0f}) rotate(4)">
      <rect width="26" height="26" rx="4" fill="#d6304f" opacity=".9"/>
      <rect x="3" y="3" width="20" height="20" rx="2" fill="none" stroke="#ffe3e8" stroke-width="1.2" opacity=".8"/>
      <text x="13" y="18.5" text-anchor="middle" font-family="{serif}" font-weight="700" font-size="14" fill="#ffe3e8">{seal_ch}</text>
    </g>
    {"".join(petals)}
    {"".join(gust)}
  </g>
</svg>
"""


# ================================================================ seishun (summer youth)

def _cloud(rng: random.Random, x: float, y: float, w: float, h: float, n: int, base: bool = True) -> str:
    """A puffy cumulus made of overlapping shaded circles; (x, y) is the flat bottom-left corner."""
    puffs = []
    for _ in range(n):
        u = rng.random()
        r = rng.uniform(0.18, 0.32) * w * (1 - 0.5 * abs(u - 0.5))
        top = h * (1 - 1.6 * abs(u - 0.5)) * rng.uniform(0.55, 1)
        puffs.append((x + u * w, y - max(r * 0.6, top - r * 0.4), r))
    puffs.sort(key=lambda p: p[1])  # higher puffs first, lower ones overlap them
    body = "".join(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}"/>' for cx, cy, r in puffs)
    # a strip of horizon colour hides the flat bottom of clouds that sit on the horizon
    fade = (f'<rect x="{x - w * 0.05:.0f}" y="{y - 4:.0f}" width="{w * 1.1:.0f}" height="30" fill="url(#cloudBase)"/>'
            if base else "")
    return f'<g fill="url(#puff)">{body}</g>{fade}'


def build_seishun(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Summer youth: towering clouds, a contrail across the sky and a paper plane over a school rooftop."""
    W, H = 900, 290
    rng = random.Random(seed)
    sky, ink, accent = {
        "aurora": (("#1f6fd6", "#62bdf6", "#dff5ff"), "#1b57b0", "#ff7eb3"),
        "sunset": (("#4a6fd0", "#ffad87", "#ffe6b8"), "#c8456b", "#ffcf4d"),
        "ocean": (("#0b57bd", "#36a3f2", "#c3efff"), "#0a468f", "#4dffd2"),
    }.get(theme, (("#1f6fd6", "#62bdf6", "#dff5ff"), "#1b57b0", "#ff7eb3"))
    sun_x, sun_y = W - 150, 46
    horizon = H - 74

    # clouds: a towering cumulus on each side, plus small ones drifting across
    tower = (f'<g class="drift" style="animation-duration:34s">{_cloud(rng, 10, horizon + 10, 215, 160, 22)}</g>'
             f'<g class="drift" style="animation-duration:41s;animation-direction:alternate-reverse">'
             f'{_cloud(rng, W - 270, horizon + 10, 240, 115, 20)}</g>')
    small = []
    for i in range(4):
        dur = rng.uniform(55, 90)
        small.append(
            f'<g class="pass" style="animation-duration:{dur:.0f}s;animation-delay:-{rng.uniform(0, dur):.0f}s">'
            f'{_cloud(rng, W, rng.uniform(40, 120), rng.uniform(70, 130), rng.uniform(20, 36), 7, base=False)}</g>'
        )

    rays = "".join(
        f'<path d="M0 0 L{math.cos(a - 0.05) * 420:.0f} {math.sin(a - 0.05) * 420:.0f} '
        f'L{math.cos(a + 0.05) * 420:.0f} {math.sin(a + 0.05) * 420:.0f}Z"/>'
        for a in (k * 2 * math.pi / 14 for k in range(14))
    )
    flares = "".join(
        f'<circle cx="{sun_x - (sun_x - 260) * t:.0f}" cy="{sun_y + (190 - sun_y) * t:.0f}" r="{r}" '
        f'class="flare" style="animation-delay:-{t * 3:.1f}s" fill="{col}"/>'
        for t, r, col in [(.25, 10, "#fff"), (.45, 22, accent), (.62, 7, "#fff"), (.8, 34, "#bfe6ff"), (1, 14, accent)]
    )

    contrail = f"M-20 150 C{W * .3:.0f} 120 {W * .55:.0f} 70 {W + 30} 34"
    cyc_jet = 16.0
    paper = ("M-30 220 C150 210 300 190 380 150 C440 120 470 66 430 56 C390 46 372 96 412 116 "
             f"C480 150 650 128 {W + 40} 70")
    cyc_pp = 11.0

    fence_top = H - 64
    posts = "".join(f'<rect x="{x}" y="{fence_top - 6}" width="6" height="{H - fence_top + 6}" rx="2"/>'
                    for x in range(18, W, 128))
    sparkles = "".join(
        f'<path d="M0 -7 L1.6 -1.6 L7 0 L1.6 1.6 L0 7 L-1.6 1.6 L-7 0 L-1.6 -1.6Z" class="spark" '
        f'transform="translate({rng.uniform(40, W - 40):.0f} {rng.uniform(20, horizon - 20):.0f}) scale({rng.uniform(.5, 1.1):.2f})" '
        f'style="animation-duration:{rng.uniform(2, 4):.1f}s;animation-delay:-{rng.uniform(0, 4):.1f}s"/>'
        for _ in range(14)
    )
    wind = "".join(
        f'<path d="M0 0 q40 -10 80 0 t80 0" class="wind" transform="translate({rng.uniform(-100, W - 200):.0f} '
        f'{rng.uniform(60, horizon - 10):.0f})" style="animation-duration:{rng.uniform(4, 7):.1f}s;'
        f'animation-delay:-{rng.uniform(0, 6):.1f}s"/>' for _ in range(5)
    )

    name_fs = min(56, 560 / max(1, len(name)) / 0.58)
    sub = esc(lines[0] if lines else "")
    sub_w = text_width(lines[0] if lines else "", 15) * 0.9 + 36
    cx, ty = W / 2 + 10, 130

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{sky[0]}"/><stop offset=".6" stop-color="{sky[1]}"/><stop offset="1" stop-color="{sky[2]}"/>
    </linearGradient>
    <radialGradient id="puff" cx="40%" cy="30%" r="75%">
      <stop offset="0" stop-color="#fff"/><stop offset=".6" stop-color="#f7fbff"/><stop offset="1" stop-color="#bcd4ef"/>
    </radialGradient>
    <linearGradient id="cloudBase" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{sky[2]}" stop-opacity="0"/><stop offset=".3" stop-color="{sky[2]}"/><stop offset="1" stop-color="{sky[2]}"/>
    </linearGradient>
    <radialGradient id="sun">
      <stop offset="0" stop-color="#fff"/><stop offset=".18" stop-color="#fffbe8"/><stop offset=".45" stop-color="#fff3c4" stop-opacity=".45"/>
      <stop offset="1" stop-color="#fff3c4" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="rayFade">
      <stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="leak" cx="85%" cy="5%" r="70%">
      <stop offset="0" stop-color="#fff6d8" stop-opacity=".55"/><stop offset="1" stop-color="#fff6d8" stop-opacity="0"/>
    </radialGradient>
    <pattern id="mesh" width="14" height="14" patternUnits="userSpaceOnUse">
      <path d="M0 7 L7 0 L14 7 L7 14Z" fill="none" stroke="#2e4664" stroke-width="1.3" opacity=".75"/>
    </pattern>
    <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#8fa3b8"/><stop offset="1" stop-color="#5c7189"/>
    </linearGradient>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
  </defs>
  <style>
    .rays   {{ transform-origin: {sun_x}px {sun_y}px; animation: spin 60s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    .flare  {{ opacity: .22; animation: flare 3s ease-in-out infinite alternate; }}
    @keyframes flare {{ to {{ opacity: .06; }} }}
    .drift  {{ animation: drift ease-in-out infinite alternate; }}
    @keyframes drift {{ from {{ transform: translateX(-14px); }} to {{ transform: translateX(16px); }} }}
    .pass   {{ animation: pass linear infinite; }}
    @keyframes pass {{ from {{ transform: translateX(80px); }} to {{ transform: translateX(-{W + 260}px); }} }}
    .trail  {{ fill: none; stroke: #fff; stroke-linecap: round; stroke-dasharray: 100 100; animation: trail {cyc_jet}s linear infinite; }}
    @keyframes trail {{ 0% {{ stroke-dashoffset: 100; opacity: .95; stroke-width: 2; }} 45% {{ stroke-dashoffset: 0; opacity: .9; stroke-width: 2.6; }}
                       90% {{ opacity: 0; stroke-width: 9; stroke-dashoffset: 0; }} 100% {{ opacity: 0; stroke-dashoffset: 0; }} }}
    .ptrail {{ fill: none; stroke: #fff; stroke-width: 1.6; stroke-dasharray: 100 100; animation: ptrail {cyc_pp}s linear infinite; }}
    @keyframes ptrail {{ 0% {{ stroke-dashoffset: 100; opacity: .7; }} 55% {{ stroke-dashoffset: 0; opacity: .6; }}
                        80%, 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
    .spark  {{ fill: #fff; transform-box: fill-box; transform-origin: center; animation: spark ease-in-out infinite; }}
    @keyframes spark {{ 0%, 100% {{ opacity: 0; scale: .3; }} 50% {{ opacity: .95; scale: 1; }} }}
    .wind   {{ fill: none; stroke: #fff; stroke-width: 1.6; stroke-linecap: round; stroke-dasharray: 40 200; animation: wind linear infinite; }}
    @keyframes wind {{ from {{ stroke-dashoffset: 40; opacity: .8; }} to {{ stroke-dashoffset: -170; opacity: 0; }} }}
    .name   {{ font: italic 900 {name_fs:.1f}px {SANS}; letter-spacing: 1px; paint-order: stroke; stroke-linejoin: round;
              transform-box: fill-box; transform-origin: center; animation: pop 1.1s cubic-bezier(.2, 1.6, .4, 1) both; }}
    .front  {{ fill: #fff; stroke: {ink}; stroke-width: 7; }}
    .shadow {{ fill: {accent}; stroke: {accent}; stroke-width: 7; animation-delay: .08s; }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(.4) rotate(-6deg); }} }}
    .ribbon {{ animation: slide .8s .7s cubic-bezier(.2, 1.3, .4, 1) both; }}
    @keyframes slide {{ from {{ opacity: 0; transform: translateX(-40px); }} }}
    .sub    {{ font: 700 15px {SANS}; fill: {ink}; letter-spacing: 1.5px; }}
    .badge  {{ font: 800 15px 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic', sans-serif; fill: #fff; }}
    .bob    {{ animation: bob 3s ease-in-out infinite alternate; }}
    @keyframes bob {{ to {{ transform: translateY(-5px); }} }}
    {reduced(".trail, .ptrail { opacity: 0; }")}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    <g class="rays" fill="url(#rayFade)" opacity=".5"><g transform="translate({sun_x} {sun_y})">{rays}</g></g>
    <circle cx="{sun_x}" cy="{sun_y}" r="120" fill="url(#sun)"/>
    {"".join(small)}
    <path d="{contrail}" pathLength="100" class="trail"/>
    <g><animateMotion dur="{cyc_jet}s" repeatCount="indefinite" path="{contrail}" rotate="auto"
        keyPoints="0;1;1" keyTimes="0;.45;1" calcMode="linear"/>
      <animate attributeName="opacity" dur="{cyc_jet}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;.45" values="1;0"/>
      <path d="M4 0 L-6 -1.4 L-9 -6 L-11 -6 L-9 -1.3 L-14 -1 L-15 -3 L-16.5 -3 L-16 0 L-16.5 3 L-15 3 L-14 1 L-9 1.3 L-11 6 L-9 6 L-6 1.4Z" fill="#fff"/>
    </g>
    {tower}
    {wind}
    {sparkles}
    {flares}
    <rect width="{W}" height="{H}" fill="url(#leak)" class="flare" style="animation-duration:5s"/>

    <path d="{paper}" pathLength="100" class="ptrail"/>
    <g><animateMotion dur="{cyc_pp}s" repeatCount="indefinite" path="{paper}" rotate="auto"
        keyPoints="0;1;1" keyTimes="0;.55;1" calcMode="spline" keySplines=".3 0 .7 1;0 0 1 1"/>
      <path d="M10 0 L-14 -9 L-8 0Z" fill="#fff"/><path d="M10 0 L-14 9 L-8 0Z" fill="#dbe7f5"/>
      <path d="M10 0 L-8 0 L-11 3Z" fill="#b9cbe3"/>
    </g>

    <g>
      <g class="bob"><circle cx="{cx - text_width(name, name_fs) * .5 - 34:.0f}" cy="{ty - name_fs * .35:.0f}" r="25" fill="{accent}"/>
        <text x="{cx - text_width(name, name_fs) * .5 - 34:.0f}" y="{ty - name_fs * .35 - 3:.0f}" text-anchor="middle" class="badge">青</text>
        <text x="{cx - text_width(name, name_fs) * .5 - 34:.0f}" y="{ty - name_fs * .35 + 13:.0f}" text-anchor="middle" class="badge">春</text></g>
      <text x="{cx + 4}" y="{ty + 4}" text-anchor="middle" class="name shadow">{esc(name)}</text>
      <text x="{cx}" y="{ty}" text-anchor="middle" class="name front">{esc(name)}</text>
      <g class="ribbon">
        <rect x="{cx - sub_w / 2:.0f}" y="{ty + 18}" width="{sub_w:.0f}" height="28" rx="14" fill="#fff" opacity=".92"/>
        <text x="{cx}" y="{ty + 37}" text-anchor="middle" class="sub">{sub}</text>
      </g>
    </g>

    <rect y="{fence_top}" width="{W}" height="{H - fence_top}" fill="url(#mesh)"/>
    <rect y="{fence_top - 6}" width="{W}" height="5" rx="2" fill="#2e4664"/>
    <g fill="#2e4664">{posts}</g>
    <rect y="{H - 14}" width="{W}" height="14" fill="url(#floor)"/>
    <rect y="{H - 14}" width="{W}" height="2" fill="#fff" opacity=".4"/>
  </g>
</svg>
"""


STYLES = {
    "terminal": build_terminal,
    "borealis": build_borealis,
    "hologram": build_hologram,
    "circuit": build_circuit,
    "warp": build_warp,
    "equalizer": build_equalizer,
    "sakura": build_sakura,
    "seishun": build_seishun,
}
