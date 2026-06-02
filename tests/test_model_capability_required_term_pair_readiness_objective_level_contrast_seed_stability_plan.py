from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan import (
    build_objective_level_contrast_seed_stability_plan,
    locate_seed_stability_plan_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_seed_stability_plan_artifacts import (
    render_objective_level_contrast_seed_stability_plan_html,
    render_objective_level_contrast_seed_stability_plan_markdown,
    render_objective_level_contrast_seed_stability_plan_text,
    write_objective_level_contrast_seed_stability_plan_outputs,
)


class ObjectiveLevelContrastSeedStabilityPlanTests(unittest.TestCase):
    def test_seed_stability_plan_ready_from_promotion_guard(self) -> None:
        report = build_objective_level_contrast_seed_stability_plan(promotion_guard_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_seed_stability_plan_ready")
        self.assertTrue(report["summary"]["seed_stability_plan_ready"])
        self.assertEqual(report["summary"]["additional_seed_count"], 2)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_promotion_is_already_allowed(self) -> None:
        guard = promotion_guard_fixture()
        guard["summary"]["promotion_allowed"] = True
        report = build_objective_level_contrast_seed_stability_plan(guard)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_not_allowed_yet", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_plan_lists_expected_seed_artifacts(self) -> None:
        report = build_objective_level_contrast_seed_stability_plan(promotion_guard_fixture())
        artifacts = report["plan"]["required_next_artifacts"]

        self.assertIn("pair_readiness_objective_level_contrast_seed_3737_training_run", artifacts)
        self.assertIn("pair_readiness_objective_level_contrast_seed_stability_rollup", artifacts)

    def test_locator_accepts_directory_and_outputs_render(self) -> None:
        report = build_objective_level_contrast_seed_stability_plan(promotion_guard_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(locate_seed_stability_plan_source(root).name, "model_capability_required_term_pair_readiness_objective_level_contrast_promotion_guard.json")
            outputs = write_objective_level_contrast_seed_stability_plan_outputs(report, root / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("seed_stability_plan_ready=True", render_objective_level_contrast_seed_stability_plan_text(report))
        self.assertIn("Objective-Level Contrast Seed Stability Plan", render_objective_level_contrast_seed_stability_plan_markdown(report))
        self.assertIn("MiniGPT objective-level contrast seed stability plan", render_objective_level_contrast_seed_stability_plan_html(report))


def promotion_guard_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_level_contrast_promotion_guard_ready_for_seed_stability",
        "summary": {
            "promotion_guard_ready": True,
            "promotion_allowed": False,
        },
        "guard": {"required_next_artifact": "pair_readiness_objective_level_contrast_seed_stability_plan"},
    }


if __name__ == "__main__":
    unittest.main()
