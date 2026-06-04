from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_review_artifacts import (
    write_bounded_objective_decoder_anchor_policy_review_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_plan import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_PLAN_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan,
    locate_decoder_anchor_policy_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_plan_artifacts import (
    render_bounded_objective_unassisted_repair_plan_html,
    render_bounded_objective_unassisted_repair_plan_markdown,
    render_bounded_objective_unassisted_repair_plan_text,
    write_bounded_objective_unassisted_repair_plan_outputs,
)
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan import main as cli_main


class BoundedObjectiveUnassistedRepairPlanTests(unittest.TestCase):
    def test_plan_is_ready_after_assisted_anchor_path_closed(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan(policy_review())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_plan_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_plan_ready"])
        self.assertEqual(report["summary"]["work_item_count"], 5)
        self.assertEqual(report["summary"]["acceptance_gate_count"], 4)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_plan_fails_if_anchor_path_not_closed(self) -> None:
        review = policy_review()
        review["summary"]["assisted_anchor_path_closed"] = False
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan(review)

        self.assertEqual(report["status"], "fail")
        self.assertIn("assisted_anchor_path_closed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_outputs = write_bounded_objective_decoder_anchor_policy_review_outputs(policy_review(), root / "review")
            self.assertEqual(locate_decoder_anchor_policy_review(Path(review_outputs["json"]).parent), Path(review_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan(policy_review())
            outputs = write_bounded_objective_unassisted_repair_plan_outputs(report, root / "plan")
            cli_main(
                [
                    "--policy-review",
                    str(Path(review_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-plan"),
                    "--require-plan-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_PLAN_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_plan_ready=True", render_bounded_objective_unassisted_repair_plan_text(report))
        self.assertIn("Acceptance Gates", render_bounded_objective_unassisted_repair_plan_markdown(report))
        self.assertIn("Work Items", render_bounded_objective_unassisted_repair_plan_html(report))


def policy_review() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_decoder_anchor_policy_review_ready": True,
            "assisted_anchor_path_closed": True,
            "selected_track": "unassisted_objective_repair",
            "promotion_ready": False,
        },
        "signals": {
            "policy_applied_pass_count": 3,
            "new_text_pass_count": 0,
            "assisted_only_recovery": True,
        },
        "recommendations": [
            {"id": "close_assisted_anchor_path", "priority": "high", "action": "stop_treating_decoder_anchor_policy_as_capability_path"}
        ],
    }


if __name__ == "__main__":
    unittest.main()
