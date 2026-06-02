from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_corpus_materialization import (
    PAIR_READINESS_CONTRACT_JSON_FILENAMES,
    PAIR_READINESS_READY_CONTRACT_DECISIONS,
    locate_pair_readiness_corpus_materialization_source,
)
from minigpt.model_capability_required_term_pair_readiness_objective_structure_contract import (
    HELDOUT_PAIR_PROBE,
    PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME,
    build_objective_structure_contract,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_structure_contract_artifacts import (
    render_objective_structure_contract_html,
    render_objective_structure_contract_markdown,
    render_objective_structure_contract_text,
    write_objective_structure_contract_outputs,
)
from minigpt.report_utils import write_json_payload


class ObjectiveStructureContractTests(unittest.TestCase):
    def test_contract_ready_from_objective_structure_plan(self) -> None:
        report = build_objective_structure_contract(plan_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_structure_contract_ready")
        self.assertTrue(report["summary"]["contract_ready"])
        self.assertEqual(report["summary"]["fixed_direct_row_count"], report["summary"]["loss_direct_row_count"])
        self.assertEqual(report["interpretation"]["model_quality_claim"], "contract_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_fails_when_plan_is_not_ready(self) -> None:
        plan = plan_fixture()
        plan["status"] = "fail"
        report = build_objective_structure_contract(plan)

        self.assertEqual(report["status"], "fail")
        self.assertIn("plan_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_keeps_heldout_probes_out_of_training_rows(self) -> None:
        report = build_objective_structure_contract(plan_fixture())
        training_rows = report["contract"]["training_rows"]

        self.assertNotIn("fixed=", training_rows)
        self.assertNotIn("loss=", training_rows)
        self.assertNotIn(HELDOUT_PAIR_PROBE, training_rows)
        self.assertIn(HELDOUT_PAIR_PROBE, [row["prompt"] for row in report["contract"]["evaluation_probes"]])

    def test_materializer_accepts_objective_structure_contract_directory(self) -> None:
        report = build_objective_structure_contract(plan_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "contract"
            write_json_payload(report, out_dir / PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME)
            located = locate_pair_readiness_corpus_materialization_source(out_dir)

        self.assertEqual(located.name, PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME)
        self.assertIn(PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME, PAIR_READINESS_CONTRACT_JSON_FILENAMES)
        self.assertIn("pair_readiness_objective_structure_contract_ready", PAIR_READINESS_READY_CONTRACT_DECISIONS)

    def test_outputs_render_all_formats(self) -> None:
        report = build_objective_structure_contract(plan_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_objective_structure_contract_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_objective_structure_contract_ready", render_objective_structure_contract_text(report))
        self.assertIn("Objective-Structure Contract", render_objective_structure_contract_markdown(report))
        self.assertIn("MiniGPT objective-structure contract", render_objective_structure_contract_html(report))


def plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_objective_structure_plan_ready",
        "plan": {"proposed_next_artifact": "pair_readiness_objective_structure_contract"},
        "summary": {"plan_ready": True},
    }


if __name__ == "__main__":
    unittest.main()
