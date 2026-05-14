from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_promotion import (  # noqa: E402
    build_training_scale_promotion,
    render_training_scale_promotion_html,
    render_training_scale_promotion_markdown,
    write_training_scale_promotion_outputs,
)


class TrainingScalePromotionTests(unittest.TestCase):
    def test_promotes_completed_handoff_with_full_variant_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_dir = make_completed_handoff_tree(root)

            report = build_training_scale_promotion(handoff_dir, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["promotion_status"], "promoted")
            self.assertEqual(report["summary"]["ready_variant_count"], 1)
            self.assertEqual(report["summary"]["checkpoint_count"], 1)
            self.assertEqual(report["summary"]["registry_count"], 1)
            self.assertFalse(report["blockers"])
            self.assertFalse(report["review_items"])

    def test_blocks_failed_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_dir = root / "handoff"
            write_json(
                handoff_dir / "training_scale_handoff.json",
                {
                    "summary": {"handoff_status": "failed"},
                    "execution": {"status": "failed", "returncode": 1},
                    "command": ["python", "scripts/run_training_scale_plan.py", "--project-root", str(root), "--out-root", "runs/scale"],
                    "artifact_rows": [],
                },
            )

            report = build_training_scale_promotion(handoff_dir)

            self.assertEqual(report["summary"]["promotion_status"], "blocked")
            self.assertTrue(any("handoff status" in item for item in report["blockers"]))
            self.assertTrue(any("Stop promotion" in item for item in report["recommendations"]))

    def test_reviews_completed_handoff_with_missing_variant_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_dir = make_completed_handoff_tree(root, missing={"registry", "maturity_narrative"})

            report = build_training_scale_promotion(handoff_dir)

            self.assertEqual(report["summary"]["promotion_status"], "review")
            self.assertEqual(report["summary"]["ready_variant_count"], 0)
            self.assertFalse(report["blockers"])
            self.assertIn("registry", report["variants"][0]["missing_required"])
            self.assertIn("maturity_narrative", report["variants"][0]["missing_required"])

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_dir = make_completed_handoff_tree(root)
            report = build_training_scale_promotion(handoff_dir, title="<Promotion>")

            outputs = write_training_scale_promotion_outputs(report, root / "promotion")
            markdown = render_training_scale_promotion_markdown(report)
            html = render_training_scale_promotion_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["promotion_status"], "promoted")
            self.assertIn("## Variant Readiness", markdown)
            self.assertIn("&lt;Promotion&gt;", html)
            self.assertNotIn("<Promotion>", html)


def make_completed_handoff_tree(root: Path, missing: set[str] | None = None) -> Path:
    missing = missing or set()
    scale_root = root / "runs" / "scale"
    batch_root = scale_root / "batch"
    variant_root = batch_root / "variants" / "scale-smoke"
    run_dir = variant_root / "runs" / "scale-smoke"
    handoff_dir = root / "handoff"

    artifact_paths = {
        "run_dir": run_dir,
        "checkpoint": run_dir / "checkpoint.pt",
        "run_manifest": run_dir / "run_manifest.json",
        "eval_suite": run_dir / "eval_suite" / "eval_suite.json",
        "generation_quality": run_dir / "eval_suite" / "generation-quality" / "generation_quality.json",
        "benchmark_scorecard": run_dir / "benchmark-scorecard" / "benchmark_scorecard.json",
        "dataset_card": variant_root / "datasets" / "sample-zh" / "v77-smoke" / "dataset_card.json",
        "registry": variant_root / "registry" / "registry.json",
        "maturity_summary": variant_root / "maturity-summary" / "maturity_summary.json",
        "maturity_narrative": variant_root / "maturity-narrative" / "maturity_narrative.json",
    }
    for key, path in artifact_paths.items():
        if key == "run_dir":
            path.mkdir(parents=True, exist_ok=True)
        elif key not in missing:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}" if path.suffix == ".json" else "artifact", encoding="utf-8")

    portfolio_json = variant_root / "training_portfolio.json"
    portfolio_html = variant_root / "training_portfolio.html"
    portfolio = {
        "execution": {"status": "completed", "step_count": 9, "completed_steps": 9, "failed_step": None},
        "run_name": "scale-smoke",
        "dataset_name": "sample-zh",
        "dataset_version": "v77-smoke",
        "artifacts": {key: rel(root, value) for key, value in artifact_paths.items()},
    }
    write_json(portfolio_json, portfolio)
    portfolio_html.write_text("<html>portfolio</html>", encoding="utf-8")

    write_json(
        scale_root / "training_scale_run.json",
        {
            "status": "completed",
            "allowed": True,
            "gate_profile": "review",
            "gate": {"overall_status": "warn"},
            "batch_summary": {"status": "completed", "variant_count": 1, "completed_variant_count": 1},
        },
    )
    (scale_root / "training_scale_run.html").write_text("<html>scale</html>", encoding="utf-8")
    write_json(
        batch_root / "training_portfolio_batch.json",
        {
            "execution": {"status": "completed", "variant_count": 1, "completed_variant_count": 1, "comparison_status": "skipped"},
            "variant_results": [
                {
                    "name": "scale-smoke",
                    "status": "completed",
                    "portfolio_json": rel(root, portfolio_json),
                    "portfolio_html": rel(root, portfolio_html),
                    "step_count": 9,
                    "completed_steps": 9,
                }
            ],
        },
    )
    (batch_root / "training_portfolio_batch.html").write_text("<html>batch</html>", encoding="utf-8")
    write_json(
        handoff_dir / "training_scale_handoff.json",
        {
            "summary": {"handoff_status": "completed", "artifact_count": 6, "available_artifact_count": 6},
            "execution": {"status": "completed", "returncode": 0},
            "command": [
                "python",
                "scripts/run_training_scale_plan.py",
                "--project-root",
                str(root),
                "--out-root",
                "runs/scale",
                "--execute",
            ],
            "artifact_rows": [
                {"key": "training_scale_run_json", "path": "runs/scale/training_scale_run.json", "exists": True},
                {"key": "training_scale_run_html", "path": "runs/scale/training_scale_run.html", "exists": True},
                {"key": "batch_json", "path": "runs/scale/batch/training_portfolio_batch.json", "exists": True},
                {"key": "batch_html", "path": "runs/scale/batch/training_portfolio_batch.html", "exists": True},
                {"key": "variant_portfolio_reports", "path": "runs/scale/batch/variants", "exists": True, "count": 1},
                {"key": "variant_checkpoints", "path": "runs/scale/batch/variants", "exists": True, "count": 1},
            ],
        },
    )
    return handoff_dir


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


if __name__ == "__main__":
    unittest.main()
