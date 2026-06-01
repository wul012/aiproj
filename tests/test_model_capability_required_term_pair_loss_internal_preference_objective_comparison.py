from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_comparison import (
    build_model_capability_required_term_pair_loss_internal_preference_objective_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_internal_preference_objective_comparison_artifacts import (
    render_loss_internal_preference_objective_comparison_html,
    render_loss_internal_preference_objective_comparison_markdown,
    render_loss_internal_preference_objective_comparison_text,
    write_loss_internal_preference_objective_comparison_outputs,
)


class LossInternalPreferenceObjectiveComparisonTests(unittest.TestCase):
    def test_comparison_records_mixed_tradeoff_without_pair_full(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_preference_objective_comparison(
            [
                refresh_report("equals_surface_no_pair_id_loss_internal_preference_repair", ["fixed"]),
                refresh_report("equals_surface_no_pair_id_loss_internal_first_token_repair", ["loss"]),
                refresh_report("equals_surface_no_pair_id_loss_internal_ranked_choice_repair", ["fixed"]),
            ]
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "loss_internal_preference_objectives_confirm_branch_tradeoff")
        self.assertEqual(report["summary"]["pair_full_report_count"], 0)
        self.assertEqual(report["summary"]["fixed_only_tradeoff_report_count"], 2)
        self.assertEqual(report["summary"]["loss_only_tradeoff_report_count"], 1)
        self.assertEqual(report["summary"]["union_hit_terms"], ["fixed", "loss"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_fails_when_mode_is_not_loss_internal(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_preference_objective_comparison(
            [
                refresh_report("equals_surface_no_pair_id_loss_internal_preference_repair", ["fixed"]),
                refresh_report("equals_surface_no_pair_id_fixed_retention_contrast_free_repair", ["fixed"]),
            ]
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("loss-internal-report-2 is not a loss-internal-preference objective corpus mode", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_internal_preference_objective_comparison(
                [
                    refresh_report("equals_surface_no_pair_id_loss_internal_preference_repair", ["fixed"]),
                    refresh_report("equals_surface_no_pair_id_loss_internal_first_token_repair", ["loss"]),
                ]
            )
            outputs = write_loss_internal_preference_objective_comparison_outputs(report, root / "comparison")
            text = render_loss_internal_preference_objective_comparison_text(report)
            markdown = render_loss_internal_preference_objective_comparison_markdown(report)
            html = render_loss_internal_preference_objective_comparison_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=loss_internal_preference_objectives_confirm_branch_tradeoff", text)
            self.assertIn("Loss-Internal-Preference Objective Comparison", markdown)
            self.assertIn("MiniGPT loss-internal-preference objective comparison", html)


def refresh_report(corpus_mode: str, hit_terms: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_coexistence_refresh_no_pair_full",
        "settings": {"corpus_mode": corpus_mode, "seed": 3535},
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": set(["fixed", "loss"]).issubset(hit_terms),
            "default_pair_full_variant_count": 0,
            "suppression_pair_full_variant_count": 0,
        },
        "replay_report": {
            "case_rows": [
                case_row("default", "fixed", "fixed" in hit_terms),
                case_row("default", "loss", "loss" in hit_terms),
            ]
        },
    }


def case_row(profile_id: str, term: str, hit: bool) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "term": term,
        "prompt": f"{term}=",
        "continuation_hit": hit,
        "continuation_preview": term if hit else "miss",
    }


if __name__ == "__main__":
    unittest.main()
