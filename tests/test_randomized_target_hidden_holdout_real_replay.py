from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.randomized_target_hidden_holdout_dry_run import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_real_replay import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
    build_randomized_target_hidden_holdout_real_replay,
    locate_randomized_target_hidden_holdout_dry_run,
    locate_randomized_target_hidden_holdout_suite,
    resolve_exit_code,
)
from minigpt.randomized_target_hidden_holdout_real_replay_artifacts import (
    render_randomized_target_hidden_holdout_real_replay_html,
    render_randomized_target_hidden_holdout_real_replay_markdown,
    render_randomized_target_hidden_holdout_real_replay_text,
    write_randomized_target_hidden_holdout_real_replay_outputs,
)
from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.run_randomized_target_hidden_holdout_real_replay import main as cli_main


class RandomizedTargetHiddenHoldoutRealReplayTests(unittest.TestCase):
    def test_real_replay_marks_randomized_quality_ready_when_all_cases_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_randomized_target_hidden_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed loss"),
            )

        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_real_replay_passed_review_required")
        self.assertTrue(report["summary"]["randomized_holdout_model_quality_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 0)

    def test_real_replay_partial_gap_stays_not_model_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_randomized_target_hidden_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed only"),
            )

        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_real_replay_partial_model_gap")
        self.assertFalse(report["summary"]["randomized_holdout_model_quality_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 1)

    def test_real_replay_fails_when_suite_factor_is_too_low(self) -> None:
        source = ready_suite()
        source["summary"]["randomized_case_factor"] = 1.0
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_randomized_target_hidden_holdout_real_replay(
                source,
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed loss"),
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("randomized_case_factor_at_least_two", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = fake_checkpoint(root)
            suite_path = root / "suite" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
            dry_path = root / "dry" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME
            write_json_payload(ready_suite(), suite_path)
            write_json_payload(ready_dry_run(), dry_path)
            self.assertEqual(locate_randomized_target_hidden_holdout_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_randomized_target_hidden_holdout_dry_run(dry_path.parent), dry_path)
            report = build_randomized_target_hidden_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed only"),
            )
            outputs = write_randomized_target_hidden_holdout_real_replay_outputs(report, root / "out")
            cli_main(
                [
                    "--holdout-suite",
                    str(suite_path.parent),
                    "--dry-run",
                    str(dry_path.parent),
                    "--checkpoint",
                    str(checkpoint),
                    "--tokenizer",
                    str(tokenizer),
                    "--device",
                    "cpu",
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-execution-pass",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME))
        self.assertIn("randomized_holdout_model_quality_ready=False", render_randomized_target_hidden_holdout_real_replay_text(report))
        self.assertIn("Replay Rows", render_randomized_target_hidden_holdout_real_replay_markdown(report))
        self.assertIn("randomized target-hidden holdout real replay", render_randomized_target_hidden_holdout_real_replay_html(report))


def fake_runner(continuation: str):
    def run(case: dict[str, object], _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict[str, object]:
        prompt_case = case.get("prompt_case")
        prompt = str(prompt_case.get("prompt") if isinstance(prompt_case, dict) else "")
        return {"prompt": prompt, "generated": prompt + continuation, "continuation": continuation, "max_new_tokens": 24, "temperature": 0.2, "top_k": 10, "seed": 1}

    return run


def ready_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "randomized_target_hidden_holdout_suite_ready": True,
            "candidate_case_count": 2,
            "random_seed": 914,
            "randomized_case_factor": 2.0,
            "target_hidden_case_count": 2,
            "unique_prompt_count": 2,
        },
        "benchmark_suite": {
            "ready": True,
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": "randomized-target-hidden-a", "source_case_id": "source-a", "random_draw_index": 1, "prompt_case": {"prompt": "memory answer final\nresult:", "max_new_tokens": 4, "temperature": 0.2, "top_k": 10, "seed": 1}},
                {"case_id": "randomized-target-hidden-b", "source_case_id": "source-b", "random_draw_index": 2, "prompt_case": {"prompt": "stored route output\nanswer:", "max_new_tokens": 4, "temperature": 0.2, "top_k": 10, "seed": 2}},
            ],
        },
    }


def ready_dry_run() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "randomized_target_hidden_holdout_dry_run_ready": True,
            "negative_control_passed": False,
        },
    }


def fake_checkpoint(root: Path) -> tuple[Path, Path]:
    tokenizer = CharTokenizer.train("memory answer final stored output route result:\n fixed loss only")
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=64, n_layer=1, n_head=1, n_embd=16, dropout=0.0)
    model = MiniGPT(config)
    checkpoint_path = root / "checkpoint.pt"
    torch.save({"config": config.__dict__, "model": model.state_dict(), "step": 0}, checkpoint_path)
    return checkpoint_path, tokenizer_path


if __name__ == "__main__":
    unittest.main()
