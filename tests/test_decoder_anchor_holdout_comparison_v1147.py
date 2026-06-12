from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.decoder_anchor_holdout_comparison_v1147 import (
    DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM,
    build_decoder_anchor_holdout_comparison_v1147,
    locate_v1146_report,
    resolve_comparison_paths,
    resolve_exit_code,
    write_decoder_anchor_holdout_comparison_v1147_outputs,
)
from minigpt.model_capability_required_term_real_execution import create_required_term_tiny_checkpoint
from minigpt.report_utils import write_json_payload
from scripts.run_decoder_anchor_holdout_comparison_v1147 import main as cli_main


class DecoderAnchorHoldoutComparisonV1147Tests(unittest.TestCase):
    def test_anchor_signal_outpaces_unassisted_holdout_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_decoder_anchor_holdout_comparison_v1147(
                v1146_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_unassisted_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "decoder_anchor_signal_exceeds_unassisted_holdout_replay")
        self.assertTrue(report["summary"]["decoder_anchor_holdout_comparison_ready"])
        self.assertEqual(report["summary"]["anchor_fragment_hit_count"], 5)
        self.assertEqual(report["summary"]["unassisted_any_term_hit_count"], 2)
        self.assertEqual(report["summary"]["unassisted_full_pair_count"], 0)
        self.assertEqual(report["summary"]["model_quality_claim"], "anchor_assisted_signal_exceeds_unassisted_holdout_replay")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["unassisted_success_claim"])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_fails_when_v1146_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            source = v1146_report()
            source["summary"]["next_step"] = "unexpected"
            report = build_decoder_anchor_holdout_comparison_v1147(
                source,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_unassisted_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("v1146_next_step_matches_comparison", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_fails_when_checkpoint_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer = root / "tokenizer.json"
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_decoder_anchor_holdout_comparison_v1147(
                v1146_report(),
                checkpoint_path=root / "missing.pt",
                tokenizer_path=tokenizer,
                generator_runner=fake_unassisted_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])

    def test_path_resolver_uses_v1145_archive_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_dir = root / "archive-report"
            run_dir = report_dir / "real-loss-signal-training-run"
            run_dir.mkdir(parents=True)
            checkpoint = run_dir / "checkpoint.pt"
            tokenizer = run_dir / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            source_v1145 = report_dir / "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json"
            write_json_payload(
                {
                    "training_signal": {
                        "checkpoint_path": "output/stale/checkpoint.pt",
                        "tokenizer_path": "output/stale/tokenizer.json",
                    }
                },
                source_v1145,
            )
            paths = resolve_comparison_paths(v1146_report(), loss_signal_report_path=source_v1145)

        self.assertFalse(paths["reported_checkpoint_exists"])
        self.assertTrue(paths["checkpoint_exists"])
        self.assertTrue(paths["tokenizer_exists"])
        self.assertTrue(paths["used_v1145_archive_resolution"])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "v1146"
            source_path.mkdir()
            write_json_payload(v1146_report(), source_path / "model_capability_decoder_anchor_probe_v1146.json")
            paths = create_required_term_tiny_checkpoint(root / "tiny", prompt="answer: fixed loss", target_token_text=" fixed loss")
            report = build_decoder_anchor_holdout_comparison_v1147(
                v1146_report(),
                checkpoint_path=paths["checkpoint"],
                tokenizer_path=paths["tokenizer"],
                device="cpu",
            )
            outputs = write_decoder_anchor_holdout_comparison_v1147_outputs(report, root / "out")
            cli_main(
                [
                    "--decoder-anchor-probe",
                    str(source_path),
                    "--checkpoint",
                    paths["checkpoint"],
                    "--tokenizer",
                    paths["tokenizer"],
                    "--out-dir",
                    str(root / "cli-out"),
                    "--force",
                ]
            )

            self.assertEqual(locate_v1146_report(source_path), source_path / "model_capability_decoder_anchor_probe_v1146.json")
            self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
            self.assertTrue(outputs["json"].endswith(f"{DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM}.json"))
            self.assertTrue((root / "cli-out" / f"{DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM}.json").is_file())


def v1146_report() -> dict[str, object]:
    return {
        "status": "pass",
        "checkpoint": "output/stale/checkpoint.pt",
        "tokenizer": "output/stale/tokenizer.json",
        "summary": {
            "decoder_anchor_probe_ready": True,
            "next_step": "compare_decoder_anchor_probe_with_unassisted_holdout_replay",
            "promotion_ready": False,
            "unassisted_success_claim": False,
        },
        "rows": [
            {
                "case_id": "fixed-space-loss",
                "prompt": "fixed ",
                "combined": "fixed lossssss",
                "fragment_hit": True,
                "anchor_assisted_loss_hit": True,
            },
            {
                "case_id": "lo-to-loss",
                "prompt": "lo",
                "combined": "losssss",
                "fragment_hit": True,
                "anchor_assisted_loss_hit": True,
            },
            {
                "case_id": "los-to-loss",
                "prompt": "los",
                "combined": "losssss",
                "fragment_hit": True,
                "anchor_assisted_loss_hit": True,
            },
            {
                "case_id": "fixed-retention",
                "prompt": "fixed",
                "combined": "fixed fixe fi",
                "fragment_hit": True,
                "anchor_assisted_loss_hit": False,
            },
            {
                "case_id": "fi-to-loss-association",
                "prompt": "fi",
                "combined": "fier losss",
                "fragment_hit": True,
                "anchor_assisted_loss_hit": True,
            },
        ],
    }


def fake_unassisted_runner(case: dict, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    continuations = {
        "answer-colon-pair": " the tos",
        "answer-space-pair": "lossssss",
        "completion-colon-pair": " tosssss",
        "finish-space-pair": "ter loss",
        "compact-signal-answer-pair": " signal only",
    }
    continuation = continuations[str(case["case_id"])]
    return {
        "prompt": case["prompt"],
        "generated": f"{case['prompt']}{continuation}",
        "continuation": continuation,
        "seed": case["seed"],
    }


if __name__ == "__main__":
    unittest.main()
