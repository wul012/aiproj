from __future__ import annotations

import unittest

import torch

from minigpt.kv_cache_eval_v1161 import KvCacheBenchConfig, run_kv_cache_benchmark


class KvCacheBenchTests(unittest.TestCase):
    def test_benchmark_verifies_correctness(self) -> None:
        # Small CPU config; assert correctness (deterministic), not timing.
        config = KvCacheBenchConfig(
            vocab_size=24, block_size=32, n_layer=2, n_head=2, n_embd=16,
            prompt_len=4, max_new_tokens=16, seed=0, use_rope=True,
        )
        report = run_kv_cache_benchmark(config=config, device=torch.device("cpu"), generated_at="2026-06-13T00:00:00Z")
        s = report["summary"]
        # Sound guarantee: cached logits are numerically identical to the full forward.
        self.assertLess(s["max_logit_diff"], 1e-4)
        self.assertTrue(s["correctness_verified"])
        self.assertEqual(report["status"], "pass")
        self.assertIn(report["decision"], {"kv_cache_correct", "kv_cache_correct_and_faster"})
        # greedy equality is reported but argmax-near-tie sensitive, so only check it is a bool.
        self.assertIsInstance(s["greedy_sequences_match"], bool)

    def test_report_shape(self) -> None:
        config = KvCacheBenchConfig(vocab_size=24, block_size=32, n_layer=1, n_head=2, n_embd=16,
                                    prompt_len=4, max_new_tokens=8, seed=0, use_rope=False)
        report = run_kv_cache_benchmark(config=config, device=torch.device("cpu"))
        self.assertEqual([r["method"] for r in report["rows"]], ["uncached_generate", "cached_generate"])
        self.assertEqual(report["csv_fieldnames"], ["method", "seconds", "tokens_per_sec"])
        for key in ("speedup", "max_logit_diff", "greedy_sequences_match", "cached_tokens_per_sec"):
            self.assertIn(key, report["summary"])


if __name__ == "__main__":
    unittest.main()
