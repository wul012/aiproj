from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_minimality_check import (
    build_model_capability_required_term_pair_surface_policy_minimality_check,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_policy_minimality_check_artifacts import (
    render_surface_policy_minimality_check_html,
    render_surface_policy_minimality_check_markdown,
    render_surface_policy_minimality_check_text,
    write_surface_policy_minimality_check_outputs,
)


class SurfacePolicyMinimalityCheckTests(unittest.TestCase):
    def test_minimality_check_marks_contextual_anchor_required(self) -> None:
        report = build_model_capability_required_term_pair_surface_policy_minimality_check(
            selector_fixture(),
            replay_fixture(),
            generated_at="2026-06-02T01:20:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_contextual_anchor_required")
        self.assertTrue(report["summary"]["contextual_anchor_required"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_minimality_check_fails_when_selected_policy_not_stable(self) -> None:
        replay = replay_fixture()
        replay["policy_summaries"][1]["stable_pair_full"] = False
        report = build_model_capability_required_term_pair_surface_policy_minimality_check(selector_fixture(), replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("selected policy must be stable across seeds", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_minimality_check(selector_fixture(), replay_fixture())
            outputs = write_surface_policy_minimality_check_outputs(report, root / "check")
            text = render_surface_policy_minimality_check_text(report)
            markdown = render_surface_policy_minimality_check_markdown(report)
            html = render_surface_policy_minimality_check_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("contextual_anchor_required=True", text)
            self.assertIn("Surface Policy Minimality Check", markdown)
            self.assertIn("MiniGPT surface policy minimality check", html)


def selector_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "selected_policy": {
            "policy_id": "pair_context_prefix",
            "leakage_level": "contextual_anchor",
        },
        "summary": {"promotion_ready": False},
    }


def replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "policy_summaries": [
            {"policy_id": "single_label_default", "stable_pair_full": False},
            {"policy_id": "pair_context_prefix", "stable_pair_full": True},
        ],
    }


if __name__ == "__main__":
    unittest.main()
