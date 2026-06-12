from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_decoder_anchor_probe_v1146 import (
    DECODER_ANCHOR_PROBE_V1146_STEM,
    build_decoder_anchor_probe_v1146,
    resolve_exit_code,
    resolve_v1145_checkpoint_paths,
    write_decoder_anchor_probe_v1146_outputs,
)
from minigpt.model_capability_required_term_real_execution import create_required_term_tiny_checkpoint
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_decoder_anchor_probe_v1146 import main as cli_main


class ModelCapabilityDecoderAnchorProbeV1146Tests(unittest.TestCase):
    def test_probe_finds_anchor_fragment_signal_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_decoder_anchor_probe_v1146(
                v1145_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_decoder_anchor_probe_found_fragment_signal")
        self.assertTrue(report["summary"]["decoder_anchor_probe_ready"])
        self.assertEqual(report["summary"]["fragment_hit_count"], 5)
        self.assertGreaterEqual(report["summary"]["anchor_assisted_loss_hit_count"], 4)
        self.assertEqual(report["summary"]["model_quality_claim"], "decoder_anchor_fragment_signal_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["unassisted_success_claim"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_resolver_uses_archive_relative_checkpoint_when_report_paths_are_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_dir = root / "archive-report"
            run_dir = report_dir / "real-loss-signal-training-run"
            run_dir.mkdir(parents=True)
            (run_dir / "checkpoint.pt").write_bytes(b"checkpoint")
            (run_dir / "tokenizer.json").write_text("{}", encoding="utf-8")
            report_path = report_dir / "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json"
            write_json_payload(v1145_report(), report_path)
            paths = resolve_v1145_checkpoint_paths(v1145_report(), report_path=report_path)

        self.assertFalse(paths["reported_checkpoint_exists"])
        self.assertFalse(paths["reported_tokenizer_exists"])
        self.assertTrue(paths["checkpoint_exists"])
        self.assertTrue(paths["tokenizer_exists"])
        self.assertTrue(paths["used_archive_relative_fallback"])

    def test_fails_when_v1145_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            source = v1145_report()
            source["summary"]["loss_signal_bridge_decoder_anchor_distribution_ready"] = False
            report = build_decoder_anchor_probe_v1146(
                source,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("v1145_report_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "v1145.json"
            write_json_payload(v1145_report(), source_path)
            paths = create_required_term_tiny_checkpoint(root / "tiny", prompt="fixed lo los fi", target_token_text="loss")
            report = build_decoder_anchor_probe_v1146(
                v1145_report(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                device="cpu",
            )
            outputs = write_decoder_anchor_probe_v1146_outputs(report, root / "out")
            cli_main(
                [
                    "--loss-signal-distribution",
                    str(source_path),
                    "--checkpoint",
                    paths["checkpoint"],
                    "--tokenizer",
                    paths["tokenizer"],
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-pass",
                    "--force",
                ]
            )

            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{DECODER_ANCHOR_PROBE_V1146_STEM}.json"))
            self.assertTrue((root / "cli-out" / f"{DECODER_ANCHOR_PROBE_V1146_STEM}.json").is_file())


def v1145_report() -> dict[str, object]:
    return {
        "status": "pass",
        "training_signal": {
            "checkpoint_path": "output/stale/real-loss-signal-training-run/checkpoint.pt",
            "tokenizer_path": "output/stale/real-loss-signal-training-run/tokenizer.json",
        },
        "summary": {
            "loss_signal_bridge_decoder_anchor_distribution_ready": True,
            "loss_signal_ready": True,
            "next_step": "run_decoder_anchor_probe_against_v1145_checkpoint",
            "model_quality_claim": "loss_signal_bridge_and_decoder_anchor_distribution_real_execution",
            "promotion_ready": False,
        },
    }


def fake_runner(case: dict, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    expected = str(case["expected_fragment"])
    continuation = expected if expected == "loss" else " fixed"
    return {
        "prompt": case["prompt"],
        "generated": f"{case['prompt']}{continuation}",
        "continuation": continuation,
        "seed": case["seed"],
        "max_new_tokens": case["max_new_tokens"],
        "top_k": case["top_k"],
    }


if __name__ == "__main__":
    unittest.main()
