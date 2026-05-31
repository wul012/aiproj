from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_first_token_route_decision import (
    build_model_capability_required_term_pair_first_token_route_decision,
    locate_first_token_route_decision_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_first_token_route_decision_artifacts import (
    render_model_capability_required_term_pair_first_token_route_decision_html,
    render_model_capability_required_term_pair_first_token_route_decision_markdown,
    render_model_capability_required_term_pair_first_token_route_decision_text,
    write_model_capability_required_term_pair_first_token_route_decision_outputs,
)


class ModelCapabilityRequiredTermPairFirstTokenRouteDecisionTests(unittest.TestCase):
    def test_decision_stops_first_token_density_and_selects_simple_baseline(self) -> None:
        report = build_model_capability_required_term_pair_first_token_route_decision(
            comparison_report(),
            source_path="comparison.json",
            generated_at="2026-05-31T07:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "stop_first_token_density_and_replay_best_baseline")
        self.assertEqual(report["summary"]["stable_route_count"], 0)
        self.assertTrue(report["summary"]["stop_first_token_density"])
        self.assertEqual(report["selected_route"]["source_label"], "v562-loss-balanced")
        self.assertEqual(report["selected_route"]["pair_full_seed_count"], 1)
        self.assertEqual(len(report["rejected_routes"]), 2)
        self.assertIn("first_token_density_no_stable_gain", report["rejected_routes"][0]["reasons"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_invalid_input_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_first_token_route_decision(
            {"status": "fail", "summary": {"compared_report_count": 0}, "source_reports": []}
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source comparison status is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_first_token_route_decision(comparison_report())
            outputs = write_model_capability_required_term_pair_first_token_route_decision_outputs(report, root / "decision")
            text = render_model_capability_required_term_pair_first_token_route_decision_text(report)
            markdown = render_model_capability_required_term_pair_first_token_route_decision_markdown(report)
            html = render_model_capability_required_term_pair_first_token_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("selected_source_label=v562-loss-balanced", text)
            self.assertIn("v566-light-first-token", markdown)
            self.assertIn("MiniGPT first-token route decision", html)

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_first_token_route_decision_input(root),
                root / "model_capability_required_term_pair_equals_surface_repair_comparison.json",
            )


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_equals_surface_pair_full_found",
        "summary": {
            "compared_report_count": 3,
            "pair_full_profile_seed_count": 1,
            "branch_competition_seed_count": 0,
        },
        "source_reports": [
            source_report("v562-loss-balanced", "equals_surface_no_pair_id_loss_balanced_repair", 1),
            source_report("v564-full-first-token", "equals_surface_no_pair_id_loss_balanced_first_token_repair", 1),
            source_report("v566-light-first-token", "equals_surface_no_pair_id_loss_balanced_light_first_token_repair", 0),
        ],
    }


def source_report(label: str, corpus_mode: str, pair_full_count: int) -> dict[str, object]:
    return {
        "source_label": label,
        "source_path": f"{label}.json",
        "status": "pass",
        "decision": "required_term_pair_colon_immediate_partial_stability",
        "corpus_mode": corpus_mode,
        "seed_count": 3,
        "pair_full_seed_count": pair_full_count,
        "pair_full_seed_rate": round(pair_full_count / 3, 4),
        "stable_pair_full": False,
    }


if __name__ == "__main__":
    unittest.main()
