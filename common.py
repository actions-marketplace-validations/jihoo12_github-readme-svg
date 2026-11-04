"""Helpers shared by the banner styles."""

from __future__ import annotations

import html
import random

SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

# (background, [accent1, accent2, accent3])
THEMES = {
    "aurora": ("#0d1117", ["#7f5af0", "#2cb67d", "#3da9fc"]),
    "sunset": ("#1a1023", ["#ff6b6b", "#feca57", "#ff9ff3"]),
    "ocean": ("#03122b", ["#00d2ff", "#3a7bd5", "#48dbfb"]),
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def text_width(s: str, font_size: float = 22) -> float:
    # monospace estimate; count wide characters (Hangul, emoji, ...) as roughly two cells
    return sum(font_size * 0.6 * (2 if ord(c) > 0x1100 else 1) for c in s)


def stars(n: int, rng: random.Random, w: float, h: float) -> str:
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.6, 1.8)
        dur, delay = rng.uniform(2, 5), rng.uniform(0, 5)
        out.append(
            f'<circle class="star" cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>'
        )
    return "\n    ".join(out)


def key_times(times: list[float], total: float) -> str:
    """Normalise absolute times to a strictly increasing SMIL keyTimes list from 0 to 1."""
    out, last = [], -1.0
    for t in times:
        k = min(max(t / total, 0.0), 1.0)
        if k <= last:
            k = last + 1e-5
        out.append(k)
        last = k
    out[0], out[-1] = 0.0, 1.0
    return ";".join(f"{k:.5f}" for k in out)
