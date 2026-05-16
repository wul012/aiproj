from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import promoted_training_scale_seed_handoff as handoff_module  # noqa: E402
from minigpt import promoted_training_scale_seed_handoff_artifacts as artifact_module  # noqa: E402
from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff,
    render_promoted_training_scale_seed_handoff_html,
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_outputs,
)


class PromotedTrainingScaleSeedHandoffTests(unittest.TestCase):
    def test_artifact_functions_are_reexported_from_handoff_module(self) -> None:
        self.assertIs(
            handoff_module.render_promoted_training_scale_seed_handoff_html,
            artifact_module.render_promoted_training_scale_seed_handoff_html,
        )
        self.assertIs(
            handoff_module.render_promoted_training_scale_seed_handoff_markdown,
            artifact_module.render_promoted_training_scale_seed_handoff_markdown,
        )
        self.assertIs(
            handoff_module.write_promoted_training_scale_seed_handoff_outputs,
            artifact_module.write_promoted_training_scale_seed_handoff_outputs,
        )

    def test_validates_ready_seed_without_executing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(seed, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["handoff_status"], "planned")
            self.assertTrue(report["handoff_allowed"])
            self.assertFalse(report["execute"])
            self.assertIn("scripts/plan_training_scale.py", report["command"])
            self.assertEqual(report["summary"]["artifact_count"], 5)

    def test_blocks_review_when_allow_review_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, seed_status="review")

            report = build_promoted_training_scale_seed_handoff(
                seed,
                allow_review=False,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "blocked")
            self.assertFalse(report["handoff_allowed"])
            self.assertIn("allow_review is false", report["blocked_reason"])

    def test_execute_runs_plan_command_and_detects_plan_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "completed")
            self.assertEqual(report["execution"]["returncode"], 0)
            self.assertEqual(report["summary"]["available_artifact_count"], 5)
            self.assertEqual(report["summary"]["plan_status"], "available")
            self.assertTrue(report["summary"]["next_batch_command_available"])
            self.assertIn("run_training_portfolio_batch.py", report["next_batch_command_text"])
            self.assertTrue((root / "next-plan" / "training_scale_plan.json").exists())

    def test_execute_reports_failed_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, command=[sys.executable, "-c", "import sys; sys.exit(7)"])

            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["summary"]["handoff_status"], "failed")
            self.assertEqual(report["execution"]["returncode"], 7)

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root)

            report = build_promoted_training_scale_seed_handoff(
                seed.parent,
                title="<Handoff>",
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            markdown = render_promoted_training_scale_seed_handoff_markdown(report)
            html = render_promoted_training_scale_seed_handoff_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("## Command", markdown)
            self.assertIn("&lt;Handoff&gt;", html)
            self.assertNotIn("<Handoff>", html)


def write_seed_tree(root: Path, *, seed_status: str = "ready", command: list[str] | None = None) -> Path:
    source = root / "corpus.txt"
    source.write_text("MiniGPT v82 next cycle corpus.\n" * 180, encoding="utf-8")
    plan_out = root / "next-plan"
    batch_out = root / "batch"
    command = command or [
        sys.executable,
        "scripts/plan_training_scale.py",
        str(source),
        "--project-root",
        str(ROOT),
        "--out-dir",
        str(plan_out),
        "--batch-out-root",
        str(batch_out),
        "--dataset-name",
        "next-zh",
        "--dataset-version-prefix",
        "v82-test",
        "--max-variants",
        "1",
    ]
    seed = {
        "schema_version": 1,
        "title": "seed",
        "generated_at": "2026-05-14T00:00:00Z",
        "seed_status": seed_status,
        "baseline_seed": {
            "selected_name": "beta",
            "decision_status": "accepted" if seed_status != "blocked" else "blocked",
            "gate_status": "pass",
            "batch_status": "completed",
            "readiness_score": 107,
            "training_scale_run_path": str(root / "beta" / "training_scale_run.json"),
            "training_scale_run_exists": True,
        },
        "next_plan": {
            "project_root": str(ROOT),
            "dataset_name": "next-zh",
            "dataset_version_prefix": "v82-test",
            "plan_out_dir": str(plan_out),
            "batch_out_root": str(batch_out),
            "sources": [
                {
                    "path": str(source),
                    "resolved_path": str(source.resolve()),
                    "exists": True,
                    "kind": "file",
                }
            ],
            "command": command,
            "command_text": " ".join(command),
            "command_available": bool(command),
            "execution_ready": seed_status == "ready",
        },
        "summary": {
            "seed_status": seed_status,
            "selected_name": "beta",
            "command_available": bool(command),
        },
    }
    seed_path = root / "promoted-seed" / "promoted_training_scale_seed.json"
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    return seed_path


if __name__ == "__main__":
    unittest.main()
