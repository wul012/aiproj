from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from tests.promoted_training_scale_comparison_fixtures import entry, make_index_tree  # noqa: E402

from minigpt.promoted_training_scale_comparison import build_promoted_training_scale_comparison  # noqa: E402
from minigpt.promoted_training_scale_comparison_csv_rows import (  # noqa: E402
    promoted_comparison_csv_fieldnames,
    promoted_comparison_csv_rows,
)


class PromotedTrainingScaleComparisonCsvRowsTests(unittest.TestCase):
    def test_csv_rows_format_handoff_regressions_and_baseline_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        include_handoff_suite_guard=True,
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="review",
                        batch_ci_regression_count=2,
                        batch_boundary_plan_regression_count=1,
                        batch_ci_regression_names=["beta-old-ci", "beta-missing-step"],
                        batch_ci_regression_reason_counts={
                            "missing-ci-step": 1,
                            "archived_path_portability_check_not_ready": 1,
                        },
                        selected_batch_ci_regression_count=1,
                        selected_batch_boundary_plan_regression_count=1,
                        selected_batch_ci_regression_reason_counts={
                            "archived_path_portability_check_not_ready": 1,
                        },
                    ),
                    entry(
                        "gamma",
                        "gamma",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            rows = {row["name"]: row for row in promoted_comparison_csv_rows(report)}

            self.assertEqual(promoted_comparison_csv_fieldnames()[0], "name")
            self.assertIn("handoff_batch_maturity_ci_regression_reason_counts", promoted_comparison_csv_fieldnames())
            self.assertEqual(set(rows), {"alpha", "beta", "gamma"})
            self.assertTrue(rows["alpha"]["is_baseline"])
            self.assertEqual(rows["alpha"]["baseline_name"], "alpha")
            self.assertEqual(rows["gamma"]["baseline_name"], "alpha")
            self.assertEqual(
                rows["beta"]["handoff_batch_maturity_ci_regression_reason_counts"],
                "archived_path_portability_check_not_ready:1, missing-ci-step:1",
            )
            self.assertEqual(
                rows["beta"]["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                "archived_path_portability_check_not_ready:1",
            )
            self.assertEqual(rows["beta"]["handoff_batch_maturity_ci_regression_names"], "beta-old-ci;beta-missing-step")
            self.assertIn("handoff batch CI regression count is 2", rows["beta"]["comparison_exclusion_reasons"])


if __name__ == "__main__":
    unittest.main()
