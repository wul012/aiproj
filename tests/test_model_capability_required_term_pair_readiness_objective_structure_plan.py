from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_objective_structure_plan import (
    build_objective_structure_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_objective_structure_plan_artifacts import (
    render_objective_structure_plan_html,
    render_objective_structure_plan_markdown,
    render_objective_structure_plan_text,
    write_objective_structure_plan_outputs,
)


class ObjectiveStructurePlanTests(unittest.TestCase):
    def test_plan_ready_from_capacity_probe_no_improvement(self) -> None:
        report = build_objective_structure_plan(five_route_comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_objective_structure_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_objective_structure_contract")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "plan_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_before_capacity_probe_closeout(self) -> None:
        comparison = five_route_comparison_fixture()
        comparison["decision"] = "pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full"
        comparison["summary"]["capacity_probe_no_improvement"] = False
        report = build_objective_structure_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("route_comparison_decision", [issue["id"] for issue in report["issues"]])
        self.assertIn("capacity_probe_no_improvement", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_plan_fails_when_loss_is_not_remaining_miss(self) -> None:
        comparison = five_route_comparison_fixture()
        comparison["summary"]["capacity_probe_default_missed_terms"] = ["fixed"]
        report = build_objective_structure_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("capacity_probe_still_misses_loss", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_objective_structure_plan(five_route_comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_objective_structure_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_objective_structure_plan_ready", render_objective_structure_plan_text(report))
        self.assertIn("Objective-Structure Plan", render_objective_structure_plan_markdown(report))
        self.assertIn("MiniGPT objective-structure plan", render_objective_structure_plan_html(report))


def five_route_comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_capacity_probe_no_improvement_fixed_only",
        "summary": {
            "route_count": 5,
            "any_pair_full_observed": False,
            "capacity_probe_no_improvement": True,
            "capacity_probe_vs_fixed_recovery_default_hit_delta": 0,
            "capacity_probe_default_missed_terms": ["loss"],
        },
        "route_rows": [
            {"label": "baseline-split"},
            {"label": "loss-retention-prefix"},
            {"label": "structured-template"},
            {"label": "fixed-recovery"},
            {"label": "capacity-probe"},
        ],
    }


if __name__ == "__main__":
    unittest.main()
