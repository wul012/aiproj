from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_plan_artifacts import (
    write_bounded_objective_unassisted_repair_plan_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed,
    locate_objective_contract,
    locate_unassisted_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_artifacts import (
    render_bounded_objective_unassisted_repair_seed_html,
    render_bounded_objective_unassisted_repair_seed_markdown,
    render_bounded_objective_unassisted_repair_seed_text,
    write_bounded_objective_unassisted_repair_seed_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed import main as cli_main


class BoundedObjectiveUnassistedRepairSeedTests(unittest.TestCase):
    def test_seed_adds_neutral_prompts_and_no_decoder_anchors(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed(repair_plan(), objective_contract())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_ready"])
        self.assertEqual(report["summary"]["example_count"], 16)
        self.assertEqual(report["summary"]["neutral_prompt_example_count"], 8)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("fixed loss", report["corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_seed_fails_when_plan_points_elsewhere(self) -> None:
        plan = repair_plan()
        plan["summary"]["proposed_next_artifact"] = "other_artifact"
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed(plan, objective_contract())

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_outputs = write_bounded_objective_unassisted_repair_plan_outputs(repair_plan(), root / "plan")
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            write_json_payload(objective_contract(), contract_path)
            self.assertEqual(locate_unassisted_repair_plan(Path(plan_outputs["json"]).parent), Path(plan_outputs["json"]))
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed(repair_plan(), objective_contract())
            outputs = write_bounded_objective_unassisted_repair_seed_outputs(report, root / "seed")
            cli_main(
                [
                    "--repair-plan",
                    str(Path(plan_outputs["json"]).parent),
                    "--objective-contract",
                    str(contract_path.parent),
                    "--out-dir",
                    str(root / "cli-seed"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_seed_ready=True", render_bounded_objective_unassisted_repair_seed_text(report))
        self.assertIn("Seed Examples", render_bounded_objective_unassisted_repair_seed_markdown(report))
        self.assertIn("Seed Examples", render_bounded_objective_unassisted_repair_seed_html(report))


def repair_plan() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_plan_ready": True,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed",
        },
    }


def objective_contract() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_contract_ready": True,
            "contract_case_count": 2,
        },
        "objective_contract": {
            "contract_id": "bounded_fixed_loss_direct_completion_contract",
            "target_terms": ["fixed", "loss"],
        },
        "contract_cases": [
            {
                "case_id": "canonical_direct_completion",
                "prompt": "Answer with exactly two tokens: fixed loss\nanswer:",
                "expected_completion": "fixed loss",
                "required_terms": ["fixed", "loss"],
            },
            {
                "case_id": "minimal_direct_completion",
                "prompt": "Answer with exactly two words: fixed loss\nanswer:",
                "expected_completion": "fixed loss",
                "required_terms": ["fixed", "loss"],
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
