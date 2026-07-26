from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.registry_ack_pub_receipt import build_ack_pub_receipt
from minigpt.registry_ack_pub_receipt_artifacts import write_pub_receipt_artifacts_outputs
from minigpt.registry_ack_receipt_review import (
    ACK_RECEIPT_REVIEW_JSON_FILENAME,
    build_ack_receipt_review,
    locate_ack_receipt_review,
    resolve_exit_code,
)
from minigpt.registry_ack_receipt_review_artifacts import (
    render_receipt_review_artifacts_html,
    render_receipt_review_artifacts_markdown,
    render_receipt_review_artifacts_text,
    write_receipt_review_artifacts_outputs,
)
from scripts.review_registry_ack_pub_receipt import main as cli_main
from tests.test_registry_ack_pub_receipt import ready_receipt_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationReceiptReviewTests(unittest.TestCase):
    def test_publication_receipt_review_accepts_ready_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            report = build_ack_receipt_review(
                receipt,
                publication_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet")
        self.assertTrue(report["summary"]["packet_ready"])
        self.assertEqual(report["summary"]["receipt_status"], "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted")
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["publication_index_row_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["consumer_receipt_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "build_registry_ack_packet")
        self.assertEqual(len(report["publication_receipt_sha256"]), 64)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_packet_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_publication_receipt_review_fails_when_granted_use_expands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            report = build_ack_receipt_review(
                receipt,
                publication_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_publication_receipt_review_fails_when_source_index_digest_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            receipt["index_review_sha256"] = "0" * 64
            report = build_ack_receipt_review(
                receipt,
                publication_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_index_review_digest_matches", [issue["id"] for issue in report["issues"]])

    def test_publication_receipt_review_fails_when_source_index_review_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            receipt["receipt"]["index_review_path"] = str(Path(tmp) / "missing.json")
            report = build_ack_receipt_review(
                receipt,
                publication_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_index_review_file_exists", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_review_inputs(root)
            self.assertEqual(locate_ack_receipt_review(receipt_path.parent), receipt_path)
            report = build_ack_receipt_review(receipt, publication_receipt_path=receipt_path)
            outputs = write_receipt_review_artifacts_outputs(report, root / "receipt-review")
            cli_main(
                [
                    "--receipt",
                    str(receipt_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-packet-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(ACK_RECEIPT_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_ready=True", render_receipt_review_artifacts_text(report))
        self.assertIn("approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet", render_receipt_review_artifacts_markdown(report))
        self.assertIn("publication receipt packet index publication receipt review", render_receipt_review_artifacts_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index_review, index_review_path = ready_receipt_inputs(root)
    receipt = build_ack_pub_receipt(
        index_review,
        index_review_path=index_review_path,
    )
    outputs = write_pub_receipt_artifacts_outputs(receipt, root / "publication-receipt")
    return receipt, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
