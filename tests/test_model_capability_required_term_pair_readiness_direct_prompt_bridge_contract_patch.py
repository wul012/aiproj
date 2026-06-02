from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import (
    PAIR_READINESS_CONTRACT_JSON_FILENAMES,
    PAIR_READINESS_READY_CONTRACT_DECISIONS,
    locate_pair_readiness_corpus_materialization_source,
)
from minigpt.model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch import (
    DIRECT_PROMPT_BRIDGE_ROWS,
    PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME,
    build_direct_prompt_bridge_contract_patch,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch_artifacts import (
    render_direct_prompt_bridge_contract_patch_html,
    render_direct_prompt_bridge_contract_patch_markdown,
    render_direct_prompt_bridge_contract_patch_text,
    write_direct_prompt_bridge_contract_patch_outputs,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import write_json_payload


class DirectPromptBridgeContractPatchTests(unittest.TestCase):
    def test_patch_adds_bridge_rows_and_preserves_pair_holdout(self) -> None:
        report = build_direct_prompt_bridge_contract_patch(
            diagnostic_report=diagnostic_fixture(),
            base_contract_report=base_contract_fixture(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_direct_prompt_bridge_contract_patch_ready")
        self.assertEqual(report["summary"]["bridge_row_count"], len(DIRECT_PROMPT_BRIDGE_ROWS))
        self.assertEqual(report["summary"]["fixed_bridge_row_count"], report["summary"]["loss_bridge_row_count"])
        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_patch_fails_for_wrong_diagnostic(self) -> None:
        diagnostic = diagnostic_fixture()
        diagnostic["decision"] = "pair_readiness_surface_mismatch_not_detected"
        report = build_direct_prompt_bridge_contract_patch(
            diagnostic_report=diagnostic,
            base_contract_report=base_contract_fixture(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_decision", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_patch_can_be_materialized(self) -> None:
        report = build_direct_prompt_bridge_contract_patch(
            diagnostic_report=diagnostic_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "patch"
            write_json_payload(report, out_dir / PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME)
            located = locate_pair_readiness_corpus_materialization_source(out_dir)

        self.assertEqual(located.name, PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME)
        self.assertIn(PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME, PAIR_READINESS_CONTRACT_JSON_FILENAMES)
        self.assertIn("pair_readiness_direct_prompt_bridge_contract_patch_ready", PAIR_READINESS_READY_CONTRACT_DECISIONS)

    def test_outputs_render_all_formats(self) -> None:
        report = build_direct_prompt_bridge_contract_patch(
            diagnostic_report=diagnostic_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_direct_prompt_bridge_contract_patch_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_direct_prompt_bridge_contract_patch_ready", render_direct_prompt_bridge_contract_patch_text(report))
        self.assertIn("Direct-Prompt Bridge Contract Patch", render_direct_prompt_bridge_contract_patch_markdown(report))
        self.assertIn("MiniGPT direct-prompt bridge contract patch", render_direct_prompt_bridge_contract_patch_html(report))


def diagnostic_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_surface_mismatch_detected",
        "summary": {
            "recommended_next_artifact": "pair_readiness_direct_prompt_bridge_contract_patch",
            "surface_mismatch_detected": True,
        },
    }


def base_contract_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_structure_contract_ready",
        "contract": {
            "contract_version": 5,
            "training_rows": ["objective=direct_term | term=fixed", "objective=direct_term | term=loss"],
            "evaluation_probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss"},
            ],
            "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        },
        "summary": {"contract_ready": True},
    }


if __name__ == "__main__":
    unittest.main()
