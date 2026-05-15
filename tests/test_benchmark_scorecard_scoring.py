from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import benchmark_scorecard_scoring


class BenchmarkScorecardScoringSplitTests(unittest.TestCase):
    def test_scoring_module_builds_cases_rubric_and_drilldowns(self) -> None:
        eval_suite = {
            "results": [
                {
                    "name": "qa-basic",
                    "task_type": "qa",
                    "difficulty": "easy",
                    "prompt": "Explain training.",
                    "generated": "model training improves learning",
                    "continuation": "model training improves learning",
                    "expected_behavior": "Mention model training.",
                    "rubric": {"must_include": ["model", "training"], "min_chars": 8},
                    "char_count": 32,
                    "unique_char_count": 18,
                },
                {
                    "name": "format-json",
                    "task_type": "format",
                    "difficulty": "medium",
                    "prompt": "Return JSON.",
                    "generated": '{"run":"demo","loss":1}',
                    "continuation": '{"run":"demo","loss":1}',
                    "expected_behavior": "Return fields run and loss.",
                    "rubric": {"must_include": ["run", "loss"], "min_chars": 4},
                    "char_count": 23,
                    "unique_char_count": 12,
                },
            ]
        }
        generation_quality = {
            "cases": [
                {"name": "qa-basic", "status": "pass", "unique_ratio": 0.8, "flag_count": 0},
                {"name": "format-json", "status": "warn", "unique_ratio": 0.7, "flag_count": 1},
            ]
        }
        pair_batch = {
            "results": [
                {"name": "qa-basic", "task_type": "qa", "difficulty": "easy", "comparison": {"generated_equal": True, "continuation_equal": True, "generated_char_delta": 0, "continuation_char_delta": 0}},
                {"name": "format-json", "task_type": "format", "difficulty": "medium", "comparison": {"generated_equal": False, "continuation_equal": False, "generated_char_delta": 2, "continuation_char_delta": 2}},
            ]
        }

        cases = benchmark_scorecard_scoring.case_scores(eval_suite, generation_quality, pair_batch)
        rubric = benchmark_scorecard_scoring.rubric_scores(cases)
        scored_cases = benchmark_scorecard_scoring.case_scores_with_rubric(cases, rubric)
        drilldowns = benchmark_scorecard_scoring.benchmark_drilldowns(scored_cases)

        self.assertEqual([case["name"] for case in cases], ["format-json", "qa-basic"])
        self.assertEqual(rubric["summary"]["case_count"], 2)
        self.assertEqual(rubric["summary"]["overall_status"], "pass")
        self.assertTrue(all("rubric_score" in case for case in scored_cases))
        self.assertEqual({row["group_by"] for row in drilldowns["task_type"]}, {"task_type"})
        self.assertEqual({row["key"] for row in drilldowns["task_type"]}, {"format", "qa"})
        self.assertEqual(drilldowns["weakest_difficulty"]["key"], "medium")

    def test_rubric_case_score_reports_missing_and_forbidden_terms(self) -> None:
        case = {
            "name": "fact-check",
            "task_type": "qa",
            "difficulty": "hard",
            "generated": "validation loss is always better",
            "continuation": "validation loss is always better",
            "expected_behavior": "Reject the false premise and mention not worse.",
            "rubric": {"must_include": ["not", "worse"], "must_avoid": ["always better"], "min_chars": 8},
            "eval_char_count": 32,
        }

        score = benchmark_scorecard_scoring.rubric_case_score(case)

        self.assertEqual(score["status"], "warn")
        self.assertEqual(score["missing_terms"], ["not", "worse"])
        self.assertIn("must_avoid", score["failed_checks"])
        self.assertIn("must_include", score["failed_checks"])


if __name__ == "__main__":
    unittest.main()
