from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_outputs,
)
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptTests(unittest.TestCase):
    def test_publication_receipt_accepts_index_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt(
                review,
                index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready"])
        self.assertEqual(report["summary"]["receipt_status"], "downstream_publication_lookup_receipted")
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["publication_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt")
        self.assertEqual(len(report["index_review_sha256"]), 64)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True, require_promotion_ready=True), 1)

    def test_publication_receipt_rejects_promotion_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt(
                review,
                index_review_path=review_path,
                requested_use="production_promotion",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_use_allowed", [issue["id"] for issue in report["issues"]])

    def test_publication_receipt_rejects_missing_publication_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            review["publication_rows"] = []
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt(
                review,
                index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("publication_rows_present", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_receipt_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt(review, index_review_path=review_path)
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_outputs(report, root / "receipt")
            cli_main(
                [
                    "--index-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-receipt"),
                    "--require-receipt-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_text(report))
        self.assertIn("downstream_publication_lookup_receipted", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_markdown(report))
        self.assertIn("publication receipt", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_html(report))


def ready_receipt_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review(
        index,
        publication_index_path=index_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_outputs(review, root / "publication-index-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
