from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_plan import (
    REGRESSION_ITEMS,
    build_model_capability_regression_plan,
    locate_cadence_report,
    read_json_report,
    resolve_exit_code,
    write_model_capability_regression_plan_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.plan_model_capability_regression_v1135 import main as cli_main


class ModelCapabilityRegressionPlanTests(unittest.TestCase):
    def test_plan_ready_from_cadence_watch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cadence_path = _write_cadence(Path(tmp), status="watch", next_action="schedule_model_capability_regression")
            report = build_model_capability_regression_plan(read_json_report(cadence_path), cadence_path=cadence_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_regression_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["regression_item_count"], len(REGRESSION_ITEMS))
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_plan_fails_without_watch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cadence_path = _write_cadence(Path(tmp), status="pass", next_action="continue_current_plan")
            report = build_model_capability_regression_plan(read_json_report(cadence_path), cadence_path=cadence_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("cadence_watch_detected", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cadence_path = _write_cadence(root, status="watch", next_action="schedule_model_capability_regression")
            report = build_model_capability_regression_plan(read_json_report(cadence_path), cadence_path=cadence_path)
            outputs = write_model_capability_regression_plan_outputs(report, root / "out")
            exit_code = cli_main([str(cadence_path.parent), "--out-dir", str(root / "cli-out"), "--require-plan-ready", "--force"])
            located = locate_cadence_report(cadence_path.parent)

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertEqual(located, cadence_path)


def _write_cadence(root: Path, *, status: str, next_action: str) -> Path:
    out_dir = root / "cadence"
    out_dir.mkdir(parents=True)
    path = out_dir / "model_capability_cadence_v1133.json"
    write_json_payload(
        {
            "status": status,
            "decision": "model_capability_cadence_ready",
            "summary": {
                "cadence_ready": True,
                "next_action": next_action,
                "leading_non_capability_run": 12,
                "max_non_capability_run": 4,
            },
        },
        path,
    )
    return path


if __name__ == "__main__":
    unittest.main()
