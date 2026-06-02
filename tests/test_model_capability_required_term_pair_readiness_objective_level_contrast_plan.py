from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_plan import (
    build_objective_level_contrast_plan,
    locate_objective_level_contrast_plan_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_plan_artifacts import (
    render_objective_level_contrast_plan_html,
    render_objective_level_contrast_plan_markdown,
    render_objective_level_contrast_plan_text,
    write_objective_level_contrast_plan_outputs,
)


class ObjectiveLevelContrastPlanTests(unittest.TestCase):
    def test_plan_ready_from_selected_objective_route(self) -> None:
        report = build_objective_level_contrast_plan(selector_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_level_contrast_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_objective_level_contrast_contract")
        self.assertEqual(report["summary"]["planned_training_row_count"], 26)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_decoding_route_is_selected(self) -> None:
        selector = selector_fixture()
        selector["selector"]["selected_route"] = "decode_side_constraint_probe"
        selector["summary"]["selected_route"] = "decode_side_constraint_probe"
        report = build_objective_level_contrast_plan(selector)

        self.assertEqual(report["status"], "fail")
        self.assertIn("selected_objective_route", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_plan_carries_heldout_boundaries_and_non_goals(self) -> None:
        report = build_objective_level_contrast_plan(selector_fixture())
        plan = report["plan"]

        self.assertIn("exact-heldout-pair prompt surface remains eval-only", plan["heldout_boundaries"])
        self.assertIn("do not add another near-exact bridge row patch", plan["non_goals"])

    def test_locator_accepts_directory_and_outputs_render(self) -> None:
        report = build_objective_level_contrast_plan(selector_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_objective_level_contrast_plan_source(root).name,
                "model_capability_required_term_pair_readiness_objective_or_decoding_alternative_selector.json",
            )
            outputs = write_objective_level_contrast_plan_outputs(report, root / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_objective_level_contrast_plan_ready", render_objective_level_contrast_plan_text(report))
        self.assertIn("Objective-Level Contrast Plan", render_objective_level_contrast_plan_markdown(report))
        self.assertIn("MiniGPT objective-level contrast plan", render_objective_level_contrast_plan_html(report))


def selector_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_or_decoding_alternative_selected",
        "summary": {
            "selector_ready": True,
            "selected_route": "objective_level_contrast",
            "selected_score": 92,
            "proposed_next_artifact": "pair_readiness_objective_level_contrast_plan",
        },
        "selector": {
            "ready": True,
            "selected_route": "objective_level_contrast",
            "selected_score": 92,
            "proposed_next_artifact": "pair_readiness_objective_level_contrast_plan",
        },
        "route_rows": [
            {"route": "objective_level_contrast", "selected": True},
            {"route": "decode_side_constraint_probe", "selected": False},
            {"route": "fresh_seed_stability", "selected": False},
        ],
    }


if __name__ == "__main__":
    unittest.main()
