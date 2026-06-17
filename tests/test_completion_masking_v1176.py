"""v1176 shared completion-mask helper tests."""
from __future__ import annotations

import unittest

from minigpt.completion_masking import build_completion_xy
from minigpt.distill_common import _build_xy


class CompletionMaskingTests(unittest.TestCase):
    def test_prompt_tokens_are_ignored_completion_tokens_are_targets(self):
        X, Y = build_completion_xy([([7, 8, 9, 10], 2)], block_size=6, pad_id=0)
        self.assertEqual(X.tolist(), [[7, 8, 9, 0, 0, 0]])
        self.assertEqual(Y.tolist(), [[-100, 9, 10, -100, -100, -100]])

    def test_distill_compat_alias_uses_the_same_helper(self):
        self.assertIs(_build_xy, build_completion_xy)

    def test_eos_free_single_completion_position_contract(self):
        X, Y = build_completion_xy([([5, 1, 3], 2), ([6, 1, 4], 2)], block_size=5, pad_id=0)
        self.assertEqual(int((Y != -100).sum()), 2)
        self.assertTrue(((Y[:, 1] != -100)).all())
        self.assertTrue(((Y[:, 0] == -100)).all())


if __name__ == "__main__":
    unittest.main()
