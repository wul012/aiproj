from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch,
    locate_objective_contract,
    locate_partial_hit_diagnostic,
    locate_seed_revision,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_artifacts import (
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_html,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_markdown,
    render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_text,
    write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch import main as cli_main


class BoundedObjectiveUnassistedRepairSeedRevisionCurriculumPatchTests(unittest.TestCase):
    def test_builds_no_anchor_loss_and_completion_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "source.txt"
            corpus.write_text("answer: fixed loss\n", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch(
                partial_hit_diagnostic(),
                seed_revision(),
                objective_contract(),
                source_corpus_path=corpus,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready")
        self.assertTrue(report["summary"]["bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready"])
        self.assertGreaterEqual(report["summary"]["patch_example_count"], 18)
        self.assertGreater(report["summary"]["patched_corpus_char_count"], report["summary"]["original_corpus_char_count"])
        self.assertEqual(report["summary"]["decoder_anchor_example_count"], 0)
        self.assertIn("completion_surface_short", report["summary"]["patch_kinds"])
        self.assertIn("fixed_to_loss_bridge", report["summary"]["patch_kinds"])
        self.assertIn("fixed\nloss", report["patched_corpus_text"])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 0)

    def test_patch_fails_when_diagnostic_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "source.txt"
            corpus.write_text("fixed loss\n", encoding="utf-8")
            diagnostic = partial_hit_diagnostic()
            diagnostic["summary"]["bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready"] = False
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch(
                diagnostic,
                seed_revision(),
                objective_contract(),
                source_corpus_path=corpus,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_patch_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "source.txt"
            corpus.write_text("answer: fixed loss\n", encoding="utf-8")
            diagnostic_path = root / "diagnostic" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
            seed_path = root / "seed" / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME
            contract_path = root / "contract" / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
            write_json_payload(partial_hit_diagnostic(), diagnostic_path)
            write_json_payload(seed_revision(), seed_path)
            write_json_payload(objective_contract(), contract_path)
            self.assertEqual(locate_partial_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_seed_revision(seed_path.parent), seed_path)
            self.assertEqual(locate_objective_contract(contract_path.parent), contract_path)
            report = build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch(
                partial_hit_diagnostic(),
                seed_revision(),
                objective_contract(),
                source_corpus_path=corpus,
            )
            outputs = write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_outputs(report, root / "out")
            cli_main(
                [
                    "--partial-hit-diagnostic",
                    str(diagnostic_path.parent),
                    "--seed-revision",
                    str(seed_path.parent),
                    "--objective-contract",
                    str(contract_path.parent),
                    "--source-corpus",
                    str(corpus),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-patch-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "jsonl", "corpus", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME))
        self.assertTrue(outputs["corpus"].endswith(BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME))
        self.assertIn("patch_example_count=", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_text(report))
        self.assertIn("Patch Examples", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_markdown(report))
        self.assertIn("Patch Examples", render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_html(report))


def partial_hit_diagnostic() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready": True,
            "partial_hit_case_count": 2,
            "zero_hit_case_count": 1,
            "hit_terms": ["fixed"],
            "missed_terms": ["fixed", "loss"],
        },
    }


def seed_revision() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_unassisted_repair_seed_revision_ready": True,
            "example_count": 24,
            "neutral_prompt_example_count": 18,
            "decoder_anchor_example_count": 0,
        },
    }


def objective_contract() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_contract_ready": True,
            "contract_case_count": 3,
            "unchanged_suite_check_required": True,
        },
        "objective_contract": {"required_exact_completion": "fixed loss"},
        "contract_cases": [
            {"case_id": "canonical_direct_completion", "prompt": "Answer with exactly two tokens: fixed loss\nanswer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "minimal_direct_completion", "prompt": "Answer with exactly two words: fixed loss\nanswer:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
            {"case_id": "completion_label_surface", "prompt": "Complete with exactly two tokens: fixed loss\ncompletion:", "expected_completion": "fixed loss", "required_terms": ["fixed", "loss"]},
        ],
    }


if __name__ == "__main__":
    unittest.main()
