from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.report_utils import write_json_payload
from minigpt.target_hidden_semantic_holdout_dry_run import (
    TARGET_HIDDEN_SEMANTIC_HOLDOUT_DRY_RUN_JSON_FILENAME,
    build_target_hidden_semantic_holdout_dry_run,
    locate_target_hidden_semantic_holdout_suite,
    resolve_exit_code,
)
from minigpt.target_hidden_semantic_holdout_dry_run_artifacts import (
    render_target_hidden_semantic_holdout_dry_run_html,
    render_target_hidden_semantic_holdout_dry_run_markdown,
    render_target_hidden_semantic_holdout_dry_run_text,
    write_target_hidden_semantic_holdout_dry_run_outputs,
)
from minigpt.target_hidden_semantic_holdout_suite import TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
from scripts.dry_run_target_hidden_semantic_holdout import main as cli_main


class TargetHiddenSemanticHoldoutDryRunTests(unittest.TestCase):
    def test_dry_run_passes_positive_and_blocks_negative_control(self) -> None:
        report = build_target_hidden_semantic_holdout_dry_run(ready_suite())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "target_hidden_semantic_holdout_dry_run_passed")
        self.assertTrue(report["summary"]["target_hidden_semantic_holdout_dry_run_ready"])
        self.assertEqual(report["summary"]["positive_passed_case_count"], 2)
        self.assertEqual(report["summary"]["negative_passed_case_count"], 0)
        self.assertFalse(report["summary"]["negative_control_passed"])
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 0)

    def test_dry_run_fails_when_negative_control_passes(self) -> None:
        report = build_target_hidden_semantic_holdout_dry_run(ready_suite(), negative_continuation=" fixed loss")

        self.assertEqual(report["status"], "fail")
        self.assertIn("negative_rows_fail", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 1)

    def test_dry_run_fails_when_source_has_task_hints(self) -> None:
        source = ready_suite()
        source["summary"]["task_hint_case_count"] = 2
        report = build_target_hidden_semantic_holdout_dry_run(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("semantic_no_task_hints", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = root / "suite" / TARGET_HIDDEN_SEMANTIC_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(ready_suite(), suite_path)
            self.assertEqual(locate_target_hidden_semantic_holdout_suite(suite_path.parent), suite_path)
            report = build_target_hidden_semantic_holdout_dry_run(ready_suite())
            outputs = write_target_hidden_semantic_holdout_dry_run_outputs(report, root / "out")
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
        self.assertTrue(outputs["json"].endswith(TARGET_HIDDEN_SEMANTIC_HOLDOUT_DRY_RUN_JSON_FILENAME))
        self.assertIn("positive_passed_case_count=2", render_target_hidden_semantic_holdout_dry_run_text(report))
        self.assertIn("Dry-Run Rows", render_target_hidden_semantic_holdout_dry_run_markdown(report))
        self.assertIn("target-hidden semantic paraphrase holdout dry-run", render_target_hidden_semantic_holdout_dry_run_html(report))


def ready_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "target_hidden_semantic_holdout_suite_ready": True,
            "task_hint_case_count": 0,
        },
        "benchmark_suite": {
            "ready": True,
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": "semantic-hidden-case-a", "source_case_id": "source-a"},
                {"case_id": "semantic-hidden-case-b", "source_case_id": "source-b"},
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
