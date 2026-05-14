from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_portfolio_comparison import (
    build_training_portfolio_comparison,
    load_training_portfolio,
    render_training_portfolio_comparison_html,
    render_training_portfolio_comparison_markdown,
    write_training_portfolio_comparison_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_portfolio(
    root: Path,
    name: str,
    *,
    overall_score: float,
    rubric_score: float,
    final_val_loss: float,
    best_val_loss: float,
    status: str = "completed",
    dataset_warnings: int = 0,
    maturity_status: str = "ready",
    relative_artifacts: bool = False,
    missing_artifacts: set[str] | None = None,
) -> Path:
    missing = missing_artifacts or set()
    portfolio_dir = root / "portfolios" / name
    run_dir = root / "runs" / name
    dataset_dir = root / "datasets" / f"{name}-zh" / "v1"
    scorecard_path = run_dir / "benchmark-scorecard" / "benchmark_scorecard.json"
    dataset_card_path = dataset_dir / "dataset_card.json"
    maturity_narrative_path = root / "maturity-narrative" / name / "maturity_narrative.json"
    manifest_path = run_dir / "run_manifest.json"
    eval_suite_path = run_dir / "eval_suite" / "eval_suite.json"
    generation_quality_path = run_dir / "eval_suite" / "generation-quality" / "generation_quality.json"
    registry_path = root / "registry" / name / "registry.json"
    maturity_summary_path = root / "maturity-summary" / name / "maturity_summary.json"

    payloads = {
        "benchmark_scorecard": (
            scorecard_path,
            {
                "schema_version": 3,
                "summary": {
                    "overall_status": "pass" if overall_score >= 80 else "warn",
                    "overall_score": overall_score,
                    "rubric_status": "pass" if rubric_score >= 80 else "warn",
                    "rubric_avg_score": rubric_score,
                    "weakest_rubric_case": "qa-basic",
                    "weakest_rubric_score": min(rubric_score, 80),
                },
            },
        ),
        "dataset_card": (
            dataset_card_path,
            {
                "schema_version": 1,
                "dataset": {"id": f"{name}-zh-v1", "name": f"{name}-zh", "version": "v1"},
                "summary": {
                    "readiness_status": "ready" if dataset_warnings == 0 else "review",
                    "quality_status": "pass" if dataset_warnings == 0 else "warn",
                    "warning_count": dataset_warnings,
                },
            },
        ),
        "maturity_narrative": (
            maturity_narrative_path,
            {
                "schema_version": 1,
                "summary": {
                    "portfolio_status": maturity_status,
                    "release_readiness_trend_status": "stable",
                    "request_history_status": "pass",
                },
            },
        ),
        "run_manifest": (
            manifest_path,
            {
                "schema_version": 1,
                "data": {"token_count": 1200, "train_token_count": 960, "val_token_count": 240},
                "model": {"parameter_count": 123456},
                "results": {"last_loss": final_val_loss, "history_summary": {"best_val_loss": best_val_loss, "last_val_loss": final_val_loss}},
            },
        ),
        "eval_suite": (
            eval_suite_path,
            {"schema_version": 1, "suite_name": "minigpt-zh-benchmark", "suite_version": "1", "case_count": 5},
        ),
        "generation_quality": (
            generation_quality_path,
            {
                "schema_version": 1,
                "summary": {
                    "overall_status": "pass",
                    "case_count": 5,
                    "warn_count": 0,
                    "fail_count": 0,
                    "avg_unique_ratio": 0.72,
                },
            },
        ),
        "registry": (registry_path, {"schema_version": 1, "runs": []}),
        "maturity_summary": (maturity_summary_path, {"schema_version": 1, "summary": {"overall_status": "pass"}}),
    }
    for key, (path, payload) in payloads.items():
        if key not in missing:
            write_json(path, payload)

    artifacts = {}
    for key, (path, _payload) in payloads.items():
        artifacts[key] = str(path.relative_to(root)) if relative_artifacts else str(path)
    portfolio = {
        "schema_version": 1,
        "title": f"{name} portfolio",
        "project_root": str(root),
        "run_name": name,
        "dataset_name": f"{name}-zh",
        "dataset_version": "v1",
        "artifacts": artifacts,
        "steps": [{"key": "train"}, {"key": "eval_suite"}],
        "execution": {
            "status": status,
            "execute": status != "planned",
            "step_count": 2,
            "completed_steps": 2 if status == "completed" else 0,
            "failed_step": None if status != "failed" else "train",
            "artifact_count": len(artifacts),
            "available_artifact_count": len(artifacts) - len(missing),
        },
    }
    portfolio_path = portfolio_dir / "training_portfolio.json"
    write_json(portfolio_path, portfolio)
    return portfolio_path


class TrainingPortfolioComparisonTests(unittest.TestCase):
    def test_load_training_portfolio_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = make_portfolio(Path(tmp), "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)

            loaded = load_training_portfolio(path.parent)

            self.assertEqual(loaded["run_name"], "baseline")
            self.assertTrue(loaded["_source_path"].endswith("training_portfolio.json"))

    def test_build_comparison_records_baseline_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(root, "candidate", overall_score=89, rubric_score=86, final_val_loss=0.95, best_val_loss=0.9)
            review = make_portfolio(
                root,
                "review",
                overall_score=74,
                rubric_score=70,
                final_val_loss=1.45,
                best_val_loss=1.35,
                dataset_warnings=2,
                maturity_status="review",
                missing_artifacts={"maturity_summary"},
            )

            report = build_training_portfolio_comparison(
                [baseline, candidate, review],
                names=["base", "candidate", "review"],
                baseline="base",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["baseline"]["name"], "base")
            self.assertEqual(report["best_by_overall_score"]["name"], "candidate")
            self.assertEqual(report["best_by_final_val_loss"]["name"], "candidate")
            self.assertEqual(report["summary"]["score_improvement_count"], 1)
            self.assertEqual(report["summary"]["score_regression_count"], 1)
            self.assertEqual(report["summary"]["artifact_regression_count"], 1)
            self.assertEqual(report["summary"]["maturity_review_count"], 1)
            candidate_delta = next(row for row in report["baseline_deltas"] if row["name"] == "candidate")
            self.assertEqual(candidate_delta["overall_relation"], "improved")
            self.assertEqual(candidate_delta["final_val_loss_relation"], "improved")
            review_delta = next(row for row in report["baseline_deltas"] if row["name"] == "review")
            self.assertEqual(review_delta["overall_relation"], "regressed")
            self.assertEqual(review_delta["final_val_loss_relation"], "regressed")
            self.assertTrue(report["recommendations"])

    def test_build_comparison_resolves_relative_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            portfolio = make_portfolio(root, "relative", overall_score=88, rubric_score=84, final_val_loss=1.0, best_val_loss=0.96, relative_artifacts=True)

            report = build_training_portfolio_comparison([portfolio.parent])

            self.assertEqual(report["portfolios"][0]["overall_score"], 88)
            self.assertEqual(report["portfolios"][0]["artifact_coverage"], 1.0)
            self.assertEqual(report["portfolios"][0]["eval_case_count"], 5)

    def test_write_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(root, "candidate", overall_score=89, rubric_score=86, final_val_loss=0.95, best_val_loss=0.9)
            report = build_training_portfolio_comparison([baseline, candidate], names=["<base>", "<candidate>"])

            outputs = write_training_portfolio_comparison_outputs(report, root / "out")
            markdown = render_training_portfolio_comparison_markdown(report)
            html = render_training_portfolio_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("overall_score_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Artifact Coverage", markdown)
            self.assertIn("&lt;base&gt;", html)
            self.assertNotIn("<strong><base>", html)

    def test_build_comparison_rejects_name_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            build_training_portfolio_comparison(["a", "b"], names=["only-one"])


if __name__ == "__main__":
    unittest.main()
