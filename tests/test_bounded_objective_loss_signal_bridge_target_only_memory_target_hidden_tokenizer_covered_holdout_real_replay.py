from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import torch

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_DRY_RUN_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
    build_target_hidden_tokenizer_covered_holdout_real_replay,
    locate_target_hidden_tokenizer_covered_holdout_dry_run,
    locate_target_hidden_tokenizer_covered_holdout_suite,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_artifacts import (
    render_target_hidden_tokenizer_covered_holdout_real_replay_html,
    render_target_hidden_tokenizer_covered_holdout_real_replay_markdown,
    render_target_hidden_tokenizer_covered_holdout_real_replay_text,
    write_target_hidden_tokenizer_covered_holdout_real_replay_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.run_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay import (
    main as cli_main,
)


class TargetHiddenTokenizerCoveredHoldoutRealReplayTests(unittest.TestCase):
    def test_real_replay_requires_checkpoint_even_with_runner(self) -> None:
        report = build_target_hidden_tokenizer_covered_holdout_real_replay(
            ready_suite(),
            ready_dry_run(),
            checkpoint_path=Path("checkpoint.pt"),
            tokenizer_path=Path("tokenizer.json"),
            generator_runner=fake_runner(" fixed loss"),
        )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])

    def test_real_replay_marks_model_quality_ready_when_all_cases_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_target_hidden_tokenizer_covered_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed loss"),
            )

        self.assertEqual(
            report["decision"],
            "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_passed_review_required",
        )
        self.assertTrue(report["summary"]["holdout_model_quality_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 0)

    def test_real_replay_partial_gap_stays_not_model_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint, tokenizer = fake_checkpoint(Path(tmp))
            report = build_target_hidden_tokenizer_covered_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed only"),
            )

        self.assertEqual(
            report["decision"],
            "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_real_replay_partial_model_gap",
        )
        self.assertFalse(report["summary"]["holdout_model_quality_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint, tokenizer = fake_checkpoint(root)
            suite_path = root / "suite" / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME
            dry_path = root / "dry" / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_DRY_RUN_JSON_FILENAME
            write_json_payload(ready_suite(), suite_path)
            write_json_payload(ready_dry_run(), dry_path)
            self.assertEqual(locate_target_hidden_tokenizer_covered_holdout_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_target_hidden_tokenizer_covered_holdout_dry_run(dry_path.parent), dry_path)
            report = build_target_hidden_tokenizer_covered_holdout_real_replay(
                ready_suite(),
                ready_dry_run(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=fake_runner(" fixed only"),
            )
            outputs = write_target_hidden_tokenizer_covered_holdout_real_replay_outputs(report, root / "out")
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
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REAL_REPLAY_JSON_FILENAME))
        self.assertIn("holdout_model_quality_ready=False", render_target_hidden_tokenizer_covered_holdout_real_replay_text(report))
        self.assertIn("Replay Rows", render_target_hidden_tokenizer_covered_holdout_real_replay_markdown(report))
        self.assertIn("real replay", render_target_hidden_tokenizer_covered_holdout_real_replay_html(report))


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
            "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready": True,
            "target_hidden_case_count": 2,
        },
        "benchmark_suite": {
            "ready": True,
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {
                    "case_id": "target-hidden-case-a",
                    "source_case_id": "source-a",
                    "prompt_case": {"prompt": "answer with the learned pair\nanswer:", "max_new_tokens": 4, "temperature": 0.2, "top_k": 10, "seed": 1},
                },
                {
                    "case_id": "target-hidden-case-b",
                    "source_case_id": "source-b",
                    "prompt_case": {"prompt": "return the target pair\noutput:", "max_new_tokens": 4, "temperature": 0.2, "top_k": 10, "seed": 2},
                },
            ],
        },
    }


def ready_dry_run() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_dry_run_ready": True},
    }


def fake_checkpoint(root: Path) -> tuple[Path, Path]:
    tokenizer = CharTokenizer.train("answer with the learned pair return target output:\n fixed loss only")
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    config = GPTConfig(vocab_size=tokenizer.vocab_size, block_size=64, n_layer=1, n_head=1, n_embd=16, dropout=0.0)
    model = MiniGPT(config)
    checkpoint_path = root / "checkpoint.pt"
    torch.save({"config": config.__dict__, "model": model.state_dict(), "step": 0}, checkpoint_path)
    return checkpoint_path, tokenizer_path


if __name__ == "__main__":
    unittest.main()
