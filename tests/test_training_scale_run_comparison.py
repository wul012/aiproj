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
    _comparison_summary,
    _run_summary,
    write_training_scale_run_comparison_outputs,
)
from minigpt.training_scale_run_comparison_artifacts import (  # noqa: E402
    render_training_scale_run_comparison_html as render_comparison_artifact_html,
    render_training_scale_run_comparison_markdown as render_comparison_artifact_markdown,
    write_training_scale_run_comparison_outputs as write_comparison_artifact_outputs,
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

    def test_artifact_module_matches_legacy_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed, blocked = self._make_allowed_and_blocked_runs(root)
            report = build_training_scale_run_comparison(
                [allowed, blocked],
                names=["allowed", "blocked"],
                generated_at="2026-05-14T00:00:00Z",
            )

            legacy_outputs = write_training_scale_run_comparison_outputs(report, root / "legacy")
            artifact_outputs = write_comparison_artifact_outputs(report, root / "artifact")

            self.assertEqual(render_training_scale_run_comparison_markdown(report), render_comparison_artifact_markdown(report))
            self.assertEqual(render_training_scale_run_comparison_html(report), render_comparison_artifact_html(report))
            self.assertEqual(
                Path(legacy_outputs["csv"]).read_text(encoding="utf-8"),
                Path(artifact_outputs["csv"]).read_text(encoding="utf-8"),
            )
            self.assertIn("training_scale_run_comparison.html", artifact_outputs["html"])

    def test_comparison_carries_batch_ci_regression_context_into_outputs(self) -> None:
        run_report = {
            "_source_path": "runs/ci-risk/training_scale_run.json",
            "status": "planned",
            "allowed": True,
            "execute": False,
            "gate_profile": "review",
            "gate": {"overall_status": "pass", "pass_count": 1, "warn_count": 0, "fail_count": 0},
            "scale_plan_summary": {
                "dataset_name": "sample",
                "version_prefix": "v1",
                "scale_tier": "tiny",
                "char_count": 120,
                "warning_count": 0,
                "variant_count": 2,
                "baseline": "base",
                "suite_path": "builtin:standard-zh",
                "suite_mode": "builtin",
                "suite_name": "standard-zh",
            },
            "batch_summary": {
                "status": "planned",
                "comparison_status": "written",
                "comparison_review_action_count": 2,
                "comparison_blocker_action_count": 1,
                "maturity_review_count": 2,
                "maturity_coverage_regression_count": 1,
                "maturity_coverage_regression_names": ["coverage-risk"],
                "maturity_suite_design_regression_count": 1,
                "maturity_suite_design_regression_names": ["suite-risk"],
                "maturity_ci_regression_count": 1,
                "maturity_ci_regression_names": ["ci-risk"],
                "maturity_ci_regression_reason_counts": {
                    "ci_failed_checks_increased": 2,
                    "ci_order_violations_increased": 1,
                },
                "comparison_blocker_reasons": ["best_score_ci_regressed"],
                "comparison_blocker_portfolios": ["ci-risk"],
                "completed_variant_count": 2,
            },
        }
        run = _run_summary(run_report, "ci-risk", 0)
        summary = _comparison_summary([run], run, [{"name": "ci-risk", "readiness_delta": 0, "suite_relation": "unchanged"}])
        report = {
            "title": "MiniGPT training scale run comparison",
            "generated_at": "2026-05-20T00:00:00Z",
            "run_count": 1,
            "baseline": run,
            "runs": [run],
            "baseline_deltas": [{"name": "ci-risk", "is_baseline": True, "explanation": "baseline"}],
            "summary": summary,
            "best_by_readiness": run,
            "recommendations": ["Review CI-regressed batch portfolios before treating scale-run readiness as clean automation evidence."],
        }

        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_training_scale_run_comparison_outputs(report, Path(tmp))
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = render_training_scale_run_comparison_markdown(report)
            html = render_training_scale_run_comparison_html(report)

        self.assertEqual(run["batch_maturity_ci_regression_count"], 1)
        self.assertEqual(run["batch_maturity_suite_design_regression_count"], 1)
        self.assertEqual(run["batch_maturity_suite_design_regression_names"], ["suite-risk"])
        self.assertEqual(run["batch_maturity_ci_regression_names"], ["ci-risk"])
        self.assertEqual(
            run["batch_maturity_ci_regression_reason_counts"],
            {"ci_failed_checks_increased": 2, "ci_order_violations_increased": 1},
        )
        self.assertEqual(summary["batch_maturity_ci_regression_count"], 1)
        self.assertEqual(summary["batch_maturity_suite_design_regression_count"], 1)
        self.assertEqual(summary["batch_maturity_suite_design_regression_names"], ["suite-risk"])
        self.assertEqual(summary["batch_maturity_ci_regression_names"], ["ci-risk"])
        self.assertEqual(
            summary["batch_maturity_ci_regression_reason_counts"],
            {"ci_failed_checks_increased": 2, "ci_order_violations_increased": 1},
        )
        self.assertIn("batch_maturity_ci_regression_count", csv_text)
        self.assertIn("batch_maturity_suite_design_regression_count", csv_text)
        self.assertIn("batch_maturity_ci_regression_reason_counts", csv_text)
        self.assertIn("ci_failed_checks_increased", csv_text)
        self.assertIn("Batch suite-design regressions", markdown)
        self.assertIn("Batch CI regressions", markdown)
        self.assertIn("Batch CI regression reasons", markdown)
        self.assertIn("ci_failed_checks_increased:2", markdown)
        self.assertIn("| ci-risk |", markdown)
        self.assertIn("CI regressions", html)
        self.assertIn("Suite-design regressions", html)
        self.assertIn("CI regression reasons", html)
        self.assertIn("ci_failed_checks_increased:2", html)

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
