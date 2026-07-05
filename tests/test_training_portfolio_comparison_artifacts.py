from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt import training_portfolio_comparison
from minigpt import training_portfolio_comparison_artifacts


class TrainingPortfolioComparisonArtifactSplitTests(unittest.TestCase):
    def test_artifact_module_writes_outputs_from_comparison_report(self) -> None:
        report = {
            "schema_version": 1,
            "title": "Training portfolio <comparison>",
            "generated_at": "2026-05-15T00:00:00Z",
            "portfolio_count": 2,
            "baseline": {"name": "base"},
            "portfolios": [
                {
                    "name": "base",
                    "source_path": "runs/base/training_portfolio.json",
                    "status": "completed",
                    "run_name": "base-run",
                    "dataset": "base-zh@v1",
                    "available_artifact_count": 8,
                    "artifact_count": 8,
                    "artifact_coverage": 1.0,
                    "overall_score": 82,
                    "rubric_avg_score": 80,
                    "final_val_loss": 1.2,
                    "best_val_loss": 1.1,
                    "parameter_count": 123,
                    "train_token_count": 900,
                    "eval_case_count": 5,
                    "generation_quality_status": "pass",
                    "dataset_readiness_status": "ready",
                    "dataset_quality_status": "pass",
                    "dataset_warning_count": 0,
                    "maturity_portfolio_status": "ready",
                    "maturity_release_readiness_trend": "stable",
                    "maturity_release_readiness_test_coverage_regression_count": 0,
                    "maturity_release_readiness_test_coverage_status_changed_count": 0,
                    "maturity_release_readiness_max_test_coverage_percent_delta": 0,
                    "maturity_release_readiness_max_test_coverage_gap_delta": 0,
                    "completed_steps": 2,
                    "step_count": 2,
                    "core_artifacts": [{"key": "run_manifest", "path": "runs/base/run_manifest.json", "exists": True}],
                },
                {
                    "name": "candidate",
                    "source_path": "runs/candidate/training_portfolio.json",
                    "status": "completed",
                    "run_name": "candidate-run",
                    "dataset": "candidate-zh@v1",
                    "available_artifact_count": 7,
                    "artifact_count": 8,
                    "artifact_coverage": 0.875,
                    "overall_score": 88,
                    "rubric_avg_score": 84,
                    "final_val_loss": 0.9,
                    "best_val_loss": 0.88,
                    "parameter_count": 456,
                    "train_token_count": 1200,
                    "eval_case_count": 5,
                    "generation_quality_status": "pass",
                    "dataset_readiness_status": "review",
                    "dataset_quality_status": "warn",
                    "dataset_warning_count": 1,
                    "maturity_portfolio_status": "review",
                    "maturity_release_readiness_trend": "coverage-regressed",
                    "maturity_release_readiness_test_coverage_regression_count": 1,
                    "maturity_release_readiness_test_coverage_status_changed_count": 1,
                    "maturity_release_readiness_max_test_coverage_percent_delta": 7.5,
                    "maturity_release_readiness_max_test_coverage_gap_delta": 2,
                    "completed_steps": 2,
                    "step_count": 2,
                    "core_artifacts": [{"key": "run_manifest", "path": "runs/candidate/run_manifest.json", "exists": True}],
                },
            ],
            "baseline_deltas": [
                {"name": "base", "baseline_name": "base", "is_baseline": True, "artifact_coverage_delta": 0, "available_artifact_delta": 0, "overall_score_delta": 0, "rubric_avg_score_delta": 0, "final_val_loss_delta": 0, "final_val_loss_relation": "baseline", "dataset_warning_delta": 0, "maturity_release_readiness_trend_changed": False, "maturity_release_readiness_test_coverage_regression_delta": 0, "overall_relation": "baseline", "explanation": "Baseline portfolio."},
                {"name": "candidate", "baseline_name": "base", "is_baseline": False, "artifact_coverage_delta": -0.125, "available_artifact_delta": -1, "overall_score_delta": 6, "rubric_avg_score_delta": 4, "final_val_loss_delta": -0.3, "final_val_loss_relation": "improved", "dataset_warning_delta": 1, "maturity_release_readiness_trend_changed": True, "maturity_release_readiness_test_coverage_regression_delta": 1, "overall_relation": "improved", "explanation": "overall +6; final val loss -0.3; artifact coverage regressed; release-readiness coverage regressed"},
            ],
            "summary": {
                "completed_count": 2,
                "failed_count": 0,
                "planned_count": 0,
                "score_improvement_count": 1,
                "score_regression_count": 0,
                "artifact_regression_count": 1,
                "dataset_warning_count": 1,
                "maturity_review_count": 1,
                "maturity_review_names": ["candidate"],
                "maturity_coverage_regression_count": 1,
                "maturity_coverage_regression_names": ["candidate"],
                "best_score_maturity_status": "review",
                "best_score_maturity_release_readiness_trend": "coverage-regressed",
                "best_score_maturity_release_readiness_test_coverage_regression_count": 1,
                "review_action_count": 1,
                "blocker_action_count": 1,
            },
            "best_by_overall_score": {"name": "candidate"},
            "best_by_final_val_loss": {"name": "candidate"},
            "review_actions": [
                {
                    "id": "maturity-1",
                    "portfolio": "candidate",
                    "severity": "blocker",
                    "category": "maturity",
                    "reason": "best_score_maturity_review",
                    "action": "Review this best-scoring portfolio's maturity narrative before promoting it as a clean baseline.",
                    "evidence": {"maturity_portfolio_status": "review"},
                }
            ],
            "recommendations": ["Review artifact coverage regressions."],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = training_portfolio_comparison_artifacts.write_training_portfolio_comparison_outputs(report, tmp)
            markdown = training_portfolio_comparison_artifacts.render_training_portfolio_comparison_markdown(report)
            html = training_portfolio_comparison_artifacts.render_training_portfolio_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            self.assertIn("overall_score_delta", csv_text)
            self.assertIn("maturity_release_readiness_test_coverage_regression_count", csv_text)
            self.assertIn("Best score maturity", markdown)
            self.assertIn("Maturity review portfolios", markdown)
            self.assertIn("Maturity coverage regressions", markdown)
            self.assertIn("Best score release readiness trend", markdown)
            self.assertIn("## Review Actions", markdown)
            self.assertIn("best_score_maturity_review", markdown)
            self.assertIn("## Artifact Coverage", markdown)
            self.assertIn("Best score maturity", html)
            self.assertIn("Maturity reviews", html)
            self.assertIn("Coverage regressions", html)
            self.assertIn("Best score release trend", html)
            self.assertIn("Review Actions", html)
            self.assertIn("best_score_maturity_review", html)
            self.assertIn("Training portfolio &lt;comparison&gt;", html)
            self.assertNotIn("Training portfolio <comparison>", html)

    def test_comparison_module_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(
            training_portfolio_comparison.render_training_portfolio_comparison_html,
            training_portfolio_comparison_artifacts.render_training_portfolio_comparison_html,
        )
        self.assertIs(
            training_portfolio_comparison.render_training_portfolio_comparison_markdown,
            training_portfolio_comparison_artifacts.render_training_portfolio_comparison_markdown,
        )
        self.assertIs(
            training_portfolio_comparison.write_training_portfolio_comparison_outputs,
            training_portfolio_comparison_artifacts.write_training_portfolio_comparison_outputs,
        )
        self.assertIs(
            training_portfolio_comparison.write_training_portfolio_comparison_csv,
            training_portfolio_comparison_artifacts.write_training_portfolio_comparison_csv,
        )


if __name__ == "__main__":
    unittest.main()
