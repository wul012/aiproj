from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_workflow import (  # noqa: E402
    render_training_scale_workflow_html,
    render_training_scale_workflow_markdown,
    run_training_scale_workflow,
    write_training_scale_workflow_outputs,
)
from minigpt.training_scale_workflow_artifacts import (  # noqa: E402
    render_training_scale_workflow_html as artifact_render_training_scale_workflow_html,
    write_training_scale_workflow_outputs as artifact_write_training_scale_workflow_outputs,
)


class TrainingScaleWorkflowTests(unittest.TestCase):
    def test_workflow_runs_plan_profiles_comparison_and_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                baseline_profile="review",
                generated_at="2026-05-14T00:00:00Z",
                python_executable="python",
            )

            self.assertEqual(report["summary"]["decision_status"], "review")
            self.assertEqual(report["summary"]["selected_profile"], "review")
            self.assertEqual(report["summary"]["allowed_count"], 1)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            self.assertTrue((root / "workflow" / "plan" / "training_scale_plan.json").exists())
            self.assertTrue((root / "workflow" / "runs" / "review" / "training_scale_run.json").exists())
            self.assertTrue((root / "workflow" / "comparison" / "training_scale_run_comparison.json").exists())
            self.assertTrue((root / "workflow" / "decision" / "training_scale_run_decision.json").exists())
            self.assertTrue((root / "workflow" / "training_scale_workflow.html").exists())
            self.assertIn("--execute", report["execute_command_text"])

    def test_strict_decision_blocks_warn_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                decision_require_gate_pass=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["decision_status"], "blocked")
            self.assertIsNone(report["summary"]["selected_profile"])
            self.assertEqual(report["decision_summary"]["candidate_count"], 0)

    def test_rejects_duplicate_profiles_and_missing_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            with self.assertRaises(ValueError):
                run_training_scale_workflow([source], project_root=root, out_root=root / "dup", profiles=["review", "review"])
            with self.assertRaises(ValueError):
                run_training_scale_workflow(
                    [source],
                    project_root=root,
                    out_root=root / "missing",
                    profiles=["review"],
                    baseline_profile="standard",
                )

    def test_renderers_escape_html_and_outputs_are_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                title="MiniGPT <workflow>",
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_training_scale_workflow_outputs(report, root / "export")
            markdown = render_training_scale_workflow_markdown(report)
            html = render_training_scale_workflow_html(report)

            self.assertIn("## Runs", markdown)
            self.assertIn("&lt;workflow&gt;", html)
            self.assertNotIn("<workflow>", html)
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertTrue(Path(outputs["csv"]).exists())

    def test_artifact_helpers_are_reexported_from_workflow_module(self) -> None:
        self.assertIs(render_training_scale_workflow_html, artifact_render_training_scale_workflow_html)
        self.assertIs(write_training_scale_workflow_outputs, artifact_write_training_scale_workflow_outputs)

    def _write_source(self, root: Path) -> Path:
        source = root / "corpus.txt"
        source.write_text(("MiniGPT workflow data.\n" * 40), encoding="utf-8")
        return source


if __name__ == "__main__":
    unittest.main()
