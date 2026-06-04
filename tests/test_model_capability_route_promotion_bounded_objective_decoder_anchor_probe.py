from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe,
    locate_objective_replay_comparison,
    locate_objective_zero_hit_diagnostic,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_probe_artifacts import (
    render_bounded_objective_decoder_anchor_probe_html,
    render_bounded_objective_decoder_anchor_probe_markdown,
    render_bounded_objective_decoder_anchor_probe_text,
    write_bounded_objective_decoder_anchor_probe_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import (
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.run_model_capability_route_promotion_bounded_objective_decoder_anchor_probe import main as cli_main


class BoundedObjectiveDecoderAnchorProbeTests(unittest.TestCase):
    def test_probe_detects_assisted_completion_signal_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
                replay_comparison(),
                zero_hit_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                device="cpu",
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_decoder_anchor_probe_found_completion_signal")
        self.assertTrue(report["summary"]["anchor_completion_success"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["completion_pass_count"], 3)
        self.assertEqual(report["interpretation"]["model_quality_claim"], "decoder_anchor_signal_only")
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True, require_anchor_success=True), 0)

    def test_probe_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer = root / "tokenizer.json"
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
                replay_comparison(),
                zero_hit_diagnostic(),
                checkpoint_path=root / "missing.pt",
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True), 1)

    def test_probe_fails_when_objective_already_recovered(self) -> None:
        replay = replay_comparison()
        replay["summary"]["objective_contract_recovered"] = True
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
                replay,
                zero_hit_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("objective_not_recovered", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            replay_path = root / "replay" / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME
            diagnostic_path = root / "diagnostic" / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
            write_json_payload(replay_comparison(), replay_path)
            write_json_payload(zero_hit_diagnostic(), diagnostic_path)
            self.assertEqual(locate_objective_replay_comparison(replay_path.parent), replay_path)
            self.assertEqual(locate_objective_zero_hit_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
                replay_comparison(),
                zero_hit_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )
            outputs = write_bounded_objective_decoder_anchor_probe_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-comparison",
                    str(replay_path.parent),
                    "--zero-hit-diagnostic",
                    str(diagnostic_path.parent),
                    "--checkpoint",
                    str(checkpoint),
                    "--tokenizer",
                    str(tokenizer),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME))
        self.assertIn("bounded_objective_decoder_anchor_probe_ready=True", render_bounded_objective_decoder_anchor_probe_text(report))
        self.assertIn("Probe Rows", render_bounded_objective_decoder_anchor_probe_markdown(report))
        self.assertIn("Probe Rows", render_bounded_objective_decoder_anchor_probe_html(report))


def replay_comparison() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_replay_comparison_ready": True,
            "objective_contract_recovered": False,
            "zero_hit_case_count": 1,
        },
        "replay_rows": [
            {
                "case_id": "canonical_direct_completion",
                "prompt": "Answer with exactly two tokens: fixed loss\nanswer:",
                "continuation": " wixed w",
                "required_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "any_hit": False,
                "seed": 1839,
            }
        ],
    }


def zero_hit_diagnostic() -> dict:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_zero_hit_diagnostic_ready": True,
            "case_count": 1,
            "zero_hit_case_count": 1,
            "near_miss_case_count": 1,
        },
    }


def write_fake_run(root: Path) -> tuple[Path, Path]:
    checkpoint = root / "checkpoint.pt"
    tokenizer = root / "tokenizer.json"
    checkpoint.write_bytes(b"checkpoint")
    tokenizer.write_text("{}", encoding="utf-8")
    return checkpoint, tokenizer


def fake_runner(row: dict, profile: dict, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    profile_id = profile["profile_id"]
    continuation = "ixed loss" if profile_id == "prefix_f" else "loss" if profile_id == "prefix_fixed_space" else "oss"
    return {
        "prompt": f"{row['prompt']}{profile['anchor']}",
        "continuation": continuation,
        "generated": f"{row['prompt']}{profile['anchor']}{continuation}",
        "seed": int(row["seed"]) + int(profile["seed_offset"]),
        "max_new_tokens": profile["max_new_tokens"],
        "temperature": 0.2,
        "top_k": 20,
    }


if __name__ == "__main__":
    unittest.main()
