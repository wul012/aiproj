from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision import (
    build_model_capability_route_promotion_bounded_rebalanced_intervention_decision,
    locate_rebalanced_comparison,
    locate_rebalanced_failure_diagnostic,
    locate_rebalanced_profile_sweep,
    locate_rebalanced_seed_revision,
    locate_rebalanced_training_run,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_rebalanced_intervention_decision_artifacts import (
    render_bounded_rebalanced_intervention_decision_html,
    render_bounded_rebalanced_intervention_decision_markdown,
    render_bounded_rebalanced_intervention_decision_text,
    write_bounded_rebalanced_intervention_decision_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_model_capability_route_promotion_bounded_rebalanced_intervention_decision import main as cli_main


class BoundedRebalancedInterventionDecisionTests(unittest.TestCase):
    def test_stops_rebalanced_decoder_rescue_after_no_profile_recovery(self) -> None:
        report = build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
            seed_report(),
            training_report(),
            comparison_report(),
            diagnostic_report(),
            profile_sweep_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention")
        self.assertEqual(report["summary"]["selected_intervention_track"], "objective_contract_intervention_first")
        self.assertEqual(report["summary"]["recommended_next_artifact"], "model_capability_route_promotion_bounded_objective_intervention_plan")
        self.assertFalse(report["summary"]["promotion_allowed"])
        self.assertFalse(report["summary"]["new_training_allowed"])
        self.assertIn("decoder_profile_sweep_no_recovery", report["route"]["stop_reasons"])
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True, require_intervention_selected=True), 0)

    def test_partial_profile_recovery_routes_to_review_before_intervention(self) -> None:
        sweep = profile_sweep_report()
        sweep["summary"]["any_profile_recovered"] = True
        sweep["summary"]["best_passed_case_count"] = 1
        report = build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
            seed_report(),
            training_report(),
            comparison_report(),
            diagnostic_report(),
            sweep,
        )

        self.assertEqual(report["decision"], "hold_rebalanced_decoder_rescue_for_partial_recovery_review")
        self.assertEqual(report["summary"]["selected_intervention_track"], "partial_decoder_profile_recovery_review")
        self.assertFalse(report["summary"]["promotion_allowed"])

    def test_distribution_must_be_repaired_before_closing_branch(self) -> None:
        seed = seed_report()
        seed["summary"]["direct_answer_share"] = 0.1
        seed["summary"]["carry_forward_share"] = 0.7
        report = build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
            seed,
            training_report(),
            comparison_report(),
            diagnostic_report(),
            profile_sweep_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("distribution_repaired", [row["id"] for row in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_decision_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_inputs(root)
            self.assertEqual(locate_rebalanced_seed_revision(paths["seed"].parent), paths["seed"])
            self.assertEqual(locate_rebalanced_training_run(paths["training"].parent), paths["training"])
            self.assertEqual(locate_rebalanced_comparison(paths["comparison"].parent), paths["comparison"])
            self.assertEqual(locate_rebalanced_failure_diagnostic(paths["diagnostic"].parent), paths["diagnostic"])
            self.assertEqual(locate_rebalanced_profile_sweep(paths["sweep"].parent), paths["sweep"])
            report = build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
                seed_report(),
                training_report(),
                comparison_report(),
                diagnostic_report(),
                profile_sweep_report(),
            )
            outputs = write_bounded_rebalanced_intervention_decision_outputs(report, root / "decision")
            cli_main(
                [
                    "--rebalanced-seed",
                    str(paths["seed"].parent),
                    "--training-run",
                    str(paths["training"].parent),
                    "--comparison",
                    str(paths["comparison"].parent),
                    "--failure-diagnostic",
                    str(paths["diagnostic"].parent),
                    "--profile-sweep",
                    str(paths["sweep"].parent),
                    "--out-dir",
                    str(root / "cli-decision"),
                    "--require-decision-ready",
                    "--require-intervention-selected",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("selected_intervention_track=objective_contract_intervention_first", render_bounded_rebalanced_intervention_decision_text(report))
        self.assertIn("Stop Reasons", render_bounded_rebalanced_intervention_decision_markdown(report))
        self.assertIn("Blocked Actions", render_bounded_rebalanced_intervention_decision_html(report))


def write_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "seed": root / "seed" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.json",
        "training": root / "training" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run.json",
        "comparison": root / "comparison" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison.json",
        "diagnostic": root / "diagnostic" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.json",
        "sweep": root / "sweep" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.json",
    }
    write_json_payload(seed_report(), paths["seed"])
    write_json_payload(training_report(), paths["training"])
    write_json_payload(comparison_report(), paths["comparison"])
    write_json_payload(diagnostic_report(), paths["diagnostic"])
    write_json_payload(profile_sweep_report(), paths["sweep"])
    return paths


def seed_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_rebalanced_seed_revision_ready": True,
            "case_count": 5,
            "direct_answer_share": 0.375,
            "carry_forward_share": 0.25,
            "decoder_bridge_share": 0.375,
        },
    }


def training_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_rebalanced_training_ready": True,
            "final_val_loss": 4.1945,
        },
    }


def comparison_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "rebalanced_checkpoint_comparison_ready": True,
            "rebalanced_passed_case_count": 0,
            "rebalanced_vs_baseline_pass_rate_delta": -0.4,
            "rebalanced_vs_decoder_anchor_pass_rate_delta": 0.0,
            "promotion_ready": False,
        },
    }


def diagnostic_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "rebalanced_failure_diagnostic_ready": True,
            "case_count": 5,
            "zero_hit_case_count": 5,
            "fragment_like_case_count": 5,
            "root_cause_count": 4,
        },
    }


def profile_sweep_report() -> dict:
    return {
        "status": "pass",
        "summary": {
            "rebalanced_profile_sweep_ready": True,
            "case_count": 5,
            "best_profile_id": "greedy_short",
            "best_passed_case_count": 0,
            "best_any_hit_case_count": 0,
            "any_profile_recovered": False,
            "promotion_ready": False,
            "next_step": "route_to_objective_or_architecture_intervention",
        },
    }


if __name__ == "__main__":
    unittest.main()
