"""Tests for v1198 induction OV-copying circuit.

The verdict is a deterministic function of cached per-head OV copying scores + DLA gaps, so the
decide() ladder runs on synthetic caches. A tiny real Phase-A smoke exercises the OV-matrix and
DLA machinery (hooks, ln_f folding) end to end.
"""
from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.induction_ov_v1198 import (  # noqa: E402
    OVConfig, build_report, copying_scores, decide, ov_matrix, run_phase_a, summarize,
)

SEEDS = (1, 2, 3, 4, 5)
NH = 4


def synth_cache(*, n_head=NH, seeds=SEEDS, K=20, base=0.99, unigram=0.14,
                ind_heads=(0, 1, 2), prev_heads=(0,),
                ind_copy_z=2.0, ctrl_copy_z=-0.3, prev_copy_z=-0.9, gram_copy_z=3.5,
                ind_diag_max=0.6, ind_dla=0.5, ctrl_dla=-0.05, prev_dla=0.0,
                ind_low_score=0.10):
    """Synthetic Phase-A cache. Defaults => the clean copying verdict. Knobs flip each branch."""
    jit = [-0.01, -0.005, 0.0, 0.005, 0.01]
    seeds_out = {}
    for si, s in enumerate(seeds):
        j = jit[si % len(jit)]
        prev = {f"0,{h}": (0.9 if h in prev_heads else 0.1) for h in range(n_head)}
        prev.update({f"1,{h}": 0.05 for h in range(n_head)})
        ind = {f"1,{h}": (0.8 if h in ind_heads else ind_low_score) for h in range(n_head)}
        ind.update({f"0,{h}": 0.05 for h in range(n_head)})
        copy_z = {}
        diag_max = {}
        dla_gap = {}
        for h in range(n_head):
            copy_z[f"1,{h}"] = (ind_copy_z + j) if h in ind_heads else ctrl_copy_z
            copy_z[f"0,{h}"] = (prev_copy_z if h in prev_heads else 0.0)
            diag_max[f"1,{h}"] = (ind_diag_max if h in ind_heads else 0.05)
            diag_max[f"0,{h}"] = 0.05
            dla_gap[f"1,{h}"] = (ind_dla + j) if h in ind_heads else ctrl_dla
            dla_gap[f"0,{h}"] = (prev_dla if h in prev_heads else 0.0)
        rec = {
            "base_acc": base + j, "prev": prev, "ind": ind,
            "copy_z": copy_z, "diag_is_max": diag_max, "dla_gap": dla_gap,
            "dla_correct": {k: dla_gap[k] for k in dla_gap}, "dla_wrong": {k: 0.0 for k in dla_gap},
            "gram_diag_is_max": 1.0, "gram_copy_z": gram_copy_z,
        }
        seeds_out[s] = rec
    return {
        "config": {"K": K, "T": 64, "width": 64, "depth": 2, "n_head": n_head, "steps": 1500,
                   "seeds": list(seeds), "tau_prev": 0.30, "tau_ind": 0.35},
        "chance": 1.0 / K, "S": 0.6 * (1 - 1.0 / K), "unigram_acc": unigram, "seeds": seeds_out,
    }


class DecideLadder(unittest.TestCase):
    def cfg(self):
        return OVConfig(seeds=SEEDS)

    def test_clean_copying_verdict(self):
        info = decide(summarize(synth_cache(), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "induction_ov_is_copying_circuit")
        f = info["flags"]
        self.assertTrue(f["copy_ok"] and f["dla_ok"])
        self.assertGreater(f["ind_copy_z"], f["ctrl_copy_z"])
        self.assertGreater(f["ind_dla_gap"], f["ctrl_dla_gap"])
        self.assertEqual(f["tau_grid_agree_frac"], 1.0)

    def test_paired_not_gram_driven(self):
        # even with a huge tied-embedding Gram, if induction does NOT beat the control the verdict
        # is the null -- proving the verdict is the PAIRED contrast, not the Gram diagonal (lens-1)
        c = synth_cache(ind_copy_z=-0.2, ind_dla=-0.04, gram_copy_z=9.9)
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "induction_ov_not_copying")
        self.assertFalse(info["flags"]["copy_ok"])

    def test_not_copying_null(self):
        # induction OV is flat AND DLA is flat -> consistent null
        c = synth_cache(ind_copy_z=0.1, ind_diag_max=0.05, ind_dla=-0.02)
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "induction_ov_not_copying")

    def test_ov_dla_disagree(self):
        # weight-level says copying but DLA does not (LN distortion) -> review
        c = synth_cache(ind_dla=-0.02)
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "ov_dla_disagree")
        self.assertTrue(info["flags"]["copy_ok"])
        self.assertFalse(info["flags"]["dla_ok"])

    def test_review_base_not_inducting(self):
        c = synth_cache(base=0.30)
        self.assertEqual(decide(summarize(c, self.cfg()), self.cfg())["verdict"], "base_not_inducting")

    def test_review_circuit_not_classifiable(self):
        # all four L1 heads are induction -> no non-induction control head -> not classifiable
        c = synth_cache(ind_heads=(0, 1, 2, 3))
        info = decide(summarize(c, self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "circuit_not_classifiable")

    def test_copy_needs_positive_sign(self):
        # induction beats control by margin but is itself negative (anti-copying) -> copy_ok False
        c = synth_cache(ind_copy_z=0.2, ctrl_copy_z=-1.5, prev_copy_z=-1.5, ind_diag_max=0.1)
        f = decide(summarize(c, self.cfg()), self.cfg())["flags"]
        self.assertFalse(f["copy_ok"])  # fails copy_z_floor / diag_max_floor despite the margin

    def test_report_shape(self):
        r = summarize(synth_cache(), self.cfg()); info = decide(r, self.cfg())
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertEqual(report["summary"]["verdict"], "induction_ov_is_copying_circuit")


class OVMath(unittest.TestCase):
    def test_copying_scores_identity_is_diagonal(self):
        # a perfectly diagonal matrix => diag_is_max 1.0 and positive copy_z
        M = torch.eye(8) * 3.0 + torch.randn(8, 8) * 0.01
        dim, cz = copying_scores(M)
        self.assertGreater(dim, 0.9)
        self.assertGreater(cz, 1.0)

    def test_copying_scores_random_is_flat(self):
        torch.manual_seed(0)
        M = torch.randn(20, 20)
        dim, cz = copying_scores(M)
        self.assertLess(dim, 0.3)
        self.assertLess(abs(cz), 1.0)


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        cfg = OVConfig(K=10, T=24, width=16, n_head=4, depth=2, steps=40, batch=64,
                       eval_batch=64, eval_n_batches=2, mech_batch=16, seeds=(1, 2),
                       tau_ind_grid=(0.3, 0.4))
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertEqual(sorted(cache["seeds"].keys()), [1, 2])
        rec = cache["seeds"][1]
        for k in ("base_acc", "copy_z", "diag_is_max", "dla_gap", "gram_copy_z"):
            self.assertIn(k, rec)
        # OV + DLA computed for every head in both layers
        self.assertEqual(len(rec["copy_z"]), cfg.n_head * cfg.depth)
        self.assertEqual(len(rec["dla_gap"]), cfg.n_head * cfg.depth)
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
