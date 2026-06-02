from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_plan import (
    build_exact_surface_repair_plan,
    locate_exact_surface_repair_plan_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_plan_artifacts import (
    render_exact_surface_repair_plan_html,
    render_exact_surface_repair_plan_markdown,
    render_exact_surface_repair_plan_text,
    write_exact_surface_repair_plan_outputs,
)


class ExactSurfaceRepairPlanTests(unittest.TestCase):
    def test_plan_ready_from_surface_sensitivity(self) -> None:
        report = build_exact_surface_repair_plan(sensitivity_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["repair_row_budget"], 4)
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_exact_surface_repair_contract_patch")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_promotion_is_not_blocked(self) -> None:
        diagnostic = sensitivity_fixture()
        diagnostic["summary"]["promotion_blocked"] = False
        report = build_exact_surface_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_blocked", [issue["id"] for issue in report["issues"]])

    def test_plan_fails_without_optional_surface_signal(self) -> None:
        diagnostic = sensitivity_fixture()
        diagnostic["summary"]["optional_pair_full_surface_ids"] = []
        report = build_exact_surface_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("optional_surface_signal_present", [issue["id"] for issue in report["issues"]])

    def test_locator_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = locate_exact_surface_repair_plan_source(tmp)
        self.assertEqual(source.name, "model_capability_required_term_pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_diagnostic.json")

    def test_outputs_render_all_formats(self) -> None:
        report = build_exact_surface_repair_plan(sensitivity_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_exact_surface_repair_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("plan_ready=True", render_exact_surface_repair_plan_text(report))
        self.assertIn("Exact-Surface Repair Plan", render_exact_surface_repair_plan_markdown(report))
        self.assertIn("MiniGPT exact-surface repair plan", render_exact_surface_repair_plan_html(report))


def sensitivity_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_preserving_transfer_prompt_surface_sensitivity_found",
        "summary": {
            "surface_sensitivity_observed": True,
            "promotion_blocked": True,
            "required_missed_surface_ids": ["exact-heldout-pair"],
            "optional_pair_full_surface_ids": ["arrow-heldout-pair"],
        },
    }


if __name__ == "__main__":
    unittest.main()
