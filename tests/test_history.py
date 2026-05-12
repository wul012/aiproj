from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.history import TrainingRecord, append_record, load_records, summarize_records, write_loss_curve_svg


class HistoryTests(unittest.TestCase):
    def test_append_load_and_summarize_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "metrics.jsonl"
            append_record(history_path, TrainingRecord(step=1, train_loss=2.0, val_loss=2.5, last_loss=2.2))
            append_record(history_path, TrainingRecord(step=2, train_loss=1.5, val_loss=1.7, last_loss=1.6))

            records = load_records(history_path)
            summary = summarize_records(records)

            self.assertEqual([record.step for record in records], [1, 2])
            self.assertEqual(summary["record_count"], 2)
            self.assertEqual(summary["best_val_step"], 2)
            self.assertAlmostEqual(float(summary["best_val_loss"]), 1.7)

    def test_write_loss_curve_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg_path = Path(tmp) / "loss_curve.svg"

            write_loss_curve_svg(
                [
                    TrainingRecord(step=1, train_loss=2.0, val_loss=2.2),
                    TrainingRecord(step=2, train_loss=1.8, val_loss=2.0),
                ],
                svg_path,
            )

            self.assertIn("<svg", svg_path.read_text(encoding="utf-8"))
            self.assertIn("MiniGPT loss curve", svg_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
