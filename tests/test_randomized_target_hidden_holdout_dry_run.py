from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_target_hidden_holdout_dry_run import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME,
    build_randomized_target_hidden_holdout_dry_run,
    locate_randomized_target_hidden_holdout_suite,
    resolve_exit_code,
)
from minigpt.randomized_target_hidden_holdout_dry_run_artifacts import (
    render_randomized_target_hidden_holdout_dry_run_html,
    render_randomized_target_hidden_holdout_dry_run_markdown,
    render_randomized_target_hidden_holdout_dry_run_text,
    write_randomized_target_hidden_holdout_dry_run_outputs,
)
from minigpt.randomized_target_hidden_holdout_suite import RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
from minigpt.report_utils import write_json_payload
from scripts.dry_run_randomized_target_hidden_holdout import main as cli_main


class RandomizedTargetHiddenHoldoutDryRunTests(unittest.TestCase):
    def test_dry_run_passes_positive_and_blocks_negative_control(self) -> None:
        report = build_randomized_target_hidden_holdout_dry_run(ready_suite())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_target_hidden_holdout_dry_run_passed")
        self.assertTrue(report["summary"]["randomized_target_hidden_holdout_dry_run_ready"])
        self.assertEqual(report["summary"]["case_count"], 4)
        self.assertEqual(report["summary"]["source_random_seed"], 914)
        self.assertEqual(report["summary"]["source_randomized_case_factor"], 2.0)
        self.assertEqual(report["summary"]["positive_passed_case_count"], 4)
        self.assertEqual(report["summary"]["negative_passed_case_count"], 0)
        self.assertFalse(report["summary"]["negative_control_passed"])
        self.assertEqual(report["summary"]["next_step"], "run_randomized_target_hidden_holdout_real_replay")
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 0)

    def test_dry_run_fails_when_negative_control_passes(self) -> None:
        report = build_randomized_target_hidden_holdout_dry_run(ready_suite(), negative_continuation=" fixed loss")

        self.assertEqual(report["status"], "fail")
        self.assertIn("negative_rows_fail", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 1)

    def test_dry_run_fails_when_source_is_not_ready(self) -> None:
        source = ready_suite()
        source["summary"]["randomized_target_hidden_holdout_suite_ready"] = False
        report = build_randomized_target_hidden_holdout_dry_run(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("holdout_suite_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = root / "suite" / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(ready_suite(), suite_path)
            self.assertEqual(locate_randomized_target_hidden_holdout_suite(suite_path.parent), suite_path)
            report = build_randomized_target_hidden_holdout_dry_run(ready_suite())
            outputs = write_randomized_target_hidden_holdout_dry_run_outputs(report, root / "out")
            cli_main(
                [
                    "--holdout-suite",
                    str(suite_path.parent),
                    "--out-dir",
                    str(root / "cli-out"),
                    "--require-dry-run-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_TARGET_HIDDEN_HOLDOUT_DRY_RUN_JSON_FILENAME))
        self.assertIn("positive_passed_case_count=4", render_randomized_target_hidden_holdout_dry_run_text(report))
        self.assertIn("Dry-Run Rows", render_randomized_target_hidden_holdout_dry_run_markdown(report))
        self.assertIn("randomized target-hidden holdout dry-run", render_randomized_target_hidden_holdout_dry_run_html(report))


def ready_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "randomized_target_hidden_holdout_suite_ready": True,
            "candidate_case_count": 4,
            "random_seed": 914,
            "randomized_case_factor": 2.0,
            "tokenizer_covered_case_count": 4,
            "target_hidden_case_count": 4,
            "task_hint_case_count": 0,
            "unique_prompt_count": 4,
        },
        "benchmark_suite": {
            "ready": True,
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": "randomized-target-hidden-01", "source_case_id": "source-a", "random_draw_index": 1},
                {"case_id": "randomized-target-hidden-02", "source_case_id": "source-b", "random_draw_index": 2},
                {"case_id": "randomized-target-hidden-03", "source_case_id": "source-c", "random_draw_index": 3},
                {"case_id": "randomized-target-hidden-04", "source_case_id": "source-d", "random_draw_index": 4},
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
