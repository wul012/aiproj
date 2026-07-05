from __future__ import annotations

import unittest

import torch

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.model import GPTConfig, MiniGPT


class MiniGPTTests(unittest.TestCase):
    def test_forward_returns_logits_and_loss(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=16, block_size=8, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        idx = torch.randint(0, 16, (2, 8))
        targets = torch.randint(0, 16, (2, 8))

        logits, loss = model(idx, targets)

        self.assertEqual(tuple(logits.shape), (2, 8, 16))
        self.assertIsNotNone(loss)
        self.assertGreater(model.parameter_count(), 0)

    def test_generate_extends_sequence(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=4, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        idx = torch.tensor([[1, 2, 3]], dtype=torch.long)

        out = model.generate(idx, max_new_tokens=5, temperature=1.0, top_k=4)

        self.assertEqual(tuple(out.shape), (1, 8))

    def test_sample_next_returns_one_token(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=4, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        idx = torch.tensor([[1, 2, 3]], dtype=torch.long)

        next_idx = model.sample_next(idx, temperature=1.0, top_k=4)

        self.assertEqual(tuple(next_idx.shape), (1, 1))
        self.assertGreaterEqual(int(next_idx.item()), 0)
        self.assertLess(int(next_idx.item()), 12)

    def test_sample_next_respects_blocked_token_ids(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=4, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        idx = torch.tensor([[1, 2, 3]], dtype=torch.long)

        next_idx = model.sample_next(idx, temperature=1.0, blocked_token_ids=list(range(11)))

        self.assertEqual(int(next_idx.item()), 11)
        with self.assertRaisesRegex(ValueError, "cannot block every token"):
            model.sample_next(idx, temperature=1.0, blocked_token_ids=list(range(12)))


if __name__ == "__main__":
    unittest.main()
