from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import maturity_narrative, maturity_narrative_artifacts
from minigpt import maturity_narrative_sections, maturity_narrative_summary
from minigpt.maturity_narrative import (
    build_maturity_narrative,
    render_maturity_narrative_html,
    write_maturity_narrative_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_project(
    root: Path,
    *,
    release_trend: str = "improved",
    regressed_count: int = 0,
    ci_regression_count: int = 0,
    ci_order_regression_count: int = 0,
    ci_boundary_plan_regression_count: int = 0,
    ci_archived_path_regression_count: int = 0,
    ci_regression_reasons: list[str] | None = None,
    coverage_regression_count: int = 0,
    benchmark_history_regression_count: int = 0,
    benchmark_suite_design_regression_count: int = 0,
    benchmark_design_change_delta_count: int = 0,
    benchmark_requirement_change_count: int = 0,
    benchmark_requirement_reason_added: list[str] | None = None,
    benchmark_requirement_reason_removed: list[str] | None = None,
) -> dict[str, Path]:
    project = root / "project"
    maturity_path = project / "runs" / "maturity-summary" / "maturity_summary.json"
    registry_path = project / "runs" / "registry" / "registry.json"
    request_path = project / "runs" / "request-history-summary" / "request_history_summary.json"
    scorecard_path = project / "runs" / "demo-run" / "benchmark-scorecard" / "benchmark_scorecard.json"
    decision_path = project / "runs" / "demo-run" / "benchmark-scorecard-decision" / "benchmark_scorecard_decision.json"
    history_path = project / "runs" / "demo-run" / "benchmark-history" / "benchmark_history.json"
    dataset_card_path = project / "datasets" / "demo" / "v1" / "dataset_card.json"
    reason_added = benchmark_requirement_reason_added or []
    reason_removed = benchmark_requirement_reason_removed or []
    ci_reasons = ci_regression_reasons or []
    ci_reason_counts = {reason: ci_reasons.count(reason) for reason in sorted(set(ci_reasons))}
    reason_mixed_delta_count = 1 if reason_added and reason_removed else 0
    reason_recovery_delta_count = 1 if reason_removed and not reason_added else 0
    if reason_mixed_delta_count:
        reason_drift_status_counts = {"mixed": 1}
    elif reason_added:
        reason_drift_status_counts = {"regressed": 1}
    elif reason_removed:
        reason_drift_status_counts = {"recovered": 1}
    else:
        reason_drift_status_counts = {"stable": 2}

    write_json(
        maturity_path,
        {
            "schema_version": 4,
            "summary": {
                "current_version": 66,
                "overall_status": "pass",
                "average_maturity_level": 4.75,
                "registry_runs": 2,
                "release_readiness_trend_status": release_trend,
                "release_readiness_regressed_count": regressed_count,
                "release_readiness_improved_count": 2,
                "release_readiness_ci_workflow_regression_count": ci_regression_count,
                "release_readiness_ci_workflow_order_regression_count": ci_order_regression_count,
                "release_readiness_ci_workflow_status_changed_count": 1 if ci_regression_count or ci_order_regression_count else 0,
                "release_readiness_ci_workflow_regression_reasons": ci_reasons,
                "release_readiness_ci_workflow_regression_reason_counts": ci_reason_counts,
                "release_readiness_ci_boundary_plan_check_ready_regression_count": ci_boundary_plan_regression_count,
                "release_readiness_ci_archived_path_portability_check_ready_regression_count": ci_archived_path_regression_count,
                "release_readiness_max_ci_workflow_failed_check_delta": 2 if ci_regression_count or ci_order_regression_count else 0,
                "release_readiness_max_ci_workflow_order_violation_delta": 1 if ci_order_regression_count else 0,
                "release_readiness_test_coverage_regression_count": coverage_regression_count,
                "release_readiness_test_coverage_status_changed_count": 1 if coverage_regression_count else 0,
                "release_readiness_max_test_coverage_percent_delta": 7.5 if coverage_regression_count else 0,
                "release_readiness_max_test_coverage_gap_delta": 3 if coverage_regression_count else 0,
                "release_readiness_benchmark_history_regression_count": benchmark_history_regression_count,
                "release_readiness_benchmark_history_status_changed_count": 1 if benchmark_history_regression_count else 0,
                "release_readiness_benchmark_history_boundary_changed_count": 1 if benchmark_history_regression_count else 0,
                "release_readiness_max_benchmark_history_case_regression_delta": 2 if benchmark_history_regression_count else 0,
                "release_readiness_max_benchmark_history_generation_flag_regression_delta": 1 if benchmark_history_regression_count else 0,
                "release_readiness_benchmark_suite_design_delta_count": 1 if benchmark_suite_design_regression_count else 0,
                "release_readiness_benchmark_suite_design_regression_count": benchmark_suite_design_regression_count,
                "release_readiness_benchmark_design_change_delta_count": benchmark_design_change_delta_count,
                "release_readiness_max_benchmark_suite_design_delta": 2 if benchmark_suite_design_regression_count else 0,
                "release_readiness_max_benchmark_design_change_delta": 3 if benchmark_design_change_delta_count else 0,
                "release_readiness_benchmark_requirement_status_changed_count": benchmark_requirement_change_count,
                "release_readiness_max_benchmark_requirement_exit_code_delta": 1 if benchmark_requirement_change_count else 0,
                "release_readiness_benchmark_requirement_failed_reason_added_count": len(reason_added),
                "release_readiness_benchmark_requirement_failed_reason_removed_count": len(reason_removed),
                "release_readiness_benchmark_requirement_failed_reason_added": reason_added,
                "release_readiness_benchmark_requirement_failed_reason_removed": reason_removed,
                "release_readiness_benchmark_requirement_failed_reason_recovery_delta_count": reason_recovery_delta_count,
                "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count": reason_mixed_delta_count,
                "release_readiness_benchmark_requirement_failed_reason_drift_status_counts": reason_drift_status_counts,
            },
            "release_readiness_context": {
                "available": True,
                "trend_status": release_trend,
                "delta_count": 2,
                "regressed_count": regressed_count,
                "improved_count": 2,
                "panel_changed_count": 0,
                "ci_workflow_regression_count": ci_regression_count,
                "ci_workflow_order_regression_count": ci_order_regression_count,
                "ci_workflow_status_changed_count": 1 if ci_regression_count or ci_order_regression_count else 0,
                "ci_workflow_regression_reasons": ci_reasons,
                "ci_workflow_regression_reason_counts": ci_reason_counts,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": ci_boundary_plan_regression_count,
                "ci_workflow_archived_path_portability_check_ready_regression_count": ci_archived_path_regression_count,
                "max_abs_ci_workflow_failed_check_delta": 2 if ci_regression_count or ci_order_regression_count else 0,
                "max_abs_ci_workflow_order_violation_delta": 1 if ci_order_regression_count else 0,
                "test_coverage_regression_count": coverage_regression_count,
                "test_coverage_status_changed_count": 1 if coverage_regression_count else 0,
                "max_abs_test_coverage_percent_delta": 7.5 if coverage_regression_count else 0,
                "max_abs_test_coverage_gap_delta": 3 if coverage_regression_count else 0,
                "benchmark_history_regression_count": benchmark_history_regression_count,
                "benchmark_history_status_changed_count": 1 if benchmark_history_regression_count else 0,
                "benchmark_history_boundary_changed_count": 1 if benchmark_history_regression_count else 0,
                "benchmark_history_suite_design_non_comparison_ready_delta_count": 1 if benchmark_suite_design_regression_count else 0,
                "benchmark_history_suite_design_non_comparison_ready_regression_count": benchmark_suite_design_regression_count,
                "benchmark_history_design_comparison_changed_delta_count": benchmark_design_change_delta_count,
                "benchmark_history_readiness_requirement_status_changed_count": benchmark_requirement_change_count,
                "max_abs_benchmark_history_case_regression_delta": 2 if benchmark_history_regression_count else 0,
                "max_abs_benchmark_history_generation_flag_regression_delta": 1 if benchmark_history_regression_count else 0,
                "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": 2 if benchmark_suite_design_regression_count else 0,
                "max_abs_benchmark_history_design_comparison_changed_entries_delta": 3 if benchmark_design_change_delta_count else 0,
                "max_abs_benchmark_history_readiness_requirement_exit_code_delta": 1 if benchmark_requirement_change_count else 0,
                "benchmark_history_readiness_requirement_failed_reason_added_count": len(reason_added),
                "benchmark_history_readiness_requirement_failed_reason_removed_count": len(reason_removed),
                "benchmark_history_readiness_requirement_failed_reason_added": reason_added,
                "benchmark_history_readiness_requirement_failed_reason_removed": reason_removed,
                "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": reason_recovery_delta_count,
                "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": reason_mixed_delta_count,
                "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": reason_drift_status_counts,
            },
            "request_history_context": {
                "status": "pass",
                "total_log_records": 6,
                "timeout_rate": 0.0,
            },
        },
    )
    write_json(
        registry_path,
        {
            "run_count": 2,
            "release_readiness_comparison_counts": {release_trend: 1, "stable": 1},
            "release_readiness_delta_summary": {
                "delta_count": 2,
                "regressed_count": regressed_count,
                "improved_count": 2,
                "panel_changed_count": 0,
                "ci_workflow_regression_count": ci_regression_count,
                "ci_workflow_order_regression_count": ci_order_regression_count,
                "ci_workflow_status_changed_count": 1 if ci_regression_count or ci_order_regression_count else 0,
                "ci_workflow_regression_reasons": ci_reasons,
                "ci_workflow_regression_reason_counts": ci_reason_counts,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count": ci_boundary_plan_regression_count,
                "ci_workflow_archived_path_portability_check_ready_regression_count": ci_archived_path_regression_count,
                "max_abs_ci_workflow_failed_check_delta": 2 if ci_regression_count or ci_order_regression_count else 0,
                "max_abs_ci_workflow_order_violation_delta": 1 if ci_order_regression_count else 0,
                "test_coverage_regression_count": coverage_regression_count,
                "test_coverage_status_changed_count": 1 if coverage_regression_count else 0,
                "max_abs_test_coverage_percent_delta": 7.5 if coverage_regression_count else 0,
                "max_abs_test_coverage_gap_delta": 3 if coverage_regression_count else 0,
                "benchmark_history_regression_count": benchmark_history_regression_count,
                "benchmark_history_status_changed_count": 1 if benchmark_history_regression_count else 0,
                "benchmark_history_boundary_changed_count": 1 if benchmark_history_regression_count else 0,
                "benchmark_history_suite_design_non_comparison_ready_delta_count": 1 if benchmark_suite_design_regression_count else 0,
                "benchmark_history_suite_design_non_comparison_ready_regression_count": benchmark_suite_design_regression_count,
                "benchmark_history_design_comparison_changed_delta_count": benchmark_design_change_delta_count,
                "benchmark_history_readiness_requirement_status_changed_count": benchmark_requirement_change_count,
                "max_abs_benchmark_history_case_regression_delta": 2 if benchmark_history_regression_count else 0,
                "max_abs_benchmark_history_generation_flag_regression_delta": 1 if benchmark_history_regression_count else 0,
                "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta": 2 if benchmark_suite_design_regression_count else 0,
                "max_abs_benchmark_history_design_comparison_changed_entries_delta": 3 if benchmark_design_change_delta_count else 0,
                "max_abs_benchmark_history_readiness_requirement_exit_code_delta": 1 if benchmark_requirement_change_count else 0,
                "benchmark_history_readiness_requirement_failed_reason_added_count": len(reason_added),
                "benchmark_history_readiness_requirement_failed_reason_removed_count": len(reason_removed),
                "benchmark_history_readiness_requirement_failed_reason_added": reason_added,
                "benchmark_history_readiness_requirement_failed_reason_removed": reason_removed,
                "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": reason_recovery_delta_count,
                "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": reason_mixed_delta_count,
                "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": reason_drift_status_counts,
            },
        },
    )
    write_json(
        request_path,
        {
            "schema_version": 1,
            "summary": {
                "status": "pass",
                "total_log_records": 6,
                "timeout_rate": 0.0,
                "error_rate": 0.0,
            },
        },
    )
    write_json(
        scorecard_path,
        {
            "schema_version": 3,
            "summary": {
                "overall_status": "pass",
                "overall_score": 88.5,
                "rubric_status": "pass",
                "rubric_avg_score": 90.0,
                "weakest_rubric_case": "summary-short",
                "weakest_rubric_score": 82.0,
            },
        },
    )
    write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_status": "promote",
            "recommended_action": "promote_selected_scorecard",
            "summary": {
                "candidate_count": 1,
                "clean_candidate_count": 1,
                "review_candidate_count": 0,
                "blocked_candidate_count": 0,
                "non_comparison_ready_candidate_count": 0,
                "non_comparison_ready_candidates": [],
                "selected_name": "demo-run",
                "selected_relation": "promote",
                "selected_rubric_avg_score": 90.0,
                "selected_generation_quality_total_flags_delta": -2,
                "selected_eval_suite_comparison_status": "pass",
            },
            "selected_run": {
                "name": "demo-run",
                "decision_relation": "promote",
                "rubric_avg_score": 90.0,
                "generation_quality_total_flags_delta": -2,
                "eval_suite_comparison_status": "pass",
            },
            "candidate_evaluations": [
                {"name": "baseline", "is_baseline": True, "blockers": ["baseline run is not a promotion candidate"], "review_items": []},
                {"name": "demo-run", "is_baseline": False, "eval_suite_comparison_status": "pass", "blockers": [], "review_items": []},
            ],
        },
    )
    write_json(
        history_path,
        {
            "schema_version": 1,
            "evidence_kind": "real-benchmark",
            "summary": {
                "entry_count": 1,
                "promote_count": 1,
                "review_count": 0,
                "blocked_count": 0,
                "ready_count": 1,
                "case_regression_entry_count": 0,
                "generation_quality_flag_regression_entry_count": 0,
                "suite_design_non_comparison_ready_entry_count": 0,
                "design_comparison_changed_entry_count": 0,
                "best_candidate_name": "demo-run",
                "model_quality_claim": "candidate_evidence",
            },
            "readiness_requirement": {
                "status": "pass",
                "decision": "continue",
                "exit_code": 0,
                "min_ready_entries": 1,
                "ready_count": 1,
                "entry_count": 1,
                "evidence_kind": "real-benchmark",
                "require_real_benchmark": True,
                "failed_reasons": [],
            },
            "entries": [
                {
                    "name": "demo-history",
                    "candidate_name": "demo-run",
                    "decision_status": "promote",
                    "promotion_readiness": "ready",
                    "model_quality_claim": "candidate_evidence",
                    "rubric_avg_score_delta": 5.0,
                    "generation_quality_total_flags_delta": -2,
                    "case_regression_count": 0,
                    "eval_suite_design_comparison_status": "pass",
                    "non_design_comparison_ready_count": 0,
                    "design_comparison_changed_count": 0,
                    "boundary": "standard-benchmark-candidate-evidence",
                }
            ],
        },
    )
    write_json(
        dataset_card_path,
        {
            "schema_version": 1,
            "summary": {
                "readiness_status": "ready",
                "quality_status": "pass",
                "warning_count": 0,
                "short_fingerprint": "abc12345",
            },
            "quality": {"status": "pass", "warning_count": 0},
        },
    )
    return {
        "project": project,
        "maturity": maturity_path,
        "registry": registry_path,
        "request": request_path,
        "scorecard": scorecard_path,
        "scorecard_decision": decision_path,
        "benchmark_history": history_path,
        "dataset_card": dataset_card_path,
    }


