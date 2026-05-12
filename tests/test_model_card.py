from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model_card import build_model_card, render_model_card_html, write_model_card_outputs


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_registry(root: Path, names: tuple[str, str] = ("candidate", "baseline")) -> Path:
    run_a = root / "run-a"
    run_b = root / "run-b"
    run_a.mkdir()
    run_b.mkdir()
    registry = {
        "schema_version": 1,
        "run_count": 2,
        "best_by_best_val_loss": {"name": names[0], "path": str(run_a), "best_val_loss": 0.88},
        "loss_leaderboard": [
            {"rank": 1, "name": names[0], "path": str(run_a), "best_val_loss": 0.88, "best_val_loss_delta": 0.0},
            {"rank": 2, "name": names[1], "path": str(run_b), "best_val_loss": 1.2, "best_val_loss_delta": 0.32},
        ],
        "quality_counts": {"pass": 1, "warn": 1},
        "generation_quality_counts": {"pass": 1, "warn": 1},
        "tag_counts": {"candidate": 1, "review": 1},
        "dataset_fingerprints": ["abc123def456"],
        "runs": [
            {
                "name": names[0],
                "path": str(run_a),
                "best_val_loss_rank": 1,
                "best_val_loss": 0.88,
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
                "note": "best run",
                "tags": ["candidate"],
            },
            {
                "name": names[1],
                "path": str(run_b),
                "best_val_loss_rank": 2,
                "best_val_loss": 1.2,
                "best_val_loss_delta": 0.32,
                "dataset_quality": "warn",
                "eval_suite_cases": 3,
                "generation_quality_status": "warn",
                "generation_quality_cases": 3,
                "generation_quality_pass_count": 2,
                "generation_quality_warn_count": 1,
                "generation_quality_fail_count": 0,
                "artifact_count": 10,
                "checkpoint_exists": True,
                "dashboard_exists": False,
                "note": "needs review",
                "tags": ["review"],
            },
        ],
    }
    registry_path = root / "registry" / "registry.json"
    write_json(registry_path, registry)
    return registry_path


def make_experiment_cards(root: Path) -> None:
    write_json(
        root / "run-a" / "experiment_card.json",
        {
            "run_dir": str(root / "run-a"),
            "summary": {"status": "ready", "best_val_loss_rank": 1},
            "notes": {"note": "card note", "tags": ["candidate", "keep"]},
            "recommendations": ["Use this run as the current reference."],
        },
    )
    write_json(
        root / "run-b" / "experiment_card.json",
        {
            "run_dir": str(root / "run-b"),
            "summary": {"status": "review", "best_val_loss_rank": 2},
            "notes": {"note": "review card", "tags": ["review"]},
            "recommendations": ["Review dataset quality warnings."],
        },
    )


class ModelCardTests(unittest.TestCase):
    def test_build_model_card_summarizes_registry_and_experiment_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            make_experiment_cards(root)

            card = build_model_card(registry_path, generated_at="2026-05-12T00:00:00Z")

            self.assertEqual(card["summary"]["run_count"], 2)
            self.assertEqual(card["summary"]["best_run_name"], "candidate")
            self.assertEqual(card["summary"]["ready_runs"], 1)
            self.assertEqual(card["summary"]["review_runs"], 1)
            self.assertEqual(card["coverage"]["experiment_cards_found"], 2)
            self.assertEqual(card["coverage"]["experiment_card_coverage"], 1.0)
            self.assertEqual(card["coverage"]["generation_quality_runs"], 2)
            self.assertEqual(card["generation_quality_counts"], {"pass": 1, "warn": 1})
            self.assertEqual(card["top_runs"][0]["name"], "candidate")
            self.assertEqual(card["runs"][0]["status"], "ready")
            self.assertEqual(card["runs"][0]["generation_quality_status"], "pass")
            self.assertEqual(card["runs"][0]["tags"], ["candidate", "keep"])
            self.assertIn("non-pass generation quality", " ".join(card["recommendations"]))
            self.assertIn("best ready run", " ".join(card["recommendations"]))

    def test_build_model_card_recommends_missing_experiment_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = make_registry(Path(tmp))

            card = build_model_card(registry_path)

            self.assertEqual(card["coverage"]["experiment_cards_found"], 0)
            self.assertIn("Generate missing experiment cards", " ".join(card["recommendations"]))

    def test_write_model_card_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            make_experiment_cards(root)
            card = build_model_card(registry_path, generated_at="2026-05-12T00:00:00Z")

            outputs = write_model_card_outputs(card, root / "model-card")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Top Runs", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT model card", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_model_card_html_escapes_run_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root, names=("<script>", "baseline"))
            make_experiment_cards(root)
            card = build_model_card(registry_path, title="<Model Card>")

            html = render_model_card_html(card)

            self.assertIn("&lt;Model Card&gt;", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<strong><script>", html)


if __name__ == "__main__":
    unittest.main()
