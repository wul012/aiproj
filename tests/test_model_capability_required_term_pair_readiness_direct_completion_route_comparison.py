from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_direct_completion_route_comparison import (
    build_direct_completion_route_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_direct_completion_route_comparison_artifacts import (
    render_direct_completion_route_comparison_html,
    render_direct_completion_route_comparison_markdown,
    render_direct_completion_route_comparison_text,
    write_direct_completion_route_comparison_outputs,
)


class DirectCompletionRouteComparisonTests(unittest.TestCase):
    def test_comparison_selects_direct_completion_candidate(self) -> None:
        report = build_direct_completion_route_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
            direct_completion_training_report=training_fixture("direct"),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_direct_completion_route_candidate_found")
        self.assertEqual(report["summary"]["previous_best_hit_count"], 0)
        self.assertEqual(report["summary"]["direct_completion_default_hit_count"], 2)
        self.assertEqual(report["summary"]["direct_completion_hit_delta_from_previous_best"], 2)
        self.assertEqual(report["summary"]["selected_route"], "direct-completion-surface")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_comparison_keeps_review_when_polluted(self) -> None:
        direct = training_fixture("direct")
        direct["replay_report"]["case_rows"][1]["continuation"] = "fixed loss"
        direct["replay_report"]["case_rows"][1]["continuation_hit"] = False
        report = build_direct_completion_route_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
            direct_completion_training_report=direct,
        )

        self.assertEqual(report["decision"], "pair_readiness_direct_completion_pair_full_with_review_flags")
        self.assertFalse(report["summary"]["direct_completion_candidate"])

    def test_comparison_fails_for_missing_checkpoint(self) -> None:
        direct = training_fixture("direct")
        direct["summary"]["checkpoint_exists"] = False
        report = build_direct_completion_route_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
            direct_completion_training_report=direct,
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("direct-completion-surface_checkpoint_missing", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_direct_completion_route_comparison(
            objective_training_report=training_fixture("objective"),
            bridge_training_report=training_fixture("bridge"),
            direct_completion_training_report=training_fixture("direct"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_direct_completion_route_comparison_outputs(report, Path(tmp))

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("direct_completion_hit_delta_from_previous_best=2", render_direct_completion_route_comparison_text(report))
        self.assertIn("Direct-Completion Route Comparison", render_direct_completion_route_comparison_markdown(report))
        self.assertIn("MiniGPT direct-completion route comparison", render_direct_completion_route_comparison_html(report))


def training_fixture(kind: str) -> dict[str, object]:
    if kind == "objective":
        decision = "pair_readiness_training_no_pair_full"
        pair_full = False
        continuations = [("fixed", "d | | |", False), ("loss", "d | | |", False)]
    elif kind == "bridge":
        decision = "pair_readiness_training_no_pair_full"
        pair_full = False
        continuations = [("fixed", " | | | ted |", False), ("loss", "fixed | | |", False)]
    else:
        decision = "pair_readiness_training_pair_full_observed"
        pair_full = True
        continuations = [("fixed", "fixed", True), ("loss", "loss", True)]
    return {
        "status": "pass",
        "decision": decision,
        "summary": {
            "training_status": "pass",
            "checkpoint_exists": True,
            "pair_full_observed": pair_full,
            "suppression_continuation_hit_count": 2 if pair_full else 0,
        },
        "replay_report": {
            "case_rows": [
                {"profile_id": "default", "term": term, "continuation": continuation, "continuation_hit": hit}
                for term, continuation, hit in continuations
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
