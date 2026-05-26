from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import release_readiness_comparison as comparison_module  # noqa: E402
from minigpt import release_readiness_comparison_artifacts as artifact_module  # noqa: E402
from minigpt.release_readiness_comparison import (
    build_release_readiness_comparison,
    render_release_readiness_comparison_html,
    render_release_readiness_comparison_markdown,
    write_release_readiness_comparison_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_readiness(
    root: Path,
    name: str,
    *,
    status: str,
    decision: str,
    gate_status: str,
    request_status: str = "pass",
    audit_score: float = 100.0,
    ci_workflow_status: str = "pass",
    ci_workflow_failed_checks: int = 0,
    ci_workflow_order_violations: int = 0,
    ci_workflow_tiny_scorecard_plan_digest_gate_ready: bool | None = True,
    ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready: bool | None = True,
    ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready: bool | None = True,
    ci_workflow_release_readiness_drift_contract_smoke_ready: bool | None = True,
    test_coverage_status: str = "pass",
    test_coverage_percent: float = 90.17,
    test_coverage_gap: float = 0.0,
    benchmark_history_status: str = "pass",
    benchmark_history_entries: int = 1,
    benchmark_history_ready: int = 1,
    benchmark_history_review: int = 0,
    benchmark_history_blocked: int = 0,
    benchmark_history_case_regressions: int = 0,
    benchmark_history_generation_flag_regressions: int = 0,
    benchmark_history_suite_design_non_comparison_ready_entries: int = 0,
    benchmark_history_design_comparison_changed_entries: int = 0,
    benchmark_history_readiness_requirement_status: str = "pass",
    benchmark_history_readiness_requirement_exit_code: int = 0,
    benchmark_history_readiness_requirement_failed_reasons: list[str] | None = None,
    benchmark_history_model_quality_claim: str = "candidate_evidence",
    benchmark_history_latest_boundary: str = "standard-benchmark-candidate-evidence",
    fail_panels: int = 0,
    warn_panels: int = 0,
) -> Path:
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name).strip("_") or "readiness"
    benchmark_history_panel_status = (
        "pass"
        if benchmark_history_status == "pass" and benchmark_history_suite_design_non_comparison_ready_entries == 0
        else "warn"
    )
    panel_statuses = {
        "registry": "pass",
        "release_bundle": "pass",
        "project_audit": "pass",
        "release_gate": "pass" if gate_status == "pass" else "fail",
        "request_history": "pass" if request_status == "pass" else "warn",
        "maturity": "pass",
        "ci_workflow_hygiene": "pass" if ci_workflow_status == "pass" else "warn",
        "test_coverage": "pass" if test_coverage_status == "pass" else "warn",
        "benchmark_history": benchmark_history_panel_status,
    }
    report = {
        "schema_version": 1,
        "title": "MiniGPT release readiness dashboard",
        "summary": {
            "release_name": name,
            "readiness_status": status,
            "decision": decision,
            "gate_status": gate_status,
            "audit_status": "pass",
            "audit_score_percent": audit_score,
            "ci_workflow_status": ci_workflow_status,
            "ci_workflow_failed_checks": ci_workflow_failed_checks,
            "ci_workflow_node24_actions": 2 if ci_workflow_status == "pass" else 1,
            "ci_workflow_required_order_count": 1,
            "ci_workflow_order_violation_count": ci_workflow_order_violations,
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready": ci_workflow_tiny_scorecard_plan_digest_gate_ready,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready": ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready,
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready": ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready,
            "ci_workflow_release_readiness_drift_contract_smoke_ready": ci_workflow_release_readiness_drift_contract_smoke_ready,
            "request_history_status": request_status,
            "test_coverage_status": test_coverage_status,
            "test_coverage_percent": test_coverage_percent,
            "test_coverage_fail_under": 80.0,
            "test_coverage_gap": test_coverage_gap,
            "benchmark_history_status": benchmark_history_status,
            "benchmark_history_entries": benchmark_history_entries,
            "benchmark_history_ready": benchmark_history_ready,
            "benchmark_history_review": benchmark_history_review,
            "benchmark_history_blocked": benchmark_history_blocked,
            "benchmark_history_case_regressions": benchmark_history_case_regressions,
            "benchmark_history_generation_flag_regressions": benchmark_history_generation_flag_regressions,
            "benchmark_history_suite_design_non_comparison_ready_entries": benchmark_history_suite_design_non_comparison_ready_entries,
            "benchmark_history_design_comparison_changed_entries": benchmark_history_design_comparison_changed_entries,
            "benchmark_history_readiness_requirement_status": benchmark_history_readiness_requirement_status,
            "benchmark_history_readiness_requirement_exit_code": benchmark_history_readiness_requirement_exit_code,
            "benchmark_history_readiness_requirement_failed_reasons": benchmark_history_readiness_requirement_failed_reasons or [],
            "benchmark_history_model_quality_claim": benchmark_history_model_quality_claim,
            "benchmark_history_latest_boundary": benchmark_history_latest_boundary,
            "maturity_status": "pass",
            "ready_runs": 1,
            "missing_artifacts": 0,
            "fail_panel_count": fail_panels,
            "warn_panel_count": warn_panels,
        },
        "panels": [{"key": key, "title": key, "status": value, "detail": value} for key, value in panel_statuses.items()],
        "actions": ["all good"] if status == "ready" else ["fix release gate"],
        "evidence": [],
    }
    path = root / safe_name / "release_readiness.json"
    write_json(path, report)
    return path


