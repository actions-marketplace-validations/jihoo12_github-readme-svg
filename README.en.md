<p align="center">
  <img src="assets/banner.svg" alt="animated banner" width="100%"/>
</p>

# github-readme-svg

**English** | [한국어](README.md)

A generator for **animated SVG banners** to put in your GitHub profile or repository README.

- Title with a continuously shifting gradient
- Typewriter effect that types and erases multiple lines in turn (with a cursor)
- Twinkling stars, floating orbs and flowing waves
- No JavaScript: uses only CSS animations and SMIL, so it plays as-is on GitHub
- Respects `prefers-reduced-motion`

## Usage (Nix)

```sh
# Run directly
nix run . -- --name "Hi, I'm Jihoo" \
  --line "Welcome to my GitHub!" \
  --line "I love building cool stuff" \
  --theme aurora \
  --out assets/banner.svg

# Dev shell (python3 + rsvg-convert)
nix develop
python3 generate.py --help
```

| Option | Description | Default |
|---|---|---|
| `--name` | Large title | `Hi, I'm Jihoo` |
| `--line` | Line to type (can be given multiple times) | 3 sample lines |
| `--theme` | `aurora` · `sunset` · `ocean` | `aurora` |
| `--seed` | Random seed for star placement | `42` |
| `--out` | Output path | `assets/banner.svg` |

## Adding it to your README

Commit the generated SVG to your repository, then add this to your README:

```html
<p align="center">
  <img src="assets/banner.svg" alt="banner" width="100%"/>
</p>
```

> Text width for `--line` is estimated assuming a monospace font. It is most accurate for English text; Korean (and other wide characters) is approximate.
