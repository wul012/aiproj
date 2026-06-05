from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_gap_diagnostic import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
    build_tokenizer_coverage_aware_holdout_suite,
    locate_holdout_gap_diagnostic,
    locate_source_benchmark_suite,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_artifacts import (
    render_tokenizer_coverage_aware_holdout_suite_html,
    render_tokenizer_coverage_aware_holdout_suite_markdown,
    render_tokenizer_coverage_aware_holdout_suite_text,
    write_tokenizer_coverage_aware_holdout_suite_outputs,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import main as cli_main


class TokenizerCoverageAwareHoldoutSuiteTests(unittest.TestCase):
    def test_builds_tokenizer_covered_holdout_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path = write_tokenizer(root, all_candidate_prompt_text())
            report = build_tokenizer_coverage_aware_holdout_suite(
                holdout_gap_diagnostic(),
                source_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"])
        self.assertEqual(report["summary"]["candidate_case_count"], 5)
        self.assertEqual(report["summary"]["tokenizer_covered_case_count"], 5)
        self.assertEqual(report["summary"]["candidate_prompt_unknown_token_count"], 0)
        self.assertEqual(report["benchmark_suite"]["scoring_contract"]["expected_terms"], ["fixed", "loss"])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)

    def test_fails_when_diagnostic_does_not_route_to_this_suite(self) -> None:
        diagnostic = holdout_gap_diagnostic()
        diagnostic["summary"]["next_step"] = "train_more"
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), all_candidate_prompt_text())
            report = build_tokenizer_coverage_aware_holdout_suite(diagnostic, source_suite(), tokenizer_path=tokenizer_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("diagnostic_routes_to_tokenizer_coverage_suite", [issue["id"] for issue in report["issues"]])

    def test_fails_when_candidate_prompts_are_not_tokenizer_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), "fixed loss")
            report = build_tokenizer_coverage_aware_holdout_suite(
                holdout_gap_diagnostic(),
                source_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_candidate_prompts_tokenizer_covered", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path = write_tokenizer(root, all_candidate_prompt_text())
            diagnostic_path = root / "diagnostic" / TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_GAP_DIAGNOSTIC_JSON_FILENAME
            suite_path = root / "suite" / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
            write_json_payload(holdout_gap_diagnostic(), diagnostic_path)
            write_json_payload(source_suite(), suite_path)
            self.assertEqual(locate_holdout_gap_diagnostic(diagnostic_path.parent), diagnostic_path)
            self.assertEqual(locate_source_benchmark_suite(suite_path.parent), suite_path)
            report = build_tokenizer_coverage_aware_holdout_suite(
                holdout_gap_diagnostic(),
                source_suite(),
                tokenizer_path=tokenizer_path,
            )
            outputs = write_tokenizer_coverage_aware_holdout_suite_outputs(report, root / "out")
            cli_main(
                [
                    "--holdout-gap-diagnostic",
                    str(diagnostic_path.parent),
                    "--source-benchmark-suite",
                    str(suite_path.parent),
                    "--tokenizer",
                    str(tokenizer_path),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-suite-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME))
        self.assertIn("tokenizer_covered_case_count=5", render_tokenizer_coverage_aware_holdout_suite_text(report))
        self.assertIn("Coverage Rows", render_tokenizer_coverage_aware_holdout_suite_markdown(report))
        self.assertIn("tokenizer-coverage-aware holdout suite", render_tokenizer_coverage_aware_holdout_suite_html(report))


def write_tokenizer(root: Path, text: str) -> Path:
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    return tokenizer_path


def all_candidate_prompt_text() -> str:
    return "\n".join(
        [
            "answer with exactly two words: fixed loss\nanswer:",
            "return the two target words fixed loss\noutput:",
            "contrast route result fixed loss\nresult:",
            "jsonish answer_terms fixed loss\nanswer_terms:",
            "self check requires fixed and loss\nfinal answer:",
        ]
    )


def holdout_gap_diagnostic() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "next_step": "build_tokenizer_coverage_aware_holdout_suite_before_more_training",
            "prompt_unknown_row_count": 5,
            "prompt_unknown_token_count": 96,
        },
    }


def source_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "benchmark_suite": {
            "ready": True,
            "suite_name": "route-promotion-objective-level-contrast-bounded-suite",
            "suite_version": "v803",
            "route_id": "objective_level_contrast",
            "cases": [
                {"case_id": "objective-answer-direct", "expected_terms": ["fixed", "loss"]},
                {"case_id": "objective-answer-role", "expected_terms": ["fixed", "loss"]},
                {"case_id": "objective-answer-contrast", "expected_terms": ["fixed", "loss"]},
                {"case_id": "objective-answer-jsonish", "expected_terms": ["fixed", "loss"]},
                {"case_id": "objective-answer-check", "expected_terms": ["fixed", "loss"]},
            ],
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
        },
    }


if __name__ == "__main__":
    unittest.main()
