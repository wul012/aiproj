from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991,
    locate_receipt_index_review_v991,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_outputs
from minigpt.report_utils import write_json_payload
from scripts.publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v991 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990 import ready_review_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationV991Tests(unittest.TestCase):
    def test_receipt_index_publication_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready"])
        self.assertEqual(report["summary"]["publication_status"], "published_for_publication_receipt_index_receipt_index_lookup_only")
        self.assertEqual(report["summary"]["published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["receipt_index_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991")
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_promotion_ready=True), 1)

    def test_receipt_index_publication_fails_when_review_status_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["summary"]["review_status"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("review_status_publishable", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_publication_fails_when_source_receipt_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["review"]["source_receipt_path"] = str(Path(tmp) / "missing-receipt.json")
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_file_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_publication_ready_returns_one_on_tampered_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_publication_inputs(root)
            review["summary"]["allowed_use"] = "production_promotion"
            write_json_payload(review, review_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(review_path.parent), "--out-dir", str(root / "cli-publication"), "--require-publication-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-publication" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_publication_inputs(root)
            self.assertEqual(locate_receipt_index_review_v991(review_path.parent), review_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991(
                review,
                receipt_index_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_outputs(report, root / "publication")
            cli_main([str(review_path.parent), "--out-dir", str(root / "cli-publication"), "--require-publication-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_V991_JSON_FILENAME))
        self.assertIn("publication_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_text(report))
        self.assertIn("Publication", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_markdown(report))
        self.assertIn("receipt index", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_html(report))


def ready_publication_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990(
        index,
        receipt_index_path=index_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_outputs(review, root / "receipt-index-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
