from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationReceiptPacketIndexTests(unittest.TestCase):
    def test_receipt_packet_index_accepts_packet_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
                packet,
                check,
                receipt_packet_path=packet_path,
                receipt_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready"])
        self.assertEqual(report["summary"]["receipt_packet_index_row_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_receipt_packet_index_fails_when_contract_check_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
                packet,
                check,
                receipt_packet_path=packet_path,
                receipt_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("receipt_packet_check_passed", ids)
        self.assertIn("contract_check_ready", ids)

    def test_receipt_packet_index_fails_when_source_review_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            packet["packet"]["source_review_path"] = str(Path(tmp) / "missing-source-review.json")
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
                packet,
                check,
                receipt_packet_path=packet_path,
                receipt_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_review_file_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_index_ready_returns_one_on_tampered_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path, _check, check_path = ready_index_inputs(root)
            packet["summary"]["granted_use"] = "production_promotion"
            write_json_payload(packet, packet_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "--receipt-packet",
                        str(packet_path.parent),
                        "--receipt-packet-check",
                        str(check_path.parent),
                        "--out-dir",
                        str(root / "cli-index"),
                        "--require-index-ready",
                        "--force",
                    ]
                )

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-index" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet(packet_path.parent), packet_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(check_path.parent), check_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index(
                packet,
                check,
                receipt_packet_path=packet_path,
                receipt_packet_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_outputs(report, root / "index")
            cli_main(
                [
                    "--receipt-packet",
                    str(packet_path.parent),
                    "--receipt-packet-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_text(report))
        self.assertIn("Source Evidence", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_markdown(report))
        self.assertIn("receipt packet index", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    packet, packet_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check(
        packet,
        receipt_packet_path=packet_path,
    )
    check_outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check_outputs(check, root / "receipt-packet-check")
    return packet, packet_path, check, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
