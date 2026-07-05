"""Tests for v1197 induction-circuit dissection.

The verdict is a deterministic function of cached head-scores + ablation accuracies, so the
decide() ladder runs on synthetic caches. A tiny real Phase-A smoke exercises the ablation
machinery (head scoring, mean/zero hooks, composition) end to end.
"""
from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.induction_circuit_v1197 import (  # noqa: E402
    CircuitConfig, build_report, decide, run_phase_a, summarize,
)
from minigpt.induction_circuit_v1197_decision import decide_induction_circuit  # noqa: E402
from minigpt.induction_circuit_v1197_report import build_report as extracted_build_report  # noqa: E402

SEEDS = (1, 2, 3, 4, 5)
NH = 8


def synth_cache(*, n_head=NH, seeds=SEEDS, K=20, prev_high=(0, 1, 2, 3), ind_high=(0, 1, 2, 3),
                base=0.99, unigram=0.14, topprev_full=0.10, botprev_full=0.92, topind_full=0.09,
                botind_full=0.93, zero_topprev_full=0.08, zero_topind_full=0.07,
                single_prev_drop=0.03, single_ind_drop=0.04, comp_intact=0.80, comp_no_prev=0.10,
                comp_no_nonprev=0.78, hi=0.9, lo=0.1, hi_ind=0.8, lo_ind=0.05):
    jit = [-0.01, -0.005, 0.0, 0.005, 0.01]
    kp, ki = len(prev_high), len(ind_high)

    def lst(full, n=n_head):
        a = [base] * (n + 1)
        for k in range(1, n + 1):
            a[k] = full if k >= 1 else base
        a[0] = base
        # only the k==class-size entry is read in the primary path; fill all k>=1 with `full`
        for k in range(1, n + 1):
            a[k] = full
        return a

    seeds_out = {}
    for si, s in enumerate(seeds):
        j = jit[si % len(jit)]
        prev = {f"0,{h}": (hi if h in prev_high else lo) for h in range(n_head)}
        prev.update({f"1,{h}": lo for h in range(n_head)})       # L1 prev scores low
        ind = {f"1,{h}": (hi_ind if h in ind_high else lo_ind) for h in range(n_head)}
        ind.update({f"0,{h}": lo_ind for h in range(n_head)})    # L0 ind scores low
        l0_by_prev = sorted(range(n_head), key=lambda h: prev[f"0,{h}"], reverse=True)
        l1_by_ind = sorted(range(n_head), key=lambda h: ind[f"1,{h}"], reverse=True)
        rec = {"base_acc": base + j, "prev": prev, "ind": ind,
               "l0_by_prev": l0_by_prev, "l1_by_ind": l1_by_ind}
        rec["mean_topprev"] = [base] + [topprev_full + j] * n_head
        rec["mean_botprev"] = [base] + [botprev_full + j] * n_head
        rec["mean_topind"] = [base] + [topind_full + j] * n_head
        rec["mean_botind"] = [base] + [botind_full + j] * n_head
        rec["zero_topprev"] = [base] + [zero_topprev_full + j] * n_head
        rec["zero_botprev"] = [base] + [botprev_full + j] * n_head
        rec["zero_topind"] = [base] + [zero_topind_full + j] * n_head
        rec["zero_botind"] = [base] + [botind_full + j] * n_head
        rec["mean_single_l0"] = [(base - single_prev_drop) if h in prev_high else base for h in range(n_head)]
        rec["mean_single_l1"] = [(base - single_ind_drop) if h in ind_high else base for h in range(n_head)]
        rec["zero_single_l0"] = list(rec["mean_single_l0"])
        rec["zero_single_l1"] = list(rec["mean_single_l1"])
        rec["composition"] = {"kp": kp, "ki": ki, "ind_attn_intact": comp_intact + j,
                              "ind_attn_no_prev": comp_no_prev, "ind_attn_no_nonprev": comp_no_nonprev,
                              "noind_l1_attn_intact": 0.05, "noind_l1_attn_no_prev": 0.05}
        seeds_out[s] = rec
    return {
        "config": {"K": K, "T": 64, "width": 64, "depth": 2, "n_head": n_head, "steps": 1500,
                   "seeds": list(seeds), "tau_prev": 0.40, "tau_ind": 0.35},
        "chance": 1.0 / K, "S": 0.6 * (1 - 1.0 / K), "unigram_acc": unigram, "seeds": seeds_out,
    }


class DecideLadder(unittest.TestCase):
    def test_extracted_decision_matches_public_facade(self):
        cfg = self.cfg()
        result = summarize(synth_cache(), cfg)
        self.assertEqual(decide(result, cfg), decide_induction_circuit(result, cfg))

    def cfg(self):
        return CircuitConfig(seeds=SEEDS)

    def test_clean_redundant_verdict(self):
        info = decide(summarize(synth_cache(), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "circuit_necessary_specific_composed_and_redundant")
        f = info["flags"]
        self.assertTrue(f["necessity"] and f["specificity"] and f["composition"])
        self.assertTrue(f["prev_redundant"] and f["ind_redundant"])
        self.assertEqual(f["tau_grid_agree_frac"], 1.0)

    def test_concentrated_when_single_head_critical(self):
        # a single induction head carries it -> large single-head drop -> not redundant
        c = synth_cache(single_ind_drop=0.85)
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "circuit_necessary_specific_composed_concentrated")
        self.assertFalse(info["flags"]["ind_redundant"])

    def test_not_composed(self):
        c = synth_cache(comp_no_prev=0.79)   # prev-ablation barely drops induction attention
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "circuit_necessary_specific_not_composed")
        self.assertFalse(info["flags"]["composition"])

    def test_circuit_not_clean_when_necessity_fails(self):
        c = synth_cache(topprev_full=0.85, zero_topprev_full=0.85)  # ablating prev barely hurts
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "circuit_not_clean")
        self.assertFalse(info["flags"]["necessity"])

    def test_review_base_not_inducting(self):
        c = synth_cache(base=0.30)
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "base_not_inducting")

    def test_redundancy_unassessed_when_single_head_classes(self):
        # only 1 prev and 1 induction head per seed -> circuit valid but redundancy not assessable
        c = synth_cache(prev_high=(0,), ind_high=(0,))
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "circuit_necessary_specific_composed_redundancy_unassessed")

    def test_review_mean_zero_disagree(self):
        # mean-ablation collapses, zero-ablation does NOT (OOD/confound) -> disagreement
        c = synth_cache(zero_topprev_full=0.90, zero_topind_full=0.90)
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "mean_zero_disagree")

    def test_report_shape(self):
        r = summarize(synth_cache(), self.cfg()); info = decide(r, self.cfg())
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertEqual(report["summary"]["verdict"], "circuit_necessary_specific_composed_and_redundant")

    def test_public_module_reexports_report_builder(self):
        self.assertIs(build_report, extracted_build_report)


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        cfg = CircuitConfig(K=10, T=24, width=16, n_head=4, depth=2, steps=50, batch=64,
                            eval_batch=64, eval_n_batches=2, mech_batch=16, seeds=(1, 2),
                            tau_prev_grid=(0.3, 0.4), tau_ind_grid=(0.3, 0.4))
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertEqual(sorted(cache["seeds"].keys()), [1, 2])
        rec = cache["seeds"][1]
        for k in ("base_acc", "mean_topprev", "zero_topind", "mean_single_l0", "composition"):
            self.assertIn(k, rec)
        self.assertEqual(len(rec["mean_topprev"]), cfg.n_head + 1)   # k = 0..n_head
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
