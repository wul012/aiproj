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


def make_release_inputs(root: Path, name: str = "candidate") -> tuple[Path, Path, Path]:
    run_dir = root / "run-a"
    run_dir.mkdir()
    registry_dir = root / "registry"
    model_dir = root / "model-card"
    audit_dir = root / "audit"
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
        "summary": {
            "overall_status": "pass",
            "score_percent": 100.0,
            "pass_count": 11,
            "warn_count": 0,
            "fail_count": 0,
            "ready_runs": 1,
        },
        "checks": [{"id": "ready_run", "title": "At least one ready run", "status": "pass", "detail": "1 ready run(s)."}],
        "recommendations": ["All audit checks passed."],
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
    return registry_path, model_path, audit_path


class ReleaseBundleTests(unittest.TestCase):
    def test_build_release_bundle_summarizes_ready_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path = make_release_inputs(root)

            bundle = build_release_bundle(
                registry_path,
                model_card_path=model_path,
                audit_path=audit_path,
                release_name="v26-demo",
                generated_at="2026-05-12T00:00:00Z",
            )

            self.assertEqual(bundle["summary"]["release_status"], "release-ready")
            self.assertEqual(bundle["summary"]["audit_status"], "pass")
            self.assertEqual(bundle["summary"]["best_run_name"], "candidate")
            self.assertGreaterEqual(bundle["summary"]["available_artifacts"], 7)
            self.assertEqual(bundle["top_runs"][0]["name"], "candidate")
            self.assertIn("Release evidence is complete", " ".join(bundle["recommendations"]))

    def test_build_release_bundle_marks_missing_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path = make_release_inputs(root)
            audit_path.unlink()

            bundle = build_release_bundle(registry_path, model_card_path=model_path)

            self.assertEqual(bundle["summary"]["release_status"], "needs-audit")
            self.assertIn("Generate project_audit.json", " ".join(bundle["recommendations"]))

    def test_write_release_bundle_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path = make_release_inputs(root)
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path)

            outputs = write_release_bundle_outputs(bundle, root / "release-bundle")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Evidence Artifacts", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT release bundle", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_release_bundle_html_escapes_run_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path, model_path, audit_path = make_release_inputs(root, name="<script>")
            bundle = build_release_bundle(registry_path, model_card_path=model_path, audit_path=audit_path, title="<Release>")

            html = render_release_bundle_html(bundle)

            self.assertIn("&lt;Release&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)


if __name__ == "__main__":
    unittest.main()
