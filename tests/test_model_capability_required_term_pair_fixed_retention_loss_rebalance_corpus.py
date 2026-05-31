from __future__ import annotations

import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_fixed_retention_loss_rebalance_corpus import (
    PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES,
    is_pair_fixed_retention_loss_rebalance_corpus_mode,
)


class FixedRetentionLossRebalanceCorpusTests(unittest.TestCase):
    def test_modes_are_registered_with_equals_source_prompts(self) -> None:
        for mode in PAIR_FIXED_RETENTION_LOSS_REBALANCE_CORPUS_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, PAIR_COEXISTENCE_CORPUS_MODES)
                self.assertTrue(is_pair_fixed_retention_loss_rebalance_corpus_mode(mode))
                self.assertEqual(source_prompts(mode), ("fixed=", "loss="))

    def test_loss_rebalance_repair_keeps_fixed_prefix_and_loss_rows(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair",
        )

        self.assertIn("fixed=fix", corpus)
        self.assertIn("loss=los", corpus)
        self.assertGreaterEqual(corpus.count("fixed=fixed"), 2)
        self.assertGreaterEqual(corpus.count("loss=loss"), 2)
        self.assertIn("loss rebalance restores loss while retaining fixed first-token rows.", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_dual_cycle_repair_alternates_fixed_and_loss_targets(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_dual_cycle_repair",
        )

        self.assertGreaterEqual(corpus.count("fixed=fixed"), 2)
        self.assertGreaterEqual(corpus.count("loss=loss"), 2)
        self.assertIn("fixed=fixed loss=loss", corpus)
        self.assertIn("loss=loss fixed=fixed", corpus)
        self.assertIn("dual cycle alternates fixed and loss targets without pair ids.", corpus)
        self.assertNotIn("pair=01", corpus)


if __name__ == "__main__":
    unittest.main()
