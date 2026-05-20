from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio_comparison_review import (
    build_training_portfolio_recommendations,
    build_training_portfolio_review_actions,
    has_maturity_ci_regression,
    has_maturity_coverage_regression,
    is_review_status,
)


class TrainingPortfolioComparisonReviewTests(unittest.TestCase):
    def test_review_status_and_coverage_predicate_are_tolerant(self) -> None:
        self.assertTrue(is_review_status("review"))
        self.assertTrue(is_review_status(" warn "))
        self.assertFalse(is_review_status("ready"))
        self.assertFalse(is_review_status(None))
        self.assertTrue(
            has_maturity_coverage_regression(
                {
                    "maturity_release_readiness_trend": "stable",
                    "maturity_release_readiness_test_coverage_regression_count": "2",
                }
            )
        )
        self.assertTrue(
            has_maturity_coverage_regression(
                {
                    "maturity_release_readiness_trend": "coverage-regressed",
                    "maturity_release_readiness_test_coverage_regression_count": "not-a-number",
                }
            )
        )
        self.assertFalse(
            has_maturity_coverage_regression(
                {
                    "maturity_release_readiness_trend": "stable",
                    "maturity_release_readiness_test_coverage_regression_count": "not-a-number",
                }
            )
        )
        self.assertTrue(
            has_maturity_ci_regression(
                {
                    "maturity_release_readiness_trend": "stable",
                    "maturity_release_readiness_ci_workflow_order_regression_count": "1",
                }
            )
        )
        self.assertTrue(
            has_maturity_ci_regression(
                {
                    "maturity_release_readiness_trend": "ci-regressed",
                    "maturity_release_readiness_ci_workflow_regression_count": "not-a-number",
                }
            )
        )
        self.assertFalse(
            has_maturity_ci_regression(
                {
                    "maturity_release_readiness_trend": "stable",
                    "maturity_release_readiness_ci_workflow_regression_count": "not-a-number",
                    "maturity_release_readiness_ci_workflow_order_regression_count": None,
                }
            )
        )

    def test_best_score_coverage_regression_becomes_blocker_action(self) -> None:
        summary = {
            "best_score_name": "candidate",
            "maturity_coverage_regression_count": 1,
            "best_score_maturity_release_readiness_trend": "coverage-regressed",
            "best_score_maturity_release_readiness_test_coverage_regression_count": 1,
        }
        portfolios = [
            {
                "name": "candidate",
                "status": "completed",
                "core_artifacts": [],
                "dataset_warning_count": 0,
                "dataset_readiness_status": "ready",
                "dataset_quality_status": "pass",
                "maturity_portfolio_status": "ready",
                "maturity_release_readiness_trend": "coverage-regressed",
                "maturity_release_readiness_test_coverage_regression_count": 1,
                "maturity_release_readiness_test_coverage_status_changed_count": 1,
                "maturity_release_readiness_max_test_coverage_percent_delta": 7.5,
                "maturity_release_readiness_max_test_coverage_gap_delta": 3,
            }
        ]
        deltas = [
            {
                "name": "candidate",
                "overall_relation": "improved",
                "final_val_loss_relation": "improved",
                "artifact_coverage_delta": 0,
            }
        ]

        actions = build_training_portfolio_review_actions(summary, portfolios, deltas)
        recommendations = build_training_portfolio_recommendations(summary, deltas)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["reason"], "best_score_coverage_regressed")
        self.assertEqual(actions[0]["severity"], "blocker")
        self.assertEqual(actions[0]["evidence"]["coverage_regression_count"], 1)
        self.assertIn("Block best-score promotion", " ".join(recommendations))

    def test_best_score_ci_regression_becomes_blocker_action(self) -> None:
        summary = {
            "best_score_name": "candidate",
            "maturity_ci_regression_count": 1,
            "best_score_maturity_release_readiness_trend": "ci-regressed",
            "best_score_maturity_release_readiness_ci_workflow_order_regression_count": 1,
        }
        portfolios = [
            {
                "name": "candidate",
                "status": "completed",
                "core_artifacts": [],
                "dataset_warning_count": 0,
                "dataset_readiness_status": "ready",
                "dataset_quality_status": "pass",
                "maturity_portfolio_status": "ready",
                "maturity_release_readiness_trend": "ci-regressed",
                "maturity_release_readiness_ci_workflow_regression_count": 0,
                "maturity_release_readiness_ci_workflow_order_regression_count": 1,
                "maturity_release_readiness_ci_workflow_status_changed_count": 1,
                "maturity_release_readiness_max_ci_workflow_failed_check_delta": 0,
                "maturity_release_readiness_max_ci_workflow_order_violation_delta": 1,
            }
        ]
        deltas = [
            {
                "name": "candidate",
                "overall_relation": "improved",
                "final_val_loss_relation": "improved",
                "artifact_coverage_delta": 0,
            }
        ]

        actions = build_training_portfolio_review_actions(summary, portfolios, deltas)
        recommendations = build_training_portfolio_recommendations(summary, deltas)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["reason"], "best_score_ci_regressed")
        self.assertEqual(actions[0]["severity"], "blocker")
        self.assertEqual(actions[0]["evidence"]["ci_workflow_order_regression_count"], 1)
        self.assertIn("CI workflow regressions", " ".join(recommendations))


if __name__ == "__main__":
    unittest.main()
