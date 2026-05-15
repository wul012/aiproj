from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import experiment_card, experiment_card_artifacts
from minigpt.experiment_card import build_experiment_card, render_experiment_card_html, write_experiment_card_outputs


def make_card_run(root: Path) -> Path:
    run_dir = root / "run-a"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"fake")
    (run_dir / "train_config.json").write_text(
        json.dumps({"tokenizer": "char", "max_iters": 4, "batch_size": 2, "block_size": 8}),
        encoding="utf-8",
    )
    (run_dir / "history_summary.json").write_text(
        json.dumps({"best_val_loss": 0.9, "last_val_loss": 1.0}),
        encoding="utf-8",
    )
    (run_dir / "dataset_report.json").write_text(
        json.dumps({"source_count": 2, "char_count": 120, "line_count": 4, "unique_char_count": 30}),
        encoding="utf-8",
    )
    (run_dir / "dataset_quality.json").write_text(
        json.dumps({"status": "pass", "short_fingerprint": "abc123def456", "warning_count": 0, "issue_count": 0}),
        encoding="utf-8",
    )
    (run_dir / "eval_report.json").write_text(json.dumps({"loss": 1.1, "perplexity": 3.0}), encoding="utf-8")
    eval_dir = run_dir / "eval_suite"
    eval_dir.mkdir()
    (eval_dir / "eval_suite.json").write_text(
        json.dumps({"case_count": 2, "avg_unique_chars": 7.5, "results": []}),
        encoding="utf-8",
    )
    (run_dir / "run_notes.json").write_text(
        json.dumps({"note": "candidate run", "tags": ["candidate", "keep"]}),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "git": {"short_commit": "abc1234", "dirty": False},
                "data": {
                    "source": {"kind": "data-dir"},
                    "token_count": 100,
                    "train_token_count": 90,
                    "val_token_count": 10,
                },
                "training": {"tokenizer": "char", "device_used": "cpu", "start_step": 0, "end_step": 4},
                "model": {"parameter_count": 1234},
                "results": {"history_summary": {"best_val_loss": 0.9}},
            }
        ),
        encoding="utf-8",
    )
    return run_dir


class ExperimentCardTests(unittest.TestCase):
    def test_build_card_reads_run_and_registry_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_card_run(root)
            registry_path = root / "registry.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "run_count": 1,
                        "quality_counts": {"pass": 1},
                        "tag_counts": {"candidate": 1, "keep": 1},
                        "runs": [
                            {
                                "name": "demo-run",
                                "path": str(run_dir),
                                "git_commit": "abc1234",
                                "dataset_quality": "pass",
                                "dataset_fingerprint": "abc123def456",
                                "eval_suite_cases": 2,
                                "total_parameters": 1234,
                                "best_val_loss": 0.9,
                                "best_val_loss_rank": 1,
                                "best_val_loss_delta": 0.0,
                                "is_best_val_loss": True,
                                "note": "registry note",
                                "tags": ["candidate"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            card = build_experiment_card(run_dir, registry_path=registry_path, generated_at="2026-05-12T00:00:00Z")

            self.assertEqual(card["summary"]["run_name"], "demo-run")
            self.assertEqual(card["summary"]["status"], "ready")
            self.assertEqual(card["summary"]["best_val_loss_rank"], 1)
            self.assertEqual(card["summary"]["dataset_quality"], "pass")
            self.assertEqual(card["notes"]["tags"], ["candidate", "keep"])
            self.assertTrue(card["registry"]["matched_run"])
            self.assertIn("current best-val reference", " ".join(card["recommendations"]))

    def test_write_card_outputs_json_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_card_run(root)
            card = build_experiment_card(run_dir, generated_at="2026-05-12T00:00:00Z")

            outputs = write_experiment_card_outputs(card, run_dir)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("## Recommendations", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("MiniGPT experiment card", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_card_html_escapes_note_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_card_run(Path(tmp))
            (run_dir / "run_notes.json").write_text(
                json.dumps({"note": "<script>alert(1)</script>", "tags": ["<tag>"]}),
                encoding="utf-8",
            )
            card = build_experiment_card(run_dir, title="<Card>")

            html = render_experiment_card_html(card)

            self.assertIn("&lt;Card&gt;", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertIn("&lt;tag&gt;", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_experiment_card_facade_keeps_artifact_writer_identity(self) -> None:
        self.assertIs(experiment_card.render_experiment_card_html, experiment_card_artifacts.render_experiment_card_html)
        self.assertIs(
            experiment_card.write_experiment_card_outputs,
            experiment_card_artifacts.write_experiment_card_outputs,
        )


if __name__ == "__main__":
    unittest.main()
