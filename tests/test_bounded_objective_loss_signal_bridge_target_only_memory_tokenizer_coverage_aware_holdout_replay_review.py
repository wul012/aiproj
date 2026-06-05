from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    build_tokenizer_coverage_aware_holdout_replay_review,
    locate_holdout_real_replay,
    locate_holdout_suite,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_artifacts import (
    render_tokenizer_coverage_aware_holdout_replay_review_html,
    render_tokenizer_coverage_aware_holdout_replay_review_markdown,
    render_tokenizer_coverage_aware_holdout_replay_review_text,
    write_tokenizer_coverage_aware_holdout_replay_review_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.review_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay import main as cli_main


class TokenizerCoverageAwareHoldoutReplayReviewTests(unittest.TestCase):
    def test_target_leakage_blocks_promotion_but_review_is_ready(self) -> None:
        report = build_tokenizer_coverage_aware_holdout_replay_review(real_replay(), suite_with_prompt("answer fixed loss\nanswer:"))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_target_leakage_blocks_promotion")
        self.assertTrue(report["summary"]["source_holdout_model_quality_ready"])
        self.assertEqual(report["summary"]["target_leakage_case_count"], 1)
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_approval=True), 1)

    def test_target_hidden_suite_can_be_approved(self) -> None:
        report = build_tokenizer_coverage_aware_holdout_replay_review(real_replay(), suite_with_prompt("answer the target pair\nanswer:"))

        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review_approved")
        self.assertTrue(report["summary"]["approved_for_promotion"])

    def test_source_replay_failure_blocks_review(self) -> None:
        source = real_replay()
        source["status"] = "fail"
        report = build_tokenizer_coverage_aware_holdout_replay_review(source, suite_with_prompt("answer fixed loss\nanswer:"))

        self.assertEqual(report["status"], "fail")
        self.assertIn("real_replay_passed", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REAL_REPLAY_JSON_FILENAME
            suite_path = root / "suite" / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(real_replay(), replay_path)
            write_json_payload(suite_with_prompt("answer fixed loss\nanswer:"), suite_path)
            self.assertEqual(locate_holdout_real_replay(replay_path.parent), replay_path)
            self.assertEqual(locate_holdout_suite(suite_path.parent), suite_path)
            report = build_tokenizer_coverage_aware_holdout_replay_review(real_replay(), suite_with_prompt("answer fixed loss\nanswer:"))
            outputs = write_tokenizer_coverage_aware_holdout_replay_review_outputs(report, root / "out")
            cli_main([
                "--real-replay",
                str(replay_path.parent),
                "--holdout-suite",
                str(suite_path.parent),
                "--out-dir",
                str(root / "cli-out"),
                "--require-review-ready",
                "--force",
            ])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME))
        self.assertIn("approved_for_promotion=False", render_tokenizer_coverage_aware_holdout_replay_review_text(report))
        self.assertIn("Review Rows", render_tokenizer_coverage_aware_holdout_replay_review_markdown(report))
        self.assertIn("replay review", render_tokenizer_coverage_aware_holdout_replay_review_html(report))


def real_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_real_replay_ready": True,
            "holdout_model_quality_ready": True,
        },
    }


def suite_with_prompt(prompt: str) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {"bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready": True},
        "benchmark_suite": {
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {
                    "case_id": "case-a",
                    "source_case_id": "source-a",
                    "prompt_case": {"prompt": prompt},
                }
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
