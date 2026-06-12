from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_cadence import (
    build_model_capability_cadence_report,
    resolve_exit_code,
    write_model_capability_cadence_outputs,
)
from scripts.evaluation.check_model_capability_cadence_v1133 import main as cli_main


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


def _write_readme(root: Path, bodies: list[str]) -> None:
    sections = []
    version = 200
    for body in bodies:
        sections.append(f"## Latest v{version} checkpoint\n\n- {body}\n")
        version -= 1
    (root / "README.md").write_text("# MiniGPT\n\n" + "\n".join(sections), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
