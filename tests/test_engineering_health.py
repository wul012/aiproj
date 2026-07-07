from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from scripts._bootstrap import HEALTH_ENGINEERING_ENTRYPOINTS
from scripts._engineering_health import (
    ENGINEERING_HEALTH_STEP_IDS,
    EngineeringHealthStep,
    EngineeringHealthStepResult,
    build_steps,
    build_summary,
    render_summary_markdown,
    write_summary,
    write_summary_outputs,
)
from scripts.check_engineering_health import run_steps


class EngineeringHealthTests(unittest.TestCase):
    def test_build_steps_runs_stable_health_gates_in_order(self) -> None:
        out_dir = ROOT / "runs" / "engineering-health-test"
        steps = build_steps(out_dir, python_executable="python")

        self.assertEqual(tuple(step.step_id for step in steps), ENGINEERING_HEALTH_STEP_IDS)
        self.assertEqual(tuple(step.command[2] for step in steps), HEALTH_ENGINEERING_ENTRYPOINTS)
        self.assertNotIn("scripts/run_test_coverage.py", HEALTH_ENGINEERING_ENTRYPOINTS)
        self.assertEqual(steps[0].command[:3], ("python", "-B", "scripts/check_source_encoding.py"))
        self.assertIn(str(out_dir / "source-encoding"), steps[0].command)
        self.assertEqual(steps[1].command[:3], ("python", "-B", "scripts/check_project_docs_readability.py"))
        self.assertIn(str(out_dir / "project-docs-readability"), steps[1].command)
        self.assertIn("--require-pass", steps[1].command)
        self.assertIn("--force", steps[1].command)
        self.assertEqual(steps[2].command[:3], ("python", "-B", "scripts/check_ci_workflow_hygiene.py"))
        self.assertIn(str(out_dir / "ci-workflow-hygiene"), steps[2].command)
        self.assertEqual(steps[3].command[:3], ("python", "-B", "scripts/check_static_analysis.py"))
        self.assertIn(str(out_dir / "static-analysis"), steps[3].command)
        self.assertEqual(steps[4].command[:3], ("python", "-B", "scripts/check_type_analysis.py"))
        self.assertIn(str(out_dir / "type-analysis"), steps[4].command)
        self.assertEqual(steps[5].command[:3], ("python", "-B", "scripts/check_model_capability_honest_measurement.py"))
        self.assertIn(str(out_dir / "model-capability-honest-measurement"), steps[5].command)
        self.assertEqual(steps[6].command[:3], ("python", "-B", "scripts/check_artifact_schema_guard.py"))
        self.assertIn(str(out_dir / "artifact-schema-guard"), steps[6].command)
        self.assertEqual(steps[7].command[:3], ("python", "-B", "scripts/check_file_size_ratchet.py"))
        self.assertIn(str(out_dir / "file-size-ratchet"), steps[7].command)
        self.assertEqual(steps[8].command, ("python", "-B", "scripts/check_normalization_guard.py"))

    def test_summary_records_step_statuses_and_output_path(self) -> None:
        out_dir = ROOT / "runs" / "engineering-health-test"
        results = (
            EngineeringHealthStepResult("source_encoding", ("python", "-B", "source.py"), 0),
            EngineeringHealthStepResult("normalization_guard", ("python", "-B", "guard.py"), 5),
        )
        summary = build_summary(results, out_dir)

        self.assertEqual(summary["status"], "fail")
        self.assertEqual(summary["decision"], "repair_engineering_health")
        self.assertEqual(summary["summary"]["step_count"], 2)
        self.assertEqual(summary["summary"]["passed_step_count"], 1)
        self.assertEqual(summary["summary"]["failed_step_count"], 1)
        self.assertEqual(summary["summary"]["first_failure_code"], 5)
        self.assertEqual(summary["steps"][0]["status"], "pass")
        self.assertEqual(summary["steps"][1]["status"], "fail")

    def test_write_summary_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            summary = build_summary((EngineeringHealthStepResult("ok", ("python",), 0),), target)
            path = write_summary(summary, target)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(path.name, "engineering_health_summary.json")
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["summary"]["first_failure_code"], 0)

    def test_summary_outputs_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            summary = build_summary((EngineeringHealthStepResult("ok", ("python", "-B", "ok.py"), 0),), target)
            markdown = render_summary_markdown(summary)
            outputs = write_summary_outputs(summary, target)

        self.assertIn("# MiniGPT engineering health summary", markdown)
        self.assertIn("| ok | pass | 0 |", markdown)
        self.assertEqual(set(outputs), {"json", "markdown"})
        self.assertTrue(outputs["json"].endswith("engineering_health_summary.json"))
        self.assertTrue(outputs["markdown"].endswith("engineering_health_summary.md"))

    def test_run_steps_runs_all_steps_and_returns_first_failure(self) -> None:
        steps = (
            EngineeringHealthStep("first", ("python", "-B", "first.py")),
            EngineeringHealthStep("second", ("python", "-B", "second.py")),
            EngineeringHealthStep("third", ("python", "-B", "third.py")),
        )
        calls: list[tuple[str, ...]] = []
        return_codes = iter([0, 7, 3])

        def fake_runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
            calls.append(tuple(command))
            return subprocess.CompletedProcess(command, next(return_codes))

        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            exit_code = run_steps(steps, runner=fake_runner, summary_out_dir=Path(tmp))
            summary_path = Path(tmp) / "engineering_health_summary.json"
            markdown_path = Path(tmp) / "engineering_health_summary.md"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            markdown_exists = markdown_path.is_file()

        self.assertEqual(exit_code, 7)
        self.assertEqual(calls, [step.command for step in steps])
        self.assertTrue(markdown_exists)
        self.assertEqual(summary["summary"]["first_failure_code"], 7)
        self.assertEqual([step["status"] for step in summary["steps"]], ["pass", "fail", "fail"])

    def test_cli_uses_shared_bootstrap_and_step_config(self) -> None:
        text = (ROOT / "scripts" / "check_engineering_health.py").read_text(encoding="utf-8")

        self.assertIn("_bootstrap", text)
        self.assertIn("_engineering_health", text)
        self.assertNotIn("Path(__file__).resolve()" + ".parents[1]", text)
        self.assertNotIn("sys.path" + ".insert", text)


if __name__ == "__main__":
    unittest.main()
