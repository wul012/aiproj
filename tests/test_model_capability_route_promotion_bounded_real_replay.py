from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run import build_model_capability_route_promotion_bounded_benchmark_dry_run
from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run_artifacts import write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs
from minigpt.model_capability_route_promotion_bounded_real_replay import (
    build_model_capability_route_promotion_bounded_real_replay,
    locate_route_promotion_bounded_benchmark_dry_run,
    locate_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_bounded_benchmark_suite_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_html,
    render_model_capability_route_promotion_bounded_real_replay_markdown,
    render_model_capability_route_promotion_bounded_real_replay_text,
    write_model_capability_route_promotion_bounded_real_replay_outputs,
)
from scripts.run_model_capability_route_promotion_bounded_real_replay import main as cli_main
from tests.test_model_capability_route_promotion_bounded_benchmark_dry_run import ready_suite_and_review


def ready_replay_inputs(root: Path) -> tuple[dict, Path, dict, Path, dict, Path, Path, Path]:
    suite, suite_path, review, review_path = ready_suite_and_review(root)
    dry_run = build_model_capability_route_promotion_bounded_benchmark_dry_run(review, suite, suite_review_path=review_path, benchmark_suite_path=suite_path)
    dry_outputs = write_model_capability_route_promotion_bounded_benchmark_dry_run_outputs(dry_run, root / "dry-run")
    run_dir = root / "run"
    run_dir.mkdir()
    checkpoint = run_dir / "checkpoint.pt"
    tokenizer = run_dir / "tokenizer.json"
    checkpoint.write_bytes(b"fake checkpoint")
    tokenizer.write_text("{}", encoding="utf-8")
    return suite, suite_path, review, review_path, dry_run, Path(dry_outputs["json"]), checkpoint, tokenizer


class ModelCapabilityRoutePromotionBoundedRealReplayTests(unittest.TestCase):
    def test_real_replay_executes_but_keeps_partial_model_quality_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(Path(tmp))
            report = build_model_capability_route_promotion_bounded_real_replay(
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                suite_review_path=review_path,
                benchmark_suite_path=suite_path,
                dry_run_path=dry_path,
                generator_runner=partial_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_completed_with_model_gaps")
        self.assertTrue(report["summary"]["bounded_real_replay_executed"])
        self.assertFalse(report["summary"]["model_route_quality_ready"])
        self.assertEqual(report["summary"]["passed_case_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 1)

    def test_real_replay_can_mark_model_quality_ready_when_all_cases_hit_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(Path(tmp))
            report = build_model_capability_route_promotion_bounded_real_replay(
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=passing_runner,
            )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_passed")
        self.assertTrue(report["summary"]["model_route_quality_ready"])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True, require_model_pass=True), 0)

    def test_real_replay_fails_when_checkpoint_or_tokenizer_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            checkpoint.unlink()
            report = build_model_capability_route_promotion_bounded_real_replay(
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=passing_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("checkpoint_exists", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_execution_pass=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(root)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_suite_review(review_path.parent), review_path)
            self.assertEqual(locate_route_promotion_bounded_benchmark_dry_run(dry_path.parent), dry_path)
            report = build_model_capability_route_promotion_bounded_real_replay(
                review,
                suite,
                dry_run,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=passing_runner,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_outputs(report, root / "real-replay")
            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
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
                        str(root / "cli-real-replay"),
                        "--require-execution-pass",
                        "--force",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("bounded_real_replay_executed=True", render_model_capability_route_promotion_bounded_real_replay_text(report))
        self.assertIn("Replay Rows", render_model_capability_route_promotion_bounded_real_replay_markdown(report))
        self.assertIn("real replay", render_model_capability_route_promotion_bounded_real_replay_html(report))


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
