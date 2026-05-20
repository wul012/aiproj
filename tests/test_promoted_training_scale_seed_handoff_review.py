from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff_review import (  # noqa: E402
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_review_recommendations,
    build_seed_handoff_suite_alignment,
)


class PromotedTrainingScaleSeedHandoffReviewTests(unittest.TestCase):
    def test_builds_batch_review_summary_with_string_reason_lists(self) -> None:
        summary = build_seed_handoff_batch_review_summary(
            {
                "handoff_batch_review": {
                    "selected_handoff_selected_batch_review_status": "blocker",
                    "selected_handoff_selected_batch_comparison_review_action_count": 2,
                    "selected_handoff_selected_batch_comparison_blocker_action_count": 1,
                    "selected_handoff_batch_comparison_blocker_reasons": ["coverage-regressed", 7],
                    "comparison_ready_handoff_selected_batch_blocker_count": 1,
                    "comparison_ready_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
                }
            }
        )

        self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
        self.assertEqual(summary["selected_handoff_selected_batch_comparison_review_action_count"], 2)
        self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
        self.assertEqual(summary["selected_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed", "7"])
        self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
        self.assertEqual(
            summary["comparison_ready_handoff_batch_comparison_blocker_reasons"],
            ["coverage-regressed"],
        )

    def test_builds_clean_batch_review_summary_with_ci_regression_context(self) -> None:
        from minigpt.promoted_training_scale_seed_handoff_review import (
            build_seed_handoff_clean_batch_review_summary,
        )

        summary = build_seed_handoff_clean_batch_review_summary(
            {
                "handoff_clean_batch_review": {
                    "selected_handoff_require_clean_batch_review": True,
                    "selected_handoff_clean_batch_review_status": "clean",
                    "selected_handoff_batch_maturity_ci_regression_count": 1,
                    "selected_handoff_batch_maturity_ci_regression_names": ["dirty-selected", 7],
                    "selected_handoff_selected_batch_maturity_ci_regression_count": 1,
                    "selected_comparison_exclusion_reasons": ["selected stale"],
                    "handoff_batch_maturity_ci_regression_count": 2,
                    "handoff_selected_batch_maturity_ci_regression_total": 1,
                    "handoff_batch_maturity_ci_regression_names": ["dirty-old"],
                    "comparison_exclusion_reasons": ["handoff batch CI regression count is 2"],
                    "comparison_ready_handoff_batch_maturity_ci_regression_count": 0,
                    "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": 0,
                    "comparison_ready_handoff_batch_maturity_ci_regression_names": [],
                }
            }
        )

        self.assertEqual(summary["selected_handoff_batch_maturity_ci_regression_count"], 1)
        self.assertEqual(summary["selected_handoff_batch_maturity_ci_regression_names"], ["dirty-selected", "7"])
        self.assertEqual(summary["selected_handoff_selected_batch_maturity_ci_regression_count"], 1)
        self.assertEqual(summary["selected_comparison_exclusion_reasons"], ["selected stale"])
        self.assertEqual(summary["handoff_batch_maturity_ci_regression_count"], 2)
        self.assertEqual(summary["handoff_selected_batch_maturity_ci_regression_total"], 1)
        self.assertEqual(summary["handoff_batch_maturity_ci_regression_names"], ["dirty-old"])
        self.assertEqual(summary["comparison_exclusion_reasons"], ["handoff batch CI regression count is 2"])
        self.assertEqual(summary["comparison_ready_handoff_batch_maturity_ci_regression_count"], 0)

    def test_builds_suite_alignment_without_requiring_generated_plan(self) -> None:
        alignment = build_seed_handoff_suite_alignment("suites/standard-zh.json", "suites/standard-zh.json", None)

        self.assertEqual(alignment["status"], "pending-plan")
        self.assertEqual(alignment["mismatch_count"], 0)
        self.assertEqual(alignment["missing_count"], 0)
        self.assertIn("plan suite is not available yet", alignment["detail"])

    def test_combines_review_recommendations_without_changing_handoff_status(self) -> None:
        recommendations = build_seed_handoff_review_recommendations(
            {
                "seed_handoff_suite_alignment_status": "pending-plan",
                "seed_handoff_suite_alignment_detail": "plan suite is not available yet",
                "selected_handoff_selected_batch_review_status": "blocker",
                "comparison_ready_handoff_selected_batch_blocker_count": 1,
            },
            {
                "required": True,
                "status": "fail",
                "ready": False,
                "readiness_status": "pending-plan",
                "detail": "execute the seed handoff before treating clean comparison evidence as ready",
                "status_domain": ["not-required", "pass", "fail"],
            },
        )

        self.assertTrue(any("pending plan generation" in item for item in recommendations))
        self.assertTrue(any("Clean-evidence requirement failed" in item for item in recommendations))
        self.assertTrue(any("selected handoff batch blocker actions" in item for item in recommendations))


if __name__ == "__main__":
    unittest.main()
