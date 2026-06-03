from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe,
    locate_failure_diagnostic,
    locate_prompt_aligned_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_outputs,
)


def replay_report() -> dict:
    return {
        "status": "pass",
        "checkpoint": "checkpoint.pt",
        "tokenizer": "tokenizer.json",
        "summary": {"case_count": 1, "passed_case_count": 0, "failed_case_count": 1},
        "replay_rows": [
            {
                "case_id": "case-1",
                "prompt": "Prompt\nAnswer:",
                "continuation": "f i",
                "expected_terms": ["fixed", "loss"],
                "hit_terms": [],
                "missed_terms": ["fixed", "loss"],
                "case_pass": False,
                "seed": 10,
                "temperature": 0.2,
                "top_k": 10,
            }
        ],
    }


def diagnostic_report() -> dict:
    return {
        "status": "pass",
        "summary": {"case_count": 1, "failed_case_count": 1, "zero_hit_case_count": 1, "fragment_like_case_count": 1},
    }


def fake_runner(row: dict, profile: dict, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    profile_id = profile["profile_id"]
    continuation = "ixed loss" if profile_id == "prefix_f" else "loss" if profile_id == "prefix_fixed_space" else "oss"
    return {
        "prompt": f"{row['prompt']}{profile['anchor']}",
        "continuation": continuation,
        "generated": f"{row['prompt']}{profile['anchor']}{continuation}",
        "seed": int(row["seed"]) + int(profile["seed_offset"]),
        "max_new_tokens": profile["max_new_tokens"],
        "temperature": row["temperature"],
        "top_k": row["top_k"],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorProbeTests(unittest.TestCase):
    def test_probe_detects_anchor_completion_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe(
                replay_report(),
                diagnostic_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                device="cpu",
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_found_completion_signal")
        self.assertTrue(report["summary"]["anchor_completion_success"])
        self.assertEqual(report["summary"]["completion_pass_count"], 3)
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True, require_anchor_success=True), 0)

    def test_probe_fails_without_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer = root / "tokenizer.json"
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe(
                replay_report(),
                diagnostic_report(),
                checkpoint_path=root / "missing.pt",
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_probe_ready=True), 1)

    def test_outputs_and_locators_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            replay_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(), root / "replay")
            diagnostic_outputs = write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_outputs(diagnostic_report(), root / "diagnostic")
            self.assertEqual(locate_prompt_aligned_replay(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            self.assertEqual(locate_failure_diagnostic(Path(diagnostic_outputs["json"]).parent), Path(diagnostic_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe(
                replay_report(),
                diagnostic_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_outputs(report, root / "probe")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("anchor_completion_success=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_text(report))
        self.assertIn("Probe Rows", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_markdown(report))
        self.assertIn("Completion", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_html(report))


if __name__ == "__main__":
    unittest.main()
