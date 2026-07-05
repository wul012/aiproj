from __future__ import annotations

import math
import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.similarity_v1195_stats import (  # noqa: E402
    _interp,
    _isotonic_decreasing,
    _ols2,
    spearman,
    spearman_perm_p,
)


class SimilarityV1195StatsTests(unittest.TestCase):
    def test_spearman_handles_ties_and_constant_axis(self) -> None:
        self.assertAlmostEqual(spearman([0.0, 1.0, 1.0, 2.0], [4.0, 3.0, 2.0, 1.0]), -0.948683, places=6)
        self.assertEqual(spearman([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]), 0.0)

    def test_spearman_perm_p_caps_large_exact_enumeration(self) -> None:
        self.assertLessEqual(
            spearman_perm_p([0.0, 0.3, 0.5, 0.8, 1.0], [0.9, 0.7, 0.5, 0.3, 0.1]),
            0.05,
        )
        self.assertTrue(math.isnan(spearman_perm_p(list(range(9)), list(reversed(range(9))))))

    def test_ols2_returns_nan_for_collinear_controls(self) -> None:
        b1, b2, r2 = _ols2([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [2.0, 4.0, 6.0])

        self.assertTrue(math.isnan(b1))
        self.assertTrue(math.isnan(b2))
        self.assertTrue(math.isnan(r2))

    def test_isotonic_decreasing_and_interp_clamp_endpoints(self) -> None:
        curve = _isotonic_decreasing([0.0, 1.0, 2.0, 3.0], [0.9, 0.6, 0.7, 0.2])

        self.assertEqual([x for x, _ in curve], [0.0, 1.0, 2.0, 3.0])
        self.assertGreaterEqual(curve[0][1], curve[1][1])
        self.assertGreaterEqual(curve[1][1], curve[2][1])
        self.assertGreaterEqual(curve[2][1], curve[3][1])
        self.assertEqual(_interp(curve, -1.0), curve[0][1])
        self.assertEqual(_interp(curve, 4.0), curve[-1][1])
        self.assertAlmostEqual(_interp([(0.0, 1.0), (2.0, 0.0)], 1.0), 0.5)


if __name__ == "__main__":
    unittest.main()