class ReleaseReadinessComparisonTests(unittest.TestCase):
    def test_artifact_functions_are_reexported_from_comparison_module(self) -> None:
        self.assertIs(
            comparison_module.render_release_readiness_comparison_html,
            artifact_module.render_release_readiness_comparison_html,
        )
        self.assertIs(
            comparison_module.render_release_readiness_comparison_markdown,
            artifact_module.render_release_readiness_comparison_markdown,
        )
        self.assertIs(
            comparison_module.write_release_readiness_comparison_outputs,
            artifact_module.write_release_readiness_comparison_outputs,
        )
        self.assertIs(
            comparison_module.write_release_readiness_delta_csv,
            artifact_module.write_release_readiness_delta_csv,
        )

    def test_build_release_readiness_comparison_marks_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "v62", status="blocked", decision="block", gate_status="fail", fail_panels=1)
            current = make_readiness(root, "v63", status="ready", decision="ship", gate_status="pass")

            report = build_release_readiness_comparison([baseline, current], generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["readiness_count"], 2)
            self.assertEqual(report["summary"]["improved_count"], 1)
            self.assertEqual(report["summary"]["regressed_count"], 0)
            delta = report["deltas"][0]
            self.assertEqual(delta["delta_status"], "improved")
            self.assertGreater(delta["status_delta"], 0)
            self.assertIn("release_gate:fail->pass", delta["changed_panels"])
            self.assertEqual(delta["ci_workflow_failed_check_delta"], 0)
            self.assertEqual(delta["ci_workflow_order_violation_delta"], 0)
            self.assertEqual(delta["test_coverage_percent_delta"], 0)
            self.assertIn("Readiness improved", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_marks_regression_with_baseline_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked = make_readiness(root, "blocked", status="blocked", decision="block", gate_status="fail", fail_panels=1)
            ready = make_readiness(root, "ready", status="ready", decision="ship", gate_status="pass")

            report = build_release_readiness_comparison([blocked, ready], baseline_path=ready)

            self.assertEqual(report["baseline_path"], str(ready))
            self.assertEqual(report["summary"]["regressed_count"], 1)
            delta = report["deltas"][0]
            self.assertEqual(delta["delta_status"], "regressed")
            self.assertLess(delta["status_delta"], 0)
            self.assertIn("regressed", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_ci_workflow_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="pass",
                ci_workflow_status="fail",
                ci_workflow_failed_checks=2,
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["ci_workflow_regression_count"], 1)
            delta = report["deltas"][0]
            self.assertTrue(delta["ci_workflow_status_changed"])
            self.assertEqual(delta["ci_workflow_failed_check_delta"], 2)
            self.assertEqual(delta["ci_workflow_order_violation_delta"], 0)
            self.assertEqual(delta["ci_workflow_regression_reasons"], ["failed_checks_increased", "workflow_status_downgraded"])
            self.assertIn("ci_workflow_hygiene:pass->warn", delta["changed_panels"])
            self.assertEqual(
                report["summary"]["ci_workflow_regression_reason_counts"],
                {"failed_checks_increased": 1, "workflow_status_downgraded": 1},
            )
            self.assertIn("failed checks increased=1", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_ci_order_regression_without_status_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="ready",
                decision="ship",
                gate_status="pass",
                ci_workflow_status="pass",
                ci_workflow_failed_checks=0,
                ci_workflow_order_violations=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["ci_workflow_regression_count"], 1)
            self.assertEqual(report["summary"]["ci_workflow_order_regression_count"], 1)
            self.assertEqual(report["summary"]["max_abs_ci_workflow_order_violation_delta"], 1)
            self.assertEqual(report["rows"][1]["ci_workflow_order_violation_count"], 1)
            delta = report["deltas"][0]
            self.assertFalse(delta["ci_workflow_status_changed"])
            self.assertEqual(delta["ci_workflow_failed_check_delta"], 0)
            self.assertEqual(delta["ci_workflow_order_violation_delta"], 1)
            self.assertEqual(delta["ci_workflow_regression_reasons"], ["order_violations_increased"])
            self.assertIn("CI workflow order violation delta is 1", delta["explanation"])
            self.assertIn("order-violation deltas", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_drift_smoke_ready_regression_without_status_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="ready",
                decision="ship",
                gate_status="pass",
                ci_workflow_release_readiness_drift_contract_smoke_ready=True,
            )
            current = make_readiness(
                root,
                "current",
                status="ready",
                decision="ship",
                gate_status="pass",
                ci_workflow_release_readiness_drift_contract_smoke_ready=False,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["ci_workflow_regression_count"], 1)
            self.assertEqual(report["summary"]["ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count"], 1)
            self.assertEqual(report["summary"]["ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"], 1)
            self.assertTrue(report["rows"][0]["ci_workflow_release_readiness_drift_contract_smoke_ready"])
            self.assertFalse(report["rows"][1]["ci_workflow_release_readiness_drift_contract_smoke_ready"])
            delta = report["deltas"][0]
            self.assertEqual(delta["delta_status"], "same")
            self.assertFalse(delta["ci_workflow_status_changed"])
            self.assertTrue(delta["ci_workflow_release_readiness_drift_contract_smoke_ready_changed"])
            self.assertTrue(delta["ci_workflow_release_readiness_drift_contract_smoke_ready_regressed"])
            self.assertEqual(delta["ci_workflow_regression_reasons"], ["drift_contract_smoke_not_ready"])
            self.assertEqual(
                report["summary"]["ci_workflow_regression_reason_counts"],
                {"drift_contract_smoke_not_ready": 1},
            )
            self.assertIn("drift-contract smoke ready changed", delta["explanation"])
            self.assertIn("drift-contract smoke ready regressed", delta["explanation"])
            self.assertIn("drift-contract smoke readiness", delta["explanation"])
            self.assertIn("CI workflow hygiene regression", " ".join(report["recommendations"]))
            self.assertIn("drift-contract smoke readiness=1", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_boundary_plan_check_regression_without_status_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="ready",
                decision="ship",
                gate_status="pass",
                ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready=True,
            )
            current = make_readiness(
                root,
                "current",
                status="ready",
                decision="ship",
                gate_status="pass",
                ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready=False,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["ci_workflow_regression_count"], 1)
            self.assertEqual(
                report["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"],
                1,
            )
            self.assertEqual(
                report["summary"]["ci_workflow_regression_reason_counts"],
                {"boundary_gate_plan_check_not_ready": 1},
            )
            self.assertTrue(report["rows"][0]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertFalse(report["rows"][1]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            delta = report["deltas"][0]
            self.assertEqual(delta["delta_status"], "same")
            self.assertFalse(delta["ci_workflow_status_changed"])
            self.assertTrue(delta["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_changed"])
            self.assertTrue(delta["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed"])
            self.assertEqual(delta["ci_workflow_regression_reasons"], ["boundary_gate_plan_check_not_ready"])
            self.assertIn("boundary gate plan check ready changed", delta["explanation"])
            self.assertIn("boundary plan check readiness=1", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_test_coverage_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass", test_coverage_percent=90.17, test_coverage_gap=0.0)
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="pass",
                test_coverage_status="fail",
                test_coverage_percent=76.0,
                test_coverage_gap=4.0,
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["test_coverage_regression_count"], 1)
            delta = report["deltas"][0]
            self.assertTrue(delta["test_coverage_status_changed"])
            self.assertEqual(delta["test_coverage_percent_delta"], -14.17)
            self.assertEqual(delta["test_coverage_gap_delta"], 4)
            self.assertIn("test_coverage:pass->warn", delta["changed_panels"])
            self.assertIn("test coverage regression", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_benchmark_history_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="pass",
                benchmark_history_status="warn",
                benchmark_history_ready=0,
                benchmark_history_review=1,
                benchmark_history_case_regressions=2,
                benchmark_history_generation_flag_regressions=1,
                benchmark_history_model_quality_claim="not_claimed",
                benchmark_history_latest_boundary="tiny-smoke-plumbing-evidence",
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 1)
            self.assertEqual(report["rows"][1]["benchmark_history_status"], "warn")
            delta = report["deltas"][0]
            self.assertTrue(delta["benchmark_history_status_changed"])
            self.assertEqual(delta["benchmark_history_status_delta"], -1)
            self.assertEqual(delta["benchmark_history_ready_delta"], -1)
            self.assertEqual(delta["benchmark_history_case_regression_delta"], 2)
            self.assertEqual(delta["benchmark_history_generation_flag_regression_delta"], 1)
            self.assertTrue(delta["benchmark_history_latest_boundary_changed"])
            self.assertIn("benchmark_history:pass->warn", delta["changed_panels"])
            self.assertIn("Benchmark history status changed", delta["explanation"])
            self.assertIn("benchmark history regression", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_benchmark_requirement_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_status="pass",
                benchmark_history_ready=1,
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=["insufficient_ready_entries"],
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 1)
            self.assertEqual(report["rows"][1]["benchmark_history_status"], "pass")
            self.assertEqual(report["rows"][1]["benchmark_history_readiness_requirement_status"], "fail")
            delta = report["deltas"][0]
            self.assertFalse(delta["benchmark_history_status_changed"])
            self.assertTrue(delta["benchmark_history_readiness_requirement_status_changed"])
            self.assertEqual(delta["benchmark_history_readiness_requirement_exit_code_delta"], 1)
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_added_count"], 1)
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_added"], ["insufficient_ready_entries"])
            self.assertIn("Benchmark history readiness requirement changed", delta["explanation"])
            self.assertIn("added failed reason", delta["explanation"])
            self.assertIn("benchmark history regression", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_suite_design_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_status="pass",
                benchmark_history_suite_design_non_comparison_ready_entries=2,
                benchmark_history_design_comparison_changed_entries=3,
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_suite_design_non_comparison_ready_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_suite_design_non_comparison_ready_regression_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_design_comparison_changed_delta_count"], 1)
            self.assertEqual(report["rows"][1]["benchmark_history_suite_design_non_comparison_ready_entries"], 2)
            self.assertEqual(report["rows"][1]["benchmark_history_design_comparison_changed_entries"], 3)
            delta = report["deltas"][0]
            self.assertEqual(delta["benchmark_history_suite_design_non_comparison_ready_entries_delta"], 2)
            self.assertEqual(delta["benchmark_history_design_comparison_changed_entries_delta"], 3)
            self.assertIn("benchmark_history:pass->warn", delta["changed_panels"])
            self.assertIn("suite-design not-ready delta is 2", delta["explanation"])
            self.assertIn("design-comparison changed delta is 3", delta["explanation"])
            self.assertIn("suite-design not-ready regression", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_flags_benchmark_requirement_reason_regression_without_status_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="ready",
                decision="ship",
                gate_status="pass",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=["insufficient_ready_entries"],
            )
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_status="pass",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=[
                    "insufficient_ready_entries",
                    "tiny_smoke_only",
                ],
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_added_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_added"], ["tiny_smoke_only"])
            delta = report["deltas"][0]
            self.assertFalse(delta["benchmark_history_readiness_requirement_status_changed"])
            self.assertEqual(delta["benchmark_history_readiness_requirement_exit_code_delta"], 0)
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_added"], ["tiny_smoke_only"])
            self.assertIn("tiny_smoke_only", delta["explanation"])
            self.assertIn("benchmark history regression", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_tracks_benchmark_requirement_reason_removal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=[
                    "insufficient_ready_entries",
                    "tiny_smoke_only",
                ],
                warn_panels=1,
            )
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=["insufficient_ready_entries"],
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 0)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_added_count"], 0)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_removed_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_removed"], ["tiny_smoke_only"])
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"], 0)
            self.assertEqual(
                report["summary"]["benchmark_history_readiness_requirement_failed_reason_drift_status_counts"],
                {"recovered": 1},
            )
            delta = report["deltas"][0]
            self.assertFalse(delta["benchmark_history_readiness_requirement_status_changed"])
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_added"], [])
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_removed"], ["tiny_smoke_only"])
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_drift_status"], "recovered")
            self.assertIn("removed failed reason", delta["explanation"])
            self.assertIn("recovery evidence", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_tracks_mixed_benchmark_requirement_reason_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=[
                    "insufficient_ready_entries",
                    "legacy_fixture_gap",
                ],
                warn_panels=1,
            )
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=[
                    "insufficient_ready_entries",
                    "tiny_smoke_only",
                ],
                warn_panels=1,
            )

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_added_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_removed_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_added"], ["tiny_smoke_only"])
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_removed"], ["legacy_fixture_gap"])
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"], 0)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"], 1)
            self.assertEqual(
                report["summary"]["benchmark_history_readiness_requirement_failed_reason_drift_status_counts"],
                {"mixed": 1},
            )
            delta = report["deltas"][0]
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_drift_status"], "mixed")
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_added"], ["tiny_smoke_only"])
            self.assertEqual(delta["benchmark_history_readiness_requirement_failed_reason_removed"], ["legacy_fixture_gap"])
            self.assertIn("mixed benchmark readiness failed-reason drift", " ".join(report["recommendations"]))

    def test_build_release_readiness_comparison_tracks_benchmark_history_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(
                root,
                "baseline",
                status="review",
                decision="review",
                gate_status="pass",
                benchmark_history_status="warn",
                benchmark_history_ready=0,
                benchmark_history_review=1,
                benchmark_history_case_regressions=1,
                warn_panels=1,
            )
            current = make_readiness(root, "current", status="ready", decision="ship", gate_status="pass")

            report = build_release_readiness_comparison([baseline, current])

            self.assertEqual(report["summary"]["benchmark_history_delta_count"], 1)
            self.assertEqual(report["summary"]["benchmark_history_regression_count"], 0)
            delta = report["deltas"][0]
            self.assertEqual(delta["benchmark_history_status_delta"], 1)
            self.assertEqual(delta["benchmark_history_ready_delta"], 1)
            self.assertEqual(delta["benchmark_history_case_regression_delta"], -1)
            self.assertIn("Readiness improved", " ".join(report["recommendations"]))

    def test_write_release_readiness_comparison_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="review", decision="review", gate_status="pass", request_status="watch", warn_panels=1)
            current = make_readiness(root, "current", status="ready", decision="ship", gate_status="pass")
            report = build_release_readiness_comparison([baseline, current])

            outputs = write_release_readiness_comparison_outputs(report, root / "comparison")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["delta_csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("readiness_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("ci_workflow_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("ci_workflow_order_violation_count", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn(
                "ci_workflow_tiny_scorecard_plan_digest_gate_ready",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "ci_workflow_release_readiness_drift_contract_smoke_ready",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("test_coverage_percent", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("benchmark_history_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn(
                "benchmark_history_suite_design_non_comparison_ready_entries",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("benchmark_history_readiness_requirement_status", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("changed_panels", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("ci_workflow_failed_check_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("ci_workflow_order_violation_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn(
                "ci_workflow_release_readiness_drift_contract_smoke_ready_regressed",
                Path(outputs["delta_csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regressed",
                Path(outputs["delta_csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("ci_workflow_regression_reasons", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("test_coverage_gap_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("benchmark_history_case_regression_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn(
                "benchmark_history_suite_design_non_comparison_ready_entries_delta",
                Path(outputs["delta_csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("benchmark_history_readiness_requirement_exit_code_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("## Readiness Matrix", markdown)
            self.assertIn("CI boundary plan", markdown)
            self.assertIn("CI boundary plan regressed", markdown)
            self.assertIn("CI drift smoke ready", markdown)
            self.assertIn("CI regression reasons", markdown)
            self.assertIn("Suite-design not-ready", markdown)
            self.assertIn("CI boundary plan", html)
            self.assertIn("CI boundary plan regressed", html)
            self.assertIn("CI drift smoke ready", html)
            self.assertIn("CI regression reasons", html)
            self.assertIn("Suite-design not-ready", html)

    def test_compare_release_readiness_cli_prints_suite_design_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "baseline", status="ready", decision="ship", gate_status="pass")
            current = make_readiness(
                root,
                "current",
                status="review",
                decision="review",
                gate_status="warn",
                benchmark_history_suite_design_non_comparison_ready_entries=4,
                benchmark_history_design_comparison_changed_entries=5,
                warn_panels=1,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "compare_release_readiness.py"),
                    "--readiness",
                    str(baseline),
                    "--readiness",
                    str(current),
                    "--out-dir",
                    str(root / "comparison"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("benchmark_history_suite_design_non_comparison_ready_delta_count=1", completed.stdout)
            self.assertIn("benchmark_history_suite_design_non_comparison_ready_regression_count=1", completed.stdout)
            self.assertIn("benchmark_history_design_comparison_changed_delta_count=1", completed.stdout)
            self.assertIn("ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count=0", completed.stdout)
            self.assertIn("benchmark_history_suite_design=current:4:5", completed.stdout)

    def test_renderers_escape_release_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_readiness(root, "<baseline>", status="ready", decision="ship", gate_status="pass")
            report = build_release_readiness_comparison([baseline], title="<Comparison>")

            html = render_release_readiness_comparison_html(report)
            markdown = render_release_readiness_comparison_markdown(report)

            self.assertIn("&lt;Comparison&gt;", html)
            self.assertIn("&lt;baseline&gt;", html)
            self.assertNotIn("<h1><Comparison>", html)
            self.assertIn("<baseline>", markdown)


if __name__ == "__main__":
    unittest.main()
