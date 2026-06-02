from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan import (
    build_pair_prompt_transfer_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan_artifacts import (
    render_pair_prompt_transfer_repair_plan_html,
    render_pair_prompt_transfer_repair_plan_markdown,
    render_pair_prompt_transfer_repair_plan_text,
    write_pair_prompt_transfer_repair_plan_outputs,
)


class PairPromptTransferRepairPlanTests(unittest.TestCase):
    def test_plan_ready_from_not_ready_pair_probe_replay(self) -> None:
        report = build_pair_prompt_transfer_repair_plan(pair_probe_replay_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_pair_prompt_transfer_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_pair_prompt_transfer_contract_patch")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_pair_probe_is_ready(self) -> None:
        source = pair_probe_replay_fixture()
        source["decision"] = "pair_readiness_direct_completion_pair_probe_replay_ready"
        source["summary"]["exact_heldout_pair_full"] = True
        source["summary"]["pair_full_count"] = 1
        report = build_pair_prompt_transfer_repair_plan(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("pair_probe_not_ready", [issue["id"] for issue in report["issues"]])
        self.assertIn("exact_pair_failed", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_prompt_transfer_repair_plan(pair_probe_replay_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_prompt_transfer_repair_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("plan_ready=True", render_pair_prompt_transfer_repair_plan_text(report))
        self.assertIn("Pair Prompt Transfer Repair Plan", render_pair_prompt_transfer_repair_plan_markdown(report))
        self.assertIn("MiniGPT pair prompt transfer repair plan", render_pair_prompt_transfer_repair_plan_html(report))


def pair_probe_replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_completion_pair_probe_replay_not_ready",
        "summary": {
            "pair_full_count": 0,
            "exact_heldout_pair_full": False,
            "required_all_pair_full": False,
        },
    }


if __name__ == "__main__":
    unittest.main()
