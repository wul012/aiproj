from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_type_analysis import (
    build_report,
    parse_diagnostics,
    validate_scope,
    write_report_outputs,
)


def _scope(targets: list[str], *, floor: int = 1) -> dict[str, object]:
    return {
        "schema_version": 1,
        "tool": "mypy",
        "scope_floor": floor,
        "targets": targets,
        "groups": {"test_group": targets},
    }


class TypeAnalysisTests(unittest.TestCase):
    def test_validate_scope_accepts_grouped_existing_python_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "typed.py"
            target.parent.mkdir(parents=True)
            target.write_text("VALUE: int = 1\n", encoding="utf-8")

            issues = validate_scope(_scope(["src/typed.py"]), root)

        self.assertEqual(issues, [])

    def test_validate_scope_rejects_floor_regression_and_undeclared_group_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typed.py"
            target.write_text("VALUE: int = 1\n", encoding="utf-8")
            scope = _scope(["typed.py"], floor=2)
            scope["groups"] = {"broken": ["typed.py", "missing.py"]}

            issues = validate_scope(scope, root)

        self.assertIn("target count 1 is below scope_floor 2", issues)
        self.assertIn("group broken references an undeclared target: missing.py", issues)

    def test_parse_diagnostics_supports_optional_column(self) -> None:
        output = "\n".join(
            [
                "src/minigpt/a.py:12:3: error: Wrong type [arg-type]",
                "scripts/b.py:8: error: Missing return [return]",
            ]
        )

        diagnostics = parse_diagnostics(output, Path.cwd())

        self.assertEqual([item["column"] for item in diagnostics], [3, 0])
        self.assertEqual([item["code"] for item in diagnostics], ["arg-type", "return"])

    def test_build_report_fails_on_mypy_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "typed.py"
            target.write_text("VALUE = 'bad'\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n", encoding="utf-8")
            scope_path = root / "scope.json"
            scope_path.write_text(json.dumps(_scope(["typed.py"])), encoding="utf-8")

            def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(command, 1, "typed.py:1:1: error: Bad assignment [assignment]\n", "")

            report = build_report(project_root=root, scope_path=scope_path, runner=fake_runner)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["diagnostic_count"], 1)
        self.assertEqual(report["diagnostics"][0]["code"], "assignment")

    def test_write_report_outputs_creates_reviewable_bundle(self) -> None:
        report = {
            "status": "pass",
            "decision": "continue_with_typed_scope",
            "scope_path": "scope.json",
            "summary": {
                "target_count": 1,
                "scope_floor": 1,
                "group_count": 1,
                "diagnostic_count": 0,
                "scope_issue_count": 0,
            },
            "targets": ["typed.py"],
            "scope_issues": [],
            "diagnostics": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_report_outputs(report, tmp)
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")

        self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
        self.assertIn("typed.py", markdown)


if __name__ == "__main__":
    unittest.main()
