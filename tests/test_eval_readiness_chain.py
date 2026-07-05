from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.benchmark_scorecard_comparison import build_benchmark_scorecard_comparison
from minigpt.benchmark_scorecard_comparison_artifacts import write_benchmark_scorecard_comparison_outputs
from minigpt.benchmark_scorecard_decision import build_benchmark_scorecard_decision
from minigpt.benchmark_scorecard_decision_artifacts import write_benchmark_scorecard_decision_outputs
from minigpt.maturity_narrative import build_maturity_narrative


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_scorecard(root: Path, name: str, *, rubric: float, overall: float, eval_compare: str) -> Path:
    run_dir = root / "runs" / name
    scorecard_path = run_dir / "benchmark-scorecard" / "benchmark_scorecard.json"
    status = "pass" if rubric >= 80 else "warn"
    write_json(
        scorecard_path,
        {
            "schema_version": 3,
            "title": f"{name} scorecard",
            "generated_at": "2026-05-18T00:00:00Z",
            "run_dir": str(run_dir),
            "summary": {
                "overall_status": "pass" if overall >= 80 else "warn",
                "overall_score": overall,
                "component_count": 6,
                "eval_suite_coverage_status": "pass",
                "eval_suite_comparison_status": eval_compare,
                "rubric_status": status,
                "rubric_avg_score": rubric,
                "rubric_pass_count": 2,
                "rubric_warn_count": 0,
                "rubric_fail_count": 0,
                "weakest_rubric_case": "summary-short",
                "weakest_rubric_score": rubric - 2,
                "generation_quality_total_flags": 3,
                "generation_quality_dominant_flag": "low_diversity",
                "generation_quality_worst_case": "summary-short",
                "generation_quality_worst_case_status": "warn",
            },
            "rubric_scores": {
                "summary": {
                    "case_count": 2,
                    "avg_score": rubric,
                    "overall_status": status,
                    "pass_count": 2,
                    "warn_count": 0,
                    "fail_count": 0,
                    "weakest_case": "summary-short",
                    "weakest_score": rubric - 2,
                },
                "cases": [
                    {
                        "name": "qa-basic",
                        "task_type": "qa",
                        "difficulty": "easy",
                        "status": status,
                        "score": rubric,
                        "missing_terms": [],
                        "failed_checks": [],
                    },
                    {
                        "name": "summary-short",
                        "task_type": "summary",
                        "difficulty": "medium",
                        "status": status,
                        "score": rubric - 2,
                        "missing_terms": [],
                        "failed_checks": [],
                    },
                ],
            },
            "case_scores": [
                {
                    "name": "qa-basic",
                    "task_type": "qa",
                    "difficulty": "easy",
                    "rubric_status": status,
                    "rubric_score": rubric,
                    "rubric_missing_terms": [],
                    "rubric_failed_checks": [],
                },
                {
                    "name": "summary-short",
                    "task_type": "summary",
                    "difficulty": "medium",
                    "rubric_status": status,
                    "rubric_score": rubric - 2,
                    "rubric_missing_terms": [],
                    "rubric_failed_checks": [],
                },
            ],
            "drilldowns": {
                "task_type": [
                    {"group_by": "task_type", "key": "qa", "status": status, "score": rubric, "rubric_score": rubric, "case_count": 1},
                    {
                        "group_by": "task_type",
                        "key": "summary",
                        "status": status,
                        "score": rubric - 2,
                        "rubric_score": rubric - 2,
                        "case_count": 1,
                    },
                ],
                "difficulty": [
                    {"group_by": "difficulty", "key": "easy", "status": status, "score": rubric, "rubric_score": rubric, "case_count": 1},
                    {
                        "group_by": "difficulty",
                        "key": "medium",
                        "status": status,
                        "score": rubric - 2,
                        "rubric_score": rubric - 2,
                        "case_count": 1,
                    },
                ],
            },
        },
    )
    return scorecard_path


def write_maturity_inputs(root: Path, decision_path: Path, scorecard_paths: list[Path]) -> Path:
    write_json(
        root / "runs" / "maturity-summary" / "maturity_summary.json",
        {
            "schema_version": 4,
            "summary": {
                "current_version": 231,
                "overall_status": "pass",
                "average_maturity_level": 4.75,
                "registry_runs": 2,
            },
            "release_readiness_context": {
                "available": True,
                "trend_status": "improved",
                "delta_count": 1,
                "regressed_count": 0,
                "improved_count": 1,
            },
        },
    )
    write_json(root / "runs" / "registry" / "registry.json", {"run_count": 2})
    write_json(root / "runs" / "request-history-summary" / "request_history_summary.json", {"summary": {"status": "pass", "total_log_records": 1}})
    write_json(
        root / "datasets" / "demo" / "v1" / "dataset_card.json",
        {"summary": {"quality_status": "pass", "warning_count": 0}, "quality": {"status": "pass", "warning_count": 0}},
    )
    decision_target = root / "runs" / "candidate" / "benchmark-scorecard-decision" / "benchmark_scorecard_decision.json"
    decision_target.parent.mkdir(parents=True, exist_ok=True)
    decision_target.write_text(decision_path.read_text(encoding="utf-8"), encoding="utf-8")
    for source in scorecard_paths:
        target = root / "runs" / source.parents[1].name / "benchmark-scorecard" / "benchmark_scorecard.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return root


class EvalReadinessChainTests(unittest.TestCase):
    def test_eval_readiness_flows_from_scorecard_comparison_to_maturity_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_scorecard(root, "baseline", rubric=86.0, overall=88.0, eval_compare="pass")
            candidate = make_scorecard(root, "candidate", rubric=90.0, overall=92.0, eval_compare="warn")
            comparison = build_benchmark_scorecard_comparison(
                [baseline, candidate],
                names=["baseline", "candidate"],
                baseline="baseline",
                generated_at="2026-05-18T00:00:00Z",
            )
            comparison_outputs = write_benchmark_scorecard_comparison_outputs(comparison, root / "runs" / "comparison")
            decision = build_benchmark_scorecard_decision(
                comparison_outputs["json"],
                generated_at="2026-05-18T00:00:00Z",
            )
            decision_outputs = write_benchmark_scorecard_decision_outputs(decision, root / "runs" / "decision")
            project = write_maturity_inputs(root / "project", Path(decision_outputs["json"]), [baseline, candidate])

            narrative = build_maturity_narrative(project, generated_at="2026-05-18T00:00:00Z")
            decision_section = next(section for section in narrative["sections"] if section["key"] == "benchmark_promotion")

            self.assertEqual(comparison["summary"]["non_comparison_ready_runs"], ["candidate"])
            self.assertEqual(decision["decision_status"], "review")
            self.assertEqual(decision["summary"]["non_comparison_ready_candidates"], ["candidate"])
            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_run"], "candidate")
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_eval_suite_comparison_status"], "warn")
            self.assertEqual(narrative["summary"]["benchmark_decision_non_comparison_ready_candidates"], ["candidate"])
            self.assertEqual(decision_section["status"], "warn")
            self.assertIn("review-only", narrative["recommendations"][0])


if __name__ == "__main__":
    unittest.main()
