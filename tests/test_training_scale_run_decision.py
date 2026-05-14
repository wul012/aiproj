from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.training_scale_plan import build_training_scale_plan, write_training_scale_plan_outputs  # noqa: E402
from minigpt.training_scale_run import run_training_scale_plan  # noqa: E402
from minigpt.training_scale_run_comparison import (  # noqa: E402
    build_training_scale_run_comparison,
    write_training_scale_run_comparison_outputs,
)
from minigpt.training_scale_run_decision import (  # noqa: E402
    build_training_scale_run_decision,
    load_training_scale_run_comparison,
    render_training_scale_run_decision_html,
    render_training_scale_run_decision_markdown,
    write_training_scale_run_decision_outputs,
)


class TrainingScaleRunDecisionTests(unittest.TestCase):
    def test_selects_allowed_batch_run_and_builds_execute_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)

            report = build_training_scale_run_decision(
                comparison,
                generated_at="2026-05-14T00:00:00Z",
                python_executable="python",
            )

            self.assertEqual(report["decision_status"], "review")
            self.assertEqual(report["recommended_action"], "review_warnings_then_execute")
            self.assertEqual(report["selected_run"]["name"], "allowed")
            self.assertEqual(report["summary"]["candidate_count"], 1)
            self.assertEqual(report["summary"]["rejected_count"], 1)
            self.assertIn("--execute", report["execute_command"])
            self.assertIn("--gate-profile", report["execute_command"])
            self.assertIn("review", report["execute_command"])

    def test_require_gate_pass_blocks_warn_only_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)

            report = build_training_scale_run_decision(
                comparison,
                require_gate_pass=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["decision_status"], "blocked")
            self.assertIsNone(report["selected_run"])
            reasons = [reason for row in report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("gate is not pass", reasons)

    def test_min_readiness_can_block_low_score_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)

            report = build_training_scale_run_decision(
                comparison,
                min_readiness=90,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["decision_status"], "blocked")
            reasons = [reason for row in report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("readiness_score below 90", reasons)

    def test_write_outputs_load_directory_and_render_html_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root, names=["<allowed>", "blocked"])

            report = build_training_scale_run_decision(comparison.parent, generated_at="2026-05-14T00:00:00Z")
            outputs = write_training_scale_run_decision_outputs(report, root / "decision")
            loaded = load_training_scale_run_comparison(comparison.parent)
            markdown = render_training_scale_run_decision_markdown(report)
            html = render_training_scale_run_decision_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["markdown"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            self.assertEqual(loaded["schema_version"], 1)
            self.assertIn("## Execute command", markdown)
            self.assertIn("&lt;allowed&gt;", html)
            self.assertNotIn("<allowed>", html)
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)

    def test_rejects_comparison_without_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = root / "training_scale_run_comparison.json"
            comparison.write_text(json.dumps({"schema_version": 1, "runs": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                build_training_scale_run_decision(comparison)

    def _make_comparison(self, root: Path, names: list[str] | None = None) -> Path:
        source = root / "corpus.txt"
        source.write_text(("MiniGPT decision data.\n" * 40), encoding="utf-8")
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
            out_root=root / "allowed",
            gate_profile="review",
            generated_at="2026-05-14T00:00:00Z",
        )
        run_training_scale_plan(
            plan_outputs["json"],
            project_root=root,
            out_root=root / "blocked",
            gate_profile="standard",
            generated_at="2026-05-14T00:00:00Z",
        )
        comparison_report = build_training_scale_run_comparison(
            [root / "allowed" / "training_scale_run.json", root / "blocked" / "training_scale_run.json"],
            names=names or ["allowed", "blocked"],
            generated_at="2026-05-14T00:00:00Z",
        )
        outputs = write_training_scale_run_comparison_outputs(comparison_report, root / "comparison")
        return Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
