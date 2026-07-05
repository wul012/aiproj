"""Tests for v1195 task-similarity -> catastrophic forgetting.

Analytic table/overlap logic and the stats helpers are tested directly; the verdict is a
deterministic function of a cached set of accuracies, so the decide() ladder is exercised on
synthetic caches (no training). A tiny p=7 smoke runs the real Phase-A primitives.
"""
from __future__ import annotations

import math
import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.continual_v1193 import ContinualConfig  # noqa: E402
from minigpt.similarity_v1195 import (  # noqa: E402
    SimilarityConfig, analytic_overlap, build_report, build_rows, conflict_overlap_masks,
    decide, f_add_table, mixture_table, run_phase_a, spearman, spearman_perm_p, summarize,
    type_table,
)
from minigpt.similarity_v1195_decision import decide_similarity  # noqa: E402
from minigpt.similarity_v1195_report import build_similarity_report  # noqa: E402

P = 23
MIX_SS = (1.0, 0.875, 0.75, 0.5, 0.25, 0.0)


# --------------------------------------------------------------------------- analytic tables
class Tables(unittest.TestCase):
    def test_overlap_endpoints(self):
        self.assertEqual(analytic_overlap(type_table("add_same", P, 0, 7), P), 1.0)
        self.assertEqual(analytic_overlap(type_table("add_offset", P, 0, 7), P), 0.0)  # c0!=0 never agrees
        # linear (2a+b)==(a+b) iff a==0 -> p cells -> exactly 1/p
        self.assertAlmostEqual(analytic_overlap(type_table("linear", P, 0, 7), P), 1.0 / P, places=6)

    def test_mul_overlap_is_collisions_not_zero(self):
        ov = analytic_overlap(type_table("mul", P, 0, 7), P)
        self.assertGreater(ov, 0.0)          # a*b==a+b mod p has solutions
        self.assertLess(ov, 0.2)

    def test_mixture_stratified_overlap_at_least_s(self):
        tr = torch.zeros(P, P, dtype=torch.bool); tr[:, : int(0.8 * P)] = True
        te = ~tr
        for s in (0.0, 0.25, 0.5, 0.75, 1.0):
            mt = mixture_table(s, P, 7, tr, te)
            self.assertGreaterEqual(analytic_overlap(mt, P, tr) + 1e-9, s)   # collisions only push up
            self.assertGreaterEqual(analytic_overlap(mt, P, te) + 1e-9, s)

    def test_mixture_table_deterministic(self):
        tr = torch.zeros(P, P, dtype=torch.bool); tr[:, :18] = True
        te = ~tr
        a = mixture_table(0.5, P, 7, tr, te)
        b = mixture_table(0.5, P, 7, tr, te)
        self.assertTrue(torch.equal(a, b))                      # byte-identical rebuild

    def test_conflict_overlap_split_partitions_cells(self):
        tr = torch.zeros(P, P, dtype=torch.bool); tr[:, :18] = True
        te = ~tr
        mt = mixture_table(0.5, P, 7, tr, te)
        conf, ovl = conflict_overlap_masks(mt, P, te)
        self.assertEqual(int(conf.sum() + ovl.sum()), int(te.sum()))
        self.assertEqual(int((conf & ovl).sum()), 0)

    def test_build_rows_layout_and_targets(self):
        cfg = SimilarityConfig(base=ContinualConfig(p=7))
        cells = torch.ones(7, 7, dtype=torch.bool)
        table = type_table("mul", 7, 0, 7)
        rows = build_rows(cfg, table, "B", cells)
        for r in rows[:6]:
            self.assertEqual(int(r[4]), (int(r[0]) * int(r[2])) % 7)   # answer from the table
            self.assertEqual(int(r[1]), 7 + 1)                          # TIMES op-token


# --------------------------------------------------------------------------- stats helpers
class Stats(unittest.TestCase):
    def test_spearman_monotone(self):
        self.assertAlmostEqual(spearman([0, 1, 2, 3], [9, 6, 4, 1]), -1.0, places=6)
        self.assertAlmostEqual(spearman([0, 1, 2, 3], [1, 4, 6, 9]), 1.0, places=6)

    def test_perm_p_significant_for_perfect_monotone(self):
        p = spearman_perm_p([0.0, 0.3, 0.5, 0.8, 1.0], [0.9, 0.7, 0.5, 0.3, 0.1])
        self.assertLessEqual(p, 0.05)


