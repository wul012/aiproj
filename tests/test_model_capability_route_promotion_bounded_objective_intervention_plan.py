from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_intervention_plan import (
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_intervention_plan,
    locate_intervention_decision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_intervention_plan_artifacts import (
    render_bounded_objective_intervention_plan_html,
    render_bounded_objective_intervention_plan_markdown,
    render_bounded_objective_intervention_plan_text,
    write_bounded_objective_intervention_plan_outputs,
)
from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision import (
    BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_intervention_plan import main as cli_main


class BoundedObjectiveInterventionPlanTests(unittest.TestCase):
    def test_builds_objective_contract_intervention_plan(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_intervention_plan(intervention_decision())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_intervention_plan_ready")
        self.assertTrue(report["summary"]["objective_intervention_plan_ready"])
        self.assertEqual(report["summary"]["contract_id"], "bounded_fixed_loss_direct_completion_contract")
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_contract")
        self.assertTrue(report["summary"]["unchanged_suite_check_required"])
        self.assertEqual(report["summary"]["work_item_count"], 5)
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_plan_fails_when_objective_track_is_not_selected(self) -> None:
        decision = intervention_decision()
        decision["summary"]["selected_intervention_track"] = "partial_decoder_profile_recovery_review"

        report = build_model_capability_route_promotion_bounded_objective_intervention_plan(decision)

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_track_selected", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_plan_fails_when_new_training_is_not_blocked(self) -> None:
        decision = intervention_decision()
        decision["summary"]["new_training_allowed"] = True

        report = build_model_capability_route_promotion_bounded_objective_intervention_plan(decision)

        self.assertEqual(report["status"], "fail")
        self.assertIn("training_blocked_until_plan", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "decision" / BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME
            write_json_payload(intervention_decision(), input_path)
            self.assertEqual(locate_intervention_decision(input_path.parent), input_path)
            report = build_model_capability_route_promotion_bounded_objective_intervention_plan(intervention_decision())
            outputs = write_bounded_objective_intervention_plan_outputs(report, root / "plan")
            cli_main(
                [
                    "--intervention-decision",
                    str(input_path.parent),
                    "--out-dir",
                    str(root / "cli-plan"),
                    "--require-plan-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME))
        self.assertIn("objective_intervention_plan_ready=True", render_bounded_objective_intervention_plan_text(report))
        self.assertIn("Objective Contract", render_bounded_objective_intervention_plan_markdown(report))
        self.assertIn("Work Items", render_bounded_objective_intervention_plan_html(report))


def intervention_decision() -> dict:
    return {
        "status": "pass",
        "decision": "stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention",
        "summary": {
            "intervention_decision_ready": True,
            "selected_intervention_track": "objective_contract_intervention_first",
            "fallback_intervention_track": "architecture_capacity_probe_if_objective_contract_fails",
            "recommended_next_artifact": "model_capability_route_promotion_bounded_objective_intervention_plan",
            "promotion_allowed": False,
            "new_training_allowed": False,
        },
        "route": {
            "closed_route": "decoder_anchor_rebalanced_rescue",
            "selected_intervention_track": "objective_contract_intervention_first",
            "fallback_intervention_track": "architecture_capacity_probe_if_objective_contract_fails",
        },
    }


if __name__ == "__main__":
    unittest.main()
