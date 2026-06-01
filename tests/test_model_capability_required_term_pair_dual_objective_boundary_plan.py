from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_dual_objective_boundary_plan import (
    DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE,
    build_model_capability_required_term_pair_dual_objective_boundary_plan,
    locate_dual_objective_boundary_closeout,
    locate_dual_objective_boundary_miss_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_dual_objective_boundary_plan_artifacts import (
    render_dual_objective_boundary_plan_html,
    render_dual_objective_boundary_plan_markdown,
    render_dual_objective_boundary_plan_text,
    write_dual_objective_boundary_plan_outputs,
)


class DualObjectiveBoundaryPlanTests(unittest.TestCase):
    def test_plan_ready_when_fixed_miss_and_loss_constrained_hit_are_present(self) -> None:
        report = build_model_capability_required_term_pair_dual_objective_boundary_plan(
            closeout_report(),
            miss_diagnostic(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "explicit_dual_objective_boundary_plan_ready")
        self.assertEqual(report["proposed_corpus_mode"], DUAL_OBJECTIVE_BOUNDARY_CORPUS_MODE)
        self.assertEqual(report["summary"]["constraint_count"], 5)
        self.assertTrue(report["summary"]["ready_to_add_corpus_mode"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_plan_fails_when_fixed_is_not_remaining_miss(self) -> None:
        miss = miss_diagnostic()
        miss["summary"]["remaining_missed_terms"] = []

        report = build_model_capability_required_term_pair_dual_objective_boundary_plan(closeout_report(), miss)

        self.assertEqual(report["status"], "fail")
        self.assertIn("miss diagnostic does not identify fixed as remaining missed term", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_dual_objective_boundary_plan(
                closeout_report(),
                miss_diagnostic(),
            )
            outputs = write_dual_objective_boundary_plan_outputs(report, root / "plan")
            text = render_dual_objective_boundary_plan_text(report)
            markdown = render_dual_objective_boundary_plan_markdown(report)
            html = render_dual_objective_boundary_plan_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=explicit_dual_objective_boundary_plan_ready", text)
            self.assertIn("Dual-Objective Boundary Plan", markdown)
            self.assertIn("MiniGPT dual-objective boundary plan", html)

    def test_locators_accept_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_dual_objective_boundary_closeout(root),
                root / "model_capability_required_term_pair_generation_internal_batch_closeout.json",
            )
            self.assertEqual(
                locate_dual_objective_boundary_miss_diagnostic(root),
                root / "model_capability_required_term_pair_constrained_decode_miss_diagnostic.json",
            )


def closeout_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "close_batch_and_design_constrained_decode_or_explicit_dual_objective_boundary",
        "summary": {
            "aligned_pair_full_count": 0,
            "selected_generation_route": "loss-internal-joint-cycle",
            "internal_anchor_route": "joint-cycle-internal-repair",
            "next_route": "constrained_decode_or_explicit_dual_objective_boundary",
        },
    }


def miss_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "fixed_branch_still_missed_after_constrained_decode",
        "summary": {
            "fixed_miss_class": "prefix_fragment_without_full_term",
            "remaining_missed_terms": ["fixed"],
            "loss_constrained_hit": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
