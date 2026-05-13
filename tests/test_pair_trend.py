from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.pair_trend import build_pair_batch_trend_report, load_pair_batch_report, write_pair_batch_trend_outputs


def _sample_report(*, suite: str, generated_equal: bool, delta: int) -> dict:
    return {
        "schema_version": 1,
        "kind": "minigpt_pair_generation_batch",
        "suite": {"name": suite, "version": "1"},
        "left": {"checkpoint_id": "base"},
        "right": {"checkpoint_id": "wide"},
        "case_count": 1,
        "generated_equal_count": 1 if generated_equal else 0,
        "generated_difference_count": 0 if generated_equal else 1,
        "continuation_difference_count": 0 if generated_equal else 1,
        "avg_abs_generated_char_delta": abs(delta),
        "avg_abs_continuation_char_delta": abs(delta),
        "results": [
            {
                "name": "case-one",
                "task_type": "qa",
                "difficulty": "easy",
                "comparison": {
                    "generated_equal": generated_equal,
                    "continuation_equal": generated_equal,
                    "generated_char_delta": delta,
                    "continuation_char_delta": delta,
                    "left_continuation_chars": 4,
                    "right_continuation_chars": 4 + delta,
                },
            }
        ],
    }


class PairTrendTests(unittest.TestCase):
    def test_build_pair_batch_trend_report_detects_case_changes(self) -> None:
        report_a = _sample_report(suite="demo", generated_equal=True, delta=0)
        report_b = _sample_report(suite="demo", generated_equal=False, delta=3)

        trend = build_pair_batch_trend_report([report_a, report_b], names=["baseline", "candidate"])

        self.assertEqual(trend["kind"], "minigpt_pair_batch_trend")
        self.assertEqual(trend["report_count"], 2)
        self.assertEqual(trend["case_count"], 1)
        self.assertEqual(trend["changed_generated_equal_cases"], 1)
        self.assertEqual(trend["max_abs_generated_char_delta"], 3)
        self.assertEqual(trend["reports"][1]["name"], "candidate")
        self.assertEqual(trend["case_trends"][0]["generated_equal_variants"], [False, True])

    def test_load_pair_batch_report_and_name_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pair_generation_batch.json"
            path.write_text(json.dumps(_sample_report(suite="demo", generated_equal=True, delta=0)), encoding="utf-8")

            report = load_pair_batch_report(path)

            self.assertEqual(report["_source_path"], str(path))
            with self.assertRaisesRegex(ValueError, "--name count"):
                build_pair_batch_trend_report([report], names=["one", "two"])

    def test_write_pair_batch_trend_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trend = build_pair_batch_trend_report(
                [
                    _sample_report(suite="demo", generated_equal=True, delta=0),
                    _sample_report(suite="demo", generated_equal=False, delta=-2),
                ],
                names=["a", "b"],
            )

            outputs = write_pair_batch_trend_outputs(trend, tmp)

            self.assertEqual(set(outputs), {"json", "csv", "md", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["kind"], "minigpt_pair_batch_trend")
            self.assertIn("report_name", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT Pair Batch Trend", Path(outputs["md"]).read_text(encoding="utf-8"))
            self.assertIn("Case Trends", Path(outputs["html"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
