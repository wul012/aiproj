from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision import (
    build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision,
    locate_repair_seed,
    locate_repair_strategy_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (
    comparison_report,
    repair_plan_report,
    repair_seed_report,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (
    build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision,
)
from tests.test_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import training_report


def ready_strategy_revision() -> dict:
    return build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(
        comparison_report(),
        repair_plan_report(),
        repair_seed_report(),
        training_report(),
    )


class ModelCapabilityRoutePromotionBoundedRealReplayRepairSeedRevisionTests(unittest.TestCase):
    def test_builds_seed_revision_with_baseline_preservation(self) -> None:
        strategy = ready_strategy_revision()
        seed = repair_seed_report()
        report = build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision(strategy, seed)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_seed_revision_ready")
        self.assertTrue(report["summary"]["bounded_real_replay_repair_seed_revision_ready"])
        self.assertEqual(report["summary"]["original_example_count"], 1)
        self.assertGreater(report["summary"]["added_example_count"], 0)
        self.assertEqual(report["summary"]["baseline_preservation_example_count"], 2)
        self.assertTrue(any(row["revision_type"] == "carry_forward_original_repair_seed" for row in report["seed_examples"]))
        self.assertEqual(resolve_exit_code(report, require_seed_revision_ready=True), 0)

    def test_seed_revision_fails_when_strategy_is_not_ready(self) -> None:
        strategy = ready_strategy_revision()
        strategy["status"] = "fail"
        report = build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision(strategy, repair_seed_report())

        self.assertEqual(report["status"], "fail")
        self.assertIn("strategy_revision_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_revision_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            strategy = ready_strategy_revision()
            seed = repair_seed_report()
            strategy_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_outputs(strategy, root / "strategy")
            seed_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_outputs(seed, root / "seed")
            self.assertEqual(locate_repair_strategy_revision(Path(strategy_outputs["json"]).parent), Path(strategy_outputs["json"]))
            self.assertEqual(locate_repair_seed(Path(seed_outputs["json"]).parent), Path(seed_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision(strategy, seed)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_outputs(report, root / "seed-revision")
            cli_main(
                [
                    "--strategy-revision",
                    str(Path(strategy_outputs["json"]).parent),
                    "--repair-seed",
                    str(Path(seed_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-seed-revision"),
                    "--require-seed-revision-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertIn("seed_revision_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_text(report))
        self.assertIn("Seed Examples", render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_markdown(report))
        self.assertIn("baseline preservation", render_model_capability_route_promotion_bounded_real_replay_repair_seed_revision_html(report).lower())


if __name__ == "__main__":
    unittest.main()
