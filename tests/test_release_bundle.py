from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt import release_bundle_artifacts
from minigpt import release_bundle as release_bundle_facade
from minigpt.release_bundle import build_release_bundle, render_release_bundle_html, write_release_bundle_outputs


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_release_inputs(root: Path, name: str = "candidate") -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    run_dir = root / "run-a"
    run_dir.mkdir()
    registry_dir = root / "registry"
    model_dir = root / "model-card"
    audit_dir = root / "audit"
    request_dir = root / "request-history-summary"
    history_dir = root / "benchmark-history"
    ci_dir = root / "ci-workflow-hygiene"
    coverage_dir = root / "test-coverage"
    registry = {
        "run_count": 1,
        "best_by_best_val_loss": {"name": name, "path": str(run_dir), "best_val_loss": 0.8},
        "loss_leaderboard": [{"rank": 1, "name": name, "path": str(run_dir), "best_val_loss": 0.8, "best_val_loss_delta": 0.0}],
        "runs": [
            {
                "name": name,
                "path": str(run_dir),
                "best_val_loss_rank": 1,
                "best_val_loss": 0.8,
                "best_val_loss_delta": 0.0,
                "dataset_quality": "pass",
                "eval_suite_cases": 3,
            }
        ],
    }
    model_card = {
        "summary": {"run_count": 1, "best_run_name": name, "best_val_loss": 0.8, "ready_runs": 1},
        "top_runs": [
            {
                "name": name,
                "path": str(run_dir),
                "status": "ready",
                "best_val_loss_rank": 1,
                "best_val_loss": 0.8,
                "best_val_loss_delta": 0.0,
                "dataset_quality": "pass",
                "eval_suite_cases": 3,
                "experiment_card_html": str(run_dir / "experiment_card.html"),
            }
        ],
        "recommendations": ["Use this run as the current reference."],
    }
    audit = {
        "request_history_summary_path": str(request_dir / "request_history_summary.json"),
        "benchmark_history_path": str(history_dir / "benchmark_history.json"),
        "ci_workflow_hygiene_path": str(ci_dir / "ci_workflow_hygiene.json"),
        "test_coverage_report_path": str(coverage_dir / "test_coverage_report.json"),
        "summary": {
            "overall_status": "pass",
            "score_percent": 100.0,
            "pass_count": 12,
            "warn_count": 0,
            "fail_count": 0,
            "ready_runs": 1,
            "request_history_status": "pass",
            "request_history_records": 4,
            "benchmark_history_status": "pass",
            "benchmark_history_entries": 1,
            "benchmark_history_ready": 1,
            "benchmark_history_review": 0,
            "benchmark_history_blocked": 0,
            "benchmark_history_case_regressions": 0,
            "benchmark_history_generation_flag_regressions": 0,
            "benchmark_history_suite_design_non_comparison_ready_entries": 0,
            "benchmark_history_design_comparison_changed_entries": 0,
            "benchmark_history_readiness_requirement_status": "pass",
            "benchmark_history_readiness_requirement_exit_code": 0,
            "benchmark_history_readiness_requirement_failed_reasons": [],
            "benchmark_history_model_quality_claim": "candidate_evidence",
            "benchmark_history_latest_boundary": "standard-benchmark-candidate-evidence",
            "ci_workflow_status": "pass",
            "ci_workflow_failed_checks": 0,
            "ci_workflow_node24_actions": 2,
            "ci_workflow_required_order_count": 1,
            "ci_workflow_order_violation_count": 0,
            "ci_archived_path_portability_check_ready": True,
            "ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": True,
            "ci_release_readiness_drift_contract_smoke_ready": True,
            "test_coverage_status": "pass",
            "test_coverage_decision": "continue_with_coverage_gate",
            "test_coverage_percent": 90.17,
            "test_coverage_fail_under": 80.0,
            "test_coverage_gap": 0.0,
        },
        "ci_workflow_context": {
            "available": True,
            "workflow_path": ".github/workflows/ci.yml",
            "status": "pass",
            "decision": "continue_with_node24_native_ci",
            "check_count": 7,
            "failed_check_count": 0,
            "action_count": 2,
            "node24_native_action_count": 2,
            "forbidden_env_count": 0,
            "missing_step_count": 0,
            "required_order_count": 1,
            "order_violation_count": 0,
            "tiny_scorecard_plan_digest_gate_present": True,
            "tiny_scorecard_plan_digest_gate_order_ready": True,
            "tiny_scorecard_plan_digest_gate_ready": True,
            "baseline_candidate_threshold_boundary_gate_check_present": True,
            "baseline_candidate_threshold_boundary_gate_check_order_ready": True,
            "baseline_candidate_threshold_boundary_gate_check_ready": True,
            "baseline_candidate_threshold_boundary_gate_plan_check_present": True,
            "baseline_candidate_threshold_boundary_gate_plan_check_order_ready": True,
            "baseline_candidate_threshold_boundary_gate_plan_check_ready": True,
            "archived_path_portability_check_present": True,
            "archived_path_portability_check_order_ready": True,
            "archived_path_portability_check_ready": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_present": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": True,
            "release_readiness_drift_contract_smoke_present": True,
            "release_readiness_drift_contract_smoke_order_ready": True,
            "release_readiness_drift_contract_smoke_ready": True,
            "python_version": "3.11",
        },
        "benchmark_history_context": {
            "available": True,
            "evidence_kind": "real-benchmark",
            "entry_count": 1,
            "promote_count": 1,
            "ready_count": 1,
            "review_count": 0,
            "blocked_count": 0,
            "case_regression_entry_count": 0,
            "generation_quality_flag_regression_entry_count": 0,
            "suite_design_non_comparison_ready_entry_count": 0,
            "design_comparison_changed_entry_count": 0,
            "best_candidate_name": name,
            "best_entry_name": "round-1",
            "readiness_requirement_status": "pass",
            "readiness_requirement_decision": "continue",
            "readiness_requirement_exit_code": 0,
            "readiness_requirement_failed_reasons": [],
            "model_quality_claim": "candidate_evidence",
            "latest_boundary": "standard-benchmark-candidate-evidence",
            "latest_decision_status": "promote",
            "latest_promotion_readiness": "ready",
        },
        "test_coverage_context": {
            "available": True,
            "status": "pass",
            "decision": "continue_with_coverage_gate",
            "line_coverage_percent": 90.17,
            "covered_lines": 12367,
            "num_statements": 13715,
            "missing_lines": 1348,
            "file_count": 122,
            "threshold_enabled": True,
            "fail_under": 80.0,
            "coverage_gap": 0.0,
        },
        "checks": [
            {"id": "ready_run", "title": "At least one ready run", "status": "pass", "detail": "1 ready run(s)."},
            {
                "id": "request_history_summary",
                "title": "Request history summary is clean",
                "status": "pass",
                "detail": "status=pass; records=4; invalid=0; timeout_rate=0; error_rate=0.",
            },
            {
                "id": "ci_workflow_hygiene",
                "title": "CI workflow hygiene is clean",
                "status": "pass",
                "detail": "status=pass; actions=2; node24_native=2; failed_checks=0; forbidden_env=0; missing_steps=0.",
            },
            {
                "id": "test_coverage_report",
                "title": "Test coverage gate is clean",
                "status": "pass",
                "detail": "status=pass; decision=continue_with_coverage_gate; line_coverage=90.17; fail_under=80; coverage_gap=0.",
            },
        ],
        "recommendations": ["All audit checks passed."],
    }
    request_summary = {
        "schema_version": 1,
        "request_log": str(root / "runs" / "minigpt" / "inference_requests.jsonl"),
        "summary": {
            "status": "pass",
            "total_log_records": 4,
            "invalid_record_count": 0,
            "timeout_rate": 0.0,
            "bad_request_rate": 0.0,
            "error_rate": 0.0,
            "latest_timestamp": "2026-05-14T00:00:00Z",
        },
    }
    benchmark_history = {
        "schema_version": 1,
        "title": "MiniGPT benchmark history",
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
            "best_candidate_name": name,
            "best_entry_name": "round-1",
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
                "name": "round-1",
                "candidate_name": name,
                "decision_status": "promote",
                "promotion_readiness": "ready",
                "eval_suite_design_comparison_status": "pass",
                "non_design_comparison_ready_count": 0,
                "design_comparison_changed_count": 0,
                "boundary": "standard-benchmark-candidate-evidence",
            }
        ],
    }
    ci_workflow_hygiene = {
        "schema_version": 1,
        "workflow_path": ".github/workflows/ci.yml",
        "summary": {
            "status": "pass",
            "decision": "continue_with_node24_native_ci",
            "check_count": 7,
            "passed_check_count": 7,
            "failed_check_count": 0,
            "action_count": 2,
            "node24_native_action_count": 2,
            "forbidden_env_count": 0,
            "missing_step_count": 0,
            "required_order_count": 1,
            "order_violation_count": 0,
            "archived_path_portability_check_present": True,
            "archived_path_portability_check_order_ready": True,
            "archived_path_portability_check_ready": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_present": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": True,
            "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": True,
            "release_readiness_drift_contract_smoke_present": True,
            "release_readiness_drift_contract_smoke_order_ready": True,
            "release_readiness_drift_contract_smoke_ready": True,
            "python_version": "3.11",
        },
    }
    test_coverage_report = {
        "schema_version": 1,
        "title": "MiniGPT test coverage report",
        "summary": {
            "status": "pass",
            "decision": "continue_with_coverage_gate",
            "line_coverage_percent": 90.17,
            "covered_lines": 12367,
            "num_statements": 13715,
            "missing_lines": 1348,
            "file_count": 122,
            "threshold_enabled": True,
            "fail_under": 80.0,
            "coverage_gap": 0.0,
        },
    }
    registry_path = registry_dir / "registry.json"
    model_path = model_dir / "model_card.json"
    audit_path = audit_dir / "project_audit.json"
    write_json(registry_path, registry)
    (registry_dir / "registry.csv").write_text("name\ncandidate\n", encoding="utf-8")
    (registry_dir / "registry.html").write_text("<html></html>", encoding="utf-8")
    write_json(model_path, model_card)
    (model_dir / "model_card.md").write_text("# model card", encoding="utf-8")
    (model_dir / "model_card.html").write_text("<html></html>", encoding="utf-8")
    write_json(audit_path, audit)
    (audit_dir / "project_audit.md").write_text("# audit", encoding="utf-8")
    (audit_dir / "project_audit.html").write_text("<html></html>", encoding="utf-8")
    request_summary_path = request_dir / "request_history_summary.json"
    write_json(request_summary_path, request_summary)
    (request_dir / "request_history_summary.md").write_text("# request history summary", encoding="utf-8")
    (request_dir / "request_history_summary.html").write_text("<html></html>", encoding="utf-8")
    benchmark_history_path = history_dir / "benchmark_history.json"
    write_json(benchmark_history_path, benchmark_history)
    (history_dir / "benchmark_history.md").write_text("# benchmark history", encoding="utf-8")
    (history_dir / "benchmark_history.html").write_text("<html></html>", encoding="utf-8")
    ci_workflow_hygiene_path = ci_dir / "ci_workflow_hygiene.json"
    write_json(ci_workflow_hygiene_path, ci_workflow_hygiene)
    (ci_dir / "ci_workflow_hygiene.md").write_text("# ci workflow hygiene", encoding="utf-8")
    (ci_dir / "ci_workflow_hygiene.html").write_text("<html></html>", encoding="utf-8")
    test_coverage_report_path = coverage_dir / "test_coverage_report.json"
    write_json(test_coverage_report_path, test_coverage_report)
    (coverage_dir / "test_coverage_report.md").write_text("# test coverage report", encoding="utf-8")
    (coverage_dir / "test_coverage_report.html").write_text("<html></html>", encoding="utf-8")
    return registry_path, model_path, audit_path, request_summary_path, benchmark_history_path, ci_workflow_hygiene_path, test_coverage_report_path


