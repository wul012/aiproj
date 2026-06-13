from __future__ import annotations

import unittest

import torch

from minigpt.lora_finetune import LoRAFinetuneConfig, run_lora_finetune
from minigpt.model import GPTConfig, MiniGPT


def _memorizable_data(vocab_size: int, length: int = 400) -> torch.Tensor:
    # A short repeating pattern the model can drive its loss down on.
    pattern = [i % vocab_size for i in range(8)]
    ids = (pattern * (length // len(pattern) + 1))[:length]
    return torch.tensor(ids, dtype=torch.long)


class LoraFinetuneTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(0)
        self.vocab_size = 12
        self.config = GPTConfig(
            vocab_size=self.vocab_size, block_size=16, n_layer=2, n_head=2, n_embd=16, dropout=0.0
        )
        self.model = MiniGPT(self.config)
        data = _memorizable_data(self.vocab_size)
        self.train_data = data
        self.val_data = data.clone()

    def test_finetune_reduces_loss_and_freezes_base(self) -> None:
        device = torch.device("cpu")
        # Snapshot a base weight to prove the frozen weights never move.
        base_weight = self.model.blocks[0].attn.c_attn.weight.detach().clone()

        ft_config = LoRAFinetuneConfig(
            r=4, alpha=8.0, steps=150, batch_size=8, learning_rate=1e-2, eval_iters=10, eval_interval=50, seed=0
        )
        report = run_lora_finetune(
            self.model, self.train_data, self.val_data, config=ft_config, device=device, generated_at="2026-06-13T00:00:00Z"
        )
        summary = report["summary"]

        # Real ML claim: adapter-only training lowers the training loss.
        self.assertTrue(summary["train_loss_improved"], summary)
        self.assertLess(summary["after_train_loss"], summary["before_train_loss"])
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "lora_finetune_reduced_train_loss")

        # Only a small slice of parameters is trainable.
        self.assertLess(summary["trainable_ratio_percent"], 50.0)
        self.assertEqual(summary["adapted_module_count"], 4)
        self.assertEqual(len(report["rows"]), 4)

        # The original (frozen) weight must be byte-for-byte unchanged.
        after_base = self.model.blocks[0].attn.c_attn.base.weight.detach()
        self.assertTrue(torch.equal(base_weight, after_base))

    def test_report_has_expected_shape(self) -> None:
        ft_config = LoRAFinetuneConfig(r=2, alpha=4.0, steps=10, batch_size=4, eval_iters=4, eval_interval=5, seed=0)
        report = run_lora_finetune(
            self.model, self.train_data, self.val_data, config=ft_config, device=torch.device("cpu")
        )
        for key in ("schema_version", "title", "generated_at", "status", "decision", "summary", "rows", "history"):
            self.assertIn(key, report)
        self.assertEqual(report["csv_fieldnames"], ["module", "kind", "r", "alpha"])
        self.assertTrue(report["history"])
        self.assertEqual(report["history"][-1]["step"], 10)


if __name__ == "__main__":
    unittest.main()
