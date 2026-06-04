from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_contract,
    locate_objective_intervention_plan,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract_artifacts import (
    render_bounded_objective_contract_html,
    render_bounded_objective_contract_markdown,
    render_bounded_objective_contract_text,
    write_bounded_objective_contract_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_intervention_plan import (
    BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_contract import main as cli_main


class BoundedObjectiveContractTests(unittest.TestCase):
    def test_builds_bounded_objective_contract_from_ready_plan(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_contract(objective_intervention_plan())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_contract_ready")
        self.assertTrue(report["summary"]["bounded_objective_contract_ready"])
        self.assertEqual(report["summary"]["target_terms"], ["fixed", "loss"])
        self.assertEqual(report["summary"]["contract_case_count"], 3)
        self.assertEqual(report["summary"]["planned_seed_example_count"], 18)
        self.assertFalse(report["summary"]["promotion_claim_allowed"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_seed")
        self.assertEqual(resolve_exit_code(report, require_contract_ready=True), 0)

    def test_contract_fails_when_plan_points_elsewhere(self) -> None:
        plan = objective_intervention_plan()
        plan["summary"]["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_training_run"

        report = build_model_capability_route_promotion_bounded_objective_contract(plan)

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_contract_ready=True), 1)

    def test_contract_fails_when_completion_is_not_exact(self) -> None:
        plan = objective_intervention_plan()
        plan["objective_contract"]["canonical_completion"] = "fixed"

        report = build_model_capability_route_promotion_bounded_objective_contract(plan)

        self.assertEqual(report["status"], "fail")
        self.assertIn("canonical_completion_exact", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "plan" / BOUNDED_OBJECTIVE_INTERVENTION_PLAN_JSON_FILENAME
            write_json_payload(objective_intervention_plan(), input_path)
            self.assertEqual(locate_objective_intervention_plan(input_path.parent), input_path)
            report = build_model_capability_route_promotion_bounded_objective_contract(objective_intervention_plan())
            outputs = write_bounded_objective_contract_outputs(report, root / "contract")
            cli_main(
                [
                    "--objective-intervention-plan",
                    str(input_path.parent),
                    "--out-dir",
                    str(root / "cli-contract"),
                    "--require-contract-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME))
        self.assertIn("bounded_objective_contract_ready=True", render_bounded_objective_contract_text(report))
        self.assertIn("Contract Cases", render_bounded_objective_contract_markdown(report))
        self.assertIn("Seed Blueprint", render_bounded_objective_contract_html(report))


def objective_intervention_plan() -> dict:
    return {
        "status": "pass",
        "summary": {
            "objective_intervention_plan_ready": True,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_contract",
        },
        "objective_contract": {
            "contract_id": "bounded_fixed_loss_direct_completion_contract",
            "target_terms": ["fixed", "loss"],
            "canonical_prompt": "Answer with exactly two tokens: fixed loss\nanswer:",
            "canonical_completion": "fixed loss",
            "allowed_surfaces": [
                "canonical_direct_completion_surface",
                "v803_prompt_surface_replay_as_holdout_check",
            ],
            "blocked_surfaces": [
                "forced_prefix_decoder_anchor_as_quality_claim",
                "carry_forward_only_seed_expansion",
                "more_training_epochs_without_contract_change",
            ],
            "unchanged_suite_check_required": True,
        },
        "work_items": [
            {"item_id": "contract_fixture"},
            {"item_id": "direct_seed_corpus"},
            {"item_id": "controlled_training"},
            {"item_id": "dual_replay"},
            {"item_id": "fallback_decision"},
        ],
        "plan": {
            "objective_contract": {},
            "work_items": [],
        },
    }


if __name__ == "__main__":
    unittest.main()
