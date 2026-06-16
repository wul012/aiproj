"""v1173 distillation-under-uncertainty tests: the KL-direction wrapper (the
blocking-bug guard), single-position mask, distributional metrics, the gate/verdict
selection, the entropy regression, and an end-to-end smoke."""
from __future__ import annotations

import unittest

import numpy as np
import torch

from minigpt.distill_common import _build_xy, shuffle_residual_mass
from minigpt.distill_v1173 import (
    ARM_ORDER,
    PRIMARY_VERDICTS,
    REVIEW_VERDICTS,
    DistillUncertaintyConfig,
    beats_lower,
    build_stochastic_task,
    decide,
    entropy,
    eps_for_entropy,
    kl_full,
    kl_fwd,
    ols_slope_se,
    run_distill_uncertainty,
    student_P,
)
from minigpt.experiment_utils import significant
from minigpt.model import GPTConfig, MiniGPT
from minigpt.distill_v1173 import EOS, PAD, SEP
from minigpt.tokenizer import CharTokenizer

DEVICE = torch.device("cpu")


class BeatsLowerTests(unittest.TestCase):
    def test_direction_is_lower_is_better(self):
        # distill (0.028) is BETTER (lower) than hard (4.89) -> True; swap -> False
        self.assertTrue(beats_lower(0.028, 0.01, 4.89, 0.2))
        self.assertFalse(beats_lower(4.89, 0.2, 0.028, 0.01))
        # equivalence to the inverted primitive
        self.assertEqual(beats_lower(0.1, 0.01, 0.5, 0.02), significant(0.5, 0.02, 0.1, 0.01))


class MaskTests(unittest.TestCase):
    def test_eos_free_completion_masks_one_position(self):
        # full = [ctx, sep, x], n_prompt=2 -> exactly ONE supervised position (the stochastic output)
        ex = [([5, 9, 1], 2), ([6, 9, 3], 2)]
        X, Y = _build_xy(ex, block_size=8, pad_id=0)
        self.assertEqual(int((Y != -100).sum()), 2)             # one per example
        self.assertTrue(((Y[:, 1] != -100)).all())              # at the output position
        self.assertTrue(((Y[:, 0] == -100)).all())              # prompt position masked


class MetricTests(unittest.TestCase):
    def test_kl_identity_nll(self):
        P = np.array([[0.5, 0.3, 0.2]])
        Q = np.array([[0.4, 0.4, 0.2]])
        kl = kl_fwd(P, Q)[0]
        nll = -(P * np.log(Q + 1e-12)).sum(1)[0]
        H = entropy(P)[0]
        self.assertAlmostEqual(nll, kl + H, places=6)

    def test_kl_full_charges_leakage(self):
        # renormalized KL ignores leaked mass; kl_full penalizes it
        P = np.array([[0.5, 0.3, 0.2]])
        sub_raw = np.array([[0.35, 0.21, 0.14]])   # sums to 0.7 -> 30% leakage
        Pn = sub_raw / sub_raw.sum(1, keepdims=True)
        self.assertLess(kl_fwd(P, Pn)[0], 1e-6)                # shape identical after renorm
        self.assertGreater(kl_full(P, sub_raw)[0], 0.3)        # but full charges ~ -log(0.7)=0.357

    def test_eps_for_entropy(self):
        for target in (0.8, 1.2):
            e = eps_for_entropy(target, 5)
            p0 = (1 - e) + e / 5
            pe = e / 5
            H = -(p0 * np.log(p0) + 4 * pe * np.log(pe))
            self.assertAlmostEqual(H, target, places=2)

    def test_ols_slope(self):
        x = np.linspace(0, 1, 10)
        slope, se = ols_slope_se(x, 2.0 * x + 0.1)
        self.assertAlmostEqual(slope, 2.0, places=3)
        self.assertLess(se, 0.05)
        flat, _ = ols_slope_se(x, np.zeros(10) + 0.5)
        self.assertAlmostEqual(flat, 0.0, places=6)


class TaskTests(unittest.TestCase):
    def test_build_stochastic_task(self):
        P, H, ctx, out = build_stochastic_task(16, seed=0)
        self.assertEqual(P.shape, (16, 5))
        self.assertTrue(np.allclose(P.sum(1), 1.0, atol=1e-6))
        self.assertGreater(H.max() - H.min(), 0.8)             # real entropy spread
        self.assertLessEqual(H.max(), np.log(5) + 1e-6)
        self.assertEqual(len(ctx), 16)


