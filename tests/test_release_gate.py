from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.release_gate import (
    build_release_gate,
    exit_code_for_gate,
    render_release_gate_html,
    write_release_gate_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_bundle(
    root: Path,
    *,
    release_name: str = "v27-demo",
    release_status: str = "release-ready",
    audit_status: str = "pass",
    audit_score: float | None = 100.0,
    ready_runs: int = 1,
    missing_artifacts: int = 0,
    warnings: list[str] | None = None,
) -> Path:
    bundle = {
        "schema_version": 1,
        "title": "MiniGPT release bundle",
        "release_name": release_name,
        "generated_at": "2026-05-12T00:00:00Z",
        "summary": {
            "release_status": release_status,
            "audit_status": audit_status,
            "audit_score_percent": audit_score,
            "run_count": 2,
            "best_run_name": "candidate",
            "best_val_loss": 0.75,
            "ready_runs": ready_runs,
            "available_artifacts": 9,
            "missing_artifacts": missing_artifacts,
        },
        "artifacts": [
            {"key": "registry_json", "title": "Registry JSON", "path": str(root / "registry.json"), "exists": True},
            {"key": "project_audit_json", "title": "Project audit JSON", "path": str(root / "audit.json"), "exists": missing_artifacts == 0},
        ],
        "top_runs": [
            {
                "name": "candidate",
                "path": str(root / "run-a"),
                "status": "ready",
                "best_val_loss_rank": 1,
                "best_val_loss": 0.75,
                "best_val_loss_delta": 0.0,
                "dataset_quality": "pass",
                "eval_suite_cases": 3,
            }
        ],
        "audit_checks": [
            {"id": "ready_run", "title": "At least one ready run", "status": audit_status, "detail": "1 ready run."}
        ],
        "recommendations": ["Release evidence is complete."],
        "warnings": warnings or [],
    }
    path = root / "release-bundle" / "release_bundle.json"
    write_json(path, bundle)
    return path


class ReleaseGateTests(unittest.TestCase):
    def test_build_release_gate_passes_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp))

            gate = build_release_gate(bundle_path, generated_at="2026-05-12T00:00:00Z")

            self.assertEqual(gate["summary"]["gate_status"], "pass")
            self.assertEqual(gate["summary"]["decision"], "approved")
            self.assertEqual(gate["summary"]["fail_count"], 0)
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertIn("Release gate passed", " ".join(gate["recommendations"]))

    def test_build_release_gate_warns_for_bundle_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), warnings=["model card was auto-discovered"])

            gate = build_release_gate(bundle_path)

            self.assertEqual(gate["summary"]["gate_status"], "warn")
            self.assertEqual(gate["summary"]["decision"], "needs-review")
            self.assertEqual(exit_code_for_gate(gate), 0)
            self.assertEqual(exit_code_for_gate(gate, fail_on_warn=True), 1)
            self.assertIn("Bundle has no warnings", " ".join(gate["recommendations"]))

    def test_build_release_gate_fails_for_incomplete_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(
                Path(tmp),
                release_status="blocked",
                audit_status="fail",
                audit_score=40.0,
                ready_runs=0,
                missing_artifacts=2,
            )

            gate = build_release_gate(bundle_path, minimum_audit_score=90.0, minimum_ready_runs=1)

            self.assertEqual(gate["summary"]["gate_status"], "fail")
            self.assertEqual(gate["summary"]["decision"], "blocked")
            self.assertGreater(gate["summary"]["fail_count"], 0)
            self.assertEqual(exit_code_for_gate(gate), 1)
            self.assertIn("Release gate failed", " ".join(gate["recommendations"]))

    def test_write_release_gate_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_path = make_bundle(root)
            gate = build_release_gate(bundle_path)

            outputs = write_release_gate_outputs(gate, root / "release-gate")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Checks", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT release gate", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_release_gate_html_escapes_release_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = make_bundle(Path(tmp), release_name="<script>")
            gate = build_release_gate(bundle_path, title="<Gate>")

            html = render_release_gate_html(gate)

            self.assertIn("&lt;Gate&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<h1><Gate>", html)


if __name__ == "__main__":
    unittest.main()
