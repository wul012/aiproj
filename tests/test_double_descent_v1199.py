"""Tests for v1199 double descent (absent at toy scale).

The verdict is a deterministic function of the cached sweeps, so the decide() ladder runs on
synthetic caches covering every branch. A tiny real Phase-A smoke exercises the training +
trajectory machinery end to end.
"""
from __future__ import annotations

import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

import torch  # noqa: E402

from minigpt.double_descent_v1199 import (  # noqa: E402
    DDConfig, build_report, decide, run_phase_a, summarize,
)

WIDTHS = (3, 4, 6, 8, 12, 16, 24, 32)
EPOCH_WIDTHS = (16, 32)
SEEDS = (0, 1, 2, 3, 4)


def _traj(kind, interp_step=2000, steps=12000, rec=250, jit=0.0):
    """Build a (step, train_acc, test_err) trajectory for the epoch-wise arm."""
    pts = []
    for s in range(0, steps + 1, rec):
        ta = 1.0 if s >= interp_step else 0.5
        if kind == "control":                              # monotone to ~0.02, no dip-rise
            te = 0.02 if s >= 1000 else max(0.02, 0.59 - 0.57 * s / 1000)
            ta = 1.0 if s >= 250 else 0.5
        elif kind == "sbn":                                # dip BEFORE interp, then rise to plateau
            if s <= 1000:
                te = 0.59 - (0.59 - 0.23) * s / 1000       # 0.59 -> 0.23 (best before interp)
            elif s <= 4000:
                te = 0.23 + (0.36 - 0.23) * (s - 1000) / 3000   # rise 0.23 -> 0.36
            else:
                te = 0.36
        elif kind == "dd":                                 # dip, rise to a PEAK, then RECOVER (2nd descent)
            if s <= 1000:
                te = 0.59 - (0.59 - 0.23) * s / 1000       # -> 0.23
            elif s <= 3000:
                te = 0.23 + (0.40 - 0.23) * (s - 1000) / 2000   # rise to peak 0.40
            else:
                te = max(0.25, 0.40 - (0.40 - 0.25) * (s - 3000) / 4000)  # recover to 0.25
        elif kind == "monotone":                           # plateau ~0.30, best_pre ~= final (no rise)
            te = 0.30 if s >= 1000 else max(0.30, 0.59 - 0.29 * s / 1000)
        pts.append((s, ta, te + jit))
    return pts


def synth_cache(*, ms="null_rise", epoch="sbn", substrate_ok=True, interp=True, seeds=SEEDS):
    jit = [-0.01, -0.005, 0.0, 0.005, 0.01]
    cfg = {"L": 21, "n_train": 256, "etas": [0.0, 0.2], "widths": list(WIDTHS),
           "epoch_widths": list(EPOCH_WIDTHS), "seeds": list(seeds), "tau_interp": 0.99,
           "epoch_steps": 12000, "rec_every": 250}
    model_size, epoch_d = {}, {}

    # model-size test-error patterns for the eta=0.2 (noise) arm
    ms_rise = {3: 0.30, 4: 0.28, 6: 0.26, 8: 0.28, 12: 0.31, 16: 0.33, 24: 0.36, 32: 0.38}  # no 2nd descent
    ms_dd = {3: 0.30, 4: 0.28, 6: 0.40, 8: 0.30, 12: 0.25, 16: 0.20, 24: 0.18, 32: 0.17}     # peak@thresh, drop
    noise_te = ms_dd if ms == "dd" else ms_rise

    for si, s in enumerate(seeds):
        j = jit[si % len(jit)]
        for eta in (0.0, 0.2):
            for w in WIDTHS:
                if eta == 0.0:
                    ta = 1.0
                    te = (0.02 if substrate_ok else 0.30) + max(j, 0)
                else:
                    ta = (0.85 if (w <= 4 or not interp) else 1.0)
                    te = noise_te[w] + j
                model_size[f"{eta}|{w}|{s}"] = {"train_acc": ta, "test_err": te, "steps": 100,
                                                "eff_params": 10 * w}
            for w in EPOCH_WIDTHS:
                k0 = _traj("control", jit=j)
                kn = _traj(epoch, jit=j)
                epoch_d[f"0.0|{w}|{s}"] = {"traj": k0, "interp_step": 250, "eff_params": 10 * w}
                epoch_d[f"0.2|{w}|{s}"] = {"traj": kn, "interp_step": 2000, "eff_params": 10 * w}
    return {"config": cfg, "model_size": model_size, "epoch": epoch_d}


class DecideLadder(unittest.TestCase):
    def cfg(self):
        return DDConfig(seeds=SEEDS)

    def test_no_dd_signal_before_noise(self):
        info = decide(summarize(synth_cache(), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "no_double_descent_signal_before_noise")
        f = info["flags"]
        self.assertFalse(f["ms_second_descent"])
        self.assertFalse(f["epoch_dd"])
        self.assertTrue(f["signal_before_noise"])
        self.assertTrue(f["interp_reached"] and f["ctrl_ok"])

    def test_model_size_double_descent(self):
        info = decide(summarize(synth_cache(ms="dd"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "model_size_double_descent")
        self.assertTrue(info["flags"]["ms_second_descent"])

    def test_epoch_wise_double_descent(self):
        info = decide(summarize(synth_cache(epoch="dd"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "epoch_wise_double_descent")
        self.assertTrue(info["flags"]["epoch_dd"])

    def test_no_dd_monotone(self):
        info = decide(summarize(synth_cache(epoch="monotone"), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "no_double_descent_monotone")
        self.assertFalse(info["flags"]["signal_before_noise"])

    def test_review_substrate_unsound(self):
        info = decide(summarize(synth_cache(substrate_ok=False), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "substrate_unsound")

    def test_review_threshold_unreachable(self):
        info = decide(summarize(synth_cache(interp=False), self.cfg()), self.cfg())
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "threshold_unreachable")

    def test_review_too_few_seeds(self):
        info = decide(summarize(synth_cache(seeds=(0, 1)), DDConfig(seeds=(0, 1))), DDConfig(seeds=(0, 1)))
        self.assertEqual(info["verdict"], "too_few_seeds")

    def test_report_shape(self):
        r = summarize(synth_cache(), self.cfg()); info = decide(r, self.cfg())
        report = build_report(r, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["rows"])
        for fld in report["csv_fieldnames"]:
            self.assertIn(fld, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertEqual(report["summary"]["verdict"], "no_double_descent_signal_before_noise")


class PhaseASmoke(unittest.TestCase):
    def test_tiny_run_phase_a(self):
        cfg = DDConfig(L=11, n_train=64, n_test=200, etas=(0.0, 0.2), widths=(4, 8), epoch_widths=(8,),
                       seeds=(0, 1), ms_max_steps=80, epoch_steps=200, rec_every=50, tau_interp=0.99,
                       tau_grid=(0.98, 0.99))
        cache = run_phase_a(cfg, torch.device("cpu"))
        self.assertIn("0.2|4|0", cache["model_size"])
        self.assertIn("0.2|8|0", cache["epoch"])
        rec = cache["model_size"]["0.2|4|0"]
        for k in ("train_acc", "test_err", "steps", "eff_params"):
            self.assertIn(k, rec)
        traj = cache["epoch"]["0.0|8|0"]["traj"]
        self.assertEqual(traj[0][0], 0)               # records start at step 0
        self.assertGreater(len(traj), 1)
        info = decide(summarize(cache, cfg), cfg)
        self.assertIn(info["status"], ("pass", "review"))


if __name__ == "__main__":
    unittest.main()
