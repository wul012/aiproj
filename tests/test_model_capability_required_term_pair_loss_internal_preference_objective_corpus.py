from __future__ import annotations

import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_corpus import (
    PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES,
    is_pair_loss_internal_preference_objective_corpus_mode,
)


class LossInternalPreferenceObjectiveCorpusTests(unittest.TestCase):
    def test_modes_are_registered_with_equals_source_prompts(self) -> None:
        for mode in PAIR_LOSS_INTERNAL_PREFERENCE_OBJECTIVE_CORPUS_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, PAIR_COEXISTENCE_CORPUS_MODES)
                self.assertTrue(is_pair_loss_internal_preference_objective_corpus_mode(mode))
                self.assertEqual(source_prompts(mode), ("fixed=", "loss="))

    def test_internal_preference_mode_adds_forced_choice_rows(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_loss_internal_preference_repair",
        )

        self.assertIn("forced choice loss= prefers loss", corpus)
        self.assertIn("score loss= loss lower than fixed", corpus)
        self.assertIn("fixed=fixed|loss=loss", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_internal_first_token_mode_targets_l_before_loss(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_loss_internal_first_token_repair",
        )

        self.assertIn("loss=l", corpus)
        self.assertIn("loss internal first token prefers l", corpus)
        self.assertIn("fixed internal first token prefers f", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_ranked_choice_mode_mirrors_forced_choice_diagnostic(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_loss_internal_ranked_choice_repair",
        )

        self.assertIn("choice loss= candidate loss rank 1", corpus)
        self.assertIn("choice loss= candidate fixed rank 2", corpus)
        self.assertIn("ranked choice rows mirror forced-choice diagnostics.", corpus)
        self.assertNotIn("pair=01", corpus)


if __name__ == "__main__":
    unittest.main()
