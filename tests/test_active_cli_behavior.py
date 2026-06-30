from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

from minigpt.core.history import TrainingRecord, append_record
from scripts import (
    analyze_generation_quality,
    compare_runs,
    inspect_tokenizer,
    plot_history,
    prepare_dataset,
)
from tests.test_comparison import make_run as make_comparison_run
from tests.test_generation_quality import make_eval_suite as make_quality_eval_suite

ensure_src_path()


class ActiveCliBehaviorTests(unittest.TestCase):
    def test_prepare_dataset_main_writes_versioned_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.txt"
            out_dir = root / "prepared"
            source.write_text("ai governance\nmachine learning\n", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = prepare_dataset.main(
                    [
                        str(source),
                        "--out-dir",
                        str(out_dir),
                        "--output-name",
                        "train.txt",
                        "--dataset-name",
                        "demo",
                        "--dataset-version",
                        "v1",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("dataset_id=demo@v1", stdout.getvalue())
            self.assertIn("outputs=", stdout.getvalue())
            self.assertIn("ai governance", (out_dir / "train.txt").read_text(encoding="utf-8"))
            self.assertTrue((out_dir / "dataset_report.json").is_file())
            self.assertTrue((out_dir / "dataset_quality.json").is_file())
            version = json.loads((out_dir / "dataset_version.json").read_text(encoding="utf-8"))
            self.assertEqual(version["dataset"]["name"], "demo")
            self.assertEqual(version["dataset"]["version"], "v1")

    def test_inspect_tokenizer_main_runs_with_temp_char_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "corpus.txt"
            source.write_text("ai governance\nai learning\n", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = inspect_tokenizer.main(["--data", str(source), "--text", "ai governance", "--tokenizer", "char"])

            output = stdout.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn(f"source={source}", output)
            self.assertIn("tokenizer=char", output)
            self.assertIn("text=ai governance", output)
            self.assertIn("decoded=ai governance", output)

    def test_plot_history_main_writes_loss_curve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history_path = root / "metrics.jsonl"
            svg_path = root / "loss.svg"
            append_record(history_path, TrainingRecord(step=1, train_loss=2.0, val_loss=2.5, last_loss=2.2))
            append_record(history_path, TrainingRecord(step=2, train_loss=1.5, val_loss=1.7, last_loss=1.6))

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exit_code = plot_history.main(["--history", str(history_path), "--out", str(svg_path)])

            self.assertEqual(exit_code, 0)
            self.assertIn('"best_val_loss": 1.7', stdout.getvalue())
            self.assertIn(f"saved={svg_path}", stdout.getvalue())
            svg = svg_path.read_text(encoding="utf-8")
            self.assertIn("<svg", svg)
            self.assertIn("MiniGPT loss curve", svg)

    def test_comparison_and_generation_quality_mains_write_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_a = make_comparison_run(root, "a", best_val=2.0, eval_loss=3.0, params=100)
            run_b = make_comparison_run(root, "b", best_val=1.5, eval_loss=2.5, params=120)
            comparison_out = root / "comparison"

            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                comparison_exit_code = compare_runs.main(
                    [
                        str(run_a),
                        str(run_b),
                        "--name",
                        "small",
                        "--name",
                        "wide",
                        "--baseline",
                        "small",
                        "--out-dir",
                        str(comparison_out),
                    ]
                )

            comparison_output = stdout.getvalue()
            self.assertEqual(comparison_exit_code, 0)
            self.assertIn("run_count=2", comparison_output)
            self.assertIn("best_by_best_val_loss=", comparison_output)
            self.assertIn("saved_json=", comparison_output)
            comparison = json.loads((comparison_out / "comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(comparison["run_count"], 2)
            self.assertEqual(comparison["best_by_best_val_loss"]["name"], "wide")
            self.assertTrue((comparison_out / "comparison.md").is_file())
            self.assertTrue((comparison_out / "comparison.html").is_file())
            self.assertTrue((comparison_out / "comparison.svg").is_file())

            quality_input = make_quality_eval_suite(root)
            quality_out = root / "generation-quality"
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                quality_exit_code = analyze_generation_quality.main(
                    ["--input", str(quality_input), "--out-dir", str(quality_out)]
                )

            quality_output = stdout.getvalue()
            self.assertEqual(quality_exit_code, 0)
            self.assertIn("source_type=eval_suite", quality_output)
            self.assertIn("cases=3", quality_output)
            self.assertIn("outputs=", quality_output)
            quality = json.loads((quality_out / "generation_quality.json").read_text(encoding="utf-8"))
            self.assertEqual(quality["summary"]["case_count"], 3)
            self.assertTrue((quality_out / "generation_quality.md").is_file())
            self.assertTrue((quality_out / "generation_quality.html").is_file())
            self.assertTrue((quality_out / "generation_quality.svg").is_file())


if __name__ == "__main__":
    unittest.main()
