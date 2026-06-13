from __future__ import annotations

import unittest

from minigpt.templated_corpus import build_templated_corpus


class TemplatedCorpusTests(unittest.TestCase):
    def test_deterministic_for_same_seed(self) -> None:
        a = build_templated_corpus(seed=7)
        b = build_templated_corpus(seed=7)
        self.assertEqual(a.train_text, b.train_text)
        self.assertEqual(a.heldout_text, b.heldout_text)

    def test_different_seed_changes_split(self) -> None:
        a = build_templated_corpus(seed=1)
        b = build_templated_corpus(seed=2)
        self.assertNotEqual(a.heldout_sentences, b.heldout_sentences)

    def test_train_and_heldout_are_disjoint(self) -> None:
        corpus = build_templated_corpus(seed=1337, heldout_ratio=0.2, max_sentences=200)
        train_set = set(corpus.train_sentences)
        heldout_set = set(corpus.heldout_sentences)
        self.assertTrue(train_set.isdisjoint(heldout_set))
        self.assertEqual(len(train_set) + len(heldout_set), len(corpus.train_sentences) + len(corpus.heldout_sentences))

    def test_heldout_vocab_is_covered_by_full_text(self) -> None:
        # Held-out chars must all be in the full corpus so the tokenizer (trained on
        # full text) never emits <unk> on held-out — held-out is in-distribution.
        corpus = build_templated_corpus(seed=3, max_sentences=300)
        self.assertTrue(set(corpus.heldout_text).issubset(set(corpus.full_text)))
        # In this grammar every char also appears in train (shared vocabulary).
        self.assertTrue(set(corpus.heldout_text).issubset(set(corpus.train_text)))

    def test_sizes_are_reasonable(self) -> None:
        corpus = build_templated_corpus(seed=1337, heldout_ratio=0.2, max_sentences=400)
        stats = corpus.stats()
        self.assertGreater(stats["train_char_count"], 2000)
        self.assertGreater(stats["heldout_char_count"], 400)
        self.assertEqual(stats["heldout_sentence_count"], 80)

    def test_invalid_ratio(self) -> None:
        with self.assertRaises(ValueError):
            build_templated_corpus(heldout_ratio=0.0)


if __name__ == "__main__":
    unittest.main()
