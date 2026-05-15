from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.maintenance_policy import (  # noqa: E402
    build_maintenance_batching_report,
    build_maintenance_proposal_decision,
    render_maintenance_batching_html,
    render_maintenance_batching_markdown,
    write_maintenance_batching_outputs,
)


class MaintenancePolicyTests(unittest.TestCase):
    def test_report_warns_on_long_single_module_utils_run(self) -> None:
        history = [
            {"version": "v84", "title": "report-utils migration", "category": "report-utils", "modules": ["a.py"]},
            {"version": "v85", "title": "report-utils migration", "category": "report-utils", "modules": ["b.py"]},
            {"version": "v86", "title": "report-utils migration", "category": "report-utils", "modules": ["c.py"]},
            {"version": "v87", "title": "report-utils migration", "category": "report-utils", "modules": ["d.py"]},
        ]

        report = build_maintenance_batching_report(history, single_module_limit=3, generated_at="2026-05-15T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "warn")
        self.assertEqual(report["summary"]["longest_single_module_utils_run"], 4)
        self.assertEqual(report["single_module_utils_runs"][0]["start_version"], "v84")
        self.assertIn("Batch the next related", " ".join(report["recommendations"]))

    def test_batched_utils_release_breaks_the_warning_run(self) -> None:
        history = [
            {"version": "v105", "title": "report-utils migration", "category": "report-utils", "modules": ["a.py"]},
            {
                "version": "v108",
                "title": "batched release governance report utility migration",
                "category": "report-utils",
                "modules": ["release_gate.py", "release_gate_comparison.py", "request_history_summary.py"],
            },
            {"version": "v109", "title": "maintenance batching policy", "category": "feature", "modules": ["maintenance_policy.py"]},
        ]

        report = build_maintenance_batching_report(history, single_module_limit=3)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["batched_utils_count"], 1)
        self.assertEqual(report["summary"]["longest_single_module_utils_run"], 1)

    def test_proposal_batches_related_low_risk_items(self) -> None:
        decision = build_maintenance_proposal_decision(
            [
                {"name": "registry helpers", "category": "report-utils"},
                {"name": "benchmark helpers", "category": "report-utils"},
                {"name": "audit helpers", "category": "report-utils"},
            ]
        )

        self.assertEqual(decision["decision"], "batch")
        self.assertEqual(decision["target_version_kind"], "batched")
        self.assertEqual(decision["groups"][0]["count"], 3)

    def test_proposal_splits_high_risk_items(self) -> None:
        decision = build_maintenance_proposal_decision(
            [
                {"name": "server endpoint", "category": "report-utils", "risk_flags": ["service_change"]},
                {"name": "registry helper", "category": "report-utils"},
            ]
        )

        self.assertEqual(decision["decision"], "split")
        self.assertEqual(decision["split_count"], 1)
        self.assertIn("service/API", decision["items"][0]["split_reasons"][0])

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_maintenance_batching_report(
                [{"version": "<v1>", "title": "<report-utils>", "category": "report-utils", "modules": ["a.py"]}],
                proposal_items=[{"name": "<helper>", "category": "report-utils"}],
                title="<Maintenance>",
            )

            outputs = write_maintenance_batching_outputs(report, root)
            html = render_maintenance_batching_html(report)
            markdown = render_maintenance_batching_markdown(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertIn("&lt;Maintenance&gt;", html)
            self.assertNotIn("<h1><Maintenance>", html)
            self.assertIn("<Maintenance>", markdown)
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["proposal"]["decision"], "single_ok")


if __name__ == "__main__":
    unittest.main()
