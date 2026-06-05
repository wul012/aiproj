from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME,
    build_target_hidden_tokenizer_covered_holdout_suite,
    locate_replay_review,
    locate_source_holdout_suite,
    resolve_exit_code,
    target_hidden_candidate_prompt_seed_text,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_artifacts import (
    render_target_hidden_tokenizer_covered_holdout_suite_html,
    render_target_hidden_tokenizer_covered_holdout_suite_markdown,
    render_target_hidden_tokenizer_covered_holdout_suite_text,
    write_target_hidden_tokenizer_covered_holdout_suite_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.tokenizer import CharTokenizer
from scripts.build_bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    main as cli_main,
)


class TargetHiddenTokenizerCoveredHoldoutSuiteTests(unittest.TestCase):
    def test_builds_target_hidden_tokenizer_covered_holdout_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), target_hidden_candidate_prompt_seed_text())
            report = build_target_hidden_tokenizer_covered_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            report["decision"],
            "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready",
        )
        self.assertTrue(
            report["summary"][
                "bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite_ready"
            ]
        )
        self.assertEqual(report["summary"]["candidate_case_count"], 5)
        self.assertEqual(report["summary"]["tokenizer_covered_case_count"], 5)
        self.assertEqual(report["summary"]["target_hidden_case_count"], 5)
        self.assertEqual(report["summary"]["candidate_prompt_unknown_token_count"], 0)
        self.assertEqual(report["summary"]["source_target_leakage_case_count"], 5)
        self.assertEqual(report["benchmark_suite"]["scoring_contract"]["expected_terms"], ["fixed", "loss"])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)
        for row in report["coverage_rows"]:
            self.assertTrue(row["target_hidden"])
            prompt = prompt_for_case(report, row["case_id"])
            self.assertNotIn("fixed", prompt)
            self.assertNotIn("loss", prompt)

    def test_fails_when_review_does_not_route_to_target_hidden_suite(self) -> None:
        review = replay_review()
        review["summary"]["next_step"] = "train_more"
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), target_hidden_candidate_prompt_seed_text())
            report = build_target_hidden_tokenizer_covered_holdout_suite(review, source_holdout_suite(), tokenizer_path=tokenizer_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_routes_to_target_hidden_suite", [issue["id"] for issue in report["issues"]])

    def test_fails_when_candidate_prompts_are_not_tokenizer_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), "fixed loss")
            report = build_target_hidden_tokenizer_covered_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_prompts_tokenizer_covered", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path = write_tokenizer(root, target_hidden_candidate_prompt_seed_text())
            review_path = root / "review" / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
            suite_path = root / "suite" / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(replay_review(), review_path)
            write_json_payload(source_holdout_suite(), suite_path)
            self.assertEqual(locate_replay_review(review_path.parent), review_path)
            self.assertEqual(locate_source_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_tokenizer_covered_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )
            outputs = write_target_hidden_tokenizer_covered_holdout_suite_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-review",
                    str(review_path.parent),
                    "--source-holdout-suite",
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
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME))
        self.assertIn("target_hidden_case_count=5", render_target_hidden_tokenizer_covered_holdout_suite_text(report))
        self.assertIn("Target Hidden", render_target_hidden_tokenizer_covered_holdout_suite_markdown(report))
        self.assertIn("target-hidden tokenizer-covered holdout suite", render_target_hidden_tokenizer_covered_holdout_suite_html(report))


def write_tokenizer(root: Path, text: str) -> Path:
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    return tokenizer_path


def replay_review() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "target_leakage_case_count": 5,
            "target_hidden_case_count": 0,
            "approved_for_promotion": False,
            "next_step": "build_target_hidden_tokenizer_covered_holdout_suite",
        },
    }


def source_holdout_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "benchmark_suite": {
            "ready": True,
            "suite_name": "route-promotion-objective-level-contrast-tokenizer-covered-holdout-suite",
            "suite_version": "v898",
            "route_id": "objective_level_contrast",
            "cases": [
                {"case_id": "tokenizer-covered-answer-direct", "expected_terms": ["fixed", "loss"]},
                {"case_id": "tokenizer-covered-answer-role", "expected_terms": ["fixed", "loss"]},
                {"case_id": "tokenizer-covered-answer-contrast", "expected_terms": ["fixed", "loss"]},
                {"case_id": "tokenizer-covered-answer-jsonish", "expected_terms": ["fixed", "loss"]},
                {"case_id": "tokenizer-covered-answer-check", "expected_terms": ["fixed", "loss"]},
            ],
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
        },
    }


def prompt_for_case(report: dict[str, object], case_id: object) -> str:
    cases = {str(row["case_id"]): row for row in report["benchmark_suite"]["cases"]}
    return str(cases[str(case_id)]["prompt_case"]["prompt"])


if __name__ == "__main__":
    unittest.main()
