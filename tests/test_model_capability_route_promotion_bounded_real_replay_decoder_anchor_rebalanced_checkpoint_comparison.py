from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison,
    locate_rebalanced_training_run,
    locate_route_promotion_bounded_real_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from scripts.compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint import main as cli_main


class RebalancedCheckpointComparisonTests(unittest.TestCase):
    def test_comparison_marks_rebalanced_still_regressed_from_baseline(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison(
            replay(2),
            replay(0),
            replay(0),
            replay(0),
            training(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_still_regressed_from_baseline")
        self.assertEqual(report["summary"]["rebalanced_vs_baseline_pass_rate_delta"], -0.4)
        self.assertFalse(report["summary"]["rebalanced_checkpoint_improved_over_baseline"])
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_improvement=False), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_improvement=True), 1)

    def test_comparison_can_report_partial_recovery_over_decoder_anchor(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison(
            replay(2),
            replay(0),
            replay(0),
            replay(1),
            training(),
        )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_partial_recovery")
        self.assertTrue(report["summary"]["rebalanced_checkpoint_recovered_over_decoder_anchor"])
        self.assertFalse(report["summary"]["rebalanced_checkpoint_improved_over_baseline"])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = write_model_capability_route_promotion_bounded_real_replay_outputs(replay(2), root / "baseline")
            prompt = write_model_capability_route_promotion_bounded_real_replay_outputs(replay(0), root / "prompt")
            decoder = write_model_capability_route_promotion_bounded_real_replay_outputs(replay(0), root / "decoder")
            rebalanced = write_model_capability_route_promotion_bounded_real_replay_outputs(replay(0), root / "comparison" / "rebalanced-replay")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run_outputs(training(), root / "training")
            self.assertEqual(locate_route_promotion_bounded_real_replay(Path(rebalanced["json"]).parent), Path(rebalanced["json"]))
            self.assertEqual(locate_rebalanced_training_run(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison(replay(2), replay(0), replay(0), replay(0), training())
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_outputs(report, root / "out")
            cli_main(
                [
                    "--baseline-replay",
                    str(Path(baseline["json"]).parent),
                    "--prompt-aligned-replay",
                    str(Path(prompt["json"]).parent),
                    "--decoder-anchor-replay",
                    str(Path(decoder["json"]).parent),
                    "--rebalanced-replay",
                    str(Path(rebalanced["json"]).parent),
                    "--rebalanced-training",
                    str(Path(training_outputs["json"]).parent),
                    "--out-dir",
                    str(root / "comparison"),
                    "--require-comparison-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("rebalanced_passed_case_count=0", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_text(report))
        self.assertIn("Routes", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_markdown(report))
        self.assertIn("Rebalanced pass", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison_html(report))


def replay(passed: int) -> dict:
    case_count = 5
    return {
        "status": "pass",
        "summary": {
            "bounded_real_replay_executed": True,
            "model_route_quality_ready": passed == case_count,
            "case_count": case_count,
            "passed_case_count": passed,
            "failed_case_count": case_count - passed,
            "pass_rate": round(passed / case_count, 4),
        },
    }


def training() -> dict:
    return {
        "status": "pass",
        "summary": {
            "decoder_anchor_rebalanced_training_ready": True,
            "final_val_loss": 4.19,
        },
        "artifacts": [],
    }


if __name__ == "__main__":
    unittest.main()
