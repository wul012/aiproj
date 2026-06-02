from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_capacity_probe_plan import (
    CAPACITY_PROBE_TRAINING_CONFIG,
    build_capacity_probe_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_capacity_probe_plan_artifacts import (
    render_capacity_probe_plan_html,
    render_capacity_probe_plan_markdown,
    render_capacity_probe_plan_text,
    write_capacity_probe_plan_outputs,
)


class CapacityProbePlanTests(unittest.TestCase):
    def test_plan_ready_from_row_patching_closeout(self) -> None:
        report = build_capacity_probe_plan(route_comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_capacity_probe_plan_ready")
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_capacity_probe_training_run")
        self.assertEqual(report["plan"]["training_config"], CAPACITY_PROBE_TRAINING_CONFIG)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "plan_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_before_row_patching_closeout(self) -> None:
        comparison = route_comparison_fixture()
        comparison["decision"] = "pair_readiness_structured_template_changes_failure_shape_without_pair_full"
        comparison["summary"]["fixed_recovery_returns_to_baseline"] = False
        report = build_capacity_probe_plan(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("route_comparison_decision", [issue["id"] for issue in report["issues"]])
        self.assertIn("fixed_recovery_returned_to_baseline", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_capacity_probe_plan(route_comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_capacity_probe_plan_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_capacity_probe_plan_ready", render_capacity_probe_plan_text(report))
        self.assertIn("Capacity-Probe Plan", render_capacity_probe_plan_markdown(report))
        self.assertIn("MiniGPT capacity-probe plan", render_capacity_probe_plan_html(report))


def route_comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full",
        "summary": {
            "route_count": 4,
            "any_pair_full_observed": False,
            "fixed_recovery_returns_to_baseline": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
