from __future__ import annotations

import unittest

from minigpt.sft_corpus import EOS, OPS, SEP, build_sft_corpus


class SftCorpusTests(unittest.TestCase):
    def test_deterministic(self) -> None:
        a = build_sft_corpus(seed=3, ops=("C", "R"), lengths=(3, 4), inputs_per_op_length=40)
        b = build_sft_corpus(seed=3, ops=("C", "R"), lengths=(3, 4), inputs_per_op_length=40)
        self.assertEqual([e.text for e in a.train], [e.text for e in b.train])
        self.assertEqual([e.text for e in a.heldout], [e.text for e in b.heldout])

    def test_example_format_and_ops(self) -> None:
        corpus = build_sft_corpus(seed=1, ops=("C", "R", "S"), lengths=(4,), inputs_per_op_length=60)
        for e in corpus.train + corpus.heldout:
            self.assertTrue(e.prompt.startswith(e.op))
            self.assertTrue(e.prompt.endswith(SEP))
            self.assertTrue(e.completion.endswith(EOS))
            inp = e.prompt[1:-1]  # strip op marker and '='
            self.assertEqual(e.expected_output, OPS[e.op](inp))

    def test_heldout_inputs_are_unseen(self) -> None:
        corpus = build_sft_corpus(seed=2, ops=("C", "R"), lengths=(4,), inputs_per_op_length=80)
        for op in ("C", "R"):
            train_inputs = {e.prompt[1:-1] for e in corpus.train if e.op == op}
            heldout_inputs = {e.prompt[1:-1] for e in corpus.heldout if e.op == op}
            self.assertTrue(train_inputs.isdisjoint(heldout_inputs))
            self.assertGreater(len(heldout_inputs), 0)

    def test_shift_left_op(self) -> None:
        self.assertEqual(OPS["L"]("abcd"), "bcda")
        self.assertEqual(OPS["L"]("xy"), "yx")
        corpus = build_sft_corpus(seed=5, ops=("L",), lengths=(4,), inputs_per_op_length=30)
        for e in corpus.train + corpus.heldout:
            self.assertEqual(e.op, "L")
            self.assertEqual(e.expected_output, OPS["L"](e.prompt[1:-1]))

    def test_rejects_unknown_op(self) -> None:
        with self.assertRaises(ValueError):
            build_sft_corpus(seed=0, ops=("Z",))


if __name__ == "__main__":
    unittest.main()
