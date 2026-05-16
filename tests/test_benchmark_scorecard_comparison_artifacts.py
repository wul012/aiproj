from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import benchmark_scorecard_comparison
from minigpt import benchmark_scorecard_comparison_artifacts


class BenchmarkScorecardComparisonArtifactSplitTests(unittest.TestCase):
    def test_artifact_module_writes_outputs_from_comparison_report(self) -> None:
        report = {
            "schema_version": 1,
            "title": "Demo <comparison>",
            "generated_at": "2026-05-15T00:00:00Z",
            "scorecard_count": 2,
            "baseline": {"name": "base"},
            "runs": [
                {"name": "base", "run_dir": "runs/base", "overall_score": 80, "rubric_avg_score": 70, "case_count": 1, "weakest_rubric_case": "qa", "weakest_rubric_score": 70, "rubric_pass_count": 0, "rubric_warn_count": 1, "rubric_fail_count": 0, "generation_quality_total_flags": 3, "generation_quality_dominant_flag": "low_diversity", "generation_quality_worst_case": "qa"},
                {"name": "candidate", "run_dir": "runs/candidate", "overall_score": 86, "rubric_avg_score": 82, "case_count": 1, "weakest_rubric_case": "qa", "weakest_rubric_score": 82, "rubric_pass_count": 1, "rubric_warn_count": 0, "rubric_fail_count": 0, "generation_quality_total_flags": 1, "generation_quality_dominant_flag": "low_diversity", "generation_quality_worst_case": "qa"},
            ],
            "baseline_deltas": [
                {"name": "base", "baseline_name": "base", "is_baseline": True, "overall_score_delta": 0, "rubric_avg_score_delta": 0, "generation_quality_total_flags_delta": 0, "generation_quality_flag_relation": "baseline", "rubric_relation": "baseline", "overall_relation": "baseline", "explanation": "baseline"},
                {"name": "candidate", "baseline_name": "base", "is_baseline": False, "overall_score_delta": 6, "rubric_avg_score_delta": 12, "generation_quality_total_flags_delta": -2, "generation_quality_flag_relation": "improved", "rubric_relation": "improved", "overall_relation": "improved", "explanation": "improved"},
            ],
            "case_deltas": [
                {"case": "qa", "run_name": "candidate", "baseline_name": "base", "task_type": "qa", "difficulty": "hard", "rubric_score_delta": 12, "relation": "improved", "added_missing_terms": [], "removed_missing_terms": ["事实"], "added_failed_checks": [], "removed_failed_checks": [], "explanation": "case improved"}
            ],
            "task_type_deltas": [
                {"key": "qa", "group_by": "task_type", "run_name": "candidate", "score": 82, "score_delta": 12, "rubric_score": 82, "rubric_score_delta": 12, "case_count": 1, "relation": "improved", "explanation": "qa improved"}
            ],
            "difficulty_deltas": [],
            "summary": {"improved_overall_count": 1, "regressed_overall_count": 0, "improved_rubric_count": 1, "regressed_rubric_count": 0, "generation_quality_flag_improvement_count": 1, "generation_quality_flag_regression_count": 0, "baseline_generation_quality_dominant_flag": "low_diversity", "case_regression_count": 0, "case_improvement_count": 1, "weakest_case_regression": None},
            "best_by_overall_score": {"name": "candidate"},
            "best_by_rubric_avg_score": {"name": "candidate"},
            "recommendations": ["Inspect case deltas."],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = benchmark_scorecard_comparison_artifacts.write_benchmark_scorecard_comparison_outputs(report, tmp)
            markdown = benchmark_scorecard_comparison_artifacts.render_benchmark_scorecard_comparison_markdown(report)
            html = benchmark_scorecard_comparison_artifacts.render_benchmark_scorecard_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "case_delta_csv", "markdown", "html"})
            self.assertIn("rubric_avg_score_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("generation_quality_flag_relation", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("removed_missing_terms", Path(outputs["case_delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Case Deltas", markdown)
            self.assertIn("Generation flag improvements", markdown)
            self.assertIn("Gen Flags", html)
            self.assertIn("Demo &lt;comparison&gt;", html)
            self.assertNotIn("Demo <comparison>", html)

    def test_comparison_module_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(
            benchmark_scorecard_comparison.render_benchmark_scorecard_comparison_html,
            benchmark_scorecard_comparison_artifacts.render_benchmark_scorecard_comparison_html,
        )
        self.assertIs(
            benchmark_scorecard_comparison.render_benchmark_scorecard_comparison_markdown,
            benchmark_scorecard_comparison_artifacts.render_benchmark_scorecard_comparison_markdown,
        )
        self.assertIs(
            benchmark_scorecard_comparison.write_benchmark_scorecard_comparison_outputs,
            benchmark_scorecard_comparison_artifacts.write_benchmark_scorecard_comparison_outputs,
        )
        self.assertIs(
            benchmark_scorecard_comparison.write_benchmark_scorecard_case_delta_csv,
            benchmark_scorecard_comparison_artifacts.write_benchmark_scorecard_case_delta_csv,
        )


if __name__ == "__main__":
    unittest.main()
