from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
    build_loss_suffix_replay_regression_diagnostic,
    locate_baseline_target_only_memory_replay_comparison,
    locate_current_loss_suffix_replay_comparison,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_artifacts import (
    render_loss_suffix_replay_regression_diagnostic_html,
    render_loss_suffix_replay_regression_diagnostic_markdown,
    render_loss_suffix_replay_regression_diagnostic_text,
    write_loss_suffix_replay_regression_diagnostic_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression import (
    main as cli_main,
)


class LossSuffixReplayRegressionDiagnosticTests(unittest.TestCase):
    def test_diagnoses_sample_success_contract_regression(self) -> None:
        report = build_loss_suffix_replay_regression_diagnostic(current_replay(), baseline_replay(), sample_text())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_sample_success_contract_regression")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready"])
        self.assertTrue(report["summary"]["sample_contract_gap"])
        self.assertFalse(report["summary"]["objective_contract_recovered"])
        self.assertEqual(report["summary"]["any_hit_delta"], -1)
        self.assertEqual(report["summary"]["zero_hit_delta"], 1)
        self.assertTrue(report["summary"]["completion_surface_regressed_to_zero"])
        self.assertEqual(report["summary"]["fixed_l_partial_case_count"], 2)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "sample_success_contract_regression")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_fails_when_sample_does_not_show_fixed_loss(self) -> None:
        report = build_loss_suffix_replay_regression_diagnostic(current_replay(), baseline_replay(), "fixed")

        self.assertEqual(report["status"], "fail")
        self.assertIn("sample_contains_fixed_loss", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 1)

    def test_fails_when_replay_signal_does_not_regress(self) -> None:
        current = current_replay()
        current["summary"]["any_hit_case_count"] = 3
        current["summary"]["zero_hit_case_count"] = 0
        current["replay_rows"][2]["any_hit"] = True
        current["replay_rows"][2]["hit_terms"] = ["fixed"]
        current["replay_rows"][2]["missed_terms"] = ["loss"]
        report = build_loss_suffix_replay_regression_diagnostic(current, baseline_replay(), sample_text())

        self.assertEqual(report["status"], "fail")
        self.assertIn("replay_signal_regressed", [issue["id"] for issue in report["issues"]])
        self.assertIn("completion_surface_regressed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_path = root / "current" / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME
            baseline_path = root / "baseline" / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
            sample_path = root / "sample.txt"
            write_json_payload(current_replay(), current_path)
            write_json_payload(baseline_replay(), baseline_path)
            sample_path.write_text(sample_text(), encoding="utf-8")
            self.assertEqual(locate_current_loss_suffix_replay_comparison(current_path.parent), current_path)
            self.assertEqual(locate_baseline_target_only_memory_replay_comparison(baseline_path.parent), baseline_path)
            report = build_loss_suffix_replay_regression_diagnostic(current_replay(), baseline_replay(), sample_text())
            outputs = write_loss_suffix_replay_regression_diagnostic_outputs(report, root / "out")
            cli_main([
                "--current-replay-comparison",
                str(current_path.parent),
                "--baseline-replay-comparison",
                str(baseline_path.parent),
                "--sample",
                str(sample_path),
                "--out-dir",
                str(root / "cli-out"),
                "--require-diagnostic-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("any_hit_delta=-1", render_loss_suffix_replay_regression_diagnostic_text(report))
        self.assertIn("completion_surface_regressed_to_zero", render_loss_suffix_replay_regression_diagnostic_markdown(report))
        self.assertIn("Regression Summary", render_loss_suffix_replay_regression_diagnostic_html(report))


def sample_text() -> str:
    return "Answer with exactly two tokens: fixed loss answer: fixed loss"


def baseline_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 3,
            "zero_hit_case_count": 0,
        },
        "replay_rows": [
            row("canonical_direct_completion", "\nfixed l", ["fixed"], ["loss"], True),
            row("minimal_direct_completion", "\nfixed l", ["fixed"], ["loss"], True),
            row("completion_label_surface", " fixed l", ["fixed"], ["loss"], True),
        ],
    }


def current_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "passed_case_count": 0,
            "any_hit_case_count": 2,
            "zero_hit_case_count": 1,
        },
        "replay_rows": [
            row("canonical_direct_completion", "\nfixed l", ["fixed"], ["loss"], True),
            row("minimal_direct_completion", "\nfixed l", ["fixed"], ["loss"], True),
            row("completion_label_surface", "\nan: fix", [], ["fixed", "loss"], False),
        ],
    }


def row(case_id: str, continuation: str, hit_terms: list[str], missed_terms: list[str], any_hit: bool) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_pass": False,
        "any_hit": any_hit,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "continuation": continuation,
        "max_new_tokens": 8,
    }


if __name__ == "__main__":
    unittest.main()
