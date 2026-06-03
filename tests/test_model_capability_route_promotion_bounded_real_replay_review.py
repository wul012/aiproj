from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay import build_model_capability_route_promotion_bounded_real_replay
from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_review import (
    build_model_capability_route_promotion_bounded_real_replay_review,
    locate_route_promotion_bounded_real_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_review_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_review_html,
    render_model_capability_route_promotion_bounded_real_replay_review_markdown,
    render_model_capability_route_promotion_bounded_real_replay_review_text,
    write_model_capability_route_promotion_bounded_real_replay_review_outputs,
)
from scripts.review_model_capability_route_promotion_bounded_real_replay import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay import partial_runner, passing_runner, ready_replay_inputs


def ready_real_replay(root: Path, *, all_cases_pass: bool = False) -> tuple[dict, Path]:
    suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
    replay = build_model_capability_route_promotion_bounded_real_replay(
        review,
        suite,
        dry_run,
        checkpoint_path=checkpoint,
        tokenizer_path=tokenizer,
        generator_runner=passing_runner if all_cases_pass else partial_runner,
    )
    outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay, root / "real-replay")
    return replay, Path(outputs["json"])


class ModelCapabilityRoutePromotionBoundedRealReplayReviewTests(unittest.TestCase):
    def test_review_routes_partial_real_replay_to_repair_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            replay, replay_path = ready_real_replay(Path(tmp))
            report = build_model_capability_route_promotion_bounded_real_replay_review(
                replay,
                real_replay_path=replay_path,
                minimum_pass_rate_for_repair_review=0.2,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_review_needs_repair")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertTrue(report["summary"]["repair_review_ready"])
        self.assertEqual(report["summary"]["passed_case_count"], 1)
        self.assertIn("partial_required_terms_generated", report["summary"]["diagnosis_counts"])
        self.assertEqual(resolve_exit_code(report, require_review_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_pass=True, require_promotion_ready=True), 1)

    def test_review_accepts_all_pass_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            replay, _ = ready_real_replay(Path(tmp), all_cases_pass=True)
            report = build_model_capability_route_promotion_bounded_real_replay_review(replay)

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_review_accepted")
        self.assertTrue(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_review_pass=True, require_promotion_ready=True), 0)

    def test_review_fails_when_source_replay_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            replay, _ = ready_real_replay(Path(tmp))
            replay["status"] = "fail"
            report = build_model_capability_route_promotion_bounded_real_replay_review(replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("real_replay_status_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_review_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay, replay_path = ready_real_replay(root)
            self.assertEqual(locate_route_promotion_bounded_real_replay(replay_path.parent), replay_path)
            report = build_model_capability_route_promotion_bounded_real_replay_review(replay, real_replay_path=replay_path)
            outputs = write_model_capability_route_promotion_bounded_real_replay_review_outputs(report, root / "review")
            cli_main(["--real-replay", str(replay_path.parent), "--out-dir", str(root / "cli-review"), "--require-review-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("promotion_ready=False", render_model_capability_route_promotion_bounded_real_replay_review_text(report))
        self.assertIn("Case Reviews", render_model_capability_route_promotion_bounded_real_replay_review_markdown(report))
        self.assertIn("real replay review", render_model_capability_route_promotion_bounded_real_replay_review_html(report))


if __name__ == "__main__":
    unittest.main()
