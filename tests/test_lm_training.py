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


if __name__ == "__main__":
    unittest.main()
