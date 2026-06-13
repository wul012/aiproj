from __future__ import annotations

import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT


def _model(use_rope: bool, block_size: int = 32) -> MiniGPT:
    torch.manual_seed(0)
    cfg = GPTConfig(vocab_size=24, block_size=block_size, n_layer=3, n_head=2, n_embd=16, dropout=0.0, use_rope=use_rope)
    return MiniGPT(cfg).eval()


class KvCacheCorrectnessTests(unittest.TestCase):
    def _assert_cached_matches_full(self, use_rope: bool) -> None:
        model = _model(use_rope)
        seq = torch.randint(0, 24, (1, 12))
        full_logits, _ = model(seq)  # (1, T, vocab)

        # Feed tokens one at a time through the cached path and collect each step's logits.
        cached_steps = []
        caches = None
        for t in range(seq.shape[1]):
            step_logits, caches = model.forward_cached(seq[:, t : t + 1], caches, t)
            cached_steps.append(step_logits[:, -1, :])
        cached_logits = torch.stack(cached_steps, dim=1)  # (1, T, vocab)

        self.assertTrue(torch.allclose(full_logits, cached_logits, atol=1e-4),
                        (full_logits - cached_logits).abs().max().item())

    def test_cached_matches_full_learned_positions(self) -> None:
        self._assert_cached_matches_full(use_rope=False)

    def test_cached_matches_full_rope(self) -> None:
        self._assert_cached_matches_full(use_rope=True)

    def test_prefill_then_decode_matches_full(self) -> None:
        # Prefill a multi-token prompt in one call, then decode one token; compare to full forward.
        model = _model(use_rope=True)
        seq = torch.randint(0, 24, (1, 10))
        full_logits, _ = model(seq)
        prefill_logits, caches = model.forward_cached(seq[:, :9], None, 0)
        step_logits, _ = model.forward_cached(seq[:, 9:10], caches, 9)
        self.assertTrue(torch.allclose(full_logits[:, 8, :], prefill_logits[:, -1, :], atol=1e-4))
        self.assertTrue(torch.allclose(full_logits[:, 9, :], step_logits[:, -1, :], atol=1e-4))

    def test_generate_cached_matches_generate_greedy(self) -> None:
        # top_k=1 is deterministic, so cached and uncached generation must produce the same tokens.
        for use_rope in (False, True):
            model = _model(use_rope)
            prompt = torch.randint(0, 24, (1, 4))
            uncached = model.generate(prompt.clone(), max_new_tokens=10, top_k=1)
            cached = model.generate_cached(prompt.clone(), max_new_tokens=10, top_k=1)
            self.assertTrue(torch.equal(uncached, cached), f"use_rope={use_rope}")

    def test_cache_grows_by_one_per_step(self) -> None:
        model = _model(use_rope=False)
        seq = torch.randint(0, 24, (1, 5))
        _, caches = model.forward_cached(seq, None, 0)
        self.assertEqual(caches[0][0].shape[2], 5)  # k cache length
        _, caches = model.forward_cached(seq[:, :1], caches, 5)
        self.assertEqual(caches[0][0].shape[2], 6)


if __name__ == "__main__":
    unittest.main()