class MaturityNarrativeTests(unittest.TestCase):
    def test_maturity_narrative_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(
            maturity_narrative.render_maturity_narrative_html,
            maturity_narrative_artifacts.render_maturity_narrative_html,
        )
        self.assertIs(
            maturity_narrative.write_maturity_narrative_outputs,
            maturity_narrative_artifacts.write_maturity_narrative_outputs,
        )

    def test_maturity_narrative_uses_split_summary_and_section_helpers(self) -> None:
        self.assertIs(
            maturity_narrative.build_maturity_narrative.__globals__["build_maturity_narrative_summary"],
            maturity_narrative_summary.build_maturity_narrative_summary,
        )
        self.assertIs(
            maturity_narrative.build_maturity_narrative.__globals__["build_maturity_narrative_sections"],
            maturity_narrative_sections.build_maturity_narrative_sections,
        )
        summary = maturity_narrative_summary.build_maturity_narrative_summary(
            {"summary": {"current_version": 1, "overall_status": "pass", "average_maturity_level": 1.0}, "release_readiness_context": {"trend_status": "improved"}},
            {"run_count": 1},
            {"summary": {"status": "pass", "total_log_records": 1}},
            [{"summary": {"overall_status": "pass", "overall_score": 80}}],
            [{"decision_status": "promote", "selected_run": {"name": "demo"}}],
            [{"summary": {"quality_status": "pass", "warning_count": 0}}],
            [
                {
                    "summary": {"entry_count": 1, "ready_count": 1},
                    "readiness_requirement": {"status": "pass", "exit_code": 0, "failed_reasons": []},
                    "entries": [{"boundary": "standard-benchmark-candidate-evidence"}],
                }
            ],
        )
        sections = maturity_narrative_sections.build_maturity_narrative_sections(summary)

        self.assertEqual(summary["portfolio_status"], "ready")
        self.assertEqual(sections[4]["title"], "Benchmark Promotion Decision")
        self.assertEqual(sections[5]["title"], "Benchmark History")

    def test_build_maturity_narrative_ready_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))

            narrative = build_maturity_narrative(
                paths["project"],
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(narrative["schema_version"], 1)
            self.assertEqual(narrative["summary"]["portfolio_status"], "ready")
            self.assertEqual(narrative["summary"]["current_version"], 66)
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "improved")
            self.assertEqual(narrative["summary"]["release_readiness_regressed_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_ci_workflow_regression_reasons"], [])
            self.assertEqual(narrative["summary"]["release_readiness_ci_workflow_regression_reason_counts"], {})
            self.assertEqual(narrative["summary"]["release_readiness_test_coverage_regression_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_history_regression_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_suite_design_delta_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_suite_design_regression_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_design_change_delta_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_status_changed_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_exit_code_delta_max"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_removed_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_removed"], [])
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_drift_status_counts"], {"stable": 2})
            self.assertEqual(narrative["summary"]["request_history_status"], "pass")
            self.assertEqual(narrative["summary"]["benchmark_scorecard_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_avg_score"], 88.5)
            self.assertEqual(narrative["summary"]["benchmark_weakest_case"], "summary-short")
            self.assertEqual(narrative["summary"]["benchmark_decision_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_run"], "demo-run")
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_flag_delta"], -2)
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_eval_suite_comparison_status"], "pass")
            self.assertEqual(narrative["summary"]["benchmark_decision_non_comparison_ready_candidate_count"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_entry_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_ready_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_readiness_requirement_failed_count"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_readiness_requirement_exit_code_max"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_readiness_requirement_failed_reasons"], [])
            self.assertEqual(narrative["summary"]["benchmark_history_suite_design_non_comparison_ready_entry_count"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_design_comparison_changed_entry_count"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_best_candidate"], "demo-run")
            self.assertEqual(narrative["summary"]["benchmark_history_latest_boundary"], "standard-benchmark-candidate-evidence")
            self.assertEqual(narrative["summary"]["dataset_card_count"], 1)
            self.assertEqual(narrative["summary"]["dataset_warning_count"], 0)
            self.assertEqual(narrative["warnings"], [])
            self.assertIn("Release Quality Trend", {item["title"] for item in narrative["sections"]})
            self.assertIn("benchmark", {item["area"] for item in narrative["evidence_matrix"]})
            self.assertIn("scorecard promotion decision", {item["signal"] for item in narrative["evidence_matrix"]})
            self.assertIn("benchmark history ledger", {item["signal"] for item in narrative["evidence_matrix"]})
            self.assertIn("dataset", {item["area"] for item in narrative["evidence_matrix"]})

    def test_build_maturity_narrative_marks_review_for_history_flag_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            history = json.loads(paths["benchmark_history"].read_text(encoding="utf-8"))
            history["summary"]["generation_quality_flag_regression_entry_count"] = 1
            history["entries"][0]["generation_quality_total_flags_delta"] = 3
            history["entries"][0]["generation_quality_flag_relation"] = "regressed"
            write_json(paths["benchmark_history"], history)

            narrative = build_maturity_narrative(paths["project"])
            history_section = next(item for item in narrative["sections"] if item["key"] == "benchmark_history")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["benchmark_history_generation_flag_regression_entry_count"], 1)
            self.assertEqual(history_section["status"], "warn")
            self.assertIn("generation-quality flag regressions", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_history_readiness_requirement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            history = json.loads(paths["benchmark_history"].read_text(encoding="utf-8"))
            history["readiness_requirement"] = {
                "status": "fail",
                "decision": "stop",
                "exit_code": 1,
                "min_ready_entries": 2,
                "ready_count": 1,
                "entry_count": 1,
                "evidence_kind": "real-benchmark",
                "require_real_benchmark": True,
                "failed_reasons": ["insufficient_ready_entries"],
            }
            write_json(paths["benchmark_history"], history)

            narrative = build_maturity_narrative(paths["project"])
            history_section = next(item for item in narrative["sections"] if item["key"] == "benchmark_history")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["benchmark_history_readiness_requirement_failed_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_readiness_requirement_exit_code_max"], 1)
            self.assertEqual(
                narrative["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["insufficient_ready_entries"],
            )
            self.assertEqual(history_section["status"], "fail")
            self.assertIn("readiness requirement failures=1", history_section["claim"])
            self.assertIn("Fix benchmark history readiness requirement failures", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_history_suite_design_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            history = json.loads(paths["benchmark_history"].read_text(encoding="utf-8"))
            history["summary"]["ready_count"] = 0
            history["summary"]["review_count"] = 1
            history["summary"]["suite_design_non_comparison_ready_entry_count"] = 1
            history["summary"]["design_comparison_changed_entry_count"] = 1
            history["readiness_requirement"] = {
                "status": "fail",
                "decision": "stop",
                "exit_code": 1,
                "min_ready_entries": 1,
                "ready_count": 0,
                "entry_count": 1,
                "evidence_kind": "real-benchmark",
                "require_real_benchmark": True,
                "failed_reasons": ["suite_design_non_comparison_ready_entries"],
            }
            history["entries"][0]["promotion_readiness"] = "review"
            history["entries"][0]["eval_suite_design_comparison_status"] = "warn"
            history["entries"][0]["non_design_comparison_ready_count"] = 1
            history["entries"][0]["design_comparison_changed_count"] = 1
            history["entries"][0]["boundary"] = "suite-design-not-comparison-ready"
            write_json(paths["benchmark_history"], history)

            narrative = build_maturity_narrative(paths["project"])
            history_section = next(item for item in narrative["sections"] if item["key"] == "benchmark_history")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["benchmark_history_ready_count"], 0)
            self.assertEqual(narrative["summary"]["benchmark_history_review_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_suite_design_non_comparison_ready_entry_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_design_comparison_changed_entry_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_history_latest_boundary"], "suite-design-not-comparison-ready")
            self.assertEqual(
                narrative["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["suite_design_non_comparison_ready_entries"],
            )
            self.assertEqual(history_section["status"], "fail")
            self.assertIn("suite-design not-ready entries=1", history_section["claim"])
            self.assertIn("design comparison changes=1", history_section["claim"])
            self.assertIn("suite-design comparison readiness", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_release_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp), release_trend="regressed", regressed_count=1)

            narrative = build_maturity_narrative(paths["project"])

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "regressed")
            self.assertEqual(narrative["summary"]["release_readiness_regressed_count"], 1)
            self.assertIn("Resolve review-level release", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_release_suite_design_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="stable",
                benchmark_suite_design_regression_count=1,
                benchmark_design_change_delta_count=1,
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "benchmark-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_suite_design_delta_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_suite_design_regression_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_design_change_delta_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_max_benchmark_suite_design_delta"], 2)
            self.assertEqual(narrative["summary"]["release_readiness_max_benchmark_design_change_delta"], 3)
            self.assertEqual(release_section["status"], "benchmark-regressed")
            self.assertIn("benchmark suite-design deltas=1", release_section["claim"])
            self.assertIn("suite-design regressions=1", release_section["claim"])
            self.assertIn("max suite-design delta=2", release_section["claim"])
            self.assertIn("release-readiness benchmark suite-design regressions", " ".join(narrative["recommendations"]))

    def test_build_maturity_narrative_marks_review_for_ci_order_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="ci-regressed",
                ci_regression_count=1,
                ci_order_regression_count=1,
                ci_boundary_plan_regression_count=1,
                ci_archived_path_regression_count=1,
                ci_regression_reasons=[
                    "drift_contract_smoke_ready_to_not_ready",
                    "ci_failed_checks_increased",
                    "boundary_gate_plan_check_not_ready",
                    "archived_path_portability_check_not_ready",
                ],
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "ci-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_ci_workflow_regression_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_ci_workflow_order_regression_count"], 1)
            self.assertEqual(
                narrative["summary"]["release_readiness_ci_workflow_regression_reasons"],
                [
                    "drift_contract_smoke_ready_to_not_ready",
                    "ci_failed_checks_increased",
                    "boundary_gate_plan_check_not_ready",
                    "archived_path_portability_check_not_ready",
                ],
            )
            self.assertEqual(
                narrative["summary"]["release_readiness_ci_workflow_regression_reason_counts"],
                {
                    "ci_failed_checks_increased": 1,
                    "drift_contract_smoke_ready_to_not_ready": 1,
                    "boundary_gate_plan_check_not_ready": 1,
                    "archived_path_portability_check_not_ready": 1,
                },
            )
            self.assertEqual(narrative["summary"]["release_readiness_ci_boundary_plan_check_ready_regression_count"], 1)
            self.assertEqual(
                narrative["summary"]["release_readiness_ci_archived_path_portability_check_ready_regression_count"],
                1,
            )
            self.assertEqual(narrative["summary"]["release_readiness_max_ci_workflow_order_violation_delta"], 1)
            self.assertEqual(release_section["status"], "ci-regressed")
            self.assertIn("CI workflow regressions=1", release_section["claim"])
            self.assertIn("CI order regressions=1", release_section["claim"])
            self.assertIn("archived_path_portability_check_not_ready:1", release_section["claim"])
            self.assertIn("CI boundary plan regressions=1", release_section["claim"])
            self.assertIn("CI archived path regressions=1", release_section["claim"])
            self.assertIn("max order violation delta=1", release_section["claim"])
            self.assertIn("release readiness CI workflow regression reasons", narrative["recommendations"][0])
            self.assertIn("boundary_gate_plan_check_not_ready:1", narrative["recommendations"][0])
            self.assertIn("archived_path_portability_check_not_ready:1", narrative["recommendations"][0])
            self.assertIn("drift_contract_smoke_ready_to_not_ready:1", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_coverage_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp), release_trend="coverage-regressed", coverage_regression_count=1)

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "coverage-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_test_coverage_regression_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_test_coverage_status_changed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_max_test_coverage_percent_delta"], 7.5)
            self.assertEqual(narrative["summary"]["release_readiness_max_test_coverage_gap_delta"], 3)
            self.assertEqual(narrative["summary"]["release_readiness_ci_workflow_order_regression_count"], 0)
            self.assertEqual(release_section["status"], "coverage-regressed")
            self.assertIn("test coverage regressions=1", release_section["claim"])
            self.assertIn("max coverage gap delta=3", release_section["claim"])
            self.assertIn("Resolve review-level release", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_benchmark_history_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="benchmark-regressed",
                benchmark_history_regression_count=1,
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "benchmark-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_history_regression_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_history_status_changed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_history_boundary_changed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_max_benchmark_history_case_regression_delta"], 2)
            self.assertEqual(narrative["summary"]["release_readiness_max_benchmark_history_generation_flag_regression_delta"], 1)
            self.assertEqual(release_section["status"], "benchmark-regressed")
            self.assertIn("benchmark-history regressions=1", release_section["claim"])
            self.assertIn("max benchmark case-regression delta=2", release_section["claim"])
            self.assertIn("benchmark boundary changes=1", release_section["claim"])
            self.assertIn("Resolve review-level release", narrative["recommendations"][0])

    def test_build_maturity_narrative_marks_review_for_benchmark_requirement_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="benchmark-regressed",
                benchmark_history_regression_count=0,
                benchmark_requirement_change_count=1,
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "benchmark-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_status_changed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_exit_code_delta_max"], 1)
            self.assertEqual(release_section["status"], "benchmark-regressed")
            self.assertIn("benchmark requirement changes=1", release_section["claim"])
            self.assertIn("benchmark requirement exit delta=1", release_section["claim"])
            self.assertIn("benchmark-history readiness requirement changes", " ".join(narrative["recommendations"]))

    def test_build_maturity_narrative_marks_review_for_benchmark_requirement_reason_addition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="benchmark-regressed",
                benchmark_requirement_reason_added=["tiny_smoke_only"],
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "benchmark-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_status_changed_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_added_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_added"], ["tiny_smoke_only"])
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"], 0)
            self.assertEqual(release_section["status"], "benchmark-regressed")
            self.assertIn("benchmark failed reasons added=1", release_section["claim"])
            self.assertIn("tiny_smoke_only", release_section["claim"])
            self.assertIn("newly added benchmark-history readiness failed reasons", " ".join(narrative["recommendations"]))

    def test_build_maturity_narrative_keeps_reason_removal_visible_without_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="stable",
                benchmark_requirement_reason_removed=["tiny_smoke_only"],
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "ready")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "stable")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_added_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_removed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_removed"], ["tiny_smoke_only"])
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"], 0)
            self.assertEqual(
                narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_drift_status_counts"],
                {"recovered": 1},
            )
            self.assertEqual(release_section["status"], "stable")
            self.assertIn("removed=1", release_section["claim"])
            self.assertIn("recovery deltas=1", release_section["claim"])
            self.assertIn("tiny_smoke_only", release_section["claim"])
            self.assertIn("recovery evidence", " ".join(narrative["recommendations"]))

    def test_build_maturity_narrative_marks_review_for_mixed_reason_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(
                Path(tmp),
                release_trend="stable",
                benchmark_requirement_reason_added=["tiny_smoke_only"],
                benchmark_requirement_reason_removed=["legacy_fixture_gap"],
            )

            narrative = build_maturity_narrative(paths["project"])
            release_section = next(item for item in narrative["sections"] if item["key"] == "release_quality")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "benchmark-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_added_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_removed_count"], 1)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_recovery_delta_count"], 0)
            self.assertEqual(narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_mixed_delta_count"], 1)
            self.assertEqual(
                narrative["summary"]["release_readiness_benchmark_requirement_failed_reason_drift_status_counts"],
                {"mixed": 1},
            )
            self.assertEqual(release_section["status"], "benchmark-regressed")
            self.assertIn("mixed deltas=1", release_section["claim"])
            self.assertIn("tiny_smoke_only", release_section["claim"])
            self.assertIn("legacy_fixture_gap", release_section["claim"])
            self.assertIn("mixed benchmark-history readiness failed-reason drift", " ".join(narrative["recommendations"]))

    def test_build_maturity_narrative_marks_review_for_non_comparison_ready_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            decision = json.loads(paths["scorecard_decision"].read_text(encoding="utf-8"))
            decision["decision_status"] = "review"
            decision["summary"]["clean_candidate_count"] = 0
            decision["summary"]["review_candidate_count"] = 1
            decision["summary"]["non_comparison_ready_candidate_count"] = 1
            decision["summary"]["non_comparison_ready_candidates"] = ["demo-run"]
            decision["summary"]["selected_relation"] = "review"
            decision["summary"]["selected_eval_suite_comparison_status"] = "warn"
            decision["selected_run"]["decision_relation"] = "review"
            decision["selected_run"]["eval_suite_comparison_status"] = "warn"
            decision["candidate_evaluations"][1]["decision_relation"] = "review"
            decision["candidate_evaluations"][1]["eval_suite_comparison_status"] = "warn"
            decision["candidate_evaluations"][1]["review_items"] = ["eval-suite comparison readiness is warn"]
            write_json(paths["scorecard_decision"], decision)

            narrative = build_maturity_narrative(paths["project"])
            decision_section = next(item for item in narrative["sections"] if item["key"] == "benchmark_promotion")

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["benchmark_decision_selected_eval_suite_comparison_status"], "warn")
            self.assertEqual(narrative["summary"]["benchmark_decision_non_comparison_ready_candidate_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_decision_non_comparison_ready_candidates"], ["demo-run"])
            self.assertEqual(decision_section["status"], "warn")
            self.assertIn("review-only", narrative["recommendations"][0])

    def test_build_maturity_narrative_requires_request_history_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            paths["request"].unlink()

            narrative = build_maturity_narrative(paths["project"])

            self.assertEqual(narrative["summary"]["portfolio_status"], "incomplete")
            self.assertIn("request history summary is missing", narrative["warnings"])

    def test_write_maturity_narrative_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            narrative = build_maturity_narrative(paths["project"])

            outputs = write_maturity_narrative_outputs(narrative, root / "narrative")

            self.assertEqual(set(outputs), {"json", "markdown", "html"})
            self.assertIn("maturity_narrative", Path(outputs["json"]).name)
            self.assertIn("## Evidence Matrix", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release Quality Trend", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release CI workflow regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release CI order regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release CI regression reasons", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release CI boundary plan regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release coverage regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release coverage gap delta", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark-history regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark-history boundary changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark suite-design regressions", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark design changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark requirement changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release benchmark requirement exit delta", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Scorecard decision run", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Scorecard decision eval compare", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Scorecard decision non-ready candidates", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark histories", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history boundary", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history suite-design not-ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history design changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness failures", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness exit", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Evidence Matrix", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI regressions", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI order regressions", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI reasons", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI boundary plan", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Coverage regressions", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Coverage gap delta", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark regressions", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark boundary changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark suite regressions", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark design changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark req changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark req exit", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark Promotion Decision", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark History", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("History boundary", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("History design review", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("History design changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("History readiness failures", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("History readiness exit", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Decision eval", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark Quality", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_cli_prints_benchmark_history_suite_design_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            out_dir = Path(tmp) / "cli-narrative"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_maturity_narrative.py"),
                    "--project-root",
                    str(paths["project"]),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("benchmark_history_suite_design_non_comparison_ready_entries=0", completed.stdout)
            self.assertIn("benchmark_history_design_comparison_changed_entries=0", completed.stdout)
            self.assertIn("release_readiness_benchmark_suite_design_delta_count=0", completed.stdout)
            self.assertIn("release_readiness_benchmark_suite_design_regression_count=0", completed.stdout)
            self.assertTrue((out_dir / "maturity_narrative.json").is_file())

    def test_render_maturity_narrative_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            narrative = build_maturity_narrative(paths["project"], title="<Narrative>")

            html = render_maturity_narrative_html(narrative)

            self.assertIn("&lt;Narrative&gt;", html)
            self.assertNotIn("<h1><Narrative>", html)


if __name__ == "__main__":
    unittest.main()
