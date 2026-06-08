from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998,
    locate_receipt_index_v998,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_outputs
from minigpt.report_utils import write_json_payload
from scripts.review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v998 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997 import ready_index_inputs as ready_receipt_index_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationIndexReceiptIndexReviewV998Tests(unittest.TestCase):
    def test_receipt_index_review_accepts_ready_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_publication_index_receipt_index_receipt_lookup_only")
        self.assertTrue(report["summary"]["receipt_index_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v998")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_receipt_index_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_receipt_index_review_fails_on_bad_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["receipt_index"]["source_evidence_rows"][0]["sha256"] = "bad"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_evidence_digests", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_review_fails_when_lookup_scope_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["summary"]["lookup_scope"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_scope_downstream", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_review_fails_when_body_and_row_paths_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["receipt_index"]["receipt_index_rows"][0]["source_receipt_path"] = str(Path(tmp) / "different-receipt.json")
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_paths_match_rows", [issue["id"] for issue in report["issues"]])

    def test_cli_require_review_ready_returns_one_on_tampered_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            index["summary"]["lookup_scope"] = "production_promotion"
            write_json_payload(index, index_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(index_path.parent), "--out-dir", str(root / "cli-review"), "--require-review-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-review" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            self.assertEqual(locate_receipt_index_v998(index_path.parent), index_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998(
                index,
                receipt_index_path=index_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_outputs(report, root / "review")
            cli_main([str(index_path.parent), "--out-dir", str(root / "cli-review"), "--require-review-ready", "--require-receipt-index-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_REVIEW_V998_JSON_FILENAME))
        self.assertIn("review_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_text(report))
        self.assertIn("Review", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_markdown(report))
        self.assertIn("receipt index", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    receipt, receipt_path, check, check_path = ready_receipt_index_inputs(root)
    index = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997(
        receipt,
        check,
        receipt_path=receipt_path,
        receipt_check_path=check_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_outputs(index, root / "receipt-index")
    return index, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
