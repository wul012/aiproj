from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_suite_manifest import (
    build_model_capability_regression_suite_manifest,
    locate_inventory_report,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_suite_manifest_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.build_model_capability_regression_suite_manifest_v1137 import main as cli_main


class ModelCapabilityRegressionSuiteManifestTests(unittest.TestCase):
    def test_suite_manifest_ready_from_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory_path = _write_inventory(Path(tmp), ready=True)
            report = build_model_capability_regression_suite_manifest(read_json_report(inventory_path), inventory_path=inventory_path)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["suite_ready"])
        self.assertEqual(report["summary"]["suite_item_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)

    def test_suite_manifest_fails_without_ready_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory_path = _write_inventory(Path(tmp), ready=False)
            report = build_model_capability_regression_suite_manifest(read_json_report(inventory_path), inventory_path=inventory_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("inventory_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_path = _write_inventory(root, ready=True)
            report = build_model_capability_regression_suite_manifest(read_json_report(inventory_path), inventory_path=inventory_path)
            outputs = write_model_capability_regression_suite_manifest_outputs(report, root / "out")
            exit_code = cli_main([str(inventory_path.parent), "--out-dir", str(root / "cli-out"), "--require-suite-ready", "--force"])
            located = locate_inventory_report(inventory_path.parent)

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertEqual(located, inventory_path)


def _write_inventory(root: Path, *, ready: bool) -> Path:
    out_dir = root / "inventory"
    out_dir.mkdir(parents=True)
    path = out_dir / "model_capability_regression_inventory_v1136.json"
    write_json_payload(
        {
            "status": "pass" if ready else "fail",
            "inventory": {"inventory_ready": ready},
            "summary": {"inventory_ready": ready},
            "rows": [
                {
                    "check_id": "required_term_coverage",
                    "status": "ready" if ready else "missing",
                    "sample_source": "src/minigpt/required_term_coverage.py",
                    "sample_test": "tests/test_required_term_coverage.py" if ready else "",
                    "sample_artifact": "f/1/解释/report.json",
                }
            ],
        },
        path,
    )
    return path


if __name__ == "__main__":
    unittest.main()
