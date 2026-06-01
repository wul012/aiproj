from __future__ import annotations

import unittest

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_contrast_free_objective_corpus import (
    PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES,
    is_pair_contrast_free_objective_corpus_mode,
)


class ContrastFreeObjectiveCorpusTests(unittest.TestCase):
    def test_modes_are_registered_with_equals_source_prompts(self) -> None:
        for mode in PAIR_CONTRAST_FREE_OBJECTIVE_CORPUS_MODES:
            with self.subTest(mode=mode):
                self.assertIn(mode, PAIR_COEXISTENCE_CORPUS_MODES)
                self.assertTrue(is_pair_contrast_free_objective_corpus_mode(mode))
                self.assertEqual(source_prompts(mode), ("fixed=", "loss="))

    def test_contrast_free_mode_separates_branch_rows(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_contrast_free_repair",
        )

        self.assertIn("fixed=fixed.", corpus)
        self.assertIn("loss=loss.", corpus)
        self.assertIn("fixed= chooses fixed without mentioning loss.", corpus)
        self.assertIn("loss= chooses loss without mentioning fixed.", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_delimiter_span_mode_adds_stop_spans(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_delimiter_span_repair",
        )

        self.assertIn("fixed=fixed;", corpus)
        self.assertIn("loss=loss;", corpus)
        self.assertIn("the semicolon separates answer from another prompt.", corpus)
        self.assertNotIn("pair=01", corpus)

    def test_context_switch_mode_keeps_prompt_surface(self) -> None:
        corpus = build_pair_coexistence_refresh_corpus(
            repeat=2,
            bridge_repeat=1,
            corpus_mode="equals_surface_no_pair_id_fixed_retention_context_switch_repair",
        )

        self.assertIn("[fixed-context]", corpus)
        self.assertIn("[loss-context]", corpus)
        self.assertIn("fixed=fix", corpus)
        self.assertIn("loss=los", corpus)
        self.assertIn("the prompt surface remains fixed= and loss=.", corpus)
        self.assertNotIn("pair=01", corpus)


if __name__ == "__main__":
    unittest.main()
