from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import write_model_capability_route_promotion_bounded_real_replay_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay import (
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay,
    locate_decoder_anchor_policy,
    locate_prompt_aligned_replay,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs,
)


def replay_report() -> dict:
    return {
        "status": "pass",
        "summary": {"case_count": 2},
        "replay_rows": [
            {"case_id": "case-1", "prompt": "Prompt 1:", "expected_terms": ["fixed", "loss"], "seed": 1, "temperature": 0.2, "top_k": 10, "max_new_tokens": 12},
            {"case_id": "case-2", "prompt": "Prompt 2:", "expected_terms": ["fixed", "loss"], "seed": 2, "temperature": 0.2, "top_k": 10, "max_new_tokens": 12},
        ],
    }


def policy_report() -> dict:
    return {
        "status": "pass",
        "summary": {"decoder_anchor_policy_ready": True},
        "policy_rows": [{"case_id": "case-1", "profile_id": "prefix_fixed_space", "anchor": "fixed "}],
    }


def fake_runner(row: dict, policy: dict | None, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    continuation = "loss" if policy else "noise"
    anchor = "" if policy is None else policy.get("anchor", "")
    return {
        "prompt": f"{row['prompt']}{anchor}",
        "continuation": continuation,
        "generated": f"{row['prompt']}{anchor}{continuation}",
        "seed": row["seed"],
        "max_new_tokens": row["max_new_tokens"],
        "temperature": row["temperature"],
        "top_k": row["top_k"],
    }


class ModelCapabilityRoutePromotionBoundedRealReplayDecoderAnchorPolicyReplayTests(unittest.TestCase):
    def test_policy_replay_reproduces_partial_signal_but_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay(
                replay_report(),
                policy_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_reproduced_partial_signal")
        self.assertEqual(report["summary"]["policy_applied_pass_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_replay_ready=True, require_policy_case_pass=True), 0)

    def test_policy_replay_fails_without_policy_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            empty_policy = policy_report()
            empty_policy["policy_rows"] = []
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay(
                replay_report(),
                empty_policy,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("policy_rows_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_replay_ready=True), 1)

    def test_outputs_and_locators_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = root / "checkpoint.pt"
            tokenizer = root / "tokenizer.json"
            checkpoint.write_bytes(b"checkpoint")
            tokenizer.write_text("{}", encoding="utf-8")
            replay_outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(replay_report(), root / "replay")
            policy_outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs(policy_report(), root / "policy")
            self.assertEqual(locate_prompt_aligned_replay(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_policy(Path(policy_outputs["json"]).parent), Path(policy_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay(
                replay_report(),
                policy_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs(report, root / "policy-replay")

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("policy_replay_success=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text(report))
        self.assertIn("Replay Rows", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_markdown(report))
        self.assertIn("Applied pass", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_html(report))


if __name__ == "__main__":
    unittest.main()
