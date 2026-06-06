from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_summary import RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME, build_randomized_holdout_acceptance_summary
from minigpt.randomized_holdout_acceptance_summary_check import (
    RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME,
    build_randomized_holdout_acceptance_summary_check,
    locate_randomized_holdout_acceptance_summary,
    resolve_exit_code,
)
from minigpt.randomized_holdout_acceptance_summary_check_artifacts import (
    render_randomized_holdout_acceptance_summary_check_html,
    render_randomized_holdout_acceptance_summary_check_markdown,
    render_randomized_holdout_acceptance_summary_check_text,
    write_randomized_holdout_acceptance_summary_check_outputs,
)
from minigpt.randomized_holdout_acceptance_summary_artifacts import write_randomized_holdout_acceptance_summary_outputs
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_acceptance_summary import main as cli_main
from tests.test_randomized_holdout_acceptance_summary import ready_summary_inputs


class RandomizedHoldoutAcceptanceSummaryCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, summary_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_acceptance_summary_check(summary, acceptance_summary_path=summary_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_acceptance_summary_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_accepted_claim_count"], 1)
        self.assertEqual(report["summary"]["rebuilt_accepted_claim_count"], 1)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_accepted_claim_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, summary_path = ready_check_inputs(Path(tmp))
            summary["accepted_claims"][0]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_acceptance_summary_check(summary, acceptance_summary_path=summary_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("accepted_claims", [issue["id"] for issue in report["issues"]])
        self.assertEqual(resolve_exit_code(report, require_pass=True), 1)

    def test_contract_check_fails_when_source_index_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary, summary_path = ready_check_inputs(Path(tmp))
            summary["source_decision_index"] = "missing-index.json"
            report = build_randomized_holdout_acceptance_summary_check(summary, acceptance_summary_path=summary_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_decision_index_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary, summary_path = ready_check_inputs(root)
            summary["blocked_claims"][0]["reason"] = "changed"
            write_json_payload(summary, summary_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(summary_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary, summary_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_acceptance_summary(summary_path.parent), summary_path)
            report = build_randomized_holdout_acceptance_summary_check(summary, acceptance_summary_path=summary_path)
            outputs = write_randomized_holdout_acceptance_summary_check_outputs(report, root / "check")
            cli_main([str(summary_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_acceptance_summary_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_acceptance_summary_check_markdown(report))
        self.assertIn("contract check", render_randomized_holdout_acceptance_summary_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_summary_inputs(root / "summary-source")
    summary = build_randomized_holdout_acceptance_summary(index, decision_index_path=index_path)
    out_dir = root / "summary"
    outputs = write_randomized_holdout_acceptance_summary_outputs(summary, out_dir)
    path = Path(outputs["json"])
    self_written = out_dir / RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME
    assert path == self_written
    return summary, path


if __name__ == "__main__":
    unittest.main()
