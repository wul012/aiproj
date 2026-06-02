from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison import (
    build_objective_level_contrast_route_comparison,
    locate_objective_level_contrast_route_comparison_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_route_comparison_artifacts import (
    render_objective_level_contrast_route_comparison_html,
    render_objective_level_contrast_route_comparison_markdown,
    render_objective_level_contrast_route_comparison_text,
    write_objective_level_contrast_route_comparison_outputs,
)


class ObjectiveLevelContrastRouteComparisonTests(unittest.TestCase):
    def test_objective_route_wins_over_prior_partial_routes(self) -> None:
        report = build_objective_level_contrast_route_comparison(partial_replay(), partial_replay(), ready_replay())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_replay_wins_needs_promotion_guard")
        self.assertTrue(report["summary"]["objective_route_best"])
        self.assertEqual(report["summary"]["objective_pair_full_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_fails_when_objective_replay_is_not_pass(self) -> None:
        objective = ready_replay()
        objective["status"] = "fail"
        report = build_objective_level_contrast_route_comparison(partial_replay(), partial_replay(), objective)

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_comparison_requires_objective_to_beat_prior_pair_full_count(self) -> None:
        prior = ready_replay()
        report = build_objective_level_contrast_route_comparison(prior, partial_replay(), ready_replay())

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_pair_full_count_wins", [issue["id"] for issue in report["issues"]])

    def test_locator_accepts_directory_and_outputs_render(self) -> None:
        report = build_objective_level_contrast_route_comparison(partial_replay(), partial_replay(), ready_replay())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_objective_level_contrast_route_comparison_source(root).name,
                "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json",
            )
            outputs = write_objective_level_contrast_route_comparison_outputs(report, root / "comparison")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("objective_route_best=True", render_objective_level_contrast_route_comparison_text(report))
        self.assertIn("Objective-Level Contrast Route Comparison", render_objective_level_contrast_route_comparison_markdown(report))
        self.assertIn("MiniGPT objective-level contrast route comparison", render_objective_level_contrast_route_comparison_html(report))


def partial_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial",
        "summary": {"exact_heldout_pair_full": False, "required_all_pair_full": False, "pair_full_count": 1},
        "replay_rows": [
            {"spec_id": "exact-heldout-pair", "default_continuation_hit_count": 1, "suppression_continuation_hit_count": 1},
            {"spec_id": "arrow-heldout-pair", "default_continuation_hit_count": 2, "suppression_continuation_hit_count": 2},
        ],
        "interpretation": {"model_quality_claim": "not_claimed"},
    }


def ready_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready",
        "summary": {"exact_heldout_pair_full": True, "required_all_pair_full": True, "pair_full_count": 3},
        "replay_rows": [
            {"spec_id": "exact-heldout-pair", "default_continuation_hit_count": 2, "suppression_continuation_hit_count": 2},
            {"spec_id": "spaced-heldout-pair", "default_continuation_hit_count": 2, "suppression_continuation_hit_count": 2},
            {"spec_id": "arrow-heldout-pair", "default_continuation_hit_count": 2, "suppression_continuation_hit_count": 2},
        ],
        "interpretation": {"model_quality_claim": "pair_probe_replay_ready"},
    }


if __name__ == "__main__":
    unittest.main()
