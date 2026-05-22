from __future__ import annotations

import json
import subprocess
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
from minigpt import training_scale_run_decision  # noqa: E402
from minigpt import training_scale_run_decision_artifacts  # noqa: E402


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
            self.assertEqual(report["summary"]["suite_consistency"], "consistent")
            self.assertGreater(report["summary"]["batch_comparison_review_action_count"], 0)
            self.assertEqual(report["summary"]["batch_comparison_blocker_action_count"], 0)
            self.assertEqual(report["summary"]["selected_batch_review_status"], "review")
            self.assertGreater(report["summary"]["selected_batch_comparison_review_action_count"], 0)
            self.assertTrue(str(report["summary"]["selected_suite_path"]).replace("\\", "/").endswith("data/eval_prompts.json"))
            self.assertIn("--execute", report["execute_command"])
            self.assertIn("--gate-profile", report["execute_command"])
            self.assertIn("review", report["execute_command"])
            self.assertTrue(any("Review selected batch comparison actions" in item for item in report["recommendations"]))

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

    def test_mixed_suite_summary_is_carried_into_decision_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)
            payload = json.loads(comparison.read_text(encoding="utf-8"))
            payload["runs"][0]["suite_path"] = "builtin:standard-zh"
            payload["summary"]["suite_consistency"] = "mixed"
            payload["summary"]["suite_paths"] = ["builtin:standard-zh", "data/eval_prompts.json"]
            payload["summary"]["suite_mismatch_count"] = 1
            comparison.write_text(json.dumps(payload), encoding="utf-8")

            report = build_training_scale_run_decision(comparison, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["summary"]["suite_consistency"], "mixed")
            self.assertFalse(report["summary"]["require_suite_consistency"])
            self.assertEqual(report["summary"]["selected_suite_path"], "builtin:standard-zh")
            self.assertTrue(any("different benchmark suites" in item for item in report["recommendations"]))

    def test_require_suite_consistency_blocks_mixed_suite_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)
            payload = json.loads(comparison.read_text(encoding="utf-8"))
            payload["runs"][0]["suite_path"] = "builtin:standard-zh"
            payload["summary"]["suite_consistency"] = "mixed"
            payload["summary"]["suite_paths"] = ["builtin:standard-zh", "data/eval_prompts.json"]
            payload["summary"]["suite_mismatch_count"] = 1
            comparison.write_text(json.dumps(payload), encoding="utf-8")

            report = build_training_scale_run_decision(
                comparison,
                require_suite_consistency=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(report["decision_status"], "blocked")
            self.assertIsNone(report["selected_run"])
            self.assertTrue(report["summary"]["require_suite_consistency"])
            reasons = [reason for row in report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("benchmark suite consistency is mixed", reasons)
            self.assertTrue(any("Fix benchmark suite consistency" in item for item in report["recommendations"]))

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
            self.assertIn("Selected batch review status", markdown)
            self.assertIn("Batch comparison reviews", markdown)
            self.assertIn("Batch review status", html)
            self.assertIn("&lt;allowed&gt;", html)
            self.assertNotIn("<allowed>", html)
            payload = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)

    def test_selected_batch_blocker_downgrades_ready_decision_to_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)
            payload = json.loads(comparison.read_text(encoding="utf-8"))
            allowed = payload["runs"][0]
            allowed["gate_status"] = "pass"
            allowed["readiness_score"] = 95
            allowed["batch_comparison_review_action_count"] = 1
            allowed["batch_comparison_blocker_action_count"] = 1
            allowed["batch_maturity_coverage_regression_count"] = 1
            payload["summary"]["batch_comparison_review_action_count"] = 1
            payload["summary"]["batch_comparison_blocker_action_count"] = 1
            payload["summary"]["batch_maturity_coverage_regression_count"] = 1
            payload["summary"]["batch_comparison_blocker_reasons"] = ["coverage-regressed"]
            comparison.write_text(json.dumps(payload), encoding="utf-8")

            report = build_training_scale_run_decision(comparison, generated_at="2026-05-14T00:00:00Z")

            self.assertEqual(report["selected_run"]["name"], "allowed")
            self.assertEqual(report["decision_status"], "review")
            self.assertEqual(report["summary"]["selected_batch_review_status"], "blocker")
            self.assertEqual(report["summary"]["selected_batch_comparison_blocker_action_count"], 1)
            self.assertTrue(any("Resolve selected batch comparison blocker actions" in item for item in report["recommendations"]))

    def test_require_clean_batch_review_blocks_review_or_blocker_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)

            default_report = build_training_scale_run_decision(
                comparison,
                generated_at="2026-05-14T00:00:00Z",
            )
            strict_report = build_training_scale_run_decision(
                comparison,
                require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(default_report["decision_status"], "review")
            self.assertEqual(default_report["summary"]["clean_batch_review_status"], "review")
            self.assertEqual(strict_report["decision_status"], "blocked")
            self.assertTrue(strict_report["summary"]["require_clean_batch_review"])
            self.assertEqual(strict_report["summary"]["clean_batch_review_status"], "review")
            self.assertIsNone(strict_report["selected_run"])
            reasons = [reason for row in strict_report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("batch comparison review actions are present", reasons)
            self.assertTrue(any("Resolve batch review" in item for item in strict_report["recommendations"]))

    def test_batch_ci_regression_marks_decision_review_and_clean_gate_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)
            payload = json.loads(comparison.read_text(encoding="utf-8"))
            allowed = payload["runs"][0]
            allowed["batch_comparison_review_action_count"] = 0
            allowed["batch_comparison_blocker_action_count"] = 0
            allowed["batch_maturity_coverage_regression_count"] = 0
            allowed["batch_maturity_ci_regression_count"] = 1
            allowed["batch_maturity_ci_regression_names"] = ["ci-risk"]
            allowed["batch_maturity_ci_regression_reason_counts"] = {
                "ci_failed_checks_increased": 2,
                "ci_order_violations_increased": 1,
            }
            payload["summary"]["batch_comparison_review_action_count"] = 0
            payload["summary"]["batch_comparison_blocker_action_count"] = 0
            payload["summary"]["batch_maturity_coverage_regression_count"] = 0
            payload["summary"]["batch_maturity_ci_regression_count"] = 1
            payload["summary"]["batch_maturity_ci_regression_names"] = ["ci-risk"]
            payload["summary"]["batch_maturity_ci_regression_reason_counts"] = {
                "ci_failed_checks_increased": 2,
                "ci_order_violations_increased": 1,
            }
            comparison.write_text(json.dumps(payload), encoding="utf-8")

            default_report = build_training_scale_run_decision(comparison, generated_at="2026-05-14T00:00:00Z")
            strict_report = build_training_scale_run_decision(
                comparison,
                require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
            )

            self.assertEqual(default_report["summary"]["selected_batch_review_status"], "review")
            self.assertEqual(default_report["summary"]["selected_batch_maturity_ci_regression_count"], 1)
            self.assertEqual(
                default_report["summary"]["selected_batch_maturity_ci_regression_reason_counts"],
                {"ci_failed_checks_increased": 2, "ci_order_violations_increased": 1},
            )
            self.assertEqual(default_report["summary"]["batch_maturity_ci_regression_count"], 1)
            self.assertEqual(default_report["summary"]["batch_maturity_ci_regression_names"], ["ci-risk"])
            self.assertEqual(
                default_report["summary"]["batch_maturity_ci_regression_reason_counts"],
                {"ci_failed_checks_increased": 2, "ci_order_violations_increased": 1},
            )
            self.assertEqual(default_report["summary"]["clean_batch_review_status"], "review")
            self.assertTrue(any("CI regression context" in item for item in default_report["recommendations"]))
            self.assertEqual(strict_report["decision_status"], "blocked")
            self.assertIsNone(strict_report["selected_run"])
            reasons = [reason for row in strict_report["rejected_runs"] for reason in row["reasons"]]
            self.assertIn("batch maturity CI regressions are present", reasons)

    def test_clean_batch_review_fields_are_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)

            report = build_training_scale_run_decision(
                comparison,
                require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_training_scale_run_decision_outputs(report, root / "decision")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = render_training_scale_run_decision_markdown(report)
            html = render_training_scale_run_decision_html(report)

            self.assertIn("require_clean_batch_review", csv_text)
            self.assertIn("clean_batch_review_status", csv_text)
            self.assertIn("Require clean batch review", markdown)
            self.assertIn("Clean batch review status", markdown)
            self.assertIn("Require clean batch review", html)
            self.assertIn("Clean batch review", html)

    def test_ci_regression_fields_are_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = self._make_comparison(root)
            payload = json.loads(comparison.read_text(encoding="utf-8"))
            allowed = payload["runs"][0]
            allowed["batch_maturity_ci_regression_count"] = 1
            allowed["batch_maturity_ci_regression_names"] = ["ci-risk"]
            allowed["batch_maturity_ci_regression_reason_counts"] = {
                "ci_failed_checks_increased": 2,
                "ci_order_violations_increased": 1,
            }
            payload["summary"]["batch_maturity_ci_regression_count"] = 1
            payload["summary"]["batch_maturity_ci_regression_names"] = ["ci-risk"]
            payload["summary"]["batch_maturity_ci_regression_reason_counts"] = {
                "ci_failed_checks_increased": 2,
                "ci_order_violations_increased": 1,
            }
            comparison.write_text(json.dumps(payload), encoding="utf-8")

            report = build_training_scale_run_decision(comparison, generated_at="2026-05-14T00:00:00Z")
            outputs = write_training_scale_run_decision_outputs(report, root / "decision")
            csv_text = Path(outputs["csv"]).read_text(encoding="utf-8")
            markdown = render_training_scale_run_decision_markdown(report)
            html = render_training_scale_run_decision_html(report)
            cli = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "decide_training_scale_run.py"),
                    str(comparison),
                    "--out-dir",
                    str(root / "cli-decision"),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("selected_batch_maturity_ci_regression_count", csv_text)
            self.assertIn("selected_batch_maturity_ci_regression_reason_counts", csv_text)
            self.assertIn("batch_maturity_ci_regression_count", csv_text)
            self.assertIn("batch_maturity_ci_regression_reason_counts", csv_text)
            self.assertIn("ci_failed_checks_increased", csv_text)
            self.assertIn("Selected batch CI regressions", markdown)
            self.assertIn("Selected batch CI regression reasons", markdown)
            self.assertIn("Batch CI regressions", markdown)
            self.assertIn("Batch CI regression reasons", markdown)
            self.assertIn("ci_failed_checks_increased:2", markdown)
            self.assertIn("Selected CI regressions", html)
            self.assertIn("Selected CI reasons", html)
            self.assertIn("CI regressions", html)
            self.assertIn("CI regression reasons", html)
            self.assertIn("ci_failed_checks_increased:2", html)
            self.assertIn("batch_maturity_ci_regression_reason_counts=", cli.stdout)
            self.assertIn("selected_batch_maturity_ci_regression_reason_counts=", cli.stdout)
            self.assertIn("ci_failed_checks_increased", cli.stdout)

    def test_rejects_comparison_without_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = root / "training_scale_run_comparison.json"
            comparison.write_text(json.dumps({"schema_version": 1, "runs": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                build_training_scale_run_decision(comparison)

    def test_decision_module_reexports_artifact_writers(self) -> None:
        self.assertIs(
            training_scale_run_decision.write_training_scale_run_decision_outputs,
            training_scale_run_decision_artifacts.write_training_scale_run_decision_outputs,
        )
        self.assertIs(
            training_scale_run_decision.render_training_scale_run_decision_html,
            training_scale_run_decision_artifacts.render_training_scale_run_decision_html,
        )

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
