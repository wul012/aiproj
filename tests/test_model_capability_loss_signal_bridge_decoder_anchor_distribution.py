from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.history import TrainingRecord, append_record
from minigpt.model_capability_loss_signal_bridge_decoder_anchor_distribution import (
    LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM,
    build_loss_signal_bridge_decoder_anchor_distribution,
    materialize_loss_signal_bridge_inputs,
    read_json_report,
    resolve_exit_code,
    write_loss_signal_bridge_decoder_anchor_distribution_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145 import main as cli_main


class ModelCapabilityLossSignalBridgeDecoderAnchorDistributionTests(unittest.TestCase):
    def test_builds_ready_loss_signal_and_distribution_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = materialize_loss_signal_bridge_inputs(root / "inputs")
            training_run = write_training_run(root / "training")
            report = build_loss_signal_bridge_decoder_anchor_distribution(
                holdout_scorecard_report(),
                read_json_report(inputs["seed_revision"]),
                read_json_report(inputs["failure_diagnostic"]),
                corpus_path=inputs["corpus"],
                training_run_dir=training_run,
                distribution_out_dir=root / "distribution",
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_loss_signal_bridge_decoder_anchor_distribution_ready")
        self.assertTrue(report["summary"]["loss_signal_bridge_decoder_anchor_distribution_ready"])
        self.assertTrue(report["summary"]["loss_signal_ready"])
        self.assertLess(report["summary"]["train_loss_delta"], 0)
        self.assertFalse(report["summary"]["rebalanced_seed_needed"])
        self.assertEqual(report["summary"]["model_quality_claim"], "loss_signal_bridge_and_decoder_anchor_distribution_real_execution")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_fails_when_train_loss_does_not_decrease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = materialize_loss_signal_bridge_inputs(root / "inputs")
            training_run = write_training_run(root / "training", train_losses=(1.0, 1.1))
            report = build_loss_signal_bridge_decoder_anchor_distribution(
                holdout_scorecard_report(),
                read_json_report(inputs["seed_revision"]),
                read_json_report(inputs["failure_diagnostic"]),
                corpus_path=inputs["corpus"],
                training_run_dir=training_run,
                distribution_out_dir=root / "distribution",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("train_loss_decreased", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_fails_when_v1144_prerequisite_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs = materialize_loss_signal_bridge_inputs(root / "inputs")
            training_run = write_training_run(root / "training")
            source = holdout_scorecard_report()
            source["summary"]["holdout_scorecard_smoke_ready"] = False
            report = build_loss_signal_bridge_decoder_anchor_distribution(
                source,
                read_json_report(inputs["seed_revision"]),
                read_json_report(inputs["failure_diagnostic"]),
                corpus_path=inputs["corpus"],
                training_run_dir=training_run,
                distribution_out_dir=root / "distribution",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("v1144_holdout_scorecard_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired_with_reused_training_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            holdout_path = root / "holdout.json"
            write_json_payload(holdout_scorecard_report(), holdout_path)
            inputs = materialize_loss_signal_bridge_inputs(root / "inputs")
            training_run = write_training_run(root / "training")
            report = build_loss_signal_bridge_decoder_anchor_distribution(
                holdout_scorecard_report(),
                read_json_report(inputs["seed_revision"]),
                read_json_report(inputs["failure_diagnostic"]),
                corpus_path=inputs["corpus"],
                training_run_dir=training_run,
                distribution_out_dir=root / "distribution",
            )
            outputs = write_loss_signal_bridge_decoder_anchor_distribution_outputs(report, root / "out")
            cli_main(
                [
                    "--holdout-scorecard-smoke",
                    str(holdout_path),
                    "--training-run-dir",
                    str(training_run),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-pass",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM}.json"))
            self.assertTrue((root / "cli-out" / f"{LOSS_SIGNAL_BRIDGE_DECODER_ANCHOR_DISTRIBUTION_STEM}.json").is_file())
            self.assertTrue((root / "cli-out" / "decoder-anchor-distribution-audit").is_dir())


def holdout_scorecard_report() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "holdout_scorecard_smoke_ready": True,
            "scorecard_overall_status": "pass",
            "model_quality_claim": "holdout_scorecard_smoke_real_execution",
            "promotion_ready": False,
        },
    }


def write_training_run(root: Path, *, train_losses: tuple[float, float] = (1.2, 0.7)) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    append_record(root / "metrics.jsonl", TrainingRecord(step=1, train_loss=train_losses[0], val_loss=1.4, last_loss=train_losses[0]))
    append_record(root / "metrics.jsonl", TrainingRecord(step=4, train_loss=train_losses[1], val_loss=0.9, last_loss=train_losses[1]))
    (root / "checkpoint.pt").write_bytes(b"checkpoint")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    write_json_payload({"status": "ok", "end_step": 4}, root / "run_manifest.json")
    write_json_payload({"max_iters": 4, "device": "cpu"}, root / "train_config.json")
    return root


if __name__ == "__main__":
    unittest.main()
