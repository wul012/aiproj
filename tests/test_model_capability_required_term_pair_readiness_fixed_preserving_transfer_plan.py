from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan import (
    build_fixed_preserving_transfer_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan_artifacts import (
    render_fixed_preserving_transfer_plan_html,
    render_fixed_preserving_transfer_plan_markdown,
    render_fixed_preserving_transfer_plan_text,
    write_fixed_preserving_transfer_plan_outputs,
)


class FixedPreservingTransferPlanTests(unittest.TestCase):
    def test_plan_ready_from_regressed_transfer_diagnostic(self) -> None:
        report = build_fixed_preserving_transfer_plan(regression_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_preserving_transfer_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_fixed_preserving_transfer_contract_patch")
        self.assertEqual(report["plan"]["transfer_row_budget"], 4)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_transfer_route_is_not_closed(self) -> None:
        diagnostic = regression_fixture()
        diagnostic["summary"]["transfer_route_closed"] = False
        report = build_fixed_preserving_transfer_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("transfer_route_closed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_plan_fails_without_fixed_regression(self) -> None:
        diagnostic = regression_fixture()
        diagnostic["summary"]["fixed_regressed"] = False
        report = build_fixed_preserving_transfer_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("fixed_regressed", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_fixed_preserving_transfer_plan(regression_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_fixed_preserving_transfer_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("plan_ready=True", render_fixed_preserving_transfer_plan_text(report))
        self.assertIn("Fixed-Preserving Transfer Plan", render_fixed_preserving_transfer_plan_markdown(report))
        self.assertIn("MiniGPT fixed-preserving transfer plan", render_fixed_preserving_transfer_plan_html(report))


def regression_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_pair_prompt_transfer_regressed_stop_route",
        "summary": {
            "direct_completion_default_hit_count": 2,
            "transfer_default_hit_count": 1,
            "transfer_hit_delta_from_direct": -1,
            "fixed_regressed": True,
            "pair_probe_exact_heldout_pair_full": False,
            "transfer_route_closed": True,
            "closed_route": "pair_prompt_transfer_full_surrogate_patch",
        },
    }


if __name__ == "__main__":
    unittest.main()
