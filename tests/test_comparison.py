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
    summarize_run,
    write_comparison_csv,
    write_comparison_outputs,
    write_comparison_svg,
)


def make_run(root: Path, name: str, best_val: float, eval_loss: float, params: int) -> Path:
    run_dir = root / name
    run_dir.mkdir()
    (run_dir / "train_config.json").write_text(json.dumps({"tokenizer": "char", "max_iters": 2}), encoding="utf-8")
    (run_dir / "history_summary.json").write_text(
        json.dumps({"best_val_loss": best_val, "last_val_loss": best_val + 0.1}),
        encoding="utf-8",
    )
    (run_dir / "eval_report.json").write_text(json.dumps({"loss": eval_loss, "perplexity": 10.0}), encoding="utf-8")
    (run_dir / "metrics.jsonl").write_text('{"step": 1}\n{"step": 2}\n', encoding="utf-8")
    report_dir = run_dir / "model_report"
    report_dir.mkdir()
    (report_dir / "model_report.json").write_text(
        json.dumps(
            {
                "total_parameters": params,
                "tokenizer": "char",
                "config": {"n_layer": 1, "n_head": 1, "n_embd": 32, "block_size": 16, "vocab_size": 20},
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

    def test_build_comparison_report_picks_best(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = make_run(root, "a", best_val=2.0, eval_loss=3.0, params=100)
            b = make_run(root, "b", best_val=1.5, eval_loss=2.5, params=120)

            report = build_comparison_report([a, b], names=["small", "wide"])

            self.assertEqual(report["run_count"], 2)
            self.assertEqual(report["best_by_best_val_loss"]["name"], "wide")
            self.assertEqual(report["best_by_eval_loss"]["name"], "wide")

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

            self.assertIn("best_val_loss", csv_path.read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
