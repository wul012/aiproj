from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import release_readiness as release_readiness_facade
from minigpt import release_readiness_artifacts
from minigpt.release_readiness import (
    build_release_readiness_dashboard,
    render_release_readiness_html,
    write_release_readiness_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_readiness_inputs(
    root: Path,
    *,
    release_name: str = "v62-demo",
    include_gate: bool = True,
    gate_status: str = "pass",
    gate_decision: str = "approved",
    benchmark_history_status: str = "pass",
    benchmark_history_ready: int = 1,
    benchmark_history_review: int = 0,
    benchmark_history_blocked: int = 0,
    benchmark_history_case_regressions: int = 0,
    benchmark_history_suite_design_non_comparison_ready_entries: int = 0,
    benchmark_history_design_comparison_changed_entries: int = 0,
    benchmark_history_readiness_requirement_status: str = "pass",
    benchmark_history_readiness_requirement_exit_code: int = 0,
    benchmark_history_readiness_requirement_failed_reasons: list[str] | None = None,
    benchmark_history_model_quality_claim: str = "candidate_evidence",
    benchmark_history_latest_boundary: str = "standard-benchmark-candidate-evidence",
    include_request_history: bool = True,
    include_ci_workflow: bool = True,
    ci_workflow_status: str = "pass",
    include_test_coverage: bool = True,
    test_coverage_status: str = "pass",
) -> Path:
    runs = root / "runs"
    registry_path = runs / "registry" / "registry.json"
    audit_path = runs / "audit" / "project_audit.json"
    request_path = runs / "request-history-summary" / "request_history_summary.json"
    gate_path = runs / "release-gate" / "gate_report.json"
    maturity_path = runs / "maturity-summary" / "maturity_summary.json"
    ci_workflow_path = runs / "ci-workflow-hygiene" / "ci_workflow_hygiene.json"
    coverage_path = runs / "test-coverage" / "test_coverage_report.json"
    bundle_path = runs / "release-bundle" / "release_bundle.json"
    artifact_path = runs / "request-history-summary" / "request_history_summary.html"
    ci_artifact_path = runs / "ci-workflow-hygiene" / "ci_workflow_hygiene.html"
    coverage_artifact_path = runs / "test-coverage" / "test_coverage_report.html"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("<html></html>", encoding="utf-8")
    ci_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    ci_artifact_path.write_text("<html></html>", encoding="utf-8")
    coverage_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_artifact_path.write_text("<html></html>", encoding="utf-8")
    benchmark_gate_check_status = (
        "warn"
        if benchmark_history_status == "pass" and benchmark_history_suite_design_non_comparison_ready_entries > 0
        else benchmark_history_status
    )
    artifact_rows = []
    if include_request_history:
        artifact_rows.append(
            {
                "key": "request_history_summary_html",
                "title": "Request history summary HTML",
                "path": str(artifact_path),
                "kind": "HTML",
                "exists": True,
                "size_bytes": artifact_path.stat().st_size,
            }
        )
    if include_ci_workflow:
        artifact_rows.append(
            {
                "key": "ci_workflow_hygiene_html",
                "title": "CI workflow hygiene HTML",
                "path": str(ci_artifact_path),
                "kind": "HTML",
                "exists": True,
                "size_bytes": ci_artifact_path.stat().st_size,
            }
        )
    if include_test_coverage:
        artifact_rows.append(
            {
                "key": "test_coverage_report_html",
                "title": "Test coverage report HTML",
                "path": str(coverage_artifact_path),
                "kind": "HTML",
                "exists": True,
                "size_bytes": coverage_artifact_path.stat().st_size,
            }
        )

    write_json(
        registry_path,
        {
            "run_count": 1,
            "best_by_best_val_loss": {"name": "candidate", "best_val_loss": 0.8},
            "runs": [{"name": "candidate"}],
        },
    )
    write_json(
        audit_path,
        {
            "summary": {
                "overall_status": "pass",
                "score_percent": 100.0,
                "pass_count": 14,
                "warn_count": 0,
                "fail_count": 0,
                "ready_runs": 1,
                "request_history_status": "pass" if include_request_history else None,
                "request_history_records": 4 if include_request_history else None,
                "benchmark_history_status": benchmark_history_status,
                "benchmark_history_entries": 1,
                "benchmark_history_ready": benchmark_history_ready,
                "benchmark_history_review": benchmark_history_review,
                "benchmark_history_blocked": benchmark_history_blocked,
                "benchmark_history_case_regressions": benchmark_history_case_regressions,
                "benchmark_history_generation_flag_regressions": 0,
                "benchmark_history_suite_design_non_comparison_ready_entries": benchmark_history_suite_design_non_comparison_ready_entries,
                "benchmark_history_design_comparison_changed_entries": benchmark_history_design_comparison_changed_entries,
                "benchmark_history_readiness_requirement_status": benchmark_history_readiness_requirement_status,
                "benchmark_history_readiness_requirement_exit_code": benchmark_history_readiness_requirement_exit_code,
                "benchmark_history_readiness_requirement_failed_reasons": benchmark_history_readiness_requirement_failed_reasons or [],
                "benchmark_history_model_quality_claim": benchmark_history_model_quality_claim,
                "benchmark_history_latest_boundary": benchmark_history_latest_boundary,
                "ci_workflow_status": ci_workflow_status if include_ci_workflow else None,
                "ci_workflow_failed_checks": 0 if ci_workflow_status == "pass" else 1,
                "ci_workflow_node24_actions": 2 if include_ci_workflow else None,
                "ci_workflow_required_order_count": 1 if include_ci_workflow else None,
                "ci_workflow_order_violation_count": (0 if ci_workflow_status == "pass" else 1) if include_ci_workflow else None,
                "ci_workflow_tiny_scorecard_plan_digest_gate_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_archived_path_portability_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": (
                    ci_workflow_status == "pass" if include_ci_workflow else None
                ),
                "ci_workflow_release_readiness_drift_contract_smoke_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "test_coverage_status": test_coverage_status if include_test_coverage else None,
                "test_coverage_percent": 90.17 if include_test_coverage else None,
                "test_coverage_fail_under": 80.0 if include_test_coverage else None,
                "test_coverage_gap": 0.0 if test_coverage_status == "pass" else 8.0,
            },
            "checks": [
                {"id": "ready_run", "status": "pass", "title": "At least one ready run", "detail": "1 ready run."},
                {"id": "request_history_summary", "status": "pass", "title": "Request history summary is clean", "detail": "status=pass."},
                {
                    "id": "benchmark_history",
                    "status": benchmark_gate_check_status,
                    "title": "Benchmark history is audit-ready",
                    "detail": (
                        f"status={benchmark_history_status}; "
                        f"suite_design_not_ready={benchmark_history_suite_design_non_comparison_ready_entries}; "
                        f"design_comparison_changed={benchmark_history_design_comparison_changed_entries}."
                    ),
                },
                {"id": "ci_workflow_hygiene", "status": ci_workflow_status, "title": "CI workflow hygiene is clean", "detail": f"status={ci_workflow_status}."},
                {"id": "test_coverage_report", "status": test_coverage_status, "title": "Test coverage gate is clean", "detail": f"status={test_coverage_status}."},
            ],
            "recommendations": ["All audit checks passed."],
        },
    )
    if include_request_history:
        write_json(
            request_path,
            {
                "summary": {
                    "status": "pass",
                    "total_log_records": 4,
                    "invalid_record_count": 0,
                    "timeout_rate": 0.0,
                    "bad_request_rate": 0.0,
                    "error_rate": 0.0,
                }
            },
        )
    if include_ci_workflow:
        write_json(
            ci_workflow_path,
            {
                "summary": {
                    "status": ci_workflow_status,
                    "decision": "keep" if ci_workflow_status == "pass" else "review_workflow_hygiene",
                    "check_count": 4,
                    "failed_check_count": 0 if ci_workflow_status == "pass" else 1,
                    "node24_native_action_count": 2,
                    "required_order_count": 1,
                    "order_violation_count": 0 if ci_workflow_status == "pass" else 1,
                    "tiny_scorecard_plan_digest_gate_present": ci_workflow_status == "pass",
                    "tiny_scorecard_plan_digest_gate_order_ready": ci_workflow_status == "pass",
                    "tiny_scorecard_plan_digest_gate_ready": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_check_present": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_check_order_ready": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_check_ready": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_plan_check_present": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_plan_check_order_ready": ci_workflow_status == "pass",
                    "baseline_candidate_threshold_boundary_gate_plan_check_ready": ci_workflow_status == "pass",
                    "archived_path_portability_check_present": ci_workflow_status == "pass",
                    "archived_path_portability_check_order_ready": ci_workflow_status == "pass",
                    "archived_path_portability_check_ready": ci_workflow_status == "pass",
                    "promoted_seed_receipt_contract_failure_smoke_plan_check_present": ci_workflow_status == "pass",
                    "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": ci_workflow_status == "pass",
                    "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": ci_workflow_status == "pass",
                    "release_readiness_drift_contract_smoke_present": ci_workflow_status == "pass",
                    "release_readiness_drift_contract_smoke_order_ready": ci_workflow_status == "pass",
                    "release_readiness_drift_contract_smoke_ready": ci_workflow_status == "pass",
                    "legacy_node_actions": 0 if ci_workflow_status == "pass" else 1,
                },
                "checks": [
                    {
                        "id": "actions_node24_native",
                        "status": ci_workflow_status,
                        "detail": "all actions are Node 24 native" if ci_workflow_status == "pass" else "legacy action found",
                    }
                ],
            },
        )
    if include_test_coverage:
        write_json(
            coverage_path,
            {
                "summary": {
                    "status": test_coverage_status,
                    "decision": "continue_with_coverage_gate" if test_coverage_status == "pass" else "improve_test_coverage",
                    "line_coverage_percent": 90.17 if test_coverage_status == "pass" else 72.0,
                    "fail_under": 80.0,
                    "coverage_gap": 0.0 if test_coverage_status == "pass" else 8.0,
                }
            },
        )
    if include_gate:
        request_gate_status = "fail" if gate_status == "fail" else "pass"
        write_json(
            gate_path,
            {
                "release_name": release_name,
                "summary": {
                    "gate_status": gate_status,
                    "decision": gate_decision,
                    "pass_count": 12 if gate_status == "pass" else 11,
                    "warn_count": 0,
                    "fail_count": 0 if gate_status == "pass" else 1,
                    "release_status": "release-ready",
                    "audit_status": "pass",
                    "audit_score_percent": 100.0,
                    "ready_runs": 1,
                    "test_coverage_status": test_coverage_status if include_test_coverage else None,
                    "test_coverage_percent": 90.17 if include_test_coverage else None,
                    "test_coverage_fail_under": 80.0 if include_test_coverage else None,
                    "test_coverage_gap": 0.0 if test_coverage_status == "pass" else 8.0,
                    "benchmark_history_status": benchmark_history_status,
                    "benchmark_history_entries": 1,
                    "benchmark_history_ready": benchmark_history_ready,
                    "benchmark_history_review": benchmark_history_review,
                    "benchmark_history_blocked": benchmark_history_blocked,
                    "benchmark_history_case_regressions": benchmark_history_case_regressions,
                    "benchmark_history_generation_flag_regressions": 0,
                    "benchmark_history_suite_design_non_comparison_ready_entries": benchmark_history_suite_design_non_comparison_ready_entries,
                    "benchmark_history_design_comparison_changed_entries": benchmark_history_design_comparison_changed_entries,
                    "benchmark_history_readiness_requirement_status": benchmark_history_readiness_requirement_status,
                    "benchmark_history_readiness_requirement_exit_code": benchmark_history_readiness_requirement_exit_code,
                    "benchmark_history_readiness_requirement_failed_reasons": benchmark_history_readiness_requirement_failed_reasons or [],
                    "benchmark_history_model_quality_claim": benchmark_history_model_quality_claim,
                    "benchmark_history_latest_boundary": benchmark_history_latest_boundary,
                },
                "checks": [
                    {
                        "id": "request_history_summary_audit_check",
                        "status": request_gate_status,
                        "title": "Request history summary audit check passed",
                        "detail": "request_history_summary=pass."
                        if request_gate_status == "pass"
                        else "missing required audit check: request_history_summary.",
                    },
                    {
                        "id": "benchmark_history_gate_check",
                        "status": benchmark_gate_check_status,
                        "title": "Benchmark history release evidence passed",
                        "detail": (
                            f"benchmark_history={benchmark_history_status}; "
                            f"case_regressions={benchmark_history_case_regressions}; "
                            f"suite_design_not_ready={benchmark_history_suite_design_non_comparison_ready_entries}; "
                            f"design_comparison_changed={benchmark_history_design_comparison_changed_entries}; "
                            f"readiness_requirement={benchmark_history_readiness_requirement_status}; "
                            f"readiness_exit={benchmark_history_readiness_requirement_exit_code}; "
                            f"latest_boundary={benchmark_history_latest_boundary}."
                        ),
                    },
                ],
            },
        )
    write_json(
        maturity_path,
        {
            "summary": {
                "overall_status": "pass",
                "current_version": 62,
                "average_maturity_level": 4.6,
            }
        },
    )
    write_json(
        bundle_path,
        {
            "schema_version": 1,
            "release_name": release_name,
            "summary": {
                "release_status": "release-ready",
                "audit_status": "pass",
                "audit_score_percent": 100.0,
                "ready_runs": 1,
                "request_history_status": "pass" if include_request_history else None,
                "request_history_records": 4 if include_request_history else None,
                "benchmark_history_status": benchmark_history_status,
                "benchmark_history_entries": 1,
                "benchmark_history_ready": benchmark_history_ready,
                "benchmark_history_review": benchmark_history_review,
                "benchmark_history_blocked": benchmark_history_blocked,
                "benchmark_history_case_regressions": benchmark_history_case_regressions,
                "benchmark_history_generation_flag_regressions": 0,
                "benchmark_history_suite_design_non_comparison_ready_entries": benchmark_history_suite_design_non_comparison_ready_entries,
                "benchmark_history_design_comparison_changed_entries": benchmark_history_design_comparison_changed_entries,
                "benchmark_history_readiness_requirement_status": benchmark_history_readiness_requirement_status,
                "benchmark_history_readiness_requirement_exit_code": benchmark_history_readiness_requirement_exit_code,
                "benchmark_history_readiness_requirement_failed_reasons": benchmark_history_readiness_requirement_failed_reasons or [],
                "benchmark_history_model_quality_claim": benchmark_history_model_quality_claim,
                "benchmark_history_latest_boundary": benchmark_history_latest_boundary,
                "ci_workflow_status": ci_workflow_status if include_ci_workflow else None,
                "ci_workflow_failed_checks": 0 if ci_workflow_status == "pass" else 1,
                "ci_workflow_node24_actions": 2 if include_ci_workflow else None,
                "ci_workflow_required_order_count": 1 if include_ci_workflow else None,
                "ci_workflow_order_violation_count": (0 if ci_workflow_status == "pass" else 1) if include_ci_workflow else None,
                "ci_workflow_tiny_scorecard_plan_digest_gate_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_archived_path_portability_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": (
                    ci_workflow_status == "pass" if include_ci_workflow else None
                ),
                "ci_workflow_release_readiness_drift_contract_smoke_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "test_coverage_status": test_coverage_status if include_test_coverage else None,
                "test_coverage_percent": 90.17 if include_test_coverage else None,
                "test_coverage_fail_under": 80.0 if include_test_coverage else None,
                "test_coverage_gap": 0.0 if test_coverage_status == "pass" else 8.0,
                "available_artifacts": len(artifact_rows),
                "missing_artifacts": 0,
            },
            "inputs": {
                "registry_path": str(registry_path),
                "project_audit_path": str(audit_path),
                "request_history_summary_path": str(request_path) if include_request_history else None,
                "ci_workflow_hygiene_path": str(ci_workflow_path) if include_ci_workflow else None,
                "test_coverage_report_path": str(coverage_path) if include_test_coverage else None,
            },
            "artifacts": artifact_rows,
            "ci_workflow_context": {
                "status": ci_workflow_status if include_ci_workflow else None,
                "failed_check_count": 0 if ci_workflow_status == "pass" else 1,
                "node24_native_action_count": 2 if include_ci_workflow else None,
                "required_order_count": 1 if include_ci_workflow else None,
                "order_violation_count": (0 if ci_workflow_status == "pass" else 1) if include_ci_workflow else None,
                "tiny_scorecard_plan_digest_gate_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "baseline_candidate_threshold_boundary_gate_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "baseline_candidate_threshold_boundary_gate_plan_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "archived_path_portability_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "release_readiness_drift_contract_smoke_ready": ci_workflow_status == "pass" if include_ci_workflow else None,
                "path": str(ci_workflow_path) if include_ci_workflow else None,
            },
            "test_coverage_context": {
                "status": test_coverage_status if include_test_coverage else None,
                "line_coverage_percent": 90.17 if include_test_coverage else None,
                "fail_under": 80.0 if include_test_coverage else None,
                "coverage_gap": 0.0 if test_coverage_status == "pass" else 8.0,
                "path": str(coverage_path) if include_test_coverage else None,
            },
            "recommendations": ["Release evidence is complete."],
        },
    )
    return bundle_path


class ReleaseReadinessTests(unittest.TestCase):
    def test_build_release_readiness_dashboard_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(root)

            report = build_release_readiness_dashboard(bundle_path, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["readiness_status"], "ready")
            self.assertEqual(report["summary"]["decision"], "ship")
            self.assertEqual(report["summary"]["gate_status"], "pass")
            self.assertEqual(report["summary"]["request_history_status"], "pass")
            self.assertEqual(report["summary"]["ci_workflow_status"], "pass")
            self.assertEqual(report["summary"]["ci_workflow_failed_checks"], 0)
            self.assertEqual(report["summary"]["ci_workflow_node24_actions"], 2)
            self.assertEqual(report["summary"]["ci_workflow_required_order_count"], 1)
            self.assertEqual(report["summary"]["ci_workflow_order_violation_count"], 0)
            self.assertTrue(report["summary"]["ci_workflow_tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(report["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_archived_path_portability_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_release_readiness_drift_contract_smoke_ready"])
            self.assertEqual(report["summary"]["test_coverage_status"], "pass")
            self.assertEqual(report["summary"]["test_coverage_percent"], 90.17)
            self.assertEqual(report["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(report["summary"]["benchmark_history_ready"], 1)
            self.assertEqual(report["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 0)
            self.assertEqual(report["summary"]["benchmark_history_design_comparison_changed_entries"], 0)
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_status"], "pass")
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_exit_code"], 0)
            self.assertEqual({panel["status"] for panel in report["panels"]}, {"pass"})
            self.assertIn("ci_workflow_hygiene", {panel["key"] for panel in report["panels"]})
            ci_panel = next(panel for panel in report["panels"] if panel["key"] == "ci_workflow_hygiene")
            self.assertIn("boundary_gate_plan_check_ready=True", ci_panel["detail"])
            self.assertIn("archived_path_portability_check_ready=True", ci_panel["detail"])
            self.assertIn("receipt_failure_smoke_plan_check_ready=True", ci_panel["detail"])
            self.assertIn("drift_contract_smoke_ready=True", ci_panel["detail"])
            self.assertIn("test_coverage", {panel["key"] for panel in report["panels"]})
            self.assertIn("benchmark_history", {panel["key"] for panel in report["panels"]})
            self.assertIn("All readiness panels are clean", " ".join(report["actions"]))

    def test_build_release_readiness_uses_bundle_ci_context_when_report_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(root)
            (root / "runs" / "ci-workflow-hygiene" / "ci_workflow_hygiene.json").unlink()

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "ready")
            self.assertEqual(report["summary"]["ci_workflow_status"], "pass")
            self.assertEqual(report["summary"]["ci_workflow_node24_actions"], 2)
            self.assertEqual(report["summary"]["ci_workflow_order_violation_count"], 0)
            self.assertTrue(report["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_archived_path_portability_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(report["summary"]["ci_workflow_release_readiness_drift_contract_smoke_ready"])
            ci_panel = next(panel for panel in report["panels"] if panel["key"] == "ci_workflow_hygiene")
            self.assertEqual(ci_panel["status"], "pass")
            self.assertIn("order_violations=0", ci_panel["detail"])
            self.assertIn("boundary_gate_plan_check_ready=True", ci_panel["detail"])
            self.assertIn("archived_path_portability_check_ready=True", ci_panel["detail"])
            self.assertIn("receipt_failure_smoke_plan_check_ready=True", ci_panel["detail"])
            self.assertIn("drift_contract_smoke_ready=True", ci_panel["detail"])
            self.assertIn("source=bundle summary/context", ci_panel["detail"])

    def test_build_release_readiness_uses_bundle_coverage_context_when_report_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(root)
            (root / "runs" / "test-coverage" / "test_coverage_report.json").unlink()

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "ready")
            self.assertEqual(report["summary"]["test_coverage_status"], "pass")
            self.assertEqual(report["summary"]["test_coverage_percent"], 90.17)
            coverage_panel = next(panel for panel in report["panels"] if panel["key"] == "test_coverage")
            self.assertEqual(coverage_panel["status"], "pass")
            self.assertIn("source=bundle summary/context", coverage_panel["detail"])

    def test_build_release_readiness_reviews_benchmark_history_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(
                Path(tmp),
                gate_status="warn",
                gate_decision="needs-review",
                benchmark_history_status="warn",
                benchmark_history_ready=0,
                benchmark_history_review=1,
                benchmark_history_case_regressions=1,
                benchmark_history_model_quality_claim="not_claimed",
                benchmark_history_latest_boundary="tiny-smoke-plumbing-evidence",
            )

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(report["summary"]["benchmark_history_case_regressions"], 1)
            self.assertEqual(report["summary"]["benchmark_history_latest_boundary"], "tiny-smoke-plumbing-evidence")
            panel = next(panel for panel in report["panels"] if panel["key"] == "benchmark_history")
            self.assertEqual(panel["status"], "warn")
            self.assertIn("case_regressions=1", panel["detail"])
            self.assertIn("gate_check=warn", panel["detail"])
            self.assertIn("Gate warn: benchmark_history_gate_check", " ".join(report["actions"]))

    def test_build_release_readiness_reviews_benchmark_requirement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(
                Path(tmp),
                gate_status="warn",
                gate_decision="needs-review",
                benchmark_history_status="pass",
                benchmark_history_ready=1,
                benchmark_history_readiness_requirement_status="fail",
                benchmark_history_readiness_requirement_exit_code=1,
                benchmark_history_readiness_requirement_failed_reasons=["insufficient_ready_entries"],
            )

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_status"], "fail")
            self.assertEqual(report["summary"]["benchmark_history_readiness_requirement_exit_code"], 1)
            self.assertEqual(
                report["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["insufficient_ready_entries"],
            )
            panel = next(panel for panel in report["panels"] if panel["key"] == "benchmark_history")
            self.assertEqual(panel["status"], "warn")
            self.assertIn("readiness_requirement=fail", panel["detail"])
            self.assertIn("readiness_failed_reasons=insufficient_ready_entries", panel["detail"])

    def test_build_release_readiness_reviews_suite_design_history_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(
                Path(tmp),
                gate_status="warn",
                gate_decision="needs-review",
                benchmark_history_status="pass",
                benchmark_history_suite_design_non_comparison_ready_entries=1,
                benchmark_history_design_comparison_changed_entries=2,
            )

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(report["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 1)
            self.assertEqual(report["summary"]["benchmark_history_design_comparison_changed_entries"], 2)
            panel = next(panel for panel in report["panels"] if panel["key"] == "benchmark_history")
            self.assertEqual(panel["status"], "warn")
            self.assertIn("suite_design_not_ready=1", panel["detail"])
            self.assertIn("design_comparison_changed=2", panel["detail"])
            self.assertIn("Gate warn: benchmark_history_gate_check", " ".join(report["actions"]))

    def test_build_release_readiness_uses_bundle_benchmark_history_when_gate_summary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(root, benchmark_history_status="warn", benchmark_history_ready=0)
            gate_path = root / "runs" / "release-gate" / "gate_report.json"
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            gate["summary"].pop("benchmark_history_status", None)
            gate["summary"].pop("benchmark_history_ready", None)
            gate["checks"] = [check for check in gate["checks"] if check.get("id") != "benchmark_history_gate_check"]
            write_json(gate_path, gate)

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["benchmark_history_status"], "warn")
            panel = next(panel for panel in report["panels"] if panel["key"] == "benchmark_history")
            self.assertEqual(panel["status"], "warn")
            self.assertIn("ready=0", panel["detail"])

    def test_build_release_readiness_dashboard_incomplete_without_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(Path(tmp), include_gate=False)

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "incomplete")
            gate_panel = next(panel for panel in report["panels"] if panel["key"] == "release_gate")
            self.assertEqual(gate_panel["status"], "warn")
            self.assertIn("Review warning panel", " ".join(report["actions"]))

    def test_build_release_readiness_dashboard_blocks_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(Path(tmp), gate_status="fail", gate_decision="blocked")

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "blocked")
            gate_panel = next(panel for panel in report["panels"] if panel["key"] == "release_gate")
            self.assertEqual(gate_panel["status"], "fail")
            self.assertIn("Gate fail: request_history_summary_audit_check", " ".join(report["actions"]))

    def test_build_release_readiness_reviews_failed_ci_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(Path(tmp), ci_workflow_status="fail")

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["decision"], "review")
            self.assertEqual(report["summary"]["ci_workflow_status"], "fail")
            self.assertEqual(report["summary"]["ci_workflow_order_violation_count"], 1)
            ci_panel = next(panel for panel in report["panels"] if panel["key"] == "ci_workflow_hygiene")
            self.assertEqual(ci_panel["status"], "warn")
            self.assertIn("order_violations=1", ci_panel["detail"])
            self.assertIn("Review warning panel: CI Workflow Hygiene", " ".join(report["actions"]))

    def test_build_release_readiness_reviews_failed_test_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_readiness_inputs(Path(tmp), test_coverage_status="fail")

            report = build_release_readiness_dashboard(bundle_path)

            self.assertEqual(report["summary"]["readiness_status"], "review")
            self.assertEqual(report["summary"]["decision"], "review")
            self.assertEqual(report["summary"]["test_coverage_status"], "fail")
            coverage_panel = next(panel for panel in report["panels"] if panel["key"] == "test_coverage")
            self.assertEqual(coverage_panel["status"], "warn")
            self.assertIn("Review warning panel: Test Coverage Gate", " ".join(report["actions"]))

    def test_write_release_readiness_outputs_and_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(root, release_name="<script>")
            report = build_release_readiness_dashboard(bundle_path, title="<Readiness>")

            outputs = write_release_readiness_outputs(report, root / "readiness")
            html = render_release_readiness_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Panels", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Test coverage", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI receipt failure-smoke plan check", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history suite-design not-ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("&lt;Readiness&gt;", html)
            self.assertIn("Bench design review", html)
            self.assertIn("CI receipt plan", html)
            self.assertNotIn("<h1><Readiness>", html)

    def test_build_release_readiness_cli_prints_suite_design_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_readiness_inputs(
                root,
                gate_status="warn",
                gate_decision="needs-review",
                benchmark_history_suite_design_non_comparison_ready_entries=3,
                benchmark_history_design_comparison_changed_entries=4,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_release_readiness.py"),
                    "--bundle",
                    str(bundle_path),
                    "--out-dir",
                    str(root / "readiness"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("benchmark_history_suite_design_non_comparison_ready_entries=3", completed.stdout)
            self.assertIn("benchmark_history_design_comparison_changed_entries=4", completed.stdout)
            self.assertIn("ci_workflow_archived_path_portability_check_ready=True", completed.stdout)
            self.assertIn("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True", completed.stdout)
            self.assertIn("readiness_status=review", completed.stdout)

    def test_release_readiness_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(release_readiness_facade.render_release_readiness_html, release_readiness_artifacts.render_release_readiness_html)
        self.assertIs(release_readiness_facade.render_release_readiness_markdown, release_readiness_artifacts.render_release_readiness_markdown)
        self.assertIs(release_readiness_facade.write_release_readiness_outputs, release_readiness_artifacts.write_release_readiness_outputs)
        self.assertIs(release_readiness_facade.write_release_readiness_json, release_readiness_artifacts.write_release_readiness_json)


if __name__ == "__main__":
    unittest.main()
