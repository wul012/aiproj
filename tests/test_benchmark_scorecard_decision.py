from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import benchmark_scorecard_decision  # noqa: E402
from minigpt import benchmark_scorecard_decision_artifacts  # noqa: E402
from minigpt.benchmark_scorecard_decision import (  # noqa: E402
    build_benchmark_scorecard_decision,
    load_benchmark_scorecard_comparison,
    render_benchmark_scorecard_decision_html,
    render_benchmark_scorecard_decision_markdown,
    write_benchmark_scorecard_decision_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_comparison(root: Path, *, clean_candidate: bool = False) -> Path:
    comparison_path = root / "comparison" / "benchmark_scorecard_comparison.json"
    candidate_flag_delta = -2 if clean_candidate else 3
    candidate_flag_relation = "improved" if clean_candidate else "regressed"
    candidate_case_relation = "improved" if clean_candidate else "regressed"
    candidate_case_delta = 4 if clean_candidate else -8
    payload = {
        "schema_version": 1,
        "title": "Demo <scorecard comparison>",
        "generated_at": "2026-05-16T00:00:00Z",
        "scorecard_count": 2,
        "baseline": {"name": "baseline"},
        "runs": [
            {
                "name": "baseline",
                "source_path": "baseline/benchmark_scorecard.json",
                "run_dir": "baseline",
                "overall_score": 88,
                "rubric_avg_score": 86,
                "generation_quality_total_flags": 5,
                "generation_quality_dominant_flag": "low_diversity",
                "generation_quality_worst_case": "summary-short",
            },
            {
                "name": "candidate",
                "source_path": "candidate/benchmark_scorecard.json",
                "run_dir": "candidate",
                "overall_score": 90 if clean_candidate else 86,
                "rubric_avg_score": 89 if clean_candidate else 84,
                "generation_quality_total_flags": 3 if clean_candidate else 8,
                "generation_quality_dominant_flag": "low_diversity" if clean_candidate else "empty_continuation",
                "generation_quality_worst_case": "summary-short" if clean_candidate else "qa-basic",
            },
        ],
        "baseline_deltas": [
            {
                "name": "baseline",
                "baseline_name": "baseline",
                "is_baseline": True,
                "overall_score_delta": 0,
                "rubric_avg_score_delta": 0,
                "generation_quality_total_flags_delta": 0,
                "generation_quality_flag_relation": "baseline",
                "overall_relation": "baseline",
                "rubric_relation": "baseline",
            },
            {
                "name": "candidate",
                "baseline_name": "baseline",
                "is_baseline": False,
                "overall_score_delta": 2 if clean_candidate else -2,
                "rubric_avg_score_delta": 3 if clean_candidate else -2,
                "generation_quality_total_flags_delta": candidate_flag_delta,
                "generation_quality_flag_relation": candidate_flag_relation,
                "generation_quality_dominant_flag_changed": not clean_candidate,
                "generation_quality_worst_case_changed": not clean_candidate,
                "overall_relation": "improved" if clean_candidate else "regressed",
                "rubric_relation": "improved" if clean_candidate else "regressed",
            },
        ],
        "case_deltas": [
            {
                "case": "qa-basic",
                "run_name": "candidate",
                "baseline_name": "baseline",
                "is_baseline": False,
                "rubric_score_delta": candidate_case_delta,
                "relation": candidate_case_relation,
            }
        ],
        "summary": {
            "baseline_name": "baseline",
            "generation_quality_flag_regression_count": 0 if clean_candidate else 1,
            "generation_quality_dominant_flag_change_count": 0 if clean_candidate else 1,
            "case_regression_count": 0 if clean_candidate else 1,
        },
    }
    write_json(comparison_path, payload)
    return comparison_path


class BenchmarkScorecardDecisionTests(unittest.TestCase):
    def test_decision_module_reexports_artifact_writers(self) -> None:
        self.assertIs(
            benchmark_scorecard_decision.write_benchmark_scorecard_decision_outputs,
            benchmark_scorecard_decision_artifacts.write_benchmark_scorecard_decision_outputs,
        )
        self.assertIs(
            benchmark_scorecard_decision.render_benchmark_scorecard_decision_html,
            benchmark_scorecard_decision_artifacts.render_benchmark_scorecard_decision_html,
        )
        self.assertIs(
            benchmark_scorecard_decision.render_benchmark_scorecard_decision_markdown,
            benchmark_scorecard_decision_artifacts.render_benchmark_scorecard_decision_markdown,
        )

    def test_blocks_regressed_candidate_and_keeps_baseline_out(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=False)

            report = build_benchmark_scorecard_decision(comparison, generated_at="2026-05-16T00:00:00Z")

            self.assertEqual(report["decision_status"], "blocked")
            self.assertIsNone(report["selected_run"])
            baseline = next(row for row in report["candidate_evaluations"] if row["name"] == "baseline")
            candidate = next(row for row in report["candidate_evaluations"] if row["name"] == "candidate")
            self.assertIn("baseline run is not a promotion candidate", baseline["blockers"])
            self.assertIn("rubric score regressed from baseline", candidate["blockers"])
            self.assertIn("overall score regressed from baseline", candidate["blockers"])
            self.assertIn("generation-quality flags increased by 3", candidate["review_items"])
            self.assertEqual(report["summary"]["blocked_candidate_count"], 1)

    def test_promotes_clean_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=True)

            report = build_benchmark_scorecard_decision(comparison, generated_at="2026-05-16T00:00:00Z")

            self.assertEqual(report["decision_status"], "promote")
            self.assertEqual(report["recommended_action"], "promote_selected_scorecard")
            self.assertEqual(report["selected_run"]["name"], "candidate")
            self.assertEqual(report["selected_run"]["generation_quality_total_flags_delta"], -2)
            self.assertEqual(report["summary"]["clean_candidate_count"], 1)

    def test_load_directory_and_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = make_comparison(root, clean_candidate=True)

            loaded = load_benchmark_scorecard_comparison(comparison.parent)
            report = build_benchmark_scorecard_decision(comparison.parent, generated_at="2026-05-16T00:00:00Z")
            outputs = write_benchmark_scorecard_decision_outputs(report, root / "decision")
            markdown = render_benchmark_scorecard_decision_markdown(report)
            html = render_benchmark_scorecard_decision_html(report)

            self.assertEqual(loaded["schema_version"], 1)
            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("benchmark_scorecard_decision", Path(outputs["json"]).name)
            self.assertIn("generation_quality_total_flags_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Candidate Evaluations", markdown)
            self.assertIn("Demo &lt;scorecard comparison&gt;", html)
            self.assertNotIn("Demo <scorecard comparison>", html)

    def test_rejects_empty_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark_scorecard_comparison.json"
            write_json(path, {"schema_version": 1, "runs": []})

            with self.assertRaises(ValueError):
                build_benchmark_scorecard_decision(path)


if __name__ == "__main__":
    unittest.main()
