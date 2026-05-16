from __future__ import annotations

import json
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
    fail_panels: int = 0,
    warn_panels: int = 0,
) -> Path:
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name).strip("_") or "readiness"
    panel_statuses = {
        "registry": "pass",
        "release_bundle": "pass",
        "project_audit": "pass",
        "release_gate": "pass" if gate_status == "pass" else "fail",
        "request_history": "pass" if request_status == "pass" else "warn",
        "maturity": "pass",
        "ci_workflow_hygiene": "pass" if ci_workflow_status == "pass" else "warn",
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
            "request_history_status": request_status,
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
            self.assertIn("ci_workflow_hygiene:pass->warn", delta["changed_panels"])
            self.assertIn("CI workflow hygiene regression", " ".join(report["recommendations"]))

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
            self.assertIn("changed_panels", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("ci_workflow_failed_check_delta", Path(outputs["delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Readiness Matrix", Path(outputs["markdown"]).read_text(encoding="utf-8"))

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
