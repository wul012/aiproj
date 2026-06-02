from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch import (
    EXACT_SURFACE_REPAIR_ROWS,
    build_exact_surface_repair_contract_patch,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch_artifacts import (
    render_exact_surface_repair_contract_patch_html,
    render_exact_surface_repair_contract_patch_markdown,
    render_exact_surface_repair_contract_patch_text,
    write_exact_surface_repair_contract_patch_outputs,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch import FIXED_PRESERVING_TRANSFER_ROWS
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE


class ExactSurfaceRepairContractPatchTests(unittest.TestCase):
    def test_patch_adds_budgeted_near_exact_rows(self) -> None:
        report = build_exact_surface_repair_contract_patch(
            repair_plan=repair_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_contract_patch_ready")
        self.assertEqual(report["summary"]["exact_surface_repair_row_count"], len(EXACT_SURFACE_REPAIR_ROWS))
        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertTrue(all(row in report["contract"]["training_rows"] for row in FIXED_PRESERVING_TRANSFER_ROWS))
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_patch_fails_for_wrong_base_contract(self) -> None:
        base = base_contract_fixture()
        base["decision"] = "pair_readiness_direct_completion_surface_contract_ready"
        report = build_exact_surface_repair_contract_patch(
            repair_plan=repair_plan_fixture(),
            base_contract_report=base,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("base_contract_decision", [issue["id"] for issue in report["issues"]])

    def test_patch_can_be_materialized(self) -> None:
        report = build_exact_surface_repair_contract_patch(
            repair_plan=repair_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(report, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_outputs_render_all_formats(self) -> None:
        report = build_exact_surface_repair_contract_patch(
            repair_plan=repair_plan_fixture(),
            base_contract_report=base_contract_fixture(),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_exact_surface_repair_contract_patch_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("patch_ready=True", render_exact_surface_repair_contract_patch_text(report))
        self.assertIn("Exact-Surface Repair Contract Patch", render_exact_surface_repair_contract_patch_markdown(report))
        self.assertIn("MiniGPT exact-surface repair contract patch", render_exact_surface_repair_contract_patch_html(report))


def repair_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_exact_surface_repair_plan_ready",
        "plan": {
            "proposed_next_artifact": "pair_readiness_exact_surface_repair_contract_patch",
            "repair_row_budget": 4,
        },
        "summary": {"plan_ready": True},
    }


def base_contract_fixture() -> dict[str, object]:
    training_rows = [
        "fixed=fixed",
        "loss=loss",
        *FIXED_PRESERVING_TRANSFER_ROWS,
    ]
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_contract_patch_ready",
        "summary": {"patch_ready": True},
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
