from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch import (
    FIXED_PRESERVING_TRANSFER_ROWS,
    build_fixed_preserving_transfer_contract_patch,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch_artifacts import (
    render_fixed_preserving_transfer_contract_patch_html,
    render_fixed_preserving_transfer_contract_patch_markdown,
    render_fixed_preserving_transfer_contract_patch_text,
    write_fixed_preserving_transfer_contract_patch_outputs,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE


class FixedPreservingTransferContractPatchTests(unittest.TestCase):
    def test_patch_adds_only_budgeted_fixed_preserving_rows(self) -> None:
        report = build_fixed_preserving_transfer_contract_patch(
            transfer_plan=transfer_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_preserving_transfer_contract_patch_ready")
        self.assertEqual(report["summary"]["fixed_preserving_transfer_row_count"], len(FIXED_PRESERVING_TRANSFER_ROWS))
        self.assertLessEqual(len(FIXED_PRESERVING_TRANSFER_ROWS), 4)
        self.assertIn("fixed=fixed", report["contract"]["training_rows"])
        self.assertIn("loss=loss", report["contract"]["training_rows"])
        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertFalse(any(row.startswith("pair_transfer ") for row in FIXED_PRESERVING_TRANSFER_ROWS))
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_patch_fails_when_plan_is_wrong_artifact(self) -> None:
        plan = transfer_plan_fixture()
        plan["plan"]["proposed_next_artifact"] = "pair_readiness_pair_prompt_transfer_contract_patch"
        report = build_fixed_preserving_transfer_contract_patch(
            transfer_plan=plan,
            base_contract_report=base_contract_fixture(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])

    def test_patch_can_be_materialized(self) -> None:
        report = build_fixed_preserving_transfer_contract_patch(
            transfer_plan=transfer_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(report, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_outputs_render_all_formats(self) -> None:
        report = build_fixed_preserving_transfer_contract_patch(
            transfer_plan=transfer_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_fixed_preserving_transfer_contract_patch_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("patch_ready=True", render_fixed_preserving_transfer_contract_patch_text(report))
        self.assertIn("Fixed-Preserving Transfer Contract Patch", render_fixed_preserving_transfer_contract_patch_markdown(report))
        self.assertIn("MiniGPT fixed-preserving transfer contract patch", render_fixed_preserving_transfer_contract_patch_html(report))


def transfer_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_plan_ready",
        "plan": {
            "proposed_next_artifact": "pair_readiness_fixed_preserving_transfer_contract_patch",
            "transfer_row_budget": 4,
        },
        "summary": {"plan_ready": True},
    }


def base_contract_fixture() -> dict[str, object]:
    training_rows = [
        "fixed=fixed",
        "loss=loss",
        "fixed=f",
        "loss=l",
        "pair_surface order=fixed_then_loss | fixed=fixed | loss=loss",
        "direct_completion fixed branch keeps fixed not loss",
        "direct_completion loss branch keeps loss not fixed",
        "direct_completion fixed surface cannot answer loss",
    ]
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_completion_surface_contract_ready",
        "summary": {"contract_ready": True},
        "contract": {
            "training_rows": training_rows,
            "evaluation_probes": [
                {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed"},
                {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss"},
                {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss"},
            ],
            "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        },
    }


if __name__ == "__main__":
    unittest.main()
