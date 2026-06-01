from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_contrast_free_batch_closeout import (
    build_model_capability_required_term_pair_contrast_free_batch_closeout,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_contrast_free_batch_closeout_artifacts import (
    render_model_capability_required_term_pair_contrast_free_batch_closeout_html,
    render_model_capability_required_term_pair_contrast_free_batch_closeout_markdown,
    render_model_capability_required_term_pair_contrast_free_batch_closeout_text,
    write_model_capability_required_term_pair_contrast_free_batch_closeout_outputs,
)


class ContrastFreeBatchCloseoutTests(unittest.TestCase):
    def test_closeout_ready_for_new_loss_internal_preference_objective(self) -> None:
        report = build_model_capability_required_term_pair_contrast_free_batch_closeout(
            corpus_contract=corpus_contract(),
            refresh_reports=[refresh_report(False), refresh_report(False), refresh_report(False)],
            comparison=comparison_report(),
            route_decision=route_decision_report(),
            forced_choice=forced_choice_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_contrast_free_batch_and_design_loss_internal_preference_objective")
        self.assertTrue(report["summary"]["closeout_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_forced_choice_finds_full_match(self) -> None:
        forced = forced_choice_report(full_match=1)
        report = build_model_capability_required_term_pair_contrast_free_batch_closeout(
            corpus_contract=corpus_contract(),
            refresh_reports=[refresh_report(False), refresh_report(False), refresh_report(False)],
            comparison=comparison_report(),
            route_decision=route_decision_report(),
            forced_choice=forced,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("forced-choice diagnostic found a full internal match", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_contrast_free_batch_closeout(
                corpus_contract=corpus_contract(),
                refresh_reports=[refresh_report(False), refresh_report(False), refresh_report(False)],
                comparison=comparison_report(),
                route_decision=route_decision_report(),
                forced_choice=forced_choice_report(),
            )
            outputs = write_model_capability_required_term_pair_contrast_free_batch_closeout_outputs(report, root / "closeout")
            text = render_model_capability_required_term_pair_contrast_free_batch_closeout_text(report)
            markdown = render_model_capability_required_term_pair_contrast_free_batch_closeout_markdown(report)
            html = render_model_capability_required_term_pair_contrast_free_batch_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=close_contrast_free_batch_and_design_loss_internal_preference_objective", text)
            self.assertIn("Contrast-Free Batch Closeout", markdown)
            self.assertIn("MiniGPT contrast-free batch closeout", html)


def corpus_contract() -> dict[str, object]:
    return {"status": "pass", "decision": "contrast_free_objective_corpus_modes_ready", "summary": {"new_mode_count": 3}}


def refresh_report(pair_full: bool) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "summary": {"pair_full_observed": pair_full, "training_status": "pass"},
    }


def comparison_report() -> dict[str, object]:
    return {"status": "pass", "decision": "select_fixed_retention_route_for_loss_rebalance", "summary": {"pair_full_report_count": 0, "union_hit_terms": ["fixed"]}}


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "stop_contrast_free_routes_and_run_forced_choice_diagnostic",
        "summary": {"requires_forced_choice_diagnostic": True},
    }


def forced_choice_report(*, full_match: int = 0) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "refresh_forced_choice_partial_internal_match",
        "summary": {"expected_best_prompt_count": 3, "forced_choice_full_match_source_count": full_match, "best_internal_sources": []},
    }


if __name__ == "__main__":
    unittest.main()
