from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import maintenance_policy
from minigpt import maintenance_policy_artifacts


class MaintenancePolicyArtifactSplitTests(unittest.TestCase):
    def test_artifact_module_writes_both_report_families(self) -> None:
        batching_report = {
            "schema_version": 1,
            "title": "Maintenance <batch>",
            "generated_at": "2026-05-15T00:00:00Z",
            "policy": {"single_module_utils_limit": 3},
            "summary": {
                "status": "warn",
                "decision": "batch_next_related_work",
                "entry_count": 4,
                "single_module_utils_count": 4,
                "batched_utils_count": 0,
                "longest_single_module_utils_run": 4,
            },
            "single_module_utils_runs": [{"start_version": "v84", "end_version": "v87", "length": 4, "versions": ["v84", "v85", "v86", "v87"]}],
            "proposal": {"decision": "batch", "target_version_kind": "batched", "item_count": 2, "groups": [{"category": "report-utils", "count": 2, "items": ["a", "b"]}], "reasons": ["Batch them."]},
            "recommendations": ["Batch the next related work."],
        }
        pressure_report = {
            "schema_version": 1,
            "title": "Pressure <audit>",
            "generated_at": "2026-05-15T00:00:00Z",
            "summary": {"status": "watch", "decision": "monitor_large_modules", "module_count": 1, "warn_count": 1, "critical_count": 0, "largest_module": "src/minigpt/maintenance_policy.py", "largest_line_count": 465},
            "modules": [{"path": "src/minigpt/maintenance_policy.py", "status": "warn", "line_count": 465, "byte_count": 12000, "function_count": 18, "class_count": 0, "max_function_lines": 70, "largest_function": "build_module_pressure_report", "recommendation": "Prefer extracting cohesive helpers."}],
            "top_modules": [{"path": "src/minigpt/maintenance_policy.py", "status": "warn", "line_count": 465, "byte_count": 12000, "function_count": 18, "class_count": 0, "max_function_lines": 70, "largest_function": "build_module_pressure_report", "recommendation": "Prefer extracting cohesive helpers."}],
            "recommendations": ["Watch large modules."],
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batching_outputs = maintenance_policy_artifacts.write_maintenance_batching_outputs(batching_report, root / "batching")
            pressure_outputs = maintenance_policy_artifacts.write_module_pressure_outputs(pressure_report, root / "pressure")
            batching_html = maintenance_policy_artifacts.render_maintenance_batching_html(batching_report)
            pressure_markdown = maintenance_policy_artifacts.render_module_pressure_markdown(pressure_report)

            self.assertEqual(set(batching_outputs), {"json", "csv", "markdown", "html"})
            self.assertEqual(set(pressure_outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("proposal_decision", Path(batching_outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("max_function_lines", Path(pressure_outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("Maintenance &lt;batch&gt;", batching_html)
            self.assertNotIn("Maintenance <batch>", batching_html)
            self.assertIn("## Top Modules", pressure_markdown)

    def test_maintenance_policy_keeps_legacy_artifact_exports(self) -> None:
        self.assertIs(
            maintenance_policy.write_maintenance_batching_outputs,
            maintenance_policy_artifacts.write_maintenance_batching_outputs,
        )
        self.assertIs(
            maintenance_policy.render_maintenance_batching_html,
            maintenance_policy_artifacts.render_maintenance_batching_html,
        )
        self.assertIs(
            maintenance_policy.write_module_pressure_outputs,
            maintenance_policy_artifacts.write_module_pressure_outputs,
        )
        self.assertIs(
            maintenance_policy.render_module_pressure_markdown,
            maintenance_policy_artifacts.render_module_pressure_markdown,
        )


if __name__ == "__main__":
    unittest.main()
