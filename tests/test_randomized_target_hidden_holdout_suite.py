from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_target_hidden_holdout_suite import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME,
    build_randomized_target_hidden_holdout_suite,
    locate_replay_review,
    locate_source_holdout_suite,
    randomized_target_hidden_candidate_prompt_seed_text,
    resolve_exit_code,
)
from minigpt.randomized_target_hidden_holdout_suite_artifacts import (
    render_randomized_target_hidden_holdout_suite_html,
    render_randomized_target_hidden_holdout_suite_markdown,
    render_randomized_target_hidden_holdout_suite_text,
    write_randomized_target_hidden_holdout_suite_outputs,
)
from minigpt.report_utils import as_dict, list_of_dicts, write_json_payload
from minigpt.target_hidden_prompt_mutation_holdout_replay_review import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
from minigpt.target_hidden_prompt_mutation_holdout_suite import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.tokenizer import CharTokenizer
from scripts.build_randomized_target_hidden_holdout_suite import main as cli_main


class RandomizedTargetHiddenHoldoutSuiteTests(unittest.TestCase):
    def test_builds_seeded_randomized_target_hidden_holdout_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), randomized_target_hidden_candidate_prompt_seed_text())
            report = build_randomized_target_hidden_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
                seed=914,
                candidate_count=8,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_suite_ready")
        self.assertTrue(report["summary"]["randomized_target_hidden_holdout_suite_ready"])
        self.assertEqual(report["summary"]["source_case_count"], 4)
        self.assertEqual(report["summary"]["candidate_case_count"], 8)
        self.assertEqual(report["summary"]["random_seed"], 914)
        self.assertEqual(report["summary"]["randomized_case_factor"], 2.0)
        self.assertEqual(report["summary"]["tokenizer_covered_case_count"], 8)
        self.assertEqual(report["summary"]["target_hidden_case_count"], 8)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["unique_prompt_count"], 8)
        self.assertEqual(report["summary"]["new_vs_source_prompt_count"], 8)
        self.assertEqual(report["summary"]["next_step"], "dry_run_randomized_target_hidden_holdout")
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)

    def test_seed_reproducibility_and_seed_variation_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), randomized_target_hidden_candidate_prompt_seed_text())
            first = build_randomized_target_hidden_holdout_suite(replay_review(), source_holdout_suite(), tokenizer_path=tokenizer_path, seed=914, candidate_count=8)
            second = build_randomized_target_hidden_holdout_suite(replay_review(), source_holdout_suite(), tokenizer_path=tokenizer_path, seed=914, candidate_count=8)
            third = build_randomized_target_hidden_holdout_suite(replay_review(), source_holdout_suite(), tokenizer_path=tokenizer_path, seed=915, candidate_count=8)

        self.assertEqual(prompts(first), prompts(second))
        self.assertNotEqual(prompts(first), prompts(third))

    def test_fails_when_review_does_not_approve_randomized_holdout(self) -> None:
        review = replay_review()
        review["summary"]["approved_for_randomized_prompt_holdout"] = False
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), randomized_target_hidden_candidate_prompt_seed_text())
            report = build_randomized_target_hidden_holdout_suite(review, source_holdout_suite(), tokenizer_path=tokenizer_path, candidate_count=8)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_approves_randomized_holdout", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 1)

    def test_fails_when_randomized_prompts_are_not_tokenizer_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), "fixed loss")
            report = build_randomized_target_hidden_holdout_suite(replay_review(), source_holdout_suite(), tokenizer_path=tokenizer_path, candidate_count=8)

        self.assertEqual(report["status"], "fail")
        self.assertIn("all_prompts_tokenizer_covered", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tokenizer_path = write_tokenizer(root, randomized_target_hidden_candidate_prompt_seed_text())
            review_path = root / "review" / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
            suite_path = root / "suite" / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(replay_review(), review_path)
            write_json_payload(source_holdout_suite(), suite_path)
            self.assertEqual(locate_replay_review(review_path.parent), review_path)
            self.assertEqual(locate_source_holdout_suite(suite_path.parent), suite_path)
            report = build_randomized_target_hidden_holdout_suite(replay_review(), source_holdout_suite(), tokenizer_path=tokenizer_path, seed=914, candidate_count=8)
            outputs = write_randomized_target_hidden_holdout_suite_outputs(report, root / "out")
            cli_main(
                [
                    "--replay-review",
                    str(review_path.parent),
                    "--source-holdout-suite",
                    str(suite_path.parent),
                    "--tokenizer",
                    str(tokenizer_path),
                    "--seed",
                    "914",
                    "--candidate-count",
                    "8",
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-suite-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME))
        self.assertIn("randomized_target_hidden_holdout_suite_ready=True", render_randomized_target_hidden_holdout_suite_text(report))
        self.assertIn("Coverage Rows", render_randomized_target_hidden_holdout_suite_markdown(report))
        self.assertIn("randomized target-hidden", render_randomized_target_hidden_holdout_suite_html(report))


def write_tokenizer(root: Path, text: str) -> Path:
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    return tokenizer_path


def prompts(report: dict[str, object]) -> list[str]:
    suite = as_dict(report.get("benchmark_suite"))
    return [str(as_dict(case.get("prompt_case")).get("prompt") or "") for case in list_of_dicts(suite.get("cases"))]


def replay_review() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "approved_for_randomized_prompt_holdout": True,
            "clean_prompt_mutation_case_count": 10,
            "pass_rate": 1.0,
            "next_step": "build_randomized_target_hidden_holdout_suite",
        },
    }


def source_holdout_suite() -> dict[str, object]:
    prompts_ = [
        "memory answer\nfinal:",
        "stored memory\noutput:",
        "learned final route\nresult:",
        "write final memory\nanswer:",
    ]
    return {
        "status": "pass",
        "summary": {"target_hidden_prompt_mutation_holdout_suite_ready": True},
        "benchmark_suite": {
            "ready": True,
            "suite_name": "route-promotion-objective-level-contrast-prompt-mutation-target-hidden-holdout-suite",
            "suite_version": "v910",
            "route_id": "objective_level_contrast",
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": f"prompt-mutation-{index}", "expected_terms": ["fixed", "loss"], "prompt_case": {"prompt": prompt}}
                for index, prompt in enumerate(prompts_, start=1)
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
