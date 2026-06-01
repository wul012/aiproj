from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_generation_internal_batch_closeout import (
    build_model_capability_required_term_pair_generation_internal_batch_closeout,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_batch_closeout_artifacts import (
    render_generation_internal_batch_closeout_html,
    render_generation_internal_batch_closeout_markdown,
    render_generation_internal_batch_closeout_text,
    write_generation_internal_batch_closeout_outputs,
)


class GenerationInternalBatchCloseoutTests(unittest.TestCase):
    def test_closeout_selects_internal_repair_after_unaligned_generation_signal(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_batch_closeout(
            comparison_report(),
            route_decision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_batch_and_design_joint_cycle_internal_repair")
        self.assertEqual(report["summary"]["batch_version_count"], 10)
        self.assertEqual(report["summary"]["selected_generation_route"], "loss-internal-joint-cycle")
        self.assertEqual(report["summary"]["aligned_pair_full_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_route_decision_is_missing(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_batch_closeout(
            comparison_report(),
            {"status": "pass", "summary": {}},
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("route decision has no selected generation route", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_generation_internal_batch_closeout(
                comparison_report(),
                route_decision_report(),
            )
            outputs = write_generation_internal_batch_closeout_outputs(report, root / "closeout")
            text = render_generation_internal_batch_closeout_text(report)
            markdown = render_generation_internal_batch_closeout_markdown(report)
            html = render_generation_internal_batch_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=close_batch_and_design_joint_cycle_internal_repair", text)
            self.assertIn("Generation/Internal Batch Closeout", markdown)
            self.assertIn("MiniGPT generation/internal batch closeout", html)


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "keep_generation_pair_full_and_repair_internal_preference",
        "summary": {
            "compared_source_count": 4,
            "generation_pair_full_count": 1,
            "internal_pair_full_count": 1,
            "aligned_pair_full_count": 0,
        },
        "source_rows": [{"source_label": "loss-internal-joint-cycle"}],
    }


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "repair_internal_preference_preserve_generation_pair_full",
        "summary": {
            "direct_promotion_ready": False,
            "selected_generation_route_label": "loss-internal-joint-cycle",
            "internal_anchor_route_label": "loss-internal-first-token",
        },
        "selected_generation_route": {"source_label": "loss-internal-joint-cycle"},
    }


if __name__ == "__main__":
    unittest.main()
