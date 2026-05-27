from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import project_audit, project_audit_artifacts
from minigpt.project_audit_contexts import (
    build_benchmark_history_check,
    build_benchmark_history_context,
    build_ci_workflow_context,
    build_ci_workflow_hygiene_check,
    build_request_history_context,
    build_request_history_summary_check,
    build_test_coverage_check,
    build_test_coverage_context,
)
from minigpt.project_audit import build_project_audit, render_project_audit_html, write_project_audit_outputs


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_registry(root: Path, name: str = "candidate") -> Path:
    run_dir = root / "run-a"
    run_dir.mkdir()
    registry = {
        "schema_version": 1,
        "run_count": 1,
        "best_by_best_val_loss": {"name": name, "path": str(run_dir), "best_val_loss": 0.8},
        "runs": [
            {
                "name": name,
                "path": str(run_dir),
                "best_val_loss_rank": 1,
                "best_val_loss": 0.8,
                "best_val_loss_delta": 0.0,
                "dataset_quality": "pass",
                "eval_suite_cases": 3,
                "generation_quality_status": "pass",
                "generation_quality_cases": 3,
                "generation_quality_pass_count": 3,
                "generation_quality_warn_count": 0,
                "generation_quality_fail_count": 0,
                "artifact_count": 12,
                "checkpoint_exists": True,
                "dashboard_exists": True,
                "tags": ["candidate"],
                "note": "ready",
            }
        ],
    }
    registry_path = root / "registry" / "registry.json"
    write_json(registry_path, registry)
    return registry_path


def make_model_card(root: Path, registry_path: Path) -> Path:
    run_dir = root / "run-a"
    model_card = {
        "registry_path": str(registry_path),
        "summary": {"ready_runs": 1, "review_runs": 0},
        "runs": [
            {
                "name": "candidate",
                "path": str(run_dir),
                "status": "ready",
                "experiment_card_exists": True,
                "generation_quality_status": "pass",
                "generation_quality_cases": 3,
                "tags": ["candidate", "keep"],
                "note": "ready card",
            }
        ],
    }
    model_card_path = root / "model-card" / "model_card.json"
    write_json(model_card_path, model_card)
    return model_card_path


def make_request_history_summary(root: Path, *, status: str = "pass") -> Path:
    summary = {
        "schema_version": 1,
        "request_log": str(root / "runs" / "minigpt" / "inference_requests.jsonl"),
        "summary": {
            "status": status,
            "total_log_records": 4,
            "invalid_record_count": 0,
            "timeout_count": 0 if status == "pass" else 1,
            "bad_request_count": 0,
            "error_count": 0,
            "timeout_rate": 0.0 if status == "pass" else 0.25,
            "bad_request_rate": 0.0,
            "error_rate": 0.0,
            "unique_checkpoint_count": 1,
            "latest_timestamp": "2026-05-14T00:00:00Z",
        },
    }
    path = root / "request-history-summary" / "request_history_summary.json"
    write_json(path, summary)
    return path


