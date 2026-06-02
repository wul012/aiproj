from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_loss_retention_repair_plan import (
    build_loss_retention_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_loss_retention_repair_plan_artifacts import (
    render_loss_retention_repair_plan_html,
    render_loss_retention_repair_plan_markdown,
    render_loss_retention_repair_plan_text,
    write_loss_retention_repair_plan_outputs,
)


class LossRetentionRepairPlanTests(unittest.TestCase):
    def test_plan_ready_from_loss_prompt_fixed_pollution(self) -> None:
        report = build_loss_retention_repair_plan(diagnostic_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_loss_retention_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_loss_retention_contract_patch")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_for_wrong_failure_mode(self) -> None:
        diagnostic = diagnostic_fixture()
        diagnostic["decision"] = "pair_readiness_fixed_prompt_absorbed_by_loss"
        report = build_loss_retention_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_decision", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_loss_retention_repair_plan(diagnostic_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_loss_retention_repair_plan_outputs(report, Path(tmp) / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_loss_retention_repair_plan_ready", render_loss_retention_repair_plan_text(report))
        self.assertIn("Loss-Retention Repair Plan", render_loss_retention_repair_plan_markdown(report))
        self.assertIn("MiniGPT loss-retention repair plan", render_loss_retention_repair_plan_html(report))


def diagnostic_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_loss_prompt_absorbed_by_fixed",
        "summary": {
            "loss_hit_count": 0,
            "loss_prompt_fixed_pollution_count": 1,
        },
    }


if __name__ == "__main__":
    unittest.main()
