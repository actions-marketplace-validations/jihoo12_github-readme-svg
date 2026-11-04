"""Translate Action inputs into CLI arguments without shell interpolation."""

import json
import os
from pathlib import Path
import subprocess
import sys

import generate


def main():
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
    os.chdir(workspace)
    style = os.environ.get("SVG_STYLE", "banner")
    user = os.environ.get("SVG_USER", "")
    styles = ([*generate.STYLES, *(generate.contrib.STYLES if user else [])]
              if style == "all" else [style])
    if any(s not in {**generate.STYLES, **generate.contrib.STYLES} for s in styles):
        raise ValueError(f"Unknown style: {style}")
    out = os.environ.get("SVG_OUT", "")
    if out and style == "all":
        raise ValueError("out cannot be used with style: all; use output-dir")
    if any(s in generate.contrib.STYLES for s in styles) and not user:
        raise ValueError("Contribution styles require the user input")
    args = []
    for key, flag in [("NAME", "name"), ("THEME", "theme"), ("SEED", "seed"),
                      ("USER", "user"), ("PALETTE", "palette"),
                      ("CONTRIB_HTML", "contrib-html")]:
        value = os.environ.get(f"SVG_{key}", "")
        if value:
            args.append(f"--{flag}={value}")
    for key, flag in [("LINES", "line"), ("TAGS", "tag")]:
        for value in os.environ.get(f"SVG_{key}", "").splitlines():
            if value.strip():
                args.append(f"--{flag}={value}")
    files = []
    for selected in styles:
        target = Path(out) if out else Path(os.environ.get("SVG_OUTPUT_DIR") or "assets") / f"{selected}.svg"
        subprocess.run([sys.executable, str(Path(__file__).resolve().with_name("generate.py")),
                        f"--style={selected}", f"--out={target}", *args], check=True)
        files.append(str(target.resolve()))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write(f"files={json.dumps(files)}\n")


if __name__ == "__main__":
    main()