def make_benchmark_history(
    root: Path,
    *,
    decision_status: str = "promote",
    evidence_kind: str = "real-benchmark",
    readiness_requirement_status: str = "pass",
    suite_design_status: str | None = "pass",
) -> Path:
    suite_design_ready = suite_design_status in {None, "pass"}
    suite_design_not_ready = 0 if suite_design_ready else 1
    design_changed = 0 if suite_design_ready else 1
    effective_readiness_status = (
        "fail" if not suite_design_ready and readiness_requirement_status == "pass" else readiness_requirement_status
    )
    ready = decision_status == "promote" and evidence_kind != "tiny-smoke" and suite_design_ready
    failed_reasons: list[str] = []
    if effective_readiness_status != "pass":
        failed_reasons = (
            ["suite_design_non_comparison_ready_entries"] if not suite_design_ready else ["insufficient_ready_entries"]
        )
    summary = {
        "entry_count": 1,
        "promote_count": 1 if decision_status == "promote" else 0,
        "review_count": 1 if decision_status == "review" else 0,
        "blocked_count": 1 if decision_status == "blocked" else 0,
        "ready_count": 1 if ready else 0,
        "case_regression_entry_count": 1 if decision_status == "review" else 0,
        "generation_quality_flag_regression_entry_count": 0,
        "suite_design_non_comparison_ready_entry_count": suite_design_not_ready,
        "design_comparison_changed_entry_count": design_changed,
        "best_candidate_name": "candidate",
        "best_entry_name": "round-1",
        "model_quality_claim": "not_claimed" if evidence_kind == "tiny-smoke" else "candidate_evidence",
    }
    report = {
        "schema_version": 1,
        "title": "MiniGPT benchmark history",
        "evidence_kind": evidence_kind,
        "summary": summary,
        "readiness_requirement": {
            "status": effective_readiness_status,
            "decision": "continue" if effective_readiness_status == "pass" else "stop",
            "exit_code": 0 if effective_readiness_status == "pass" else 1,
            "min_ready_entries": 1 if effective_readiness_status == "pass" else 2,
            "ready_count": summary["ready_count"],
            "entry_count": summary["entry_count"],
            "evidence_kind": evidence_kind,
            "require_real_benchmark": True,
            "failed_reasons": failed_reasons,
        },
        "entries": [
            {
                "name": "round-1",
                "candidate_name": "candidate",
                "decision_status": decision_status,
                "promotion_readiness": "ready" if ready else "review",
                "case_regression_count": summary["case_regression_entry_count"],
                "generation_quality_total_flags_delta": 0,
                "eval_suite_design_comparison_status": suite_design_status,
                "non_design_comparison_ready_count": suite_design_not_ready,
                "design_comparison_changed_count": design_changed,
                "boundary": (
                    "suite-design-not-comparison-ready"
                    if not suite_design_ready
                    else "tiny-smoke-plumbing-evidence"
                    if evidence_kind == "tiny-smoke"
                    else "standard-benchmark-candidate-evidence"
                ),
            }
        ],
    }
    path = root / "benchmark-history" / "benchmark_history.json"
    write_json(path, report)
    return path


def make_ci_workflow_hygiene(root: Path, *, status: str = "pass") -> Path:
    summary = {
        "status": status,
        "decision": "continue_with_node24_native_ci" if status == "pass" else "fix_ci_workflow_hygiene",
        "check_count": 7,
        "passed_check_count": 7 if status == "pass" else 4,
        "failed_check_count": 0 if status == "pass" else 3,
        "action_count": 2,
        "node24_native_action_count": 2 if status == "pass" else 0,
        "forbidden_env_count": 0 if status == "pass" else 1,
        "missing_step_count": 0 if status == "pass" else 1,
        "required_order_count": 4,
        "order_violation_count": 0 if status == "pass" else 1,
        "tiny_scorecard_plan_digest_gate_present": status == "pass",
        "tiny_scorecard_plan_digest_gate_order_ready": status == "pass",
        "tiny_scorecard_plan_digest_gate_ready": status == "pass",
        "baseline_candidate_threshold_boundary_gate_check_present": status == "pass",
        "baseline_candidate_threshold_boundary_gate_check_order_ready": status == "pass",
        "baseline_candidate_threshold_boundary_gate_check_ready": status == "pass",
        "baseline_candidate_threshold_boundary_gate_plan_check_present": status == "pass",
        "baseline_candidate_threshold_boundary_gate_plan_check_order_ready": status == "pass",
        "baseline_candidate_threshold_boundary_gate_plan_check_ready": status == "pass",
        "archived_path_portability_check_present": status == "pass",
        "archived_path_portability_check_order_ready": status == "pass",
        "archived_path_portability_check_ready": status == "pass",
        "promoted_seed_receipt_contract_failure_smoke_plan_check_present": status == "pass",
        "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": status == "pass",
        "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": status == "pass",
        "release_readiness_drift_contract_smoke_present": status == "pass",
        "release_readiness_drift_contract_smoke_order_ready": status == "pass",
        "release_readiness_drift_contract_smoke_ready": status == "pass",
        "python_version": "3.11",
    }
    report = {
        "schema_version": 1,
        "workflow_path": ".github/workflows/ci.yml",
        "summary": summary,
        "checks": [],
    }
    path = root / "ci-workflow-hygiene" / "ci_workflow_hygiene.json"
    write_json(path, report)
    return path


