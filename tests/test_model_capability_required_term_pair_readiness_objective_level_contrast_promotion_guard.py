from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard import (
    build_objective_level_contrast_promotion_guard,
    locate_promotion_guard_comparison,
    locate_promotion_guard_replay,
    locate_promotion_guard_training,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard_artifacts import (
    render_objective_level_contrast_promotion_guard_html,
    render_objective_level_contrast_promotion_guard_markdown,
    render_objective_level_contrast_promotion_guard_text,
    write_objective_level_contrast_promotion_guard_outputs,
)


class ObjectiveLevelContrastPromotionGuardTests(unittest.TestCase):
    def test_guard_ready_but_not_promotion_allowed(self) -> None:
        report = build_objective_level_contrast_promotion_guard(comparison_fixture(), replay_fixture(), training_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability")
        self.assertTrue(report["summary"]["promotion_guard_ready"])
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertEqual(report["summary"]["required_next_artifact"], "pair_readiness_objective_level_contrast_seed_stability_plan")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_guard_fails_when_comparison_is_not_winner(self) -> None:
        comparison = comparison_fixture()
        comparison["summary"]["objective_route_best"] = False
        report = build_objective_level_contrast_promotion_guard(comparison, replay_fixture(), training_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_route_best", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_guard_fails_when_checkpoint_is_missing(self) -> None:
        training = training_fixture()
        training["training"]["checkpoint_exists"] = False
        report = build_objective_level_contrast_promotion_guard(comparison_fixture(), replay_fixture(), training)

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])

    def test_locators_accept_directories_and_outputs_render(self) -> None:
        report = build_objective_level_contrast_promotion_guard(comparison_fixture(), replay_fixture(), training_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(locate_promotion_guard_comparison(root).name, "model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison.json")
            self.assertEqual(locate_promotion_guard_replay(root).name, "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json")
            self.assertEqual(locate_promotion_guard_training(root).name, "model_capability_required_term_pair_readiness_training_run.json")
            outputs = write_objective_level_contrast_promotion_guard_outputs(report, root / "guard")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("promotion_allowed=False", render_objective_level_contrast_promotion_guard_text(report))
        self.assertIn("Objective-Level Contrast Promotion Guard", render_objective_level_contrast_promotion_guard_markdown(report))
        self.assertIn("MiniGPT objective-level contrast promotion guard", render_objective_level_contrast_promotion_guard_html(report))


def comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard",
        "summary": {"objective_route_best": True, "promotion_guard_required": True},
    }


def replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready",
        "summary": {"required_all_pair_full": True, "pair_full_count": 3},
    }


def training_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"pair_full_observed": True},
        "training": {"checkpoint_exists": True, "tokenizer_exists": True},
        "source_materialization": {"summary": {"training_line_count": 8320}},
    }


if __name__ == "__main__":
    unittest.main()
