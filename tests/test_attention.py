from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT


class AttentionCaptureTests(unittest.TestCase):
    def test_attention_capture_returns_one_map_per_layer(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=6, n_layer=2, n_head=2, n_embd=16, dropout=0.0))
        model.eval()
        model.set_attention_capture(True)

        model(torch.tensor([[1, 2, 3, 4]], dtype=torch.long))
        maps = model.attention_maps()

        self.assertEqual(len(maps), 2)
        self.assertEqual(tuple(maps[0].shape), (1, 2, 4, 4))

    def test_attention_capture_respects_causal_mask(self) -> None:
        torch.manual_seed(1)
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=6, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        model.eval()
        model.set_attention_capture(True)

        model(torch.tensor([[1, 2, 3, 4]], dtype=torch.long))
        att = model.attention_maps()[0][0, 0]

        future_weights = att.triu(diagonal=1)
        self.assertTrue(torch.allclose(future_weights, torch.zeros_like(future_weights)))

    def test_disabling_attention_capture_clears_maps(self) -> None:
        model = MiniGPT(GPTConfig(vocab_size=12, block_size=6, n_layer=1, n_head=2, n_embd=16, dropout=0.0))
        model.set_attention_capture(True)
        model(torch.tensor([[1, 2, 3]], dtype=torch.long))

        model.set_attention_capture(False)

        self.assertEqual(model.attention_maps(), [])


if __name__ == "__main__":
    unittest.main()
