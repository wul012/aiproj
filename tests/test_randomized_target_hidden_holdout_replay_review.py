from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_target_hidden_holdout_real_replay import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME
from minigpt.randomized_target_hidden_holdout_replay_review import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    build_randomized_target_hidden_holdout_replay_review,
    locate_randomized_target_hidden_holdout_real_replay,
    locate_randomized_target_hidden_holdout_suite,
    resolve_exit_code,
)
from minigpt.randomized_target_hidden_holdout_replay_review_artifacts import (
    render_randomized_target_hidden_holdout_replay_review_html,
    render_randomized_target_hidden_holdout_replay_review_markdown,
    render_randomized_target_hidden_holdout_replay_review_text,
    write_randomized_target_hidden_holdout_replay_review_outputs,
)
from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.review_randomized_target_hidden_holdout_replay import main as cli_main


class RandomizedTargetHiddenHoldoutReplayReviewTests(unittest.TestCase):
    def test_clean_randomized_signal_routes_to_candidate_packet_without_promotion(self) -> None:
        report = build_randomized_target_hidden_holdout_replay_review(real_replay(case_count=20), randomized_suite([f"memory route {index}\nanswer:" for index in range(20)]))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required")
        self.assertTrue(report["summary"]["source_randomized_holdout_model_quality_ready"])
        self.assertEqual(report["summary"]["target_leakage_case_count"], 0)
        self.assertEqual(report["summary"]["task_hint_case_count"], 0)
        self.assertEqual(report["summary"]["unique_prompt_count"], 20)
        self.assertEqual(report["summary"]["randomized_prompt_count"], 20)
        self.assertEqual(report["summary"]["clean_randomized_case_count"], 20)
        self.assertTrue(report["summary"]["approved_for_candidate_promotion_packet"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_candidate_promotion_packet")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_candidate_packet_approval=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_approval=True), 1)

    def test_known_task_hint_blocks_candidate_packet(self) -> None:
        prompts = [f"memory route {index}\nanswer:" for index in range(20)]
        prompts[3] = "return target pair\nanswer:"
        report = build_randomized_target_hidden_holdout_replay_review(real_replay(case_count=20), randomized_suite(prompts))

        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_replay_review_task_hint_blocks_promotion")
        self.assertEqual(report["summary"]["task_hint_case_count"], 1)
        self.assertFalse(report["summary"]["approved_for_candidate_promotion_packet"])
        self.assertEqual(report["summary"]["next_step"], "repair_randomized_holdout_prompt_task_hints")

    def test_source_replay_failure_blocks_review(self) -> None:
        source = real_replay(case_count=20)
        source["status"] = "fail"
        report = build_randomized_target_hidden_holdout_replay_review(source, randomized_suite([f"memory route {index}\nanswer:" for index in range(20)]))

        self.assertEqual(report["status"], "fail")
        self.assertIn("real_replay_passed", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_review_ready=True), 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            replay_path = root / "replay" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME
            suite_path = root / "suite" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
            prompts = [f"memory route {index}\nanswer:" for index in range(20)]
            write_json_payload(real_replay(case_count=20), replay_path)
            write_json_payload(randomized_suite(prompts), suite_path)
            self.assertEqual(locate_randomized_target_hidden_holdout_real_replay(replay_path.parent), replay_path)
            self.assertEqual(locate_randomized_target_hidden_holdout_suite(suite_path.parent), suite_path)
            report = build_randomized_target_hidden_holdout_replay_review(real_replay(case_count=20), randomized_suite(prompts))
            outputs = write_randomized_target_hidden_holdout_replay_review_outputs(report, root / "out")
            cli_main(
                [
                    "--real-replay",
                    str(replay_path.parent),
                    "--holdout-suite",
                    str(suite_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-review-ready",
                    "--require-candidate-packet-approval",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME))
        self.assertIn("approved_for_candidate_promotion_packet=True", render_randomized_target_hidden_holdout_replay_review_text(report))
        self.assertIn("Review Rows", render_randomized_target_hidden_holdout_replay_review_markdown(report))
        self.assertIn("randomized target-hidden holdout replay review", render_randomized_target_hidden_holdout_replay_review_html(report))


def real_replay(case_count: int) -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "randomized_target_hidden_holdout_real_replay_ready": True,
            "holdout_model_quality_ready": True,
            "randomized_holdout_model_quality_ready": True,
            "passed_case_count": case_count,
            "pass_rate": 1.0,
        },
    }


def randomized_suite(prompts: list[str]) -> dict[str, object]:
    cases = [
        {
            "case_id": f"randomized-target-hidden-{index:02d}",
            "source_case_id": f"source-{index}",
            "random_draw_index": index,
            "prompt_case": {"prompt": prompt},
        }
        for index, prompt in enumerate(prompts, start=1)
    ]
    return {
        "status": "pass",
        "summary": {
            "randomized_target_hidden_holdout_suite_ready": True,
            "candidate_case_count": len(prompts),
            "random_seed": 914,
            "randomized_case_factor": 2.0,
            "target_hidden_case_count": len(prompts),
            "task_hint_case_count": 0,
            "unique_prompt_count": len(prompts),
        },
        "benchmark_suite": {
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": cases,
        },
        "coverage_rows": [
            {
                "case_id": case["case_id"],
                "source_case_id": case["source_case_id"],
                "unique_prompt": True,
                "randomized_prompt": True,
            }
            for case in cases
        ],
    }


if __name__ == "__main__":
    unittest.main()
