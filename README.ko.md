<p align="center">
  <img src="assets/synthwave.svg" alt="synthwave banner" width="100%"/>
</p>

# github-readme-svg

[English](README.md) | **한국어**

GitHub 프로필/저장소 README에 넣을 **애니메이션 SVG 배너** 생성기입니다.
JavaScript 없이 CSS 애니메이션과 SMIL만 써서 GitHub에서 그대로 재생됩니다.
모든 스타일이 `prefers-reduced-motion` 설정을 따릅니다.

## 스타일

### `synthwave`
네온 타이틀이 선으로 그려진 뒤 빛나며 깜빡이고, 레트로 줄무늬 태양과 다가오는 원근 그리드가 배경에 깔립니다.

<img src="assets/synthwave.svg" width="100%"/>

### `matrix`
깊이감 있는 코드 비, RGB가 갈라지는 글리치 타이틀, 타이핑 효과 부제목.

<img src="assets/matrix.svg" width="100%"/>

### `orbit`
기술 스택 태그가 이름 주위를 3D 궤도로 돌고, 뒤로 갈수록 작고 흐려집니다. 가운데에는 맥동하는 코어가 있습니다.

<img src="assets/orbit.svg" width="100%"/>

### `banner`
그라디언트 타이틀, 여러 문구를 번갈아 타이핑하고 지우는 효과, 반짝이는 별, 떠다니는 원, 흘러가는 물결.

<img src="assets/banner.svg" width="100%"/>

## 사용법 (Nix)

```sh
# 모든 스타일을 assets/에 생성
nix run . -- --style all --name "Hi, I'm Jihoo"

# 스타일 하나만
nix run . -- --style orbit --name "Jihoo" \
  --line "Full-stack tinkerer" \
  --tag Python --tag Nix --tag Rust --tag Linux

nix run . -- --style matrix \
  --line "Welcome to my GitHub!" --line "I love building cool stuff"

# 개발 셸 (python3 + rsvg-convert)
nix develop
python3 generate.py --help
```

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--style` | `banner` · `synthwave` · `matrix` · `orbit` · `all` | `banner` |
| `--name` | 큰 타이틀 | `Hi, I'm Jihoo` |
| `--line` | 부제목 문구, 여러 번 지정 가능 (`banner`/`matrix`는 모두 타이핑, `synthwave`/`orbit`은 첫 줄만 사용) | 예시 문구 3개 |
| `--tag` | `orbit` 스타일에서 궤도를 도는 태그, 여러 번 지정 가능 | Python, Nix, Linux, … |
| `--theme` | `aurora` · `sunset` · `ocean` (`banner`, `orbit`) | `aurora` |
| `--seed` | 별/코드 비 배치용 랜덤 시드 | `42` |
| `--out` | 출력 경로 (스타일 하나일 때만) | `assets/<style>.svg` |

## README에 넣기

생성한 SVG를 저장소에 커밋한 뒤 README에 다음을 넣으세요.

```html
<p align="center">
  <img src="assets/synthwave.svg" alt="banner" width="100%"/>
</p>
```

> `--line`, `--tag` 문구 폭은 글꼴 크기로 추정합니다. 영문이 가장 정확하고, 한글 등 전각 문자는 대략 맞습니다.
