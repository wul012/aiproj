from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision import (
    build_model_capability_required_term_pair_generation_internal_alignment_route_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_generation_internal_alignment_route_decision_artifacts import (
    render_generation_internal_alignment_route_decision_html,
    render_generation_internal_alignment_route_decision_markdown,
    render_generation_internal_alignment_route_decision_text,
    write_generation_internal_alignment_route_decision_outputs,
)


class GenerationInternalAlignmentRouteDecisionTests(unittest.TestCase):
    def test_route_decision_selects_generation_route_and_internal_anchor(self) -> None:
        report = build_model_capability_required_term_pair_generation_internal_alignment_route_decision(
            comparison_report()
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "repair_internal_preference_preserve_generation_pair_full")
        self.assertEqual(report["summary"]["selected_generation_route_label"], "joint-cycle")
        self.assertEqual(report["summary"]["internal_anchor_route_label"], "first-token")
        self.assertFalse(report["summary"]["direct_promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_route_decision_prefers_aligned_candidate_when_available(self) -> None:
        payload = comparison_report()
        payload["source_rows"].append(
            {
                "source_label": "aligned",
                "alignment_class": "generation_internal_pair_full",
                "generation_hit_terms": ["fixed", "loss"],
                "internal_expected_best_terms": ["fixed", "loss"],
                "generation_pair_full": True,
                "internal_pair_full": True,
            }
        )
        report = build_model_capability_required_term_pair_generation_internal_alignment_route_decision(payload)

        self.assertEqual(report["decision"], "repeat_aligned_pair_full_candidate_before_promotion")
        self.assertTrue(report["summary"]["direct_promotion_ready"])
        self.assertEqual(report["summary"]["aligned_route_label"], "aligned")

    def test_route_decision_prefers_internal_repair_anchor_when_available(self) -> None:
        payload = comparison_report()
        payload["source_rows"].append(
            {
                "source_label": "internal-repair",
                "alignment_class": "internal_pair_full_generation_none",
                "generation_hit_terms": [],
                "internal_expected_best_terms": ["fixed", "loss"],
                "generation_pair_full": False,
                "internal_pair_full": True,
            }
        )
        report = build_model_capability_required_term_pair_generation_internal_alignment_route_decision(payload)

        self.assertEqual(report["decision"], "repair_internal_preference_preserve_generation_pair_full")
        self.assertEqual(report["summary"]["internal_anchor_route_label"], "internal-repair")

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_generation_internal_alignment_route_decision(
                comparison_report()
            )
            outputs = write_generation_internal_alignment_route_decision_outputs(report, root / "route")
            text = render_generation_internal_alignment_route_decision_text(report)
            markdown = render_generation_internal_alignment_route_decision_markdown(report)
            html = render_generation_internal_alignment_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=repair_internal_preference_preserve_generation_pair_full", text)
            self.assertIn("Generation/Internal Alignment Route Decision", markdown)
            self.assertIn("MiniGPT generation/internal alignment route decision", html)


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "keep_generation_pair_full_and_repair_internal_preference",
        "summary": {
            "generation_pair_full_count": 1,
            "internal_pair_full_count": 1,
            "aligned_pair_full_count": 0,
        },
        "source_rows": [
            {
                "source_label": "first-token",
                "alignment_class": "internal_pair_full_generation_gap",
                "generation_hit_terms": ["loss"],
                "internal_expected_best_terms": ["fixed", "loss"],
                "generation_pair_full": False,
                "internal_pair_full": True,
            },
            {
                "source_label": "joint-cycle",
                "alignment_class": "generation_pair_full_internal_partial",
                "generation_hit_terms": ["fixed", "loss"],
                "internal_expected_best_terms": ["fixed"],
                "generation_pair_full": True,
                "internal_pair_full": False,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
