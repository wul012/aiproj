from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_split_plan import (
    build_pair_readiness_split_plan,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_split_plan_artifacts import (
    render_pair_readiness_split_plan_html,
    render_pair_readiness_split_plan_markdown,
    render_pair_readiness_split_plan_text,
    write_pair_readiness_split_plan_outputs,
)


class PairReadinessSplitPlanTests(unittest.TestCase):
    def test_split_plan_ready_from_minimal_prompt_closeout(self) -> None:
        report = build_pair_readiness_split_plan(closeout_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_split_plan_ready")
        self.assertTrue(report["summary"]["plan_ready"])
        self.assertEqual(report["summary"]["proposed_next_artifact"], "pair_readiness_split_contract")
        self.assertEqual(report["interpretation"]["model_quality_claim"], "plan_only")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_split_plan_blocks_pair_full_closeout(self) -> None:
        closeout = closeout_fixture()
        closeout["summary"]["pair_full_report_count"] = 1
        report = build_pair_readiness_split_plan(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_pair_full", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_split_plan_requires_mixed_failures(self) -> None:
        closeout = closeout_fixture()
        closeout["summary"]["fixed_only_report_count"] = 0
        report = build_pair_readiness_split_plan(closeout)

        self.assertEqual(report["status"], "fail")
        self.assertIn("mixed_failures", [issue["id"] for issue in report["issues"]])

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_readiness_split_plan(closeout_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_readiness_split_plan_outputs(report, Path(tmp) / "plan")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decision=pair_readiness_split_plan_ready", render_pair_readiness_split_plan_text(report))
        self.assertIn("Pair-Readiness Split Plan", render_pair_readiness_split_plan_markdown(report))
        self.assertIn("MiniGPT pair-readiness split plan", render_pair_readiness_split_plan_html(report))


def closeout_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "minimal_prompt_batch_closed_without_pair_full",
        "summary": {
            "report_count": 3,
            "pair_full_report_count": 0,
            "fixed_only_report_count": 1,
            "loss_only_report_count": 2,
        },
    }


if __name__ == "__main__":
    unittest.main()
