from __future__ import annotations

import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.rope import apply_rope, build_rope_cache, rotate_half


class RopePrimitiveTests(unittest.TestCase):
    def test_rotate_half(self) -> None:
        x = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
        # [x1, x2] = [[1,2],[3,4]] -> [-x2, x1] = [-3,-4,1,2]
        self.assertTrue(torch.equal(rotate_half(x), torch.tensor([[-3.0, -4.0, 1.0, 2.0]])))

    def test_cache_shapes_and_even_requirement(self) -> None:
        cos, sin = build_rope_cache(10, 8)
        self.assertEqual(cos.shape, (10, 8))
        self.assertEqual(sin.shape, (10, 8))
        with self.assertRaises(ValueError):
            build_rope_cache(10, 7)

    def test_rope_is_norm_preserving(self) -> None:
        torch.manual_seed(0)
        x = torch.randn(2, 3, 5, 8)  # (B, nh, T, hs)
        cos, sin = build_rope_cache(5, 8)
        y = apply_rope(x, cos, sin)
        self.assertTrue(torch.allclose(x.norm(dim=-1), y.norm(dim=-1), atol=1e-5))

    def test_position_zero_is_identity(self) -> None:
        # At position 0 the rotation angle is 0, so RoPE leaves the vector unchanged.
        x = torch.randn(1, 1, 3, 8)
        cos, sin = build_rope_cache(3, 8)
        y = apply_rope(x, cos, sin)
        self.assertTrue(torch.allclose(y[:, :, 0, :], x[:, :, 0, :], atol=1e-6))


class RopeModelTests(unittest.TestCase):
    def test_rope_model_forward_and_no_position_embedding_used(self) -> None:
        torch.manual_seed(0)
        cfg = GPTConfig(vocab_size=20, block_size=16, n_layer=2, n_head=2, n_embd=16, dropout=0.0, use_rope=True)
        model = MiniGPT(cfg)
        idx = torch.randint(0, 20, (2, 12))
        logits, loss = model(idx, idx)
        self.assertEqual(logits.shape, (2, 12, 20))
        self.assertIsNotNone(loss)
        # RoPE attention registers rotary buffers.
        self.assertTrue(hasattr(model.blocks[0].attn, "rope_cos"))

    def test_rope_buffers_are_not_in_state_dict(self) -> None:
        cfg = GPTConfig(vocab_size=20, block_size=16, n_layer=1, n_head=2, n_embd=16, use_rope=True)
        model = MiniGPT(cfg)
        self.assertFalse(any("rope_cos" in k or "rope_sin" in k for k in model.state_dict()))

    def test_rope_odd_head_size_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MiniGPT(GPTConfig(vocab_size=20, block_size=16, n_layer=1, n_head=3, n_embd=15, use_rope=True))

    def test_default_is_not_rope(self) -> None:
        cfg = GPTConfig(vocab_size=20)
        self.assertFalse(cfg.use_rope)
        model = MiniGPT(cfg)
        self.assertFalse(model.blocks[0].attn.use_rope)


if __name__ == "__main__":
    unittest.main()
