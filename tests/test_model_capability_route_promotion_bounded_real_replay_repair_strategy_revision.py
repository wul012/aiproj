from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import (
    build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (
    build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision,
    locate_repair_checkpoint_comparison,
    locate_repair_plan,
    locate_repair_seed,
    locate_repair_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import replay_report, training_report


def comparison_report(*, baseline_passed: int = 2, repair_passed: int = 0) -> dict:
    return build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
        replay_report(passed=baseline_passed),
        replay_report(passed=repair_passed),
        training_report(),
    )


def repair_plan_report() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_real_replay_repair_plan_ready": True, "task_count": 3, "source_pass_rate": 0.4, "target_pass_rate": 1.0},
        "repair_tasks": [{"task_id": "repair-case-1", "case_id": "case-1", "repair_type": "missing_term_retention_repair"}],
    }


def repair_seed_report() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_real_replay_repair_seed_ready": True, "example_count": 6, "case_count": 3},
        "seed_examples": [{"example_id": "seed-1", "case_id": "case-1", "completion": "fixed loss", "text": "fixed loss"}],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayRepairStrategyRevisionTests(unittest.TestCase):
    def test_builds_strategy_revision_after_regression(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(
            comparison_report(),
            repair_plan_report(),
            repair_seed_report(),
            training_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_ready")
        self.assertTrue(report["summary"]["bounded_real_replay_repair_strategy_revision_ready"])
        self.assertTrue(report["summary"]["blocked_checkpoint"])
        self.assertTrue(report["summary"]["regression_detected"])
        self.assertEqual(report["summary"]["passed_case_delta"], -2)
        self.assertGreaterEqual(report["summary"]["case_action_count"], 1)
        self.assertEqual(report["strategy_revision"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_real_replay_repair_seed_revision")
        self.assertEqual(resolve_exit_code(report, require_revision_ready=True), 0)

    def test_revision_fails_when_repair_checkpoint_already_improved(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(
            comparison_report(baseline_passed=1, repair_passed=3),
            repair_plan_report(),
            repair_seed_report(),
            training_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("repair_not_improved", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_revision_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = comparison_report()
            plan = repair_plan_report()
            seed = repair_seed_report()
            training = training_report()
            comparison_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs(comparison, root / "comparison")
            plan_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs(plan, root / "plan")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs(seed, root / "seed")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs(training, root / "training")
            self.assertEqual(locate_repair_checkpoint_comparison(Path(comparison_outputs["json"]).parent), Path(comparison_outputs["json"]))
            self.assertEqual(locate_repair_plan(Path(plan_outputs["json"]).parent), Path(plan_outputs["json"]))
            self.assertEqual(locate_repair_seed(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            self.assertEqual(locate_repair_training_run(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(comparison, plan, seed, training)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs(report, root / "revision")
            cli_main(
                [
                    "--comparison",
                    str(Path(comparison_outputs["json"]).parent),
                    "--repair-plan",
                    str(Path(plan_outputs["json"]).parent),
                    "--repair-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--training-run",
                    str(Path(training_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-revision"),
                    "--require-revision-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("strategy_revision_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_text(report))
        self.assertIn("Case Actions", render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_markdown(report))
        self.assertIn("Strategy Actions", render_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_html(report))


if __name__ == "__main__":
    unittest.main()
