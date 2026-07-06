from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_static_analysis import (
    build_report,
    compare_issues,
    load_baseline,
    main as static_analysis_main,
    write_report_outputs,
)


def _completed(
    command: list[str], return_code: int, stdout: object = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, return_code, json.dumps(stdout), stderr)


class StaticAnalysisTests(unittest.TestCase):
    def test_compare_issues_allows_existing_baseline_and_flags_new_source_line(self) -> None:
        baseline = [
            {
                "path": "scripts/example.py",
                "line": 1,
                "column": 1,
                "code": "F401",
                "message": "`os` imported but unused",
                "source_line": "import os",
            }
        ]
        current = baseline + [
            {
                "path": "scripts/example.py",
                "line": 2,
                "column": 1,
                "code": "F401",
                "message": "`sys` imported but unused",
                "source_line": "import sys",
            }
        ]

        comparison = compare_issues(baseline, current)

        self.assertEqual(comparison["new_issues"], [current[1]])
        self.assertEqual(comparison["resolved_issues"], [])

    def test_build_report_fails_on_strict_lint_issue_even_when_baselined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "strict.py"
            script.parent.mkdir(parents=True)
            script.write_text("import os\n", encoding="utf-8")
            baseline = root / "docs" / "static-analysis" / "ruff-baseline.json"
            baseline.parent.mkdir(parents=True)
            issue = {
                "filename": str(script),
                "location": {"row": 1, "column": 1},
                "code": "F401",
                "message": "`os` imported but unused",
            }
            baseline.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "tool": "ruff",
                        "targets": ["scripts"],
                        "strict_paths": ["scripts/strict.py"],
                        "issues": [
                            {
                                "path": "scripts/strict.py",
                                "line": 1,
                                "column": 1,
                                "code": "F401",
                                "message": "`os` imported but unused",
                                "source_line": "import os",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if "format" in command:
                    return _completed(command, 0, "")
                return _completed(command, 1, [issue])

            report = build_report(project_root=root, baseline_path=baseline, targets=("scripts",), runner=fake_runner)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["new_issue_count"], 0)
        self.assertEqual(report["summary"]["strict_lint_issue_count"], 1)

    def test_build_report_fails_when_format_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = root / "baseline.json"
            baseline.write_text(
                json.dumps({"schema_version": 1, "tool": "ruff", "strict_paths": ["scripts/strict.py"], "issues": []}),
                encoding="utf-8",
            )

            def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if "format" in command:
                    return _completed(command, 1, "", "would reformat")
                return _completed(command, 0, [])

            report = build_report(project_root=root, baseline_path=baseline, targets=("scripts",), runner=fake_runner)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["strict_format_status"], "fail")

    def test_cli_update_baseline_writes_report_and_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "scripts" / "loose.py"
            script.parent.mkdir(parents=True)
            script.write_text("import os\n", encoding="utf-8")
            baseline = root / "docs" / "static-analysis" / "ruff-baseline.json"
            out_dir = root / "out"
            issue = {
                "filename": str(script),
                "location": {"row": 1, "column": 1},
                "code": "F401",
                "message": "`os` imported but unused",
            }

            def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if "format" in command:
                    return _completed(command, 0, "")
                return _completed(command, 1, [issue])

            from scripts import check_static_analysis

            original_runner = check_static_analysis.subprocess.run
            check_static_analysis.subprocess.run = fake_runner
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exit_code = static_analysis_main(
                        [
                            "scripts",
                            "--project-root",
                            str(root),
                            "--baseline",
                            str(baseline),
                            "--out-dir",
                            str(out_dir),
                            "--update-baseline",
                            "--no-format-check",
                        ]
                    )
            finally:
                check_static_analysis.subprocess.run = original_runner

            payload = load_baseline(baseline)
            report = json.loads((out_dir / "static_analysis.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["issue_count"], 1)
        self.assertEqual(report["summary"]["current_issue_count"], 1)

    def test_write_report_outputs_creates_all_formats(self) -> None:
        report = {
            "title": "MiniGPT staged static analysis",
            "generated_at": "2026-01-01T00:00:00Z",
            "status": "pass",
            "decision": "continue_with_static_analysis_gate",
            "baseline_path": "docs/static-analysis/ruff-baseline.json",
            "summary": {
                "status": "pass",
                "decision": "continue_with_static_analysis_gate",
                "new_issue_count": 0,
            },
            "commands": [{"command": "python -m ruff check", "return_code": 0}],
            "new_issues": [],
            "strict_lint_issues": [],
            "resolved_baseline_issues": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_report_outputs(report, Path(tmp))

            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertIn("new_issue_count", Path(outputs["markdown"]).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