def make_test_coverage_report(root: Path, *, status: str = "pass", threshold_enabled: bool = True) -> Path:
    summary = {
        "status": status,
        "decision": "continue_with_coverage_gate" if status == "pass" and threshold_enabled else "improve_test_coverage",
        "line_coverage_percent": 90.16 if status == "pass" else 72.0,
        "covered_lines": 12336,
        "num_statements": 13683,
        "missing_lines": 1347,
        "file_count": 122,
        "threshold_enabled": threshold_enabled,
        "fail_under": 80.0 if threshold_enabled else None,
        "coverage_gap": 0.0 if status == "pass" else 8.0,
    }
    report = {
        "schema_version": 1,
        "title": "MiniGPT test coverage report",
        "summary": summary,
    }
    path = root / "test-coverage" / "test_coverage_report.json"
    write_json(path, report)
    return path


class ProjectAuditTests(unittest.TestCase):
    def test_build_project_audit_passes_complete_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            request_history_summary_path = make_request_history_summary(root)
            benchmark_history_path = make_benchmark_history(root)
            ci_workflow_hygiene_path = make_ci_workflow_hygiene(root)
            test_coverage_report_path = make_test_coverage_report(root)

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                request_history_summary_path=request_history_summary_path,
                benchmark_history_path=benchmark_history_path,
                ci_workflow_hygiene_path=ci_workflow_hygiene_path,
                test_coverage_report_path=test_coverage_report_path,
                generated_at="2026-05-12T00:00:00Z",
            )

            self.assertEqual(audit["summary"]["overall_status"], "pass")
            self.assertEqual(audit["summary"]["fail_count"], 0)
            self.assertEqual(audit["summary"]["warn_count"], 0)
            self.assertEqual(audit["summary"]["ready_runs"], 1)
            self.assertEqual(audit["summary"]["request_history_status"], "pass")
            self.assertEqual(audit["summary"]["request_history_records"], 4)
            self.assertEqual(audit["summary"]["benchmark_history_status"], "pass")
            self.assertEqual(audit["summary"]["benchmark_history_entries"], 1)
            self.assertEqual(audit["summary"]["benchmark_history_ready"], 1)
            self.assertEqual(audit["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 0)
            self.assertEqual(audit["summary"]["benchmark_history_design_comparison_changed_entries"], 0)
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_status"], "pass")
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_exit_code"], 0)
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_failed_reasons"], [])
            self.assertEqual(audit["summary"]["benchmark_history_latest_boundary"], "standard-benchmark-candidate-evidence")
            self.assertEqual(audit["summary"]["ci_workflow_status"], "pass")
            self.assertEqual(audit["summary"]["ci_workflow_failed_checks"], 0)
            self.assertTrue(audit["summary"]["ci_tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(audit["summary"]["ci_baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(audit["summary"]["ci_baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(audit["summary"]["ci_archived_path_portability_check_ready"])
            self.assertTrue(audit["summary"]["ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(audit["summary"]["ci_release_readiness_drift_contract_smoke_ready"])
            self.assertEqual(audit["summary"]["test_coverage_status"], "pass")
            self.assertEqual(audit["summary"]["test_coverage_percent"], 90.16)
            self.assertEqual(audit["summary"]["test_coverage_fail_under"], 80.0)
            self.assertEqual(audit["request_history_context"]["status"], "pass")
            self.assertEqual(audit["benchmark_history_context"]["best_candidate_name"], "candidate")
            self.assertEqual(audit["benchmark_history_context"]["suite_design_non_comparison_ready_entry_count"], 0)
            self.assertEqual(audit["benchmark_history_context"]["design_comparison_changed_entry_count"], 0)
            self.assertEqual(audit["ci_workflow_context"]["status"], "pass")
            self.assertTrue(audit["ci_workflow_context"]["tiny_scorecard_plan_digest_gate_ready"])
            self.assertTrue(audit["ci_workflow_context"]["baseline_candidate_threshold_boundary_gate_check_ready"])
            self.assertTrue(audit["ci_workflow_context"]["baseline_candidate_threshold_boundary_gate_plan_check_ready"])
            self.assertTrue(audit["ci_workflow_context"]["archived_path_portability_check_ready"])
            self.assertTrue(audit["ci_workflow_context"]["promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
            self.assertTrue(audit["ci_workflow_context"]["release_readiness_drift_contract_smoke_ready"])
            self.assertEqual(audit["test_coverage_context"]["decision"], "continue_with_coverage_gate")
            self.assertIn("request_history_summary", {check["id"] for check in audit["checks"]})
            self.assertIn("benchmark_history", {check["id"] for check in audit["checks"]})
            self.assertIn("ci_workflow_hygiene", {check["id"] for check in audit["checks"]})
            self.assertIn("test_coverage_report", {check["id"] for check in audit["checks"]})
            self.assertEqual(audit["runs"][0]["experiment_card_exists"], True)
            self.assertIn("All audit checks passed", " ".join(audit["recommendations"]))

    def test_build_project_audit_warns_for_request_history_summary_review_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            request_history_summary_path = make_request_history_summary(root, status="watch")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                request_history_summary_path=request_history_summary_path,
            )

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            check = next(item for item in audit["checks"] if item["id"] == "request_history_summary")
            self.assertEqual(check["status"], "warn")
            self.assertIn("status=watch", check["detail"])
            self.assertIn("Generate or review request_history_summary.json", " ".join(audit["recommendations"]))

    def test_build_project_audit_warns_for_benchmark_history_review_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            request_history_summary_path = make_request_history_summary(root)
            benchmark_history_path = make_benchmark_history(root, decision_status="review")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                request_history_summary_path=request_history_summary_path,
                benchmark_history_path=benchmark_history_path,
            )

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_review"], 1)
            self.assertEqual(audit["summary"]["benchmark_history_case_regressions"], 1)
            check = next(item for item in audit["checks"] if item["id"] == "benchmark_history")
            self.assertEqual(check["status"], "warn")
            self.assertIn("review=1", check["detail"])
            self.assertIn("case_regressions=1", check["detail"])
            self.assertIn("Generate or review benchmark_history.json", " ".join(audit["recommendations"]))

    def test_build_project_audit_warns_for_benchmark_history_readiness_requirement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            benchmark_history_path = make_benchmark_history(root, readiness_requirement_status="fail")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                benchmark_history_path=benchmark_history_path,
            )
            check = next(item for item in audit["checks"] if item["id"] == "benchmark_history")

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_status"], "fail")
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_exit_code"], 1)
            self.assertEqual(audit["summary"]["benchmark_history_readiness_requirement_failed_reasons"], ["insufficient_ready_entries"])
            self.assertEqual(audit["benchmark_history_context"]["readiness_requirement_status"], "fail")
            self.assertEqual(check["status"], "warn")
            self.assertIn("readiness_requirement=fail", check["detail"])

    def test_build_project_audit_warns_for_benchmark_history_suite_design_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            benchmark_history_path = make_benchmark_history(root, suite_design_status="warn")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                benchmark_history_path=benchmark_history_path,
            )
            check = next(item for item in audit["checks"] if item["id"] == "benchmark_history")

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_status"], "warn")
            self.assertEqual(audit["summary"]["benchmark_history_ready"], 0)
            self.assertEqual(audit["summary"]["benchmark_history_suite_design_non_comparison_ready_entries"], 1)
            self.assertEqual(audit["summary"]["benchmark_history_design_comparison_changed_entries"], 1)
            self.assertEqual(
                audit["summary"]["benchmark_history_readiness_requirement_failed_reasons"],
                ["suite_design_non_comparison_ready_entries"],
            )
            self.assertEqual(audit["summary"]["benchmark_history_latest_boundary"], "suite-design-not-comparison-ready")
            self.assertEqual(audit["benchmark_history_context"]["suite_design_non_comparison_ready_entry_count"], 1)
            self.assertEqual(audit["benchmark_history_context"]["design_comparison_changed_entry_count"], 1)
            self.assertEqual(check["status"], "warn")
            self.assertIn("suite_design_not_ready=1", check["detail"])
            self.assertIn("design_comparison_changed=1", check["detail"])

    def test_build_project_audit_auto_discovers_benchmark_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            make_benchmark_history(root)

            audit = build_project_audit(registry_path, model_card_path=model_card_path)

            self.assertTrue(str(audit["benchmark_history_path"]).endswith("benchmark_history.json"))
            self.assertEqual(audit["summary"]["benchmark_history_status"], "pass")

    def test_build_project_audit_warns_for_ci_workflow_hygiene_fail_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            request_history_summary_path = make_request_history_summary(root)
            ci_workflow_hygiene_path = make_ci_workflow_hygiene(root, status="fail")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                request_history_summary_path=request_history_summary_path,
                ci_workflow_hygiene_path=ci_workflow_hygiene_path,
            )

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            self.assertEqual(audit["summary"]["ci_workflow_status"], "fail")
            check = next(item for item in audit["checks"] if item["id"] == "ci_workflow_hygiene")
            self.assertEqual(check["status"], "warn")
            self.assertIn("status=fail", check["detail"])
            self.assertIn("failed_checks=3", check["detail"])
            self.assertIn("tiny_scorecard_plan_digest_gate_ready=False", check["detail"])
            self.assertIn("baseline_candidate_threshold_boundary_gate_plan_check_ready=False", check["detail"])
            self.assertIn("promoted_seed_receipt_contract_failure_smoke_plan_check_ready=False", check["detail"])
            self.assertIn("Generate or review ci_workflow_hygiene.json", " ".join(audit["recommendations"]))

    def test_build_project_audit_warns_for_test_coverage_gate_fail_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            request_history_summary_path = make_request_history_summary(root)
            ci_workflow_hygiene_path = make_ci_workflow_hygiene(root)
            test_coverage_report_path = make_test_coverage_report(root, status="fail")

            audit = build_project_audit(
                registry_path,
                model_card_path=model_card_path,
                request_history_summary_path=request_history_summary_path,
                ci_workflow_hygiene_path=ci_workflow_hygiene_path,
                test_coverage_report_path=test_coverage_report_path,
            )

            self.assertEqual(audit["summary"]["overall_status"], "warn")
            self.assertEqual(audit["summary"]["test_coverage_status"], "fail")
            self.assertEqual(audit["summary"]["test_coverage_gap"], 8.0)
            check = next(item for item in audit["checks"] if item["id"] == "test_coverage_report")
            self.assertEqual(check["status"], "warn")
            self.assertIn("coverage_gap=8", check["detail"])
            self.assertIn("Generate or review test_coverage_report.json", " ".join(audit["recommendations"]))

    def test_build_project_audit_fails_for_missing_experiment_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = make_registry(Path(tmp))

            audit = build_project_audit(registry_path)

            self.assertEqual(audit["summary"]["overall_status"], "fail")
            self.assertGreater(audit["summary"]["fail_count"], 0)
            self.assertIn("Build model_card.json", " ".join(audit["recommendations"]))
            self.assertIn("Generate experiment cards", " ".join(audit["recommendations"]))

    def test_write_project_audit_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            audit = build_project_audit(registry_path, model_card_path=model_card_path)

            outputs = write_project_audit_outputs(audit, root / "audit")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Checks", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI workflow hygiene", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI receipt failure-smoke plan check", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Test coverage report", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history readiness exit", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history suite-design not-ready", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark history design changes", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT project audit", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench history", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design review", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench design changes", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Bench readiness exit", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("CI receipt plan", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_cli_prints_project_audit_benchmark_history_suite_design_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)
            benchmark_history_path = make_benchmark_history(root)
            out_dir = root / "audit"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_project.py"),
                    "--registry",
                    str(registry_path),
                    "--model-card",
                    str(model_card_path),
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
            self.assertIn("ci_archived_path_portability_check_ready=None", completed.stdout)
            self.assertIn("ci_promoted_seed_receipt_contract_failure_smoke_plan_check_ready=None", completed.stdout)

    def test_render_project_audit_html_escapes_run_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root, name="<script>")
            model_card_path = make_model_card(root, registry_path)
            audit = build_project_audit(registry_path, model_card_path=model_card_path, title="<Audit>")

            html = render_project_audit_html(audit)

            self.assertIn("&lt;Audit&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)

    def test_project_audit_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(project_audit.render_project_audit_html, project_audit_artifacts.render_project_audit_html)
        self.assertIs(project_audit.write_project_audit_outputs, project_audit_artifacts.write_project_audit_outputs)

    def test_project_audit_context_helpers_map_statuses_and_missing_inputs(self) -> None:
        request_summary = {
            "request_log": "runs/minigpt/inference_requests.jsonl",
            "summary": {
                "status": "watch",
                "total_log_records": 2,
                "invalid_record_count": 0,
                "timeout_rate": 0.5,
                "bad_request_rate": 0.0,
                "error_rate": 0.0,
            },
        }
        ci_hygiene = {
            "workflow_path": ".github/workflows/ci.yml",
            "summary": {
                "status": "fail",
                "decision": "fix_ci_workflow_hygiene",
                "action_count": 2,
                "node24_native_action_count": 0,
                "failed_check_count": 3,
                "forbidden_env_count": 1,
                "missing_step_count": 1,
                "required_order_count": 1,
                "order_violation_count": 1,
                "tiny_scorecard_plan_digest_gate_present": True,
                "tiny_scorecard_plan_digest_gate_order_ready": False,
                "tiny_scorecard_plan_digest_gate_ready": False,
                "baseline_candidate_threshold_boundary_gate_check_present": True,
                "baseline_candidate_threshold_boundary_gate_check_order_ready": False,
                "baseline_candidate_threshold_boundary_gate_check_ready": False,
                "baseline_candidate_threshold_boundary_gate_plan_check_present": True,
                "baseline_candidate_threshold_boundary_gate_plan_check_order_ready": False,
                "baseline_candidate_threshold_boundary_gate_plan_check_ready": False,
                "promoted_seed_receipt_contract_failure_smoke_plan_check_present": True,
                "promoted_seed_receipt_contract_failure_smoke_plan_check_order_ready": False,
                "promoted_seed_receipt_contract_failure_smoke_plan_check_ready": False,
                "python_version": "3.11",
            },
        }
        coverage = {
            "summary": {
                "status": "pass",
                "decision": "continue_with_coverage_gate",
                "line_coverage_percent": 90.16,
                "covered_lines": 12336,
                "num_statements": 13683,
                "missing_lines": 1347,
                "file_count": 122,
                "threshold_enabled": True,
                "fail_under": 80.0,
                "coverage_gap": 0.0,
            }
        }

        request_check = build_request_history_summary_check(request_summary, Path("request_history_summary.json"))
        ci_check = build_ci_workflow_hygiene_check(ci_hygiene, Path("ci_workflow_hygiene.json"))
        coverage_check = build_test_coverage_check(coverage, Path("test_coverage_report.json"))
        history = {
            "evidence_kind": "tiny-smoke",
            "summary": {
                "entry_count": 1,
                "ready_count": 0,
                "review_count": 0,
                "blocked_count": 0,
                "case_regression_entry_count": 0,
                "generation_quality_flag_regression_entry_count": 0,
                "suite_design_non_comparison_ready_entry_count": 0,
                "design_comparison_changed_entry_count": 0,
                "model_quality_claim": "not_claimed",
            },
            "readiness_requirement": {
                "status": "fail",
                "decision": "stop",
                "exit_code": 1,
                "failed_reasons": ["not_real_benchmark_evidence"],
            },
            "entries": [{"boundary": "tiny-smoke-plumbing-evidence", "decision_status": "promote"}],
        }
        history_check = build_benchmark_history_check(history, Path("benchmark_history.json"))

        self.assertEqual(request_check["status"], "warn")
        self.assertIn("status=watch", request_check["detail"])
        self.assertEqual(request_check["evidence"]["timeout_rate"], 0.5)
        self.assertEqual(build_request_history_context(request_summary)["request_log"], "runs/minigpt/inference_requests.jsonl")
        self.assertEqual(build_request_history_summary_check(None, None)["status"], "warn")
        self.assertFalse(build_request_history_context(None)["available"])

        self.assertEqual(history_check["status"], "warn")
        self.assertIn("model_quality_claim=not_claimed", history_check["detail"])
        self.assertIn("readiness_requirement=fail", history_check["detail"])
        self.assertIn("suite_design_not_ready=0", history_check["detail"])
        self.assertEqual(history_check["evidence"]["suite_design_non_comparison_ready_entry_count"], 0)
        self.assertEqual(history_check["evidence"]["design_comparison_changed_entry_count"], 0)
        self.assertEqual(history_check["evidence"]["latest_boundary"], "tiny-smoke-plumbing-evidence")
        self.assertEqual(build_benchmark_history_context(history)["latest_decision_status"], "promote")
        self.assertEqual(build_benchmark_history_context(history)["readiness_requirement_status"], "fail")
        self.assertEqual(build_benchmark_history_context(history)["suite_design_non_comparison_ready_entry_count"], 0)
        self.assertEqual(build_benchmark_history_check(None, None)["status"], "warn")
        self.assertFalse(build_benchmark_history_context(None)["available"])
        self.assertIsNone(build_benchmark_history_context(None)["suite_design_non_comparison_ready_entry_count"])

        self.assertEqual(ci_check["status"], "warn")
        self.assertIn("failed_checks=3", ci_check["detail"])
        self.assertIn("order_violations=1", ci_check["detail"])
        self.assertEqual(ci_check["evidence"]["decision"], "fix_ci_workflow_hygiene")
        self.assertEqual(ci_check["evidence"]["order_violation_count"], 1)
        self.assertFalse(ci_check["evidence"]["tiny_scorecard_plan_digest_gate_ready"])
        self.assertFalse(ci_check["evidence"]["baseline_candidate_threshold_boundary_gate_check_ready"])
        self.assertFalse(ci_check["evidence"]["baseline_candidate_threshold_boundary_gate_plan_check_ready"])
        self.assertFalse(ci_check["evidence"]["archived_path_portability_check_ready"])
        self.assertFalse(ci_check["evidence"]["promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
        self.assertEqual(build_ci_workflow_context(ci_hygiene)["python_version"], "3.11")
        self.assertEqual(build_ci_workflow_context(ci_hygiene)["order_violation_count"], 1)
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["tiny_scorecard_plan_digest_gate_ready"])
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["baseline_candidate_threshold_boundary_gate_check_ready"])
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["baseline_candidate_threshold_boundary_gate_plan_check_ready"])
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["archived_path_portability_check_ready"])
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["promoted_seed_receipt_contract_failure_smoke_plan_check_ready"])
        self.assertFalse(build_ci_workflow_context(ci_hygiene)["release_readiness_drift_contract_smoke_ready"])
        self.assertEqual(build_ci_workflow_hygiene_check(None, None)["status"], "warn")
        self.assertFalse(build_ci_workflow_context(None)["available"])

        self.assertEqual(coverage_check["status"], "pass")
        self.assertIn("line_coverage=90.16", coverage_check["detail"])
        self.assertEqual(coverage_check["evidence"]["fail_under"], 80.0)
        self.assertEqual(build_test_coverage_context(coverage)["coverage_gap"], 0.0)
        self.assertEqual(build_test_coverage_check({"summary": {"status": "pass", "threshold_enabled": False}}, None)["status"], "warn")
        self.assertEqual(build_test_coverage_check(None, None)["status"], "warn")
        self.assertFalse(build_test_coverage_context(None)["available"])


if __name__ == "__main__":
    unittest.main()
