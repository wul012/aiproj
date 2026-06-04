from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_artifacts import (
    write_bounded_objective_decoder_anchor_policy_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay import (
    BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME,
    build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay,
    locate_decoder_anchor_policy,
    locate_objective_replay_comparison,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_artifacts import (
    render_bounded_objective_decoder_anchor_policy_replay_html,
    render_bounded_objective_decoder_anchor_policy_replay_markdown,
    render_bounded_objective_decoder_anchor_policy_replay_text,
    write_bounded_objective_decoder_anchor_policy_replay_outputs,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison_artifacts import (
    write_bounded_objective_replay_comparison_outputs,
)
from scripts.run_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay import main as cli_main


class BoundedObjectiveDecoderAnchorPolicyReplayTests(unittest.TestCase):
    def test_policy_replay_reproduces_assisted_signal_but_blocks_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay(
                replay_comparison(),
                policy_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay_reproduced_assisted_signal")
        self.assertEqual(report["summary"]["policy_applied_pass_count"], 2)
        self.assertEqual(report["summary"]["new_text_pass_count"], 0)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_replay_ready=True, require_policy_case_pass=True), 0)

    def test_policy_replay_fails_without_policy_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            empty_policy = policy_report()
            empty_policy["policy_rows"] = []
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay(
                replay_comparison(),
                empty_policy,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("policy_rows_present", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_replay_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = write_fake_run(root)
            replay_outputs = write_bounded_objective_replay_comparison_outputs(replay_comparison(), root / "replay")
            policy_outputs = write_bounded_objective_decoder_anchor_policy_outputs(policy_report(), root / "policy")
            self.assertEqual(locate_objective_replay_comparison(Path(replay_outputs["json"]).parent), Path(replay_outputs["json"]))
            self.assertEqual(locate_decoder_anchor_policy(Path(policy_outputs["json"]).parent), Path(policy_outputs["json"]))
            report = build_model_capability_route_promotion_bounded_objective_decoder_anchor_policy_replay(
                replay_comparison(),
                policy_report(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner,
            )
            outputs = write_bounded_objective_decoder_anchor_policy_replay_outputs(report, root / "policy-replay")
            cli_main(
                [
                    "--replay-comparison",
                    str(Path(replay_outputs["json"]).parent),
                    "--decoder-anchor-policy",
                    str(Path(policy_outputs["json"]).parent),
                    "--checkpoint",
                    str(checkpoint),
                    "--tokenizer",
                    str(tokenizer),
                    "--out-dir",
                    str(root / "cli-policy-replay"),
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(BOUNDED_OBJECTIVE_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME))
        self.assertIn("policy_replay_success=True", render_bounded_objective_decoder_anchor_policy_replay_text(report))
        self.assertIn("Replay Rows", render_bounded_objective_decoder_anchor_policy_replay_markdown(report))
        self.assertIn("Applied pass", render_bounded_objective_decoder_anchor_policy_replay_html(report))


def replay_comparison() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_objective_replay_comparison_ready": True},
        "replay_rows": [
            {"case_id": "case-1", "prompt": "Prompt 1:", "required_terms": ["fixed", "loss"], "seed": 1839},
            {"case_id": "case-2", "prompt": "Prompt 2:", "required_terms": ["fixed", "loss"], "seed": 1839},
        ],
    }


def policy_report() -> dict:
    return {
        "status": "pass",
        "summary": {"bounded_objective_decoder_anchor_policy_ready": True},
        "policy_rows": [
            {"case_id": "case-1", "profile_id": "prefix_f", "anchor": "f"},
            {"case_id": "case-2", "profile_id": "prefix_f", "anchor": "f"},
        ],
    }


def write_fake_run(root: Path) -> tuple[Path, Path]:
    checkpoint = root / "checkpoint.pt"
    tokenizer = root / "tokenizer.json"
    checkpoint.write_bytes(b"checkpoint")
    tokenizer.write_text("{}", encoding="utf-8")
    return checkpoint, tokenizer


def fake_runner(row: dict, policy: dict | None, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict:
    anchor = "" if policy is None else str(policy.get("anchor") or "")
    continuation = "ixed loss" if policy else "noise"
    return {
        "prompt": f"{row['prompt']}{anchor}",
        "continuation": continuation,
        "generated": f"{row['prompt']}{anchor}{continuation}",
        "seed": int(row["seed"]) + 1100,
        "max_new_tokens": 12,
        "temperature": 0.2,
        "top_k": 20,
    }


if __name__ == "__main__":
    unittest.main()
