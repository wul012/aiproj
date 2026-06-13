from __future__ import annotations

import unittest

import torch

from minigpt.lora_finetune import LoRAFinetuneConfig
from minigpt.lora_heldout_eval_v1157 import HeldoutEvalConfig, run_lora_heldout_eval
from minigpt.model import GPTConfig, MiniGPT
from minigpt.templated_corpus import build_templated_corpus
from minigpt.tokenizer import CharTokenizer


def _setup():
    torch.manual_seed(0)
    corpus = build_templated_corpus(seed=0, heldout_ratio=0.2, max_sentences=120)
    tokenizer = CharTokenizer.train(corpus.full_text)
    train_ids = torch.tensor(tokenizer.encode(corpus.train_text), dtype=torch.long)
    heldout_ids = torch.tensor(tokenizer.encode(corpus.heldout_text), dtype=torch.long)
    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=24, n_layer=2, n_head=2, n_embd=32, dropout=0.0)
    model = MiniGPT(config)
    return model, train_ids, heldout_ids, corpus.stats()


class LoraHeldoutEvalTests(unittest.TestCase):
    def test_harness_is_valid_when_full_finetune_improves(self) -> None:
        model, train_ids, heldout_ids, stats = _setup()
        eval_config = HeldoutEvalConfig(
            base_steps=20,
            base_lr=3e-4,
            base_batch_size=16,
            block_size=24,
            lora=LoRAFinetuneConfig(r=8, alpha=16.0, steps=200, batch_size=16, learning_rate=3e-3, seed=0, target_all_linear=True),
        )
        report = run_lora_heldout_eval(
            model, train_ids, heldout_ids, config=eval_config, device=torch.device("cpu"),
            corpus_stats=stats, generated_at="2026-06-13T00:00:00Z",
        )
        summary = report["summary"]

        # Harness validity: full fine-tuning measurably lowers held-out loss (real generalization,
        # not v1156's noise). This is the version's actual deliverable.
        self.assertLess(summary["full_finetune_loss_delta"], -0.02)
        self.assertTrue(summary["harness_valid"], summary)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "heldout_eval_harness_validated")

        # The comparison is reported honestly, whatever LoRA's outcome.
        self.assertIn(summary["lora_verdict"], {"lora_matches_full_finetune", "lora_partial_gain", "lora_no_gain"})
        self.assertLess(summary["trainable_ratio_percent"], 50.0)
        # all-linear adapts attention + MLP: 2 layers x 4 linears = 8 modules.
        self.assertEqual(summary["adapted_module_count"], 8)

    def test_report_shape(self) -> None:
        model, train_ids, heldout_ids, stats = _setup()
        eval_config = HeldoutEvalConfig(
            base_steps=5, block_size=24,
            lora=LoRAFinetuneConfig(r=4, alpha=8.0, steps=5, batch_size=8, learning_rate=1e-3, seed=0, target_all_linear=True),
        )
        report = run_lora_heldout_eval(
            model, train_ids, heldout_ids, config=eval_config, device=torch.device("cpu"), corpus_stats=stats
        )
        self.assertEqual(len(report["rows"]), 3)
        self.assertEqual([r["stage"] for r in report["rows"]], ["base", "full_finetune", "lora"])
        for key in ("base_heldout_loss", "full_finetune_heldout_loss", "lora_heldout_loss", "lora_vs_full_capture_ratio", "lora_verdict"):
            self.assertIn(key, report["summary"])
        self.assertEqual(report["csv_fieldnames"], ["stage", "heldout_loss", "heldout_token_accuracy", "trainable_parameters"])


if __name__ == "__main__":
    unittest.main()
