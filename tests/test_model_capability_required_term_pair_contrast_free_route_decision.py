from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_contrast_free_route_decision import (
    build_model_capability_required_term_pair_contrast_free_route_decision,
    locate_contrast_free_comparison,
    locate_first_token_diagnostic,
    locate_prior_closeout,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_contrast_free_route_decision_artifacts import (
    render_model_capability_required_term_pair_contrast_free_route_decision_html,
    render_model_capability_required_term_pair_contrast_free_route_decision_markdown,
    render_model_capability_required_term_pair_contrast_free_route_decision_text,
    write_model_capability_required_term_pair_contrast_free_route_decision_outputs,
)


class ContrastFreeRouteDecisionTests(unittest.TestCase):
    def test_decision_stops_routes_and_requires_forced_choice(self) -> None:
        report = build_model_capability_required_term_pair_contrast_free_route_decision(
            comparison=comparison_report(),
            prior_closeout=prior_closeout_report(),
            first_token_diagnostic=first_token_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "stop_contrast_free_routes_and_run_forced_choice_diagnostic")
        self.assertTrue(report["summary"]["requires_forced_choice_diagnostic"])
        self.assertEqual(report["summary"]["selected_fixed_signal_route"], "v612-delimiter-span")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decision_routes_pair_full_to_seed_stability(self) -> None:
        comparison = comparison_report(pair_full=True)
        report = build_model_capability_required_term_pair_contrast_free_route_decision(
            comparison=comparison,
            prior_closeout=prior_closeout_report(),
            first_token_diagnostic=first_token_report(),
        )

        self.assertEqual(report["decision"], "promote_contrast_free_pair_full_candidate_to_seed_stability")
        self.assertFalse(report["summary"]["requires_forced_choice_diagnostic"])

    def test_decision_fails_without_prior_stop(self) -> None:
        closeout = prior_closeout_report()
        closeout["summary"]["stop_current_loss_rebalance_routes"] = False
        report = build_model_capability_required_term_pair_contrast_free_route_decision(
            comparison=comparison_report(),
            prior_closeout=closeout,
            first_token_diagnostic=first_token_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("prior closeout did not stop loss-rebalance routes", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_contrast_free_route_decision(
                comparison=comparison_report(),
                prior_closeout=prior_closeout_report(),
                first_token_diagnostic=first_token_report(),
            )
            outputs = write_model_capability_required_term_pair_contrast_free_route_decision_outputs(report, root / "decision")
            text = render_model_capability_required_term_pair_contrast_free_route_decision_text(report)
            markdown = render_model_capability_required_term_pair_contrast_free_route_decision_markdown(report)
            html = render_model_capability_required_term_pair_contrast_free_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=stop_contrast_free_routes_and_run_forced_choice_diagnostic", text)
            self.assertIn("Contrast-Free Route Decision", markdown)
            self.assertIn("MiniGPT contrast-free route decision", html)

    def test_locators_accept_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_contrast_free_comparison(root),
                root / "model_capability_required_term_pair_fixed_retention_objective_comparison.json",
            )
            self.assertEqual(
                locate_prior_closeout(root),
                root / "model_capability_required_term_pair_fixed_retention_batch_closeout.json",
            )
            self.assertEqual(
                locate_first_token_diagnostic(root),
                root / "model_capability_required_term_pair_first_token_preference_diagnostic.json",
            )


def comparison_report(*, pair_full: bool = False) -> dict[str, object]:
    first_hit_terms = ["fixed", "loss"] if pair_full else ["fixed"]
    return {
        "status": "pass",
        "decision": "select_fixed_retention_route_for_loss_rebalance",
        "summary": {"pair_full_report_count": 1 if pair_full else 0, "union_hit_terms": ["fixed"] if not pair_full else ["fixed", "loss"]},
        "branch_rows": [
            {
                "source_label": "v612-delimiter-span",
                "corpus_mode": "equals_surface_no_pair_id_fixed_retention_delimiter_span_repair",
                "hit_terms": first_hit_terms,
                "missed_terms": [] if pair_full else ["loss"],
                "fixed_only_tradeoff": not pair_full,
                "loss_only_tradeoff": False,
                "pair_full_observed": pair_full,
            },
            {
                "source_label": "v613-context-switch",
                "corpus_mode": "equals_surface_no_pair_id_fixed_retention_context_switch_repair",
                "hit_terms": ["fixed"],
                "missed_terms": ["loss"],
                "fixed_only_tradeoff": True,
                "loss_only_tradeoff": False,
                "pair_full_observed": False,
            },
            {
                "source_label": "v611-contrast-free",
                "corpus_mode": "equals_surface_no_pair_id_fixed_retention_contrast_free_repair",
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "fixed_only_tradeoff": False,
                "loss_only_tradeoff": False,
                "pair_full_observed": False,
            },
        ],
    }


def prior_closeout_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "close_fixed_retention_loss_rebalance_batch_before_new_design",
        "summary": {"stop_current_loss_rebalance_routes": True},
    }


def first_token_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "first_token_preference_tradeoff_confirmed",
        "summary": {"first_token_conflict_confirmed": True, "mixed_branch_tradeoff_confirmed": True},
    }


if __name__ == "__main__":
    unittest.main()
