#!/usr/bin/env python3
"""GitHub README용 애니메이션 SVG 배너 생성기.

외부 의존성 없이 표준 라이브러리만 사용합니다.
GitHub는 README의 SVG를 <img>로 렌더링하므로 JavaScript는 동작하지 않지만,
CSS 애니메이션과 SMIL(<animate>)은 동작합니다. 이 스크립트는 그 두 가지만 사용합니다.

예시:
    python3 generate.py --name "Jihoo" \
        --line "Hello, World! 👋" --line "I build things with Nix & Python" \
        --out banner.svg
"""

from __future__ import annotations

import argparse
import html
import random
from pathlib import Path

WIDTH = 900
HEIGHT = 260
FONT_SIZE = 22
CHAR_W = FONT_SIZE * 0.6  # monospace 글자 폭 근사치

THEMES = {
    "aurora": ("#0d1117", ["#7f5af0", "#2cb67d", "#3da9fc"]),
    "sunset": ("#1a1023", ["#ff6b6b", "#feca57", "#ff9ff3"]),
    "ocean": ("#03122b", ["#00d2ff", "#3a7bd5", "#48dbfb"]),
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def text_width(s: str) -> float:
    # 한글/이모지 등 전각 문자는 대략 2칸으로 계산
    return sum(CHAR_W * (2 if ord(c) > 0x1100 else 1) for c in s)


def stars(n: int, rng: random.Random) -> str:
    out = []
    for i in range(n):
        x, y = rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT * 0.75)
        r = rng.uniform(0.6, 1.8)
        dur, delay = rng.uniform(2, 5), rng.uniform(0, 5)
        out.append(
            f'<circle class="star" cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" '
            f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>'
        )
    return "\n    ".join(out)


def wave_path(amp: float, base: float, wavelength: float) -> str:
    # 화면 폭의 2배 길이 파형 → translateX(-50%)로 끊김 없이 반복
    d = [f"M0 {base}"]
    x = 0.0
    while x < WIDTH * 2:
        d.append(f"q {wavelength / 4} {-amp} {wavelength / 2} 0 t {wavelength / 2} 0")
        x += wavelength
    d.append(f"V {HEIGHT} H 0 Z")
    return " ".join(d)


def typing_lines(lines: list[str], y: float, type_speed: float, hold: float) -> tuple[str, float]:
    """SMIL로 여러 줄을 '타이핑 → 잠시 멈춤 → 지우기' 순서로 반복."""
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

        # (시간, 폭) 키프레임: 타이핑 → 유지 → 지우기 → 숨김
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

        # keyTimes는 단조 증가 + 0으로 시작 + 1로 끝나야 함
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
        # discrete 모드에서는 각 값이 다음 keyTime까지 유지되므로,
        # 지우기가 끝나는 프레임(폭 0)에서 바로 숨겨야 커서가 남지 않음
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


def build(name: str, lines: list[str], theme: str, seed: int) -> str:
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


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="Hi, I'm Jihoo")
    p.add_argument("--line", action="append", dest="lines",
                   help="타이핑될 문구 (여러 번 지정 가능)")
    p.add_argument("--theme", choices=THEMES, default="aurora")
    p.add_argument("--seed", type=int, default=42, help="별 배치용 랜덤 시드")
    p.add_argument("--out", default="assets/banner.svg")
    a = p.parse_args()

    lines = a.lines or ["Welcome to my GitHub!", "I love building cool stuff", "Let's code together :)"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(a.name, lines, a.theme, a.seed), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
