from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_plan import build_training_scale_plan, write_training_scale_plan_outputs  # noqa: E402
from minigpt.training_scale_run import (  # noqa: E402
    render_training_scale_run_html,
    render_training_scale_run_markdown,
    run_training_scale_plan,
)


class TrainingScaleRunTests(unittest.TestCase):
    def test_review_gate_allows_warn_plan_and_runs_batch_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT gated scale run data.\n" * 40), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")

            report = run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="review",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertTrue(report["allowed"])
            self.assertEqual(report["status"], "planned_with_warnings")
            self.assertEqual(report["gate"]["overall_status"], "warn")
            self.assertEqual(report["batch_summary"]["status"], "planned")
            self.assertTrue((root / "run" / "batch" / "training_portfolio_batch.json").exists())
            self.assertTrue((root / "run" / "training_scale_run.json").exists())

    def test_warn_plan_can_be_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT blocked warn data.\n" * 35), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")

            report = run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="review",
                allow_warn=False,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertFalse(report["allowed"])
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["blocked_reason"], "gate warned and allow_warn is false")
            self.assertEqual(report["batch_summary"]["status"], "skipped")
            self.assertFalse((root / "run" / "batch" / "training_portfolio_batch.json").exists())

    def test_standard_gate_blocks_fail_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tiny.txt"
            source.write_text("tiny", encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")

            report = run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="standard",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertFalse(report["allowed"])
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["blocked_reason"], "gate failed")
            self.assertEqual(report["batch_summary"]["status"], "skipped")

    def test_allow_fail_forces_report_only_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tiny.txt"
            source.write_text("tiny", encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")

            report = run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="standard",
                allow_fail=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertTrue(report["allowed"])
            self.assertEqual(report["gate"]["overall_status"], "fail")
            self.assertEqual(report["batch_summary"]["status"], "planned")

    def test_renderers_escape_html_and_include_batch_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT render scale run data.\n" * 40), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                dataset_name="<demo>",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")
            report = run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="review",
                generated_at="2026-05-14T00:00:00Z",
            )

            markdown = render_training_scale_run_markdown(report)
            html = render_training_scale_run_html(report)

            self.assertIn("## Batch", markdown)
            self.assertIn("&lt;demo&gt;", html)
            self.assertNotIn("<demo>", html)

    def test_run_outputs_are_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT output scale run data.\n" * 40), encoding="utf-8")
            plan = build_training_scale_plan(
                [source],
                project_root=root,
                out_root=root / "scale",
                generated_at="2026-05-14T00:00:00Z",
            )
            plan_outputs = write_training_scale_plan_outputs(plan, root / "scale")
            run_training_scale_plan(
                plan_outputs["json"],
                project_root=root,
                out_root=root / "run",
                gate_profile="review",
                generated_at="2026-05-14T00:00:00Z",
            )

            payload = json.loads((root / "run" / "training_scale_run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertIn("gate_outputs", payload)
            self.assertIn("batch_outputs", payload)
            self.assertTrue((root / "run" / "training_scale_run.csv").exists())


if __name__ == "__main__":
    unittest.main()
