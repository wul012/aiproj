from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_branch_binding_route_decision import (
    build_model_capability_required_term_pair_branch_binding_route_decision,
    locate_branch_binding_route_decision_input,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_branch_binding_route_decision_artifacts import (
    render_model_capability_required_term_pair_branch_binding_route_decision_html,
    render_model_capability_required_term_pair_branch_binding_route_decision_markdown,
    render_model_capability_required_term_pair_branch_binding_route_decision_text,
    write_model_capability_required_term_pair_branch_binding_route_decision_outputs,
)


class ModelCapabilityRequiredTermPairBranchBindingRouteDecisionTests(unittest.TestCase):
    def test_decision_stops_branch_binding_when_it_regresses_below_baseline(self) -> None:
        report = build_model_capability_required_term_pair_branch_binding_route_decision(comparison_report())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "stop_branch_binding_v1_and_keep_residual_baseline")
        self.assertEqual(report["summary"]["branch_binding_route_count"], 2)
        self.assertEqual(report["summary"]["branch_binding_visible_hit_route_count"], 0)
        self.assertEqual(report["summary"]["best_residual_signal"], "v571-loss-balanced")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_decision_promotes_branch_binding_when_pair_full_exists(self) -> None:
        payload = comparison_report()
        payload["source_reports"][1]["pair_full_seed_count"] = 1
        payload["term_rows"].append(term_row("v579-branch-binding", "loss", True))
        report = build_model_capability_required_term_pair_branch_binding_route_decision(payload)

        self.assertEqual(report["decision"], "promote_branch_binding_pair_full_route")

    def test_invalid_input_fails_require_pass(self) -> None:
        report = build_model_capability_required_term_pair_branch_binding_route_decision({"status": "fail", "source_reports": []})

        self.assertEqual(report["status"], "fail")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_branch_binding_route_decision(comparison_report())
            outputs = write_model_capability_required_term_pair_branch_binding_route_decision_outputs(report, root / "decision")
            text = render_model_capability_required_term_pair_branch_binding_route_decision_text(report)
            markdown = render_model_capability_required_term_pair_branch_binding_route_decision_markdown(report)
            html = render_model_capability_required_term_pair_branch_binding_route_decision_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=stop_branch_binding_v1_and_keep_residual_baseline", text)
            self.assertIn("Branch-Binding Route Decision", markdown)
            self.assertIn("MiniGPT branch-binding route decision", html)

    def test_locate_accepts_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(
                locate_branch_binding_route_decision_input(root),
                root / "model_capability_required_term_pair_equals_surface_repair_comparison.json",
            )


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "pair_full_profile_seed_count": 0,
            "union_hit_terms": ["fixed"],
        },
        "source_reports": [
            source("v571-loss-balanced", "equals_surface_no_pair_id_loss_balanced_repair"),
            source("v579-branch-binding", "equals_surface_no_pair_id_branch_binding_repair"),
            source("v581-branch-binding-no-space", "equals_surface_no_pair_id_branch_binding_no_space_repair"),
        ],
        "term_rows": [
            term_row("v571-loss-balanced", "fixed", True),
            term_row("v571-loss-balanced", "loss", False),
            term_row("v579-branch-binding", "fixed", False),
            term_row("v579-branch-binding", "loss", False),
            term_row("v581-branch-binding-no-space", "fixed", False),
            term_row("v581-branch-binding-no-space", "loss", False),
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


def term_row(label: str, term: str, hit: bool) -> dict[str, object]:
    return {
        "source_label": label,
        "term": term,
        "continuation_hit": hit,
    }


if __name__ == "__main__":
    unittest.main()
