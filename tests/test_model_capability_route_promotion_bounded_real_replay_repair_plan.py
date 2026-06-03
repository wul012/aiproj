from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_review import build_model_capability_route_promotion_bounded_real_replay_review
from minigpt.model_capability_route_promotion_bounded_real_replay_review_artifacts import write_model_capability_route_promotion_bounded_real_replay_review_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import (
    build_model_capability_route_promotion_bounded_real_replay_repair_plan,
    locate_route_promotion_bounded_real_replay_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_plan_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_plan_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_plan_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_real_replay_repair_plan import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay_review import ready_real_replay


def ready_repair_review(root: Path) -> tuple[dict, Path]:
    replay, _ = ready_real_replay(root)
    review = build_model_capability_route_promotion_bounded_real_replay_review(
        replay,
        minimum_pass_rate_for_repair_review=0.2,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_review_outputs(review, root / "review")
    return review, Path(outputs["json"])


class ModelCapabilityRoutePromotionBoundedRealReplayRepairPlanTests(unittest.TestCase):
    def test_builds_repair_plan_from_failed_replay_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_repair_review(Path(tmp))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_plan(review, real_replay_review_path=review_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_plan_ready")
        self.assertTrue(report["summary"]["bounded_real_replay_repair_plan_ready"])
        self.assertEqual(report["summary"]["task_count"], 4)
        self.assertEqual(report["repair_plan"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_real_replay_repair_seed")
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_plan_fails_when_review_is_already_promotion_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            replay, _ = ready_real_replay(Path(tmp), all_cases_pass=True)
            review = build_model_capability_route_promotion_bounded_real_replay_review(replay)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_plan(review)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_needs_repair", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_repair_review(root)
            self.assertEqual(locate_route_promotion_bounded_real_replay_review(review_path.parent), review_path)
            report = build_model_capability_route_promotion_bounded_real_replay_repair_plan(review, real_replay_review_path=review_path)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_plan_outputs(report, root / "plan")
            cli_main(["--real-replay-review", str(review_path.parent), "--out-dir", str(root / "cli-plan"), "--require-plan-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bounded_real_replay_repair_plan_ready=True", render_model_capability_route_promotion_bounded_real_replay_repair_plan_text(report))
        self.assertIn("Repair Tasks", render_model_capability_route_promotion_bounded_real_replay_repair_plan_markdown(report))
        self.assertIn("repair plan", render_model_capability_route_promotion_bounded_real_replay_repair_plan_html(report))


if __name__ == "__main__":
    unittest.main()
