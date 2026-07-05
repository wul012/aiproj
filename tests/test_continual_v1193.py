"""Tests for v1193 continual learning / catastrophic forgetting.

Pure-analysis tests run on synthetic caches (the verdict is a deterministic function of the
cached accuracies, so no training needed); a tiny p=7 smoke exercises the task builder, the
operand-leak verifier, and the training primitives.
"""
from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.continual_v1193 import (  # noqa: E402
    ContinualConfig, build_op, build_report, consolidate, decide, majority_prior, pair_masks,
    run_phase_a, savings_probe, summarize, train_phase, verify_no_leak, vocab_size,
)
from minigpt.continual_v1193_decision import decide_continual  # noqa: E402
from minigpt.continual_v1193_report import build_report as extracted_build_report  # noqa: E402

SEEDS = (1337, 1338, 1339)


def synth_cache(*, plateau=0.99, naive_after=0.05, accB=0.90, cont_after=0.99, rand_after=0.05,
                wrong_after=0.05, joint_accA=0.97, joint_accB=0.90, leak=True, majority=0.08,
                replay_after=None, savings=None, p=23):
    """A synthetic Phase-A cache matching run_phase_a's schema (identical across seeds)."""
    if replay_after is None:
        replay_after = {0: naive_after, 8: 0.40, 32: 0.70, 128: 0.85}  # acc_A rises with buffer
    if savings is None:
        savings = [[1, 0.1], [2, 0.15], [5, 0.3], [10, 0.5], [20, 0.7], [50, 0.85], [100, 0.95], [200, 0.99], [400, 0.99]]
    traj = [0.22, 0.05, 0.05, naive_after]
    cache = {
        "config": {"p": p, "task_a": "add", "task_b": "mul", "train_frac": 0.8, "b_budget": 1500,
                   "replay_buffer_sizes": sorted(replay_after), "seeds": list(SEEDS), "weight_decay": 0.5},
        "chance": 1.0 / p, "b_majority_prior": majority, "leak_free": leak,
        "accA_plateau": {s: plateau for s in SEEDS},
        "naive": {s: {"accA_after_B": naive_after, "accB_after_B": accB, "trajA": traj} for s in SEEDS},
        "random_label_B": {s: {"accA_after_B": rand_after} for s in SEEDS},
        "continue_on_A": {s: {"accA_after_B": cont_after} for s in SEEDS},
        "joint": {s: {"accA": joint_accA, "accB": joint_accB} for s in SEEDS},
        "savings": {s: savings for s in SEEDS},
        "wrong_replay": {s: {"accA_after_B": wrong_after} for s in SEEDS},
        "replay": {bs: {s: {"accA_after_B": replay_after[bs], "accB_after_B": accB, "trajA": traj} for s in SEEDS}
                   for bs in replay_after},
    }
    return cache


class Summarize(unittest.TestCase):
    def test_forgetting_and_aggregates(self):
        r = summarize(synth_cache())
        self.assertAlmostEqual(r["naive_forget"][0], 0.99 - 0.05, places=5)
        self.assertAlmostEqual(r["continue_on_A_forget"][0], 0.0, places=5)
        self.assertEqual(r["replay_max_bs"], 128)
        self.assertLess(r["replay_forget"][128][0], r["replay_forget"][0][0])   # more replay -> less forgetting


