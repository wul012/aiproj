from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

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
    maturity_release_trend: str = "stable",
    ci_regression_count: int = 0,
    ci_order_regression_count: int = 0,
    ci_boundary_plan_regression_count: int = 0,
    ci_archived_path_regression_count: int = 0,
    ci_regression_reasons: list[str] | None = None,
    coverage_regression_count: int = 0,
    suite_design_regression_count: int = 0,
    suite_design_delta_count: int = 0,
    design_change_delta_count: int = 0,
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
    ci_reason_list = ci_regression_reasons or []
    ci_reason_counts: dict[str, int] = {}
    for reason in ci_reason_list:
        ci_reason_counts[reason] = ci_reason_counts.get(reason, 0) + 1

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
                    "release_readiness_trend_status": maturity_release_trend,
                    "release_readiness_ci_workflow_regression_count": ci_regression_count,
                    "release_readiness_ci_workflow_order_regression_count": ci_order_regression_count,
                    "release_readiness_ci_workflow_status_changed_count": 1 if ci_regression_count or ci_order_regression_count else 0,
                    "release_readiness_max_ci_workflow_failed_check_delta": 1 if ci_regression_count else 0,
                    "release_readiness_max_ci_workflow_order_violation_delta": 1 if ci_order_regression_count else 0,
                    "release_readiness_ci_workflow_regression_reasons": ci_reason_list,
                    "release_readiness_ci_workflow_regression_reason_counts": ci_reason_counts,
                    "release_readiness_ci_boundary_plan_check_ready_regression_count": ci_boundary_plan_regression_count,
                    "release_readiness_ci_archived_path_portability_check_ready_regression_count": ci_archived_path_regression_count,
                    "release_readiness_test_coverage_regression_count": coverage_regression_count,
                    "release_readiness_test_coverage_status_changed_count": 1 if coverage_regression_count else 0,
                    "release_readiness_max_test_coverage_percent_delta": 8.5 if coverage_regression_count else 0,
                    "release_readiness_max_test_coverage_gap_delta": 3 if coverage_regression_count else 0,
                    "release_readiness_benchmark_suite_design_delta_count": suite_design_delta_count,
                    "release_readiness_benchmark_suite_design_regression_count": suite_design_regression_count,
                    "release_readiness_benchmark_design_change_delta_count": design_change_delta_count,
                    "release_readiness_max_benchmark_suite_design_delta": 2 if suite_design_regression_count else 0,
                    "release_readiness_max_benchmark_design_change_delta": 3 if design_change_delta_count else 0,
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
            self.assertEqual(report["summary"]["maturity_review_names"], ["review"])
            self.assertEqual(report["summary"]["maturity_ci_regression_count"], 0)
            self.assertEqual(report["summary"]["maturity_ci_regression_names"], [])
            self.assertEqual(report["summary"]["maturity_coverage_regression_count"], 0)
            self.assertEqual(report["summary"]["maturity_coverage_regression_names"], [])
            self.assertEqual(report["summary"]["maturity_suite_design_regression_count"], 0)
            self.assertEqual(report["summary"]["maturity_suite_design_regression_names"], [])
            self.assertEqual(report["summary"]["review_action_count"], 4)
            self.assertEqual(report["summary"]["blocker_action_count"], 0)
            self.assertEqual(report["summary"]["best_score_name"], "candidate")
            self.assertEqual(report["summary"]["best_score_maturity_status"], "ready")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_trend"], "stable")
            candidate_delta = next(row for row in report["baseline_deltas"] if row["name"] == "candidate")
            self.assertEqual(candidate_delta["overall_relation"], "improved")
            self.assertEqual(candidate_delta["final_val_loss_relation"], "improved")
            review_delta = next(row for row in report["baseline_deltas"] if row["name"] == "review")
            self.assertEqual(review_delta["overall_relation"], "regressed")
            self.assertEqual(review_delta["final_val_loss_relation"], "regressed")
            self.assertTrue(report["recommendations"])
            self.assertIn("non-leading portfolios", " ".join(report["recommendations"]))
            reasons = {action["reason"] for action in report["review_actions"]}
            self.assertIn("artifact_coverage_gap", reasons)
            self.assertIn("quality_regression", reasons)
            self.assertIn("dataset_card_review", reasons)
            self.assertIn("non_leading_maturity_review", reasons)

    def test_best_scoring_review_portfolio_keeps_maturity_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=91,
                rubric_score=88,
                final_val_loss=0.9,
                best_val_loss=0.88,
                maturity_status="review",
            )

            report = build_training_portfolio_comparison([baseline, candidate], names=["base", "candidate"], baseline="base")

            self.assertEqual(report["summary"]["best_score_name"], "candidate")
            self.assertEqual(report["summary"]["best_score_maturity_status"], "review")
            self.assertEqual(report["summary"]["maturity_review_count"], 1)
            self.assertEqual(report["summary"]["maturity_review_names"], ["candidate"])
            self.assertEqual(report["summary"]["review_action_count"], 1)
            self.assertEqual(report["summary"]["blocker_action_count"], 1)
            self.assertEqual(report["review_actions"][0]["reason"], "best_score_maturity_review")
            self.assertEqual(report["review_actions"][0]["severity"], "blocker")
            self.assertIn("best-scoring portfolio's maturity narrative", " ".join(report["recommendations"]))

    def test_best_scoring_coverage_regressed_portfolio_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=92,
                rubric_score=88,
                final_val_loss=0.9,
                best_val_loss=0.88,
                maturity_release_trend="coverage-regressed",
                coverage_regression_count=2,
            )

            report = build_training_portfolio_comparison([baseline, candidate], names=["base", "candidate"], baseline="base")

            self.assertEqual(report["summary"]["best_score_name"], "candidate")
            self.assertEqual(report["summary"]["best_score_maturity_status"], "ready")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_trend"], "coverage-regressed")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_test_coverage_regression_count"], 2)
            self.assertEqual(report["summary"]["maturity_coverage_regression_count"], 1)
            self.assertEqual(report["summary"]["maturity_coverage_regression_names"], ["candidate"])
            self.assertEqual(report["summary"]["review_action_count"], 1)
            self.assertEqual(report["summary"]["blocker_action_count"], 1)
            self.assertEqual(report["review_actions"][0]["reason"], "best_score_coverage_regressed")
            self.assertEqual(report["review_actions"][0]["severity"], "blocker")
            self.assertEqual(report["review_actions"][0]["evidence"]["coverage_regression_count"], 2)
            candidate_delta = next(row for row in report["baseline_deltas"] if row["name"] == "candidate")
            self.assertTrue(candidate_delta["maturity_release_readiness_trend_changed"])
            self.assertEqual(candidate_delta["maturity_release_readiness_test_coverage_regression_delta"], 2)
            self.assertIn("release-readiness coverage regressed", candidate_delta["explanation"])
            self.assertIn("coverage regressions", " ".join(report["recommendations"]))

    def test_best_scoring_ci_order_regressed_portfolio_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=92,
                rubric_score=88,
                final_val_loss=0.9,
                best_val_loss=0.88,
                maturity_release_trend="ci-regressed",
                ci_order_regression_count=1,
                ci_boundary_plan_regression_count=1,
                ci_archived_path_regression_count=1,
                ci_regression_reasons=[
                    "ci_order_violations_increased",
                    "ci_failed_checks_increased",
                    "boundary_gate_plan_check_not_ready",
                    "archived_path_portability_check_not_ready",
                ],
            )

            report = build_training_portfolio_comparison([baseline, candidate], names=["base", "candidate"], baseline="base")

            self.assertEqual(report["summary"]["best_score_name"], "candidate")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_trend"], "ci-regressed")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_ci_workflow_order_regression_count"], 1)
            self.assertEqual(
                report["summary"]["best_score_maturity_release_readiness_ci_workflow_regression_reasons"],
                [
                    "ci_order_violations_increased",
                    "ci_failed_checks_increased",
                    "boundary_gate_plan_check_not_ready",
                    "archived_path_portability_check_not_ready",
                ],
            )
            self.assertEqual(
                report["summary"]["best_score_maturity_release_readiness_ci_workflow_regression_reason_counts"],
                {
                    "ci_order_violations_increased": 1,
                    "ci_failed_checks_increased": 1,
                    "boundary_gate_plan_check_not_ready": 1,
                    "archived_path_portability_check_not_ready": 1,
                },
            )
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count"], 1)
            self.assertEqual(
                report["summary"]["best_score_maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count"],
                1,
            )
            self.assertEqual(report["summary"]["maturity_ci_regression_count"], 1)
            self.assertEqual(report["summary"]["maturity_ci_regression_names"], ["candidate"])
            self.assertEqual(
                report["summary"]["maturity_ci_regression_reason_counts"],
                {
                    "archived_path_portability_check_not_ready": 1,
                    "boundary_gate_plan_check_not_ready": 1,
                    "ci_failed_checks_increased": 1,
                    "ci_order_violations_increased": 1,
                },
            )
            self.assertEqual(report["summary"]["review_action_count"], 1)
            self.assertEqual(report["summary"]["blocker_action_count"], 1)
            self.assertEqual(report["review_actions"][0]["reason"], "best_score_ci_regressed")
            self.assertEqual(report["review_actions"][0]["severity"], "blocker")
            self.assertEqual(report["review_actions"][0]["evidence"]["ci_workflow_order_regression_count"], 1)
            self.assertEqual(
                report["review_actions"][0]["evidence"]["ci_workflow_regression_reason_counts"],
                {
                    "ci_order_violations_increased": 1,
                    "ci_failed_checks_increased": 1,
                    "boundary_gate_plan_check_not_ready": 1,
                    "archived_path_portability_check_not_ready": 1,
                },
            )
            self.assertEqual(report["review_actions"][0]["evidence"]["ci_boundary_plan_check_ready_regression_count"], 1)
            self.assertEqual(
                report["review_actions"][0]["evidence"]["ci_archived_path_portability_check_ready_regression_count"],
                1,
            )
            self.assertIn("ci_order_violations_increased:1", report["review_actions"][0]["action"])
            candidate_delta = next(row for row in report["baseline_deltas"] if row["name"] == "candidate")
            self.assertEqual(candidate_delta["maturity_release_readiness_ci_workflow_order_regression_delta"], 1)
            self.assertIn("release-readiness CI regressed", candidate_delta["explanation"])
            self.assertIn("ci_failed_checks_increased:1", candidate_delta["explanation"])
            self.assertIn("boundary_gate_plan_check_not_ready:1", candidate_delta["explanation"])
            self.assertIn("archived_path_portability_check_not_ready:1", candidate_delta["explanation"])
            self.assertIn("CI workflow regressions", " ".join(report["recommendations"]))
            self.assertIn("boundary_gate_plan_check_not_ready:1", " ".join(report["recommendations"]))
            self.assertIn("archived_path_portability_check_not_ready:1", " ".join(report["recommendations"]))
            self.assertIn("ci_failed_checks_increased:1", " ".join(report["recommendations"]))

    def test_best_scoring_suite_design_regressed_portfolio_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=92,
                rubric_score=88,
                final_val_loss=0.9,
                best_val_loss=0.88,
                maturity_status="review",
                maturity_release_trend="benchmark-regressed",
                suite_design_delta_count=1,
                suite_design_regression_count=1,
                design_change_delta_count=1,
            )

            report = build_training_portfolio_comparison([baseline, candidate], names=["base", "candidate"], baseline="base")

            self.assertEqual(report["summary"]["best_score_name"], "candidate")
            self.assertEqual(report["summary"]["best_score_maturity_status"], "review")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_trend"], "benchmark-regressed")
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_benchmark_suite_design_regression_count"], 1)
            self.assertEqual(report["summary"]["best_score_maturity_release_readiness_benchmark_design_change_delta_count"], 1)
            self.assertEqual(report["summary"]["maturity_suite_design_regression_count"], 1)
            self.assertEqual(report["summary"]["maturity_suite_design_regression_names"], ["candidate"])
            self.assertEqual(report["summary"]["review_action_count"], 1)
            self.assertEqual(report["summary"]["blocker_action_count"], 1)
            self.assertEqual(report["review_actions"][0]["reason"], "best_score_suite_design_regressed")
            self.assertEqual(report["review_actions"][0]["severity"], "blocker")
            self.assertEqual(report["review_actions"][0]["evidence"]["suite_design_regression_count"], 1)
            self.assertEqual(report["review_actions"][0]["evidence"]["design_change_delta_count"], 1)
            candidate_delta = next(row for row in report["baseline_deltas"] if row["name"] == "candidate")
            self.assertEqual(candidate_delta["maturity_release_readiness_benchmark_suite_design_regression_delta"], 1)
            self.assertEqual(candidate_delta["maturity_release_readiness_benchmark_design_change_delta"], 1)
            self.assertIn("release-readiness suite-design regressed", candidate_delta["explanation"])
            self.assertIn("suite-design regressions", " ".join(report["recommendations"]))

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
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=89,
                rubric_score=86,
                final_val_loss=0.95,
                best_val_loss=0.9,
                maturity_release_trend="ci-regressed",
                ci_regression_count=1,
                ci_regression_reasons=["ci_failed_checks_increased"],
            )
            report = build_training_portfolio_comparison([baseline, candidate], names=["<base>", "<candidate>"])

            outputs = write_training_portfolio_comparison_outputs(report, root / "out")
            markdown = render_training_portfolio_comparison_markdown(report)
            html = render_training_portfolio_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("overall_score_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn(
                "maturity_release_readiness_ci_workflow_regression_reason_counts",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "maturity_release_readiness_ci_boundary_plan_check_ready_regression_count",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn(
                "maturity_release_readiness_benchmark_suite_design_regression_count",
                Path(outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("## Artifact Coverage", markdown)
            self.assertIn("Maturity review portfolios", markdown)
            self.assertIn("Maturity CI regressions", markdown)
            self.assertIn("Maturity CI regression reasons", markdown)
            self.assertIn("Best score CI boundary plan regressions", markdown)
            self.assertIn("Best score CI archived path regressions", markdown)
            self.assertIn("ci_failed_checks_increased:1", markdown)
            self.assertIn("Maturity coverage regressions", markdown)
            self.assertIn("Maturity suite-design regressions", markdown)
            self.assertIn("Best score release readiness trend", markdown)
            self.assertIn("## Review Actions", markdown)
            self.assertIn("Best score maturity", markdown)
            self.assertIn("&lt;base&gt;", html)
            self.assertIn("Maturity reviews", html)
            self.assertIn("CI regressions", html)
            self.assertIn("CI regression reasons", html)
            self.assertIn("Best score CI boundary plan", html)
            self.assertIn("ci_failed_checks_increased:1", html)
            self.assertIn("Coverage regressions", html)
            self.assertIn("Suite-design regressions", html)
            self.assertIn("Best score release trend", html)
            self.assertIn("Review Actions", html)
            self.assertIn("Best score maturity", html)
            self.assertNotIn("<strong><base>", html)

    def test_cli_can_fail_on_blocker_review_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = make_portfolio(root, "baseline", overall_score=82, rubric_score=80, final_val_loss=1.2, best_val_loss=1.1)
            candidate = make_portfolio(
                root,
                "candidate",
                overall_score=91,
                rubric_score=88,
                final_val_loss=0.9,
                best_val_loss=0.88,
                maturity_status="review",
            )
            out_dir = root / "out"
            command = [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "compare_training_portfolios.py"),
                str(baseline),
                str(candidate),
                "--name",
                "base",
                "--name",
                "candidate",
                "--baseline",
                "base",
                "--out-dir",
                str(out_dir),
            ]

            default_result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            gated_result = subprocess.run(command + ["--fail-on-blocker-action"], cwd=ROOT, capture_output=True, text=True, check=False)

            self.assertEqual(default_result.returncode, 0)
            self.assertIn("blocker_action_count=1", default_result.stdout)
            self.assertIn(
                "best_score_maturity_release_readiness_ci_archived_path_portability_check_ready_regression_count=0",
                default_result.stdout,
            )
            self.assertIn("maturity_suite_design_regression_count=0", default_result.stdout)
            self.assertIn("decision=continue_with_portfolio_comparison", default_result.stdout)
            self.assertEqual(gated_result.returncode, 1)
            self.assertIn("blocker_action_count=1", gated_result.stdout)
            self.assertIn("decision=blocked_by_review_actions", gated_result.stdout)
            self.assertTrue((out_dir / "training_portfolio_comparison.json").exists())

    def test_build_comparison_rejects_name_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            build_training_portfolio_comparison(["a", "b"], names=["only-one"])


if __name__ == "__main__":
    unittest.main()
