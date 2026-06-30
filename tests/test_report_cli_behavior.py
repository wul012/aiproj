from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import torch

from tests._bootstrap import ensure_src_path

from minigpt.core.model import GPTConfig, MiniGPT
from minigpt.core.tokenizer import CharTokenizer
from minigpt.training.data_prep import build_prepared_dataset, write_prepared_dataset
from scripts import (
    build_dashboard,
    build_dataset_card,
    build_experiment_card,
    build_model_card,
    inspect_model,
)

ensure_src_path()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_dataset_dir(root: Path) -> Path:
    source = root / "sources"
    source.mkdir()
    (source / "demo.txt").write_text("人工智能\n机器学习\n数据治理\n", encoding="utf-8")
    dataset = build_prepared_dataset([source])
    out_dir = root / "datasets" / "demo" / "v1"
    write_prepared_dataset(
        dataset,
        out_dir,
        dataset_name="demo",
        dataset_version="v1",
        dataset_description="temporary CLI behavior fixture",
        source_roots=[source],
    )
    return out_dir


def make_run_dir(root: Path) -> Path:
    run_dir = root / "run-a"
    run_dir.mkdir()
    (run_dir / "checkpoint.pt").write_bytes(b"fake")
    write_json(run_dir / "train_config.json", {"tokenizer": "char", "max_iters": 4, "batch_size": 2, "block_size": 8})
    write_json(run_dir / "history_summary.json", {"best_val_loss": 0.9, "last_val_loss": 1.0})
    write_json(run_dir / "dataset_report.json", {"source_count": 1, "char_count": 42, "line_count": 3, "unique_char_count": 12})
    write_json(run_dir / "dataset_quality.json", {"status": "pass", "short_fingerprint": "abc123def456", "warning_count": 0, "issue_count": 0})
    write_json(
        run_dir / "dataset_version.json",
        {
            "dataset": {"id": "demo@v1", "name": "demo", "version": "v1"},
            "fingerprint": {"short": "abc123def456"},
        },
    )
    write_json(run_dir / "eval_report.json", {"loss": 1.1, "perplexity": 3.0})
    eval_dir = run_dir / "eval_suite"
    eval_dir.mkdir()
    write_json(eval_dir / "eval_suite.json", {"case_count": 2, "avg_unique_chars": 7.5, "results": []})
    write_json(run_dir / "run_notes.json", {"note": "candidate run", "tags": ["candidate", "keep"]})
    write_json(
        run_dir / "run_manifest.json",
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
        },
    )
    return run_dir


def make_registry(root: Path, run_dir: Path) -> Path:
    registry_path = root / "registry" / "registry.json"
    write_json(
        registry_path,
        {
            "schema_version": 1,
            "run_count": 1,
            "best_by_best_val_loss": {"name": "demo-run", "path": str(run_dir), "best_val_loss": 0.9},
            "loss_leaderboard": [
                {"rank": 1, "name": "demo-run", "path": str(run_dir), "best_val_loss": 0.9, "best_val_loss_delta": 0.0}
            ],
            "quality_counts": {"pass": 1},
            "generation_quality_counts": {"pass": 1},
            "tag_counts": {"candidate": 1},
            "dataset_versions": ["demo@v1"],
            "dataset_fingerprints": ["abc123def456"],
            "runs": [
                {
                    "name": "demo-run",
                    "path": str(run_dir),
                    "best_val_loss_rank": 1,
                    "best_val_loss": 0.9,
                    "best_val_loss_delta": 0.0,
                    "dataset_version": "demo@v1",
                    "dataset_fingerprint": "abc123def456",
                    "dataset_quality": "pass",
                    "eval_suite_cases": 2,
                    "generation_quality_status": "pass",
                    "generation_quality_cases": 2,
                    "artifact_count": 8,
                    "checkpoint_exists": True,
                    "dashboard_exists": False,
                    "note": "registry note",
                    "tags": ["candidate"],
                }
            ],
        },
    )
    return registry_path


