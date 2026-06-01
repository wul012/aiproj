from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_policy_plan import (
    build_model_capability_required_term_pair_surface_policy_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_surface_policy_plan_artifacts import (
    render_surface_policy_plan_html,
    render_surface_policy_plan_markdown,
    render_surface_policy_plan_text,
    write_surface_policy_plan_outputs,
)


class SurfacePolicyPlanTests(unittest.TestCase):
    def test_policy_plan_excludes_target_echo_and_keeps_replay_candidates(self) -> None:
        report = build_model_capability_required_term_pair_surface_policy_plan(
            surface_failure_fixture(),
            generated_at="2026-06-02T00:20:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_policy_plan_ready")
        self.assertEqual(report["summary"]["failure_terms"], ["loss"])
        self.assertIn("pair_context_prefix", report["summary"]["recommended_replay_policy_ids"])
        self.assertNotIn("target_echo_upper_bound", report["summary"]["recommended_replay_policy_ids"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_policy_plan_fails_without_surface_failure(self) -> None:
        source = surface_failure_fixture()
        source["summary"]["surface_failure_seed_count"] = 0
        source["summary"]["surface_failure_terms"] = []
        report = build_model_capability_required_term_pair_surface_policy_plan(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source diagnostic has no surface failure to plan against", report["issues"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_model_capability_required_term_pair_surface_policy_plan(surface_failure_fixture())
            outputs = write_surface_policy_plan_outputs(report, root / "plan")
            text = render_surface_policy_plan_text(report)
            markdown = render_surface_policy_plan_markdown(report)
            html = render_surface_policy_plan_html(report)

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertIn("surface_policy_plan_ready", text)
            self.assertIn("Surface Policy Plan", markdown)
            self.assertIn("MiniGPT surface policy plan", html)


def surface_failure_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "required_term_pair_single_term_surface_failure_isolated",
        "summary": {
            "surface_failure_seed_count": 1,
            "surface_failure_terms": ["loss"],
        },
    }


if __name__ == "__main__":
    unittest.main()
