from __future__ import annotations

import unittest

import torch

from minigpt.lm_training import train_lm
from minigpt.model import GPTConfig, MiniGPT


def _memorizable(vocab_size: int, length: int = 400) -> torch.Tensor:
    pattern = [i % vocab_size for i in range(8)]
    ids = (pattern * (length // len(pattern) + 1))[:length]
    return torch.tensor(ids, dtype=torch.long)


class TrainLmTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(0)
        self.model = MiniGPT(GPTConfig(vocab_size=12, block_size=16, n_layer=2, n_head=2, n_embd=16, dropout=0.0))
        self.data = _memorizable(12)

    def test_reduces_loss_and_returns_float(self) -> None:
        before = train_lm(self.model, list(self.model.parameters()), self.data,
                          steps=1, lr=1e-2, batch_size=8, block_size=16, device=torch.device("cpu"))
        after = train_lm(self.model, list(self.model.parameters()), self.data,
                         steps=150, lr=1e-2, batch_size=8, block_size=16, device=torch.device("cpu"))
        self.assertIsInstance(after, float)
        self.assertLess(after, before)

    def test_only_passed_params_are_updated(self) -> None:
        # Train only one attention block; the token embedding must stay untouched.
        embed_before = self.model.token_embedding.weight.detach().clone()
        subset = list(self.model.blocks[0].attn.parameters())
        train_lm(self.model, subset, self.data, steps=20, lr=1e-2, batch_size=8, block_size=16, device=torch.device("cpu"))
        self.assertTrue(torch.equal(embed_before, self.model.token_embedding.weight.detach()))

    def test_log_every_runs(self) -> None:
        # Smoke: logging path must not raise.
        loss = train_lm(self.model, list(self.model.parameters()), self.data,
                        steps=4, lr=1e-3, batch_size=8, block_size=16, device=torch.device("cpu"),
                        log_every=2, label="smoke")
        self.assertIsInstance(loss, float)

    def test_weight_decay_zero_leaves_ungradiented_rows_at_init(self) -> None:
        # v1162 contract: with weight_decay=0.0, position rows beyond the training
        # window length (block_size=8 here, table=16) get exactly zero gradient and
        # zero decay, so they stay BITWISE at their init. This is what makes the
        # "untrained tail = at init" claim literally true.
        torch.manual_seed(0)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        tail_before = model.position_embedding.weight[8:16].detach().clone()
        train_lm(model, list(model.parameters()), self.data, steps=30, lr=1e-2,
                 batch_size=8, block_size=8, device=torch.device("cpu"), weight_decay=0.0)
        tail_after = model.position_embedding.weight[8:16].detach()
        self.assertTrue(torch.equal(tail_before, tail_after))

    def test_default_weight_decay_shrinks_ungradiented_rows(self) -> None:
        # Documents WHY v1162 must pass weight_decay=0.0: under AdamW's default
        # weight_decay=0.01 the unused tail rows are decoupled-decayed toward zero
        # every step despite zero gradient, so they would NOT be "at init".
        torch.manual_seed(0)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=16, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        tail_before = model.position_embedding.weight[8:16].detach().clone()
        train_lm(model, list(model.parameters()), self.data, steps=30, lr=1e-2,
                 batch_size=8, block_size=8, device=torch.device("cpu"))  # weight_decay=None -> AdamW default 0.01
        tail_after = model.position_embedding.weight[8:16].detach()
        self.assertFalse(torch.equal(tail_before, tail_after))
        self.assertLess(tail_after.norm().item(), tail_before.norm().item())


if __name__ == "__main__":
    unittest.main()
