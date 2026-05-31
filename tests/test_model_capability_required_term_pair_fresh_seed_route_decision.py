from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_fresh_seed_route_decision import (
    build_model_capability_required_term_pair_fresh_seed_route_decision,
    locate_fresh_seed_route_decision_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_fresh_seed_route_decision_artifacts import (
    render_model_capability_required_term_pair_fresh_seed_route_decision_html,
    render_model_capability_required_term_pair_fresh_seed_route_decision_markdown,
    render_model_capability_required_term_pair_fresh_seed_route_decision_text,
    write_model_capability_required_term_pair_fresh_seed_route_decision_outputs,
)


class ModelCapabilityRequiredTermPairFreshSeedRouteDecisionTests(unittest.TestCase):
    def test_decision_stops_first_token_and_width_routes(self) -> None:
        report = build_model_capability_required_term_pair_fresh_seed_route_decision(comparison_report(), source_path="comparison.json")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "stop_first_token_and_width_for_fresh_seed")
        self.assertEqual(report["summary"]["pair_full_route_count"], 0)
        self.assertEqual(report["summary"]["best_residual_signal"], "v571-loss-balanced")
        self.assertTrue(report["summary"]["stop_first_token_route"])
        self.assertTrue(report["summary"]["stop_width_scaling"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_invalid_input_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_fresh_seed_route_decision({"status": "fail", "source_reports": []})

        self.assertEqual(report["status"], "fail")
        self.assertIn("source comparison status is not pass", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_fresh_seed_route_decision(comparison_report())
            outputs = write_model_capability_required_term_pair_fresh_seed_route_decision_outputs(report, root / "decision")
            text = render_model_capability_required_term_pair_fresh_seed_route_decision_text(report)
            markdown = render_model_capability_required_term_pair_fresh_seed_route_decision_markdown(report)
            html = render_model_capability_required_term_pair_fresh_seed_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=stop_first_token_and_width_for_fresh_seed", text)
            self.assertIn("v575-wider-embd", markdown)
            self.assertIn("MiniGPT fresh-seed route decision", html)

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_fresh_seed_route_decision_input(root),
                root / "model_capability_required_term_pair_equals_surface_repair_comparison.json",
            )


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"pair_full_profile_seed_count": 0, "union_hit_terms": ["fixed"]},
        "source_reports": [
            source("v571-loss-balanced", "equals_surface_no_pair_id_loss_balanced_repair"),
            source("v573-first-token", "equals_surface_no_pair_id_loss_balanced_first_token_repair"),
            source("v575-wider-embd", "equals_surface_no_pair_id_loss_balanced_repair"),
        ],
        "term_rows": [
            {"source_label": "v571-loss-balanced", "term": "fixed", "continuation_hit": True},
            {"source_label": "v571-loss-balanced", "term": "loss", "continuation_hit": False},
            {"source_label": "v573-first-token", "term": "fixed", "continuation_hit": False},
            {"source_label": "v575-wider-embd", "term": "loss", "continuation_hit": False},
        ],
    }


def source(label: str, mode: str) -> dict[str, object]:
    return {
        "source_label": label,
        "corpus_mode": mode,
        "pair_full_seed_count": 0,
        "seed_count": 1,
        "stable_pair_full": False,
    }


if __name__ == "__main__":
    unittest.main()
