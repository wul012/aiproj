"""v1174 shared distillation helper contract tests."""
from __future__ import annotations

import inspect
import unittest

import torch
import torch.nn.functional as F

import minigpt.distill_v1172 as deterministic
from minigpt.distill_common import _build_xy, kl_term, make_distill_model, shuffle_residual_mass


class DistillCommonContractTests(unittest.TestCase):
    def test_v1172_reexports_common_helpers(self):
        self.assertIs(deterministic.kl_term, kl_term)
        self.assertIs(deterministic.shuffle_residual_mass, shuffle_residual_mass)
        self.assertEqual(inspect.getmodule(deterministic.train_student).__name__, "minigpt.distill_common")

    def test_completion_mask_contract(self):
        X, Y = _build_xy([([4, 5, 6, 7], 2)], block_size=6, pad_id=0)
        self.assertEqual(X.tolist()[0][:3], [4, 5, 6])
        self.assertEqual(Y.tolist()[0][:3], [-100, 6, 7])
        self.assertEqual(Y.tolist()[0][3:], [-100, -100, -100])

    def test_kl_term_zero_at_identical_logits(self):
        torch.manual_seed(1174)
        logits = torch.randn(2, 3, 9)
        mask = torch.ones(2, 3, dtype=torch.bool)
        probs = F.softmax(logits / 2.0, dim=-1)
        self.assertLess(abs(float(kl_term(logits, probs, mask, tau=2.0))), 1e-6)

    def test_make_distill_model_contract(self):
        model = make_distill_model(vocab_size=17, block_size=8, n_layer=1, n_head=1, n_embd=8)
        self.assertEqual(model.config.vocab_size, 17)
        self.assertEqual(model.config.block_size, 8)
        self.assertTrue(model.config.use_rope)
        self.assertEqual(model.config.dropout, 0.0)


if __name__ == "__main__":
    unittest.main()
