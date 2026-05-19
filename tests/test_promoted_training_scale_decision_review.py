from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_decision_review import (  # noqa: E402
    append_decision_handoff_batch_recommendations,
    build_decision_handoff_review_summary,
)


class PromotedTrainingScaleDecisionReviewTests(unittest.TestCase):
    def test_builds_handoff_summary_from_selected_and_comparison_totals(self) -> None:
        summary = build_decision_handoff_review_summary(
            {
                "comparison_ready_handoff_selected_batch_blocker_count": 3,
                "comparison_ready_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
            },
            [
                {
                    "promoted_for_comparison": True,
                    "handoff_require_suite_consistency": True,
                    "handoff_suite_consistency": "consistent",
                    "handoff_suite_mismatch_count": 0,
                    "handoff_selected_batch_review_status": "blocker",
                    "handoff_selected_batch_comparison_blocker_action_count": 1,
                    "handoff_batch_comparison_blocker_action_count": 1,
                    "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
                }
            ],
            {
                "handoff_require_suite_consistency": True,
                "handoff_suite_consistency": "consistent",
                "handoff_suite_mismatch_count": 0,
                "handoff_selected_suite_path": "builtin:standard-zh",
                "handoff_selected_batch_review_status": "blocker",
                "handoff_selected_batch_comparison_blocker_action_count": 1,
                "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
            },
        )

        self.assertTrue(summary["selected_handoff_require_suite_consistency"])
        self.assertEqual(summary["selected_handoff_suite_consistency"], "consistent")
        self.assertEqual(summary["selected_handoff_selected_suite_path"], "builtin:standard-zh")
        self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
        self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
        self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 3)
        self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])

    def test_derives_batch_totals_when_comparison_summary_is_missing_them(self) -> None:
        summary = build_decision_handoff_review_summary(
            {},
            [
                {
                    "promoted_for_comparison": True,
                    "handoff_selected_batch_review_status": "review",
                    "handoff_selected_batch_comparison_review_action_count": 2,
                    "handoff_batch_comparison_review_action_count": 3,
                },
                {
                    "promoted_for_comparison": True,
                    "handoff_selected_batch_review_status": "blocker",
                    "handoff_selected_batch_comparison_blocker_action_count": 1,
                    "handoff_batch_comparison_blocker_action_count": 1,
                    "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
                },
            ],
            None,
        )

        self.assertEqual(summary["comparison_ready_handoff_selected_batch_review_count"], 1)
        self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
        self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_review_action_total"], 2)
        self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_blocker_action_total"], 1)
        self.assertEqual(summary["comparison_ready_handoff_batch_comparison_review_action_total"], 3)
        self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_action_total"], 1)
        self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])

    def test_recommendations_prefer_selected_status_then_other_blockers(self) -> None:
        recommendations: list[str] = []
        append_decision_handoff_batch_recommendations(
            recommendations,
            {"handoff_selected_batch_review_status": "blocker"},
            {"comparison_ready_handoff_selected_batch_blocker_count": 4},
        )
        self.assertTrue(any("selected handoff batch blocker actions" in item for item in recommendations))

        recommendations = []
        append_decision_handoff_batch_recommendations(
            recommendations,
            None,
            {"comparison_ready_handoff_selected_batch_blocker_count": 4},
        )
        self.assertTrue(any("Other comparison-ready promoted inputs" in item for item in recommendations))


if __name__ == "__main__":
    unittest.main()
