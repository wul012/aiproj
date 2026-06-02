from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup import (
    build_objective_level_contrast_seed_stability_rollup,
    locate_seed_stability_rollup_plan,
    locate_seed_stability_rollup_replay,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_rollup_artifacts import (
    render_objective_level_contrast_seed_stability_rollup_html,
    render_objective_level_contrast_seed_stability_rollup_markdown,
    render_objective_level_contrast_seed_stability_rollup_text,
    write_objective_level_contrast_seed_stability_rollup_outputs,
)


class ObjectiveLevelContrastSeedStabilityRollupTests(unittest.TestCase):
    def test_rollup_ready_when_all_planned_seed_replays_are_ready(self) -> None:
        report = build_objective_level_contrast_seed_stability_rollup(
            seed_stability_plan_fixture(),
            [
                (3636, replay_fixture(3), "seed-3636.json"),
                (3737, replay_fixture(2), "seed-3737.json"),
                (3838, replay_fixture(2), "seed-3838.json"),
            ],
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_seed_stability_ready_for_acceptance_review")
        self.assertTrue(report["summary"]["acceptance_review_ready"])
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertEqual(report["summary"]["ready_replay_count"], 3)
        self.assertFalse(report["summary"]["uniform_pair_full_strength"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_rollup_fails_when_expected_seed_is_missing(self) -> None:
        report = build_objective_level_contrast_seed_stability_rollup(
            seed_stability_plan_fixture(),
            [
                (3636, replay_fixture(3), "seed-3636.json"),
                (3737, replay_fixture(2), "seed-3737.json"),
            ],
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_expected_seeds_observed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_rollup_fails_when_a_replay_is_not_ready(self) -> None:
        failing_replay = replay_fixture(0)
        failing_replay["summary"]["required_all_pair_full"] = False
        report = build_objective_level_contrast_seed_stability_rollup(
            seed_stability_plan_fixture(),
            [
                (3636, replay_fixture(3), "seed-3636.json"),
                (3737, failing_replay, "seed-3737.json"),
                (3838, replay_fixture(2), "seed-3838.json"),
            ],
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_zero_pair_full_seed", [issue["id"] for issue in report["issues"]])
        self.assertIn("every_observed_replay_ready", [issue["id"] for issue in report["issues"]])

    def test_locator_accepts_directories_and_render_outputs(self) -> None:
        report = build_objective_level_contrast_seed_stability_rollup(
            seed_stability_plan_fixture(),
            [
                (3636, replay_fixture(3), "seed-3636.json"),
                (3737, replay_fixture(2), "seed-3737.json"),
                (3838, replay_fixture(2), "seed-3838.json"),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(locate_seed_stability_rollup_plan(root).name, "model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan.json")
            self.assertEqual(locate_seed_stability_rollup_replay(root).name, "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json")
            outputs = write_objective_level_contrast_seed_stability_rollup_outputs(report, root / "rollup")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("acceptance_review_ready=True", render_objective_level_contrast_seed_stability_rollup_text(report))
        self.assertIn("Objective-Level Contrast Seed Stability Rollup", render_objective_level_contrast_seed_stability_rollup_markdown(report))
        self.assertIn("MiniGPT objective-level contrast seed stability rollup", render_objective_level_contrast_seed_stability_rollup_html(report))


def seed_stability_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_level_contrast_seed_stability_plan_ready",
        "summary": {"seed_stability_plan_ready": True},
        "plan": {
            "source_seed": 3636,
            "additional_seeds": [3737, 3838],
            "required_seed_count": 3,
            "minimum_ready_replay_count": 2,
        },
    }


def replay_fixture(pair_full_count: int) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready",
        "summary": {
            "exact_heldout_pair_full": pair_full_count > 0,
            "required_all_pair_full": pair_full_count > 0,
            "pair_full_count": pair_full_count,
            "pair_full_rate": round(pair_full_count / 3, 4),
        },
    }


if __name__ == "__main__":
    unittest.main()
