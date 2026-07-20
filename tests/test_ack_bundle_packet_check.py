from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.ack_bundle_packet import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet
from minigpt.ack_bundle_packet_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_outputs
from minigpt.ack_bundle_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet,
    resolve_exit_code,
)
from minigpt.ack_bundle_packet_check_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_ack_bundle_packet import main as build_cli_main
from scripts.check_ack_bundle_packet import main as cli_main
from tests.test_ack_bundle_packet import ready_packet_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationReceiptPacketCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_receipt_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
                packet,
                receipt_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_packet_status"], "downstream_receipt_packet_index_publication_receipt_packet_ready")
        self.assertEqual(report["summary"]["rebuilt_packet_status"], "downstream_receipt_packet_index_publication_receipt_packet_ready")
        self.assertEqual(report["summary"]["original_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["original_source_evidence_count"], 2)
        self.assertEqual(report["summary"]["rebuilt_source_evidence_count"], 2)
        self.assertEqual(report["summary"]["original_consumer_receipt_count"], 1)
        self.assertEqual(report["summary"]["rebuilt_consumer_receipt_count"], 1)
        self.assertEqual(report["summary"]["original_promotion_ready"], False)
        self.assertEqual(report["summary"]["rebuilt_promotion_ready"], False)
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)
        self.assertEqual(resolve_exit_code(report, require_pass=True, require_promotion_ready=True), 1)

    def test_contract_check_fails_when_packet_source_path_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["packet"]["source_review_path"] = str(Path(tmp) / "drifted-source-review.json")
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
                packet,
                receipt_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("packet.source_review_path", [issue["id"] for issue in report["issues"]])

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["receipt_review_path"] = "missing-review.json"
            packet["packet"]["receipt_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
                packet,
                receipt_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_check_inputs(root)
            packet["summary"]["granted_use"] = "production_promotion"
            write_json_payload(packet, packet_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(packet_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
                packet,
                receipt_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_outputs(report, root / "check")
            cli_main([str(packet_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_markdown(report))
        self.assertIn("receipt packet contract check", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_html(report))

    def test_builder_cli_can_write_sidecar_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, review_path = ready_packet_inputs(root)
            build_cli_main(
                [
                    "--receipt-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "packet"),
                    "--check-out-dir",
                    str(root / "packet-check"),
                    "--require-packet-ready",
                    "--force",
                ]
            )
            self.assertTrue((root / "packet-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_CHECK_JSON_FILENAME).is_file())


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_packet_inputs(root)
    packet = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(review, receipt_review_path=review_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_outputs(packet, root / "receipt-packet")
    return packet, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
