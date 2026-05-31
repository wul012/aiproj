from __future__ import annotations

import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_fixed_retention_objective_corpus import (
    PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES,
    is_pair_fixed_retention_objective_corpus_mode,
)


class FixedRetentionObjectiveCorpusTests(unittest.TestCase):
    def test_modes_are_registered_with_equals_source_prompts(self) -> None:
        for mode in PAIR_FIXED_RETENTION_OBJECTIVE_CORPUS_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, PAIR_COEXISTENCE_CORPUS_MODES)
                self.assertTrue(is_pair_fixed_retention_objective_corpus_mode(mode))
                self.assertEqual(source_prompts(mode), ("fixed=", "loss="))

    def test_balanced_repair_weights_fixed_without_erasing_loss(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_balanced_repair",
        )

        self.assertGreater(corpus.count("fixed=fixed"), corpus.count("loss=loss"))
        self.assertIn("fixed retention target fixed", corpus)
        self.assertIn("loss branch still target loss", corpus)
        self.assertIn("loss= should not erase fixed retention", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_first_token_repair_adds_fixed_prefix_spans(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_first_token_repair",
        )

        self.assertGreater(corpus.count("fixed=f"), corpus.count("loss=l"))
        self.assertIn("fixed=fi", corpus)
        self.assertIn("fixed=fix", corpus)
        self.assertIn("first token fixed= f", corpus)
        self.assertIn("full token loss= loss", corpus)

    def test_prompt_guard_repair_separates_prompt_surfaces(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_prompt_guard_repair",
        )

        self.assertIn("guard fixed= not loss", corpus)
        self.assertIn("guard loss= not fixed", corpus)
        self.assertIn("prompt guard rows separate fixed= from loss=.", corpus)
        self.assertIn("fixed=fixed|loss=loss", corpus)
        self.assertNotIn("pair=01", corpus)


if __name__ == "__main__":
    unittest.main()