class ReleaseBundleTests(unittest.TestCase):
    def test_build_release_bundle_summarizes_ready_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, request_summary_path, benchmark_history_path, _ci_workflow_hygiene_path, test_coverage_report_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                request_history_summary_path=request_summary_path,
                benchmark_history_path=benchmark_history_path,
                test_coverage_report_path=test_coverage_report_path,
                release_name="v26-demo",
                generated_at="2026-05-12T00:00:00Z",
            )

            self.assertEqual(bundle["summary"]["release_status"], "release-ready")
            self.assertEqual(bundle["summary"]["audit_status"], "pass")
            self.assertEqual(bundle["summary"]["request_history_status"], "pass")
            self.assertEqual(bundle["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(bundle["summary"]["benchmark_history_entries"], 1)
            self.assertEqual(bundle["summary"]["benchmark_history_ready"], 1)
            self.assertEqual(bundle["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 0)
            self.assertEqual(bundle["summary"]["benchmark_history_design_comparison_changed_entries"], 0)
            self.assertEqual(bundle["summary"]["benchmark_history_readiness_requirement_status"], "pass")
            self.assertEqual(bundle["summary"]["benchmark_history_readiness_requirement_exit_code"], 0)
            self.assertEqual(bundle["summary"]["benchmark_history_readiness_requirement_failed_reasons"], [])
            self.assertEqual(bundle["summary"]["benchmark_history_latest_boundary"], "standard-benchmark-candidate-evidence")
            self.assertEqual(bundle["summary"]["ci_workflow_status"], "pass")
            self.assertEqual(bundle["summary"]["ci_workflow_failed_checks"], 0)
            self.assertEqual(bundle["summary"]["ci_workflow_required_order_count"], 1)
            self.assertEqual(bundle["summary"]["ci_workflow_order_violation_count"], 0)
            self.assertTrue(bundle["summary"]["ci_workflow_tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_archived_path_portability_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_release_readiness_drift_contract_smoke_ready"])
            self.assertEqual(bundle["summary"]["test_coverage_status"], "pass")
            self.assertEqual(bundle["summary"]["test_coverage_percent"], 90.17)
            self.assertEqual(bundle["summary"]["test_coverage_fail_under"], 80.0)
            self.assertEqual(bundle["summary"]["test_coverage_gap"], 0.0)
            self.assertEqual(bundle["summary"]["best_run_name"], "candidate")
            self.assertIn("request_history_summary_json", {item["key"] for item in bundle["artifacts"]})
            self.assertIn("benchmark_history_json", {item["key"] for item in bundle["artifacts"]})
            self.assertIn("ci_workflow_hygiene_json", {item["key"] for item in bundle["artifacts"]})
            self.assertIn("test_coverage_report_json", {item["key"] for item in bundle["artifacts"]})
            self.assertEqual(bundle["ci_workflow_context"]["status"], "pass")
            self.assertTrue(bundle["ci_workflow_context"]["tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(bundle["ci_workflow_context"]["baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(bundle["ci_workflow_context"]["baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(bundle["ci_workflow_context"]["archived_path_portability_check_ready"])
            self.assertTrue(bundle["ci_workflow_context"]["promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(bundle["ci_workflow_context"]["release_readiness_drift_contract_smoke_ready"])
            self.assertEqual(bundle["benchmark_history_context"]["latest_decision_status"], "promote")
            self.assertEqual(bundle["benchmark_history_context"]["readiness_requirement_status"], "pass")
            self.assertEqual(bundle["benchmark_history_context"]["suite_design_non_comparison_ready_entry_count"], 0)
            self.assertEqual(bundle["ci_workflow_context"]["order_violation_count"], 0)
            self.assertEqual(bundle["test_coverage_context"]["coverage_gap"], 0.0)
            self.assertGreaterEqual(bundle["summary"]["available_artifacts"], 10)
            self.assertEqual(bundle["top_runs"][0]["name"], "candidate")
            self.assertIn("Release evidence is complete", " ".join(bundle["recommendations"]))

    def test_build_release_bundle_accepts_explicit_ci_workflow_hygiene_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _benchmark_history_path, ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                ci_workflow_hygiene_path=ci_workflow_hygiene_path,
            )

            self.assertEqual(bundle["inputs"]["ci_workflow_hygiene_path"], str(ci_workflow_hygiene_path))
            self.assertEqual(bundle["summary"]["ci_workflow_node24_actions"], 2)
            self.assertEqual(bundle["summary"]["ci_workflow_order_violation_count"], 0)
            self.assertTrue(bundle["summary"]["ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_archived_path_portability_check_ready"])
            self.assertTrue(bundle["summary"]["ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertIn("ci_workflow_hygiene_html", {item["key"] for item in bundle["artifacts"]})

    def test_build_release_bundle_accepts_explicit_test_coverage_report_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _benchmark_history_path, _ci_workflow_hygiene_path, test_coverage_report_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                test_coverage_report_path=test_coverage_report_path,
            )

            self.assertEqual(bundle["inputs"]["test_coverage_report_path"], str(test_coverage_report_path))
            self.assertEqual(bundle["summary"]["test_coverage_status"], "pass")
            self.assertEqual(bundle["test_coverage_context"]["line_coverage_percent"], 90.17)
            self.assertIn("test_coverage_report_html", {item["key"] for item in bundle["artifacts"]})

    def test_build_release_bundle_warns_from_audit_benchmark_history_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            audit["summary"]["overall_status"] = "warn"
            audit["summary"]["warn_count"] = 1
            audit["summary"]["benchmark_history_status"] = "warn"
            audit["summary"]["benchmark_history_ready"] = 0
            audit["summary"]["benchmark_history_model_quality_claim"] = "not_claimed"
            audit["summary"]["benchmark_history_latest_boundary"] = "tiny-smoke-plumbing-evidence"
            audit["benchmark_history_context"]["ready_count"] = 0
            audit["benchmark_history_context"]["model_quality_claim"] = "not_claimed"
            audit["benchmark_history_context"]["latest_boundary"] = "tiny-smoke-plumbing-evidence"
            write_json(audit_path, audit)
            benchmark_history_path.unlink()

            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path)

            self.assertEqual(bundle["summary"]["release_status"], "review-needed")
            self.assertEqual(bundle["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(bundle["summary"]["benchmark_history_ready"], 0)
            self.assertEqual(bundle["summary"]["benchmark_history_latest_boundary"], "tiny-smoke-plumbing-evidence")
            self.assertEqual(bundle["benchmark_history_context"]["model_quality_claim"], "not_claimed")

    def test_build_release_bundle_warns_when_history_requirement_fails_even_if_audit_is_stale_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            history = json.loads(benchmark_history_path.read_text(encoding="utf-8"))
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
            write_json(benchmark_history_path, history)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                benchmark_history_path=benchmark_history_path,
            )

            self.assertEqual(bundle["summary"]["release_status"], "review-needed")
            self.assertEqual(bundle["summary"]["audit_status"], "pass")
            self.assertEqual(bundle["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(bundle["summary"]["benchmark_history_readiness_requirement_status"], "fail")
            self.assertEqual(bundle["summary"]["benchmark_history_readiness_requirement_exit_code"], 1)
            self.assertEqual(
                bundle["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["insufficient_ready_entries"],
            )
            self.assertEqual(bundle["benchmark_history_context"]["readiness_requirement_status"], "fail")

    def test_build_release_bundle_warns_when_history_suite_design_not_ready_even_if_audit_is_stale_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            history = json.loads(benchmark_history_path.read_text(encoding="utf-8"))
            history["summary"]["ready_count"] = 0
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
            write_json(benchmark_history_path, history)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                benchmark_history_path=benchmark_history_path,
            )

            self.assertEqual(bundle["summary"]["release_status"], "review-needed")
            self.assertEqual(bundle["summary"]["audit_status"], "pass")
            self.assertEqual(bundle["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(bundle["summary"]["benchmark_history_ready"], 0)
            self.assertEqual(bundle["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 1)
            self.assertEqual(bundle["summary"]["benchmark_history_design_comparison_changed_entries"], 1)
            self.assertEqual(
                bundle["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["suite_design_non_comparison_ready_entries"],
            )
            self.assertEqual(bundle["summary"]["benchmark_history_latest_boundary"], "suite-design-not-comparison-ready")
            self.assertEqual(bundle["benchmark_history_context"]["suite_design_non_comparison_ready_entry_count"], 1)
            self.assertEqual(bundle["benchmark_history_context"]["design_comparison_changed_entry_count"], 1)

    def test_build_release_bundle_marks_missing_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            audit_path.unlink()

            bundle = build_release_bundle(registry_path, model_card_path=model_path)

            self.assertEqual(bundle["summary"]["release_status"], "needs-audit")
            self.assertIn("Generate project_audit.json", " ".join(bundle["recommendations"]))

    def test_write_release_bundle_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path)

            outputs = write_release_bundle_outputs(bundle, root / "release-bundle")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Evidence Artifacts", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI workflow status", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history status", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness exit", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history suite-design not-ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history design changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI receipt failure-smoke plan check", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Test coverage status", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT release bundle", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench history", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design review", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness exit", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI receipt plan", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_cli_prints_release_bundle_benchmark_history_suite_design_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root)
            out_dir = root / "release-bundle"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_release_bundle.py"),
                    "--registry",
                    str(registry_path),
                    "--model-card",
                    str(model_path),
                    "--audit",
                    str(audit_path),
                    "--benchmark-history",
                    str(benchmark_history_path),
                    "--out-dir",
                    str(out_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("benchmark_history_suite_design_non_comparison_ready_entries=0", completed.stdout)
            self.assertIn("benchmark_history_design_comparison_changed_entries=0", completed.stdout)
            self.assertIn("ci_workflow_archived_path_portability_check_ready=True", completed.stdout)
            self.assertIn("ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True", completed.stdout)

    def test_render_release_bundle_html_escapes_run_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _benchmark_history_path, _ci_workflow_hygiene_path, _test_coverage_report_path = make_release_inputs(root, name="<script>")
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path, title="<Release>")

            html = render_release_bundle_html(bundle)

            self.assertIn("&lt;Release&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)

    def test_release_bundle_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(release_bundle_facade.render_release_bundle_html, release_bundle_artifacts.render_release_bundle_html)
        self.assertIs(release_bundle_facade.render_release_bundle_markdown, release_bundle_artifacts.render_release_bundle_markdown)
        self.assertIs(release_bundle_facade.write_release_bundle_outputs, release_bundle_artifacts.write_release_bundle_outputs)
        self.assertIs(release_bundle_facade.write_release_bundle_json, release_bundle_artifacts.write_release_bundle_json)


if __name__ == "__main__":
    unittest.main()
