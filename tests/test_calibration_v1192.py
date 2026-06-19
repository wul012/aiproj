"""Tests for v1192 calibration-under-uncertainty + temperature scaling.

CPU-fast, no training: the metrics are pure functions of (P_true, logits), so the oracle
(z = log P_true) has analytic ECE/KL exactly 0, and a sharpened oracle is a known-T
overconfident model. A small SYNTHETIC cache exercises run_analysis/decide end to end.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from minigpt.calibration_v1192 import (  # noqa: E402
    BIN_SCHEMES, CalibrationConfig, analytic_ece, beats_lower, brier, build_report,
    confidence_spread, decide, entropy_floor, expected_nll, fit_temperature, kl_to_true,
    oracle_logits, paired_beats, pmodel, reliability_curve, run_analysis, sampled_ece,
)


def make_P(K=16, M=5, alpha=0.5, seed=0):
    rng = np.random.default_rng(seed)
    return np.stack([rng.dirichlet([alpha] * M) for _ in range(K)])


def make_cache(*, hard_scale=2.0, K=16, M=5, seed=0, main_alpha=0.5):
    """Synthetic cache: arms are sharpened oracles (z = log P_true * scale). A scale>1 is
    overconfident with known optimal T==scale; scale==1 is perfectly calibrated."""
    P = make_P(K, M, main_alpha, seed)
    lp = oracle_logits(P)
    seeds = (1337, 1338, 1339)
    sweep_scales = {3: 3.0, 10: hard_scale, 30: 1.5, 100: 1.2, 300: 1.05}
    arms = {
        "hard_ce": {s: (lp * hard_scale).astype(np.float32) for s in seeds},
        "soft_distill": {s: lp.astype(np.float32) for s in seeds},
        "label_smooth": {s: (lp * 1.3).astype(np.float32) for s in seeds},
        "random_init": {s: np.zeros_like(lp, dtype=np.float32) for s in seeds},
    }
    sweep = {n: {s: (lp * sc).astype(np.float32) for s in seeds} for n, sc in sweep_scales.items()}
    bP = make_P(K, M, 0.05, seed + 7)            # peaky -> low entropy boundary
    blp = oracle_logits(bP)
    boundary = {s: blp.astype(np.float32) for s in seeds}
    H = -(P * np.log(P + 1e-12)).sum(1)
    bH = -(bP * np.log(bP + 1e-12)).sum(1)
    return {
        "p_true": P, "H": H, "arms": arms, "sweep": sweep,
        "boundary": boundary, "boundary_p_true": bP, "boundary_H": bH,
        "teacher_kl": 0.01, "uniform_kl_floor": float(np.log(M) - H.mean()), "headline_n": 10,
        "meta": {"seeds": list(seeds)},
    }


class MetricPrimitives(unittest.TestCase):
    def setUp(self):
        self.P = make_P()
        self.zo = oracle_logits(self.P)

    def test_oracle_analytic_ece_is_exactly_zero(self):
        for scheme in BIN_SCHEMES:
            self.assertAlmostEqual(analytic_ece(self.P, self.zo, 1.0, scheme)[0], 0.0, places=9)

    def test_oracle_kl_and_nll_floor(self):
        self.assertAlmostEqual(kl_to_true(self.P, self.zo, 1.0), 0.0, places=9)
        self.assertAlmostEqual(expected_nll(self.P, self.zo, 1.0), entropy_floor(self.P), places=9)

    def test_sampled_ece_has_positive_jensen_floor(self):
        # the oracle's plug-in sampled ECE is >0 even though its analytic ECE is 0
        self.assertGreater(sampled_ece(self.P, self.zo, 1.0, n_eval=2000, seed=1), 0.0)

    def test_pmodel_normalized_and_temperature_flattens(self):
        P1 = pmodel(self.zo, 1.0); P5 = pmodel(self.zo, 5.0)
        np.testing.assert_allclose(P1.sum(1), 1.0, atol=1e-9)
        self.assertLess(P5.max(1).mean(), P1.max(1).mean())   # higher T -> lower confidence

    def test_fit_temperature_recovers_sharpening(self):
        T, nT, n1, interior = fit_temperature(self.P, self.zo * 3.0)
        self.assertAlmostEqual(T, 3.0, delta=0.15)            # T should undo the 3x sharpen
        self.assertTrue(interior)
        self.assertLess(nT, n1)

    def test_brier_floor_and_ordering(self):
        floor = brier(self.P, self.zo, 1.0)
        over = brier(self.P, self.zo * 4.0, 1.0)
        self.assertGreater(over, floor)

    def test_reliability_curve_points(self):
        self.assertGreater(len(reliability_curve(self.P, self.zo * 3.0, 1.0)), 0)


class SignificancePrimitives(unittest.TestCase):
    def test_beats_lower(self):
        self.assertTrue(beats_lower(0.1, 0.01, 0.5, 0.01))    # 0.1 significantly below 0.5
        self.assertFalse(beats_lower(0.49, 0.05, 0.5, 0.05))  # overlapping

    def test_paired_beats(self):
        self.assertTrue(paired_beats([0.05, 0.06, 0.055]))    # consistent positive deltas
        self.assertFalse(paired_beats([0.05, -0.06, 0.2]))    # noisy, std swamps mean


class AnalysisAndDecide(unittest.TestCase):
    def test_overconfidence_specifically_corrected(self):
        result = run_analysis(make_cache(hard_scale=2.0))
        info = decide(result)
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "overconfidence_specifically_corrected_by_temperature")
        f = info["flags"]
        self.assertTrue(f["direction_overconfident"])
        self.assertTrue(f["T_significantly_gt_1"])
        self.assertTrue(f["correction_paired_significant"])
        self.assertTrue(f["u_shaped"] and f["wrong_T_worse"] and f["t_not_helping_calibrated"])
        self.assertTrue(f["not_magic_T_to_one"])             # T decreases across the sweep

    def test_calibrated_headline_routes_to_null(self):
        # hard_ce scale 1.0 == perfectly calibrated -> not overconfident
        info = decide(run_analysis(make_cache(hard_scale=1.0)))
        self.assertEqual(info["status"], "pass")
        self.assertEqual(info["verdict"], "already_calibrated_no_overconfidence")

    def test_g0_task_not_learned_routes_to_review(self):
        cache = make_cache(hard_scale=2.0)
        cache["uniform_kl_floor"] = 0.0                       # nothing can beat a 0 floor
        info = decide(run_analysis(cache))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "task_not_learned")

    def test_g1_no_entropy_structure_routes_to_review(self):
        # a peaky (low-entropy) main task (consistent arms) fails the aleatoric-uncertainty gate
        info = decide(run_analysis(make_cache(hard_scale=2.0, main_alpha=0.03)))
        self.assertEqual(info["status"], "review")
        self.assertEqual(info["verdict"], "no_entropy_structure")

    def test_boundary_is_null(self):
        result = run_analysis(make_cache(hard_scale=2.0))
        self.assertFalse(result["boundary_overconfident"])

    def test_co_movement_reported_not_dissociation(self):
        # sharpened oracle: T fully recovers P, so ECE and KL both collapse together
        result = run_analysis(make_cache(hard_scale=2.0))
        self.assertTrue(result["comovement"]["co_move"])


class ReportShape(unittest.TestCase):
    def test_build_report_shape(self):
        result = run_analysis(make_cache(hard_scale=2.0))
        info = decide(result)
        report = build_report(result, info, "synthetic")
        self.assertEqual(report["status"], "pass")
        self.assertIn("summary", report)
        self.assertTrue(report["rows"])
        self.assertEqual(report["rows"][0]["arm"], "hard_ce")
        for field in report["csv_fieldnames"]:
            self.assertIn(field, report["rows"][0])
        self.assertGreaterEqual(len(report["recommendations"]), 5)
        self.assertIn("fig_ece_vs_T", report)
        self.assertEqual(report["summary"]["headline_n"], 10)

    def test_confidence_spread_nonzero(self):
        self.assertGreater(confidence_spread(oracle_logits(make_P()) * 2.0), 0.0)


if __name__ == "__main__":
    unittest.main()
