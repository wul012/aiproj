from __future__ import annotations

import unittest

import torch

from minigpt.rope_eval_v1160 import RopeEvalConfig, run_rope_eval
from minigpt.templated_corpus import build_templated_corpus
from minigpt.tokenizer import CharTokenizer


class RopeEvalTests(unittest.TestCase):
    def _run(self, steps: int):
        torch.manual_seed(0)
        corpus = build_templated_corpus(seed=0, heldout_ratio=0.2, max_sentences=120)
        tok = CharTokenizer.train(corpus.full_text)
        train_ids = torch.tensor(tok.encode(corpus.train_text), dtype=torch.long)
        heldout_ids = torch.tensor(tok.encode(corpus.heldout_text), dtype=torch.long)
        cfg = RopeEvalConfig(steps=steps, lr=3e-3, batch_size=16, block_size=24, n_layer=2, n_head=2, n_embd=32, seed=0)
        return run_rope_eval(vocab_size=tok.vocab_size, train_ids=train_ids, heldout_ids=heldout_ids,
                             config=cfg, device=torch.device("cpu"), corpus_stats=corpus.stats(),
                             generated_at="2026-06-13T00:00:00Z")

    def test_both_schemes_train_and_report(self) -> None:
        report = self._run(steps=120)
        s = report["summary"]
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "rope_capability_validated")
        # Both schemes reach a real (non-degenerate) held-out loss.
        self.assertGreater(s["learned_heldout_loss"], 0.0)
        self.assertGreater(s["rope_heldout_loss"], 0.0)
        self.assertIn(s["verdict"], {"rope_matches_learned_positions", "rope_lower_heldout_loss", "learned_positions_lower_heldout_loss"})

    def test_report_shape(self) -> None:
        report = self._run(steps=5)
        self.assertEqual([r["positional_scheme"] for r in report["rows"]], ["learned_absolute", "rope"])
        self.assertEqual(report["csv_fieldnames"], ["positional_scheme", "heldout_loss", "heldout_token_accuracy", "parameter_count"])
        for key in ("learned_heldout_loss", "rope_heldout_loss", "heldout_loss_delta_rope_minus_learned", "verdict"):
            self.assertIn(key, report["summary"])


if __name__ == "__main__":
    unittest.main()
