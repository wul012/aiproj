from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            self.assertFalse(report["summary"]["decision_require_suite_consistency"])
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertTrue((root / "workflow" / "plan" / "training_scale_plan.json").exists())
            self.assertTrue((root / "workflow" / "runs" / "review" / "training_scale_run.json").exists())
            self.assertTrue((root / "workflow" / "comparison" / "training_scale_run_comparison.json").exists())
            self.assertTrue((root / "workflow" / "decision" / "training_scale_run_decision.json").exists())
            self.assertTrue((root / "workflow" / "training_scale_workflow.html").exists())
            self.assertIn("--execute", report["execute_command_text"])

    def test_workflow_can_use_builtin_standard_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                baseline_profile="review",
                suite_name="standard-zh",
                generated_at="2026-05-14T00:00:00Z",
                python_executable="python",
            )

            self.assertEqual(report["plan_summary"]["suite_mode"], "builtin")
            self.assertEqual(report["plan_summary"]["suite_name"], "standard-zh")
            self.assertEqual(report["plan_summary"]["suite_path"], "builtin:standard-zh")
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            plan_payload = json.loads(Path(report["plan_outputs"]["json"]).read_text(encoding="utf-8"))
            self.assertIn("--suite-name", plan_payload["batch"]["command"])
            self.assertIn("standard-zh", plan_payload["batch"]["command"])
            self.assertIn("builtin:standard-zh", report["summary"]["suite_path"])

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

    def test_workflow_passes_suite_consistency_guard_to_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                decision_require_suite_consistency=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertTrue(report["decision_require_suite_consistency"])
            self.assertTrue(report["summary"]["decision_require_suite_consistency"])
            self.assertTrue(report["decision_summary"]["require_suite_consistency"])
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertNotEqual(report["summary"]["decision_status"], "blocked")
            decision_payload = json.loads(Path(report["decision_outputs"]["json"]).read_text(encoding="utf-8"))
            self.assertTrue(decision_payload["require_suite_consistency"])

    def test_workflow_can_require_clean_batch_review_for_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            default_report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "default-workflow",
                profiles=["review", "standard"],
                baseline_profile="review",
                generated_at="2026-05-14T00:00:00Z",
                python_executable="python",
            )
            strict_report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "strict-workflow",
                profiles=["review", "standard"],
                baseline_profile="review",
                decision_require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
                python_executable="python",
            )

            self.assertEqual(default_report["summary"]["decision_status"], "review")
            self.assertFalse(default_report["summary"]["decision_require_clean_batch_review"])
            self.assertEqual(default_report["summary"]["clean_batch_review_status"], "review")
            self.assertEqual(default_report["summary"]["batch_maturity_ci_regression_count"], 0)
            self.assertEqual(strict_report["summary"]["decision_status"], "blocked")
            self.assertTrue(strict_report["decision_require_clean_batch_review"])
            self.assertTrue(strict_report["summary"]["decision_require_clean_batch_review"])
            self.assertEqual(strict_report["summary"]["clean_batch_review_status"], "review")
            self.assertEqual(strict_report["summary"]["batch_maturity_ci_regression_count"], 0)
            self.assertIsNone(strict_report["summary"]["selected_profile"])
            self.assertEqual(strict_report["decision_summary"]["candidate_count"], 0)
            self.assertTrue(any("Resolve workflow batch review" in item for item in strict_report["recommendations"]))
            decision_payload = json.loads(Path(strict_report["decision_outputs"]["json"]).read_text(encoding="utf-8"))
            self.assertTrue(decision_payload["require_clean_batch_review"])
            self.assertEqual(decision_payload["summary"]["clean_batch_review_status"], "review")

    def test_workflow_carries_decision_batch_ci_regressions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            import minigpt.training_scale_workflow as workflow_module  # noqa: PLC0415

            real_builder = workflow_module.build_training_scale_run_decision

            def builder_with_ci_regressions(*args: object, **kwargs: object) -> dict[str, object]:
                payload = real_builder(*args, **kwargs)
                summary = dict(payload["summary"])
                summary["selected_batch_maturity_ci_regression_count"] = 1
                summary["batch_maturity_ci_regression_count"] = 2
                summary["batch_maturity_ci_regression_names"] = ["review", "standard"]
                payload["summary"] = summary
                return payload

            with patch("minigpt.training_scale_workflow.build_training_scale_run_decision", side_effect=builder_with_ci_regressions):
                report = run_training_scale_workflow(
                    [source],
                    project_root=root,
                    out_root=root / "workflow",
                    profiles=["review", "standard"],
                    baseline_profile="review",
                    generated_at="2026-05-14T00:00:00Z",
                    python_executable="python",
                )
            markdown = render_training_scale_workflow_markdown(report)
            html = render_training_scale_workflow_html(report)
            outputs = write_training_scale_workflow_outputs(report, root / "export")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")

            summary = report["summary"]
            self.assertEqual(summary["selected_batch_maturity_ci_regression_count"], 1)
            self.assertEqual(summary["batch_maturity_ci_regression_count"], 2)
            self.assertEqual(summary["batch_maturity_ci_regression_names"], ["review", "standard"])
            self.assertIn("Batch CI regressions", markdown)
            self.assertIn("Batch CI-regressed names", markdown)
            self.assertIn("Batch CI regressions", html)
            self.assertIn("batch_maturity_ci_regression_count", csv_text)
            self.assertIn("review;standard", csv_text)

    def test_workflow_clean_batch_fields_are_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_source(root)

            report = run_training_scale_workflow(
                [source],
                project_root=root,
                out_root=root / "workflow",
                profiles=["review", "standard"],
                decision_require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_training_scale_workflow_outputs(report, root / "export")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = render_training_scale_workflow_markdown(report)
            html = render_training_scale_workflow_html(report)

            self.assertIn("decision_require_clean_batch_review", csv_text)
            self.assertIn("clean_batch_review_status", csv_text)
            self.assertIn("Require clean batch review", markdown)
            self.assertIn("Clean batch review status", markdown)
            self.assertIn("Require clean batch review", html)
            self.assertIn("Clean batch review", html)

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
