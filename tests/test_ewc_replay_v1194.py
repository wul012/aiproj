"""Tests for v1194 EWC vs replay for catastrophic forgetting.

Verdict tests run on synthetic frontier caches (the verdict is a deterministic function of the
two frontiers + arms); a tiny p=7 smoke exercises Fisher estimation and the EWC training step.
"""
from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.continual_v1193 import ContinualConfig, build_op, consolidate, make_model, pair_masks  # noqa: E402
from minigpt.ewc_replay_v1194 import (  # noqa: E402
    EWCReplayConfig, build_report, compute_fisher, decide, summarize, train_ewc,
)

SEEDS = (1337, 1338, 1339)

# probe-shaped frontiers: {knob: (accA, accB)}
EWC_ALLORNOTHING = {0.0: (0.05, 0.83), 3e9: (0.15, 0.80), 1e10: (0.24, 0.28), 3e10: (0.39, 0.16),
                    4e10: (0.50, 0.12), 5e10: (0.70, 0.09), 6e10: (0.86, 0.07), 1e11: (0.87, 0.09), 3e11: (0.15, 0.11)}
REPLAY_GOOD = {0: (0.05, 0.83), 4: (0.27, 0.90), 8: (0.62, 0.89), 16: (0.83, 0.85),
               32: (0.83, 0.83), 64: (0.93, 0.83), 128: (0.93, 0.83)}


def synth_cache(*, ewc_front=None, replay_front=None, plateau=0.99, joint=(0.86, 0.84),
                cont_after=0.99, leak=True, majority=0.09, fisher_frac=0.0, hybrid=(0.62, 0.89),
                hybrid_lambda=3e10, hybrid_k=8, p=23):
    ewc_front = ewc_front or EWC_ALLORNOTHING
    replay_front = replay_front or REPLAY_GOOD
    return {
        "config": {"p": p, "task_a": "add", "task_b": "mul", "b_budget": 1500,
                   "ewc_lambdas": sorted(ewc_front), "replay_ks": sorted(replay_front),
                   "b_phase_weight_decay": 0.0, "hybrid_lambda": hybrid_lambda, "hybrid_k": hybrid_k,
                   "seeds": list(SEEDS)},
        "chance": 1.0 / p, "b_majority_prior": majority, "leak_free": leak,
        "accA_plateau": {s: plateau for s in SEEDS},
        "ewc": {float(l): {s: {"accA_after_B": a, "accB_after_B": b, "penalty_ce_ratio": 1.0}
                           for s in SEEDS} for l, (a, b) in ewc_front.items()},
        "replay": {int(k): {s: {"accA_after_B": a, "accB_after_B": b} for s in SEEDS}
                   for k, (a, b) in replay_front.items()},
        "joint": {s: {"accA": joint[0], "accB": joint[1]} for s in SEEDS},
        "hybrid": {s: {"accA_after_B": hybrid[0], "accB_after_B": hybrid[1], "penalty_ce_ratio": 1.0} for s in SEEDS},
        "continue_on_A": {s: {"accA_after_B": cont_after} for s in SEEDS},
        "fisher_degenerate_frac": {s: fisher_frac for s in SEEDS},
    }


class Summarize(unittest.TestCase):
    def test_best_min_scalars(self):
        r = summarize(synth_cache())
        self.assertAlmostEqual(r["M_replay"][0], 0.83, places=2)   # k=16/64 keep both
        self.assertLess(r["M_ewc"][0], 0.30)                       # all-or-nothing: best min ~0.24
        self.assertGreaterEqual(r["ewc_max_accA"][0], 0.85)        # CAN protect A at some lambda
        self.assertGreaterEqual(r["ewc_max_accB"][0], 0.80)        # CAN stay plastic at some lambda


