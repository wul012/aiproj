from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.target_hidden_prompt_mutation_holdout_real_replay import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REAL_REPLAY_JSON_FILENAME
from minigpt.target_hidden_prompt_mutation_holdout_replay_review import (
    TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    build_target_hidden_prompt_mutation_holdout_replay_review,
    locate_target_hidden_prompt_mutation_holdout_real_replay,
    locate_target_hidden_prompt_mutation_holdout_suite,
    resolve_exit_code,
)
from minigpt.target_hidden_prompt_mutation_holdout_replay_review_artifacts import (
    render_target_hidden_prompt_mutation_holdout_replay_review_html,
    render_target_hidden_prompt_mutation_holdout_replay_review_markdown,
    render_target_hidden_prompt_mutation_holdout_replay_review_text,
    write_target_hidden_prompt_mutation_holdout_replay_review_outputs,
)
from minigpt.target_hidden_prompt_mutation_holdout_suite import TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
from scripts.review_target_hidden_prompt_mutation_holdout_replay import main as cli_main


class TargetHiddenPromptMutationHoldoutReplayReviewTests(unittest.TestCase):
    def test_small_clean_prompt_mutation_signal_remains_review_only(self) -> None:
        report = build_target_hidden_prompt_mutation_holdout_replay_review(real_replay(), prompt_mutation_suite(["memory answer\nfinal:", "stored memory\noutput:"]))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "target_hidden_prompt_mutation_holdout_replay_review_blocks_promotion")
        self.assertTrue(report["summary"]["source_prompt_mutation_holdout_model_quality_ready"])
        self.assertEqual(report["summary"]["target_leakage_case_count"], 0)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["prompt_mutated_case_count"], 2)
        self.assertEqual(report["summary"]["clean_prompt_mutation_case_count"], 2)
        self.assertFalse(report["summary"]["approved_for_randomized_prompt_holdout"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["next_step"], "diagnose_prompt_mutation_target_hidden_holdout_replay_gap")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_randomized_holdout_approval=True), 1)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_approval=True), 1)

    def test_clean_ten_case_signal_approves_randomized_holdout(self) -> None:
        prompts = [f"memory variant {index}\nfinal:" for index in range(10)]
        report = build_target_hidden_prompt_mutation_holdout_replay_review(real_replay(case_count=10), prompt_mutation_suite(prompts))

        self.assertEqual(report["decision"], "target_hidden_prompt_mutation_holdout_replay_review_clean_signal_randomized_holdout_required")
        self.assertEqual(report["summary"]["case_count"], 10)
        self.assertTrue(report["summary"]["approved_for_randomized_prompt_holdout"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["next_step"], "build_randomized_target_hidden_holdout_suite")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_randomized_holdout_approval=True), 0)

    def test_unmutated_prompt_blocks_randomized_holdout_approval(self) -> None:
        source = prompt_mutation_suite(["memory answer\nfinal:", "stored memory\noutput:"])
        source["coverage_rows"][1]["prompt_mutated"] = False
        report = build_target_hidden_prompt_mutation_holdout_replay_review(real_replay(), source)

        self.assertEqual(report["decision"], "target_hidden_prompt_mutation_holdout_replay_review_unmutated_prompt_blocks_promotion")
        self.assertEqual(report["summary"]["prompt_mutated_case_count"], 1)
        self.assertEqual(report["summary"]["clean_prompt_mutation_case_count"], 1)
        self.assertFalse(report["summary"]["approved_for_randomized_prompt_holdout"])
        self.assertEqual(report["summary"]["next_step"], "repair_prompt_mutation_holdout_unmutated_prompts")

    def test_source_replay_failure_blocks_review(self) -> None:
        source = real_replay()
        source["status"] = "fail"
        report = build_target_hidden_prompt_mutation_holdout_replay_review(source, prompt_mutation_suite(["memory answer\nfinal:", "stored memory\noutput:"]))

        self.assertEqual(report["status"], "fail")
        self.assertIn("real_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REAL_REPLAY_JSON_FILENAME
            suite_path = root / "suite" / TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_SUITE_JSON_FILENAME
            prompts = [f"memory variant {index}\nfinal:" for index in range(10)]
            write_json_payload(real_replay(case_count=10), replay_path)
            write_json_payload(prompt_mutation_suite(prompts), suite_path)
            self.assertEqual(locate_target_hidden_prompt_mutation_holdout_real_replay(replay_path.parent), replay_path)
            self.assertEqual(locate_target_hidden_prompt_mutation_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_prompt_mutation_holdout_replay_review(real_replay(case_count=10), prompt_mutation_suite(prompts))
            outputs = write_target_hidden_prompt_mutation_holdout_replay_review_outputs(report, root / "out")
            cli_main(
                [
                    "--real-replay",
                    str(replay_path.parent),
                    "--holdout-suite",
                    str(suite_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-review-ready",
                    "--require-randomized-holdout-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(TARGET_HIDDEN_PROMPT_MUTATION_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME))
        self.assertIn("approved_for_randomized_prompt_holdout=True", render_target_hidden_prompt_mutation_holdout_replay_review_text(report))
        self.assertIn("Review Rows", render_target_hidden_prompt_mutation_holdout_replay_review_markdown(report))
        self.assertIn("prompt-mutation holdout replay review", render_target_hidden_prompt_mutation_holdout_replay_review_html(report))


def real_replay(case_count: int = 2) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "target_hidden_prompt_mutation_holdout_real_replay_ready": True,
            "holdout_model_quality_ready": True,
            "prompt_mutation_holdout_model_quality_ready": True,
            "passed_case_count": case_count,
            "pass_rate": 1.0,
        },
    }


def prompt_mutation_suite(prompts: list[str]) -> dict[str, object]:
    cases = [
        {
            "case_id": f"prompt-mutation-{index}",
            "source_case_id": f"semantic-hidden-{index}",
            "prompt_case": {"prompt": prompt},
        }
        for index, prompt in enumerate(prompts, start=1)
    ]
    return {
        "status": "pass",
        "summary": {
            "target_hidden_prompt_mutation_holdout_suite_ready": True,
            "mutation_factor": 2.0,
            "target_hidden_case_count": len(prompts),
            "task_hint_case_count": 0,
            "prompt_mutated_case_count": len(prompts),
        },
        "benchmark_suite": {
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": cases,
        },
        "coverage_rows": [
            {
                "case_id": case["case_id"],
                "source_case_id": case["source_case_id"],
                "prompt_mutated": True,
            }
            for case in cases
        ],
    }


if __name__ == "__main__":
    unittest.main()
