from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.prediction import perplexity_from_loss, top_k_predictions, write_predictions_svg


class PredictionTests(unittest.TestCase):
    def test_top_k_predictions_are_sorted(self) -> None:
        logits = torch.tensor([0.0, 2.0, 1.0])

        predictions = top_k_predictions(logits, tokens=["a", "b", "c"], k=2)

        self.assertEqual([prediction.token for prediction in predictions], ["b", "c"])
        self.assertGreater(predictions[0].probability, predictions[1].probability)

    def test_top_k_predictions_reject_bad_temperature(self) -> None:
        with self.assertRaises(ValueError):
            top_k_predictions(torch.tensor([1.0]), tokens=["a"], temperature=0)

    def test_perplexity_from_loss(self) -> None:
        self.assertAlmostEqual(perplexity_from_loss(0.0), 1.0)

    def test_write_predictions_svg(self) -> None:
        predictions = top_k_predictions(torch.tensor([0.0, 2.0]), tokens=["a", "b"], k=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.svg"

            write_predictions_svg(predictions, path)

            text = path.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("MiniGPT next-token predictions", text)


if __name__ == "__main__":
    unittest.main()
