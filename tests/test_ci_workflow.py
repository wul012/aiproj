from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.ci_workflow_hygiene import (
    build_ci_workflow_hygiene_report,
    render_ci_workflow_hygiene_html,
    render_ci_workflow_hygiene_markdown,
    write_ci_workflow_hygiene_outputs,
)

CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class CIWorkflowTests(unittest.TestCase):
    def test_ci_uses_node24_native_action_versions(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)
        self.assertNotIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24", workflow)

    def test_ci_workflow_hygiene_report_passes_current_workflow(self) -> None:
        report = build_ci_workflow_hygiene_report(CI_WORKFLOW, project_root=ROOT, generated_at="2026-01-01T00:00:00Z")

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["decision"], "continue_with_node24_native_ci")
        self.assertEqual(report["summary"]["node24_native_action_count"], 2)
        self.assertEqual(report["summary"]["forbidden_env_count"], 0)
        self.assertEqual(report["summary"]["missing_step_count"], 0)
        self.assertEqual(report["summary"]["python_version"], "3.11")
        self.assertIn("actions/checkout", {item["repository"] for item in report["actions"]})
        self.assertTrue(all(item["status"] == "pass" for item in report["checks"]))

    def test_ci_workflow_hygiene_report_fails_old_runtime_policy(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "env:",
                        '  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"',
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v4",
                        "      - uses: actions/setup-python@v5",
                        "        with:",
                        '          python-version: "3.12"',
                        "      - name: Unit tests",
                        "        run: python -B -m unittest discover -s tests -v",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["decision"], "fix_ci_workflow_hygiene")
            self.assertGreaterEqual(report["summary"]["failed_check_count"], 4)
            self.assertEqual(report["summary"]["node24_native_action_count"], 0)
            self.assertEqual(report["summary"]["forbidden_env_count"], 1)
            self.assertEqual(report["summary"]["missing_step_count"], 2)
            self.assertIn("Upgrade required GitHub actions", " ".join(report["recommendations"]))

    def test_ci_workflow_hygiene_accepts_semver_and_bare_major_action_tags(self) -> None:
        with TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "ci.yml"
            workflow.write_text(
                "\n".join(
                    [
                        "name: ci",
                        "jobs:",
                        "  test:",
                        "    steps:",
                        "      - uses: actions/checkout@v6.0.0",
                        "      - uses: actions/setup-python@6",
                        "        with:",
                        '          python-version: "3.11"',
                        "      - name: Source encoding and syntax check",
                        "        run: python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-ci",
                        "      - name: CI workflow hygiene check",
                        "        run: python -B scripts/check_ci_workflow_hygiene.py --out-dir runs/ci-workflow-hygiene-ci",
                        "      - name: Unit tests",
                        "        run: python -B -m unittest discover -s tests -v",
                    ]
                ),
                encoding="utf-8",
            )

            report = build_ci_workflow_hygiene_report(workflow, project_root=Path(tmp), generated_at="2026-01-01T00:00:00Z")

            self.assertEqual(report["summary"]["status"], "fail")
            self.assertEqual(report["summary"]["node24_native_action_count"], 2)
            self.assertEqual(
                {item["version"]: item["node24_native"] for item in report["actions"]},
                {"v6.0.0": True, "6": True},
            )
            self.assertIn("Action version must be upgraded", " ".join(item["detail"] for item in report["checks"]))

    def test_ci_workflow_hygiene_outputs_json_csv_markdown_and_html(self) -> None:
        report = build_ci_workflow_hygiene_report(CI_WORKFLOW, project_root=ROOT, title="CI <workflow>", generated_at="2026-01-01T00:00:00Z")

        with TemporaryDirectory() as tmp:
            outputs = write_ci_workflow_hygiene_outputs(report, Path(tmp) / "out")

            for path in outputs.values():
                self.assertTrue(Path(path).exists())
            self.assertIn("actions/setup-python", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("CI &lt;workflow&gt;", render_ci_workflow_hygiene_html(report))
            self.assertIn("continue_with_node24_native_ci", render_ci_workflow_hygiene_markdown(report))


if __name__ == "__main__":
    unittest.main()
