"""從實際成果檢查規則、資料一致性與可重用性。"""

import copy
import contextlib
import io
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/slide-master/scripts"
sys.path.insert(0, str(SCRIPTS))
from build_deck import build, main, statistics, validate, SKILL_DIR
from inspect_deck import inspect
from pptx import Presentation


class SlideMasterTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "data/sensor-demo.json").read_text(encoding="utf-8"))
        self.hero = SKILL_DIR / "assets/sensor-hero.png"

    def test_known_statistics(self):
        stats = statistics(self.data["samples"])
        self.assertAlmostEqual(stats["mae"], 0.3)
        self.assertAlmostEqual(stats["max_error"], 0.5)
        self.assertEqual(stats["sample_count"], 6)

    def test_real_deck_is_editable_and_matches_input(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(self.data, output, self.hero)
            report = inspect(output / "slides.pptx", self.data)
            self.assertTrue(report["ok"], report["issues"])
            self.assertEqual(report["native_charts"], 1)
            self.assertEqual(report["native_tables"], 1)
            prs = Presentation(output / "slides.pptx")
            self.assertEqual(len(prs.slides), 6)
            self.assertGreater(sum(s.has_text_frame for slide in prs.slides for s in slide.shapes), 20)

    def test_second_input_changes_data_title_and_theme(self):
        data = json.loads((ROOT / "data/sensor-updated.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            result = build(data, output, self.hero)
            self.assertAlmostEqual(result["statistics"]["mae"], 0.15)
            self.assertEqual(result["accent"], "5A4D9D")
            self.assertTrue(inspect(output / "slides.pptx", data)["ok"])

    def test_rejects_unsafe_or_unrenderable_input(self):
        for value in [True, float("nan"), float("inf"), "20"]:
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data["samples"][0]["measured"] = value
                with self.assertRaises(ValueError):
                    validate(data)
        for field, value in [("title", "標" * 29), ("architecture", ["只有一個"]),
                             ("theme", {"accent": "red"})]:
            data = copy.deepcopy(self.data)
            data[field] = value
            with self.assertRaises(ValueError):
                validate(data)

    def test_duplicate_labels_rejected_and_zero_accepted(self):
        self.data["samples"][0]["reference"] = 0
        validate(self.data)
        self.data["samples"][1]["label"] = self.data["samples"][0]["label"]
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_missing_asset_fails_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            with self.assertRaises(ValueError):
                build(self.data, output, output / "missing.png")
            self.assertFalse(output.exists())

    def test_inspector_detects_changed_source_data(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(self.data, output, self.hero)
            self.data["samples"][0]["measured"] += 1
            self.assertFalse(inspect(output / "slides.pptx", self.data)["ok"])

    def test_maximum_sample_count(self):
        self.data["samples"] = [{"label": f"P{i}", "reference": i, "measured": i + 0.1} for i in range(12)]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(self.data, output, self.hero)
            self.assertTrue(inspect(output / "slides.pptx", self.data)["ok"])

    def test_cli_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "build_deck.py"),
                                     "--input", str(ROOT / "data/sensor-demo.json"), "--out", str(output)],
                                    cwd=directory, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "slides.pptx").is_file())

    def test_bad_json_returns_nonzero_without_success(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            source.write_text("{}", encoding="utf-8")
            output = Path(directory) / "result"
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--input", str(source), "--out", str(output)]), 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
