<p align="center">
  <img src="assets/banner.svg" alt="animated banner" width="100%"/>
</p>

# github-readme-svg

GitHub 프로필/저장소 README에 넣을 **애니메이션 SVG 배너** 생성기입니다.

- 그라디언트가 계속 바뀌는 타이틀
- 여러 문구를 번갈아 타이핑하고 지우는 효과 (커서 포함)
- 반짝이는 별, 떠다니는 원, 흘러가는 물결
- JavaScript 없이 CSS 애니메이션과 SMIL만 써서 GitHub에서 그대로 재생됨
- `prefers-reduced-motion` 설정을 따름

## 사용법 (Nix)

```sh
# 바로 실행
nix run . -- --name "Hi, I'm Jihoo" \
  --line "Welcome to my GitHub!" \
  --line "I love building cool stuff" \
  --theme aurora \
  --out assets/banner.svg

# 개발 셸 (python3 + rsvg-convert)
nix develop
python3 generate.py --help
```

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--name` | 큰 타이틀 | `Hi, I'm Jihoo` |
| `--line` | 타이핑될 문구 (여러 번 지정 가능) | 예시 문구 3개 |
| `--theme` | `aurora` · `sunset` · `ocean` | `aurora` |
| `--seed` | 별 배치 랜덤 시드 | `42` |
| `--out` | 출력 경로 | `assets/banner.svg` |

## README에 넣기

생성한 SVG를 저장소에 커밋한 뒤 README에 다음을 넣으세요.

```html
<p align="center">
  <img src="assets/banner.svg" alt="banner" width="100%"/>
</p>
```

> `--line` 문구는 고정폭 글꼴 기준으로 폭을 추정합니다. 영문이 가장 정확하고, 한글도 대략 맞습니다.
