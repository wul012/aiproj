from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketTests(unittest.TestCase):
    def test_publication_receipt_packet_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_ready"])
        self.assertEqual(report["summary"]["packet_status"], "downstream_publication_receipt_packet_ready")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["publication_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["consumer_receipt_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertIn("production_promotion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet")
        self.assertEqual(len(report["receipt_review_sha256"]), 64)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_publication_receipt_packet_fails_when_review_grants_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            review["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_publication_receipt_packet_fails_when_lookup_key_namespace_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            review["review"]["lookup_keys"] = ["model:randomized-holdout-publication-v928"]
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_keys_publication_namespace", [issue["id"] for issue in report["issues"]])

    def test_publication_receipt_packet_fails_when_source_publication_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            review["review"]["source_publication_path"] = str(Path(tmp) / "missing-publication.json")
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_publication_file_exists", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_packet_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet(review, receipt_review_path=review_path)
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_outputs(report, root / "receipt-packet")
            cli_main(
                [
                    "--receipt-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-packet"),
                    "--require-packet-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_text(report))
        self.assertIn("downstream_publication_receipt_packet_ready", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_markdown(report))
        self.assertIn("publication receipt packet", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_html(report))


def ready_packet_inputs(root: Path) -> tuple[dict[str, object], Path]:
    receipt, receipt_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review(
        receipt,
        publication_receipt_path=receipt_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_outputs(review, root / "publication-receipt-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
