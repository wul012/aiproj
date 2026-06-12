from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_cadence import (
    build_model_capability_cadence_report,
    resolve_exit_code,
    write_model_capability_cadence_outputs,
    write_model_capability_cadence_watch_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.evaluation.check_model_capability_cadence_v1133 import main as cli_main
from scripts.generate_model_capability_cadence_watch_v1142 import main as watch_cli_main


class ModelCapabilityCadenceTests(unittest.TestCase):
    def test_cadence_passes_when_model_version_is_recent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_readme(root, ["benchmark scorecard required term loss signal", "publication receipt lookup-only"])
            report = build_model_capability_cadence_report(root, max_non_capability_run=2)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["latest_model_capability_version"], "v200")
        self.assertEqual(resolve_exit_code(report, require_ready=True), 0)

    def test_cadence_watches_long_governance_or_maintenance_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_readme(root, ["publication receipt lookup-only", "readability maintenance", "contract check review"])
            report = build_model_capability_cadence_report(root, max_non_capability_run=1)

        self.assertEqual(report["status"], "watch")
        self.assertEqual(report["summary"]["next_action"], "schedule_model_capability_regression")
        self.assertEqual(resolve_exit_code(report, require_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_within_cadence=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_readme(root, ["publication receipt lookup-only", "benchmark scorecard required term"])
            report = build_model_capability_cadence_report(root)
            outputs = write_model_capability_cadence_outputs(report, root / "out")
            exit_code = cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-ready", "--force"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})

    def test_cadence_due_list_follows_closed_regression_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_readme(root, ["model capability regression loop trend", "dedup refactor shared helper"], start_version=1141)
            _write_explanation(root, 1141)
            _write_evidence(root, 1141)
            _write_loop_trend(root, loop_closed=True)
            report = build_model_capability_cadence_report(root, max_non_capability_run=2)

        self.assertEqual(report["summary"]["due_count"], 1)
        self.assertEqual(report["summary"]["next_action"], "run_selected_model_capability_regression_execution")
        self.assertEqual(report["due"][0]["action"], "run_selected_model_capability_regression_execution")

    def test_cadence_due_list_can_be_empty_when_slots_are_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_readme(root, ["dedup refactor shared helper", "benchmark scorecard required term loss signal"], start_version=200)
            _write_explanation(root, 200)
            _write_evidence(root, 200)
            report = build_model_capability_cadence_report(root, max_non_capability_run=2)
            outputs = write_model_capability_cadence_watch_outputs(report, root / "out")
            exit_code = watch_cli_main(["--root", str(root), "--out-dir", str(root / "cli-out"), "--require-ready", "--force"])

        self.assertEqual(report["summary"]["due_count"], 0)
        self.assertEqual(report["summary"]["due_list"], "none")
        self.assertEqual(exit_code, 0)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})


def _write_readme(root: Path, bodies: list[str], *, start_version: int = 200) -> None:
    sections = []
    version = start_version
    for body in bodies:
        sections.append(f"## Latest v{version} checkpoint\n\n- {body}\n")
        version -= 1
    (root / "README.md").write_text("# MiniGPT\n\n" + "\n".join(sections), encoding="utf-8")


def _write_explanation(root: Path, version: int) -> None:
    folder = root / "代码讲解记录_工程保养阶段"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"1-v{version}-demo.md").write_text("# demo\n", encoding="utf-8")


def _write_evidence(root: Path, version: int) -> None:
    folder = root / "f" / str(version)
    folder.mkdir(parents=True, exist_ok=True)


def _write_loop_trend(root: Path, *, loop_closed: bool) -> None:
    path = root / "f" / "1141" / "解释" / "model-capability-regression-loop-trend-v1141" / "model_capability_regression_loop_trend_v1141.json"
    write_json_payload({"summary": {"loop_closed": loop_closed}}, path)


if __name__ == "__main__":
    unittest.main()
