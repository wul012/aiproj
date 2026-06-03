from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import (
    build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison,
    locate_repair_training_run,
    locate_route_promotion_bounded_real_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_html,
    render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_markdown,
    render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_text,
    write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs,
)
from scripts.compare_model_capability_route_promotion_bounded_real_replay_repair_checkpoint import main as cli_main


def replay_report(*, passed: int, case_count: int = 3, status: str = "pass") -> dict:
    rows = []
    for index in range(case_count):
        is_pass = index < passed
        rows.append(
            {
                "case_id": f"case-{index + 1}",
                "case_pass": is_pass,
                "hit_terms": ["fixed", "loss"] if is_pass else ["fixed"],
                "missed_terms": [] if is_pass else ["loss"],
                "continuation": "fixed loss" if is_pass else "fixed only",
            }
        )
    return {
        "status": status,
        "decision": "model_capability_route_promotion_bounded_real_replay_passed" if passed == case_count else "model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps",
        "summary": {
            "bounded_real_replay_executed": status == "pass",
            "model_route_quality_ready": status == "pass" and passed == case_count,
            "case_count": case_count,
            "executed_case_count": case_count,
            "passed_case_count": passed,
            "failed_case_count": case_count - passed,
            "pass_rate": round(passed / case_count, 4),
        },
        "replay_rows": rows,
    }


def training_report(*, ready: bool = True) -> dict:
    return {
        "status": "pass" if ready else "fail",
        "summary": {"bounded_real_replay_repair_training_ready": ready},
        "artifacts": [{"key": "checkpoint", "exists": ready, "path": "checkpoint.pt", "size": 10}],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayRepairCheckpointComparisonTests(unittest.TestCase):
    def test_regression_is_valid_comparison_but_blocks_improvement(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
            replay_report(passed=2),
            replay_report(passed=0),
            training_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_regressed")
        self.assertTrue(report["summary"]["bounded_repair_checkpoint_comparison_ready"])
        self.assertTrue(report["summary"]["repair_checkpoint_regressed"])
        self.assertEqual(report["summary"]["passed_case_delta"], -2)
        self.assertEqual(report["summary"]["pass_rate_delta"], -0.6667)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_improvement=True), 1)

    def test_improved_repair_checkpoint_can_satisfy_improvement_gate(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
            replay_report(passed=1),
            replay_report(passed=3),
            training_report(),
        )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_repair_checkpoint_improved_ready_for_review")
        self.assertTrue(report["summary"]["repair_checkpoint_improved"])
        self.assertTrue(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_improvement=True), 0)

    def test_source_failure_makes_comparison_fail(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(
            replay_report(passed=1, status="fail"),
            replay_report(passed=2),
            training_report(),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("baseline_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = replay_report(passed=2)
            repair = replay_report(passed=0)
            training = training_report()
            baseline_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(baseline, root / "baseline")
            repair_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(repair, root / "repair")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_repair_training_run_outputs(training, root / "training")
            self.assertEqual(locate_route_promotion_bounded_real_replay(Path(baseline_outputs["json"]).parent), Path(baseline_outputs["json"]))
            self.assertEqual(locate_repair_training_run(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison(baseline, repair, training)
            outputs = write_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_outputs(report, root / "comparison")
            cli_main(
                [
                    "--baseline-replay",
                    str(Path(baseline_outputs["json"]).parent),
                    "--repair-replay",
                    str(Path(repair_outputs["json"]).parent),
                    "--training-evidence",
                    str(Path(training_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "cli-comparison"),
                    "--require-comparison-pass",
                    "--force",
                ]
            )
            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "--baseline-replay",
                        str(Path(baseline_outputs["json"]).parent),
                        "--repair-replay",
                        str(Path(repair_outputs["json"]).parent),
                        "--out-dir",
                        str(root / "cli-comparison-fail"),
                        "--require-comparison-pass",
                        "--require-improvement",
                        "--force",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("repair_checkpoint_regressed=True", render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_text(report))
        self.assertIn("Case Comparison", render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_markdown(report))
        self.assertIn("Repair passed", render_model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison_html(report))


if __name__ == "__main__":
    unittest.main()
