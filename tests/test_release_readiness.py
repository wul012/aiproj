from __future__ import annotations

import json
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
    include_request_history: bool = True,
    include_ci_workflow: bool = True,
    ci_workflow_status: str = "pass",
) -> Path:
    runs = root / "runs"
    registry_path = runs / "registry" / "registry.json"
    audit_path = runs / "audit" / "project_audit.json"
    request_path = runs / "request-history-summary" / "request_history_summary.json"
    gate_path = runs / "release-gate" / "gate_report.json"
    maturity_path = runs / "maturity-summary" / "maturity_summary.json"
    ci_workflow_path = runs / "ci-workflow-hygiene" / "ci_workflow_hygiene.json"
    bundle_path = runs / "release-bundle" / "release_bundle.json"
    artifact_path = runs / "request-history-summary" / "request_history_summary.html"
    ci_artifact_path = runs / "ci-workflow-hygiene" / "ci_workflow_hygiene.html"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("<html></html>", encoding="utf-8")
    ci_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    ci_artifact_path.write_text("<html></html>", encoding="utf-8")
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
                "ci_workflow_status": ci_workflow_status if include_ci_workflow else None,
                "ci_workflow_failed_checks": 0 if ci_workflow_status == "pass" else 1,
                "ci_workflow_node24_actions": 2 if include_ci_workflow else None,
            },
            "checks": [
                {"id": "ready_run", "status": "pass", "title": "At least one ready run", "detail": "1 ready run."},
                {"id": "request_history_summary", "status": "pass", "title": "Request history summary is clean", "detail": "status=pass."},
                {"id": "ci_workflow_hygiene", "status": ci_workflow_status, "title": "CI workflow hygiene is clean", "detail": f"status={ci_workflow_status}."},
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
    if include_gate:
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
                },
                "checks": [
                    {"id": "request_history_summary_audit_check", "status": gate_status, "title": "Request history summary audit check passed", "detail": "request_history_summary=pass." if gate_status == "pass" else "missing required audit check: request_history_summary."}
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
                "ci_workflow_status": ci_workflow_status if include_ci_workflow else None,
                "ci_workflow_failed_checks": 0 if ci_workflow_status == "pass" else 1,
                "ci_workflow_node24_actions": 2 if include_ci_workflow else None,
                "available_artifacts": len(artifact_rows),
                "missing_artifacts": 0,
            },
            "inputs": {
                "registry_path": str(registry_path),
                "project_audit_path": str(audit_path),
                "request_history_summary_path": str(request_path) if include_request_history else None,
                "ci_workflow_hygiene_path": str(ci_workflow_path) if include_ci_workflow else None,
            },
            "artifacts": artifact_rows,
            "ci_workflow_context": {
                "status": ci_workflow_status if include_ci_workflow else None,
                "failed_check_count": 0 if ci_workflow_status == "pass" else 1,
                "node24_native_action_count": 2 if include_ci_workflow else None,
                "path": str(ci_workflow_path) if include_ci_workflow else None,
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
            self.assertEqual({panel["status"] for panel in report["panels"]}, {"pass"})
            self.assertIn("ci_workflow_hygiene", {panel["key"] for panel in report["panels"]})
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
            ci_panel = next(panel for panel in report["panels"] if panel["key"] == "ci_workflow_hygiene")
            self.assertEqual(ci_panel["status"], "pass")
            self.assertIn("source=bundle summary/context", ci_panel["detail"])

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
            ci_panel = next(panel for panel in report["panels"] if panel["key"] == "ci_workflow_hygiene")
            self.assertEqual(ci_panel["status"], "warn")
            self.assertIn("Review warning panel: CI Workflow Hygiene", " ".join(report["actions"]))

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
            self.assertIn("&lt;Readiness&gt;", html)
            self.assertNotIn("<h1><Readiness>", html)

    def test_release_readiness_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(release_readiness_facade.render_release_readiness_html, release_readiness_artifacts.render_release_readiness_html)
        self.assertIs(release_readiness_facade.render_release_readiness_markdown, release_readiness_artifacts.render_release_readiness_markdown)
        self.assertIs(release_readiness_facade.write_release_readiness_outputs, release_readiness_artifacts.write_release_readiness_outputs)
        self.assertIs(release_readiness_facade.write_release_readiness_json, release_readiness_artifacts.write_release_readiness_json)


if __name__ == "__main__":
    unittest.main()
