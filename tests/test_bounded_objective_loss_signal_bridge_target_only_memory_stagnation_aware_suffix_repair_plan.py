from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic import (
    TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME,
    build_stagnation_aware_suffix_repair_plan,
    locate_stagnation_diagnostic,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_artifacts import (
    render_stagnation_aware_suffix_repair_plan_html,
    render_stagnation_aware_suffix_repair_plan_markdown,
    render_stagnation_aware_suffix_repair_plan_text,
    write_stagnation_aware_suffix_repair_plan_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (
    main as cli_main,
)


class StagnationAwareSuffixRepairPlanTests(unittest.TestCase):
    def test_builds_plan_from_no_contract_gain_diagnostic(self) -> None:
        report = build_stagnation_aware_suffix_repair_plan(stagnation_diagnostic())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready"])
        self.assertEqual(report["summary"]["action_count"], 5)
        self.assertEqual(report["summary"]["required_action_count"], 5)
        self.assertEqual(report["summary"]["suffix_position_action_count"], 1)
        self.assertEqual(report["summary"]["surface_format_action_count"], 1)
        self.assertEqual(report["summary"]["replay_prompt_boundary_action_count"], 1)
        self.assertEqual(report["summary"]["training_corpus_ratio_action_count"], 1)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "repair_plan_only")
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 0)

    def test_fails_without_no_contract_gain(self) -> None:
        diagnostic = stagnation_diagnostic()
        diagnostic["summary"]["no_contract_gain_confirmed"] = False
        report = build_stagnation_aware_suffix_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("no_contract_gain", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_plan_ready=True), 1)

    def test_fails_when_loss_was_newly_hit(self) -> None:
        diagnostic = stagnation_diagnostic()
        diagnostic["summary"]["loss_newly_hit_case_count"] = 1
        report = build_stagnation_aware_suffix_repair_plan(diagnostic)

        self.assertEqual(report["status"], "fail")
        self.assertIn("loss_not_newly_hit", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostic_path = root / "diagnostic" / TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_STAGNATION_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(stagnation_diagnostic(), diagnostic_path)
            self.assertEqual(locate_stagnation_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_stagnation_aware_suffix_repair_plan(stagnation_diagnostic(), stagnation_diagnostic_path=diagnostic_path)
            outputs = write_stagnation_aware_suffix_repair_plan_outputs(report, root / "out")
            cli_main([
                "--stagnation-diagnostic",
                str(diagnostic_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--require-plan-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME))
        self.assertIn("stagnation_aware_suffix_repair_plan_ready=True", render_stagnation_aware_suffix_repair_plan_text(report))
        self.assertIn("Plan Actions", render_stagnation_aware_suffix_repair_plan_markdown(report))
        self.assertIn("Plan Actions", render_stagnation_aware_suffix_repair_plan_html(report))


def stagnation_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_ready": True,
            "no_contract_gain_confirmed": True,
            "surface_format_changed_without_suffix_gain": True,
            "continuation_changed_count": 2,
            "loss_newly_hit_case_count": 0,
            "pass_delta": 0,
        },
        "diagnostic": {
            "next_step": "build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan",
        },
        "case_diagnostics": [
            {"case_id": "canonical_direct_completion"},
            {"case_id": "minimal_direct_completion"},
            {"case_id": "completion_label_surface"},
        ],
    }


if __name__ == "__main__":
    unittest.main()
