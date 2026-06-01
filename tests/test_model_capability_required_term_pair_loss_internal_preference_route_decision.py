from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_internal_preference_route_decision import (
    build_model_capability_required_term_pair_loss_internal_preference_route_decision,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_route_decision_artifacts import (
    render_loss_internal_preference_route_decision_html,
    render_loss_internal_preference_route_decision_markdown,
    render_loss_internal_preference_route_decision_text,
    write_loss_internal_preference_route_decision_outputs,
)


class LossInternalPreferenceRouteDecisionTests(unittest.TestCase):
    def test_selects_decode_bridge_when_internal_pair_match_lacks_generation_pair_full(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_preference_route_decision(
            comparison_report(),
            forced_choice_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "select_loss_internal_first_token_for_decode_bridge_not_promotion")
        self.assertEqual(report["summary"]["selected_decode_bridge_source"], "loss-internal-first-token")
        self.assertTrue(report["summary"]["internal_to_generation_bridge_required"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_fails_when_forced_choice_has_no_internal_match(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_preference_route_decision(
            comparison_report(),
            forced_choice_report(best_internal_sources=[]),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("forced-choice found no internal pair match", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_internal_preference_route_decision(
                comparison_report(),
                forced_choice_report(),
            )
            outputs = write_loss_internal_preference_route_decision_outputs(report, root / "decision")
            text = render_loss_internal_preference_route_decision_text(report)
            markdown = render_loss_internal_preference_route_decision_markdown(report)
            html = render_loss_internal_preference_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("selected_decode_bridge_source=loss-internal-first-token", text)
            self.assertIn("Loss-Internal-Preference Route Decision", markdown)
            self.assertIn("MiniGPT loss-internal-preference route decision", html)


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "loss_internal_preference_objectives_confirm_branch_tradeoff",
        "summary": {
            "pair_full_report_count": 0,
            "mixed_tradeoff_observed": True,
        },
        "branch_rows": [
            route("loss-internal-preference", ["fixed"], ["loss"]),
            route("loss-internal-first-token", ["loss"], ["fixed"]),
            route("loss-internal-ranked-choice", ["fixed"], ["loss"]),
        ],
    }


def route(label: str, hit_terms: list[str], missed_terms: list[str]) -> dict[str, object]:
    return {
        "source_label": label,
        "corpus_mode": f"equals_surface_no_pair_id_{label.replace('-', '_')}_repair",
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "pair_full_observed": False,
        "fixed_only_tradeoff": hit_terms == ["fixed"],
        "loss_only_tradeoff": hit_terms == ["loss"],
    }


def forced_choice_report(*, best_internal_sources: list[str] | None = None) -> dict[str, object]:
    sources = ["loss-internal-first-token"] if best_internal_sources is None else best_internal_sources
    return {
        "status": "pass",
        "decision": "refresh_forced_choice_internal_pair_match" if sources else "refresh_forced_choice_partial_internal_match",
        "summary": {
            "forced_choice_full_match_source_count": len(sources),
            "best_internal_sources": sources,
        },
    }


if __name__ == "__main__":
    unittest.main()
