from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_seed import (
    BOUNDED_OBJECTIVE_SEED_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_seed,
    locate_objective_contract,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_seed_artifacts import (
    render_bounded_objective_seed_html,
    render_bounded_objective_seed_markdown,
    render_bounded_objective_seed_text,
    write_bounded_objective_seed_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_seed import main as cli_main


class BoundedObjectiveSeedTests(unittest.TestCase):
    def test_builds_direct_objective_seed_from_contract(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_seed(objective_contract())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_seed_ready")
        self.assertTrue(report["summary"]["bounded_objective_seed_ready"])
        self.assertEqual(report["summary"]["example_count"], 18)
        self.assertEqual(report["summary"]["direct_example_count"], 18)
        self.assertEqual(report["summary"]["carry_forward_example_count"], 0)
        self.assertIn("fixed loss", report["corpus_text"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_training_run")
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_seed_fails_when_contract_points_elsewhere(self) -> None:
        contract = objective_contract()
        contract["summary"]["proposed_next_artifact"] = "model_capability_route_promotion_bounded_objective_replay_comparison"

        report = build_model_capability_route_promotion_bounded_objective_seed(contract)

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 1)

    def test_seed_fails_when_blueprint_count_drifts(self) -> None:
        contract = objective_contract()
        contract["seed_blueprint"]["planned_example_count"] = 12

        report = build_model_capability_route_promotion_bounded_objective_seed(contract)

        self.assertEqual(report["status"], "fail")
        self.assertIn("planned_count_matches", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            write_json_payload(objective_contract(), input_path)
            self.assertEqual(locate_objective_contract(input_path.parent), input_path)
            report = build_model_capability_route_promotion_bounded_objective_seed(objective_contract())
            outputs = write_bounded_objective_seed_outputs(report, root / "seed")
            cli_main(
                [
                    "--objective-contract",
                    str(input_path.parent),
                    "--out-dir",
                    str(root / "cli-seed"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_SEED_JSON_FILENAME))
        self.assertIn("bounded_objective_seed_ready=True", render_bounded_objective_seed_text(report))
        self.assertIn("Seed Examples", render_bounded_objective_seed_markdown(report))
        self.assertIn("Seed Examples", render_bounded_objective_seed_html(report))


def objective_contract() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_contract_ready": True,
            "contract_id": "bounded_fixed_loss_direct_completion_contract",
            "target_terms": ["fixed", "loss"],
            "contract_case_count": 3,
            "planned_seed_example_count": 18,
            "promotion_claim_allowed": False,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_seed",
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
                "surface": "canonical_direct_completion_surface",
            },
            {
                "case_id": "minimal_direct_completion",
                "prompt": "Answer with exactly two words: fixed loss\nanswer:",
                "expected_completion": "fixed loss",
                "required_terms": ["fixed", "loss"],
                "surface": "canonical_direct_completion_surface",
            },
            {
                "case_id": "completion_label_surface",
                "prompt": "Complete with exactly two tokens: fixed loss\ncompletion:",
                "expected_completion": "fixed loss",
                "required_terms": ["fixed", "loss"],
                "surface": "canonical_direct_completion_surface",
            },
        ],
        "seed_blueprint": {
            "blueprint_id": "bounded_objective_direct_seed_v837_blueprint",
            "source_contract_case_count": 3,
            "examples_per_case": 6,
            "planned_example_count": 18,
            "next_artifact": "model_capability_route_promotion_bounded_objective_seed",
        },
    }


if __name__ == "__main__":
    unittest.main()
