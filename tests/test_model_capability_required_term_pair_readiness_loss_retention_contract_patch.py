from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_loss_retention_contract_patch import (
    LOSS_RETENTION_ROWS,
    build_loss_retention_contract_patch,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_loss_retention_contract_patch_artifacts import (
    render_loss_retention_contract_patch_html,
    render_loss_retention_contract_patch_markdown,
    render_loss_retention_contract_patch_text,
    write_loss_retention_contract_patch_outputs,
)


class LossRetentionContractPatchTests(unittest.TestCase):
    def test_patch_adds_loss_rows_and_preserves_heldout(self) -> None:
        report = build_loss_retention_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_loss_retention_contract_patch_ready")
        self.assertEqual(report["summary"]["added_training_row_count"], len(LOSS_RETENTION_ROWS))
        self.assertNotIn("fixed=|loss=", report["contract"]["training_rows"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_patched_contract_can_be_materialized(self) -> None:
        patch = build_loss_retention_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(patch, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_patch_fails_for_wrong_plan(self) -> None:
        plan = plan_fixture()
        plan["decision"] = "wrong"
        report = build_loss_retention_contract_patch(repair_plan=plan, base_contract_report=base_contract_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("repair_plan_decision", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_loss_retention_contract_patch(repair_plan=plan_fixture(), base_contract_report=base_contract_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_loss_retention_contract_patch_outputs(report, Path(tmp) / "patch")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_loss_retention_contract_patch_ready", render_loss_retention_contract_patch_text(report))
        self.assertIn("Loss-Retention Contract Patch", render_loss_retention_contract_patch_markdown(report))
        self.assertIn("MiniGPT loss-retention contract patch", render_loss_retention_contract_patch_html(report))


def plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_loss_retention_repair_plan_ready",
        "summary": {"plan_ready": True},
    }


def base_contract_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_split_contract_ready",
        "summary": {"contract_ready": True},
        "contract": {
            "training_rows": ["fixed=f", "fixed=fixed", "loss=l", "loss=loss"],
            "evaluation_probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": "fixed=|loss=", "expected_term": "fixed+loss"},
            ],
            "heldout_pair_probe": "fixed=|loss=",
            "promotion_requirement": "both direct probes must hit",
        },
    }


if __name__ == "__main__":
    unittest.main()
