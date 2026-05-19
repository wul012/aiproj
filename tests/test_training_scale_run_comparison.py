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
    load_training_scale_run,
    render_training_scale_run_comparison_html,
    render_training_scale_run_comparison_markdown,
    write_training_scale_run_comparison_outputs,
)


class TrainingScaleRunComparisonTests(unittest.TestCase):
    def test_compare_allowed_and_blocked_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)

            report = build_training_scale_run_comparison(
                [allowed, blocked],
                names=["allowed", "blocked"],
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["run_count"], 2)
            self.assertEqual(report["summary"]["allowed_count"], 1)
            self.assertEqual(report["summary"]["blocked_count"], 1)
            self.assertEqual(report["summary"]["batch_started_count"], 1)
            self.assertEqual(report["summary"]["gate_fail_count"], 1)
            self.assertGreater(report["summary"]["batch_comparison_review_action_count"], 0)
            self.assertEqual(report["summary"]["batch_comparison_blocker_action_count"], 0)
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            blocked_delta = next(row for row in report["baseline_deltas"] if row["name"] == "blocked")
            self.assertLess(blocked_delta["readiness_delta"], 0)
            self.assertEqual(blocked_delta["batch_relation"], "regressed")

    def test_mixed_suite_runs_are_reported_as_not_clean_quality_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "corpus.txt"
            source.write_text(("MiniGPT mixed suite comparison data.\n" * 80), encoding="utf-8")
            default_run = self._make_run(root, source, "default-suite", suite_name=None)
            standard_run = self._make_run(root, source, "standard-suite", suite_name="standard-zh")

            report = build_training_scale_run_comparison(
                [default_run, standard_run],
                names=["default", "standard"],
                baseline="default",
                generated_at="2026-05-14T00:00:00Z",
            )

            standard_delta = next(row for row in report["baseline_deltas"] if row["name"] == "standard")
            self.assertEqual(report["summary"]["suite_consistency"], "mixed")
            self.assertEqual(report["summary"]["suite_mismatch_count"], 1)
            self.assertEqual(report["summary"]["suite_path_count"], 2)
            self.assertIn("builtin:standard-zh", report["summary"]["suite_paths"])
            self.assertEqual(standard_delta["suite_relation"], "changed")
            self.assertIn("suite", standard_delta["explanation"])
            self.assertTrue(any("different benchmark suites" in item for item in report["recommendations"]))

    def test_write_outputs_and_load_directory_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)

            report = build_training_scale_run_comparison(
                [allowed.parent, blocked.parent],
                names=["allowed", "blocked"],
                baseline="allowed",
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_training_scale_run_comparison_outputs(report, root / "comparison")

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertTrue(Path(outputs["html"]).exists())
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["baseline"]["name"], "allowed")
            loaded = load_training_scale_run(allowed.parent)
            self.assertEqual(loaded["schema_version"], 1)

    def test_best_by_readiness_prefers_allowed_batch_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)

            report = build_training_scale_run_comparison(
                [blocked, allowed],
                names=["blocked", "allowed"],
                baseline=0,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["baseline"]["name"], "blocked")
            self.assertEqual(report["best_by_readiness"]["name"], "allowed")
            allowed_delta = next(row for row in report["baseline_deltas"] if row["name"] == "allowed")
            self.assertGreater(allowed_delta["readiness_delta"], 0)

    def test_renderers_escape_html_and_include_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)
            report = build_training_scale_run_comparison(
                [allowed, blocked],
                names=["<allowed>", "blocked"],
                generated_at="2026-05-14T00:00:00Z",
            )

            markdown = render_training_scale_run_comparison_markdown(report)
            html = render_training_scale_run_comparison_html(report)

            self.assertIn("## Runs", markdown)
            self.assertIn("## Recommendations", markdown)
            self.assertIn("Batch comparison reviews", markdown)
            self.assertIn("&lt;allowed&gt;", html)
            self.assertIn("Batch reviews", html)
            self.assertNotIn("<allowed>", html)

    def test_rejects_duplicate_names_and_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)

            with self.assertRaises(ValueError):
                build_training_scale_run_comparison([])
            with self.assertRaises(ValueError):
                build_training_scale_run_comparison([allowed, blocked], names=["dup", "dup"])

    def _make_allowed_and_blocked_runs(self, root: Path) -> tuple[Path, Path]:
        source = root / "corpus.txt"
        source.write_text(("MiniGPT scale comparison data.\n" * 40), encoding="utf-8")
        allowed = self._make_run(root, source, "allowed", gate_profile="review")
        blocked = self._make_run(root, source, "blocked", gate_profile="standard")
        return allowed, blocked

    def _make_run(
        self,
        root: Path,
        source: Path,
        name: str,
        *,
        gate_profile: str = "review",
        suite_name: str | None = None,
    ) -> Path:
        plan = build_training_scale_plan(
            [source],
            project_root=root,
            out_root=root / f"scale-{name}",
            suite_name=suite_name,
            generated_at="2026-05-14T00:00:00Z",
        )
        plan_outputs = write_training_scale_plan_outputs(plan, root / f"scale-{name}")
        run_training_scale_plan(
            plan_outputs["json"],
            project_root=root,
            out_root=root / name,
            gate_profile=gate_profile,
            generated_at="2026-05-14T00:00:00Z",
        )
        return root / name / "training_scale_run.json"


if __name__ == "__main__":
    unittest.main()
