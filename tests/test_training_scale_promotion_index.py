from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_promotion_index import (  # noqa: E402
    build_training_scale_promotion_index,
    render_training_scale_promotion_index_html,
    render_training_scale_promotion_index_markdown,
    write_training_scale_promotion_index_outputs,
)


class TrainingScalePromotionIndexTests(unittest.TestCase):
    def test_indexes_promoted_reports_and_builds_compare_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = make_promotion(root, "alpha", "promoted")
            beta = make_promotion(root, "beta", "promoted")

            report = build_training_scale_promotion_index(
                [alpha, beta],
                names=["alpha-run", "beta-run"],
                baseline="beta-run",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 2)
            self.assertTrue(report["summary"]["compare_command_ready"])
            self.assertEqual(report["comparison_inputs"]["baseline_name"], "beta-run")
            self.assertEqual(report["comparison_inputs"]["names"], ["alpha-run", "beta-run"])
            self.assertIn("scripts/compare_training_scale_runs.py", report["comparison_inputs"]["compare_command"])

    def test_excludes_review_and_blocked_reports_from_compare_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = make_promotion(root, "promoted", "promoted")
            review = make_promotion(root, "review", "review")
            blocked = make_promotion(root, "blocked", "blocked")

            report = build_training_scale_promotion_index([promoted, review, blocked])

            self.assertEqual(report["summary"]["promoted_count"], 1)
            self.assertEqual(report["summary"]["review_count"], 1)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertFalse(report["summary"]["compare_command_ready"])
            self.assertEqual(report["comparison_inputs"]["names"], ["promoted"])
            self.assertTrue(any("single promoted run" in item for item in report["recommendations"]))

    def test_baseline_must_be_promoted_for_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promoted = make_promotion(root, "promoted", "promoted")
            review = make_promotion(root, "review", "review")

            with self.assertRaises(ValueError):
                build_training_scale_promotion_index([promoted, review], baseline="review")

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promotion = make_promotion(root, "alpha", "promoted", title="<Index>")
            report = build_training_scale_promotion_index([promotion], names=["<alpha>"], title="<Index>")

            outputs = write_training_scale_promotion_index_outputs(report, root / "index")
            markdown = render_training_scale_promotion_index_markdown(report)
            html = render_training_scale_promotion_index_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["summary"]["promoted_count"], 1)
            self.assertIn("## Compare Inputs", markdown)
            self.assertIn("&lt;Index&gt;", html)
            self.assertIn("&lt;alpha&gt;", html)
            self.assertNotIn("<Index>", html)
            self.assertNotIn("<alpha>", html)


def make_promotion(root: Path, name: str, status: str, title: str | None = None) -> Path:
    promotion_root = root / name / "promotion"
    run_root = root / name / "scale-run"
    run_json = run_root / "training_scale_run.json"
    batch_json = run_root / "batch" / "training_portfolio_batch.json"
    portfolio_json = run_root / "batch" / "variants" / name / "training_portfolio.json"
    checkpoint = run_root / "batch" / "variants" / name / "runs" / name / "checkpoint.pt"
    registry = run_root / "batch" / "variants" / name / "registry" / "registry.json"
    narrative = run_root / "batch" / "variants" / name / "maturity-narrative" / "maturity_narrative.json"
    for path in [run_json, batch_json, portfolio_json, checkpoint, registry, narrative]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}" if path.suffix == ".json" else "checkpoint", encoding="utf-8")
    variant_status = "ready" if status == "promoted" else "review"
    report = {
        "title": title or f"{name} promotion",
        "generated_at": "2026-05-14T00:00:00Z",
        "handoff_path": str(root / name / "handoff" / "training_scale_handoff.json"),
        "project_root": str(root),
        "out_root": str(run_root),
        "training_scale_run_path": str(run_json),
        "batch_path": str(batch_json),
        "summary": {
            "promotion_status": status,
            "handoff_status": "completed" if status != "blocked" else "failed",
            "scale_run_status": "completed" if status != "blocked" else "blocked",
            "batch_status": "completed" if status != "blocked" else "skipped",
            "variant_count": 1,
            "ready_variant_count": 1 if status == "promoted" else 0,
            "checkpoint_count": 1,
            "registry_count": 1,
            "maturity_narrative_count": 1,
            "required_artifact_count": 9,
            "available_required_artifact_count": 9 if status == "promoted" else 7,
            "blocker_count": 1 if status == "blocked" else 0,
            "review_item_count": 1 if status == "review" else 0,
        },
        "variants": [
            {
                "name": f"{name}-variant",
                "promotion_status": variant_status,
                "portfolio_json": str(portfolio_json),
                "missing_required": [] if status == "promoted" else ["registry", "maturity_narrative"],
                "artifact_rows": [
                    {"key": "checkpoint", "path": str(checkpoint), "exists": True},
                    {"key": "registry", "path": str(registry), "exists": status == "promoted"},
                    {"key": "maturity_narrative", "path": str(narrative), "exists": status == "promoted"},
                ],
            }
        ],
        "blockers": ["handoff status is failed"] if status == "blocked" else [],
        "review_items": ["variant missing registry, maturity_narrative"] if status == "review" else [],
    }
    write_json(promotion_root / "training_scale_promotion.json", report)
    return promotion_root


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
