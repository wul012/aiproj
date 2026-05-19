from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_review import (  # noqa: E402
    append_seed_handoff_batch_review_recommendation,
    build_seed_handoff_batch_review,
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_suite_guard,
)


class PromotedTrainingScaleSeedReviewTests(unittest.TestCase):
    def test_builds_handoff_batch_review_from_summary_with_selected_fallbacks(self) -> None:
        review = build_seed_handoff_batch_review(
            {
                "summary": {
                    "selected_handoff_selected_batch_review_status": "blocker",
                    "selected_handoff_selected_batch_comparison_review_action_count": 2,
                    "selected_handoff_selected_batch_comparison_blocker_action_count": 1,
                    "selected_handoff_batch_comparison_blocker_reasons": ["coverage-regressed", 7],
                    "comparison_ready_handoff_selected_batch_blocker_count": 1,
                    "comparison_ready_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
                }
            },
            {
                "handoff_selected_batch_review_status": "review",
                "handoff_selected_batch_comparison_review_action_count": 1,
            },
        )

        self.assertEqual(review["selected_handoff_selected_batch_review_status"], "blocker")
        self.assertEqual(review["selected_handoff_selected_batch_comparison_review_action_count"], 2)
        self.assertEqual(review["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
        self.assertEqual(review["selected_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed", "7"])
        self.assertEqual(review["comparison_ready_handoff_selected_batch_blocker_count"], 1)

    def test_builds_handoff_suite_guard_from_summary_or_selected(self) -> None:
        guard = build_seed_handoff_suite_guard(
            {
                "summary": {
                    "selected_handoff_suite_consistency": None,
                    "handoff_suite_consistent_count": 2,
                    "handoff_suite_mismatch_total": 0,
                }
            },
            {
                "handoff_require_suite_consistency": True,
                "handoff_suite_consistency": "consistent",
                "handoff_suite_mismatch_count": 0,
                "handoff_selected_suite_path": "builtin:standard-zh",
            },
        )

        self.assertTrue(guard["selected_handoff_require_suite_consistency"])
        self.assertEqual(guard["selected_handoff_suite_consistency"], "consistent")
        self.assertEqual(guard["selected_handoff_selected_suite_path"], "builtin:standard-zh")
        self.assertEqual(guard["handoff_suite_consistent_count"], 2)

    def test_batch_review_summary_and_recommendation_share_same_seed_shape(self) -> None:
        seed = {
            "handoff_batch_review": {
                "selected_handoff_selected_batch_review_status": "blocker",
                "selected_handoff_selected_batch_comparison_blocker_action_count": 1,
                "comparison_ready_handoff_selected_batch_blocker_count": 1,
            }
        }
        summary = build_seed_handoff_batch_review_summary(seed)
        recommendations: list[str] = []
        append_seed_handoff_batch_review_recommendation(recommendations, seed)

        self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
        self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
        self.assertTrue(any("selected handoff batch blocker actions" in item for item in recommendations))


if __name__ == "__main__":
    unittest.main()
