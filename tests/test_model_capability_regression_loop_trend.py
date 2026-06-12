from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_regression_loop_trend import (
    STAGE_SPECS,
    build_model_capability_regression_loop_trend,
    load_model_capability_regression_loop_reports,
    resolve_exit_code,
    write_model_capability_regression_loop_trend_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.generate_model_capability_regression_loop_trend_v1141 import main as cli_main


class ModelCapabilityRegressionLoopTrendTests(unittest.TestCase):
    def test_loop_trend_closes_complete_chain(self) -> None:
        report = build_model_capability_regression_loop_trend(_stage_entries())

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["summary"]["loop_closed"])
        self.assertEqual(report["summary"]["stage_count"], 5)
        self.assertEqual(report["summary"]["ready_stage_count"], 5)
        self.assertEqual(resolve_exit_code(report, require_loop_closed=True), 0)

    def test_loop_trend_detects_broken_chain_reference(self) -> None:
        entries = _stage_entries()
        entries[2]["report"]["source_inventory_path"] = "f/9999/wrong.json"
        report = build_model_capability_regression_loop_trend(entries)

        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["summary"]["loop_closed"])
        self.assertIn("source_paths_chain_back", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_loop_closed=True), 1)

    def test_loop_trend_detects_version_order_violation(self) -> None:
        entries = _stage_entries()
        entries[0], entries[1] = entries[1], entries[0]
        report = build_model_capability_regression_loop_trend(entries)

        self.assertEqual(report["status"], "fail")
        self.assertIn("version_order_strict", [issue["id"] for issue in report["issues"]])

    def test_loader_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_stage_artifacts(root)
            entries = load_model_capability_regression_loop_reports(root)
            report = build_model_capability_regression_loop_trend(entries)
            outputs = write_model_capability_regression_loop_trend_outputs(report, root / "out")
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-loop-closed", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _stage_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    previous_path = ""
    for spec in STAGE_SPECS:
        version_number = str(spec["version"]).removeprefix("v")
        path = f"f/{version_number}/解释/{spec['dir']}/{spec['json']}"
        report = _stage_report(spec, previous_path)
        entries.append({**spec, "path": path, "artifact_exists": True, "report": report})
        previous_path = path
    return entries


def _stage_report(spec: dict[str, object], previous_path: str) -> dict[str, object]:
    ready_key = str(spec["ready_key"])
    source_key = str(spec["source_key"])
    summary = {
        ready_key: True,
        "next_step": spec["next_step"],
        "promotion_ready": False,
        "model_quality_claim": f"{spec['stage']}_only",
    }
    report: dict[str, object] = {
        "status": "pass",
        "decision": f"{spec['stage']}_ready",
        "summary": summary,
    }
    if previous_path:
        report[source_key] = previous_path
    else:
        report[source_key] = "f/1133/解释/model-capability-cadence-v1133/model_capability_cadence_v1133.json"
    return report


def _write_stage_artifacts(root: Path) -> None:
    previous_path = ""
    for spec in STAGE_SPECS:
        version_number = str(spec["version"]).removeprefix("v")
        path = root / "f" / version_number / "解释" / str(spec["dir"]) / str(spec["json"])
        relative_path = Path("f") / version_number / "解释" / str(spec["dir"]) / str(spec["json"])
        report = _stage_report(spec, previous_path)
        write_json_payload(report, path)
        previous_path = relative_path.as_posix()


if __name__ == "__main__":
    unittest.main()
