from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_acceptance_summary import (
    RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME,
    build_randomized_holdout_acceptance_summary,
    locate_randomized_holdout_decision_index,
    resolve_exit_code,
)
from minigpt.randomized_holdout_acceptance_summary_artifacts import (
    render_randomized_holdout_acceptance_summary_html,
    render_randomized_holdout_acceptance_summary_markdown,
    render_randomized_holdout_acceptance_summary_text,
    write_randomized_holdout_acceptance_summary_outputs,
)
from minigpt.randomized_holdout_decision_index import RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME, build_randomized_holdout_decision_index
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_acceptance_summary import main as cli_main
from tests.test_randomized_holdout_decision_index import ready_index_inputs


class RandomizedHoldoutAcceptanceSummaryTests(unittest.TestCase):
    def test_summarizes_bounded_acceptance_without_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_summary_inputs(Path(tmp))
            report = build_randomized_holdout_acceptance_summary(index, decision_index_path=index_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_acceptance_summary_ready")
        self.assertTrue(report["summary"]["randomized_holdout_acceptance_summary_ready"])
        self.assertTrue(report["summary"]["bounded_promotion_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["accepted_claim_count"], 1)
        self.assertEqual(report["summary"]["blocked_claim_count"], 3)
        self.assertEqual(report["summary"]["allowed_use"], "bounded_model_capability_governance_only")
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_acceptance_summary_contract")
        self.assertEqual(resolve_exit_code(report, require_summary_ready=True, require_bounded_acceptance=True), 0)
        self.assertEqual(resolve_exit_code(report, require_summary_ready=True, require_promotion_ready=True), 1)

    def test_blocks_when_index_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_summary_inputs(Path(tmp))
            index["summary"]["randomized_holdout_decision_index_ready"] = False
            report = build_randomized_holdout_acceptance_summary(index, decision_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("summary_ready", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["allowed_use"], "none")

    def test_blocks_when_source_row_widens_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_summary_inputs(Path(tmp))
            index["source_rows"][0]["promotion_ready"] = True
            report = build_randomized_holdout_acceptance_summary(index, decision_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_rows_block_promotion", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_summary_inputs(root)
            self.assertEqual(locate_randomized_holdout_decision_index(index_path.parent), index_path)
            report = build_randomized_holdout_acceptance_summary(index, decision_index_path=index_path)
            outputs = write_randomized_holdout_acceptance_summary_outputs(report, root / "summary")
            cli_main(
                [
                    "--decision-index",
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-summary"),
                    "--require-summary-ready",
                    "--require-bounded-acceptance",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_ACCEPTANCE_SUMMARY_JSON_FILENAME))
        self.assertIn("randomized_holdout_acceptance_summary_ready=True", render_randomized_holdout_acceptance_summary_text(report))
        self.assertIn("Blocked Claims", render_randomized_holdout_acceptance_summary_markdown(report))
        self.assertIn("randomized holdout acceptance summary", render_randomized_holdout_acceptance_summary_html(report))


def ready_summary_inputs(root: Path) -> tuple[dict[str, object], Path]:
    decision, gate, review, packet, decision_path, gate_path, review_path, packet_path = ready_index_inputs(root / "index-source")
    index = build_randomized_holdout_decision_index(
        decision,
        gate,
        review,
        packet,
        bounded_decision_path=decision_path,
        bounded_gate_path=gate_path,
        candidate_packet_review_path=review_path,
        candidate_packet_path=packet_path,
    )
    index_path = root / "decision-index" / RANDOMIZED_HOLDOUT_DECISION_INDEX_JSON_FILENAME
    write_json_payload(index, index_path)
    return index, index_path


if __name__ == "__main__":
    unittest.main()
