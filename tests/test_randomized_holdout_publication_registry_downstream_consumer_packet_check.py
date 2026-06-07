from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet import build_randomized_holdout_publication_registry_downstream_consumer_packet
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_packet_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_packet_check,
    locate_randomized_holdout_publication_registry_downstream_consumer_packet,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_check_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_packet_check_html,
    render_randomized_holdout_publication_registry_downstream_consumer_packet_check_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_packet_check_text,
    write_randomized_holdout_publication_registry_downstream_consumer_packet_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_registry_downstream_consumer_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_packet import ready_packet_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerPacketCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_consumer_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet_check(
                packet,
                consumer_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_packet_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_packet_status"], "downstream_consumer_packet_ready")
        self.assertEqual(report["summary"]["rebuilt_packet_status"], "downstream_consumer_packet_ready")
        self.assertEqual(report["summary"]["original_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["original_promotion_ready"], False)
        self.assertEqual(report["summary"]["rebuilt_promotion_ready"], False)
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_registry_downstream_consumer_packet")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_packet_lookup_key_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["packet"]["lookup_keys"] = ["model:randomized-holdout-publication-v928"]
            packet["packet_rows"][0]["lookup_key"] = "model:randomized-holdout-publication-v928"
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet_check(
                packet,
                consumer_packet_path=packet_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("packet.lookup_keys", ids)
        self.assertIn("packet_rows", ids)

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["receipt_review_path"] = "missing-review.json"
            packet["packet"]["receipt_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet_check(
                packet,
                consumer_packet_path=packet_path,
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
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet_check(
                packet,
                consumer_packet_path=packet_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_packet_check_outputs(report, root / "check")
            cli_main([str(packet_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_packet_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_downstream_consumer_packet_check_markdown(report))
        self.assertIn("consumer packet contract check", render_randomized_holdout_publication_registry_downstream_consumer_packet_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_packet_inputs(root)
    packet = build_randomized_holdout_publication_registry_downstream_consumer_packet(review, receipt_review_path=review_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_packet_outputs(packet, root / "consumer-packet")
    return packet, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
