from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_route_decision import (
    build_surface_route_decision,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_route_decision_outputs,
)


class SurfaceRouteDecisionTests(unittest.TestCase):
    def test_route_closes_contextual_branch(self) -> None:
        report = build_surface_route_decision(contrast_fixture(), selector_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_contextual_decode_branch_and_design_minimal_prompt_objective")
        self.assertEqual(report["route"]["recommended_next_route"], "minimal_prompt_surface_objective")
        self.assertFalse(report["route"]["promotion_allowed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_anchor_boundary_fails(self) -> None:
        contrast = contrast_fixture()
        contrast["summary"]["contextual_anchor_required"] = False
        report = build_surface_route_decision(contrast, selector_fixture())

        self.assertEqual(report["status"], "fail")
        self.assertIn("contextual_anchor_boundary_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_route_decision(contrast_fixture(), selector_fixture())
            outputs = write_surface_route_decision_outputs(report, Path(tmp) / "route")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("current_route=contextual_decode_aid_closeout", render_text(report))
        self.assertIn("Surface Route Decision", render_markdown(report))
        self.assertIn("MiniGPT surface route decision", render_html(report))


def contrast_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"contextual_anchor_required": True, "stable_non_leaking_baseline_count": 0},
    }


def selector_fixture() -> dict[str, object]:
    return {"status": "pass", "selected_variant": {"variant_id": "space_context_control"}}


if __name__ == "__main__":
    unittest.main()
