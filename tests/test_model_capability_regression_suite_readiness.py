from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_suite_readiness import (
    build_model_capability_regression_suite_readiness,
    locate_suite_manifest,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_suite_readiness_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.check_model_capability_regression_suite_readiness_v1138 import main as cli_main


class ModelCapabilityRegressionSuiteReadinessTests(unittest.TestCase):
    def test_readiness_passes_when_source_test_and_boundary_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = _write_suite(root, ready=True)
            report = build_model_capability_regression_suite_readiness(read_json_report(suite_path), suite_path=suite_path)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["readiness_ready"])
        self.assertEqual(resolve_exit_code(report, require_readiness_ready=True), 0)

    def test_readiness_fails_when_test_path_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = _write_suite(root, ready=False)
            report = build_model_capability_regression_suite_readiness(read_json_report(suite_path), suite_path=suite_path)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["ready_item_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_readiness_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = _write_suite(root, ready=True)
            report = build_model_capability_regression_suite_readiness(read_json_report(suite_path), suite_path=suite_path)
            outputs = write_model_capability_regression_suite_readiness_outputs(report, root / "out")
            exit_code = cli_main([str(suite_path.parent), "--out-dir", str(root / "cli-out"), "--require-readiness-ready", "--force"])
            located = locate_suite_manifest(suite_path.parent)

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertEqual(located, suite_path)


def _write_suite(root: Path, *, ready: bool) -> Path:
    source = root / "src" / "minigpt" / "required_term_coverage.py"
    test = root / "tests" / "test_required_term_coverage.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    if ready:
        test.parent.mkdir(parents=True)
        test.write_text("def test_value():\n    assert True\n", encoding="utf-8")
    out_dir = root / "suite"
    out_dir.mkdir(parents=True)
    path = out_dir / "model_capability_regression_suite_manifest_v1137.json"
    write_json_payload(
        {
            "status": "pass",
            "suite": {"suite_ready": True},
            "summary": {"suite_ready": True},
            "rows": [
                {
                    "suite_id": "capability-regression-01",
                    "check_id": "required_term_coverage",
                    "primary_source": str(source),
                    "primary_test": str(test),
                    "boundary": "evidence_lookup_not_model_promotion",
                }
            ],
        },
        path,
    )
    return path


if __name__ == "__main__":
    unittest.main()
