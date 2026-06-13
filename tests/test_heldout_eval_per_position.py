from __future__ import annotations

import unittest

import torch

from minigpt.heldout_eval import (
    bucket_per_position,
    evaluate_heldout,
    evaluate_heldout_per_position,
    evaluate_sliding_window,
)
from minigpt.model import GPTConfig, MiniGPT


def _model(block_size: int = 32) -> MiniGPT:
    torch.manual_seed(0)
    return MiniGPT(GPTConfig(vocab_size=10, block_size=block_size, n_layer=1, n_head=2, n_embd=16, dropout=0.0))


def _stream(n: int = 300, vocab: int = 10) -> torch.Tensor:
    torch.manual_seed(1)
    return torch.randint(0, vocab, (n,), dtype=torch.long)


class PerPositionEvalTests(unittest.TestCase):
    def test_per_position_mean_matches_scalar_eval(self) -> None:
        # The central regression guard: token-count-weighted mean of the per-position
        # losses must reproduce evaluate_heldout's scalar loss on the same window length.
        model = _model(32)
        stream = _stream(300)
        L = 16
        scalar = evaluate_heldout(model, stream, block_size=L, device=torch.device("cpu"))
        per = evaluate_heldout_per_position(model, stream, window_len=L, device=torch.device("cpu"))
        overall, count = bucket_per_position(per["per_position_loss"], per["per_position_count"], lo=0, hi=L)
        self.assertAlmostEqual(overall, scalar["heldout_loss"], places=4)
        self.assertAlmostEqual(per["overall_loss"], scalar["heldout_loss"], places=4)
        self.assertEqual(count, scalar["heldout_token_count"])
        self.assertEqual(per["heldout_token_count"], scalar["heldout_token_count"])

    def test_per_position_arrays_have_window_length(self) -> None:
        model = _model(32)
        per = evaluate_heldout_per_position(model, _stream(300), window_len=24, device=torch.device("cpu"))
        self.assertEqual(len(per["per_position_loss"]), 24)
        self.assertEqual(len(per["per_position_count"]), 24)
        self.assertTrue(all(c >= 0 for c in per["per_position_count"]))

    def test_bucket_is_count_weighted(self) -> None:
        loss = [1.0, 2.0, 3.0, 4.0]
        count = [10, 10, 1, 0]
        mean, n = bucket_per_position(loss, count, lo=0, hi=2)
        self.assertEqual(n, 20)
        self.assertAlmostEqual(mean, 1.5)
        # A zero-count tail bucket returns (None, 0).
        empty, en = bucket_per_position(loss, count, lo=3, hi=4)
        self.assertIsNone(empty)
        self.assertEqual(en, 0)

    def test_sliding_window_scores_steady_state(self) -> None:
        model = _model(32)
        stream = _stream(300)
        W = 8
        out = evaluate_sliding_window(model, stream, window_size=W, device=torch.device("cpu"))
        self.assertGreater(out["sliding_loss"], 0.0)
        self.assertEqual(out["sliding_token_count"], stream.numel() - W)
        self.assertEqual(out["window_size"], W)

    def test_sliding_window_requires_long_enough_stream(self) -> None:
        model = _model(32)
        with self.assertRaises(ValueError):
            evaluate_sliding_window(model, _stream(8), window_size=8, device=torch.device("cpu"))


if __name__ == "__main__":
    unittest.main()
