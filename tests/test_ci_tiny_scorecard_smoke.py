from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_ci_tiny_scorecard_comparison_smoke import (  # noqa: E402
    CI_TINY_SCORECARD_CONFIG,
    build_ci_smoke_command,
    parse_args,
)


class CITinyScorecardSmokeTests(unittest.TestCase):
    def test_build_ci_smoke_command_preserves_fixed_budget_and_summary_check_contract(self) -> None:
        args = parse_args(
            [
                "--out-dir",
                "runs/ci-smoke",
                "--summary-check-out-dir",
                "runs/ci-smoke-check",
                "--force",
            ]
        )

        command = build_ci_smoke_command(args)
        command_text = " ".join(command).replace("\\", "/")

        self.assertEqual(CI_TINY_SCORECARD_CONFIG["suite_name"], "standard-zh")
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["baseline_max_iters"], 1)
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["candidate_max_iters"], 2)
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["decision_min_rubric_score"], 60.0)
        self.assertIn("scripts/run_tiny_scorecard_comparison_smoke.py", command_text)
        self.assertIn("--suite-name standard-zh", command_text)
        self.assertIn("--case-token-cap 3", command_text)
        self.assertIn("--baseline-max-iters 1", command_text)
        self.assertIn("--candidate-max-iters 2", command_text)
        self.assertIn("--decision-min-rubric-score 60.0", command_text)
        self.assertIn("--summary-check-out-dir runs/ci-smoke-check", command_text)
        self.assertTrue(command_text.endswith("--force"))

    def test_build_ci_smoke_command_preserves_optional_summary_check_flags(self) -> None:
        args = parse_args(
            [
                "--summary-check-allow-gate-stop",
                "--summary-check-no-fail",
            ]
        )

        command_text = " ".join(build_ci_smoke_command(args))

        self.assertIn("--summary-check-allow-gate-stop", command_text)
        self.assertIn("--summary-check-no-fail", command_text)


if __name__ == "__main__":
    unittest.main()
