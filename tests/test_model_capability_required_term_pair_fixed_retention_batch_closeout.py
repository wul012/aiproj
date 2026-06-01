from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_fixed_retention_batch_closeout import (
    build_model_capability_required_term_pair_fixed_retention_batch_closeout,
    locate_fixed_retention_comparison_report,
    locate_fixed_retention_refresh_report,
    locate_fixed_retention_route_decision_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fixed_retention_batch_closeout_artifacts import (
    render_model_capability_required_term_pair_fixed_retention_batch_closeout_html,
    render_model_capability_required_term_pair_fixed_retention_batch_closeout_markdown,
    render_model_capability_required_term_pair_fixed_retention_batch_closeout_text,
    write_model_capability_required_term_pair_fixed_retention_batch_closeout_outputs,
)


class ModelCapabilityRequiredTermPairFixedRetentionBatchCloseoutTests(unittest.TestCase):
    def test_closeout_stops_loss_rebalance_when_routes_trade_off(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_batch_closeout(
            initial_reports=[refresh_report("balanced", ["loss"]), refresh_report("first", ["fixed"]), refresh_report("guard", ["loss"])],
            loss_rebalance_reports=[refresh_report("rebalance", ["loss"]), refresh_report("dual", ["fixed"])],
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_fixed_retention_loss_rebalance_batch_before_new_design")
        self.assertEqual(report["summary"]["loss_rebalance_pair_full_count"], 0)
        self.assertTrue(report["summary"]["loss_rebalance_tradeoff_confirmed"])
        self.assertTrue(report["summary"]["stop_current_loss_rebalance_routes"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_routes_pair_full_candidate_to_seed_stability(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_batch_closeout(
            initial_reports=[refresh_report("balanced", ["loss"]), refresh_report("first", ["fixed"]), refresh_report("guard", ["loss"])],
            loss_rebalance_reports=[refresh_report("rebalance", ["fixed", "loss"], pair_full=True), refresh_report("dual", ["fixed"])],
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "promote_loss_rebalance_pair_full_candidate_to_seed_stability")
        self.assertEqual(report["summary"]["loss_rebalance_pair_full_count"], 1)

    def test_closeout_fails_when_loss_rebalance_input_is_missing(self) -> None:
        report = build_model_capability_required_term_pair_fixed_retention_batch_closeout(
            initial_reports=[refresh_report("balanced", ["loss"]), refresh_report("first", ["fixed"]), refresh_report("guard", ["loss"])],
            loss_rebalance_reports=[refresh_report("rebalance", ["loss"])],
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("at least two loss-rebalance reports are required", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_fixed_retention_batch_closeout(
                initial_reports=[refresh_report("balanced", ["loss"]), refresh_report("first", ["fixed"]), refresh_report("guard", ["loss"])],
                loss_rebalance_reports=[refresh_report("rebalance", ["loss"]), refresh_report("dual", ["fixed"])],
                comparison_report=comparison_report(),
                route_decision_report=route_decision_report(),
            )
            outputs = write_model_capability_required_term_pair_fixed_retention_batch_closeout_outputs(report, root / "closeout")
            text = render_model_capability_required_term_pair_fixed_retention_batch_closeout_text(report)
            markdown = render_model_capability_required_term_pair_fixed_retention_batch_closeout_markdown(report)
            html = render_model_capability_required_term_pair_fixed_retention_batch_closeout_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=close_fixed_retention_loss_rebalance_batch_before_new_design", text)
            self.assertIn("Fixed-Retention Batch Closeout", markdown)
            self.assertIn("MiniGPT fixed-retention batch closeout", html)

    def test_locators_accept_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_fixed_retention_refresh_report(root),
                root / "model_capability_required_term_pair_coexistence_refresh.json",
            )
            self.assertEqual(
                locate_fixed_retention_comparison_report(root),
                root / "model_capability_required_term_pair_fixed_retention_objective_comparison.json",
            )
            self.assertEqual(
                locate_fixed_retention_route_decision_report(root),
                root / "model_capability_required_term_pair_fixed_retention_route_decision.json",
            )


def refresh_report(mode: str, hit_terms: list[str], *, pair_full: bool = False) -> dict[str, object]:
    rows = []
    for term in ("fixed", "loss"):
        rows.append(
            {
                "profile_id": "default",
                "term": term,
                "continuation_hit": term in hit_terms,
                "generated_preview": f"{term}={term}",
                "continuation_preview": term,
            }
        )
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": f"equals_surface_no_pair_id_fixed_retention_{mode}_repair", "seed": 3535},
        "summary": {"training_status": "pass", "checkpoint_exists": True, "pair_full_observed": pair_full},
        "replay_report": {"case_rows": rows},
    }


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "fixed_retention_objectives_confirm_branch_tradeoff",
        "summary": {"pair_full_report_count": 0, "mixed_tradeoff_observed": True},
    }


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "select_fixed_recovery_route_for_loss_rebalance_not_promotion",
        "summary": {
            "selected_route": "v601-first-token",
            "selected_corpus_mode": "equals_surface_no_pair_id_fixed_retention_first_token_repair",
            "loss_rebalance_objective_required": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
