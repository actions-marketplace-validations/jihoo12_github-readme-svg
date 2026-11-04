import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class ActionTests(unittest.TestCase):
    def run_action(self, workspace, **inputs):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SVG_")}
        env.update(GITHUB_WORKSPACE=str(workspace), GITHUB_OUTPUT=str(workspace / "outputs"))
        env.update({f"SVG_{k}": v for k, v in inputs.items()})
        return subprocess.run([sys.executable, str(ROOT / "action_runner.py")],
                              cwd=ROOT, env=env, capture_output=True, text=True)

    def test_custom_inputs_in_separate_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            title = 'Hello "world" & <friends> $(touch INJECTED)'
            result = self.run_action(workspace, NAME=title, LINES="--help\nSecond line",
                                     TAGS="Python\n한글", OUT="custom folder/banner.svg")
            self.assertEqual(result.returncode, 0, result.stderr)
            target = workspace / "custom folder/banner.svg"
            self.assertEqual(ET.parse(target).getroot().find("{http://www.w3.org/2000/svg}title").text, title)
            self.assertFalse((workspace / "INJECTED").exists())
            files = json.loads((workspace / "outputs").read_text().split("=", 1)[1])
            self.assertEqual(files, [str(target.resolve())])

    def test_all_styles_with_offline_contributions(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "calendar.html").write_text(''.join(
                f'<td class="ContributionCalendar-day" data-date="2026-01-{day:02}" data-level="{day % 5}"></td>'
                for day in range(1, 29)))
            result = self.run_action(workspace, STYLE="all", USER="example",
                                     CONTRIB_HTML="calendar.html", OUTPUT_DIR="generated")
            self.assertEqual(result.returncode, 0, result.stderr)
            files = json.loads((workspace / "outputs").read_text().split("=", 1)[1])
            self.assertEqual(len(files), 21)
            for file in files:
                self.assertEqual(ET.parse(file).getroot().tag, "{http://www.w3.org/2000/svg}svg")

    def test_invalid_inputs_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            for inputs in ({"STYLE": "unknown"}, {"STYLE": "all", "OUT": "banner.svg"},
                           {"STYLE": "contrib-grid"}):
                with self.subTest(inputs=inputs):
                    self.assertNotEqual(self.run_action(workspace, **inputs).returncode, 0)
                    self.assertFalse((workspace / "outputs").exists())


if __name__ == "__main__":
    unittest.main()
