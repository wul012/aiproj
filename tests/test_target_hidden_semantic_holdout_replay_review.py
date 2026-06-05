from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.target_hidden_semantic_holdout_real_replay import TARGET_HIDDEN_SEMANTIC_HOLDOUT_REAL_REPLAY_JSON_FILENAME
from minigpt.target_hidden_semantic_holdout_replay_review import (
    TARGET_HIDDEN_SEMANTIC_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    build_target_hidden_semantic_holdout_replay_review,
    locate_target_hidden_semantic_holdout_real_replay,
    locate_target_hidden_semantic_holdout_suite,
    resolve_exit_code,
)
from minigpt.target_hidden_semantic_holdout_replay_review_artifacts import (
    render_target_hidden_semantic_holdout_replay_review_html,
    render_target_hidden_semantic_holdout_replay_review_markdown,
    render_target_hidden_semantic_holdout_replay_review_text,
    write_target_hidden_semantic_holdout_replay_review_outputs,
)
from minigpt.target_hidden_semantic_holdout_suite import TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
from scripts.review_target_hidden_semantic_holdout_replay import main as cli_main


class TargetHiddenSemanticHoldoutReplayReviewTests(unittest.TestCase):
    def test_clean_semantic_signal_routes_to_prompt_mutation_without_promotion(self) -> None:
        report = build_target_hidden_semantic_holdout_replay_review(real_replay(), semantic_suite(["answer from memory\nanswer:", "write stored result\noutput:"]))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "target_hidden_semantic_holdout_replay_review_clean_signal_prompt_mutation_holdout_required")
        self.assertTrue(report["summary"]["source_semantic_holdout_model_quality_ready"])
        self.assertEqual(report["summary"]["target_leakage_case_count"], 0)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["clean_prompt_case_count"], 2)
        self.assertTrue(report["summary"]["approved_for_prompt_mutation_holdout"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["next_step"], "build_prompt_mutation_target_hidden_holdout_suite")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_prompt_mutation_approval=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_approval=True), 1)

    def test_known_task_hint_blocks_prompt_mutation_approval(self) -> None:
        report = build_target_hidden_semantic_holdout_replay_review(real_replay(), semantic_suite(["return the target pair\nanswer:"]))

        self.assertEqual(report["decision"], "target_hidden_semantic_holdout_replay_review_task_hint_blocks_promotion")
        self.assertEqual(report["summary"]["task_hint_case_count"], 1)
        self.assertFalse(report["summary"]["approved_for_prompt_mutation_holdout"])
        self.assertEqual(report["summary"]["next_step"], "repair_semantic_holdout_prompt_task_hints")

    def test_source_replay_failure_blocks_review(self) -> None:
        source = real_replay()
        source["status"] = "fail"
        report = build_target_hidden_semantic_holdout_replay_review(source, semantic_suite(["answer from memory\nanswer:"]))

        self.assertEqual(report["status"], "fail")
        self.assertIn("real_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / TARGET_HIDDEN_SEMANTIC_HOLDOUT_REAL_REPLAY_JSON_FILENAME
            suite_path = root / "suite" / TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(real_replay(), replay_path)
            write_json_payload(semantic_suite(["answer from memory\nanswer:"]), suite_path)
            self.assertEqual(locate_target_hidden_semantic_holdout_real_replay(replay_path.parent), replay_path)
            self.assertEqual(locate_target_hidden_semantic_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_semantic_holdout_replay_review(real_replay(), semantic_suite(["answer from memory\nanswer:"]))
            outputs = write_target_hidden_semantic_holdout_replay_review_outputs(report, root / "out")
            cli_main(
                [
                    "--real-replay",
                    str(replay_path.parent),
                    "--holdout-suite",
                    str(suite_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-review-ready",
                    "--require-prompt-mutation-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_HIDDEN_SEMANTIC_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME))
        self.assertIn("approved_for_prompt_mutation_holdout=True", render_target_hidden_semantic_holdout_replay_review_text(report))
        self.assertIn("Review Rows", render_target_hidden_semantic_holdout_replay_review_markdown(report))
        self.assertIn("semantic paraphrase holdout replay review", render_target_hidden_semantic_holdout_replay_review_html(report))


def real_replay() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "target_hidden_semantic_holdout_real_replay_ready": True,
            "holdout_model_quality_ready": True,
            "semantic_holdout_model_quality_ready": True,
            "passed_case_count": 2,
            "pass_rate": 1.0,
        },
    }


def semantic_suite(prompts: list[str]) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "target_hidden_semantic_holdout_suite_ready": True,
            "target_hidden_case_count": len(prompts),
            "task_hint_case_count": 0,
        },
        "benchmark_suite": {
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {
                    "case_id": f"semantic-hidden-{index}",
                    "source_case_id": f"source-{index}",
                    "prompt_case": {"prompt": prompt},
                }
                for index, prompt in enumerate(prompts, start=1)
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
