from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision,
    locate_curriculum_revision,
    locate_objective_contract,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_html,
    render_bounded_objective_unassisted_repair_seed_revision_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_text,
    write_bounded_objective_unassisted_repair_seed_revision_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionTests(unittest.TestCase):
    def test_builds_seed_revision_with_no_decoder_anchors(self) -> None:
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision(curriculum_revision(), objective_contract())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_ready"])
        self.assertEqual(report["summary"]["example_count"], 16)
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertGreater(report["summary"]["neutral_prompt_example_count"], 0)
        self.assertIn("los", report["corpus_text"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run")
        self.assertEqual(resolve_exit_code(report, require_seed_ready=True), 0)

    def test_seed_revision_fails_when_anchors_allowed(self) -> None:
        revision = curriculum_revision()
        revision["summary"]["decoder_anchor_allowed"] = True
        report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision(revision, objective_contract())

        self.assertEqual(report["status"], "fail")
        self.assertIn("decoder_anchor_disallowed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            revision_path = root / "revision" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            write_json_payload(curriculum_revision(), revision_path)
            write_json_payload(objective_contract(), contract_path)
            self.assertEqual(locate_curriculum_revision(revision_path.parent), revision_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision(curriculum_revision(), objective_contract())
            outputs = write_bounded_objective_unassisted_repair_seed_revision_outputs(report, root / "out")
            cli_main(
                [
                    "--curriculum-revision",
                    str(revision_path.parent),
                    "--objective-contract",
                    str(contract_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-seed-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME))
        self.assertIn("bounded_objective_unassisted_repair_seed_revision_ready=True", render_bounded_objective_unassisted_repair_seed_revision_text(report))
        self.assertIn("Seed Examples", render_bounded_objective_unassisted_repair_seed_revision_markdown(report))
        self.assertIn("Seed Examples", render_bounded_objective_unassisted_repair_seed_revision_html(report))


def curriculum_revision() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_curriculum_revision_ready": True,
            "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision",
            "decoder_anchor_allowed": False,
        },
    }


def objective_contract() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_objective_contract_ready": True},
        "objective_contract": {"target_terms": ["fixed", "loss"]},
        "contract_cases": [
            {"case_id": "canonical_direct_completion", "prompt": "Answer with exactly two tokens: fixed loss\nanswer:", "required_terms": ["fixed", "loss"]},
            {"case_id": "completion_label_surface", "prompt": "Complete the objective response.\nanswer:", "required_terms": ["fixed", "loss"]},
        ],
    }


if __name__ == "__main__":
    unittest.main()