class DecideTests(unittest.TestCase):
    # std=0.02 -> combined-std bar ~0.028; gaps >0.028 are significant, gaps <0.028 are ties
    def _cell(self, soft, argmax, hard, ls, shuf, std=0.02):
        return {"teacher_soft": (soft, std), "teacher_argmax_hard": (argmax, std),
                "scratch_hard": (hard, std), "label_smooth": (ls, std), "shuffled_teacher": (shuf, std),
                "oracle_true_P": (soft * 0.5, std)}

    def test_dark_knowledge_verdict(self):                       # soft beats hard/argmax/ls; sweep recovers
        cell = self._cell(soft=0.05, argmax=0.80, hard=2.0, ls=0.50, shuf=1.5)
        out = decide(cell, None, None, 0.03, {400: 0.05}, slope_lb=0.1)
        self.assertEqual(out["status"], "pass")
        self.assertEqual(out["verdict"], "dark_knowledge_is_data_efficiency_under_uncertainty")
        self.assertTrue(out["flags"]["shuffled_hurts"])

    def test_data_efficiency_not_dark_knowledge(self):           # soft ≈ argmax (tie, gap 0.015)
        cell = self._cell(soft=0.500, argmax=0.515, hard=2.0, ls=0.55, shuf=1.5)
        out = decide(cell, None, None, 0.03, {400: 0.5}, slope_lb=0.1)
        self.assertEqual(out["verdict"], "data_efficiency_not_dark_knowledge")

    def test_generic_not_specific(self):                         # soft beats argmax but ≈ label_smooth
        cell = self._cell(soft=0.050, argmax=0.80, hard=2.0, ls=0.065, shuf=1.5)
        out = decide(cell, None, None, 0.03, {400: 0.05}, slope_lb=0.1)
        self.assertEqual(out["verdict"], "soft_target_generic_not_specific")

    def test_not_recoverable(self):                              # beats all controls but sweep does NOT recover
        cell = self._cell(soft=0.05, argmax=0.80, hard=2.0, ls=0.50, shuf=1.5)
        out = decide(cell, None, None, 0.03, {400: 0.9}, slope_lb=0.1)
        self.assertEqual(out["verdict"], "dark_knowledge_transfer_not_recoverable")

    def test_no_benefit(self):                                   # soft ≈ hard (tie, gap 0.02)
        cell = self._cell(soft=1.98, argmax=1.99, hard=2.0, ls=2.0, shuf=2.0)
        out = decide(cell, None, None, 0.03, {400: 1.98}, slope_lb=-0.1)
        self.assertEqual(out["verdict"], "no_distill_benefit")

    def test_verdict_sets(self):
        for v in ("teacher_ceiling_untrustworthy", "no_valid_entropy_headroom", "controls_missing"):
            self.assertIn(v, REVIEW_VERDICTS)
        for v in ("dark_knowledge_is_data_efficiency_under_uncertainty", "no_distill_benefit"):
            self.assertIn(v, PRIMARY_VERDICTS)


class ShuffleOnSoftTests(unittest.TestCase):
    def test_shuffling_soft_target_increases_kl_to_true(self):
        torch.manual_seed(0)
        # a soft per-context distribution; shuffling residual mass should move it AWAY from P_true
        P = torch.softmax(torch.randn(8, 1, 7), dim=-1)         # (K,1,V)
        perm = torch.randperm(6)
        Q = shuffle_residual_mass(P, perm)
        Pt = P[:, 0, :].numpy()
        kl_unshuf = kl_fwd(Pt, P[:, 0, :].numpy())              # 0 (identity)
        kl_shuf = kl_fwd(Pt, Q[:, 0, :].numpy())
        self.assertLess(kl_unshuf.mean(), 1e-6)
        self.assertGreater(kl_shuf.mean(), 0.05)


class RunSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        P, H, ctx_chars, out_chars = build_stochastic_task(8, seed=0)
        tok = CharTokenizer.train(ctx_chars + out_chars + SEP + EOS + PAD)
        sep_id, pad_id = tok.encode(SEP)[0], tok.encode(PAD)[0]
        contexts = [[tok.encode(c)[0], sep_id] for c in ctx_chars]
        out_ids = [tok.encode(c)[0] for c in out_chars]
        cls.report = run_distill_uncertainty(
            vocab_size=tok.vocab_size, P_true=P, H=H, contexts=contexts, out_ids=out_ids, pad_id=pad_id,
            config=DistillUncertaintyConfig(
                seeds=(1337, 1338), seed_base=1337, k_contexts=8,
                teacher_seeds=(1337, 1338), teacher_layer=2, teacher_head=2, teacher_embd=32, teacher_steps=60,
                teacher_samples_per_ctx=120, student_layer=2, student_head=2, student_embd=32, student_steps=40,
                student_samples_per_ctx=1, sweep_samples=(1, 120), sweep_seeds=(1337,),
                entropy_floor=0.4),
            device=DEVICE, corpus_stats={"heldout_prompts": 8}, generated_at="2026-06-15T00:00:00Z",
        )

    def test_report_shape(self):
        r = self.report
        self.assertEqual(r["title"], "MiniGPT distillation under uncertainty v1173")
        self.assertEqual({row["arm"] for row in r["rows"]}, set(ARM_ORDER))
        self.assertIn(r["summary"]["verdict"], REVIEW_VERDICTS | PRIMARY_VERDICTS)
        self.assertIn("dark_knowledge_delta_by_context", r)

    def test_status_iff_task_learned(self):
        self.assertIs(self.report["status"] == "pass", self.report["summary"]["task_learned"])

    def test_teacher_metrics_present(self):
        s = self.report["summary"]
        for key in ("teacher_kl_to_true", "teacher_entropy", "mean_true_entropy_nats", "label_smoothing_eps"):
            self.assertIn(key, s)


if __name__ == "__main__":
    unittest.main()
