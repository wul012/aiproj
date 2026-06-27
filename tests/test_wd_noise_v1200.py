"""Tests for v1200 weight-decay rescue under label noise.

The verdict is a deterministic function of the cached dose-response trajectories + flip-mask metrics,
so the decide() ladder runs on synthetic caches covering every branch. A tiny real Phase-A smoke
exercises the training + flip-mask-split machinery end to end.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import torch  # noqa: E402

from minigpt.wd_noise_v1200 import WDConfig, build_report, decide, run_phase_a, summarize  # noqa: E402

WDS = (0.0, 0.1, 0.3, 1.0, 3.0, 10.0)
SEEDS = (0, 1, 2, 3, 4)


def _traj(cv, bv, n=11, tail_spread=0.0):
    pts = [0.5, bv] + [cv] * (n - 2)
    if tail_spread:
        pts[-1] = cv + tail_spread
    return [(i * 200, p) for i, p in enumerate(pts)]


def synth_cache(*, scenario="rescue", seeds=SEEDS, tail_spread=0.0):
    # per-wd noise-arm (converged, early-stop-best) clean test errors + flip-mask metrics
    noise_conv = {0.0: 0.32, 0.1: 0.30, 0.3: 0.25, 1.0: 0.15, 3.0: 0.06, 10.0: 0.20}
    noise_best = dict(noise_conv); noise_best[0.0] = 0.30           # wd=0 early-stopping optimum
    train_acc = {0.0: 1.0, 0.1: 0.99, 0.3: 0.93, 1.0: 0.82, 3.0: 0.78, 10.0: 0.62}
    acc_clean = {0.0: 1.0, 0.1: 0.99, 0.3: 0.98, 1.0: 0.97, 3.0: 0.97, 10.0: 0.70}
    fit_noise = {0.0: 1.0, 0.1: 0.85, 0.3: 0.40, 1.0: 0.12, 3.0: 0.06, 10.0: 0.05}
    clean_conv = {0.0: 0.04, 0.1: 0.04, 0.3: 0.05, 1.0: 0.06, 3.0: 0.05, 10.0: 0.12}

    if scenario == "no_rescue":
        noise_conv = {wd: 0.31 for wd in WDS}; noise_best = dict(noise_conv); noise_best[0.0] = 0.30
    elif scenario == "early_stopping":
        noise_conv = {0.0: 0.35, 0.1: 0.30, 0.3: 0.24, 1.0: 0.22, 3.0: 0.22, 10.0: 0.30}
        noise_best = dict(noise_conv); noise_best[0.0] = 0.12       # wd=0 EARLY stop already great
    elif scenario == "helps_not_reject":
        fit_noise = {wd: 0.6 for wd in WDS}                          # rescue but NO selective rejection
    elif scenario == "substrate_unsound":
        clean_conv = {wd: 0.30 for wd in WDS}
    elif scenario == "reference_not_memorized":
        train_acc = dict(train_acc); train_acc[0.0] = 0.90          # wd=0 fails to interpolate the noise

    jit = [-0.01, -0.005, 0.0, 0.005, 0.01]
    arms, flips = {}, {}
    for si, s in enumerate(seeds):
        j = jit[si % len(jit)]
        flips[s] = list(range(50))
        for wd in WDS:
            arms[f"0.2|{wd}|{s}"] = {
                "traj": _traj(noise_conv[wd] + j, noise_best[wd] + j, tail_spread=tail_spread),
                "final_train_acc": train_acc[wd], "acc_clean_subset": acc_clean[wd],
                "fit_to_noise": fit_noise[wd], "logit_norm": 5.0 - wd, "test_err": noise_conv[wd] + j}
            arms[f"0.0|{wd}|{s}"] = {
                "traj": _traj(clean_conv[wd] + j, clean_conv[wd] + j),
                "final_train_acc": 1.0, "acc_clean_subset": 1.0,
                "fit_to_noise": float("nan"), "logit_norm": 5.0 - wd, "test_err": clean_conv[wd] + j}
    return {
        "config": {"L": 21, "n_train": 256, "width": 32, "etas": [0.0, 0.2], "wd_grid": list(WDS),
                   "seeds": list(seeds), "lr": 3e-3, "steps": 8000, "rec_every": 200, "noise_eta": 0.2},
        "arms": arms, "flips": flips,
    }


class DecideLadder(unittest.TestCase):
    def cfg(self):
        return WDConfig(seeds=SEEDS)

    def test_rescue_by_rejecting_noise(self):
        info = decide(summarize(synth_cache(), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "wd_rescues_generalization_by_rejecting_noise")
        f = info["flags"]
        self.assertTrue(f["rescue"] and f["dissociation"] and f["did_ok"])
        self.assertEqual(f["best_wd"], 3.0)
        self.assertTrue(f["interior"])          # 3.0 beats both 0.0 and 10.0
        self.assertTrue(f["robust"])

    def test_no_rescue(self):
        info = decide(summarize(synth_cache(scenario="no_rescue"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "no_wd_rescue")

    def test_wd_equals_early_stopping(self):
        info = decide(summarize(synth_cache(scenario="early_stopping"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "wd_equals_early_stopping")
        self.assertFalse(info["flags"]["rescue"])

    def test_helps_but_not_via_rejection(self):
        info = decide(summarize(synth_cache(scenario="helps_not_reject"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "wd_helps_but_not_via_noise_rejection")
        self.assertTrue(info["flags"]["rescue"])
        self.assertFalse(info["flags"]["dissociation"])

    def test_review_substrate_unsound(self):
        info = decide(summarize(synth_cache(scenario="substrate_unsound"), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "substrate_unsound")

    def test_review_reference_not_memorized(self):
        info = decide(summarize(synth_cache(scenario="reference_not_memorized"), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "reference_not_memorized")

    def test_review_budget_unconverged(self):
        info = decide(summarize(synth_cache(tail_spread=0.12), self.cfg()), self.cfg())
        self.assertEqual(info["verdict"], "budget_unconverged")

    def test_review_too_few_seeds(self):
        c = synth_cache(seeds=(0, 1)); cfg = WDConfig(seeds=(0, 1))
        self.assertEqual(decide(summarize(c, cfg), cfg)["verdict"], "too_few_seeds")

    def test_report_shape(self):
        r = summarize(synth_cache(), self.cfg()); info = decide(r, self.cfg())
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertEqual(report["summary"]["verdict"], "wd_rescues_generalization_by_rejecting_noise")


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        cfg = WDConfig(L=11, n_train=64, n_test=200, width=8, etas=(0.0, 0.2), wd_grid=(0.0, 1.0),
                       seeds=(0, 1), steps=60, rec_every=20)
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertIn("0.2|1.0|0", cache["arms"])
        self.assertIn("0.0|0.0|0", cache["arms"])
        rec = cache["arms"]["0.2|1.0|0"]
        for k in ("traj", "final_train_acc", "acc_clean_subset", "fit_to_noise", "logit_norm", "test_err"):
            self.assertIn(k, rec)
        self.assertEqual(rec["traj"][0][0], 0)               # trajectory starts at step 0
        self.assertIn(0, cache["flips"])                     # flip indices cached
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
