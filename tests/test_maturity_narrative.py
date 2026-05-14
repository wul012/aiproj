from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maturity_narrative import (
    build_maturity_narrative,
    render_maturity_narrative_html,
    write_maturity_narrative_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_project(root: Path, *, release_trend: str = "improved", regressed_count: int = 0) -> dict[str, Path]:
    project = root / "project"
    maturity_path = project / "runs" / "maturity-summary" / "maturity_summary.json"
    registry_path = project / "runs" / "registry" / "registry.json"
    request_path = project / "runs" / "request-history-summary" / "request_history_summary.json"
    scorecard_path = project / "runs" / "demo-run" / "benchmark-scorecard" / "benchmark_scorecard.json"
    dataset_card_path = project / "datasets" / "demo" / "v1" / "dataset_card.json"

    write_json(
        maturity_path,
        {
            "schema_version": 4,
            "summary": {
                "current_version": 66,
                "overall_status": "pass",
                "average_maturity_level": 4.75,
                "registry_runs": 2,
                "release_readiness_trend_status": release_trend,
                "release_readiness_regressed_count": regressed_count,
                "release_readiness_improved_count": 2,
            },
            "release_readiness_context": {
                "available": True,
                "trend_status": release_trend,
                "delta_count": 2,
                "regressed_count": regressed_count,
                "improved_count": 2,
                "panel_changed_count": 0,
            },
            "request_history_context": {
                "status": "pass",
                "total_log_records": 6,
                "timeout_rate": 0.0,
            },
        },
    )
    write_json(
        registry_path,
        {
            "run_count": 2,
            "release_readiness_comparison_counts": {release_trend: 1, "stable": 1},
            "release_readiness_delta_summary": {
                "delta_count": 2,
                "regressed_count": regressed_count,
                "improved_count": 2,
                "panel_changed_count": 0,
            },
        },
    )
    write_json(
        request_path,
        {
            "schema_version": 1,
            "summary": {
                "status": "pass",
                "total_log_records": 6,
                "timeout_rate": 0.0,
                "error_rate": 0.0,
            },
        },
    )
    write_json(
        scorecard_path,
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
        dataset_card_path,
        {
            "schema_version": 1,
            "summary": {
                "readiness_status": "ready",
                "quality_status": "pass",
                "warning_count": 0,
                "short_fingerprint": "abc12345",
            },
            "quality": {"status": "pass", "warning_count": 0},
        },
    )
    return {
        "project": project,
        "maturity": maturity_path,
        "registry": registry_path,
        "request": request_path,
        "scorecard": scorecard_path,
        "dataset_card": dataset_card_path,
    }


class MaturityNarrativeTests(unittest.TestCase):
    def test_build_maturity_narrative_ready_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))

            narrative = build_maturity_narrative(
                paths["project"],
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(narrative["schema_version"], 1)
            self.assertEqual(narrative["summary"]["portfolio_status"], "ready")
            self.assertEqual(narrative["summary"]["current_version"], 66)
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "improved")
            self.assertEqual(narrative["summary"]["release_readiness_regressed_count"], 0)
            self.assertEqual(narrative["summary"]["request_history_status"], "pass")
            self.assertEqual(narrative["summary"]["benchmark_scorecard_count"], 1)
            self.assertEqual(narrative["summary"]["benchmark_avg_score"], 88.5)
            self.assertEqual(narrative["summary"]["benchmark_weakest_case"], "summary-short")
            self.assertEqual(narrative["summary"]["dataset_card_count"], 1)
            self.assertEqual(narrative["summary"]["dataset_warning_count"], 0)
            self.assertEqual(narrative["warnings"], [])
            self.assertIn("Release Quality Trend", {item["title"] for item in narrative["sections"]})
            self.assertIn("benchmark", {item["area"] for item in narrative["evidence_matrix"]})
            self.assertIn("dataset", {item["area"] for item in narrative["evidence_matrix"]})

    def test_build_maturity_narrative_marks_review_for_release_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp), release_trend="regressed", regressed_count=1)

            narrative = build_maturity_narrative(paths["project"])

            self.assertEqual(narrative["summary"]["portfolio_status"], "review")
            self.assertEqual(narrative["summary"]["release_readiness_trend_status"], "regressed")
            self.assertEqual(narrative["summary"]["release_readiness_regressed_count"], 1)
            self.assertIn("Resolve review-level release", narrative["recommendations"][0])

    def test_build_maturity_narrative_requires_request_history_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            paths["request"].unlink()

            narrative = build_maturity_narrative(paths["project"])

            self.assertEqual(narrative["summary"]["portfolio_status"], "incomplete")
            self.assertIn("request history summary is missing", narrative["warnings"])

    def test_write_maturity_narrative_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            narrative = build_maturity_narrative(paths["project"])

            outputs = write_maturity_narrative_outputs(narrative, root / "narrative")

            self.assertEqual(set(outputs), {"json", "markdown", "html"})
            self.assertIn("maturity_narrative", Path(outputs["json"]).name)
            self.assertIn("## Evidence Matrix", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Release Quality Trend", Path(outputs["markdown"]).read_text(encoding="utf-8"))
            self.assertIn("Evidence Matrix", Path(outputs["html"]).read_text(encoding="utf-8"))
            self.assertIn("Benchmark Quality", Path(outputs["html"]).read_text(encoding="utf-8"))

    def test_render_maturity_narrative_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = make_project(Path(tmp))
            narrative = build_maturity_narrative(paths["project"], title="<Narrative>")

            html = render_maturity_narrative_html(narrative)

            self.assertIn("&lt;Narrative&gt;", html)
            self.assertNotIn("<h1><Narrative>", html)


if __name__ == "__main__":
    unittest.main()
