from __future__ import annotations

import unittest

from minigpt.training_scale_handoff_guards import build_clean_batch_review_guard, build_suite_guard


class TrainingScaleHandoffGuardTests(unittest.TestCase):
    def test_suite_guard_honors_explicit_decision_false_and_decision_values(self) -> None:
        workflow = {
            "summary": {
                "decision_require_suite_consistency": True,
                "suite_consistency": "workflow-value",
                "suite_mismatch_count": 3,
                "suite_path": "workflow-suite.json",
            }
        }
        decision = {
            "summary": {
                "require_suite_consistency": False,
                "suite_consistency": "consistent",
                "suite_mismatch_count": 0,
                "selected_suite_path": "selected-suite.json",
            }
        }

        guard = build_suite_guard(workflow, decision)

        self.assertFalse(guard["require_suite_consistency"])
        self.assertEqual(guard["suite_consistency"], "consistent")
        self.assertEqual(guard["suite_mismatch_count"], 0)
        self.assertEqual(guard["selected_suite_path"], "selected-suite.json")
        self.assertEqual(guard["workflow_suite_path"], "workflow-suite.json")

    def test_suite_guard_falls_back_to_workflow_requirement_and_values(self) -> None:
        workflow = {
            "summary": {
                "decision_require_suite_consistency": True,
                "suite_consistency": "review",
                "suite_mismatch_count": 2,
                "suite_name": "standard-zh",
            }
        }

        guard = build_suite_guard(workflow, {"summary": {}})

        self.assertTrue(guard["decision_require_suite_consistency"])
        self.assertEqual(guard["suite_consistency"], "review")
        self.assertEqual(guard["suite_mismatch_count"], 2)
        self.assertEqual(guard["workflow_suite_name"], "standard-zh")

    def test_clean_guard_normalizes_names_and_positive_reason_counts(self) -> None:
        decision = {
            "summary": {
                "require_clean_batch_review": True,
                "selected_batch_review_status": "clean",
                "selected_batch_maturity_suite_design_regression_names": ["suite-a", 2],
                "selected_batch_maturity_ci_regression_reason_counts": {
                    " failed ": "2",
                    "zero": 0,
                    "bad": "x",
                },
            }
        }

        guard = build_clean_batch_review_guard({}, decision)

        self.assertTrue(guard["require_clean_batch_review"])
        self.assertEqual(guard["clean_batch_review_status"], "clean")
        self.assertEqual(guard["selected_batch_maturity_suite_design_regression_names"], ["suite-a", "2"])
        self.assertEqual(guard["selected_batch_maturity_ci_regression_reason_counts"], {"failed": 2})

    def test_clean_guard_uses_workflow_fallbacks_without_overriding_false(self) -> None:
        workflow = {
            "require_clean_batch_review": True,
            "summary": {
                "decision_require_clean_batch_review": True,
                "clean_batch_review_status": "review",
                "batch_maturity_ci_regression_count": 1,
                "batch_comparison_blocker_reasons": ["ci-regression"],
            },
        }
        decision = {"summary": {"require_clean_batch_review": False}}

        guard = build_clean_batch_review_guard(workflow, decision)

        self.assertFalse(guard["require_clean_batch_review"])
        self.assertEqual(guard["clean_batch_review_status"], "review")
        self.assertEqual(guard["batch_maturity_ci_regression_count"], 1)
        self.assertEqual(guard["batch_comparison_blocker_reasons"], ["ci-regression"])


if __name__ == "__main__":
    unittest.main()
