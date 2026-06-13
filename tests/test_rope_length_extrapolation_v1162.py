from __future__ import annotations

import unittest

import torch

from minigpt.rope_length_extrapolation_v1162 import LengthExtrapolationConfig, run_length_extrapolation
from minigpt.templated_corpus import build_templated_corpus
from minigpt.tokenizer import CharTokenizer


class LengthExtrapolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        torch.manual_seed(0)
        corpus = build_templated_corpus(seed=0, heldout_ratio=0.3, max_sentences=160)
        tok = CharTokenizer.train(corpus.full_text)
        cls.vocab = tok.vocab_size
        cls.train_ids = torch.tensor(tok.encode(corpus.train_text), dtype=torch.long)
        cls.heldout_ids = torch.tensor(tok.encode(corpus.heldout_text), dtype=torch.long)
        cls.corpus_stats = corpus.stats()
        cfg = LengthExtrapolationConfig(
            train_block_size=8, eval_lengths=(8, 16), seeds=(1337, 1338),
            steps=20, lr=3e-3, batch_size=16, n_layer=1, n_head=2, n_embd=16,
            attention_diag_windows=4,
        )
        cls.report = run_length_extrapolation(
            vocab_size=cls.vocab, train_ids=cls.train_ids, heldout_ids=cls.heldout_ids,
            config=cfg, device=torch.device("cpu"), corpus_stats=cls.corpus_stats,
            generated_at="2026-06-13T00:00:00Z",
        )

    def test_passes_and_reports_measured_decision(self) -> None:
        self.assertEqual(self.report["status"], "pass")
        self.assertEqual(self.report["decision"], "length_extrapolation_measured")
        self.assertIn(self.report["summary"]["verdict"], {
            "absolute_index_definedness_gap_confirmed",
            "directional_but_underpowered",
            "no_separation",
        })

    def test_untrained_tail_is_exactly_at_init(self) -> None:
        # weight_decay=0.0 -> tail rows get zero gradient and zero decay -> no drift.
        self.assertLess(self.report["summary"]["untrained_tail_l2_drift_max"], 1e-6)
        self.assertTrue(all(d < 1e-6 for d in self.report["tail_drift_l2"]))

    def test_categorical_ceiling_is_block_size_gated_for_both_schemes(self) -> None:
        # The honest categorical fact: BOTH schemes raise beyond block_size, and BOTH
        # return finite logits when rebuilt larger. Not "learned crashes, RoPE survives".
        ceiling = self.report["categorical_ceiling"]
        self.assertTrue(ceiling["learned"]["small_raises"])
        self.assertTrue(ceiling["rope"]["small_raises"])
        self.assertTrue(ceiling["learned"]["big_returns_finite"])
        self.assertTrue(ceiling["rope"]["big_returns_finite"])
        self.assertTrue(self.report["summary"]["both_schemes_raise_beyond_block_size"])
        self.assertTrue(self.report["summary"]["both_schemes_finite_when_rebuilt"])

    def test_diagnostic_arms_present(self) -> None:
        s = self.report["summary"]
        # sliding-window learned baseline and zeroed-tail diagnostic both produced.
        self.assertGreater(self.report["sliding_window"]["loss_mean"], 0.0)
        self.assertEqual(self.report["sliding_window"]["window_size"], 8)
        self.assertGreater(s["learned_beyond_zeroed_tail_at_max"], 0.0)
        self.assertGreater(s["learned_beyond_random_tail_at_max"], 0.0)
        # parameter framing: RoPE's effective position params are 0.
        self.assertEqual(s["rope_effective_position_params"], 0)
        self.assertGreater(s["learned_position_table_params"], 0)

    def test_curves_and_rows_shape(self) -> None:
        rows = self.report["rows"]
        # one row per (scheme, eval_length): 2 schemes x 2 lengths
        self.assertEqual(len(rows), 4)
        schemes = {r["scheme"] for r in rows}
        self.assertEqual(schemes, {"learned", "rope"})
        curve = self.report["per_position_curve_at_max"]
        self.assertEqual(curve["eval_length"], 16)
        self.assertEqual(len(curve["learned_loss"]), 16)
        self.assertEqual(len(curve["rope_loss"]), 16)
        self.assertEqual(len(self.report["length_sweep"]), 2)

    def test_eval_lengths_must_include_train_block_size(self) -> None:
        bad = LengthExtrapolationConfig(train_block_size=8, eval_lengths=(16, 32), seeds=(1337,))
        with self.assertRaises(ValueError):
            run_length_extrapolation(
                vocab_size=self.vocab, train_ids=self.train_ids, heldout_ids=self.heldout_ids,
                config=bad, device=torch.device("cpu"),
            )


if __name__ == "__main__":
    unittest.main()
