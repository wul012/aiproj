from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard import (
    build_benchmark_scorecard,
    render_benchmark_scorecard_html,
    write_benchmark_scorecard_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_run(root: Path) -> tuple[Path, Path]:
    run_dir = root / "runs" / "demo-run"
    cases = [
        ("qa-basic", "qa", "easy", 18, "pass", 0),
        ("summary-short", "summary", "medium", 24, "pass", 0),
        ("format-json", "format", "medium", 21, "pass", 0),
        ("continue-story", "continuation", "easy", 19, "pass", 0),
        ("fact-check", "qa", "hard", 17, "warn", 2),
    ]
    write_json(
        run_dir / "eval_suite" / "eval_suite.json",
        {
            "schema_version": 1,
            "case_count": len(cases),
            "task_type_counts": {"qa": 2, "summary": 1, "format": 1, "continuation": 1},
            "difficulty_counts": {"easy": 2, "medium": 2, "hard": 1},
            "results": [
                {
                    "name": name,
                    "task_type": task_type,
                    "difficulty": difficulty,
                    "char_count": char_count,
                    "unique_char_count": max(8, char_count - 3),
                }
                for name, task_type, difficulty, char_count, _status, _delta in cases
            ],
        },
    )
    write_json(
        run_dir / "generation-quality" / "generation_quality.json",
        {
            "schema_version": 1,
            "summary": {
                "overall_status": "pass",
                "case_count": len(cases),
                "pass_count": 4,
                "warn_count": 1,
                "fail_count": 0,
            },
            "cases": [
                {"name": name, "status": status, "unique_ratio": 0.72, "flag_count": 1 if status == "warn" else 0}
                for name, _task_type, _difficulty, _char_count, status, _delta in cases
            ],
        },
    )
    write_json(
        run_dir / "pair_batch" / "pair_generation_batch.json",
        {
            "kind": "minigpt_pair_generation_batch",
            "case_count": len(cases),
            "generated_equal_count": 4,
            "generated_difference_count": 1,
            "avg_abs_generated_char_delta": 0.4,
            "results": [
                {
                    "name": name,
                    "task_type": task_type,
                    "difficulty": difficulty,
                    "comparison": {
                        "generated_equal": delta == 0,
                        "continuation_equal": delta == 0,
                        "generated_char_delta": delta,
                        "continuation_char_delta": delta,
                    },
                }
                for name, task_type, difficulty, _char_count, _status, delta in cases
            ],
        },
    )
    (run_dir / "pair_batch" / "pair_generation_batch.html").write_text("<h1>Pair</h1>", encoding="utf-8")
    registry_path = root / "registry.json"
    write_json(
        registry_path,
        {
            "run_count": 1,
            "runs": [{"path": str(run_dir), "best_val_loss_rank": 1}],
            "pair_report_counts": {"pair_batch": 1, "pair_trend": 0},
            "pair_delta_summary": {"case_count": len(cases), "max_abs_generated_char_delta": 2},
        },
    )
    return run_dir, registry_path


class BenchmarkScorecardTests(unittest.TestCase):
    def test_build_benchmark_scorecard_consolidates_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, registry_path = make_run(Path(tmp))

            scorecard = build_benchmark_scorecard(
                run_dir,
                registry_path=registry_path,
                generated_at="2026-05-13T00:00:00Z",
            )

            self.assertEqual(scorecard["summary"]["overall_status"], "pass")
            self.assertGreaterEqual(scorecard["summary"]["overall_score"], 80)
            self.assertEqual(scorecard["summary"]["component_count"], 5)
            self.assertEqual({item["key"] for item in scorecard["components"]}, {
                "eval_coverage",
                "generation_quality",
                "pair_consistency",
                "pair_delta_stability",
                "evidence_completeness",
            })
            self.assertEqual(len(scorecard["case_scores"]), 5)
            self.assertEqual(scorecard["registry_context"]["best_val_loss_rank"], 1)
            self.assertEqual(scorecard["registry_context"]["pair_delta_cases"], 5)
            self.assertEqual(scorecard["warnings"], [])

    def test_write_benchmark_scorecard_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir, registry_path = make_run(root)
            scorecard = build_benchmark_scorecard(run_dir, registry_path=registry_path)

            outputs = write_benchmark_scorecard_outputs(scorecard, root / "scorecard")

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("benchmark_scorecard", Path(outputs["json"]).name)
            self.assertIn("key,title,status,score", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Components", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark Components", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_benchmark_scorecard_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, registry_path = make_run(Path(tmp))
            scorecard = build_benchmark_scorecard(run_dir, registry_path=registry_path, title="<Scorecard>")

            html = render_benchmark_scorecard_html(scorecard)

            self.assertIn("&lt;Scorecard&gt;", html)
            self.assertNotIn("<h1><Scorecard>", html)


if __name__ == "__main__":
    unittest.main()
