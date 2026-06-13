from __future__ import annotations

import unittest

import torch

from minigpt.heldout_eval import evaluate_heldout
from minigpt.model import GPTConfig, MiniGPT


class _PerfectModel(torch.nn.Module):
    """A stand-in that always predicts the next token correctly (acc=1, loss~0).

    It one-hots the *target* it is given, so we can verify the metric plumbing
    independently of any real network.
    """

    def __init__(self, vocab_size: int, block_size: int) -> None:
        super().__init__()
        self.config = GPTConfig(vocab_size=vocab_size, block_size=block_size, n_layer=1, n_head=1, n_embd=8)

    def forward(self, idx, targets=None):
        b, t = idx.shape
        logits = torch.zeros(b, t, self.config.vocab_size)
        if targets is not None:
            logits.scatter_(2, targets.unsqueeze(-1), 30.0)  # huge logit on the true token
            loss = torch.nn.functional.cross_entropy(logits.reshape(-1, self.config.vocab_size), targets.reshape(-1))
            return logits, loss
        return logits, None


class HeldoutEvalTests(unittest.TestCase):
    def test_perfect_model_scores_full_accuracy(self) -> None:
        model = _PerfectModel(vocab_size=12, block_size=8)
        ids = torch.tensor([i % 12 for i in range(40)], dtype=torch.long)
        result = evaluate_heldout(model, ids, block_size=8, device=torch.device("cpu"))
        self.assertAlmostEqual(result["heldout_token_accuracy"], 1.0, places=6)
        self.assertLess(result["heldout_loss"], 0.01)

    def test_token_count_matches_stream(self) -> None:
        model = _PerfectModel(vocab_size=12, block_size=8)
        ids = torch.arange(0, 33, dtype=torch.long) % 12  # 33 tokens
        result = evaluate_heldout(model, ids, block_size=8, device=torch.device("cpu"))
        # 33 tokens -> predicted targets = 32 (one per non-final position across windows).
        self.assertEqual(result["heldout_token_count"], 32)

    def test_real_model_returns_bounded_metrics(self) -> None:
        torch.manual_seed(0)
        config = GPTConfig(vocab_size=16, block_size=8, n_layer=2, n_head=2, n_embd=16)
        model = MiniGPT(config)
        ids = torch.randint(0, 16, (50,), dtype=torch.long)
        result = evaluate_heldout(model, ids, block_size=8, device=torch.device("cpu"))
        self.assertGreater(result["heldout_loss"], 0.0)
        self.assertGreaterEqual(result["heldout_token_accuracy"], 0.0)
        self.assertLessEqual(result["heldout_token_accuracy"], 1.0)

    def test_rejects_tiny_stream(self) -> None:
        model = _PerfectModel(vocab_size=12, block_size=8)
        with self.assertRaises(ValueError):
            evaluate_heldout(model, torch.tensor([1]), block_size=8, device=torch.device("cpu"))


if __name__ == "__main__":
    unittest.main()
