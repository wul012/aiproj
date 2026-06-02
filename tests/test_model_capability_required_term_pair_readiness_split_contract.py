from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_split_contract import (
    HELDOUT_PAIR_PROBE,
    build_pair_readiness_split_contract,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract_artifacts import (
    render_pair_readiness_split_contract_html,
    render_pair_readiness_split_contract_markdown,
    render_pair_readiness_split_contract_text,
    write_pair_readiness_split_contract_outputs,
)


class PairReadinessSplitContractTests(unittest.TestCase):
    def test_contract_ready_from_split_plan(self) -> None:
        report = build_pair_readiness_split_contract(plan_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_split_contract_ready")
        self.assertTrue(report["summary"]["contract_ready"])
        self.assertEqual(report["summary"]["heldout_pair_probe"], HELDOUT_PAIR_PROBE)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "contract_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_fails_when_plan_is_not_ready(self) -> None:
        plan = plan_fixture()
        plan["status"] = "fail"
        report = build_pair_readiness_split_contract(plan)

        self.assertEqual(report["status"], "fail")
        self.assertIn("plan_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_keeps_pair_probe_out_of_training_rows(self) -> None:
        report = build_pair_readiness_split_contract(plan_fixture())

        self.assertNotIn(HELDOUT_PAIR_PROBE, report["contract"]["training_rows"])
        self.assertIn(HELDOUT_PAIR_PROBE, [row["prompt"] for row in report["contract"]["evaluation_probes"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_readiness_split_contract(plan_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_readiness_split_contract_outputs(report, Path(tmp) / "contract")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_split_contract_ready", render_pair_readiness_split_contract_text(report))
        self.assertIn("Pair-Readiness Split Contract", render_pair_readiness_split_contract_markdown(report))
        self.assertIn("MiniGPT pair-readiness split contract", render_pair_readiness_split_contract_html(report))


def plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_split_plan_ready",
        "plan": {"proposed_next_artifact": "pair_readiness_split_contract"},
        "summary": {"plan_ready": True},
    }


if __name__ == "__main__":
    unittest.main()
