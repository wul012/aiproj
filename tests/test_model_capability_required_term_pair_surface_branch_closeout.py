from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_surface_branch_closeout import (
    SOURCE_FILENAMES,
    build_surface_branch_closeout,
    render_html,
    render_markdown,
    render_text,
    resolve_exit_code,
    write_surface_branch_closeout_outputs,
)


class SurfaceBranchCloseoutTests(unittest.TestCase):
    def test_closeout_closes_contextual_branch(self) -> None:
        report = build_surface_branch_closeout(reports_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "required_term_pair_surface_branch_closed_as_contextual_decode_aid")
        self.assertTrue(report["summary"]["contextual_decode_aid_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_missing_report_fails(self) -> None:
        reports = reports_fixture()
        del reports["route_decision"]
        report = build_surface_branch_closeout(reports)

        self.assertEqual(report["status"], "fail")
        self.assertIn("missing_route_decision", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = build_surface_branch_closeout(reports_fixture())
            outputs = write_surface_branch_closeout_outputs(report, Path(tmp) / "closeout")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("contextual_decode_aid_ready=True", render_text(report))
        self.assertIn("Surface Branch Closeout", render_markdown(report))
        self.assertIn("MiniGPT surface branch closeout", render_html(report))


def reports_fixture() -> dict[str, dict[str, object]]:
    reports = {source_id: {"status": "pass", "decision": f"{source_id}_decision", "summary": {}} for source_id in SOURCE_FILENAMES}
    reports["surface_failure"]["summary"] = {"surface_failure_seeds": [2535]}
    reports["policy_replay"]["summary"] = {"stable_pair_full_policy_ids": ["pair_context_prefix"]}
    reports["leakage_risk"]["summary"] = {"risk_level": "medium"}
    reports["budget_sweep"]["summary"] = {"minimal_stable_budget": 8}
    reports["variant_replay"]["summary"] = {"stable_variant_ids": ["space_context_control"]}
    reports["baseline_contrast"]["summary"] = {"contextual_anchor_required": True}
    reports["route_decision"]["summary"] = {
        "current_route": "contextual_decode_aid_closeout",
        "recommended_next_route": "minimal_prompt_surface_objective",
    }
    return reports


if __name__ == "__main__":
    unittest.main()
