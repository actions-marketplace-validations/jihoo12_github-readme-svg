<p align="center">
  <img src="assets/synthwave.svg" alt="synthwave banner" width="100%"/>
</p>

# github-readme-svg

**English** | [한국어](README.ko.md)

A generator for **animated SVG banners** to put in your GitHub profile or repository README.
No JavaScript: it uses only CSS animations and SMIL, so the banners play as-is on GitHub.
All styles respect `prefers-reduced-motion`.

## Styles

### `synthwave`
A neon title that draws its own outline, then lights up and flickers. Behind it are a retro striped sun and a perspective grid that scrolls toward you.

<img src="assets/synthwave.svg" width="100%"/>

### `matrix`
Falling code rain at several depths, a title with RGB-split glitches, and a typewriter subtitle.

<img src="assets/matrix.svg" width="100%"/>

### `orbit`
Your tech stack orbits your name in 3D-style ellipses, with tags shrinking and dimming as they pass behind. A pulsing core sits in the centre.

<img src="assets/orbit.svg" width="100%"/>

### `banner`
A gradient title, a typewriter effect that types and erases several lines in turn, twinkling stars, floating orbs and flowing waves.

<img src="assets/banner.svg" width="100%"/>

## Usage (Nix)

```sh
# Generate every style into assets/
nix run . -- --style all --name "Hi, I'm Jihoo"

# A single style
nix run . -- --style orbit --name "Jihoo" \
  --line "Full-stack tinkerer" \
  --tag Python --tag Nix --tag Rust --tag Linux

nix run . -- --style matrix \
  --line "Welcome to my GitHub!" --line "I love building cool stuff"

# Dev shell (python3 + rsvg-convert)
nix develop
python3 generate.py --help
```

| Option | Description | Default |
|---|---|---|
| `--style` | `banner` · `synthwave` · `matrix` · `orbit` · `all` | `banner` |
| `--name` | Large title | `Hi, I'm Jihoo` |
| `--line` | Subtitle lines, repeatable (`banner`/`matrix` type all of them; `synthwave`/`orbit` use the first) | 3 sample lines |
| `--tag` | Tags orbiting in the `orbit` style, repeatable | Python, Nix, Linux, … |
| `--theme` | `aurora` · `sunset` · `ocean` (`banner`, `orbit`) | `aurora` |
| `--seed` | Random seed for stars / code rain | `42` |
| `--out` | Output path (single style only) | `assets/<style>.svg` |

## Adding it to your README

Commit the generated SVG to your repository, then add this to your README:

```html
<p align="center">
  <img src="assets/synthwave.svg" alt="banner" width="100%"/>
</p>
```

> Text width for `--line` and `--tag` is estimated from the font size. It is most accurate for English text; Korean and other wide characters are approximate.
