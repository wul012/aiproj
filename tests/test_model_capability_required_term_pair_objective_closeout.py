from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_objective_closeout import (
    build_model_capability_required_term_pair_objective_closeout,
    locate_branch_binding_decision,
    locate_target_anchor_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_objective_closeout_artifacts import (
    render_model_capability_required_term_pair_objective_closeout_html,
    render_model_capability_required_term_pair_objective_closeout_markdown,
    render_model_capability_required_term_pair_objective_closeout_text,
    write_model_capability_required_term_pair_objective_closeout_outputs,
)


class ModelCapabilityRequiredTermPairObjectiveCloseoutTests(unittest.TestCase):
    def test_closeout_requires_loss_branch_objective(self) -> None:
        report = build_model_capability_required_term_pair_objective_closeout(
            branch_binding_decision=branch_binding_decision(),
            target_anchor_decision=target_anchor_decision(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_current_objectives_and_design_loss_branch_objective")
        self.assertTrue(report["summary"]["branch_binding_stopped"])
        self.assertTrue(report["summary"]["target_anchor_residual_only"])
        self.assertTrue(report["summary"]["loss_branch_required"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_branch_binding_is_not_stopped(self) -> None:
        branch = branch_binding_decision()
        branch["decision"] = "record_branch_binding_route_decision"
        report = build_model_capability_required_term_pair_objective_closeout(
            branch_binding_decision=branch,
            target_anchor_decision=target_anchor_decision(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("branch-binding route is not stopped", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_objective_closeout(
                branch_binding_decision=branch_binding_decision(),
                target_anchor_decision=target_anchor_decision(),
            )
            outputs = write_model_capability_required_term_pair_objective_closeout_outputs(report, root / "closeout")
            text = render_model_capability_required_term_pair_objective_closeout_text(report)
            markdown = render_model_capability_required_term_pair_objective_closeout_markdown(report)
            html = render_model_capability_required_term_pair_objective_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=close_current_objectives_and_design_loss_branch_objective", text)
            self.assertIn("Objective Closeout", markdown)
            self.assertIn("MiniGPT objective closeout", html)

    def test_locate_accepts_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(locate_branch_binding_decision(root), root / "model_capability_required_term_pair_branch_binding_route_decision.json")
            self.assertEqual(locate_target_anchor_decision(root), root / "model_capability_required_term_pair_target_anchor_route_decision.json")


def branch_binding_decision() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "stop_branch_binding_v1_and_keep_residual_baseline",
        "summary": {
            "branch_binding_visible_hit_route_count": 0,
        },
    }


def target_anchor_decision() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "keep_target_anchor_as_residual_not_promoted",
        "summary": {
            "residual_signal_routes": ["v571-loss-balanced", "v584-target-anchor"],
            "target_anchor_loss_hit_route_count": 0,
            "union_hit_terms": ["fixed"],
        },
    }


if __name__ == "__main__":
    unittest.main()