# --------------------------------------------------------------------------- synthetic caches
def synth_cache(arm_forget, arm_overlap, *, p=P, seeds=(1, 2, 3), plateau=0.98,
                accB_conflict=0.85, accB_train=0.9, emb_drift=5.0, prior=0.05,
                cont_after=0.97, joint_accA=0.9, joint_accB=0.86, leak=True,
                accB_overrides=None, drift_overrides=None, no_conflict=("type:add_same", "mix:1.000")):
    """Build a Phase-A-schema cache from per-arm mean forgetting + overlap. Forgetting gets a
    +/-0.01 jitter across 3 seeds (nonzero std). Learnedness is driven by accB_train_conflict
    (the gate signal); accB_overrides lowers it to make an arm 'unlearned'."""
    accB_overrides = accB_overrides or {}
    drift_overrides = drift_overrides or {}
    arms, overlaps, b_majority = {}, {}, {}
    plat = {s: plateau for s in seeds}
    for key, f in arm_forget.items():
        ov = arm_overlap[key]
        jit = [-0.01, 0.0, 0.01][: len(seeds)]
        conf = None if key in no_conflict else accB_overrides.get(key, accB_conflict)
        recs = {}
        for i, s in enumerate(seeds):
            fi = f + (jit[i] if i < len(jit) else 0.0)
            recs[s] = {
                "accA_after_B": plateau - fi,
                "accB_conflict": conf,
                "accB_overlap": None,
                "accB_train": accB_train,
                "accB_train_conflict": conf,
                "accB_train_overlap": None,
                "emb_drift": drift_overrides.get(key, emb_drift),
                "total_drift": drift_overrides.get(key, emb_drift) * 2,
                "trajA": [0.2, 0.05, plateau - fi],
            }
        arms[key] = recs
        overlaps[key] = {s: (ov, ov, ov) for s in seeds}
        b_majority[key] = prior
    return {
        "config": {"p": p, "train_frac": 0.8, "b_budget": 1500, "weight_decay": 0.5,
                   "seeds": list(seeds), "mixture_ss": list(MIX_SS),
                   "type_funcs": list(("add_same", "add_offset", "linear", "mul", "rand")),
                   "add_offset_c0": 7},
        "chance": 1.0 / p, "leak_free": leak, "b_majority": b_majority,
        "plateau": plat, "arms": arms, "overlaps": overlaps,
        "continue_on_A": {s: {"accA_after_B": cont_after} for s in seeds},
        "joint": {s: {"accA": joint_accA, "accB": joint_accB} for s in seeds},
    }


# a clean "overlap governs forgetting" scenario (super-linear, family-irrelevant)
GOVERNED_FORGET = {
    "mix:1.000": 0.00, "mix:0.875": 0.35, "mix:0.750": 0.50, "mix:0.500": 0.65,
    "mix:0.250": 0.75, "mix:0.000": 0.86,
    "type:add_same": 0.00, "type:add_offset": 0.86, "type:linear": 0.84,
    "type:mul": 0.86, "type:rand": 0.83,
}
GOVERNED_OVERLAP = {
    "mix:1.000": 1.00, "mix:0.875": 0.89, "mix:0.750": 0.78, "mix:0.500": 0.55,
    "mix:0.250": 0.30, "mix:0.000": 0.045,
    "type:add_same": 1.00, "type:add_offset": 0.00, "type:linear": 0.043,
    "type:mul": 0.045, "type:rand": 0.05,
}


