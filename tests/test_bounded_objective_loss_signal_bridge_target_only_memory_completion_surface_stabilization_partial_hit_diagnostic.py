from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
    build_completion_surface_stabilization_partial_hit_diagnostic,
    locate_completion_surface_stabilization_replay_comparison,
    locate_loss_suffix_replay_regression_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_artifacts import (
    render_completion_surface_stabilization_partial_hit_diagnostic_html,
    render_completion_surface_stabilization_partial_hit_diagnostic_markdown,
    render_completion_surface_stabilization_partial_hit_diagnostic_text,
    write_completion_surface_stabilization_partial_hit_diagnostic_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.diagnose_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit import (
    main as cli_main,
)


class CompletionSurfaceStabilizationPartialHitDiagnosticTests(unittest.TestCase):
    def test_diagnoses_stabilized_surface_suffix_gap(self) -> None:
        report = build_completion_surface_stabilization_partial_hit_diagnostic(replay_comparison(), regression_diagnostic())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilized_loss_suffix_missing")
        self.assertTrue(report["summary"]["completion_surface_stabilized"])
        self.assertTrue(report["summary"]["zero_hit_resolved"])
        self.assertTrue(report["summary"]["all_cases_fixed_l_partial"])
        self.assertEqual(report["summary"]["fixed_l_partial_case_count"], 3)
        self.assertEqual(report["summary"]["loss_hit_case_count"], 0)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "completion_surface_stabilized_suffix_missing")
        self.assertEqual(resolve_exit_code(report, require_diagnostic_ready=True), 0)

    def test_fails_when_loss_already_hit(self) -> None:
        replay = replay_comparison()
        replay["replay_rows"][0]["hit_terms"] = ["fixed", "loss"]
        replay["replay_rows"][0]["missed_terms"] = []
        replay["replay_rows"][0]["continuation"] = " fixed loss"
        report = build_completion_surface_stabilization_partial_hit_diagnostic(replay, regression_diagnostic())

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_fixed_l_partial", [issue["id"] for issue in report["issues"]])
        self.assertIn("loss_still_missing", [issue["id"] for issue in report["issues"]])

    def test_fails_when_zero_hit_not_resolved(self) -> None:
        replay = replay_comparison()
        replay["summary"]["zero_hit_case_count"] = 1
        report = build_completion_surface_stabilization_partial_hit_diagnostic(replay, regression_diagnostic())

        self.assertEqual(report["status"], "fail")
        self.assertIn("zero_hit_resolved", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_REPLAY_COMPARISON_JSON_FILENAME
            regression_path = root / "regression" / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            write_json_payload(regression_diagnostic(), regression_path)
            self.assertEqual(locate_completion_surface_stabilization_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_loss_suffix_replay_regression_diagnostic(regression_path.parent), regression_path)
            report = build_completion_surface_stabilization_partial_hit_diagnostic(replay_comparison(), regression_diagnostic())
            outputs = write_completion_surface_stabilization_partial_hit_diagnostic_outputs(report, root / "out")
            cli_main([
                "--replay-comparison",
                str(replay_path.parent),
                "--regression-diagnostic",
                str(regression_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--require-diagnostic-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME))
        self.assertIn("completion_surface_stabilization_partial_hit_diagnostic_ready=True", render_completion_surface_stabilization_partial_hit_diagnostic_text(report))
        self.assertIn("Case Diagnostics", render_completion_surface_stabilization_partial_hit_diagnostic_markdown(report))
        self.assertIn("Case Diagnostics", render_completion_surface_stabilization_partial_hit_diagnostic_html(report))


def replay_comparison() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "any_hit_case_count": 3,
            "zero_hit_case_count": 0,
        },
        "replay_rows": [
            row("canonical_direct_completion"),
            row("minimal_direct_completion"),
            row("completion_label_surface"),
        ],
    }


def regression_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "sample_contract_gap": True,
        },
        "regression": {
            "completion_surface_regressed_to_zero": True,
            "any_hit_delta": -1,
            "zero_hit_delta": 1,
        },
    }


def row(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "case_pass": False,
        "any_hit": True,
        "hit_terms": ["fixed"],
        "missed_terms": ["loss"],
        "continuation": " fixed l",
    }


if __name__ == "__main__":
    unittest.main()
