from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_required_term_pair_readiness_heldout_failure_diagnostic import (
    build_pair_readiness_heldout_failure_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_heldout_failure_diagnostic_artifacts import (
    render_pair_readiness_heldout_failure_diagnostic_html,
    render_pair_readiness_heldout_failure_diagnostic_markdown,
    render_pair_readiness_heldout_failure_diagnostic_text,
    write_pair_readiness_heldout_failure_diagnostic_outputs,
)


class PairReadinessHeldoutFailureDiagnosticTests(unittest.TestCase):
    def test_diagnostic_identifies_loss_prompt_fixed_pollution(self) -> None:
        report = build_pair_readiness_heldout_failure_diagnostic(training_fixture())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "pair_readiness_loss_prompt_absorbed_by_fixed")
        self.assertEqual(report["summary"]["dominant_failure"], "loss_prompt_absorbed_by_fixed")
        self.assertEqual(report["summary"]["fixed_hit_count"], 1)
        self.assertEqual(report["summary"]["loss_hit_count"], 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_diagnostic_blocks_failed_replay(self) -> None:
        source = training_fixture()
        source["replay_report"]["status"] = "fail"
        report = build_pair_readiness_heldout_failure_diagnostic(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_report_not_pass", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_render_all_formats(self) -> None:
        report = build_pair_readiness_heldout_failure_diagnostic(training_fixture())
        with tempfile.TemporaryDirectory() as tmp:
            outputs = write_pair_readiness_heldout_failure_diagnostic_outputs(report, Path(tmp) / "diagnostic")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("dominant_failure=loss_prompt_absorbed_by_fixed", render_pair_readiness_heldout_failure_diagnostic_text(report))
        self.assertIn("Heldout Failure Diagnostic", render_pair_readiness_heldout_failure_diagnostic_markdown(report))
        self.assertIn("MiniGPT pair-readiness heldout failure diagnostic", render_pair_readiness_heldout_failure_diagnostic_html(report))


def training_fixture() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "pair_readiness_training_no_pair_full",
        "summary": {"training_status": "pass", "pair_full_observed": False},
        "replay_report": {
            "status": "pass",
            "case_rows": [
                {
                    "profile_id": "default",
                    "term": "fixed",
                    "prompt": "fixed=",
                    "generated": "fixed=fixed",
                    "continuation": "fixed",
                    "continuation_hit": True,
                },
                {
                    "profile_id": "default",
                    "term": "loss",
                    "prompt": "loss=",
                    "generated": "loss=fixed",
                    "continuation": "fixed",
                    "continuation_hit": False,
                },
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
