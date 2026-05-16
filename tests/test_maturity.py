from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maturity import build_maturity_summary, render_maturity_summary_html, write_maturity_summary_outputs


def make_project(root: Path, version_count: int = 48) -> Path:
    tags = "\n".join(f"v{version}.0.0 MiniGPT v{version}" for version in range(1, version_count + 1))
    (root / "README.md").write_text("# Demo\n\n" + tags + "\n", encoding="utf-8")
    for version in range(1, version_count + 1):
        archive_root = "a" if version <= 31 else "b" if version <= 68 else "c"
        archive = root / archive_root / str(version) / "图片"
        archive.mkdir(parents=True)
    docs = root / "代码讲解记录_项目成熟度阶段"
    docs.mkdir(parents=True)
    (docs / "63-v48-maturity-summary.md").write_text("# v48\n", encoding="utf-8")
    registry_dir = root / "runs" / "registry"
    registry_dir.mkdir(parents=True)
    (registry_dir / "registry.json").write_text(
        json.dumps(
            {
                "run_count": 2,
                "quality_counts": {"pass": 1, "warn": 1},
                "generation_quality_counts": {"pass": 2},
                "pair_report_counts": {"pair_batch": 2, "pair_trend": 1},
                "pair_delta_summary": {"case_count": 6, "max_abs_generated_char_delta": 11},
                "release_readiness_comparison_counts": {"improved": 1, "stable": 1},
                "release_readiness_delta_summary": {
                    "delta_count": 2,
                    "run_count": 2,
                    "regressed_count": 0,
                    "improved_count": 1,
                    "panel_changed_count": 0,
                    "same_count": 1,
                    "changed_panel_delta_count": 1,
                    "max_abs_status_delta": 3,
                    "ci_workflow_regression_count": 0,
                    "ci_workflow_status_changed_count": 0,
                    "max_abs_ci_workflow_failed_check_delta": 0,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return registry_dir / "registry.json"


def make_request_history_summary(root: Path) -> Path:
    summary_dir = root / "runs" / "request-history-summary"
    summary_dir.mkdir(parents=True)
    path = summary_dir / "request_history_summary.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "request_log": str(root / "runs" / "minigpt" / "inference_requests.jsonl"),
                "summary": {
                    "status": "watch",
                    "total_log_records": 4,
                    "invalid_record_count": 0,
                    "ok_count": 3,
                    "timeout_count": 1,
                    "bad_request_count": 0,
                    "error_count": 0,
                    "timeout_rate": 0.25,
                    "bad_request_rate": 0.0,
                    "error_rate": 0.0,
                    "stream_request_count": 2,
                    "pair_request_count": 1,
                    "unique_checkpoint_count": 2,
                    "latest_timestamp": "2026-05-13T00:00:00Z",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


class MaturitySummaryTests(unittest.TestCase):
    def test_build_maturity_summary_reads_versions_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, version_count=65)
            make_request_history_summary(root)

            summary = build_maturity_summary(root, generated_at="2026-05-13T00:00:00Z")

            self.assertEqual(summary["summary"]["current_version"], 65)
            self.assertEqual(summary["summary"]["published_version_count"], 65)
            self.assertEqual(summary["summary"]["archive_version_count"], 65)
            self.assertEqual(summary["summary"]["registry_runs"], 2)
            self.assertEqual(summary["summary"]["release_readiness_trend_status"], "improved")
            self.assertEqual(summary["summary"]["release_readiness_delta_count"], 2)
            self.assertEqual(summary["summary"]["release_readiness_regressed_count"], 0)
            self.assertEqual(summary["summary"]["release_readiness_ci_workflow_regression_count"], 0)
            self.assertEqual(summary["summary"]["request_history_status"], "watch")
            self.assertEqual(summary["summary"]["request_history_records"], 4)
            self.assertEqual(summary["summary"]["overall_status"], "pass")
            self.assertEqual(summary["registry_context"]["pair_delta_cases"], 6)
            self.assertEqual(summary["release_readiness_context"]["trend_status"], "improved")
            self.assertEqual(summary["release_readiness_context"]["improved_count"], 1)
            self.assertEqual(summary["release_readiness_context"]["max_abs_status_delta"], 3)
            self.assertEqual(summary["release_readiness_context"]["ci_workflow_regression_count"], 0)
            self.assertEqual(summary["request_history_context"]["timeout_rate"], 0.25)
            capability_titles = [item["title"] for item in summary["capabilities"]]
            self.assertIn("Project Synthesis", capability_titles)
            self.assertTrue(all(item["status"] == "pass" for item in summary["capabilities"]))
            local_inference = next(item for item in summary["capabilities"] if item["key"] == "local_inference")
            self.assertIn(60, local_inference["covered_versions"])
            self.assertEqual(local_inference["target_level"], 5)

    def test_archive_discovery_counts_c_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_project(root, version_count=70)

            summary = build_maturity_summary(root, registry_path=registry_path)

            self.assertEqual(summary["summary"]["current_version"], 70)
            self.assertEqual(summary["summary"]["archive_version_count"], 70)

    def test_write_maturity_summary_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_project(root)
            summary = build_maturity_summary(root, registry_path=registry_path)

            outputs = write_maturity_summary_outputs(summary, root / "maturity")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            self.assertIn("Capability Matrix", markdown)
            self.assertIn("Request History Context", markdown)
            self.assertIn("Release Readiness Trend Context", markdown)
            self.assertIn("Project Synthesis", Path(outputs["csv"]).read_text(encoding="utf-8"))
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            self.assertIn("MiniGPT project maturity summary", html)
            self.assertIn("Request History Context", html)
            self.assertIn("Release Readiness Trend Context", html)

    def test_release_readiness_regression_marks_maturity_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_project(root, version_count=65)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["release_readiness_comparison_counts"] = {"regressed": 1}
            registry["release_readiness_delta_summary"]["regressed_count"] = 1
            registry["release_readiness_delta_summary"]["improved_count"] = 0
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            summary = build_maturity_summary(root, registry_path=registry_path)

            self.assertEqual(summary["summary"]["release_readiness_trend_status"], "regressed")
            self.assertEqual(summary["summary"]["overall_status"], "warn")
            self.assertIn("release readiness regressions", " ".join(summary["recommendations"]))

    def test_ci_workflow_regression_marks_maturity_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_path = make_project(root, version_count=65)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["release_readiness_comparison_counts"] = {"ci-regressed": 1}
            registry["release_readiness_delta_summary"]["regressed_count"] = 0
            registry["release_readiness_delta_summary"]["improved_count"] = 0
            registry["release_readiness_delta_summary"]["ci_workflow_regression_count"] = 1
            registry["release_readiness_delta_summary"]["ci_workflow_status_changed_count"] = 1
            registry["release_readiness_delta_summary"]["max_abs_ci_workflow_failed_check_delta"] = 2
            registry_path.write_text(json.dumps(registry), encoding="utf-8")

            summary = build_maturity_summary(root, registry_path=registry_path)

            self.assertEqual(summary["summary"]["release_readiness_trend_status"], "ci-regressed")
            self.assertEqual(summary["summary"]["overall_status"], "warn")
            self.assertEqual(summary["summary"]["release_readiness_ci_workflow_regression_count"], 1)
            self.assertEqual(summary["summary"]["release_readiness_ci_workflow_status_changed_count"], 1)
            self.assertEqual(summary["summary"]["release_readiness_max_ci_workflow_failed_check_delta"], 2)
            self.assertEqual(summary["release_readiness_context"]["ci_workflow_regression_count"], 1)
            self.assertIn("CI workflow hygiene regressions", " ".join(summary["recommendations"]))

    def test_render_maturity_summary_html_escapes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            summary = build_maturity_summary(root, title="<Maturity>")

            html = render_maturity_summary_html(summary)

            self.assertIn("&lt;Maturity&gt;", html)
            self.assertNotIn("<h1><Maturity>", html)


if __name__ == "__main__":
    unittest.main()
