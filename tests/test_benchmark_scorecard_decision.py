from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

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


def make_comparison(
    root: Path,
    *,
    clean_candidate: bool = False,
    candidate_eval_status: str | None = "pass",
    candidate_design_status: str | None = "pass",
    extra_threshold_candidate: bool = False,
) -> Path:
    comparison_path = root / "comparison" / "benchmark_scorecard_comparison.json"
    candidate_flag_delta = -2 if clean_candidate else 3
    candidate_flag_relation = "improved" if clean_candidate else "regressed"
    candidate_case_relation = "improved" if clean_candidate else "regressed"
    candidate_case_delta = 4 if clean_candidate else -8
    runs = [
        {
            "name": "baseline",
            "source_path": "baseline/benchmark_scorecard.json",
            "run_dir": "baseline",
            "overall_score": 88,
            "rubric_avg_score": 86,
            "generation_quality_total_flags": 5,
            "generation_quality_dominant_flag": "low_diversity",
            "generation_quality_worst_case": "summary-short",
            "eval_suite_coverage_status": "pass",
            "eval_suite_comparison_status": "pass",
            "eval_suite_design_coverage_status": "pass",
            "eval_suite_design_comparison_status": "pass",
            "eval_suite_design_duplicate_seed_count": 0,
            "eval_suite_design_expected_behavior_complete": True,
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
            "eval_suite_coverage_status": "pass" if candidate_eval_status else None,
            "eval_suite_comparison_status": candidate_eval_status,
            "eval_suite_design_coverage_status": "pass" if candidate_design_status else None,
            "eval_suite_design_comparison_status": candidate_design_status,
            "eval_suite_design_duplicate_seed_count": 0 if candidate_design_status in {None, "pass"} else 1,
            "eval_suite_design_expected_behavior_complete": True,
        },
    ]
    deltas = [
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
    ]
    if extra_threshold_candidate:
        runs.append(
            {
                "name": "candidate-far",
                "source_path": "candidate-far/benchmark_scorecard.json",
                "run_dir": "candidate-far",
                "overall_score": 78,
                "rubric_avg_score": 52,
                "generation_quality_total_flags": 9,
                "generation_quality_dominant_flag": "empty_continuation",
                "generation_quality_worst_case": "qa-basic",
                "eval_suite_coverage_status": "pass",
                "eval_suite_comparison_status": "pass",
                "eval_suite_design_coverage_status": "pass",
                "eval_suite_design_comparison_status": "pass",
                "eval_suite_design_duplicate_seed_count": 0,
                "eval_suite_design_expected_behavior_complete": True,
            }
        )
        deltas.append(
            {
                "name": "candidate-far",
                "baseline_name": "baseline",
                "is_baseline": False,
                "overall_score_delta": -10,
                "rubric_avg_score_delta": -34,
                "generation_quality_total_flags_delta": 4,
                "generation_quality_flag_relation": "regressed",
                "generation_quality_dominant_flag_changed": True,
                "generation_quality_worst_case_changed": True,
                "overall_relation": "regressed",
                "rubric_relation": "regressed",
            }
        )
    payload = {
        "schema_version": 1,
        "title": "Demo <scorecard comparison>",
        "generated_at": "2026-05-16T00:00:00Z",
        "scorecard_count": len(runs),
        "baseline": {"name": "baseline"},
        "runs": runs,
        "baseline_deltas": deltas,
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
            "baseline_eval_suite_comparison_status": "pass",
            "baseline_eval_suite_design_comparison_status": "pass",
            "non_comparison_ready_count": 0 if candidate_eval_status in {None, "pass"} else 1,
            "non_comparison_ready_runs": [] if candidate_eval_status in {None, "pass"} else ["candidate"],
            "non_design_comparison_ready_count": 0 if candidate_design_status in {None, "pass"} else 1,
            "non_design_comparison_ready_runs": [] if candidate_design_status in {None, "pass"} else ["candidate"],
            "design_comparison_changed_count": 0 if candidate_design_status in {None, "pass"} else 1,
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
        self.assertIs(
            benchmark_scorecard_decision.write_benchmark_scorecard_remediation_csv,
            benchmark_scorecard_decision_artifacts.write_benchmark_scorecard_remediation_csv,
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
            self.assertEqual(candidate["blocker_categories"], ["rubric_regression", "overall_regression"])
            self.assertIn("generation_quality_flag_regression", candidate["review_categories"])
            self.assertEqual(candidate["eval_suite_comparison_status"], "pass")
            self.assertEqual(report["summary"]["blocked_candidate_count"], 1)
            self.assertEqual(report["summary"]["blocker_category_counts"]["rubric_regression"], 1)
            self.assertEqual(report["summary"]["dominant_blocker_category"], "rubric_regression")
            self.assertEqual(report["remediation_plan"][0]["category"], "rubric_regression")
            self.assertEqual(report["remediation_plan"][0]["kind"], "blocker")
            self.assertIn("rubric-regressed cases", report["remediation_plan"][0]["action"])
            self.assertEqual(report["remediation_plan"][0]["action_code"], "inspect_rubric_regressions")
            self.assertEqual(report["remediation_plan"][0]["severity"], "blocker")
            self.assertEqual(report["remediation_plan"][0]["owner_scope"], "model-eval")
            self.assertIn("benchmark_scorecard", report["remediation_plan"][0]["target_artifacts"])
            self.assertEqual(report["summary"]["remediation_plan_count"], 6)
            self.assertEqual(report["summary"]["remediation_blocker_count"], 2)
            self.assertEqual(report["summary"]["remediation_review_count"], 4)
            self.assertEqual(report["summary"]["dominant_remediation_category"], "rubric_regression")
            self.assertIn("Top remediation: rubric_regression", report["recommendations"][-1])

    def test_promotes_clean_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=True)

            report = build_benchmark_scorecard_decision(comparison, generated_at="2026-05-16T00:00:00Z")

            self.assertEqual(report["decision_status"], "promote")
            self.assertEqual(report["recommended_action"], "promote_selected_scorecard")
            self.assertEqual(report["selected_run"]["name"], "candidate")
            self.assertEqual(report["selected_run"]["generation_quality_total_flags_delta"], -2)
            self.assertEqual(report["summary"]["clean_candidate_count"], 1)

    def test_eval_suite_non_ready_candidate_requires_review_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=True, candidate_eval_status="warn")

            report = build_benchmark_scorecard_decision(comparison, generated_at="2026-05-16T00:00:00Z")

            self.assertEqual(report["decision_status"], "review")
            self.assertEqual(report["recommended_action"], "review_generation_flags_and_case_deltas")
            self.assertEqual(report["selected_run"]["name"], "candidate")
            self.assertIn("eval-suite comparison readiness is warn", report["selected_run"]["review_items"])
            self.assertEqual(report["summary"]["non_comparison_ready_candidate_count"], 1)
            self.assertEqual(report["summary"]["non_comparison_ready_candidates"], ["candidate"])
            self.assertEqual(report["summary"]["comparison_non_comparison_ready_runs"], ["candidate"])
            self.assertIn("not treat the selected scorecard as clean model-quality evidence", " ".join(report["recommendations"]))

    def test_suite_design_non_ready_candidate_requires_review_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=True, candidate_design_status="warn")

            report = build_benchmark_scorecard_decision(comparison, generated_at="2026-05-16T00:00:00Z")

            self.assertEqual(report["decision_status"], "review")
            self.assertEqual(report["recommended_action"], "review_generation_flags_and_case_deltas")
            self.assertEqual(report["selected_run"]["name"], "candidate")
            self.assertIn("suite-design comparison readiness is warn", report["selected_run"]["review_items"])
            self.assertEqual(report["selected_run"]["eval_suite_design_comparison_status"], "warn")
            self.assertEqual(report["selected_run"]["eval_suite_design_duplicate_seed_count"], 1)
            self.assertEqual(report["summary"]["non_design_comparison_ready_candidate_count"], 1)
            self.assertEqual(report["summary"]["non_design_comparison_ready_candidates"], ["candidate"])
            self.assertEqual(report["summary"]["comparison_non_design_comparison_ready_runs"], ["candidate"])
            self.assertEqual(report["summary"]["comparison_design_comparison_changed_count"], 1)
            self.assertIn("suite_design_not_ready", report["summary"]["review_category_counts"])
            self.assertEqual(report["summary"]["dominant_review_category"], "suite_design_not_ready")
            self.assertEqual(report["remediation_plan"][0]["category"], "suite_design_not_ready")
            self.assertEqual(report["remediation_plan"][0]["action_code"], "make_suite_design_comparison_ready")
            recommendations = " ".join(report["recommendations"])
            self.assertIn("prompt suite design is comparison-ready", recommendations)
            self.assertIn("non-suite-design-ready runs", recommendations)

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
            self.assertEqual(set(outputs), {"json", "csv", "remediation_csv", "markdown", "html"})
            self.assertIn("benchmark_scorecard_decision", Path(outputs["json"]).name)
            self.assertIn("generation_quality_total_flags_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("eval_suite_comparison_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("eval_suite_design_comparison_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("blocker_categories", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("review_categories", Path(outputs["csv"]).read_text(encoding="utf-8"))
            remediation_csv = Path(outputs["remediation_csv"]).read_text(encoding="utf-8")
            self.assertIn("action_code", remediation_csv)
            self.assertIn("target_artifacts", remediation_csv)
            self.assertIn("## Candidate Evaluations", markdown)
            self.assertIn("Eval Compare", markdown)
            self.assertIn("Design Compare", markdown)
            self.assertIn("Dominant blocker category", markdown)
            self.assertIn("Blocker Categories", markdown)
            self.assertIn("Remediation plan count", markdown)
            self.assertIn("Eval compare review", html)
            self.assertIn("Design compare review", html)
            self.assertIn("Top blocker", html)
            self.assertIn("Blocker Categories", html)
            self.assertIn("Threshold blocked", html)
            self.assertIn("Demo &lt;scorecard comparison&gt;", html)
            self.assertNotIn("Demo <scorecard comparison>", html)

    def test_summary_exposes_threshold_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison = make_comparison(Path(tmp), clean_candidate=False, extra_threshold_candidate=True)

            report = build_benchmark_scorecard_decision(
                comparison,
                min_rubric_score=85.0,
                generated_at="2026-05-16T00:00:00Z",
            )
            summary = report["summary"]
            markdown = render_benchmark_scorecard_decision_markdown(report)
            html = render_benchmark_scorecard_decision_html(report)

            self.assertEqual(summary["threshold_blocked_candidate_count"], 2)
            self.assertEqual(summary["threshold_blocked_candidate_names"], ["candidate", "candidate-far"])
            self.assertEqual(summary["first_threshold_blocked_candidate"], "candidate")
            self.assertEqual(summary["first_threshold_rubric_score"], 84.0)
            self.assertEqual(summary["first_threshold_min_rubric_score"], 85.0)
            self.assertEqual(summary["first_threshold_margin"], -1.0)
            self.assertEqual(summary["threshold_closest_candidate"], "candidate")
            self.assertEqual(summary["threshold_closest_margin"], -1.0)
            self.assertEqual(summary["threshold_largest_gap_candidate"], "candidate-far")
            self.assertEqual(summary["threshold_largest_gap_margin"], -33.0)
            self.assertEqual(summary["blocker_category_counts"]["threshold"], 2)
            self.assertEqual(summary["blocker_category_counts"]["rubric_regression"], 2)
            self.assertEqual(summary["blocker_category_counts"]["overall_regression"], 2)
            self.assertEqual(summary["review_category_counts"]["generation_quality_flag_regression"], 2)
            self.assertEqual(summary["dominant_blocker_category"], "threshold")
            self.assertEqual(summary["dominant_review_category"], "generation_quality_flag_regression")
            self.assertEqual(report["remediation_plan"][0]["category"], "threshold")
            self.assertEqual(report["remediation_plan"][0]["count"], 2)
            self.assertIn("explicit policy change", report["remediation_plan"][0]["action"])
            self.assertEqual(report["remediation_plan"][0]["action_code"], "raise_candidate_rubric_or_change_policy")
            self.assertEqual(report["remediation_plan"][0]["severity"], "blocker")
            self.assertEqual(report["remediation_plan"][0]["owner_scope"], "model-eval")
            self.assertIn("benchmark_scorecard_decision", report["remediation_plan"][0]["target_artifacts"])
            self.assertEqual(summary["remediation_plan_count"], 7)
            self.assertEqual(summary["dominant_remediation_kind"], "blocker")
            self.assertEqual(summary["dominant_remediation_category"], "threshold")
            self.assertIn("explicit policy change", summary["dominant_remediation_action"])
            self.assertIn("Threshold-blocked candidates: `2`", markdown)
            self.assertIn("Dominant remediation category: `threshold`", markdown)
            self.assertIn("Threshold closest: `candidate` / `-1`", markdown)
            self.assertIn("Dominant blocker category: `threshold`", markdown)
            self.assertIn("## Remediation Plan", markdown)
            self.assertIn("| blocker | threshold | 2 | 60 | blocker | model-eval | raise_candidate_rubric_or_change_policy |", markdown)
            self.assertIn("Action Code", markdown)
            self.assertIn("Threshold largest gap", html)
            self.assertIn("Remediation Plan", html)
            self.assertIn("Action Code", html)
            remediation_csv = Path(write_benchmark_scorecard_decision_outputs(report, Path(tmp) / "threshold-decision")["remediation_csv"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("raise_candidate_rubric_or_change_policy", remediation_csv)
            self.assertIn("benchmark_scorecard_decision; benchmark_scorecard", remediation_csv)

    def test_rejects_empty_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "benchmark_scorecard_comparison.json"
            write_json(path, {"schema_version": 1, "runs": []})

            with self.assertRaises(ValueError):
                build_benchmark_scorecard_decision(path)


if __name__ == "__main__":
    unittest.main()
