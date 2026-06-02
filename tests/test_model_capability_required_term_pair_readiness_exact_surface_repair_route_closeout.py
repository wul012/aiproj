from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout import (
    build_exact_surface_repair_route_closeout,
    locate_exact_surface_repair_route_closeout_source,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_route_closeout_artifacts import (
    render_exact_surface_repair_route_closeout_html,
    render_exact_surface_repair_route_closeout_markdown,
    render_exact_surface_repair_route_closeout_text,
    write_exact_surface_repair_route_closeout_outputs,
)


class ExactSurfaceRepairRouteCloseoutTests(unittest.TestCase):
    def test_closeout_ready_from_ineffective_comparison(self) -> None:
        report = build_exact_surface_repair_route_closeout(comparison_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_exact_surface_repair_route_closed")
        self.assertTrue(report["summary"]["closeout_ready"])
        self.assertEqual(report["summary"]["recommended_next_route"], "objective_or_decoding_alternative_plan")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_route_is_not_ineffective(self) -> None:
        comparison = comparison_fixture()
        comparison["summary"]["repair_ineffective"] = False
        report = build_exact_surface_repair_route_closeout(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("repair_ineffective", [issue["id"] for issue in report["issues"]])

    def test_locator_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = locate_exact_surface_repair_route_closeout_source(tmp)
        self.assertEqual(source.name, "model_capability_required_term_pair_readiness_exact_surface_repair_effectiveness_comparison.json")

    def test_outputs_render_all_formats(self) -> None:
        report = build_exact_surface_repair_route_closeout(comparison_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_exact_surface_repair_route_closeout_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("closeout_ready=True", render_exact_surface_repair_route_closeout_text(report))
        self.assertIn("Exact-Surface Repair Route Closeout", render_exact_surface_repair_route_closeout_markdown(report))
        self.assertIn("MiniGPT exact-surface repair route closeout", render_exact_surface_repair_route_closeout_html(report))


def comparison_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_exact_surface_repair_ineffective_stop_route",
        "summary": {
            "repair_ineffective": True,
            "exact_default_hit_delta": 0,
            "exact_pair_full_delta": 0,
            "baseline_pair_full_count": 1,
            "repaired_pair_full_count": 1,
            "improved_surface_ids": [],
        },
    }


if __name__ == "__main__":
    unittest.main()
