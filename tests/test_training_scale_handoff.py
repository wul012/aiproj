from __future__ import annotations

import json
import subprocess
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
from minigpt.training_scale_handoff_artifacts import (  # noqa: E402
    render_training_scale_handoff_html as render_handoff_artifact_html,
    render_training_scale_handoff_markdown as render_handoff_artifact_markdown,
    write_training_scale_handoff_outputs as write_handoff_artifact_outputs,
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
            self.assertEqual(report["summary"]["selected_batch_review_status"], "review")
            self.assertEqual(report["summary"]["selected_batch_comparison_review_action_count"], 2)
            self.assertTrue(any("Review selected batch comparison actions" in item for item in report["recommendations"]))

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
            self.assertIn("Selected batch review status", markdown)
            self.assertIn("Batch comparison reviews", markdown)
            self.assertIn("Batch review status", html)
            self.assertIn("&lt;handoff&gt;", html)
            self.assertNotIn("<handoff>", html)

    def test_carries_suite_guard_from_workflow_and_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(
                root,
                decision_status="ready",
                require_suite_consistency=True,
                suite_consistency="consistent",
                suite_mismatch_count=0,
                selected_suite_path=str(root / "suite" / "standard-zh.json"),
            )

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")
            markdown = render_training_scale_handoff_markdown(report)
            html = render_training_scale_handoff_html(report)
            outputs = write_training_scale_handoff_outputs(report, root / "handoff")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")

            self.assertTrue(report["suite_guard"]["decision_require_suite_consistency"])
            self.assertEqual(report["summary"]["decision_require_suite_consistency"], True)
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertEqual(report["summary"]["suite_mismatch_count"], 0)
            self.assertIn("Require suite consistency", markdown)
            self.assertIn("Require suite consistency", html)
            self.assertIn("decision_require_suite_consistency", csv_text)
            self.assertIn("suite_consistency", csv_text)

    def test_carries_workflow_clean_batch_review_guard_into_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(
                root,
                decision_status="review",
                require_clean_batch_review=True,
                clean_batch_review_status="review",
            )

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")

            self.assertTrue(report["clean_batch_review_guard"]["decision_require_clean_batch_review"])
            self.assertFalse(report["handoff_allowed"])
            self.assertEqual(report["summary"]["handoff_status"], "blocked")
            self.assertIn("requires clean batch-review evidence", report["blocked_reason"])
            self.assertTrue(report["summary"]["decision_require_clean_batch_review"])
            self.assertTrue(report["summary"]["require_clean_batch_review"])
            self.assertEqual(report["summary"]["clean_batch_review_status"], "review")
            self.assertTrue(any("workflow clean batch-review requirement" in item for item in report["recommendations"]))

    def test_clean_batch_review_guard_fields_are_rendered_and_printed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(
                root,
                decision_status="review",
                require_clean_batch_review=True,
                clean_batch_review_status="review",
            )

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")
            markdown = render_training_scale_handoff_markdown(report)
            html = render_training_scale_handoff_html(report)
            outputs = write_training_scale_handoff_outputs(report, root / "handoff")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/execute_training_scale_handoff.py",
                    str(workflow),
                    "--out-dir",
                    str(root / "script-handoff"),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("decision_require_clean_batch_review", csv_text)
            self.assertIn("clean_batch_review_status", csv_text)
            self.assertIn("Require clean batch review", markdown)
            self.assertIn("Clean batch review status", markdown)
            self.assertIn("Require clean batch review", html)
            self.assertIn("Clean batch review", html)
            self.assertIn("clean_batch_review_status=review", completed.stdout)

    def test_selected_batch_blocker_is_carried_into_handoff_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="review", selected_batch_review_status="blocker")

            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")

            self.assertTrue(report["handoff_allowed"])
            self.assertEqual(report["summary"]["selected_batch_review_status"], "blocker")
            self.assertEqual(report["summary"]["selected_batch_comparison_blocker_action_count"], 1)
            self.assertTrue(any("Resolve selected batch comparison blocker actions" in item for item in report["recommendations"]))

    def test_artifact_module_matches_legacy_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self._write_workflow(root, decision_status="ready")
            report = build_training_scale_handoff(workflow, generated_at="2026-05-14T00:00:00Z")

            legacy_outputs = write_training_scale_handoff_outputs(report, root / "legacy")
            artifact_outputs = write_handoff_artifact_outputs(report, root / "artifact")

            self.assertEqual(render_training_scale_handoff_markdown(report), render_handoff_artifact_markdown(report))
            self.assertEqual(render_training_scale_handoff_html(report), render_handoff_artifact_html(report))
            self.assertEqual(
                Path(legacy_outputs["csv"]).read_text(encoding="utf-8"),
                Path(artifact_outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("training_scale_handoff.html", artifact_outputs["html"])

    def _write_workflow(
        self,
        root: Path,
        *,
        decision_status: str,
        command: list[str] | None = None,
        title: str = "MiniGPT workflow",
        require_suite_consistency: bool = False,
        suite_consistency: str | None = None,
        suite_mismatch_count: int | None = None,
        selected_suite_path: str | None = None,
        require_clean_batch_review: bool = False,
        clean_batch_review_status: str | None = None,
        selected_batch_review_status: str = "review",
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
                "require_suite_consistency": require_suite_consistency,
                "suite_consistency": suite_consistency,
                "suite_mismatch_count": suite_mismatch_count,
                "selected_suite_path": selected_suite_path,
                "require_clean_batch_review": require_clean_batch_review,
                "clean_batch_review_status": clean_batch_review_status or selected_batch_review_status,
                "selected_batch_review_status": selected_batch_review_status,
                "selected_batch_comparison_review_action_count": 2 if selected_batch_review_status in {"review", "blocker"} else 0,
                "selected_batch_comparison_blocker_action_count": 1 if selected_batch_review_status == "blocker" else 0,
                "selected_batch_maturity_coverage_regression_count": 1 if selected_batch_review_status in {"review", "blocker"} else 0,
                "batch_comparison_review_action_count": 2 if selected_batch_review_status in {"review", "blocker"} else 0,
                "batch_comparison_blocker_action_count": 1 if selected_batch_review_status == "blocker" else 0,
                "batch_maturity_coverage_regression_count": 1 if selected_batch_review_status in {"review", "blocker"} else 0,
                "batch_comparison_blocker_reasons": ["coverage-regressed"] if selected_batch_review_status == "blocker" else [],
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
                "decision_require_suite_consistency": require_suite_consistency,
                "suite_consistency": suite_consistency,
                "suite_mismatch_count": suite_mismatch_count,
                "selected_suite_path": selected_suite_path,
                "suite_name": "standard-zh" if selected_suite_path else None,
                "suite_path": selected_suite_path,
                "decision_require_clean_batch_review": require_clean_batch_review,
                "clean_batch_review_status": clean_batch_review_status or selected_batch_review_status,
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
