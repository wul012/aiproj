from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.maturity import build_maturity_summary, write_maturity_summary_outputs
from minigpt.maturity_narrative import build_maturity_narrative, write_maturity_narrative_outputs
from minigpt.registry import build_run_registry, write_registry_outputs
from minigpt.release_readiness_comparison import (
    build_release_readiness_comparison,
    write_release_readiness_comparison_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_readiness(
    root: Path,
    name: str,
    *,
    readiness_status: str,
    coverage_status: str,
    coverage_percent: float,
    coverage_gap: float,
) -> Path:
    panel_status = "pass" if coverage_status == "pass" else "warn"
    report = {
        "schema_version": 1,
        "summary": {
            "release_name": name,
            "readiness_status": readiness_status,
            "decision": "ship" if readiness_status == "ready" else "review",
            "gate_status": "pass",
            "audit_status": "pass",
            "audit_score_percent": 100.0,
            "ci_workflow_status": "pass",
            "ci_workflow_failed_checks": 0,
            "request_history_status": "pass",
            "test_coverage_status": coverage_status,
            "test_coverage_percent": coverage_percent,
            "test_coverage_fail_under": 80.0,
            "test_coverage_gap": coverage_gap,
            "maturity_status": "pass",
            "ready_runs": 1,
            "missing_artifacts": 0,
            "fail_panel_count": 0,
            "warn_panel_count": 0 if panel_status == "pass" else 1,
        },
        "panels": [
            {"key": "release_gate", "title": "Release gate", "status": "pass", "detail": "pass"},
            {"key": "ci_workflow_hygiene", "title": "CI workflow", "status": "pass", "detail": "pass"},
            {"key": "test_coverage", "title": "Test coverage", "status": panel_status, "detail": panel_status},
        ],
        "actions": [],
        "evidence": [],
    }
    path = root / name / "release_readiness.json"
    write_json(path, report)
    return path


def write_project_basics(project: Path, version_count: int = 65) -> None:
    project.mkdir(parents=True, exist_ok=True)
    tags = "\n".join(f"v{version}.0.0 MiniGPT v{version}" for version in range(1, version_count + 1))
    (project / "README.md").write_text("# Demo\n\n" + tags + "\n", encoding="utf-8")
    for version in range(1, version_count + 1):
        archive_root = "a" if version <= 31 else "b"
        (project / archive_root / str(version)).mkdir(parents=True, exist_ok=True)


def write_run_manifest(run_dir: Path) -> None:
    write_json(
        run_dir / "run_manifest.json",
        {
            "git": {"short_commit": "abc1234", "dirty": False},
            "training": {"tokenizer": "char", "args": {"max_iters": 1}},
            "data": {"source": {"kind": "fixture"}, "dataset_quality": {"status": "pass", "short_fingerprint": "abc12345"}},
            "model": {"parameter_count": 1234},
            "results": {"history_summary": {"best_val_loss": 1.0}},
            "artifacts": [{"key": "run_manifest", "exists": True}],
        },
    )


def write_narrative_inputs(project: Path) -> None:
    write_json(
        project / "runs" / "request-history-summary" / "request_history_summary.json",
        {"schema_version": 1, "summary": {"status": "pass", "total_log_records": 4, "timeout_rate": 0.0, "error_rate": 0.0}},
    )
    write_json(
        project / "runs" / "demo-run" / "benchmark-scorecard" / "benchmark_scorecard.json",
        {
            "schema_version": 3,
            "summary": {
                "overall_status": "pass",
                "overall_score": 88.5,
                "rubric_status": "pass",
                "rubric_avg_score": 90.0,
                "weakest_rubric_case": "summary-short",
                "weakest_rubric_score": 82.0,
            },
        },
    )
    write_json(
        project / "runs" / "demo-run" / "benchmark-scorecard-decision" / "benchmark_scorecard_decision.json",
        {
            "schema_version": 1,
            "decision_status": "promote",
            "summary": {
                "candidate_count": 1,
                "clean_candidate_count": 1,
                "review_candidate_count": 0,
                "blocked_candidate_count": 0,
                "selected_name": "demo-run",
                "selected_eval_suite_comparison_status": "pass",
            },
            "selected_run": {
                "name": "demo-run",
                "decision_relation": "promote",
                "rubric_avg_score": 90.0,
                "generation_quality_total_flags_delta": -2,
                "eval_suite_comparison_status": "pass",
            },
            "candidate_evaluations": [
                {"name": "baseline", "is_baseline": True, "blockers": ["baseline"], "review_items": []},
                {"name": "demo-run", "is_baseline": False, "eval_suite_comparison_status": "pass", "blockers": [], "review_items": []},
            ],
        },
    )
    write_json(
        project / "datasets" / "demo" / "v1" / "dataset_card.json",
        {
            "schema_version": 1,
            "summary": {"readiness_status": "ready", "quality_status": "pass", "warning_count": 0, "short_fingerprint": "abc12345"},
            "quality": {"status": "pass", "warning_count": 0},
        },
    )


class CoverageGovernanceChainTests(unittest.TestCase):
    def test_coverage_regression_flows_from_readiness_comparison_to_maturity_narrative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            write_project_basics(project)
            baseline = make_readiness(
                root / "readiness",
                "baseline",
                readiness_status="ready",
                coverage_status="pass",
                coverage_percent=90.17,
                coverage_gap=0.0,
            )
            current = make_readiness(
                root / "readiness",
                "current",
                readiness_status="review",
                coverage_status="fail",
                coverage_percent=76.0,
                coverage_gap=4.0,
            )
            comparison = build_release_readiness_comparison([baseline, current], generated_at="2026-05-19T00:00:00Z")
            comparison_outputs = write_release_readiness_comparison_outputs(
                comparison,
                project / "runs" / "demo-run" / "release-readiness-comparison",
            )
            write_run_manifest(project / "runs" / "demo-run")

            registry = build_run_registry([project / "runs" / "demo-run"], names=["demo-run"])
            registry_outputs = write_registry_outputs(registry, project / "runs" / "registry")

            maturity = build_maturity_summary(
                project,
                registry_path=registry_outputs["json"],
                generated_at="2026-05-19T00:00:00Z",
            )
            maturity_outputs = write_maturity_summary_outputs(maturity, project / "runs" / "maturity-summary")

            write_narrative_inputs(project)
            narrative = build_maturity_narrative(
                project,
                maturity_path=maturity_outputs["json"],
                registry_path=registry_outputs["json"],
                generated_at="2026-05-19T00:00:00Z",
            )
            narrative_outputs = write_maturity_narrative_outputs(narrative, project / "runs" / "maturity-narrative")
            release_section = next(section for section in narrative["sections"] if section["key"] == "release_quality")

            self.assertEqual(comparison["summary"]["test_coverage_regression_count"], 1)
            self.assertEqual(comparison["deltas"][0]["test_coverage_percent_delta"], -14.17)
            self.assertEqual(comparison["deltas"][0]["test_coverage_gap_delta"], 4)
            self.assertEqual(registry["release_readiness_comparison_counts"], {"coverage-regressed": 1})
            self.assertEqual(registry["release_readiness_delta_summary"]["test_coverage_regression_count"], 1)
            self.assertEqual(registry["release_readiness_delta_summary"]["max_abs_test_coverage_gap_delta"], 4)
            self.assertEqual(maturity["summary"]["overall_status"], "warn")
            self.assertEqual(maturity["summary"]["release_readiness_trend_status"], "coverage-regressed")
            self.assertEqual(maturity["summary"]["release_readiness_test_coverage_regression_count"], 1)
            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "coverage-regressed")
            self.assertEqual(narrative["summary"]["release_readiness_test_coverage_regression_count"], 1)
            self.assertEqual(release_section["status"], "coverage-regressed")
            self.assertIn("test coverage regressions=1", release_section["claim"])
            self.assertIn("Resolve review-level release", narrative["recommendations"][0])
            self.assertTrue(Path(comparison_outputs["json"]).exists())
            self.assertTrue(Path(narrative_outputs["html"]).exists())


if __name__ == "__main__":
    unittest.main()
