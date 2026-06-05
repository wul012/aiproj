from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic import (
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_single_line_surface_zero_hit_diagnostic,
    locate_single_line_surface_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_artifacts import (
    render_single_line_surface_zero_hit_diagnostic_html,
    render_single_line_surface_zero_hit_diagnostic_markdown,
    render_single_line_surface_zero_hit_diagnostic_text,
    write_single_line_surface_zero_hit_diagnostic_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_single_line_surface_zero_hit import main as cli_main


class SingleLineSurfaceZeroHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_persisted_label_echo_after_loss_improvement(self) -> None:
        report = build_single_line_surface_zero_hit_diagnostic(replay_comparison())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_label_echo_persisted")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready"])
        self.assertEqual(report["summary"]["exact_label_echo_case_count"], 2)
        self.assertEqual(report["summary"]["label_prefix_fragment_case_count"], 1)
        self.assertTrue(report["summary"]["loss_improved_without_required_term_uptake"])
        self.assertIn("loss_improved_without_required_term_uptake", report["diagnostic"]["root_cause_ids"])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_fails_when_replay_is_not_zero_hit(self) -> None:
        replay = replay_comparison()
        replay["summary"]["any_hit_case_count"] = 1
        report = build_single_line_surface_zero_hit_diagnostic(replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("zero_hit_replay", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_single_line_surface_replay_comparison(replay_path.parent), replay_path)
            report = build_single_line_surface_zero_hit_diagnostic(replay_comparison(), replay_comparison_path=replay_path)
            outputs = write_single_line_surface_zero_hit_diagnostic_outputs(report, root / "out")
            cli_main(["--replay-comparison", str(replay_path.parent), "--out-dir", str(root / "cli-out"), "--require-diagnostic-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("zero_hit_diagnostic_ready=True", render_single_line_surface_zero_hit_diagnostic_text(report))
        self.assertIn("Case Diagnostics", render_single_line_surface_zero_hit_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_single_line_surface_zero_hit_diagnostic_html(report))


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "any_hit_case_count": 0,
            "zero_hit_case_count": 3,
        },
        "single_line_surface_training_summary": {
            "train_loss_delta": -2.37,
            "decoder_anchor_example_count": 0,
        },
        "replay_rows": [
            {"case_id": "canonical_direct_completion", "continuation": "\nanswer:", "case_pass": False, "any_hit": False, "hit_terms": [], "missed_terms": ["fixed", "loss"]},
            {"case_id": "minimal_direct_completion", "continuation": "\nanswer:", "case_pass": False, "any_hit": False, "hit_terms": [], "missed_terms": ["fixed", "loss"]},
            {"case_id": "completion_label_surface", "continuation": "\nansweti", "case_pass": False, "any_hit": False, "hit_terms": [], "missed_terms": ["fixed", "loss"]},
        ],
    }


if __name__ == "__main__":
    unittest.main()
