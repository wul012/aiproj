from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import maturity
from minigpt import maturity_artifacts


class MaturityArtifactSplitTests(unittest.TestCase):
    def test_artifact_module_writes_outputs_from_summary(self) -> None:
        summary = {
            "schema_version": 1,
            "title": "Maturity <summary>",
            "generated_at": "2026-05-15T00:00:00Z",
            "project_root": "D:/aiproj",
            "summary": {
                "current_version": 121,
                "published_version_count": 121,
                "archive_version_count": 121,
                "explanation_version_count": 121,
                "average_maturity_level": 4.5,
                "overall_status": "pass",
                "registry_runs": 2,
                "release_readiness_trend_status": "improved",
                "release_readiness_delta_count": 2,
                "release_readiness_regressed_count": 0,
                "request_history_status": "watch",
                "request_history_records": 4,
            },
            "capabilities": [
                {
                    "key": "model_core",
                    "title": "Model Core",
                    "status": "pass",
                    "maturity_level": 4,
                    "target_level": 4,
                    "score_percent": 100,
                    "covered_count": 2,
                    "target_count": 2,
                    "covered_versions": [1, 2],
                    "missing_versions": [],
                    "evidence": "Tokenizer and model tests.",
                    "next_step": "Scale training.",
                }
            ],
            "phase_timeline": [{"versions": "v1-v12", "title": "MiniGPT learning core", "covered_count": 12, "target_count": 12, "status": "pass"}],
            "registry_context": {"available": True, "run_count": 2, "pair_report_counts": {"pair_batch": 1}, "pair_delta_cases": 6, "pair_delta_max_generated": 11, "quality_counts": {"pass": 1}, "generation_quality_counts": {"pass": 2}},
            "release_readiness_context": {"available": True, "trend_status": "improved", "comparison_counts": {"improved": 1}, "delta_count": 2, "run_count": 2, "regressed_count": 0, "improved_count": 1, "panel_changed_count": 0, "changed_panel_delta_count": 1, "max_abs_status_delta": 3},
            "request_history_context": {"available": True, "status": "watch", "total_log_records": 4, "invalid_record_count": 0, "ok_count": 3, "timeout_count": 1, "bad_request_count": 0, "error_count": 0, "timeout_rate": 0.25, "error_rate": 0.0, "unique_checkpoint_count": 2, "latest_timestamp": "2026-05-15T00:00:00Z"},
            "recommendations": ["Keep maturity evidence current."],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = maturity_artifacts.write_maturity_summary_outputs(summary, tmp)
            html = maturity_artifacts.render_maturity_summary_html(summary)
            markdown = maturity_artifacts.render_maturity_summary_markdown(summary)

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("Model Core", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("Maturity &lt;summary&gt;", html)
            self.assertNotIn("Maturity <summary>", html)
            self.assertIn("## Release Readiness Trend Context", markdown)
            self.assertIn("## Request History Context", markdown)

    def test_maturity_module_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(maturity.write_maturity_summary_outputs, maturity_artifacts.write_maturity_summary_outputs)
        self.assertIs(maturity.render_maturity_summary_html, maturity_artifacts.render_maturity_summary_html)
        self.assertIs(maturity.render_maturity_summary_markdown, maturity_artifacts.render_maturity_summary_markdown)
        self.assertIs(maturity.write_maturity_summary_csv, maturity_artifacts.write_maturity_summary_csv)


if __name__ == "__main__":
    unittest.main()
