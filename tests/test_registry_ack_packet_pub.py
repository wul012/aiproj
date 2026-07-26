from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.registry_ack_packet_pub import (
    ACK_PACKET_PUB_JSON_FILENAME,
    build_ack_packet_pub,
    locate_ack_packet_pub,
    resolve_exit_code,
)
from minigpt.registry_ack_packet_pub_artifacts import (
    render_ack_packet_pub_artifacts_html,
    render_ack_packet_pub_artifacts_markdown,
    render_ack_packet_pub_artifacts_text,
    write_ack_packet_pub_artifacts_outputs,
)
from minigpt.registry_ack_packet_review import build_ack_packet_review
from minigpt.registry_ack_packet_review_artifacts import write_p_et_review_artifacts_outputs
from scripts.build_registry_ack_packet_pub import main as cli_main
from tests.test_registry_ack_packet_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationReceiptPacketIndexPublicationTests(unittest.TestCase):
    def test_receipt_packet_index_publication_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            report = build_ack_packet_pub(
                review,
                receipt_packet_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready"])
        self.assertEqual(report["summary"]["publication_status"], "published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only")
        self.assertTrue(report["summary"]["publish_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertEqual(report["summary"]["published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["receipt_packet_index_row_count"], 1)
        self.assertEqual(report["summary"]["source_packet_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication")
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_promotion_ready=True), 1)

    def test_receipt_packet_index_publication_fails_when_review_not_publish_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["summary"]["publish_ready"] = False
            report = build_ack_packet_pub(
                review,
                receipt_packet_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("publish_ready", [issue["id"] for issue in report["issues"]])

    def test_receipt_packet_index_publication_fails_when_index_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["review"]["receipt_packet_index_path"] = "missing-index.json"
            report = build_ack_packet_pub(
                review,
                receipt_packet_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("receipt_packet_index_file_exists", [issue["id"] for issue in report["issues"]])

    def test_receipt_packet_index_publication_fails_when_allowed_use_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["summary"]["allowed_use"] = "production_promotion"
            report = build_ack_packet_pub(
                review,
                receipt_packet_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_publication_inputs(root)
            self.assertEqual(locate_ack_packet_pub(review_path.parent), review_path)
            report = build_ack_packet_pub(
                review,
                receipt_packet_index_review_path=review_path,
            )
            outputs = write_ack_packet_pub_artifacts_outputs(report, root / "publication")
            cli_main([str(review_path.parent), "--out-dir", str(root / "cli-publication"), "--require-publication-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(ACK_PACKET_PUB_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready=True", render_ack_packet_pub_artifacts_text(report))
        self.assertIn("Receipt packet index", render_ack_packet_pub_artifacts_markdown(report))
        self.assertIn("receipt packet index publication", render_ack_packet_pub_artifacts_html(report))


def ready_publication_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_ack_packet_review(
        index,
        receipt_packet_index_path=index_path,
    )
    outputs = write_p_et_review_artifacts_outputs(review, root / "receipt-packet-index-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
