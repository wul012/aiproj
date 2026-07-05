from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from minigpt import model_card_artifacts
from minigpt import model_card as model_card_facade
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
        "dataset_versions": ["demo-card@candidate", "demo-card@baseline"],
        "dataset_fingerprints": ["abc123def456"],
        "dataset_dedupe_policy_counts": {"none": 1, "exact-source-content": 1},
        "dataset_snapshot_summary": {
            "run_count": 2,
            "snapshot_run_count": 2,
            "missing_snapshot_count": 0,
            "dataset_version_count": 2,
            "dataset_fingerprint_count": 1,
            "dedupe_policy_count": 2,
            "source_order_digest_count": 2,
            "skipped_source_run_count": 1,
            "total_included_source_count": 5,
            "total_skipped_source_count": 1,
            "total_char_count": 230,
        },
        "runs": [
            {
                "name": names[0],
                "path": str(run_a),
                "best_val_loss_rank": 1,
                "best_val_loss": 0.88,
                "best_val_loss_delta": 0.0,
                "dataset_version": "demo-card@candidate",
                "dataset_fingerprint": "abc123def456",
                "dataset_dedupe_policy": "exact-source-content",
                "dataset_source_order_digest": "order-candidate",
                "dataset_included_source_count": 2,
                "dataset_skipped_source_count": 1,
                "dataset_char_count": 90,
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
                "dataset_version": "demo-card@baseline",
                "dataset_fingerprint": "abc123def456",
                "dataset_dedupe_policy": "none",
                "dataset_source_order_digest": "order-baseline",
                "dataset_included_source_count": 3,
                "dataset_skipped_source_count": 0,
                "dataset_char_count": 140,
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
            self.assertEqual(card["coverage"]["dataset_version_count"], 2)
            self.assertEqual(card["coverage"]["dataset_snapshot_runs"], 2)
            self.assertEqual(card["coverage"]["dataset_snapshot_coverage"], 1.0)
            self.assertEqual(card["coverage"]["dataset_skipped_source_runs"], 1)
            self.assertEqual(card["dataset_snapshot_summary"]["skipped_source_run_count"], 1)
            self.assertEqual(card["dataset_dedupe_policy_counts"], {"none": 1, "exact-source-content": 1})
            self.assertEqual(card["generation_quality_counts"], {"pass": 1, "warn": 1})
            self.assertEqual(card["top_runs"][0]["name"], "candidate")
            self.assertEqual(card["top_runs"][0]["dataset_dedupe_policy"], "exact-source-content")
            self.assertEqual(card["runs"][0]["status"], "ready")
            self.assertEqual(card["runs"][0]["generation_quality_status"], "pass")
            self.assertEqual(card["runs"][0]["tags"], ["candidate", "keep"])
            self.assertIn("skipped dataset sources", " ".join(card["recommendations"]))
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
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("Dataset Snapshot Summary", markdown)
            self.assertIn("dedupe=exact-source-content", markdown)
            self.assertIn("MiniGPT model card", html)
            self.assertIn("Dataset Snapshot Summary", html)
            self.assertIn("dedupe=exact-source-content", html)

    def test_build_model_card_script_prints_dataset_snapshot_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_registry(root)
            make_experiment_cards(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_model_card.py"),
                    "--registry",
                    str(registry_path),
                    "--out-dir",
                    str(root / "script-model-card"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("dataset_snapshot_runs=2", completed.stdout)
            self.assertIn("dataset_snapshot_coverage=1.0", completed.stdout)
            self.assertIn("dataset_snapshot_summary=", completed.stdout)

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

    def test_facade_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(model_card_facade.write_model_card_outputs, model_card_artifacts.write_model_card_outputs)
        self.assertIs(model_card_facade.render_model_card_html, model_card_artifacts.render_model_card_html)
        self.assertIs(model_card_facade.render_model_card_markdown, model_card_artifacts.render_model_card_markdown)


if __name__ == "__main__":
    unittest.main()
