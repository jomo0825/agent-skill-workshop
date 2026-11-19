"""驗證排程的可觀察行為，執行：python -m unittest discover -s tests -v"""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/weekly-assistant/scripts/planner.py"
spec = importlib.util.spec_from_file_location("planner", SCRIPT)
planner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(planner)


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "data/demo.json").read_text(encoding="utf-8"))

    def test_demo_expected_results(self):
        plan = planner.build_plan(self.data, "2026-11-23")
        self.assertEqual(plan["summary"], {"events": 5, "conflicts": 1, "scheduled": 4, "unscheduled": 2})
        self.assertEqual(plan["conflicts"][0]["titles"], ["產學專班上課", "牙齒定期檢查"])
        self.assertEqual(plan["scheduled"][0]["start"], "2026-11-23T13:00:00+08:00")

    def test_tasks_never_overlap_or_miss_deadlines(self):
        plan = planner.build_plan(self.data, "2026-11-23")
        for task in plan["scheduled"]:
            a, b = planner.parse_dt(task["start"]), planner.parse_dt(task["end"])
            self.assertLessEqual(b, planner.parse_dt(task["due"]))
            self.assertEqual((b - a).total_seconds(), task["minutes"] * 60)
            for other in plan["events"] + plan["scheduled"]:
                if other is task:
                    continue
                c, d = planner.parse_dt(other["start"]), planner.parse_dt(other["end"])
                self.assertFalse(a < d and c < b)

    def test_adjacent_events_are_not_conflicts(self):
        self.data["events"][1]["start"] = "2026-11-23T12:00:00+08:00"
        self.data["events"][1]["end"] = "2026-11-23T13:00:00+08:00"
        self.assertEqual(planner.build_plan(self.data, "2026-11-23")["conflicts"], [])

    def test_cross_week_event_blocks_monday(self):
        self.data["events"] = [{"id": "e", "title": "跨週旅行", "start": "2026-11-22T12:00:00+08:00", "end": "2026-11-24T00:00:00+08:00"}]
        plan = planner.build_plan(self.data, "2026-11-23")
        self.assertTrue(all(t["start"][:10] != "2026-11-23" for t in plan["scheduled"]))

    def test_rejects_invalid_inputs(self):
        cases = [("minutes", 0), ("minutes", True), ("priority", "urgent"), ("due", "2026-11-24T18:00:00")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["tasks"][0][field] = value
                with self.assertRaises(ValueError):
                    planner.build_plan(data, "2026-11-23")

    def test_rejects_overlapping_windows_and_duplicate_ids(self):
        self.data["preferences"]["windows"] = [["09:00", "12:00"], ["11:00", "13:00"]]
        with self.assertRaises(ValueError):
            planner.build_plan(self.data, "2026-11-23")
        self.setUp()
        self.data["tasks"][1]["id"] = self.data["tasks"][0]["id"]
        with self.assertRaises(ValueError):
            planner.build_plan(self.data, "2026-11-23")

    def test_offsets_are_normalized(self):
        self.data["events"][0]["start"] = "2026-11-23T01:00:00+00:00"
        plan = planner.build_plan(self.data, "2026-11-23")
        self.assertEqual(plan["events"][0]["start"], "2026-11-23T09:00:00+08:00")

    def test_empty_week_and_monday_validation(self):
        self.data["events"], self.data["tasks"] = [], []
        self.assertEqual(planner.build_plan(self.data, "2026-11-23")["scheduled"], [])
        with self.assertRaises(ValueError):
            planner.build_plan(self.data, "2026-11-24")

    def test_html_escapes_titles_and_embeds_asset(self):
        self.data["person"] = '<script>alert("x")</script>'
        plan = planner.build_plan(self.data, "2026-11-23")
        page = planner.render_html(plan, ROOT / ".agents/skills/weekly-assistant/assets/banner.png")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("data:image/png;base64,", page)

    def test_second_week_reuses_code(self):
        data = json.loads((ROOT / "data/second-week.json").read_text(encoding="utf-8"))
        self.assertEqual(planner.build_plan(data, "2026-11-30")["summary"],
                         {"events": 2, "conflicts": 0, "scheduled": 2, "unscheduled": 0})


if __name__ == "__main__":
    unittest.main()
