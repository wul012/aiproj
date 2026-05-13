from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.benchmark_scorecard_comparison import (
    build_benchmark_scorecard_comparison,
    load_benchmark_scorecard,
    render_benchmark_scorecard_comparison_html,
    render_benchmark_scorecard_comparison_markdown,
    write_benchmark_scorecard_comparison_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_scorecard(
    root: Path,
    name: str,
    *,
    overall: float,
    qa_score: float,
    summary_score: float,
    qa_missing: list[str],
    qa_failed: list[str],
    summary_missing: list[str],
    weakest: str,
) -> Path:
    run_dir = root / "runs" / name
    scorecard_path = run_dir / "benchmark-scorecard" / "benchmark_scorecard.json"
    qa_status = "pass" if qa_score >= 80 else "warn" if qa_score >= 60 else "fail"
    summary_status = "pass" if summary_score >= 80 else "warn" if summary_score >= 60 else "fail"
    avg = round((qa_score + summary_score) / 2, 2)
    write_json(
        scorecard_path,
        {
            "schema_version": 3,
            "title": f"{name} scorecard",
            "generated_at": "2026-05-13T00:00:00Z",
            "run_dir": str(run_dir),
            "summary": {
                "overall_score": overall,
                "overall_status": "pass" if overall >= 80 else "warn",
                "component_count": 6,
                "rubric_status": "pass" if avg >= 80 else "warn",
                "rubric_avg_score": avg,
                "rubric_pass_count": sum(1 for item in [qa_status, summary_status] if item == "pass"),
                "rubric_warn_count": sum(1 for item in [qa_status, summary_status] if item == "warn"),
                "rubric_fail_count": sum(1 for item in [qa_status, summary_status] if item == "fail"),
                "weakest_rubric_case": weakest,
                "weakest_rubric_score": min(qa_score, summary_score),
                "weakest_task_type": "qa" if qa_score <= summary_score else "summary",
                "weakest_task_type_score": min(qa_score, summary_score),
                "weakest_difficulty": "hard" if qa_score <= summary_score else "medium",
                "weakest_difficulty_score": min(qa_score, summary_score),
            },
            "rubric_scores": {
                "summary": {
                    "case_count": 2,
                    "avg_score": avg,
                    "overall_status": "pass" if avg >= 80 else "warn",
                    "pass_count": sum(1 for item in [qa_status, summary_status] if item == "pass"),
                    "warn_count": sum(1 for item in [qa_status, summary_status] if item == "warn"),
                    "fail_count": 0,
                    "weakest_case": weakest,
                    "weakest_score": min(qa_score, summary_score),
                },
                "cases": [
                    {
                        "name": "qa-basic",
                        "task_type": "qa",
                        "difficulty": "hard",
                        "status": qa_status,
                        "score": qa_score,
                        "missing_terms": qa_missing,
                        "failed_checks": qa_failed,
                    },
                    {
                        "name": "summary-short",
                        "task_type": "summary",
                        "difficulty": "medium",
                        "status": summary_status,
                        "score": summary_score,
                        "missing_terms": summary_missing,
                        "failed_checks": ["must_include"] if summary_missing else [],
                    },
                ],
            },
            "case_scores": [
                {
                    "name": "qa-basic",
                    "task_type": "qa",
                    "difficulty": "hard",
                    "rubric_status": qa_status,
                    "rubric_score": qa_score,
                    "rubric_missing_terms": qa_missing,
                    "rubric_failed_checks": qa_failed,
                },
                {
                    "name": "summary-short",
                    "task_type": "summary",
                    "difficulty": "medium",
                    "rubric_status": summary_status,
                    "rubric_score": summary_score,
                    "rubric_missing_terms": summary_missing,
                    "rubric_failed_checks": ["must_include"] if summary_missing else [],
                },
            ],
            "drilldowns": {
                "task_type": [
                    {"group_by": "task_type", "key": "qa", "status": qa_status, "score": qa_score, "rubric_score": qa_score, "case_count": 1, "cases": ["qa-basic"]},
                    {
                        "group_by": "task_type",
                        "key": "summary",
                        "status": summary_status,
                        "score": summary_score,
                        "rubric_score": summary_score,
                        "case_count": 1,
                        "cases": ["summary-short"],
                    },
                ],
                "difficulty": [
                    {"group_by": "difficulty", "key": "hard", "status": qa_status, "score": qa_score, "rubric_score": qa_score, "case_count": 1, "cases": ["qa-basic"]},
                    {
                        "group_by": "difficulty",
                        "key": "medium",
                        "status": summary_status,
                        "score": summary_score,
                        "rubric_score": summary_score,
                        "case_count": 1,
                        "cases": ["summary-short"],
                    },
                ],
            },
        },
    )
    return scorecard_path


class BenchmarkScorecardComparisonTests(unittest.TestCase):
    def test_load_scorecard_accepts_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = make_scorecard(
                Path(tmp),
                "baseline",
                overall=88,
                qa_score=90,
                summary_score=86,
                qa_missing=[],
                qa_failed=[],
                summary_missing=[],
                weakest="summary-short",
            )

            loaded = load_benchmark_scorecard(path.parents[1])

            self.assertEqual(loaded["summary"]["overall_score"], 88)
            self.assertTrue(loaded["_source_path"].endswith("benchmark_scorecard.json"))

    def test_build_comparison_records_run_and_case_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_scorecard(root, "baseline", overall=88, qa_score=90, summary_score=86, qa_missing=[], qa_failed=[], summary_missing=[], weakest="summary-short")
            stronger = make_scorecard(root, "stronger", overall=92, qa_score=94, summary_score=90, qa_missing=[], qa_failed=[], summary_missing=[], weakest="summary-short")
            regressed = make_scorecard(
                root,
                "regressed",
                overall=80,
                qa_score=62,
                summary_score=88,
                qa_missing=["事实"],
                qa_failed=["must_include"],
                summary_missing=[],
                weakest="qa-basic",
            )

            report = build_benchmark_scorecard_comparison(
                [baseline, stronger, regressed],
                names=["base", "candidate", "bad"],
                baseline="base",
                generated_at="2026-05-13T00:00:00Z",
            )

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["baseline"]["name"], "base")
            self.assertEqual(report["best_by_rubric_avg_score"]["name"], "candidate")
            self.assertEqual(report["summary"]["improved_rubric_count"], 1)
            self.assertEqual(report["summary"]["regressed_rubric_count"], 1)
            self.assertEqual(report["summary"]["case_regression_count"], 1)
            self.assertEqual(report["summary"]["weakest_case_regression"], "qa-basic")
            bad_delta = next(row for row in report["baseline_deltas"] if row["name"] == "bad")
            self.assertEqual(bad_delta["rubric_relation"], "regressed")
            self.assertTrue(bad_delta["weakest_case_changed"])
            qa_delta = next(row for row in report["case_deltas"] if row["run_name"] == "bad" and row["case"] == "qa-basic")
            self.assertEqual(qa_delta["relation"], "regressed")
            self.assertEqual(qa_delta["added_missing_terms"], ["事实"])
            self.assertEqual(qa_delta["added_failed_checks"], ["must_include"])
            hard_delta = next(row for row in report["difficulty_deltas"] if row["run_name"] == "bad" and row["key"] == "hard")
            self.assertEqual(hard_delta["relation"], "regressed")
            self.assertTrue(report["recommendations"])

    def test_build_comparison_rejects_name_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            build_benchmark_scorecard_comparison(["a", "b"], names=["only-one"])

    def test_write_outputs_and_renderers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_scorecard(root, "baseline", overall=88, qa_score=90, summary_score=86, qa_missing=[], qa_failed=[], summary_missing=[], weakest="summary-short")
            regressed = make_scorecard(root, "regressed", overall=80, qa_score=62, summary_score=88, qa_missing=["事实"], qa_failed=["must_include"], summary_missing=[], weakest="qa-basic")
            report = build_benchmark_scorecard_comparison([baseline, regressed], names=["<base>", "<bad>"])

            outputs = write_benchmark_scorecard_comparison_outputs(report, root / "out")
            markdown = render_benchmark_scorecard_comparison_markdown(report)
            html = render_benchmark_scorecard_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "case_delta_csv", "markdown", "html"})
            self.assertIn("benchmark_scorecard_comparison", Path(outputs["json"]).name)
            self.assertIn("overall_score_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("added_missing_terms", Path(outputs["case_delta_csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Case Deltas", markdown)
            self.assertIn("&lt;base&gt;", html)
            self.assertIn("Case Deltas", html)
            self.assertNotIn("<strong><base>", html)


if __name__ == "__main__":
    unittest.main()
