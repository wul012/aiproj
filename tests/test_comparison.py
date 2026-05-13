from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.comparison import (
    build_comparison_report,
    render_comparison_html,
    render_comparison_markdown,
    summarize_run,
    write_comparison_csv,
    write_comparison_outputs,
    write_comparison_svg,
)


def make_run(
    root: Path,
    name: str,
    best_val: float,
    eval_loss: float,
    params: int,
    *,
    tokenizer: str = "char",
    max_iters: int = 2,
    dataset_version: str = "demo-zh@v1",
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 32,
) -> Path:
    run_dir = root / name
    run_dir.mkdir()
    config = {"n_layer": n_layer, "n_head": n_head, "n_embd": n_embd, "block_size": 16, "vocab_size": 20}
    fingerprint = f"{name}12345678"
    (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": tokenizer, "max_iters": max_iters}), encoding="utf-8")
    (run_dir / "history_summary.json").write_text(
        json.dumps({"best_val_loss": best_val, "last_val_loss": best_val + 0.1}),
        encoding="utf-8",
    )
    (run_dir / "eval_report.json").write_text(json.dumps({"loss": eval_loss, "perplexity": 10.0}), encoding="utf-8")
    (run_dir / "dataset_quality.json").write_text(json.dumps({"status": "pass", "short_fingerprint": fingerprint}), encoding="utf-8")
    (run_dir / "dataset_version.json").write_text(
        json.dumps({"dataset": {"id": dataset_version}, "stats": {"short_fingerprint": fingerprint}}),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "data": {
                    "token_count": 100,
                    "train_token_count": 90,
                    "val_token_count": 10,
                    "dataset_version": {"id": dataset_version, "short_fingerprint": fingerprint},
                    "dataset_quality": {"status": "pass", "short_fingerprint": fingerprint},
                },
                "training": {"tokenizer": tokenizer, "args": {"max_iters": max_iters}, "end_step": max_iters},
                "model": {"parameter_count": params, "config": config},
                "results": {"history_summary": {"best_val_loss": best_val, "last_val_loss": best_val + 0.1}},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.jsonl").write_text('{"step": 1}\n{"step": 2}\n', encoding="utf-8")
    report_dir = run_dir / "model_report"
    report_dir.mkdir()
    (report_dir / "model_report.json").write_text(
        json.dumps(
            {
                "total_parameters": params,
                "tokenizer": tokenizer,
                "config": config,
            }
        ),
        encoding="utf-8",
    )
    return run_dir


class ComparisonTests(unittest.TestCase):
    def test_summarize_run_reads_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = make_run(Path(tmp), "tiny", best_val=2.0, eval_loss=2.2, params=100)

            summary = summarize_run(run)

            self.assertEqual(summary.name, "tiny")
            self.assertEqual(summary.metrics_records, 2)
            self.assertEqual(summary.best_val_loss, 2.0)
            self.assertEqual(summary.total_parameters, 100)
            self.assertEqual(summary.dataset_version, "demo-zh@v1")
            self.assertEqual(summary.token_count, 100)
            self.assertIn("P=100", summary.model_signature)

    def test_build_comparison_report_picks_best(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = make_run(root, "a", best_val=2.0, eval_loss=3.0, params=100)
            b = make_run(root, "b", best_val=1.5, eval_loss=2.5, params=120)

            report = build_comparison_report([a, b], names=["small", "wide"])

            self.assertEqual(report["run_count"], 2)
            self.assertEqual(report["best_by_best_val_loss"]["name"], "wide")
            self.assertEqual(report["best_by_eval_loss"]["name"], "wide")
            self.assertEqual(report["baseline"]["name"], "small")

    def test_build_comparison_report_records_baseline_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = make_run(root, "a", best_val=2.0, eval_loss=3.0, params=100, n_embd=16)
            b = make_run(root, "b", best_val=1.5, eval_loss=2.5, params=160, n_embd=32)

            report = build_comparison_report([a, b], names=["small", "wide"], baseline="small", generated_at="2026-05-13T00:00:00Z")
            wide = next(row for row in report["baseline_deltas"] if row["name"] == "wide")

            self.assertEqual(report["baseline"]["name"], "small")
            self.assertAlmostEqual(wide["best_val_loss_delta"], -0.5)
            self.assertEqual(wide["best_val_loss_relation"], "improved")
            self.assertTrue(wide["model_signature_changed"])
            self.assertEqual(report["summary"]["improved_best_val_loss_count"], 1)
            self.assertEqual(report["summary"]["model_signature_count"], 2)
            self.assertTrue(report["recommendations"])

    def test_build_comparison_report_rejects_name_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            build_comparison_report(["a", "b"], names=["only-one"])

    def test_write_comparison_csv_and_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = make_run(root, "a", best_val=2.0, eval_loss=3.0, params=100)
            report = build_comparison_report([run])
            csv_path = root / "comparison.csv"
            svg_path = root / "comparison.svg"

            write_comparison_csv(report, csv_path)
            write_comparison_svg(report, svg_path)

            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("best_val_loss", csv_text)
            self.assertIn("best_val_loss_delta", csv_text)
            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))

    def test_write_comparison_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = make_run(root, "a", best_val=2.0, eval_loss=3.0, params=100)
            report = build_comparison_report([run])

            outputs = write_comparison_outputs(report, root / "out")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["svg"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())

    def test_render_comparison_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = make_run(root, "escape-run", best_val=2.0, eval_loss=3.0, params=100, dataset_version="<data>@v1")
            report = build_comparison_report([run], names=["<baseline>"])

            markdown = render_comparison_markdown(report)
            html = render_comparison_html(report)

            self.assertIn("MiniGPT baseline model comparison", markdown)
            self.assertIn("&lt;baseline&gt;", html)
            self.assertIn("&lt;data&gt;@v1", html)
            self.assertIn("<table>", html)
            self.assertNotIn("<strong><baseline>", html)


if __name__ == "__main__":
    unittest.main()