class DecideLadder(unittest.TestCase):
    def test_extracted_decision_matches_public_facade(self):
        result = summarize(synth_cache())
        cfg = ContinualConfig()
        self.assertEqual(decide(result, cfg), decide_continual(result, cfg))

    def test_headline_catastrophic_mitigated(self):
        info = decide(summarize(synth_cache()))
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "catastrophic_forgetting_mitigated_by_replay")
        f = info["flags"]
        self.assertTrue(f["forgets"] and f["catastrophic"])
        self.assertTrue(f["replay_reduces_forgetting"] and f["replay_specific"])
        self.assertFalse(f["wrong_replay_reduces"])
        self.assertTrue(f["replay_dose_response_monotone"])
        # random-label-B forgets as much -> distribution-shift, not task-structure specific
        self.assertTrue(f["forgetting_is_distribution_shift_not_structure"])
        self.assertFalse(f["forgetting_is_task_structure_specific"])

    def test_structure_specific_when_random_b_forgets_less(self):
        # if random-label-B barely forgets, real-B's drop IS task-structure specific
        info = decide(summarize(synth_cache(rand_after=0.95)))
        self.assertTrue(info["flags"]["forgetting_is_task_structure_specific"])

    def test_no_forgetting_null(self):
        info = decide(summarize(synth_cache(naive_after=0.99, rand_after=0.99,
                                            replay_after={0: 0.99, 8: 0.99, 32: 0.99, 128: 0.99})))
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "no_catastrophic_forgetting")

    def test_partial_when_drop_not_to_chance(self):
        # drop to 0.5 (>> 3*chance) is partial, not catastrophic
        info = decide(summarize(synth_cache(naive_after=0.5, rand_after=0.5,
                                            replay_after={0: 0.5, 8: 0.65, 32: 0.8, 128: 0.9})))
        self.assertEqual(info["verdict"], "partial_forgetting_mitigated_by_replay")

    def test_not_mitigated_when_replay_useless(self):
        # replay does not reduce forgetting at any buffer size (all == naive)
        info = decide(summarize(synth_cache(replay_after={0: 0.05, 8: 0.05, 32: 0.05, 128: 0.05})))
        self.assertEqual(info["verdict"], "catastrophic_forgetting_not_mitigated_by_replay")

    def test_not_mitigated_when_wrong_replay_also_helps(self):
        # if replaying B also protects A, replay is not specific
        info = decide(summarize(synth_cache(wrong_after=0.85)))
        self.assertFalse(info["flags"]["replay_specific"])
        self.assertEqual(info["verdict"], "catastrophic_forgetting_not_mitigated_by_replay")

    def test_review_a_not_consolidated(self):
        info = decide(summarize(synth_cache(plateau=0.5)))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "task_a_not_consolidated")

    def test_review_b_not_learned(self):
        info = decide(summarize(synth_cache(accB=0.10, majority=0.08)))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "task_b_not_learned")

    def test_review_operand_leak(self):
        info = decide(summarize(synth_cache(leak=False)))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "operand_leak")

    def test_review_no_floor(self):
        # continue-on-A forgets a lot -> the setup is unstable, not a clean forgetting measurement
        info = decide(summarize(synth_cache(cont_after=0.4)))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "no_forgetting_floor")

    def test_savings_masking_flag(self):
        fast = [[1, 0.99]] + [[k, 0.99] for k in (2, 5, 10, 20, 50, 100, 200, 400)]
        self.assertTrue(decide(summarize(synth_cache(savings=fast)))["flags"]["savings_fast_masking"])
        slow = [[k, 0.1] for k in (1, 2, 5, 10, 20, 50, 100, 200, 400)]
        self.assertFalse(decide(summarize(synth_cache(savings=slow)))["flags"]["savings_fast_masking"])


class ReportShape(unittest.TestCase):
    def test_public_module_reexports_report_builder(self):
        self.assertIs(build_report, extracted_build_report)

    def test_build_report(self):
        r = summarize(synth_cache()); info = decide(r)
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        self.assertEqual(report["rows"][0]["arm"], "consolidated_A")
        for field in report["csv_fieldnames"]:
            self.assertIn(field, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertIn("replay_curve", report)
        self.assertEqual(report["summary"]["task_b"], "mul")


class TaskAndTraining(unittest.TestCase):
    def test_global_mask_quarantines_test_operands(self):
        cfg = ContinualConfig(p=11)
        tr, te = pair_masks(cfg, 1337)
        A_tr = build_op(cfg, "A", tr); A_te = build_op(cfg, "A", te)
        B_tr = build_op(cfg, "B", tr)
        self.assertTrue(verify_no_leak(A_tr, A_te))       # A train/test disjoint operands
        self.assertTrue(verify_no_leak(B_tr, A_te))       # B-train operands never touch A-test operands

    def test_build_op_layout_and_targets(self):
        cfg = ContinualConfig(p=7)
        tr, _ = pair_masks(cfg, 1)
        A = build_op(cfg, "A", tr); B = build_op(cfg, "B", tr)
        # row [a, op, b, EQ, c]; A adds, B multiplies
        for row in A[:5]:
            self.assertEqual(int(row[4]), (int(row[0]) + int(row[2])) % 7)
            self.assertEqual(int(row[1]), cfg.p)          # PLUS token
        for row in B[:5]:
            self.assertEqual(int(row[4]), (int(row[0]) * int(row[2])) % 7)
            self.assertEqual(int(row[1]), cfg.p + 1)      # TIMES token

    def test_majority_prior(self):
        cfg = ContinualConfig(p=7)
        tr, _ = pair_masks(cfg, 1)
        mp = majority_prior(build_op(cfg, "B", tr), 7)
        self.assertTrue(0.0 < mp < 1.0)

    def test_training_primitives_run(self):
        # tiny smoke: consolidate + one B phase run without error, sane shapes
        cfg = ContinualConfig(p=7, consolidate_max_steps=120, eval_every=40, plateau_acc=0.0,
                              plateau_hold=1, b_budget=40, b_eval_every=20, savings_ks=(1, 2))
        tr, te = pair_masks(cfg, 1337)
        A_tr, A_te = build_op(cfg, "A", tr), build_op(cfg, "A", te)
        B_tr, B_te = build_op(cfg, "B", tr), build_op(cfg, "B", te)
        state, plateau, steps = consolidate(cfg, A_tr, A_te, 1337, torch.device("cpu"))
        self.assertIsInstance(plateau, float)
        self.assertGreater(steps, 0)
        out = train_phase(cfg, state, B_tr, a_test=A_te, b_test=B_te, seed=1337, device=torch.device("cpu"))
        self.assertIn("accA_after_B", out)
        self.assertIn("trajA", out)
        curve = savings_probe(cfg, out["state"], A_tr, A_te, plateau, 1337, torch.device("cpu"))
        self.assertEqual(len(curve), len(cfg.savings_ks))


if __name__ == "__main__":
    unittest.main()
