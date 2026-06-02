from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import build_pair_readiness_corpus_materialization
from minigpt.model_capability_required_term_pair_readiness_direct_completion_surface_contract import (
    DIRECT_COMPLETION_SURFACE_ROW_FAMILIES,
    build_direct_completion_surface_contract,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_direct_completion_surface_contract_artifacts import (
    render_direct_completion_surface_contract_html,
    render_direct_completion_surface_contract_markdown,
    render_direct_completion_surface_contract_text,
    write_direct_completion_surface_contract_outputs,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE


class DirectCompletionSurfaceContractTests(unittest.TestCase):
    def test_contract_ready_from_bridge_closeout_plan(self) -> None:
        report = build_direct_completion_surface_contract(closeout_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_direct_completion_surface_contract_ready")
        self.assertTrue(report["summary"]["contract_ready"])
        self.assertEqual(report["summary"]["fixed_prefix_row_count"], report["summary"]["loss_prefix_row_count"])
        self.assertIn("fixed=fixed", report["contract"]["training_rows"])
        self.assertIn("loss=loss", report["contract"]["training_rows"])
        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_fails_for_wrong_next_artifact(self) -> None:
        closeout = closeout_fixture()
        closeout["plan"]["proposed_next_artifact"] = "pair_readiness_direct_prompt_bridge_contract_patch"
        report = build_direct_completion_surface_contract(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("next_artifact_matches", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_can_be_materialized(self) -> None:
        report = build_direct_completion_surface_contract(closeout_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            materialized = build_pair_readiness_corpus_materialization(report, out_dir=tmp, repeat=1)

        self.assertEqual(materialized["status"], "pass")
        self.assertEqual(materialized["decision"], "pair_readiness_corpus_materialized")

    def test_outputs_render_all_formats(self) -> None:
        report = build_direct_completion_surface_contract(closeout_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_direct_completion_surface_contract_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_direct_completion_surface_contract_ready", render_direct_completion_surface_contract_text(report))
        self.assertIn("Direct-Completion Surface Contract", render_direct_completion_surface_contract_markdown(report))
        self.assertIn("MiniGPT direct-completion surface contract", render_direct_completion_surface_contract_html(report))

    def test_row_families_are_balanced_and_separated(self) -> None:
        rows_by_family = {str(family["family"]): [str(row) for row in family["rows"]] for family in DIRECT_COMPLETION_SURFACE_ROW_FAMILIES}

        self.assertEqual(len(rows_by_family["fixed_prefix_ladder"]), len(rows_by_family["loss_prefix_ladder"]))
        self.assertNotEqual(rows_by_family["paired_order_forward"], rows_by_family["paired_order_reverse"])
        self.assertNotIn(HELDOUT_PAIR_PROBE, [row for rows in rows_by_family.values() for row in rows])


def closeout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_bridge_closeout_plan_ready",
        "summary": {
            "plan_ready": True,
            "closed_route": "direct_prompt_bridge_contract_patch",
            "proposed_next_artifact": "pair_readiness_direct_completion_surface_contract",
        },
        "plan": {
            "ready": True,
            "closed_route": "direct_prompt_bridge_contract_patch",
            "proposed_next_artifact": "pair_readiness_direct_completion_surface_contract",
        },
    }


if __name__ == "__main__":
    unittest.main()
