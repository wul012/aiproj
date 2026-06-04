from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_partial_hit_diagnostic import (
    LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic,
    locate_loss_signal_bridge_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_partial_hit_diagnostic_artifacts import (
    render_loss_signal_bridge_partial_hit_diagnostic_html,
    render_loss_signal_bridge_partial_hit_diagnostic_markdown,
    render_loss_signal_bridge_partial_hit_diagnostic_text,
    write_loss_signal_bridge_partial_hit_diagnostic_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_partial_hit import main as cli_main


class BoundedObjectiveLossSignalBridgePartialHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_pair_binding_gap(self) -> None:
        report = build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic(replay_comparison())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_partial_hit_pair_binding_gap")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready"])
        self.assertTrue(report["summary"]["paired_signal_split"])
        self.assertEqual(report["summary"]["fixed_only_case_count"], 1)
        self.assertEqual(report["summary"]["loss_only_case_count"], 1)
        self.assertIn("paired_term_binding_gap", report["diagnostic"]["root_cause_ids"])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_without_partial_hit(self) -> None:
        replay = replay_comparison()
        replay["summary"]["any_hit_case_count"] = 0
        replay["replay_rows"] = []
        report = build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic(replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("has_partial_hits", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_loss_signal_bridge_replay_comparison(replay_path.parent), replay_path)
            report = build_bounded_objective_loss_signal_bridge_partial_hit_diagnostic(replay_comparison(), replay_comparison_path=replay_path)
            outputs = write_loss_signal_bridge_partial_hit_diagnostic_outputs(report, root / "out")
            cli_main(["--replay-comparison", str(replay_path.parent), "--out-dir", str(root / "cli-out"), "--require-diagnostic-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("partial_hit_diagnostic_ready=True", render_loss_signal_bridge_partial_hit_diagnostic_text(report))
        self.assertIn("Case Diagnostics", render_loss_signal_bridge_partial_hit_diagnostic_markdown(report))
        self.assertIn("Root Causes", render_loss_signal_bridge_partial_hit_diagnostic_html(report))


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 2,
            "zero_hit_case_count": 1,
        },
        "loss_signal_bridge_training_summary": {
            "bounded_objective_loss_signal_bridge_training_ready": True,
            "decoder_anchor_example_count": 0,
        },
        "replay_rows": [
            {
                "case_id": "canonical_direct_completion",
                "continuation": " lossswe",
                "hit_terms": ["loss"],
                "missed_terms": ["fixed"],
                "case_pass": False,
                "any_hit": True,
                "max_new_tokens": 8,
            },
            {
                "case_id": "minimal_direct_completion",
                "continuation": "\nfixed l",
                "hit_terms": ["fixed"],
                "missed_terms": ["loss"],
                "case_pass": False,
                "any_hit": True,
                "max_new_tokens": 8,
            },
            {
                "case_id": "completion_label_surface",
                "continuation": " lonssss",
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "any_hit": False,
                "max_new_tokens": 8,
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
