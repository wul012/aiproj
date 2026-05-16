from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.registry_leaderboards import (  # noqa: E402
    benchmark_rubric_leaderboard_html,
    loss_leaderboard_html,
    pair_delta_leaderboard_html,
    release_readiness_delta_leaderboard_html,
)


class RegistryLeaderboardRenderTests(unittest.TestCase):
    def test_loss_and_rubric_leaderboards_escape_text(self) -> None:
        loss_html = loss_leaderboard_html(
            [
                {
                    "rank": 1,
                    "name": "<best>",
                    "best_val_loss": 0.12,
                    "best_val_loss_delta": 0.0,
                    "dataset_quality": "pass",
                    "eval_suite_cases": 4,
                }
            ]
        )
        rubric_html = benchmark_rubric_leaderboard_html(
            [
                {
                    "rank": 2,
                    "name": "<rubric>",
                    "benchmark_rubric_avg_score": 87.5,
                    "benchmark_rubric_delta_from_best": -1.5,
                    "benchmark_rubric_status": "warn",
                    "benchmark_weakest_rubric_case": "<weak>",
                    "benchmark_weakest_rubric_score": 66,
                }
            ]
        )

        self.assertIn("&lt;best&gt;", loss_html)
        self.assertIn("0.12", loss_html)
        self.assertIn("&lt;rubric&gt;", rubric_html)
        self.assertIn("&lt;weak&gt;", rubric_html)

    def test_delta_leaderboards_render_relative_report_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_dir = root / "registry"
            pair_report = root / "run-a" / "pair_batch" / "pair_generation_batch.html"
            readiness_report = root / "run-a" / "release-readiness-comparison" / "release_readiness_comparison.html"
            pair_report.parent.mkdir(parents=True)
            readiness_report.parent.mkdir(parents=True)
            pair_report.write_text("<html></html>", encoding="utf-8")
            readiness_report.write_text("<html></html>", encoding="utf-8")

            pair_html = pair_delta_leaderboard_html(
                [
                    {
                        "run_name": "run-a",
                        "case": "delta",
                        "abs_generated_char_delta": 7,
                        "generated_char_delta": -7,
                        "continuation_char_delta": -3,
                        "generated_equal": False,
                        "continuation_equal": False,
                        "task_type": "qa",
                        "difficulty": "medium",
                        "left_checkpoint_id": "base",
                        "right_checkpoint_id": "wide",
                        "suite_name": "suite",
                        "suite_version": "1",
                        "report_path": str(pair_report),
                    }
                ],
                base_dir,
            )
            readiness_html = release_readiness_delta_leaderboard_html(
                [
                    {
                        "run_name": "run-a",
                        "compared_release": "v63",
                        "delta_status": "regressed",
                        "status_delta": -3,
                        "baseline_status": "ready",
                        "compared_status": "blocked",
                        "changed_panel_count": 1,
                        "changed_panels": ["release_gate:pass->fail"],
                        "audit_score_delta": -12.5,
                        "missing_artifact_delta": 2,
                        "baseline_ci_workflow_status": "pass",
                        "compared_ci_workflow_status": "fail",
                        "ci_workflow_failed_check_delta": 2,
                        "explanation": "<needs review>",
                        "report_path": str(readiness_report),
                    }
                ],
                base_dir,
            )

            self.assertIn("../run-a/pair_batch/pair_generation_batch.html", pair_html)
            self.assertIn("base -> wide", pair_html)
            self.assertIn("../run-a/release-readiness-comparison/release_readiness_comparison.html", readiness_html)
            self.assertIn("&lt;needs review&gt;", readiness_html)

    def test_empty_leaderboards_have_stable_messages(self) -> None:
        self.assertIn("No comparable best validation loss values", loss_leaderboard_html([]))
        self.assertIn("No benchmark rubric scores", benchmark_rubric_leaderboard_html([]))
        self.assertIn("No pair batch case deltas", pair_delta_leaderboard_html([], None))
        self.assertIn("No release readiness comparison deltas", release_readiness_delta_leaderboard_html([], None))


if __name__ == "__main__":
    unittest.main()
