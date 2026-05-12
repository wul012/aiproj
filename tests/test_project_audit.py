from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

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
                "tags": ["candidate", "keep"],
                "note": "ready card",
            }
        ],
    }
    model_card_path = root / "model-card" / "model_card.json"
    write_json(model_card_path, model_card)
    return model_card_path


class ProjectAuditTests(unittest.TestCase):
    def test_build_project_audit_passes_complete_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            model_card_path = make_model_card(root, registry_path)

            audit = build_project_audit(registry_path, model_card_path=model_card_path, generated_at="2026-05-12T00:00:00Z")

            self.assertEqual(audit["summary"]["overall_status"], "pass")
            self.assertEqual(audit["summary"]["fail_count"], 0)
            self.assertEqual(audit["summary"]["warn_count"], 0)
            self.assertEqual(audit["summary"]["ready_runs"], 1)
            self.assertEqual(audit["runs"][0]["experiment_card_exists"], True)
            self.assertIn("All audit checks passed", " ".join(audit["recommendations"]))

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
            self.assertIn("MiniGPT project audit", Path(outputs["html"]).read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
