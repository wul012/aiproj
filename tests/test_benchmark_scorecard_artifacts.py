from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard import (  # noqa: E402
    render_benchmark_scorecard_html as server_render_benchmark_scorecard_html,
    render_benchmark_scorecard_markdown as server_render_benchmark_scorecard_markdown,
    write_benchmark_scorecard_outputs as server_write_benchmark_scorecard_outputs,
)
from minigpt.benchmark_scorecard_artifacts import (  # noqa: E402
    render_benchmark_scorecard_html,
    render_benchmark_scorecard_markdown,
    write_benchmark_scorecard_outputs,
)


def make_scorecard() -> dict:
    return {
        "schema_version": 3,
        "title": "<Benchmark>",
        "generated_at": "2026-05-15T00:00:00Z",
        "run_dir": "runs/demo",
        "registry_path": None,
        "summary": {
            "overall_status": "pass",
            "overall_score": 91.25,
            "eval_suite_cases": 2,
            "generation_quality_status": "pass",
            "generation_quality_total_flags": 3,
            "generation_quality_dominant_flag": "low_diversity",
            "generation_quality_worst_case": "qa-hard",
            "rubric_status": "pass",
            "rubric_avg_score": 88.5,
            "weakest_rubric_case": "qa-hard",
            "pair_batch_cases": 2,
            "pair_generated_differences": 1,
            "max_abs_generated_delta": 4,
            "pair_comparison_mode": "cross_checkpoint_or_unknown",
            "pair_same_checkpoint_baseline": False,
            "task_type_group_count": 1,
            "difficulty_group_count": 1,
            "weakest_task_type": "qa",
            "weakest_difficulty": "hard",
        },
        "components": [
            {
                "key": "eval_coverage",
                "title": "Eval Suite Coverage",
                "status": "pass",
                "score": 100.0,
                "weight": 0.15,
                "weighted_score": 15.0,
                "evidence_path": "eval_suite.json",
                "detail": "2 fixed prompt cases.",
            }
        ],
        "rubric_scores": {
            "cases": [
                {
                    "name": "qa-hard",
                    "task_type": "qa",
                    "difficulty": "hard",
                    "status": "warn",
                    "score": 72.5,
                    "missing_terms": ["not"],
                    "failed_checks": ["must_include"],
                }
            ]
        },
        "drilldowns": {
            "task_type": [{"group_by": "task_type", "key": "qa", "status": "pass", "score": 91.25, "case_count": 2}],
            "difficulty": [{"group_by": "difficulty", "key": "hard", "status": "warn", "score": 72.5, "case_count": 1}],
        },
        "case_scores": [
            {
                "name": "qa-hard",
                "task_type": "qa",
                "eval_char_count": 42,
                "generation_quality_status": "warn",
                "rubric_score": 72.5,
                "pair_generated_char_delta": -4,
                "pair_generated_equal": False,
            }
        ],
        "registry_context": {
            "available": True,
            "run_count": 1,
            "best_val_loss_rank": 1,
            "pair_report_counts": {"pair_batch": 1},
            "pair_delta_summary": {"max_abs_generated_char_delta": 4},
        },
        "recommendations": ["Review weakest rubric case."],
        "warnings": ["demo warning"],
    }


class BenchmarkScorecardArtifactTests(unittest.TestCase):
    def test_renderers_escape_html_and_include_sections(self) -> None:
        scorecard = make_scorecard()

        html = render_benchmark_scorecard_html(scorecard)
        markdown = render_benchmark_scorecard_markdown(scorecard)

        self.assertIn("&lt;Benchmark&gt;", html)
        self.assertNotIn("<h1><Benchmark>", html)
        self.assertIn("Benchmark Components", html)
        self.assertIn("low_diversity", html)
        self.assertIn("Rubric Scores", html)
        self.assertIn("Task Type Drilldown", html)
        self.assertIn("## Components", markdown)
        self.assertIn("Dominant generation flag", markdown)
        self.assertIn("Pair comparison mode", markdown)
        self.assertIn("## Rubric Scores", markdown)
        self.assertIn("## Difficulty Drilldown", markdown)

    def test_write_outputs_creates_expected_files_and_csv_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "scorecard"

            outputs = write_benchmark_scorecard_outputs(make_scorecard(), out_dir)

            self.assertEqual(set(outputs), {"json", "csv", "drilldowns_csv", "rubric_csv", "markdown", "html"})
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["schema_version"], 3)
            self.assertIn("key,title,status,score", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("group_by,key,status,score", Path(outputs["drilldowns_csv"]).read_text(encoding="utf-8"))
            self.assertIn("name,task_type,difficulty,status,score", Path(outputs["rubric_csv"]).read_text(encoding="utf-8"))
            self.assertIn("Review weakest rubric case.", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark Components", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_benchmark_scorecard_public_wrappers_delegate_to_artifacts(self) -> None:
        scorecard = make_scorecard()

        self.assertEqual(server_render_benchmark_scorecard_html(scorecard), render_benchmark_scorecard_html(scorecard))
        self.assertEqual(server_render_benchmark_scorecard_markdown(scorecard), render_benchmark_scorecard_markdown(scorecard))
        with tempfile.TemporaryDirectory() as tmp:
            direct = write_benchmark_scorecard_outputs(scorecard, Path(tmp) / "direct")
            wrapped = server_write_benchmark_scorecard_outputs(scorecard, Path(tmp) / "wrapped")

            self.assertEqual(Path(direct["markdown"]).read_text(encoding="utf-8"), Path(wrapped["markdown"]).read_text(encoding="utf-8"))
            self.assertEqual(Path(direct["html"]).read_text(encoding="utf-8"), Path(wrapped["html"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
