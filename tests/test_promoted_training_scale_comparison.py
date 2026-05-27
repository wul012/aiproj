from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from promoted_training_scale_comparison_fixtures import entry, make_index_tree  # noqa: E402

from minigpt import promoted_training_scale_comparison  # noqa: E402
from minigpt import promoted_training_scale_comparison_artifacts  # noqa: E402
from minigpt.promoted_training_scale_comparison import (  # noqa: E402
    build_promoted_training_scale_comparison,
    render_promoted_training_scale_comparison_html,
    render_promoted_training_scale_comparison_markdown,
    write_promoted_training_scale_comparison_outputs,
)


class PromotedTrainingScaleComparisonTests(unittest.TestCase):
    def test_comparison_module_reexports_artifact_writers(self) -> None:
        self.assertIs(
            promoted_training_scale_comparison.write_promoted_training_scale_comparison_outputs,
            promoted_training_scale_comparison_artifacts.write_promoted_training_scale_comparison_outputs,
        )
        self.assertIs(
            promoted_training_scale_comparison.render_promoted_training_scale_comparison_html,
            promoted_training_scale_comparison_artifacts.render_promoted_training_scale_comparison_html,
        )
        self.assertIs(
            promoted_training_scale_comparison.render_promoted_training_scale_comparison_markdown,
            promoted_training_scale_comparison_artifacts.render_promoted_training_scale_comparison_markdown,
        )

    def test_compares_only_promoted_runs_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("beta", "beta", "promoted", "pass"),
                    entry("review", "review", "review", "warn"),
                ],
                baseline_name="beta",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["comparison_status"], "compared")
            self.assertEqual(report["summary"]["promoted_count"], 2)
            self.assertEqual(report["summary"]["comparison_ready_count"], 2)
            self.assertEqual(report["summary"]["compared_run_count"], 2)
            self.assertEqual(report["summary"]["baseline_name"], "beta")
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertEqual([row["name"] for row in report["comparison"]["runs"]], ["alpha", "beta"])
            self.assertNotIn("review", [row["name"] for row in report["comparison"]["runs"]])
            self.assertFalse(report["blockers"])

    def test_mixed_promoted_run_suites_are_carried_to_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn", suite_name=None),
                    entry("beta", "beta", "promoted", "pass", suite_name="standard-zh"),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["comparison_status"], "compared")
            self.assertEqual(report["summary"]["suite_consistency"], "mixed")
            self.assertEqual(report["summary"]["suite_mismatch_count"], 1)
            self.assertTrue(any("different benchmark suites" in item for item in report["recommendations"]))
            beta = next(row for row in report["promotions"] if row["name"] == "beta")
            self.assertEqual(beta["suite_path"], "builtin:standard-zh")

    def test_carries_index_handoff_suite_guard_into_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn", include_handoff_suite_guard=True),
                    entry("beta", "beta", "promoted", "pass", include_handoff_suite_guard=True),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertTrue(row["handoff_require_suite_consistency"])
            self.assertEqual(row["handoff_suite_consistency"], "consistent")
            self.assertEqual(row["handoff_suite_mismatch_count"], 0)
            self.assertEqual(row["handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_require_suite_consistency_count"], 2)
            self.assertEqual(summary["handoff_suite_consistent_count"], 2)
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertEqual(summary["comparison_ready_handoff_suite_mismatch_total"], 0)
            self.assertIn("handoff_suite_consistency", csv_text)
            self.assertIn("Handoff Suite", markdown)
            self.assertIn("Comparison-ready handoff suite mismatches", markdown)
            self.assertIn("Handoff suite consistent", html)
            self.assertIn("Ready suite mismatches", html)
            self.assertIn("handoff_require_suite_consistency_count=2", completed.stdout)
            self.assertIn("handoff_suite_consistent_count=2", completed.stdout)
            self.assertIn("comparison_ready_handoff_suite_mismatch_total=0", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_carries_index_handoff_batch_review_context_into_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            row = report["promotions"][0]
            summary = report["summary"]
            self.assertEqual(row["handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(row["handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_review_action_total"], 4)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_comparison_blocker_action_total"], 1)
            self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertIn("handoff_selected_batch_review_status", csv_text)
            self.assertIn("Batch Review", markdown)
            self.assertIn("Comparison-ready selected batch blockers", markdown)
            self.assertIn("Batch Review", html)
            self.assertIn("comparison_ready_handoff_selected_batch_blocker_count=1", completed.stdout)
            self.assertIn("comparison_ready_handoff_batch_comparison_blocker_reasons", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_carries_clean_batch_review_guard_and_filters_unclean_promoted_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="review",
                    ),
                    entry(
                        "gamma",
                        "gamma",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=False,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            rows = {row["name"]: row for row in report["promotions"]}
            summary = report["summary"]
            self.assertTrue(rows["alpha"]["promoted_for_comparison"])
            self.assertFalse(rows["beta"]["promoted_for_comparison"])
            self.assertTrue(rows["gamma"]["promoted_for_comparison"])
            self.assertEqual([row["name"] for row in report["comparison"]["runs"]], ["alpha", "gamma"])
            self.assertEqual(summary["comparison_ready_count"], 2)
            self.assertEqual(summary["compared_run_count"], 2)
            self.assertEqual(rows["alpha"]["handoff_require_clean_batch_review"], True)
            self.assertEqual(rows["alpha"]["handoff_clean_batch_review_status"], "clean")
            self.assertEqual(rows["beta"]["handoff_clean_batch_review_status"], "review")
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 1)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_require_clean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_clean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_unclean_batch_review_count"], 0)
            self.assertIn("handoff_require_clean_batch_review", csv_text)
            self.assertIn("Clean Required", markdown)
            self.assertIn("Clean Status", markdown)
            self.assertIn("Ready clean-required", html)
            self.assertIn("handoff_require_clean_batch_review_count=2", completed.stdout)
            self.assertIn("comparison_ready_handoff_clean_batch_review_count=1", completed.stdout)
            self.assertIn("comparison_ready_handoff_unclean_batch_review_count=0", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_handoff_batch_ci_regression_explains_filtered_promoted_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                        batch_ci_regression_count=2,
                        batch_boundary_plan_regression_count=1,
                        batch_ci_regression_names=["beta-old-ci"],
                        batch_ci_regression_reason_counts={"missing-ci-step": 1, "workflow-order-regressed": 1},
                        selected_batch_ci_regression_count=1,
                        selected_batch_boundary_plan_regression_count=1,
                        selected_batch_ci_regression_reason_counts={"workflow-order-regressed": 1},
                    ),
                    entry(
                        "gamma",
                        "gamma",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            rows = {row["name"]: row for row in report["promotions"]}
            summary = report["summary"]
            self.assertTrue(rows["alpha"]["promoted_for_comparison"])
            self.assertFalse(rows["beta"]["promoted_for_comparison"])
            self.assertEqual(rows["beta"]["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(
                rows["beta"]["handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"],
                1,
            )
            self.assertEqual(rows["beta"]["handoff_batch_maturity_ci_regression_names"], ["beta-old-ci"])
            self.assertEqual(rows["beta"]["handoff_selected_batch_maturity_ci_regression_count"], 1)
            self.assertEqual(
                rows["beta"]["handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_count"],
                1,
            )
            self.assertEqual(
                rows["beta"]["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(
                rows["beta"]["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertIn("handoff batch CI regression count is 2", rows["beta"]["comparison_exclusion_reasons"])
            self.assertEqual([row["name"] for row in report["comparison"]["runs"]], ["alpha", "gamma"])
            self.assertEqual(summary["comparison_ready_count"], 2)
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 1)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(summary["handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"], 1)
            self.assertEqual(summary["handoff_selected_batch_maturity_ci_regression_total"], 1)
            self.assertEqual(
                summary["handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"],
                1,
            )
            self.assertEqual(
                summary["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(
                summary["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertEqual(summary["handoff_batch_maturity_ci_regression_names"], ["beta-old-ci"])
            self.assertEqual(summary["comparison_ready_handoff_batch_maturity_ci_regression_count"], 0)
            self.assertEqual(
                summary["comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count"],
                0,
            )
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_maturity_ci_regression_total"], 0)
            self.assertEqual(
                summary["comparison_ready_handoff_selected_batch_maturity_ci_boundary_plan_check_ready_regression_total"],
                0,
            )
            self.assertEqual(summary["comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"], {})
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts"], {})
            self.assertIn("handoff_batch_maturity_ci_regression_count", csv_text)
            self.assertIn("handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count", csv_text)
            self.assertIn("handoff_batch_maturity_ci_regression_reason_counts", csv_text)
            self.assertIn("missing-ci-step:1, workflow-order-regressed:1", csv_text)
            self.assertIn("comparison_exclusion_reasons", csv_text)
            self.assertIn("Handoff batch CI regressions", markdown)
            self.assertIn("Handoff batch CI boundary plan-check regressions", markdown)
            self.assertIn("Handoff batch CI regression reasons", markdown)
            self.assertIn("Handoff CI boundary plan", html)
            self.assertIn("Comparison-ready handoff batch CI regression reasons", markdown)
            self.assertIn("workflow-order-regressed:1", markdown)
            self.assertIn("CI Regressions", markdown)
            self.assertIn("Handoff CI regressions", html)
            self.assertIn("Handoff CI reasons", html)
            self.assertIn("Ready CI reasons", html)
            self.assertIn("missing-ci-step:1, workflow-order-regressed:1", " ".join(report["recommendations"]))
            self.assertIn("handoff_batch_maturity_ci_regression_count=2", completed.stdout)
            self.assertIn(
                "handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count=1",
                completed.stdout,
            )
            self.assertIn(
                'handoff_batch_maturity_ci_regression_reason_counts={"missing-ci-step": 1, "workflow-order-regressed": 1}',
                completed.stdout,
            )
            self.assertIn(
                'handoff_selected_batch_maturity_ci_regression_reason_counts={"workflow-order-regressed": 1}',
                completed.stdout,
            )
            self.assertIn("comparison_ready_handoff_batch_maturity_ci_regression_count=0", completed.stdout)
            self.assertIn(
                "comparison_ready_handoff_batch_maturity_ci_boundary_plan_check_ready_regression_count=0",
                completed.stdout,
            )
            self.assertIn("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts={}", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_handoff_batch_suite_design_regression_explains_filtered_promoted_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                        batch_suite_design_regression_count=2,
                        batch_suite_design_regression_names=["beta-suite", "standard"],
                        selected_batch_suite_design_regression_count=1,
                        selected_batch_suite_design_regression_names=["beta-suite"],
                    ),
                    entry(
                        "gamma",
                        "gamma",
                        "promoted",
                        "pass",
                        include_handoff_suite_guard=True,
                        include_handoff_batch_review_context=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")
            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "compare_promoted_training_scale_runs.py"),
                    str(index_dir),
                    "--out-dir",
                    str(script_out),
                    "--require-compared",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            rows = {row["name"]: row for row in report["promotions"]}
            summary = report["summary"]
            self.assertTrue(rows["alpha"]["promoted_for_comparison"])
            self.assertFalse(rows["beta"]["promoted_for_comparison"])
            self.assertEqual(rows["beta"]["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(rows["beta"]["handoff_batch_maturity_suite_design_regression_names"], ["beta-suite", "standard"])
            self.assertEqual(rows["beta"]["handoff_selected_batch_maturity_suite_design_regression_count"], 1)
            self.assertEqual(rows["beta"]["handoff_selected_batch_maturity_suite_design_regression_names"], ["beta-suite"])
            self.assertIn("handoff batch suite-design regression count is 2", rows["beta"]["comparison_exclusion_reasons"])
            self.assertEqual([row["name"] for row in report["comparison"]["runs"]], ["alpha", "gamma"])
            self.assertEqual(summary["comparison_ready_count"], 2)
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 1)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(summary["handoff_selected_batch_maturity_suite_design_regression_total"], 1)
            self.assertEqual(summary["handoff_batch_maturity_suite_design_regression_names"], ["beta-suite", "standard"])
            self.assertEqual(summary["handoff_selected_batch_maturity_suite_design_regression_names"], ["beta-suite"])
            self.assertEqual(summary["comparison_ready_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"], 0)
            self.assertEqual(summary["comparison_ready_handoff_batch_maturity_suite_design_regression_names"], [])
            self.assertIn("handoff_batch_maturity_suite_design_regression_count", csv_text)
            self.assertIn("beta-suite;standard", csv_text)
            self.assertIn("comparison_exclusion_reasons", csv_text)
            self.assertIn("Handoff batch suite-design regressions", markdown)
            self.assertIn("Comparison-ready handoff batch suite-design regressions", markdown)
            self.assertIn("Suite-Design Regressions", markdown)
            self.assertIn("Handoff suite-design regressions", html)
            self.assertIn("Ready suite-design regressions", html)
            self.assertIn("Suite-design-regressed handoff batch evidence", " ".join(report["recommendations"]))
            self.assertIn("handoff_batch_maturity_suite_design_regression_count=2", completed.stdout)
            self.assertIn('handoff_batch_maturity_suite_design_regression_names=["beta-suite", "standard"]', completed.stdout)
            self.assertIn("handoff_selected_batch_maturity_suite_design_regression_total=1", completed.stdout)
            self.assertIn('handoff_selected_batch_maturity_suite_design_regression_names=["beta-suite"]', completed.stdout)
            self.assertIn("comparison_ready_handoff_batch_maturity_suite_design_regression_count=0", completed.stdout)
            self.assertIn('comparison_ready_handoff_batch_maturity_suite_design_regression_names=[]', completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_comparison.json").exists())

    def test_comparison_layer_blocks_stale_ci_regressed_clean_required_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                        batch_ci_regression_count=1,
                        batch_ci_regression_names=["stale-ci"],
                        batch_ci_regression_reason_counts={"workflow-status-regressed": 1},
                        force_compare_ready=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            rows = {row["name"]: row for row in report["promotions"]}
            self.assertTrue(rows["alpha"]["promoted_for_comparison"])
            self.assertFalse(rows["beta"]["promoted_for_comparison"])
            self.assertEqual(report["comparison_status"], "blocked")
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_ci_regression_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_ci_regression_reason_counts"], {"workflow-status-regressed": 1})
            self.assertEqual(report["summary"]["handoff_unclean_batch_review_count"], 1)
            self.assertIn("handoff batch CI regression count is 1", rows["beta"]["comparison_exclusion_reasons"])
            self.assertTrue(
                any("workflow-status-regressed:1" in item for item in report["recommendations"])
            )

    def test_comparison_layer_blocks_stale_suite_design_regressed_clean_required_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry(
                        "alpha",
                        "alpha",
                        "promoted",
                        "warn",
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                    ),
                    entry(
                        "beta",
                        "beta",
                        "promoted",
                        "pass",
                        require_clean_batch_review=True,
                        clean_batch_review_status="clean",
                        batch_suite_design_regression_count=1,
                        batch_suite_design_regression_names=["stale-suite"],
                        force_compare_ready=True,
                    ),
                ],
                baseline_name="alpha",
            )

            report = build_promoted_training_scale_comparison(index_dir, generated_at="2026-05-14T00:00:00Z")

            rows = {row["name"]: row for row in report["promotions"]}
            self.assertTrue(rows["alpha"]["promoted_for_comparison"])
            self.assertFalse(rows["beta"]["promoted_for_comparison"])
            self.assertEqual(report["comparison_status"], "blocked")
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_suite_design_regression_count"], 1)
            self.assertEqual(report["summary"]["handoff_batch_maturity_suite_design_regression_names"], ["stale-suite"])
            self.assertEqual(report["summary"]["handoff_unclean_batch_review_count"], 1)
            self.assertIn("handoff batch suite-design regression count is 1", rows["beta"]["comparison_exclusion_reasons"])
            self.assertTrue(any("stale-suite" in item for item in report["recommendations"]))

    def test_blocks_when_promoted_input_is_insufficient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("review", "review", "review", "warn"),
                ],
            )

            report = build_promoted_training_scale_comparison(index_dir)

            self.assertEqual(report["comparison_status"], "blocked")
            self.assertEqual(report["summary"]["comparison_ready_count"], 1)
            self.assertIn("at least two promoted runs", report["summary"]["blocked_reason"])
            self.assertTrue(any("two promoted runs" in item for item in report["blockers"]))

    def test_invalid_baseline_is_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "alpha", "promoted", "warn"),
                    entry("beta", "beta", "promoted", "pass"),
                ],
            )

            report = build_promoted_training_scale_comparison(index_dir, baseline="missing")

            self.assertEqual(report["comparison_status"], "blocked")
            self.assertIn("baseline not found", report["summary"]["blocked_reason"])

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_dir = make_index_tree(
                root,
                [
                    entry("alpha", "<alpha>", "promoted", "warn"),
                    entry("beta", "<beta>", "promoted", "pass"),
                ],
                baseline_name="<beta>",
            )
            report = build_promoted_training_scale_comparison(index_dir, title="<Promoted Compare>")

            outputs = write_promoted_training_scale_comparison_outputs(report, root / "out")
            markdown = render_promoted_training_scale_comparison_markdown(report)
            html = render_promoted_training_scale_comparison_html(report)

            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["comparison_status"], "compared")
            self.assertIn("## Comparison", markdown)
            self.assertIn("&lt;Promoted Compare&gt;", html)
            self.assertIn("&lt;alpha&gt;", html)
            self.assertNotIn("<Promoted Compare>", html)
            self.assertNotIn("<alpha>", html)


if __name__ == "__main__":
    unittest.main()
