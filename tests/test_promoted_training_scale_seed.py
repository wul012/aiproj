from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed import (  # noqa: E402
    build_promoted_training_scale_seed,
    load_promoted_training_scale_decision,
    render_promoted_training_scale_seed_html,
    render_promoted_training_scale_seed_markdown,
    write_promoted_training_scale_seed_outputs,
)
from minigpt import promoted_training_scale_seed as seed_module  # noqa: E402
from minigpt import promoted_training_scale_seed_artifacts as artifact_module  # noqa: E402


class PromotedTrainingScaleSeedTests(unittest.TestCase):
    def test_artifact_functions_are_reexported_from_seed_module(self) -> None:
        self.assertIs(
            seed_module.render_promoted_training_scale_seed_html,
            artifact_module.render_promoted_training_scale_seed_html,
        )
        self.assertIs(
            seed_module.render_promoted_training_scale_seed_markdown,
            artifact_module.render_promoted_training_scale_seed_markdown,
        )
        self.assertIs(
            seed_module.write_promoted_training_scale_seed_outputs,
            artifact_module.write_promoted_training_scale_seed_outputs,
        )

    def test_builds_ready_seed_from_accepted_decision_and_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_name="next-zh",
                dataset_version_prefix="v81-smoke",
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["seed_status"], "ready")
            self.assertEqual(report["summary"]["selected_name"], "beta")
            self.assertTrue(report["summary"]["execution_ready"])
            self.assertEqual(report["summary"]["source_count"], 1)
            self.assertIn("scripts/plan_training_scale.py", report["next_plan"]["command"])
            self.assertIn("v81-smoke", report["next_plan"]["command"])

    def test_review_decision_keeps_command_but_marks_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="review")
            source = write_source(root)

            report = build_promoted_training_scale_seed(decision, [source], project_root=root)

            self.assertEqual(report["seed_status"], "review")
            self.assertTrue(report["next_plan"]["command_available"])
            self.assertFalse(report["next_plan"]["execution_ready"])
            self.assertTrue(any("Review" in item or "review" in item for item in report["recommendations"]))

    def test_inherits_standard_suite_from_selected_scale_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted", suite_name="standard-zh")
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                generated_at="2026-05-14T00:00:00Z",
            )

            command = " ".join(report["next_plan"]["command"])
            self.assertEqual(report["baseline_seed"]["suite"]["path"], "builtin:standard-zh")
            self.assertEqual(report["next_plan"]["suite"]["path"], "builtin:standard-zh")
            self.assertEqual(report["next_plan"]["suite_source"], "inherited")
            self.assertEqual(report["summary"]["baseline_suite_path"], "builtin:standard-zh")
            self.assertEqual(report["summary"]["next_suite_path"], "builtin:standard-zh")
            self.assertIn("--suite-name standard-zh", command)

    def test_carries_decision_handoff_suite_guard_into_seed_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(
                root,
                decision_status="accepted",
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
            )
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_version_prefix="v210-smoke",
            )
            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_promoted_training_scale_seed.py"),
                    str(decision),
                    str(source),
                    "--project-root",
                    str(root),
                    "--out-dir",
                    str(script_out),
                    "--plan-out-dir",
                    str(root / "script-plan"),
                    "--batch-out-root",
                    str(root / "script-batch"),
                    "--dataset-version-prefix",
                    "v210-smoke",
                    "--require-ready",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            guard = report["baseline_seed"]["handoff_suite_guard"]
            summary = report["summary"]
            self.assertEqual(report["seed_status"], "ready")
            self.assertTrue(guard["selected_handoff_require_suite_consistency"])
            self.assertEqual(guard["selected_handoff_suite_consistency"], "consistent")
            self.assertEqual(guard["selected_handoff_suite_mismatch_count"], 0)
            self.assertEqual(guard["selected_handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["selected_handoff_suite_consistency"], "consistent")
            self.assertEqual(summary["selected_handoff_suite_mismatch_count"], 0)
            self.assertEqual(summary["selected_handoff_selected_suite_path"], "builtin:standard-zh")
            self.assertEqual(summary["handoff_suite_mismatch_total"], 0)
            self.assertIn("selected_handoff_suite_consistency", csv_text)
            self.assertIn("Selected handoff suite", markdown)
            self.assertIn("Handoff suite mismatches", markdown)
            self.assertIn("Selected handoff suite", html)
            self.assertIn("selected_handoff_suite_consistency=consistent", completed.stdout)
            self.assertIn("handoff_suite_mismatch_total=0", completed.stdout)
            self.assertTrue((script_out / "promoted_training_scale_seed.json").exists())

    def test_carries_decision_handoff_batch_review_into_seed_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(
                root,
                decision_status="accepted",
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_batch_review=True,
            )
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_version_prefix="v260-smoke",
            )
            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_promoted_training_scale_seed.py"),
                    str(decision),
                    str(source),
                    "--project-root",
                    str(root),
                    "--out-dir",
                    str(script_out),
                    "--plan-out-dir",
                    str(root / "script-plan"),
                    "--batch-out-root",
                    str(root / "script-batch"),
                    "--dataset-version-prefix",
                    "v260-smoke",
                    "--require-ready",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            batch_review = report["baseline_seed"]["handoff_batch_review"]
            summary = report["summary"]
            self.assertEqual(report["seed_status"], "ready")
            self.assertEqual(batch_review["selected_handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(batch_review["selected_handoff_selected_batch_comparison_review_action_count"], 2)
            self.assertEqual(batch_review["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(batch_review["selected_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertEqual(summary["selected_handoff_selected_batch_review_status"], "blocker")
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_review_action_count"], 2)
            self.assertEqual(summary["selected_handoff_selected_batch_comparison_blocker_action_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_selected_batch_blocker_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_batch_comparison_blocker_reasons"], ["coverage-regressed"])
            self.assertIn("selected_handoff_selected_batch_review_status", csv_text)
            self.assertIn("Selected handoff batch review", markdown)
            self.assertIn("Selected handoff batch", html)
            self.assertIn("selected_handoff_selected_batch_review_status=blocker", completed.stdout)
            self.assertIn("comparison_ready_handoff_selected_batch_blocker_count=1", completed.stdout)
            self.assertTrue(any("selected handoff batch blocker" in item for item in report["recommendations"]))

    def test_carries_decision_clean_batch_review_into_seed_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(
                root,
                decision_status="accepted",
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_clean_batch_review=True,
            )
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_version_prefix="v275-smoke",
            )
            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_promoted_training_scale_seed.py"),
                    str(decision),
                    str(source),
                    "--project-root",
                    str(root),
                    "--out-dir",
                    str(script_out),
                    "--plan-out-dir",
                    str(root / "script-plan"),
                    "--batch-out-root",
                    str(root / "script-batch"),
                    "--dataset-version-prefix",
                    "v275-smoke",
                    "--require-ready",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            clean_review = report["baseline_seed"]["handoff_clean_batch_review"]
            summary = report["summary"]
            self.assertEqual(report["seed_status"], "ready")
            self.assertTrue(clean_review["selected_handoff_require_clean_batch_review"])
            self.assertEqual(clean_review["selected_handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["selected_handoff_require_clean_batch_review"], True)
            self.assertEqual(summary["selected_handoff_clean_batch_review_status"], "clean")
            self.assertEqual(summary["handoff_require_clean_batch_review_count"], 3)
            self.assertEqual(summary["handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["handoff_unclean_batch_review_count"], 1)
            self.assertEqual(summary["comparison_ready_handoff_require_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_clean_batch_review_count"], 2)
            self.assertEqual(summary["comparison_ready_handoff_unclean_batch_review_count"], 0)
            self.assertIn("selected_handoff_require_clean_batch_review", csv_text)
            self.assertIn("Selected handoff clean batch review", markdown)
            self.assertIn("Ready clean batch", html)
            self.assertIn("selected_handoff_clean_batch_review_status=clean", completed.stdout)
            self.assertIn("handoff_unclean_batch_review_count=1", completed.stdout)
            self.assertIn("comparison_ready_handoff_unclean_batch_review_count=0", completed.stdout)
            self.assertTrue(any("Rejected promoted decision inputs include unclean clean-required handoffs" in item for item in report["recommendations"]))

    def test_carries_decision_ci_regression_exclusions_into_seed_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(
                root,
                decision_status="accepted",
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_clean_batch_review=True,
                include_ci_regression_context=True,
            )
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_version_prefix="v311-smoke",
            )
            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_promoted_training_scale_seed.py"),
                    str(decision),
                    str(source),
                    "--project-root",
                    str(root),
                    "--out-dir",
                    str(script_out),
                    "--plan-out-dir",
                    str(root / "script-plan"),
                    "--batch-out-root",
                    str(root / "script-batch"),
                    "--dataset-version-prefix",
                    "v311-smoke",
                    "--require-ready",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            clean_review = report["baseline_seed"]["handoff_clean_batch_review"]
            summary = report["summary"]
            self.assertEqual(report["seed_status"], "ready")
            self.assertEqual(clean_review["selected_handoff_batch_maturity_ci_regression_count"], 0)
            self.assertEqual(clean_review["selected_handoff_batch_maturity_ci_regression_reason_counts"], {})
            self.assertEqual(clean_review["selected_handoff_selected_batch_maturity_ci_regression_count"], 0)
            self.assertEqual(clean_review["selected_handoff_selected_batch_maturity_ci_regression_reason_counts"], {})
            self.assertEqual(clean_review["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(
                clean_review["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(clean_review["handoff_selected_batch_maturity_ci_regression_total"], 1)
            self.assertEqual(
                clean_review["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertEqual(clean_review["handoff_batch_maturity_ci_regression_names"], ["dirty-ci-old"])
            self.assertEqual(clean_review["comparison_exclusion_reasons"], ["handoff batch CI regression count is 2"])
            self.assertEqual(clean_review["comparison_ready_handoff_batch_maturity_ci_regression_count"], 0)
            self.assertEqual(clean_review["comparison_ready_handoff_batch_maturity_ci_regression_reason_counts"], {})
            self.assertEqual(summary["selected_handoff_batch_maturity_ci_regression_count"], 0)
            self.assertEqual(summary["selected_handoff_batch_maturity_ci_regression_reason_counts"], {})
            self.assertEqual(summary["handoff_batch_maturity_ci_regression_count"], 2)
            self.assertEqual(
                summary["handoff_batch_maturity_ci_regression_reason_counts"],
                {"missing-ci-step": 1, "workflow-order-regressed": 1},
            )
            self.assertEqual(summary["handoff_selected_batch_maturity_ci_regression_total"], 1)
            self.assertEqual(
                summary["handoff_selected_batch_maturity_ci_regression_reason_counts"],
                {"workflow-order-regressed": 1},
            )
            self.assertEqual(summary["comparison_exclusion_reasons"], ["handoff batch CI regression count is 2"])
            self.assertIn("handoff_batch_maturity_ci_regression_count", csv_text)
            self.assertIn("handoff_batch_maturity_ci_regression_reason_counts", csv_text)
            self.assertIn("missing-ci-step:1, workflow-order-regressed:1", csv_text)
            self.assertIn("comparison_exclusion_reasons", csv_text)
            self.assertIn("Handoff batch CI regressions", markdown)
            self.assertIn("Handoff batch CI regression reasons", markdown)
            self.assertIn("Comparison exclusion reasons", markdown)
            self.assertIn("Handoff CI regressions", html)
            self.assertIn("Handoff CI reasons", html)
            self.assertIn("handoff_batch_maturity_ci_regression_count=2", completed.stdout)
            self.assertIn(
                'handoff_batch_maturity_ci_regression_reason_counts={"missing-ci-step": 1, "workflow-order-regressed": 1}',
                completed.stdout,
            )
            self.assertIn("comparison_ready_handoff_batch_maturity_ci_regression_count=0", completed.stdout)
            self.assertIn("comparison_ready_handoff_batch_maturity_ci_regression_reason_counts={}", completed.stdout)
            self.assertTrue(any("handoff batch CI regressions" in item for item in report["recommendations"]))
            self.assertTrue(
                any("missing-ci-step:1, workflow-order-regressed:1" in item for item in report["recommendations"])
            )

    def test_carries_decision_suite_design_exclusions_into_seed_outputs_and_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(
                root,
                decision_status="accepted",
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_clean_batch_review=True,
                include_suite_design_regression_context=True,
            )
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                plan_out_dir=root / "plan",
                batch_out_root=root / "batch",
                dataset_version_prefix="v424-smoke",
            )
            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            markdown = Path(outputs["markdown"]).read_text(encoding="utf-8")
            html = Path(outputs["html"]).read_text(encoding="utf-8")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            script_out = root / "script-out"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_promoted_training_scale_seed.py"),
                    str(decision),
                    str(source),
                    "--project-root",
                    str(root),
                    "--out-dir",
                    str(script_out),
                    "--plan-out-dir",
                    str(root / "script-plan"),
                    "--batch-out-root",
                    str(root / "script-batch"),
                    "--dataset-version-prefix",
                    "v424-smoke",
                    "--require-ready",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            clean_review = report["baseline_seed"]["handoff_clean_batch_review"]
            summary = report["summary"]
            self.assertEqual(report["seed_status"], "ready")
            self.assertEqual(clean_review["selected_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(clean_review["selected_handoff_batch_maturity_suite_design_regression_names"], [])
            self.assertEqual(clean_review["selected_handoff_selected_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(clean_review["selected_handoff_selected_batch_maturity_suite_design_regression_names"], [])
            self.assertEqual(clean_review["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(clean_review["handoff_selected_batch_maturity_suite_design_regression_total"], 1)
            self.assertEqual(
                clean_review["handoff_batch_maturity_suite_design_regression_names"],
                ["beta-suite", "standard"],
            )
            self.assertEqual(clean_review["handoff_selected_batch_maturity_suite_design_regression_names"], ["beta-suite"])
            self.assertEqual(clean_review["comparison_ready_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(
                clean_review["comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total"],
                0,
            )
            self.assertEqual(clean_review["comparison_ready_handoff_batch_maturity_suite_design_regression_names"], [])
            self.assertEqual(
                clean_review["comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names"],
                [],
            )
            self.assertEqual(summary["selected_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(summary["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(summary["handoff_selected_batch_maturity_suite_design_regression_total"], 1)
            self.assertEqual(
                summary["handoff_batch_maturity_suite_design_regression_names"],
                ["beta-suite", "standard"],
            )
            self.assertEqual(
                summary["comparison_ready_handoff_batch_maturity_suite_design_regression_count"],
                0,
            )
            self.assertEqual(summary["comparison_exclusion_reasons"], ["handoff batch suite-design regression count is 2"])
            self.assertIn("handoff_batch_maturity_suite_design_regression_count", csv_text)
            self.assertIn("handoff_batch_maturity_suite_design_regression_names", csv_text)
            self.assertIn("beta-suite; standard", csv_text)
            self.assertIn("Handoff batch suite-design regressions", markdown)
            self.assertIn("Comparison-ready handoff batch suite-design regressions", markdown)
            self.assertIn("Handoff suite-design regressions", html)
            self.assertIn("Ready suite-design regressions", html)
            self.assertIn("handoff_batch_maturity_suite_design_regression_count=2", completed.stdout)
            self.assertIn(
                'handoff_batch_maturity_suite_design_regression_names=["beta-suite", "standard"]',
                completed.stdout,
            )
            self.assertIn("comparison_ready_handoff_batch_maturity_suite_design_regression_count=0", completed.stdout)
            self.assertTrue(any("handoff batch suite-design regressions" in item for item in report["recommendations"]))

    def test_default_suite_override_does_not_emit_fake_builtin_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted", suite_name="standard-zh")
            source = write_source(root)

            report = build_promoted_training_scale_seed(
                decision,
                [source],
                project_root=root,
                suite_name="default",
                generated_at="2026-05-14T00:00:00Z",
            )

            command = " ".join(report["next_plan"]["command"])
            self.assertEqual(report["next_plan"]["suite"]["mode"], "file")
            self.assertEqual(report["next_plan"]["suite"]["path"], str(root / "data" / "eval_prompts.json"))
            self.assertEqual(report["next_plan"]["suite_source"], "default")
            self.assertNotIn("builtin:default", json.dumps(report, ensure_ascii=False))
            self.assertNotIn("--suite-name default", command)

    def test_blocks_when_decision_has_no_selected_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="blocked", selected=False)
            source = write_source(root)

            report = build_promoted_training_scale_seed(decision, [source], project_root=root)

            self.assertEqual(report["seed_status"], "blocked")
            self.assertFalse(report["next_plan"]["command_available"])
            self.assertGreaterEqual(report["summary"]["blocker_count"], 1)
            self.assertTrue(any("selected_baseline" in item for item in report["blockers"]))

    def test_blocks_missing_next_corpus_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            missing = root / "missing.txt"

            report = build_promoted_training_scale_seed(decision, [missing], project_root=root)

            self.assertEqual(report["seed_status"], "blocked")
            self.assertEqual(report["summary"]["missing_source_count"], 1)
            self.assertFalse(report["next_plan"]["command_available"])
            self.assertTrue(any("missing corpus sources" in item for item in report["blockers"]))

    def test_outputs_and_renderers_escape_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            decision = write_decision_tree(root, decision_status="accepted")
            source = write_source(root)
            report = build_promoted_training_scale_seed(
                decision.parent,
                [source],
                project_root=root,
                title="<Seed>",
            )

            outputs = write_promoted_training_scale_seed_outputs(report, root / "seed")
            loaded = load_promoted_training_scale_decision(decision.parent)
            markdown = render_promoted_training_scale_seed_markdown(report)
            html = render_promoted_training_scale_seed_html(report)

            self.assertEqual(loaded["decision_status"], "accepted")
            self.assertTrue(Path(outputs["json"]).exists())
            self.assertTrue(Path(outputs["csv"]).exists())
            self.assertIn("## Next Plan Command", markdown)
            self.assertIn("&lt;Seed&gt;", html)
            self.assertNotIn("<Seed>", html)


def write_decision_tree(
    root: Path,
    *,
    decision_status: str,
    selected: bool = True,
    suite_name: str | None = None,
    include_handoff_suite_guard: bool = False,
    include_handoff_batch_review: bool = False,
    include_clean_batch_review: bool = False,
    include_ci_regression_context: bool = False,
    include_suite_design_regression_context: bool = False,
) -> Path:
    scale_summary = {
        "dataset_name": "sample-zh",
        "version_prefix": "v80",
        "scale_tier": "tiny",
        "char_count": 2048,
        "variant_count": 1,
    }
    if suite_name:
        scale_summary.update(
            {
                "suite_mode": "builtin",
                "suite_name": suite_name,
                "suite_path": f"builtin:{suite_name}",
            }
        )
    run_path = root / "beta" / "scale-run" / "training_scale_run.json"
    write_json(
        run_path,
        {
            "name": "beta",
            "status": "completed",
            "allowed": True,
            "gate_profile": "review",
            "gate": {"overall_status": "pass"},
            "scale_plan_summary": scale_summary,
            "batch_summary": {"status": "completed", "variant_count": 1},
        },
    )
    selected_baseline = {
        "name": "beta",
        "gate_status": "pass",
        "batch_status": "completed",
        "readiness_score": 107,
        "training_scale_run_path": str(run_path),
        "promotion_status": "promoted",
    }
    summary_fields = {"decision_status": decision_status, "selected_name": "beta" if selected else None}
    if include_handoff_suite_guard:
        selected_baseline.update(
            {
                "handoff_require_suite_consistency": True,
                "handoff_suite_consistency": "consistent",
                "handoff_suite_mismatch_count": 0,
                "handoff_selected_suite_path": "builtin:standard-zh",
            }
        )
        summary_fields.update(
            {
                "selected_handoff_require_suite_consistency": True,
                "selected_handoff_suite_consistency": "consistent",
                "selected_handoff_suite_mismatch_count": 0,
                "selected_handoff_selected_suite_path": "builtin:standard-zh",
                "handoff_require_suite_consistency_count": 2,
                "handoff_suite_consistent_count": 2,
                "handoff_suite_mismatch_total": 0,
                "comparison_ready_handoff_suite_mismatch_total": 0,
            }
        )
    if include_handoff_batch_review:
        selected_baseline.update(
            {
                "handoff_selected_batch_review_status": "blocker",
                "handoff_selected_batch_comparison_review_action_count": 2,
                "handoff_selected_batch_comparison_blocker_action_count": 1,
                "handoff_selected_batch_maturity_coverage_regression_count": 1,
                "handoff_batch_comparison_review_action_count": 2,
                "handoff_batch_comparison_blocker_action_count": 1,
                "handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
            }
        )
        summary_fields.update(
            {
                "selected_handoff_selected_batch_review_status": "blocker",
                "selected_handoff_selected_batch_comparison_review_action_count": 2,
                "selected_handoff_selected_batch_comparison_blocker_action_count": 1,
                "selected_handoff_selected_batch_maturity_coverage_regression_count": 1,
                "selected_handoff_batch_comparison_review_action_count": 2,
                "selected_handoff_batch_comparison_blocker_action_count": 1,
                "selected_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
                "comparison_ready_handoff_selected_batch_review_count": 1,
                "comparison_ready_handoff_selected_batch_blocker_count": 1,
                "comparison_ready_handoff_selected_batch_comparison_review_action_total": 4,
                "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": 1,
                "comparison_ready_handoff_batch_comparison_review_action_total": 4,
                "comparison_ready_handoff_batch_comparison_blocker_action_total": 1,
                "comparison_ready_handoff_batch_comparison_blocker_reasons": ["coverage-regressed"],
            }
        )
    if include_clean_batch_review:
        selected_baseline.update(
            {
                "handoff_require_clean_batch_review": True,
                "handoff_clean_batch_review_status": "clean",
                "handoff_batch_maturity_ci_regression_count": 0,
                "handoff_batch_maturity_ci_regression_names": [],
                "handoff_selected_batch_maturity_ci_regression_count": 0,
                "comparison_exclusion_reasons": [],
                "handoff_batch_maturity_suite_design_regression_count": 0,
                "handoff_batch_maturity_suite_design_regression_names": [],
                "handoff_selected_batch_maturity_suite_design_regression_count": 0,
                "handoff_selected_batch_maturity_suite_design_regression_names": [],
            }
        )
        summary_fields.update(
            {
                "selected_handoff_require_clean_batch_review": True,
                "selected_handoff_clean_batch_review_status": "clean",
                "selected_handoff_batch_maturity_ci_regression_count": 0,
                "selected_handoff_batch_maturity_ci_regression_reason_counts": {},
                "selected_handoff_batch_maturity_ci_regression_names": [],
                "selected_handoff_selected_batch_maturity_ci_regression_count": 0,
                "selected_handoff_selected_batch_maturity_ci_regression_reason_counts": {},
                "selected_handoff_batch_maturity_suite_design_regression_count": 0,
                "selected_handoff_batch_maturity_suite_design_regression_names": [],
                "selected_handoff_selected_batch_maturity_suite_design_regression_count": 0,
                "selected_handoff_selected_batch_maturity_suite_design_regression_names": [],
                "selected_comparison_exclusion_reasons": [],
                "handoff_require_clean_batch_review_count": 3,
                "handoff_clean_batch_review_count": 2,
                "handoff_unclean_batch_review_count": 1,
                "comparison_ready_handoff_require_clean_batch_review_count": 2,
                "comparison_ready_handoff_clean_batch_review_count": 2,
                "comparison_ready_handoff_unclean_batch_review_count": 0,
            }
        )
    if include_ci_regression_context:
        summary_fields.update(
            {
                "handoff_batch_maturity_ci_regression_count": 2,
                "handoff_batch_maturity_ci_regression_reason_counts": {
                    "missing-ci-step": 1,
                    "workflow-order-regressed": 1,
                },
                "handoff_selected_batch_maturity_ci_regression_total": 1,
                "handoff_selected_batch_maturity_ci_regression_reason_counts": {
                    "workflow-order-regressed": 1,
                },
                "handoff_batch_maturity_ci_regression_names": ["dirty-ci-old"],
                "comparison_exclusion_reasons": ["handoff batch CI regression count is 2"],
                "comparison_ready_handoff_batch_maturity_ci_regression_count": 0,
                "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {},
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_total": 0,
                "comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts": {},
                "comparison_ready_handoff_batch_maturity_ci_regression_names": [],
            }
        )
    if include_suite_design_regression_context:
        summary_fields.update(
            {
                "handoff_batch_maturity_suite_design_regression_count": 2,
                "handoff_selected_batch_maturity_suite_design_regression_total": 1,
                "handoff_batch_maturity_suite_design_regression_names": ["beta-suite", "standard"],
                "handoff_selected_batch_maturity_suite_design_regression_names": ["beta-suite"],
                "comparison_exclusion_reasons": ["handoff batch suite-design regression count is 2"],
                "comparison_ready_handoff_batch_maturity_suite_design_regression_count": 0,
                "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_total": 0,
                "comparison_ready_handoff_batch_maturity_suite_design_regression_names": [],
                "comparison_ready_handoff_selected_batch_maturity_suite_design_regression_names": [],
            }
        )
    payload = {
        "schema_version": 1,
        "title": "decision",
        "decision_status": decision_status,
        "comparison_path": str(root / "comparison" / "promoted_training_scale_comparison.json"),
        "selected_baseline": selected_baseline if selected else None,
        "summary": summary_fields,
    }
    decision_path = root / "promoted-decision" / "promoted_training_scale_decision.json"
    write_json(decision_path, payload)
    return decision_path


def write_source(root: Path) -> Path:
    source = root / "corpus.txt"
    source.write_text("MiniGPT next cycle corpus.\n" * 120, encoding="utf-8")
    return source


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
