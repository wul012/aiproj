from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard_comparison_deltas import (
    build_benchmark_scorecard_case_deltas,
    build_benchmark_scorecard_group_deltas,
    build_benchmark_scorecard_recommendations,
    build_benchmark_scorecard_run_delta,
    build_benchmark_scorecard_summary,
    select_best_benchmark_scorecard_run,
    summarize_benchmark_scorecard_run,
)


def make_scorecard(name: str, *, overall: float, qa_score: float, flags: int, missing: list[str]) -> dict:
    status = "pass" if qa_score >= 80 else "warn"
    return {
        "_source_path": f"runs/{name}/benchmark-scorecard/benchmark_scorecard.json",
        "run_dir": f"runs/{name}",
        "generated_at": "2026-05-16T00:00:00Z",
        "summary": {
            "overall_status": "pass" if overall >= 80 else "warn",
            "overall_score": overall,
            "component_count": 6,
            "rubric_status": status,
            "rubric_avg_score": qa_score,
            "rubric_pass_count": 1 if status == "pass" else 0,
            "rubric_warn_count": 1 if status == "warn" else 0,
            "rubric_fail_count": 0,
            "weakest_rubric_case": "qa-basic",
            "weakest_rubric_score": qa_score,
            "generation_quality_total_flags": flags,
            "generation_quality_dominant_flag": "low_diversity" if flags <= 2 else "empty_continuation",
            "generation_quality_worst_case": "qa-basic",
            "weakest_task_type": "qa",
            "weakest_task_type_score": qa_score,
            "weakest_difficulty": "hard",
            "weakest_difficulty_score": qa_score,
        },
        "case_scores": [
            {
                "name": "qa-basic",
                "task_type": "qa",
                "difficulty": "hard",
                "rubric_status": status,
                "rubric_score": qa_score,
                "rubric_missing_terms": missing,
                "rubric_failed_checks": ["must_include"] if missing else [],
            }
        ],
        "drilldowns": {
            "task_type": [{"key": "qa", "score": qa_score, "rubric_score": qa_score, "case_count": 1, "cases": ["qa-basic"]}],
            "difficulty": [{"key": "hard", "score": qa_score, "rubric_score": qa_score, "case_count": 1, "cases": ["qa-basic"]}],
        },
    }


class BenchmarkScorecardComparisonDeltaTests(unittest.TestCase):
    def test_delta_module_builds_summary_recommendations_and_best_run(self) -> None:
        scorecards = [
            make_scorecard("base", overall=88, qa_score=86, flags=2, missing=[]),
            make_scorecard("candidate", overall=82, qa_score=62, flags=5, missing=["fact"]),
        ]
        names = ["base", "candidate"]
        runs = [summarize_benchmark_scorecard_run(scorecard, names[index], index) for index, scorecard in enumerate(scorecards)]
        baseline = runs[0]

        deltas = [build_benchmark_scorecard_run_delta(run, baseline) for run in runs]
        case_deltas = build_benchmark_scorecard_case_deltas(scorecards, names, baseline)
        task_deltas = build_benchmark_scorecard_group_deltas(scorecards, names, baseline, group_name="task_type")
        difficulty_deltas = build_benchmark_scorecard_group_deltas(scorecards, names, baseline, group_name="difficulty")
        summary = build_benchmark_scorecard_summary(runs, baseline, deltas, case_deltas, task_deltas, difficulty_deltas)
        recommendations = build_benchmark_scorecard_recommendations(summary, deltas, case_deltas, task_deltas, difficulty_deltas)

        candidate_delta = next(row for row in deltas if row["name"] == "candidate")
        qa_delta = next(row for row in case_deltas if row["run_name"] == "candidate" and row["case"] == "qa-basic")
        qa_group = next(row for row in task_deltas if row["run_name"] == "candidate" and row["key"] == "qa")

        self.assertEqual(candidate_delta["rubric_relation"], "regressed")
        self.assertEqual(candidate_delta["generation_quality_flag_relation"], "regressed")
        self.assertTrue(candidate_delta["generation_quality_dominant_flag_changed"])
        self.assertEqual(qa_delta["added_missing_terms"], ["fact"])
        self.assertEqual(qa_delta["relation"], "regressed")
        self.assertEqual(qa_group["relation"], "regressed")
        self.assertEqual(summary["regressed_rubric_count"], 1)
        self.assertEqual(summary["case_regression_count"], 1)
        self.assertEqual(summary["worst_generation_quality_flag_regression_run"], "candidate")
        self.assertEqual(select_best_benchmark_scorecard_run(runs, "rubric_avg_score")["name"], "base")
        self.assertTrue(any("Generation-quality flags increased" in item for item in recommendations))
        self.assertTrue(any("missing terms" in item.lower() for item in recommendations))


if __name__ == "__main__":
    unittest.main()
