from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_suite import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from minigpt.target_hidden_semantic_holdout_suite import (
    TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME,
    build_target_hidden_semantic_holdout_suite,
    locate_replay_review,
    locate_source_holdout_suite,
    resolve_exit_code,
    semantic_candidate_prompt_seed_text,
)
from minigpt.target_hidden_semantic_holdout_suite_artifacts import (
    render_target_hidden_semantic_holdout_suite_html,
    render_target_hidden_semantic_holdout_suite_markdown,
    render_target_hidden_semantic_holdout_suite_text,
    write_target_hidden_semantic_holdout_suite_outputs,
)
from minigpt.tokenizer import CharTokenizer
from scripts.build_target_hidden_semantic_holdout_suite import main as cli_main


class TargetHiddenSemanticHoldoutSuiteTests(unittest.TestCase):
    def test_builds_semantic_target_hidden_holdout_suite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), semantic_candidate_prompt_seed_text())
            report = build_target_hidden_semantic_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "target_hidden_semantic_holdout_suite_ready")
        self.assertTrue(report["summary"]["target_hidden_semantic_holdout_suite_ready"])
        self.assertEqual(report["summary"]["candidate_case_count"], 5)
        self.assertEqual(report["summary"]["tokenizer_covered_case_count"], 5)
        self.assertEqual(report["summary"]["target_hidden_case_count"], 5)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["source_task_hint_case_count"], 5)
        self.assertEqual(report["summary"]["candidate_prompt_unknown_token_count"], 0)
        self.assertEqual(report["summary"]["next_step"], "run_target_hidden_semantic_holdout_dry_run")
        self.assertEqual(resolve_exit_code(report, require_suite_ready=True), 0)
        for row in report["coverage_rows"]:
            self.assertTrue(row["target_hidden"])
            self.assertFalse(row["task_hint"])

    def test_fails_when_review_does_not_approve_wider_holdout(self) -> None:
        review = replay_review()
        review["summary"]["approved_for_wider_holdout"] = False
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), semantic_candidate_prompt_seed_text())
            report = build_target_hidden_semantic_holdout_suite(review, source_holdout_suite(), tokenizer_path=tokenizer_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_approves_wider_holdout", [issue["id"] for issue in report["issues"]])

    def test_fails_when_prompts_are_not_tokenizer_covered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tokenizer_path = write_tokenizer(Path(tmp), "fixed loss")
            report = build_target_hidden_semantic_holdout_suite(
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
            tokenizer_path = write_tokenizer(root, semantic_candidate_prompt_seed_text())
            review_path = root / "review" / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME
            suite_path = root / "suite" / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(replay_review(), review_path)
            write_json_payload(source_holdout_suite(), suite_path)
            self.assertEqual(locate_replay_review(review_path.parent), review_path)
            self.assertEqual(locate_source_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_semantic_holdout_suite(
                replay_review(),
                source_holdout_suite(),
                tokenizer_path=tokenizer_path,
            )
            outputs = write_target_hidden_semantic_holdout_suite_outputs(report, root / "out")
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
        self.assertTrue(outputs["json"].endswith(TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME))
        self.assertIn("task_hint_case_count=0", render_target_hidden_semantic_holdout_suite_text(report))
        self.assertIn("Coverage Rows", render_target_hidden_semantic_holdout_suite_markdown(report))
        self.assertIn("target-hidden semantic paraphrase tokenizer-covered holdout suite", render_target_hidden_semantic_holdout_suite_html(report))


def write_tokenizer(root: Path, text: str) -> Path:
    tokenizer = CharTokenizer.train(text)
    tokenizer_path = root / "tokenizer.json"
    tokenizer.save(tokenizer_path)
    return tokenizer_path


def replay_review() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "approved_for_wider_holdout": True,
            "approved_for_promotion": False,
            "task_hint_case_count": 5,
            "next_step": "build_semantic_paraphrase_target_hidden_holdout_suite",
        },
    }


def source_holdout_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "benchmark_suite": {
            "ready": True,
            "suite_name": "route-promotion-objective-level-contrast-target-hidden-tokenizer-covered-holdout-suite",
            "suite_version": "v902",
            "route_id": "objective_level_contrast",
            "cases": [
                {"case_id": "target-hidden-answer_learned_pair", "expected_terms": ["fixed", "loss"]},
                {"case_id": "target-hidden-return_target_pair", "expected_terms": ["fixed", "loss"]},
                {"case_id": "target-hidden-contrast_route_pair", "expected_terms": ["fixed", "loss"]},
                {"case_id": "target-hidden-jsonish_answer_terms", "expected_terms": ["fixed", "loss"]},
                {"case_id": "target-hidden-self_check_pair", "expected_terms": ["fixed", "loss"]},
            ],
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
        },
    }


if __name__ == "__main__":
    unittest.main()