class DecideLadder(unittest.TestCase):
    def test_replay_dominates(self):
        info = decide(summarize(synth_cache()))
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "replay_dominates_ewc")
        f = info["flags"]
        self.assertTrue(f["replay_keeps_both_tasks"] and not f["ewc_keeps_both_tasks"])
        self.assertTrue(f["ewc_all_or_nothing"])              # can protect AND can stay plastic, not together
        self.assertTrue(f["ewc_can_protect_A"] and f["ewc_can_stay_plastic"])

    def test_ewc_dominates_when_frontiers_swapped(self):
        info = decide(summarize(synth_cache(ewc_front=REPLAY_GOOD_AS_EWC(), replay_front=REPLAY_BAD())))
        self.assertEqual(info["verdict"], "ewc_dominates_replay")

    def test_both_mitigate_when_close(self):
        # both frontiers keep both tasks, M within the margin -> neither dominates
        good_e = {0.0: (0.05, 0.83), 1e10: (0.82, 0.84), 1e11: (0.9, 0.4)}
        good_r = {0: (0.05, 0.83), 16: (0.84, 0.85), 64: (0.9, 0.83)}
        info = decide(summarize(synth_cache(ewc_front=good_e, replay_front=good_r)))
        self.assertEqual(info["verdict"], "both_mitigate_neither_dominates")

    def test_neither_mitigates(self):
        bad = {0: (0.05, 0.83), 1: (0.2, 0.3), 2: (0.3, 0.2)}   # nothing keeps both
        bad_e = {0.0: (0.05, 0.83), 1e10: (0.2, 0.3), 1e11: (0.86, 0.07)}  # can protect/plastic, not both
        info = decide(summarize(synth_cache(ewc_front=bad_e, replay_front=bad)))
        self.assertEqual(info["verdict"], "neither_mitigates")

    def test_review_gates(self):
        self.assertEqual(decide(summarize(synth_cache(plateau=0.5)))["verdict"], "task_a_not_consolidated")
        self.assertEqual(decide(summarize(synth_cache(leak=False)))["verdict"], "operand_leak")
        self.assertEqual(decide(summarize(synth_cache(cont_after=0.4)))["verdict"], "no_forgetting_floor")
        self.assertEqual(decide(summarize(synth_cache(fisher_frac=0.95)))["verdict"], "fisher_degenerate")

    def test_review_ewc_anchor_does_not_engage(self):
        # EWC never protects A at any lambda -> can't fairly claim it "fails"
        weak = {0.0: (0.05, 0.83), 1e10: (0.1, 0.7), 1e11: (0.12, 0.5)}
        self.assertEqual(decide(summarize(synth_cache(ewc_front=weak)))["verdict"], "ewc_anchor_does_not_engage")

    def test_review_b_not_learned(self):
        # no replay/ewc point learns B above prior+margin
        nob_e = {0.0: (0.05, 0.10), 1e11: (0.86, 0.08)}
        nob_r = {0: (0.05, 0.10), 64: (0.9, 0.11)}
        self.assertEqual(decide(summarize(synth_cache(ewc_front=nob_e, replay_front=nob_r)))["verdict"], "task_b_not_learned")


def REPLAY_GOOD_AS_EWC():
    return {0.0: (0.05, 0.83), 1e10: (0.62, 0.89), 3e10: (0.83, 0.85), 6e10: (0.93, 0.83), 1e11: (0.93, 0.83)}


def REPLAY_BAD():
    return {0: (0.05, 0.83), 8: (0.24, 0.28), 32: (0.39, 0.16), 128: (0.86, 0.07)}


class ReportShape(unittest.TestCase):
    def test_build_report(self):
        r = summarize(synth_cache()); info = decide(r)
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for field in report["csv_fieldnames"]:
            self.assertIn(field, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertIn("ewc_frontier", report)
        self.assertIn("replay_frontier", report)


class FisherAndEWCTraining(unittest.TestCase):
    def test_fisher_and_ewc_step_run(self):
        base = ContinualConfig(p=7, consolidate_max_steps=120, eval_every=40, plateau_acc=0.0,
                               plateau_hold=1, b_budget=30)
        cfg = EWCReplayConfig(base=base, ewc_lambdas=(0.0, 1e3), replay_ks=(0, 4))
        dev = torch.device("cpu")
        tr, te = pair_masks(base, 1337)
        A_tr, A_te = build_op(base, "A", tr), build_op(base, "A", te)
        B_tr, B_te = build_op(base, "B", tr), build_op(base, "B", te)
        state, plateau, _ = consolidate(base, A_tr, A_te, 1337, dev)
        model = make_model(base).to(dev); model.load_state_dict(state)
        theta_star = {n: p.detach().clone() for n, p in model.named_parameters()}
        fisher = compute_fisher(model, A_tr.to(dev))
        # Fisher has one entry per parameter tensor and is non-negative
        self.assertEqual(set(fisher), {n for n, _ in model.named_parameters()})
        self.assertTrue(all((f >= 0).all() for f in fisher.values()))
        out = train_ewc(cfg, state, theta_star, fisher, B_tr, 1e3, a_test=A_te, b_test=B_te, device=dev)
        self.assertIn("accA_after_B", out)
        self.assertIn("penalty_ce_ratio", out)
        # hybrid path (with replay) also runs
        outh = train_ewc(cfg, state, theta_star, fisher, B_tr, 1e3, a_test=A_te, b_test=B_te,
                         device=dev, a_train=A_tr, replay_k=4, seed=1337)
        self.assertIn("accA_after_B", outh)


if __name__ == "__main__":
    unittest.main()
