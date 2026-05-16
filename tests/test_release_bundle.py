from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_bundle import build_release_bundle, render_release_bundle_html, write_release_bundle_outputs


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_release_inputs(root: Path, name: str = "candidate") -> tuple[Path, Path, Path, Path, Path]:
    run_dir = root / "run-a"
    run_dir.mkdir()
    registry_dir = root / "registry"
    model_dir = root / "model-card"
    audit_dir = root / "audit"
    request_dir = root / "request-history-summary"
    ci_dir = root / "ci-workflow-hygiene"
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
        "ci_workflow_hygiene_path": str(ci_dir / "ci_workflow_hygiene.json"),
        "summary": {
            "overall_status": "pass",
            "score_percent": 100.0,
            "pass_count": 12,
            "warn_count": 0,
            "fail_count": 0,
            "ready_runs": 1,
            "request_history_status": "pass",
            "request_history_records": 4,
            "ci_workflow_status": "pass",
            "ci_workflow_failed_checks": 0,
            "ci_workflow_node24_actions": 2,
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
            "python_version": "3.11",
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
            "python_version": "3.11",
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
    ci_workflow_hygiene_path = ci_dir / "ci_workflow_hygiene.json"
    write_json(ci_workflow_hygiene_path, ci_workflow_hygiene)
    (ci_dir / "ci_workflow_hygiene.md").write_text("# ci workflow hygiene", encoding="utf-8")
    (ci_dir / "ci_workflow_hygiene.html").write_text("<html></html>", encoding="utf-8")
    return registry_path, model_path, audit_path, request_summary_path, ci_workflow_hygiene_path


class ReleaseBundleTests(unittest.TestCase):
    def test_build_release_bundle_summarizes_ready_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, request_summary_path, _ci_workflow_hygiene_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                request_history_summary_path=request_summary_path,
                release_name="v26-demo",
                generated_at="2026-05-12T00:00:00Z",
            )

            self.assertEqual(bundle["summary"]["release_status"], "release-ready")
            self.assertEqual(bundle["summary"]["audit_status"], "pass")
            self.assertEqual(bundle["summary"]["request_history_status"], "pass")
            self.assertEqual(bundle["summary"]["ci_workflow_status"], "pass")
            self.assertEqual(bundle["summary"]["ci_workflow_failed_checks"], 0)
            self.assertEqual(bundle["summary"]["best_run_name"], "candidate")
            self.assertIn("request_history_summary_json", {item["key"] for item in bundle["artifacts"]})
            self.assertIn("ci_workflow_hygiene_json", {item["key"] for item in bundle["artifacts"]})
            self.assertEqual(bundle["ci_workflow_context"]["status"], "pass")
            self.assertGreaterEqual(bundle["summary"]["available_artifacts"], 10)
            self.assertEqual(bundle["top_runs"][0]["name"], "candidate")
            self.assertIn("Release evidence is complete", " ".join(bundle["recommendations"]))

    def test_build_release_bundle_accepts_explicit_ci_workflow_hygiene_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, ci_workflow_hygiene_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                ci_workflow_hygiene_path=ci_workflow_hygiene_path,
            )

            self.assertEqual(bundle["inputs"]["ci_workflow_hygiene_path"], str(ci_workflow_hygiene_path))
            self.assertEqual(bundle["summary"]["ci_workflow_node24_actions"], 2)
            self.assertIn("ci_workflow_hygiene_html", {item["key"] for item in bundle["artifacts"]})

    def test_build_release_bundle_marks_missing_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _ci_workflow_hygiene_path = make_release_inputs(root)
            audit_path.unlink()

            bundle = build_release_bundle(registry_path, model_card_path=model_path)

            self.assertEqual(bundle["summary"]["release_status"], "needs-audit")
            self.assertIn("Generate project_audit.json", " ".join(bundle["recommendations"]))

    def test_write_release_bundle_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _ci_workflow_hygiene_path = make_release_inputs(root)
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path)

            outputs = write_release_bundle_outputs(bundle, root / "release-bundle")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Evidence Artifacts", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("CI workflow status", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT release bundle", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_release_bundle_html_escapes_run_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path, _request_summary_path, _ci_workflow_hygiene_path = make_release_inputs(root, name="<script>")
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path, title="<Release>")

            html = render_release_bundle_html(bundle)

            self.assertIn("&lt;Release&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)


if __name__ == "__main__":
    unittest.main()
