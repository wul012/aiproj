from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.target_hidden_prompt_mutation_holdout_suite import (
    TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME,
    build_target_hidden_prompt_mutation_holdout_suite,
    locate_replay_review,
    locate_source_holdout_suite,
    prompt_mutation_candidate_prompt_seed_text,
    resolve_exit_code,
)
from minigpt.target_hidden_prompt_mutation_holdout_suite_artifacts import (
    render_target_hidden_prompt_mutation_holdout_suite_html,
    render_target_hidden_prompt_mutation_holdout_suite_markdown,
    render_target_hidden_prompt_mutation_holdout_suite_text,
    write_target_hidden_prompt_mutation_holdout_suite_outputs,
)
from minigpt.target_hidden_semantic_holdout_replay_review import TARGET_HIDDEN_SEMANTIC_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
from minigpt.target_hidden_semantic_holdout_suite import TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.tokenizer import CharTokenizer
from scripts.build_target_hidden_prompt_mutation_holdout_suite import main as cli_main


class TargetHiddenPromptMutationHoldoutSuiteTests(unittest.TestCase):
    def test_builds_prompt_mutation_target_hidden_holdout_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), prompt_mutation_candidate_prompt_seed_text())
            report = build_target_hidden_prompt_mutation_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "target_hidden_prompt_mutation_holdout_suite_ready")
        self.assertTrue(report["summary"]["target_hidden_prompt_mutation_holdout_suite_ready"])
        self.assertEqual(report["summary"]["source_case_count"], 5)
        self.assertEqual(report["summary"]["candidate_case_count"], 10)
        self.assertEqual(report["summary"]["mutation_factor"], 2.0)
        self.assertEqual(report["summary"]["tokenizer_covered_case_count"], 10)
        self.assertEqual(report["summary"]["target_hidden_case_count"], 10)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["prompt_mutated_case_count"], 10)
        self.assertEqual(report["summary"]["next_step"], "run_target_hidden_prompt_mutation_holdout_dry_run")
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)

    def test_fails_when_review_does_not_approve_prompt_mutation(self) -> None:
        review = replay_review()
        review["summary"]["approved_for_prompt_mutation_holdout"] = False
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), prompt_mutation_candidate_prompt_seed_text())
            report = build_target_hidden_prompt_mutation_holdout_suite(review, source_holdout_suite(), tokenizer_path=tokenizer_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_approves_prompt_mutation", [issue["id"] for issue in report["issues"]])

    def test_fails_when_prompts_are_not_tokenizer_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), "fixed loss")
            report = build_target_hidden_prompt_mutation_holdout_suite(
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
            tokenizer_path = write_tokenizer(root, prompt_mutation_candidate_prompt_seed_text())
            review_path = root / "review" / TARGET_HIDDEN_SEMANTIC_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
            suite_path = root / "suite" / TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(replay_review(), review_path)
            write_json_payload(source_holdout_suite(), suite_path)
            self.assertEqual(locate_replay_review(review_path.parent), review_path)
            self.assertEqual(locate_source_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_prompt_mutation_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )
            outputs = write_target_hidden_prompt_mutation_holdout_suite_outputs(report, root / "out")
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
        self.assertTrue(outputs["json"].endswith(TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME))
        self.assertIn("candidate_case_count=10", render_target_hidden_prompt_mutation_holdout_suite_text(report))
        self.assertIn("Coverage Rows", render_target_hidden_prompt_mutation_holdout_suite_markdown(report))
        self.assertIn("target-hidden prompt-mutation tokenizer-covered holdout suite", render_target_hidden_prompt_mutation_holdout_suite_html(report))


def write_tokenizer(root: Path, text: str) -> Path:
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    return tokenizer_path


def replay_review() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "approved_for_prompt_mutation_holdout": True,
            "clean_prompt_case_count": 5,
            "pass_rate": 1.0,
            "next_step": "build_prompt_mutation_target_hidden_holdout_suite",
        },
    }


def source_holdout_suite() -> dict[str, object]:
    prompts = [
        "answer from memory\nanswer:",
        "write stored result\noutput:",
        "complete learned route\nresult:",
        "return final words\nanswer:",
        "self check memory result\nfinal:",
    ]
    return {
        "status": "pass",
        "summary": {"target_hidden_semantic_holdout_suite_ready": True},
        "benchmark_suite": {
            "ready": True,
            "suite_name": "route-promotion-objective-level-contrast-semantic-paraphrase-target-hidden-holdout-suite",
            "suite_version": "v906",
            "route_id": "objective_level_contrast",
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": f"semantic-hidden-{index}", "expected_terms": ["fixed", "loss"], "prompt_case": {"prompt": prompt}}
                for index, prompt in enumerate(prompts, start=1)
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
