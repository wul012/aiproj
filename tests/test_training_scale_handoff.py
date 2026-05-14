from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_handoff import (  # noqa: E402
    build_training_scale_handoff,
    load_training_scale_workflow,
    render_training_scale_handoff_html,
    render_training_scale_handoff_markdown,
    write_training_scale_handoff_outputs,
)


class TrainingScaleHandoffTests(unittest.TestCase):
    def test_validates_review_handoff_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="review")

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["handoff_status"], "planned")
            self.assertTrue(report["handoff_allowed"])
            self.assertFalse(report["execute"])
            self.assertIn("--execute", report["command"])
            self.assertEqual(report["summary"]["artifact_count"], 6)

    def test_blocks_review_when_allow_review_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="review")

            report = build_training_scale_handoff(
                workflow,
                allow_review=False,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "blocked")
            self.assertFalse(report["handoff_allowed"])
            self.assertIn("allow_review is false", report["blocked_reason"])

    def test_execute_runs_command_and_detects_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="ready", command=self._artifact_command(root))

            report = build_training_scale_handoff(
                workflow,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "completed")
            self.assertEqual(report["execution"]["returncode"], 0)
            self.assertGreaterEqual(report["summary"]["available_artifact_count"], 4)
            self.assertTrue((root / "execute" / "training_scale_run.json").exists())

    def test_execute_reports_failed_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="ready", command=[sys.executable, "-c", "import sys; sys.exit(7)", "--out-root", str(root / "execute")])

            report = build_training_scale_handoff(
                workflow,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "failed")
            self.assertEqual(report["execution"]["returncode"], 7)

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="ready", title="MiniGPT <handoff>")

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")
            report["title"] = "MiniGPT <handoff>"
            outputs = write_training_scale_handoff_outputs(report, root / "handoff")
            loaded = load_training_scale_workflow(workflow.parent)
            markdown = render_training_scale_handoff_markdown(report)
            html = render_training_scale_handoff_html(report)

            self.assertEqual(loaded["schema_version"], 1)
            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("## Command", markdown)
            self.assertIn("&lt;handoff&gt;", html)
            self.assertNotIn("<handoff>", html)

    def _write_workflow(
        self,
        root: Path,
        *,
        decision_status: str,
        command: list[str] | None = None,
        title: str = "MiniGPT workflow",
    ) -> Path:
        workflow_dir = root / "workflow"
        decision_dir = workflow_dir / "decision"
        decision_dir.mkdir(parents=True, exist_ok=True)
        command = command or [
            sys.executable,
            "-c",
            "print('planned only')",
            "--out-root",
            str(root / "execute"),
            "--execute",
        ]
        decision = {
            "schema_version": 1,
            "title": title,
            "decision_status": decision_status,
            "recommended_action": "execute_selected_run" if decision_status == "ready" else "review_warnings_then_execute",
            "execute_command": command,
            "execute_command_text": " ".join(command),
            "summary": {
                "decision_status": decision_status,
                "selected_run_name": "review",
                "recommended_action": "execute_selected_run",
            },
        }
        decision_path = decision_dir / "training_scale_run_decision.json"
        decision_path.write_text(json.dumps(decision, ensure_ascii=False), encoding="utf-8")
        workflow = {
            "schema_version": 1,
            "title": title,
            "project_root": str(root),
            "summary": {
                "decision_status": decision_status,
                "selected_profile": "review",
                "recommended_action": decision["recommended_action"],
            },
            "decision_outputs": {"json": str(decision_path)},
        }
        workflow_path = workflow_dir / "training_scale_workflow.json"
        workflow_path.write_text(json.dumps(workflow, ensure_ascii=False), encoding="utf-8")
        return workflow_path

    def _artifact_command(self, root: Path) -> list[str]:
        script = (
            "from pathlib import Path; "
            "import json, sys; "
            "out=Path(sys.argv[sys.argv.index('--out-root')+1]); "
            "(out/'batch'/'variants'/'smoke'/'runs'/'smoke').mkdir(parents=True, exist_ok=True); "
            "(out/'batch'/'variants'/'smoke').mkdir(parents=True, exist_ok=True); "
            "(out/'training_scale_run.json').write_text('{}'); "
            "(out/'training_scale_run.html').write_text('<html></html>'); "
            "(out/'batch'/'training_portfolio_batch.json').write_text('{}'); "
            "(out/'batch'/'training_portfolio_batch.html').write_text('<html></html>'); "
            "(out/'batch'/'variants'/'smoke'/'training_portfolio.json').write_text('{}'); "
            "(out/'batch'/'variants'/'smoke'/'runs'/'smoke'/'checkpoint.pt').write_text('checkpoint')"
        )
        return [sys.executable, "-c", script, "--out-root", str(root / "execute")]


if __name__ == "__main__":
    unittest.main()
