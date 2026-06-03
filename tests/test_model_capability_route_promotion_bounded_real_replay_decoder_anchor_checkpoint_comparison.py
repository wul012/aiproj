from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison,
    locate_decoder_anchor_training_run,
    locate_route_promotion_bounded_real_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_outputs,
)
from scripts.compare_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint import main as cli_main


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
        "summary": {
            "bounded_real_replay_executed": status == "pass",
            "model_route_quality_ready": status == "pass" and passed == case_count,
            "case_count": case_count,
            "passed_case_count": passed,
            "failed_case_count": case_count - passed,
            "pass_rate": round(passed / case_count, 4),
        },
        "replay_rows": rows,
    }


def training_report(*, ready: bool = True) -> dict:
    return {
        "status": "pass" if ready else "fail",
        "summary": {"decoder_anchor_training_ready": ready},
        "artifacts": [{"key": "checkpoint", "exists": ready, "path": "checkpoint.pt", "size": 10}],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorCheckpointComparisonTests(unittest.TestCase):
    def test_regression_from_baseline_and_no_recovery_blocks_promotion(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison(
            replay_report(passed=2),
            replay_report(passed=0),
            replay_report(passed=0),
            training_report(),
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_regressed_from_baseline")
        self.assertTrue(report["summary"]["bounded_decoder_anchor_checkpoint_comparison_ready"])
        self.assertTrue(report["summary"]["decoder_anchor_checkpoint_regressed_from_baseline"])
        self.assertFalse(report["summary"]["decoder_anchor_checkpoint_recovered_over_prompt"])
        self.assertEqual(report["summary"]["decoder_vs_baseline_passed_case_delta"], -2)
        self.assertEqual(report["summary"]["decoder_vs_prompt_passed_case_delta"], 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_comparison_ready=True, require_recovery=True), 1)

    def test_recovery_over_prompt_is_not_full_promotion(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison(
            replay_report(passed=2),
            replay_report(passed=0),
            replay_report(passed=1),
            training_report(),
        )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_partially_recovered")
        self.assertTrue(report["summary"]["decoder_anchor_checkpoint_recovered_over_prompt"])
        self.assertFalse(report["summary"]["promotion_ready"])

    def test_training_evidence_must_be_ready_when_provided(self) -> None:
        report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison(
            replay_report(passed=1),
            replay_report(passed=1),
            replay_report(passed=1),
            training_report(ready=False),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("decoder_anchor_training_ready_when_provided", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline = replay_report(passed=2)
            prompt = replay_report(passed=0)
            decoder = replay_report(passed=0)
            training = training_report()
            baseline_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(baseline, root / "baseline")
            prompt_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(prompt, root / "prompt")
            decoder_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(decoder, root / "decoder")
            training_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run_outputs(training, root / "training")
            self.assertEqual(locate_route_promotion_bounded_real_replay(Path(baseline_outputs["json"]).parent), Path(baseline_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_training_run(Path(training_outputs["json"]).parent), Path(training_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison(baseline, prompt, decoder, training)
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_outputs(report, root / "comparison")
            cli_main(
                [
                    "--baseline-replay",
                    str(Path(baseline_outputs["json"]).parent),
                    "--prompt-aligned-replay",
                    str(Path(prompt_outputs["json"]).parent),
                    "--decoder-anchor-replay",
                    str(Path(decoder_outputs["json"]).parent),
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
                        "--prompt-aligned-replay",
                        str(Path(prompt_outputs["json"]).parent),
                        "--decoder-anchor-replay",
                        str(Path(decoder_outputs["json"]).parent),
                        "--out-dir",
                        str(root / "cli-comparison-fail"),
                        "--require-comparison-pass",
                        "--require-recovery",
                        "--force",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("decoder_anchor_checkpoint_regressed_from_baseline=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_text(report))
        self.assertIn("Case Comparison", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_markdown(report))
        self.assertIn("Decoder passed", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_checkpoint_comparison_html(report))

    def test_cli_force_preserves_nested_decoder_replay_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "comparison"
            baseline_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(passed=2), root / "baseline")
            prompt_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(passed=0), root / "prompt")
            decoder_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(passed=0), out_dir / "decoder-anchor-replay")
            (out_dir / "stale.txt").write_text("stale", encoding="utf-8")
            cli_main(
                [
                    "--baseline-replay",
                    str(Path(baseline_outputs["json"]).parent),
                    "--prompt-aligned-replay",
                    str(Path(prompt_outputs["json"]).parent),
                    "--decoder-anchor-replay",
                    str(Path(decoder_outputs["json"]).parent),
                    "--out-dir",
                    str(out_dir),
                    "--require-comparison-pass",
                    "--force",
                ]
            )
            self.assertTrue(Path(decoder_outputs["json"]).is_file())
            self.assertFalse((out_dir / "stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
