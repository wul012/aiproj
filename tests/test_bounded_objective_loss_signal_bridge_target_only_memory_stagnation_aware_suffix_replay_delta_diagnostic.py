from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME,
    build_stagnation_aware_suffix_replay_delta_diagnostic,
    locate_stabilized_loss_suffix_uptake_replay_comparison,
    locate_stagnation_aware_suffix_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_artifacts import (
    render_stagnation_aware_suffix_replay_delta_diagnostic_html,
    render_stagnation_aware_suffix_replay_delta_diagnostic_markdown,
    render_stagnation_aware_suffix_replay_delta_diagnostic_text,
    write_stagnation_aware_suffix_replay_delta_diagnostic_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta import (
    main as cli_main,
)


class StagnationAwareSuffixReplayDeltaDiagnosticTests(unittest.TestCase):
    def test_diagnoses_newline_fixed_l_convergence_without_loss_gain(self) -> None:
        report = build_stagnation_aware_suffix_replay_delta_diagnostic(baseline_replay(), current_replay())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["decision"],
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_newline_fixed_l_converged_without_loss_gain",
        )
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready"])
        self.assertTrue(report["summary"]["no_contract_gain_confirmed"])
        self.assertTrue(report["summary"]["surface_converged_without_suffix_gain"])
        self.assertEqual(report["summary"]["pass_delta"], 0)
        self.assertEqual(report["summary"]["any_hit_delta"], 0)
        self.assertEqual(report["summary"]["zero_hit_delta"], 0)
        self.assertEqual(report["summary"]["continuation_changed_count"], 1)
        self.assertEqual(report["summary"]["space_to_newline_fixed_l_case_count"], 1)
        self.assertEqual(report["summary"]["loss_newly_hit_case_count"], 0)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "newline_fixed_l_surface_convergence_without_loss_gain")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_fails_when_loss_is_newly_hit(self) -> None:
        current = current_replay()
        current["replay_rows"][0]["continuation"] = "\nfixed loss"
        current["replay_rows"][0]["hit_terms"] = ["fixed", "loss"]
        current["replay_rows"][0]["missed_terms"] = []
        report = build_stagnation_aware_suffix_replay_delta_diagnostic(baseline_replay(), current)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_loss_newly_hit", [issue["id"] for issue in report["issues"]])
        self.assertIn("all_current_newline_fixed_l_partial", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_fails_when_case_set_changes(self) -> None:
        current = current_replay()
        current["replay_rows"] = current["replay_rows"][:-1]
        report = build_stagnation_aware_suffix_replay_delta_diagnostic(baseline_replay(), current)

        self.assertEqual(report["status"], "fail")
        self.assertIn("matching_case_set", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline" / TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_REPLAY_COMPARISON_JSON_FILENAME
            current_path = root / "current" / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(baseline_replay(), baseline_path)
            write_json_payload(current_replay(), current_path)
            self.assertEqual(locate_stabilized_loss_suffix_uptake_replay_comparison(baseline_path.parent), baseline_path)
            self.assertEqual(locate_stagnation_aware_suffix_replay_comparison(current_path.parent), current_path)
            report = build_stagnation_aware_suffix_replay_delta_diagnostic(baseline_replay(), current_replay())
            outputs = write_stagnation_aware_suffix_replay_delta_diagnostic_outputs(report, root / "out")
            cli_main([
                "--baseline-replay-comparison",
                str(baseline_path.parent),
                "--current-replay-comparison",
                str(current_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--require-diagnostic-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("stagnation_aware_suffix_replay_delta_diagnostic_ready=True", render_stagnation_aware_suffix_replay_delta_diagnostic_text(report))
        self.assertIn("Case Deltas", render_stagnation_aware_suffix_replay_delta_diagnostic_markdown(report))
        self.assertIn("Case Deltas", render_stagnation_aware_suffix_replay_delta_diagnostic_html(report))


def baseline_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 3,
            "zero_hit_case_count": 0,
        },
        "replay_rows": [
            row("canonical_direct_completion", " fixed l"),
            row("completion_label_surface", "\nfixed l"),
            row("minimal_direct_completion", "\nfixed l"),
        ],
    }


def current_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 3,
            "zero_hit_case_count": 0,
        },
        "replay_rows": [
            row("canonical_direct_completion", "\nfixed l"),
            row("completion_label_surface", "\nfixed l"),
            row("minimal_direct_completion", "\nfixed l"),
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
    }


if __name__ == "__main__":
    unittest.main()
