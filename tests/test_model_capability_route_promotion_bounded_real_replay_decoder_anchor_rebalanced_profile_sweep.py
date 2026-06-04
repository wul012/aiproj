from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep import (
    DEFAULT_REBALANCED_DECODER_PROFILES,
    build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep,
    locate_benchmark_suite,
    locate_dry_run,
    locate_failure_diagnostic,
    locate_suite_review,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_artifacts import (
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_html,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_markdown,
    render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text,
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs,
)
from scripts.sweep_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profiles import main as cli_main
from tests.test_model_capability_route_promotion_bounded_real_replay import ready_replay_inputs


class RebalancedProfileSweepTests(unittest.TestCase):
    def test_sweep_confirms_no_decoder_profile_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
                review,
                suite,
                dry_run,
                failure_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                suite_review_path=review_path,
                benchmark_suite_path=suite_path,
                dry_run_path=dry_path,
                generator_runner=no_recovery_runner,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_no_recovery")
        self.assertTrue(report["summary"]["rebalanced_profile_sweep_ready"])
        self.assertEqual(report["summary"]["profile_count"], len(DEFAULT_REBALANCED_DECODER_PROFILES))
        self.assertEqual(report["summary"]["best_passed_case_count"], 0)
        self.assertFalse(report["summary"]["any_profile_recovered"])
        self.assertEqual(report["summary"]["next_step"], "route_to_objective_or_architecture_intervention")
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True, require_recovery=True), 1)

    def test_partial_profile_recovery_is_not_full_promotion(self) -> None:
        profiles = [
            {"profile_id": "default_bounded", "max_new_tokens": 24, "temperature": 0.2, "top_k": 10},
            {"profile_id": "rescue_one", "max_new_tokens": 64, "temperature": 0.2, "top_k": 10},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
                review,
                suite,
                dry_run,
                failure_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                profiles=profiles,
                generator_runner=partial_recovery_runner,
            )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_partial_recovery_found")
        self.assertEqual(report["summary"]["best_profile_id"], "rescue_one")
        self.assertEqual(report["summary"]["best_passed_case_count"], 1)
        self.assertTrue(report["summary"]["any_profile_recovered"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True, require_recovery=True), 0)
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True, require_promotion=True), 1)

    def test_promotable_profile_is_reported_separately(self) -> None:
        profiles = [
            {"profile_id": "default_bounded", "max_new_tokens": 24, "temperature": 0.2, "top_k": 10},
            {"profile_id": "rescue_all", "max_new_tokens": 80, "temperature": 0.2, "top_k": 10},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
                review,
                suite,
                dry_run,
                failure_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                profiles=profiles,
                generator_runner=promotion_runner,
            )

        self.assertEqual(report["decision"], "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_promotable_profile_found")
        self.assertTrue(report["summary"]["promotion_ready"])
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True, require_promotion=True), 0)

    def test_sweep_fails_when_diagnostic_does_not_request_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, _, review, _, dry_run, _, checkpoint, tokenizer = ready_replay_inputs(root)
            diagnostic = failure_diagnostic()
            diagnostic["summary"]["next_step"] = "train_more_without_sweep"
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
                review,
                suite,
                dry_run,
                diagnostic,
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=no_recovery_runner,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_requests_profile_sweep", [row["id"] for row in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_sweep_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, suite_path, review, review_path, dry_run, dry_path, checkpoint, tokenizer = ready_replay_inputs(root)
            diagnostic_path = root / "diagnostic" / "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.json"
            diagnostic_path.parent.mkdir()
            diagnostic_path.write_text('{"status":"pass","summary":{"next_step":"run_rebalanced_decoder_profile_sweep_before_more_training"}}', encoding="utf-8")
            self.assertEqual(locate_benchmark_suite(suite_path.parent), suite_path)
            self.assertEqual(locate_suite_review(review_path.parent), review_path)
            self.assertEqual(locate_dry_run(dry_path.parent), dry_path)
            self.assertEqual(locate_failure_diagnostic(diagnostic_path.parent), diagnostic_path)
            report = build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
                review,
                suite,
                dry_run,
                failure_diagnostic(),
                checkpoint_path=checkpoint,
                tokenizer_path=tokenizer,
                generator_runner=no_recovery_runner,
            )
            outputs = write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs(report, root / "sweep")
            with patch(
                "scripts.sweep_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profiles.build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep",
                return_value=report,
            ):
                cli_main(
                    [
                        "--benchmark-suite",
                        str(suite_path.parent),
                        "--suite-review",
                        str(review_path.parent),
                        "--dry-run",
                        str(dry_path.parent),
                        "--failure-diagnostic",
                        str(diagnostic_path.parent),
                        "--checkpoint",
                        str(checkpoint),
                        "--tokenizer",
                        str(tokenizer),
                        "--out-dir",
                        str(root / "cli-sweep"),
                        "--require-sweep-ready",
                        "--force",
                    ]
                )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("profile_sweep_ready=True", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text(report))
        self.assertIn("Case Profile Rows", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_markdown(report))
        self.assertIn("Best profile", render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_html(report))


def failure_diagnostic() -> dict:
    return {
        "status": "pass",
        "summary": {
            "rebalanced_failure_diagnostic_ready": True,
            "next_step": "run_rebalanced_decoder_profile_sweep_before_more_training",
        },
    }


def no_recovery_runner(row: dict, _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict:
    prompt_case = row["prompt_case"]
    return _response(prompt_case, " f i x e")


def partial_recovery_runner(row: dict, _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict:
    prompt_case = row["prompt_case"]
    if prompt_case["generation_profile"] == "rescue_one" and row["case_id"] == "objective-answer-direct":
        return _response(prompt_case, " fixed loss")
    return _response(prompt_case, " f i x e")


def promotion_runner(row: dict, _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict:
    prompt_case = row["prompt_case"]
    if prompt_case["generation_profile"] == "rescue_all":
        return _response(prompt_case, " fixed loss")
    return _response(prompt_case, " f i x e")


def _response(prompt_case: dict, continuation: str) -> dict:
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
