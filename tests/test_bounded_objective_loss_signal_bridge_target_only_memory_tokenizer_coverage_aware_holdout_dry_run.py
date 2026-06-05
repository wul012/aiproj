from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME,
    build_tokenizer_coverage_aware_holdout_dry_run,
    locate_tokenizer_coverage_aware_holdout_suite,
    resolve_exit_code,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_artifacts import (
    render_tokenizer_coverage_aware_holdout_dry_run_html,
    render_tokenizer_coverage_aware_holdout_dry_run_markdown,
    render_tokenizer_coverage_aware_holdout_dry_run_text,
    write_tokenizer_coverage_aware_holdout_dry_run_outputs,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite import (
    TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME,
)
from minigpt.report_utils import write_json_payload
from scripts.dry_run_bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout import main as cli_main


class TokenizerCoverageAwareHoldoutDryRunTests(unittest.TestCase):
    def test_dry_run_passes_positive_and_blocks_negative_control(self) -> None:
        report = build_tokenizer_coverage_aware_holdout_dry_run(ready_suite())

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_passed")
        self.assertTrue(report["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_dry_run_ready"])
        self.assertEqual(report["summary"]["positive_passed_case_count"], 2)
        self.assertEqual(report["summary"]["negative_passed_case_count"], 0)
        self.assertFalse(report["summary"]["negative_control_passed"])
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 0)

    def test_dry_run_fails_when_negative_control_passes(self) -> None:
        report = build_tokenizer_coverage_aware_holdout_dry_run(ready_suite(), negative_continuation=" fixed loss")

        self.assertEqual(report["status"], "fail")
        self.assertIn("negative_rows_fail", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_dry_run_ready=True), 1)

    def test_dry_run_fails_when_source_suite_not_ready(self) -> None:
        source = ready_suite()
        source["summary"]["bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready"] = False
        report = build_tokenizer_coverage_aware_holdout_dry_run(source)

        self.assertEqual(report["status"], "fail")
        self.assertIn("holdout_suite_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_path = root / "suite" / TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_SUITE_JSON_FILENAME
            write_json_payload(ready_suite(), suite_path)
            self.assertEqual(locate_tokenizer_coverage_aware_holdout_suite(suite_path.parent), suite_path)
            report = build_tokenizer_coverage_aware_holdout_dry_run(ready_suite())
            outputs = write_tokenizer_coverage_aware_holdout_dry_run_outputs(report, root / "out")
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
        self.assertTrue(outputs["json"].endswith(TARGET_ONLY_MEMORY_TOKENIZER_COVERAGE_AWARE_HOLDOUT_DRY_RUN_JSON_FILENAME))
        self.assertIn("positive_passed_case_count=2", render_tokenizer_coverage_aware_holdout_dry_run_text(report))
        self.assertIn("Dry-Run Rows", render_tokenizer_coverage_aware_holdout_dry_run_markdown(report))
        self.assertIn("holdout dry-run", render_tokenizer_coverage_aware_holdout_dry_run_html(report))


def ready_suite() -> dict[str, object]:
    return {
        "status": "pass",
        "summary": {
            "bounded_objective_loss_signal_bridge_target_only_memory_tokenizer_coverage_aware_holdout_suite_ready": True,
        },
        "benchmark_suite": {
            "ready": True,
            "scoring_contract": {"expected_terms": ["fixed", "loss"]},
            "cases": [
                {"case_id": "case-a", "source_case_id": "source-a"},
                {"case_id": "case-b", "source_case_id": "source-b"},
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
