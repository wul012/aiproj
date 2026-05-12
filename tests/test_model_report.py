from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.model_report import (
    build_model_report,
    output_head_is_tied,
    parameter_groups,
    tensor_shape_summary,
    write_model_report_svg,
)


class ModelReportTests(unittest.TestCase):
    def test_parameter_groups_sum_to_model_parameter_count(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=8, n_layer=2, n_head=2, n_embd=8))

        total = sum(group.parameters for group in parameter_groups(model))

        self.assertEqual(total, model.parameter_count())

    def test_output_head_is_tied_to_token_embedding(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8))

        self.assertTrue(output_head_is_tied(model))

    def test_tensor_shape_summary(self) -> None:
        config = GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8)

        shapes = tensor_shape_summary(config, batch_size=3, sequence_length=5)

        self.assertEqual(shapes["token_ids"], [3, 5])
        self.assertEqual(shapes["qkv_split"], [3, 2, 5, 4])
        self.assertEqual(shapes["logits"], [3, 5, 12])

    def test_tensor_shape_summary_rejects_too_long_sequence(self) -> None:
        config = GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8)

        with self.assertRaises(ValueError):
            tensor_shape_summary(config, sequence_length=9)

    def test_build_report_contains_parameter_check(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8))

        report = build_model_report(model, tokenizer_name="char", sequence_length=4)

        self.assertEqual(report["tokenizer"], "char")
        self.assertTrue(report["parameter_check"]["owned_sum_matches_total"])
        self.assertTrue(report["tied_weights"]["is_tied"])

    def test_write_model_report_svg(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=8, n_layer=1, n_head=2, n_embd=8))
        report = build_model_report(model)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model_architecture.svg"

            write_model_report_svg(report, path)

            text = path.read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("MiniGPT model report", text)
            self.assertIn("Owned parameter groups", text)


if __name__ == "__main__":
    unittest.main()
