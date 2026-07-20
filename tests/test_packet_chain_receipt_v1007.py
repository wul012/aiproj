from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.packet_chain_receipt_v1007 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1007_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007,
    locate_receipt_index_review_v1007,
    read_json_report,
    resolve_exit_code,
)
from minigpt.packet_chain_receipt_v1007_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_outputs,
)
from minigpt.packet_chain_review_v1006 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006
from minigpt.packet_chain_review_v1006_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006_outputs
from minigpt.report_utils import write_json_payload
from scripts.record_packet_chain_receipt_v1007 import main as cli_main
from tests.test_packet_chain_review_v1006 import ready_review_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationIndexReceiptIndexReceiptIndexReceiptV1007Tests(unittest.TestCase):
    def test_receipt_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_ready"])
        self.assertEqual(report["summary"]["receipt_status"], "publication_index_receipt_index_receipt_index_receipt_index_lookup_receipted")
        self.assertEqual(report["summary"]["consumer_name"], "publication_index_receipt_index_receipt_index_receipt_index_governance_lookup_reader")
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007")
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True, require_promotion_ready=True), 1)

    def test_receipt_fails_when_requested_use_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007(
                review,
                receipt_index_review_path=review_path,
                requested_use="production_promotion",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_use_allowed", [issue["id"] for issue in report["issues"]])

    def test_receipt_fails_when_source_receipt_index_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            review["review"]["receipt_index_path"] = str(Path(tmp) / "missing-receipt-index.json")
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_index_file_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_receipt_ready_returns_one_on_bad_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_receipt_inputs(root)
            review["summary"]["receipt_index_ready"] = False
            write_json_payload(review, review_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(review_path.parent), "--out-dir", str(root / "cli-receipt"), "--require-receipt-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-receipt" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1007_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_receipt_inputs(root)
            self.assertEqual(locate_receipt_index_review_v1007(review_path.parent), review_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007(
                review,
                receipt_index_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_outputs(report, root / "receipt")
            cli_main([str(review_path.parent), "--out-dir", str(root / "cli-receipt"), "--require-receipt-ready", "--force"])
            cli_report = read_json_report(root / "cli-receipt" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1007_JSON_FILENAME)

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1007_JSON_FILENAME))
        self.assertEqual(cli_report["summary"]["consumer_name"], "publication_index_receipt_index_receipt_index_receipt_index_governance_lookup_reader")
        self.assertIn("receipt_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_text(report))
        self.assertIn("Consumer Receipts", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_markdown(report))
        self.assertIn("receipt", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_html(report))


def ready_receipt_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006(
        index,
        receipt_index_path=index_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006_outputs(review, root / "receipt-index-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
