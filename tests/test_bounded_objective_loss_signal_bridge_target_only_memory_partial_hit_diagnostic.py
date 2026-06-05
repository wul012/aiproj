from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_target_only_memory_partial_hit_diagnostic,
    locate_target_only_memory_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_artifacts import (
    render_target_only_memory_partial_hit_diagnostic_html,
    render_target_only_memory_partial_hit_diagnostic_markdown,
    render_target_only_memory_partial_hit_diagnostic_text,
    write_target_only_memory_partial_hit_diagnostic_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_target_only_memory_partial_hit import main as cli_main


class TargetOnlyMemoryPartialHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_loss_suffix_gap(self) -> None:
        report = build_target_only_memory_partial_hit_diagnostic(replay_comparison())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_loss_suffix_gap")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready"])
        self.assertEqual(report["summary"]["partial_case_count"], 3)
        self.assertEqual(report["summary"]["fixed_without_loss_case_count"], 3)
        self.assertEqual(report["summary"]["loss_prefix_case_count"], 3)
        self.assertEqual(report["summary"]["loss_hit_case_count"], 0)
        self.assertTrue(report["summary"]["all_cases_loss_prefix"])
        self.assertIn("loss_suffix_uptake_gap", report["diagnostic"]["root_cause_ids"])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_diagnostic_fails_without_partial_hit(self) -> None:
        replay = replay_comparison()
        replay["summary"]["any_hit_case_count"] = 0
        replay["replay_rows"] = []
        report = build_target_only_memory_partial_hit_diagnostic(replay)

        self.assertEqual(report["status"], "fail")
        self.assertIn("has_partial_hits", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            self.assertEqual(locate_target_only_memory_replay_comparison(replay_path.parent), replay_path)
            report = build_target_only_memory_partial_hit_diagnostic(replay_comparison(), replay_comparison_path=replay_path)
            outputs = write_target_only_memory_partial_hit_diagnostic_outputs(report, root / "out")
            cli_main([
                "--replay-comparison",
                str(replay_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--require-diagnostic-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("loss_prefix_case_count=3", render_target_only_memory_partial_hit_diagnostic_text(report))
        self.assertIn("loss_suffix_uptake_gap", render_target_only_memory_partial_hit_diagnostic_markdown(report))
        self.assertIn("Case Diagnostics", render_target_only_memory_partial_hit_diagnostic_html(report))


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 3,
            "zero_hit_case_count": 0,
        },
        "target_only_memory_training_summary": {
            "decoder_anchor_example_count": 0,
        },
        "replay_rows": [
            row("canonical_direct_completion", "\nfixed l"),
            row("minimal_direct_completion", "\nfixed l"),
            row("completion_label_surface", "fixed l"),
        ],
    }


def row(case_id: str, continuation: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_pass": False,
        "any_hit": True,
        "hit_terms": ["fixed"],
        "missed_terms": ["loss"],
        "continuation": continuation,
        "max_new_tokens": 12,
    }


if __name__ == "__main__":
    unittest.main()
