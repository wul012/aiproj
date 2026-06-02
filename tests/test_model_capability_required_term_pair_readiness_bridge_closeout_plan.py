from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_bridge_closeout_plan import (
    build_bridge_closeout_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_bridge_closeout_plan_artifacts import (
    render_bridge_closeout_plan_html,
    render_bridge_closeout_plan_markdown,
    render_bridge_closeout_plan_text,
    write_bridge_closeout_plan_outputs,
)


class BridgeCloseoutPlanTests(unittest.TestCase):
    def test_plan_ready_from_bridge_pollution_closeout(self) -> None:
        report = build_bridge_closeout_plan(comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_bridge_closeout_plan_ready")
        self.assertEqual(report["summary"]["closed_route"], "direct_prompt_bridge_contract_patch")
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_direct_completion_surface_contract")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_bridge_improved(self) -> None:
        comparison = comparison_fixture()
        comparison["summary"]["bridge_improved"] = True
        comparison["summary"]["default_hit_delta"] = 1
        report = build_bridge_closeout_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_hit_delta", [issue["id"] for issue in report["issues"]])
        self.assertIn("bridge_not_improved", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_bridge_closeout_plan(comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_bridge_closeout_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_bridge_closeout_plan_ready", render_bridge_closeout_plan_text(report))
        self.assertIn("Bridge Closeout Plan", render_bridge_closeout_plan_markdown(report))
        self.assertIn("MiniGPT bridge closeout plan", render_bridge_closeout_plan_html(report))


def comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_bridge_no_improvement_introduced_fixed_pollution",
        "summary": {
            "default_hit_delta": 0,
            "bridge_pollution_introduced": True,
            "bridge_improved": False,
        },
    }


if __name__ == "__main__":
    unittest.main()
