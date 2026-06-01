from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_execution_profile import (
    build_surface_policy_execution_profile,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_policy_execution_profile_outputs,
)


class SurfacePolicyExecutionProfileTests(unittest.TestCase):
    def test_profile_selects_minimal_stable_budget(self) -> None:
        report = build_surface_policy_execution_profile(leakage_fixture(), budget_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_execution_profile_selected")
        self.assertEqual(report["profile"]["profile_id"], "pair_context_prefix_budget_8")
        self.assertFalse(report["profile"]["promotion_allowed"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_budget_fails(self) -> None:
        budget = budget_fixture()
        budget["summary"]["minimal_stable_budget"] = None
        report = build_surface_policy_execution_profile(leakage_fixture(), budget)

        self.assertEqual(report["status"], "fail")
        self.assertIn("missing_minimal_budget", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_policy_execution_profile(leakage_fixture(), budget_fixture())
            outputs = write_surface_policy_execution_profile_outputs(report, Path(tmp) / "profile")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("profile_id=pair_context_prefix_budget_8", render_text(report))
        self.assertIn("Execution Profile", render_markdown(report))
        self.assertIn("MiniGPT surface policy execution profile", render_html(report))


def leakage_fixture() -> dict[str, object]:
    return {"status": "pass", "summary": {"promotion_allowed": False, "risk_level": "medium"}}


def budget_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "settings": {"temperature": 0.2, "top_k": 1, "device": "cpu"},
        "selected_policy": {
            "policy_id": "pair_context_prefix",
            "prompt_template": "{other_term}={other_term} {term}=",
            "leakage_level": "contextual_anchor",
        },
        "summary": {"minimal_stable_budget": 8},
    }


if __name__ == "__main__":
    unittest.main()
