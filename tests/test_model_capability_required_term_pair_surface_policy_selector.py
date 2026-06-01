from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_selector import (
    build_model_capability_required_term_pair_surface_policy_selector,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_policy_selector_artifacts import (
    render_surface_policy_selector_html,
    render_surface_policy_selector_markdown,
    render_surface_policy_selector_text,
    write_surface_policy_selector_outputs,
)


class SurfacePolicySelectorTests(unittest.TestCase):
    def test_selector_prefers_shorter_contextual_policy_over_boundary_sentence(self) -> None:
        report = build_model_capability_required_term_pair_surface_policy_selector(
            policy_plan_fixture(),
            policy_replay_fixture(),
            generated_at="2026-06-02T01:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_selected_for_minimality_check")
        self.assertEqual(report["summary"]["selected_policy_id"], "pair_context_prefix")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_selector_fails_without_stable_policy(self) -> None:
        replay = policy_replay_fixture()
        for row in replay["policy_summaries"]:
            row["stable_pair_full"] = False
        report = build_model_capability_required_term_pair_surface_policy_selector(policy_plan_fixture(), replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("policy replay has no stable pair-full policy", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_selector(policy_plan_fixture(), policy_replay_fixture())
            outputs = write_surface_policy_selector_outputs(report, root / "selector")
            text = render_surface_policy_selector_text(report)
            markdown = render_surface_policy_selector_markdown(report)
            html = render_surface_policy_selector_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("selected_policy_id=pair_context_prefix", text)
            self.assertIn("Surface Policy Selector", markdown)
            self.assertIn("MiniGPT surface policy selector", html)


def policy_plan_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "policy_rows": [
            {
                "policy_id": "pair_context_prefix",
                "prompt_template": "{other_term}={other_term} {term}=",
                "leakage_level": "contextual_anchor",
                "included_in_replay": True,
            },
            {
                "policy_id": "dual_boundary_sentence",
                "prompt_template": "dual boundary surface {other_term}={other_term} {term}=",
                "leakage_level": "contextual_anchor",
                "included_in_replay": True,
            },
        ],
    }


def policy_replay_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "policy_summaries": [
            {
                "policy_id": "pair_context_prefix",
                "pair_full_seed_count": 3,
                "hit_case_count": 6,
                "stable_pair_full": True,
            },
            {
                "policy_id": "dual_boundary_sentence",
                "pair_full_seed_count": 3,
                "hit_case_count": 6,
                "stable_pair_full": True,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
