from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_route_closeout_summary import (
    build_model_capability_required_term_pair_route_closeout_summary,
    locate_fresh_seed_report,
    locate_fresh_seed_route_decision_report,
    locate_heldout_replay_report,
    locate_route_comparison_report,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_route_closeout_summary_artifacts import (
    render_model_capability_required_term_pair_route_closeout_summary_html,
    render_model_capability_required_term_pair_route_closeout_summary_markdown,
    render_model_capability_required_term_pair_route_closeout_summary_text,
    write_model_capability_required_term_pair_route_closeout_summary_outputs,
)


class ModelCapabilityRequiredTermPairRouteCloseoutSummaryTests(unittest.TestCase):
    def test_closeout_ready_when_heldout_passes_and_fresh_seed_fails(self) -> None:
        report = build_model_capability_required_term_pair_route_closeout_summary(
            heldout_report=heldout_report(),
            fresh_seed_reports=[fresh_seed_report("v571", 1), fresh_seed_report("v573", 0), fresh_seed_report("v575", 0)],
            comparison_report=comparison_report(),
            route_decision_report=route_decision_report(),
            fresh_seed_labels=["v571-loss-balanced", "v573-first-token", "v575-wider-embd"],
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "close_required_term_pair_route_before_new_objective")
        self.assertTrue(report["summary"]["closeout_ready"])
        self.assertEqual(report["summary"]["fresh_seed_pair_full_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_closeout_fails_when_decision_does_not_stop_width(self) -> None:
        decision = route_decision_report()
        decision["summary"]["stop_width_scaling"] = False
        report = build_model_capability_required_term_pair_route_closeout_summary(
            heldout_report=heldout_report(),
            fresh_seed_reports=[fresh_seed_report("v571", 1)],
            comparison_report=comparison_report(),
            route_decision_report=decision,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("route decision did not stop width scaling", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_route_closeout_summary(
                heldout_report=heldout_report(),
                fresh_seed_reports=[fresh_seed_report("v571", 1), fresh_seed_report("v573", 0)],
                comparison_report=comparison_report(),
                route_decision_report=route_decision_report(),
            )
            outputs = write_model_capability_required_term_pair_route_closeout_summary_outputs(report, root / "closeout")
            text = render_model_capability_required_term_pair_route_closeout_summary_text(report)
            markdown = render_model_capability_required_term_pair_route_closeout_summary_markdown(report)
            html = render_model_capability_required_term_pair_route_closeout_summary_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("decision=close_required_term_pair_route_before_new_objective", text)
            self.assertIn("Route Closeout Summary", markdown)
            self.assertIn("MiniGPT route closeout summary", html)

    def test_locate_accepts_output_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(locate_heldout_replay_report(root), root / "model_capability_required_term_pair_route_heldout_replay.json")
            self.assertEqual(locate_fresh_seed_report(root), root / "model_capability_required_term_pair_colon_immediate_stability.json")
            self.assertEqual(locate_route_comparison_report(root), root / "model_capability_required_term_pair_equals_surface_repair_comparison.json")
            self.assertEqual(locate_fresh_seed_route_decision_report(root), root / "model_capability_required_term_pair_fresh_seed_route_decision.json")


def heldout_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_route_heldout_replay_ready",
        "summary": {
            "heldout_pair_full_count": 7,
            "heldout_spec_count": 7,
            "heldout_all_pair_full": True,
        },
    }


def fresh_seed_report(label: str, hits: int) -> dict[str, object]:
    return {
        "status": "pass",
        "decision": f"{label}-no-pair-full",
        "summary": {
            "seed_count": 1,
            "pair_full_seed_count": 0,
            "stable_pair_full": False,
        },
        "seed_rows": [{"continuation_hit_count": hits}],
    }


def comparison_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_equals_surface_repair_comparison_recorded",
        "summary": {
            "union_hit_terms": ["fixed"],
            "pair_full_profile_seed_count": 0,
        },
    }


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "stop_first_token_and_width_for_fresh_seed",
        "summary": {
            "stop_first_token_route": True,
            "stop_width_scaling": True,
            "best_residual_signal": "v571-loss-balanced",
        },
    }


if __name__ == "__main__":
    unittest.main()
