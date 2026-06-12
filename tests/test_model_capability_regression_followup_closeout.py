from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_followup_closeout import (
    build_model_capability_regression_followup_closeout,
    locate_readiness_report,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_followup_closeout_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.close_model_capability_regression_followup_v1139 import main as cli_main


class ModelCapabilityRegressionFollowupCloseoutTests(unittest.TestCase):
    def test_closeout_ready_from_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            readiness_path = _write_readiness(Path(tmp), ready=True)
            report = build_model_capability_regression_followup_closeout(read_json_report(readiness_path), readiness_path=readiness_path)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["closeout_ready"])
        self.assertEqual(report["summary"]["next_step"], "run_selected_model_capability_regression_execution")
        self.assertEqual(resolve_exit_code(report, require_closeout_ready=True), 0)

    def test_closeout_fails_when_readiness_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            readiness_path = _write_readiness(Path(tmp), ready=False)
            report = build_model_capability_regression_followup_closeout(read_json_report(readiness_path), readiness_path=readiness_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("readiness_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_closeout_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readiness_path = _write_readiness(root, ready=True)
            report = build_model_capability_regression_followup_closeout(read_json_report(readiness_path), readiness_path=readiness_path)
            outputs = write_model_capability_regression_followup_closeout_outputs(report, root / "out")
            exit_code = cli_main([str(readiness_path.parent), "--out-dir", str(root / "cli-out"), "--require-closeout-ready", "--force"])
            located = locate_readiness_report(readiness_path.parent)

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertEqual(located, readiness_path)


def _write_readiness(root: Path, *, ready: bool) -> Path:
    out_dir = root / "readiness"
    out_dir.mkdir(parents=True)
    path = out_dir / "model_capability_regression_suite_readiness_v1138.json"
    write_json_payload(
        {
            "status": "pass" if ready else "fail",
            "readiness": {"readiness_ready": ready},
            "summary": {"readiness_ready": ready},
            "rows": [
                {
                    "suite_id": "capability-regression-01",
                    "check_id": "required_term_coverage",
                    "status": "ready" if ready else "blocked",
                    "boundary_ok": ready,
                }
            ],
        },
        path,
    )
    return path


if __name__ == "__main__":
    unittest.main()
