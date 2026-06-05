from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME,
    build_decoder_budget_holdout_replay,
    locate_decoder_budget_replay_comparison,
    locate_route_promotion_bounded_benchmark_dry_run,
    locate_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_bounded_benchmark_suite_review,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_artifacts import (
    render_decoder_budget_holdout_replay_html,
    render_decoder_budget_holdout_replay_markdown,
    render_decoder_budget_holdout_replay_text,
    write_decoder_budget_holdout_replay_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.run_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay import ready_replay_inputs


class DecoderBudgetHoldoutReplayTests(unittest.TestCase):
    def test_holdout_partial_gap_blocks_promotion_but_execution_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_decoder_budget_holdout_replay(
                decoder_budget_replay(),
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                decoder_budget_replay_path=root / "decoder-budget.json",
                suite_review_path=review_path,
                benchmark_suite_path=suite_path,
                dry_run_path=dry_path,
                generator_runner=partial_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_partial_model_gap")
        self.assertTrue(report["summary"]["source_objective_contract_recovered"])
        self.assertFalse(report["summary"]["holdout_model_route_quality_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["passed_case_count"], 1)
        self.assertEqual(report["summary"]["any_hit_case_count"], 5)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_holdout_pass=True), 1)

    def test_holdout_pass_can_mark_promotion_ready_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_decoder_budget_holdout_replay(
                decoder_budget_replay(),
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=passing_runner,
            )

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_passed_review_required")
        self.assertTrue(report["summary"]["holdout_model_route_quality_ready"])
        self.assertTrue(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_holdout_pass=True), 0)

    def test_fails_when_source_decoder_budget_replay_did_not_recover_contract(self) -> None:
        source = decoder_budget_replay()
        source["summary"]["objective_contract_recovered"] = False
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_decoder_budget_holdout_replay(
                source,
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=passing_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_objective_contract_recovered", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(root)
            source_path = root / "source" / TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME
            write_json_payload(decoder_budget_replay(), source_path)
            self.assertEqual(locate_decoder_budget_replay_comparison(source_path.parent), source_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite_review(review_path.parent), review_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_dry_run(dry_path.parent), dry_path)
            report = build_decoder_budget_holdout_replay(
                decoder_budget_replay(),
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=partial_runner,
            )
            outputs = write_decoder_budget_holdout_replay_outputs(report, root / "out")
            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "--decoder-budget-replay",
                        str(source_path.parent),
                        "--benchmark-suite",
                        str(suite_path.parent),
                        "--suite-review",
                        str(review_path.parent),
                        "--dry-run",
                        str(dry_path.parent),
                        "--checkpoint",
                        str(checkpoint),
                        "--tokenizer",
                        str(tokenizer),
                        "--out-dir",
                        str(root / "cli-out"),
                        "--require-execution-pass",
                        "--force",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME))
        self.assertIn("holdout_model_route_quality_ready=False", render_decoder_budget_holdout_replay_text(report))
        self.assertIn("Replay Rows", render_decoder_budget_holdout_replay_markdown(report))
        self.assertIn("decoder-budget holdout replay", render_decoder_budget_holdout_replay_html(report))


def decoder_budget_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_contract_recovered_holdout_required",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_ready": True,
            "objective_contract_recovered": True,
            "passed_case_count": 3,
            "case_count": 3,
            "decoder_budget_max_new_tokens": 11,
            "next_step": "run_unchanged_bounded_suite_holdout_replay",
        },
    }


def passing_runner(row: dict, _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict:
    prompt_case = row["prompt_case"]
    return {
        "prompt": prompt_case["prompt"],
        "generated": prompt_case["prompt"] + " fixed loss",
        "continuation": " fixed loss",
        "seed": prompt_case["seed"],
        "max_new_tokens": prompt_case["max_new_tokens"],
        "temperature": prompt_case["temperature"],
        "top_k": prompt_case["top_k"],
    }


def partial_runner(row: dict, _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict:
    prompt_case = row["prompt_case"]
    continuation = " fixed loss" if row.get("case_id") == "objective-answer-direct" else " fixed only"
    return {
        "prompt": prompt_case["prompt"],
        "generated": prompt_case["prompt"] + continuation,
        "continuation": continuation,
        "seed": prompt_case["seed"],
        "max_new_tokens": prompt_case["max_new_tokens"],
        "temperature": prompt_case["temperature"],
        "top_k": prompt_case["top_k"],
    }


if __name__ == "__main__":
    unittest.main()