class ReportCliBehaviorTests(unittest.TestCase):
    def test_build_dataset_card_main_writes_card_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_dir = make_dataset_dir(root)
            out_dir = root / "dataset-card"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = build_dataset_card.main(["--dataset-dir", str(dataset_dir), "--out-dir", str(out_dir)])

            self.assertEqual(exit_code, 0)
            self.assertIn("dataset_dir=", stdout.getvalue())
            self.assertIn("outputs=", stdout.getvalue())
            card = json.loads((out_dir / "dataset_card.json").read_text(encoding="utf-8"))
            self.assertEqual(card["dataset"]["id"], "demo@v1")
            self.assertTrue((out_dir / "dataset_card.md").is_file())
            self.assertTrue((out_dir / "dataset_card.html").is_file())

    def test_build_experiment_card_main_writes_card_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run_dir(root)
            registry = make_registry(root, run_dir)
            out_dir = root / "experiment-card"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = build_experiment_card.main(
                    ["--run-dir", str(run_dir), "--registry", str(registry), "--out-dir", str(out_dir)]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("status=ready", stdout.getvalue())
            self.assertIn("outputs=", stdout.getvalue())
            card = json.loads((out_dir / "experiment_card.json").read_text(encoding="utf-8"))
            self.assertEqual(card["summary"]["run_name"], "demo-run")
            self.assertTrue((out_dir / "experiment_card.md").is_file())
            self.assertTrue((out_dir / "experiment_card.html").is_file())

    def test_build_model_card_main_writes_card_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run_dir(root)
            registry = make_registry(root, run_dir)
            build_experiment_card.main(["--run-dir", str(run_dir), "--registry", str(registry), "--out-dir", str(run_dir)])
            out_dir = root / "model-card"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = build_model_card.main(["--registry", str(registry), "--out-dir", str(out_dir)])

            self.assertEqual(exit_code, 0)
            self.assertIn("run_count=1", stdout.getvalue())
            self.assertIn("experiment_cards=1", stdout.getvalue())
            card = json.loads((out_dir / "model_card.json").read_text(encoding="utf-8"))
            self.assertEqual(card["summary"]["best_run_name"], "demo-run")
            self.assertTrue((out_dir / "model_card.md").is_file())
            self.assertTrue((out_dir / "model_card.html").is_file())

    def test_inspect_model_main_writes_model_report_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8, dropout=0.0)
            model = MiniGPT(config)
            checkpoint_path = root / "checkpoint.pt"
            tokenizer_path = root / "tokenizer.json"
            out_dir = root / "model-report"
            torch.save(
                {
                    "config": config.__dict__,
                    "model": model.state_dict(),
                    "step": 3,
                    "last_loss": 1.23,
                    "tokenizer_type": "char",
                },
                checkpoint_path,
            )
            CharTokenizer.train("abcdefghijkl").save(tokenizer_path)

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = inspect_model.main(
                    [
                        "--checkpoint",
                        str(checkpoint_path),
                        "--tokenizer",
                        str(tokenizer_path),
                        "--out-dir",
                        str(out_dir),
                        "--device",
                        "cpu",
                        "--batch-size",
                        "2",
                        "--sequence-length",
                        "4",
                    ]
                )

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("model=MiniGPT", output)
            self.assertIn("tokenizer=char", output)
            self.assertIn("owned_sum_matches_total=True", output)
            self.assertIn("saved_json=", output)
            self.assertIn("saved_svg=", output)
            report = json.loads((out_dir / "model_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["model"], "MiniGPT")
            self.assertEqual(report["tensor_shapes"]["token_ids"], [2, 4])
            self.assertTrue(report["parameter_check"]["owned_sum_matches_total"])
            self.assertTrue((out_dir / "model_architecture.svg").is_file())

    def test_build_dashboard_main_writes_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run_dir(Path(tmp))
            out_path = run_dir / "dashboard.html"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = build_dashboard.main(["--run-dir", str(run_dir), "--out", str(out_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn(f"saved={out_path}", stdout.getvalue())
            self.assertIn("available_artifacts=", stdout.getvalue())
            html = out_path.read_text(encoding="utf-8")
            self.assertIn("MiniGPT experiment dashboard", html)
            self.assertIn("demo@v1", html)


if __name__ == "__main__":
    unittest.main()
