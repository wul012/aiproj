"""v1171: regression guard for the extracted single-corpus script setup.

The 5 v1164+ ``scripts/run_*`` entrypoints used to inline the same
build_sft_corpus -> CharTokenizer.train -> pad/eos -> block_size sequence; v1171
folds it into ``minigpt.script_setup.setup_single_corpus``. These tests pin that
the helper reproduces the inline sequence byte-for-byte (so the migration is
contract-preserving without needing the old script code to survive)."""
from __future__ import annotations

import unittest

from minigpt.script_setup import setup_single_corpus
from minigpt.sft_corpus import EOS, PAD, build_sft_corpus
from minigpt.tokenizer import CharTokenizer

ARGS = dict(seed=1337, ops=("C", "R", "S"), lengths=(3, 4), inputs_per_op_length=8, heldout_ratio=0.25)


def _inline(seed, ops, lengths, inputs_per_op_length, heldout_ratio):
    """The exact pre-v1171 inline sequence, for the regression guard."""
    corpus = build_sft_corpus(seed=seed, ops=ops, lengths=lengths,
                              inputs_per_op_length=inputs_per_op_length, heldout_ratio=heldout_ratio)
    tokenizer = CharTokenizer.train("".join(e.text for e in corpus.train + corpus.heldout) + corpus.alphabet)
    pad_id = tokenizer.encode(PAD)[0]
    eos_id = tokenizer.encode(EOS)[0]
    block_size = max(16, corpus.max_text_len)
    return corpus, tokenizer, pad_id, eos_id, block_size


class ScriptSetupTests(unittest.TestCase):
    def test_setup_single_corpus_matches_inline(self):
        ic, it, ipad, ieos, iblock = _inline(**ARGS)
        hc, ht, hpad, heos, hblock = setup_single_corpus(**ARGS)
        self.assertEqual(ht.vocab_size, it.vocab_size)
        self.assertEqual(hpad, ipad)
        self.assertEqual(heos, ieos)
        self.assertEqual(hblock, iblock)
        self.assertEqual(hc.max_text_len, ic.max_text_len)
        self.assertEqual(hc.stats(), ic.stats())
        # the encodings each script derives must be identical too
        self.assertEqual([ht.encode(e.text) for e in hc.train],
                         [it.encode(e.text) for e in ic.train])

    def test_setup_single_corpus_deterministic(self):
        a = setup_single_corpus(**ARGS)
        b = setup_single_corpus(**ARGS)
        self.assertEqual((a[1].vocab_size, a[2], a[3], a[4]), (b[1].vocab_size, b[2], b[3], b[4]))
        # a different seed is still well-formed
        c = setup_single_corpus(**{**ARGS, "seed": 7})
        self.assertNotEqual(c[2], c[3])          # pad_id != eos_id
        self.assertGreaterEqual(c[4], 16)

    def test_block_size_floor_and_tracking(self):
        # tiny lengths -> the max(16, ...) floor dominates
        _c, _t, _p, _e, small = setup_single_corpus(seed=1, ops=("C",), lengths=(3,),
                                                    inputs_per_op_length=4, heldout_ratio=0.25)
        self.assertEqual(small, 16)
        # larger lengths -> block_size tracks corpus.max_text_len above the floor
        c, _t, _p, _e, big = setup_single_corpus(seed=1, ops=("C", "R"), lengths=(20,),
                                                 inputs_per_op_length=6, heldout_ratio=0.25)
        self.assertEqual(big, c.max_text_len)
        self.assertGreater(big, 16)


if __name__ == "__main__":
    unittest.main()
