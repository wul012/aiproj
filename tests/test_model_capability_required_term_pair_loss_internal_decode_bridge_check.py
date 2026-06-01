from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_loss_internal_decode_bridge_check import (
    build_model_capability_required_term_pair_loss_internal_decode_bridge_check,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_loss_internal_decode_bridge_check_artifacts import (
    render_loss_internal_decode_bridge_check_html,
    render_loss_internal_decode_bridge_check_markdown,
    render_loss_internal_decode_bridge_check_text,
    write_loss_internal_decode_bridge_check_outputs,
)


class LossInternalDecodeBridgeCheckTests(unittest.TestCase):
    def test_confirms_gap_when_internal_pair_match_generation_misses_fixed(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_decode_bridge_check(
            refresh_report(),
            forced_choice_report(),
            route_decision_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "loss_internal_decode_bridge_gap_confirmed")
        self.assertEqual(report["summary"]["bridge_gap_terms"], ["fixed"])
        self.assertTrue(report["summary"]["decode_bridge_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_fails_when_generation_is_already_pair_full(self) -> None:
        report = build_model_capability_required_term_pair_loss_internal_decode_bridge_check(
            refresh_report(fixed_hit=True, loss_hit=True),
            forced_choice_report(),
            route_decision_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("selected source already has generation pair-full", report["issues"])

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_loss_internal_decode_bridge_check(
                refresh_report(),
                forced_choice_report(),
                route_decision_report(),
            )
            outputs = write_loss_internal_decode_bridge_check_outputs(report, root / "bridge")
            text = render_loss_internal_decode_bridge_check_text(report)
            markdown = render_loss_internal_decode_bridge_check_markdown(report)
            html = render_loss_internal_decode_bridge_check_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("bridge_gap_terms=fixed", text)
            self.assertIn("Loss-Internal Decode Bridge Check", markdown)
            self.assertIn("MiniGPT loss-internal decode bridge check", html)


def refresh_report(*, fixed_hit: bool = False, loss_hit: bool = True) -> dict[str, object]:
    return {
        "status": "pass",
        "replay_report": {
            "case_rows": [
                case_row("fixed", fixed_hit),
                case_row("loss", loss_hit),
            ]
        },
    }


def case_row(term: str, hit: bool) -> dict[str, object]:
    return {
        "profile_id": "default",
        "term": term,
        "prompt": f"{term}=",
        "continuation_hit": hit,
        "continuation_preview": term if hit else "miss",
    }


def forced_choice_report() -> dict[str, object]:
    return {
        "status": "pass",
        "prompt_summaries": [
            forced_row("fixed"),
            forced_row("loss"),
        ],
    }


def forced_row(term: str) -> dict[str, object]:
    return {
        "source_label": "loss-internal-first-token",
        "prompt_term": term,
        "expected_best": True,
        "best_candidate": term,
        "expected_avg_nll": 0.5,
        "best_avg_nll": 0.5,
        "expected_first_token_rank": 1,
    }


def route_decision_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "selected_decode_bridge_source": "loss-internal-first-token",
            "internal_to_generation_bridge_required": True,
        },
    }


if __name__ == "__main__":
    unittest.main()