class DecideLadder(unittest.TestCase):
    def cfg(self):
        return SimilarityConfig(base=ContinualConfig(p=P), seeds=(1, 2, 3))

    def test_governed_verdict(self):
        info = decide(summarize(synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "forgetting_governed_by_output_overlap")
        f = info["flags"]
        self.assertTrue(f["c1_monotone_slope"])
        self.assertLessEqual(f["spearman_overlap_forget"], -0.8)
        self.assertTrue(f["c2_family_does_not_protect"])
        self.assertTrue(f["c3_type_points_on_curve"])
        self.assertTrue(f["superlinear_vs_overwrite_null"])
        self.assertFalse(f["structure_at_fixed_overlap"])
        self.assertTrue(f["overlap_survives_accB_and_drift"])

    def test_family_protects_branch(self):
        # add_offset (same op) forgets much LESS than mul -> family DOES protect
        fg = dict(GOVERNED_FORGET); fg["type:add_offset"] = 0.20
        info = decide(summarize(synth_cache(fg, GOVERNED_OVERLAP), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "forgetting_tracks_task_type")
        self.assertTrue(info["flags"]["family_protects"])

    def test_residual_structure_branch(self):
        # a learned low-overlap type point sits far OFF the mixture curve (rand barely forgets)
        fg = dict(GOVERNED_FORGET); fg["type:rand"] = 0.30
        info = decide(summarize(synth_cache(fg, GOVERNED_OVERLAP), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "overlap_grades_forgetting_with_residual_structure")

    def test_no_overlap_dependence_when_flat(self):
        flat = {k: 0.80 for k in GOVERNED_FORGET}
        flat["type:add_same"] = 0.0; flat["mix:1.000"] = 0.0
        info = decide(summarize(synth_cache(flat, GOVERNED_OVERLAP), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "no_overlap_dependence")

    def test_review_not_consolidated(self):
        c = synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP, plateau=0.5)
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "task_a_not_consolidated")

    def test_review_no_floor(self):
        c = synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP, cont_after=0.4)  # continue-on-A forgets a lot
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "no_forgetting_floor")

    def test_review_leak(self):
        c = synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP, leak=False)
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "operand_leak")

    def test_review_not_jointly_learnable(self):
        c = synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP, joint_accB=0.06)  # joint can't hold B
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "not_jointly_learnable")

    def test_review_too_few_curve_points(self):
        # make most mixture arms UNLEARNED (low accB) -> < 4 interior curve points
        ab = {k: 0.06 for k in ("mix:0.875", "mix:0.750", "mix:0.500")}
        c = synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP, accB_overrides=ab)
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "too_few_learnable_curve_points")

    def test_report_shape(self):
        r = summarize(synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP), self.cfg())
        info = decide(r, self.cfg())
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(len(report["rows"]), len(GOVERNED_FORGET))
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertIn("curve_points", report)
        self.assertIn("residuals", report)

    def test_extracted_decision_matches_public_facade(self):
        cfg = self.cfg()
        result = summarize(synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP), cfg)
        self.assertEqual(decide(result, cfg), decide_similarity(result, cfg))

    def test_extracted_report_matches_public_facade(self):
        cfg = self.cfg()
        result = summarize(synth_cache(GOVERNED_FORGET, GOVERNED_OVERLAP), cfg)
        info = decide(result, cfg)
        expected = build_report(result, info, "synthetic", generated_at="2026-01-01T00:00:00Z")
        actual = build_similarity_report(
            result,
            info,
            "synthetic",
            generated_at="2026-01-01T00:00:00Z",
            c1_min_range=SimilarityConfig().c1_min_range,
            equiv_delta=SimilarityConfig().equiv_delta,
        )
        self.assertEqual(actual, expected)


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        base = ContinualConfig(p=7, train_frac=0.8, consolidate_max_steps=120, eval_every=40,
                               plateau_acc=0.0, plateau_hold=1, b_budget=40, b_eval_every=20,
                               joint_max_steps=80)
        cfg = SimilarityConfig(base=base, seeds=(1337,), mixture_ss=(1.0, 0.5, 0.0),
                               type_funcs=("add_same", "mul", "rand"))
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertIn("type:mul", cache["arms"])
        self.assertIn("mix:0.500", cache["arms"])
        rec = cache["arms"]["type:mul"][1337]
        self.assertIn("emb_drift", rec)
        self.assertIn("accB_train", rec)
        # overlaps recorded as (global, train, test)
        self.assertEqual(len(cache["overlaps"]["type:mul"][1337]), 3)
        # summarize/decide run without error on a real (tiny) cache
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
