from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.registry_ack_pub import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication
from minigpt.registry_ack_pub_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_outputs
from minigpt.registry_ack_pub_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication,
    resolve_exit_code,
)
from minigpt.registry_ack_pub_check_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_registry_ack_pub import main as cli_main
from tests.test_registry_ack_pub import ready_publication_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_publication_status"], "published_for_downstream_receipt_packet_index_publication_receipt_packet_index_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_publication_status"], "published_for_downstream_receipt_packet_index_publication_receipt_packet_index_lookup_only")
        self.assertEqual(report["summary"]["original_published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["original_receipt_packet_index_row_count"], 1)
        self.assertEqual(report["summary"]["rebuilt_receipt_packet_index_row_count"], 1)
        self.assertFalse(report["summary"]["original_promotion_ready"])
        self.assertFalse(report["summary"]["rebuilt_promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_publication_use_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            publication["summary"]["published_use"] = "production_promotion"
            publication["publication"]["published_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("summary.published_use", ids)
        self.assertIn("publication.published_use", ids)

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            publication["receipt_packet_index_review_path"] = "missing-review.json"
            publication["publication"]["receipt_packet_index_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_packet_index_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path = ready_check_inputs(root)
            publication["summary"]["published_use"] = "production_promotion"
            write_json_payload(publication, publication_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(publication_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication(publication_path.parent), publication_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check(
                publication,
                publication_path=publication_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_outputs(report, root / "check")
            cli_main([str(publication_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_markdown(report))
        self.assertIn("publication contract check", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_publication_inputs(root)
    publication = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication(
        review,
        receipt_packet_index_review_path=review_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_outputs(publication, root / "publication")
    return publication, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
