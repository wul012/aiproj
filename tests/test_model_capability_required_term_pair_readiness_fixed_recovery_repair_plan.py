from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_repair_plan import (
    build_fixed_recovery_repair_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_repair_plan_artifacts import (
    render_fixed_recovery_repair_plan_html,
    render_fixed_recovery_repair_plan_markdown,
    render_fixed_recovery_repair_plan_text,
    write_fixed_recovery_repair_plan_outputs,
)


class FixedRecoveryRepairPlanTests(unittest.TestCase):
    def test_plan_ready_from_failure_shape_change(self) -> None:
        report = build_fixed_recovery_repair_plan(route_comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_fixed_recovery_repair_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_fixed_recovery_contract_patch")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "plan_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_for_pair_full_candidate(self) -> None:
        comparison = route_comparison_fixture()
        comparison["decision"] = "pair_readiness_route_pair_full_candidate_found"
        comparison["summary"]["any_pair_full_observed"] = True
        report = build_fixed_recovery_repair_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("route_comparison_decision", [issue["id"] for issue in report["issues"]])
        self.assertIn("no_pair_full_route", [issue["id"] for issue in report["issues"]])

    def test_plan_fails_when_structured_does_not_miss_fixed(self) -> None:
        comparison = route_comparison_fixture()
        comparison["summary"]["structured_default_missed_terms"] = ["loss"]
        report = build_fixed_recovery_repair_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("structured_misses_fixed", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_fixed_recovery_repair_plan(route_comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_fixed_recovery_repair_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_fixed_recovery_repair_plan_ready", render_fixed_recovery_repair_plan_text(report))
        self.assertIn("Fixed-Recovery Repair Plan", render_fixed_recovery_repair_plan_markdown(report))
        self.assertIn("MiniGPT fixed-recovery repair plan", render_fixed_recovery_repair_plan_html(report))


def route_comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_structured_template_changes_failure_shape_without_pair_full",
        "summary": {
            "best_routes": ["baseline-split", "structured-template"],
            "any_pair_full_observed": False,
            "structured_vs_baseline_default_hit_delta": 0,
            "structured_default_hit_terms": ["loss"],
            "structured_default_missed_terms": ["fixed"],
            "failure_shape_changed": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
