from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_lookup_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_packet,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet_artifacts import write_randomized_holdout_publication_registry_lookup_packet_outputs
from minigpt.randomized_holdout_publication_registry_lookup_packet_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_packet_check,
    locate_randomized_holdout_publication_registry_lookup_packet,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet_check_artifacts import (
    render_randomized_holdout_publication_registry_lookup_packet_check_html,
    render_randomized_holdout_publication_registry_lookup_packet_check_markdown,
    render_randomized_holdout_publication_registry_lookup_packet_check_text,
    write_randomized_holdout_publication_registry_lookup_packet_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_registry_lookup_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_lookup_packet import ready_lookup_inputs


class RandomizedHoldoutPublicationRegistryLookupPacketCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_lookup_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_lookup_packet_check(packet, lookup_packet_path=packet_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_lookup_packet_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_lookup_scope"], "governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_lookup_scope"], "governance_lookup_only")
        self.assertEqual(report["summary"]["original_rejected_use"], "production_promotion")
        self.assertEqual(report["summary"]["rebuilt_rejected_use"], "production_promotion")
        self.assertEqual(report["summary"]["original_promotion_ready"], False)
        self.assertEqual(report["summary"]["rebuilt_promotion_ready"], False)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_lookup_key_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["lookup_packet"]["lookup_keys"] = ["production:randomized-holdout-publication-v928"]
            packet["lookup_packet"]["lookup_entries"][0]["lookup_key"] = "production:randomized-holdout-publication-v928"
            report = build_randomized_holdout_publication_registry_lookup_packet_check(packet, lookup_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("lookup_packet.lookup_keys", ids)
        self.assertIn("lookup_packet.lookup_entries", ids)

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_check_inputs(Path(tmp))
            packet["registry_manifest_review_path"] = "missing-review.json"
            packet["lookup_packet"]["registry_manifest_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_lookup_packet_check(packet, lookup_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_manifest_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_lookup_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_check_inputs(root)
            packet["summary"]["rejected_use"] = "none"
            write_json_payload(packet, packet_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(packet_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_lookup_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_publication_registry_lookup_packet_check(packet, lookup_packet_path=packet_path)
            outputs = write_randomized_holdout_publication_registry_lookup_packet_check_outputs(report, root / "check")
            cli_main([str(packet_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_lookup_packet_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_lookup_packet_check_markdown(report))
        self.assertIn("lookup packet contract check", render_randomized_holdout_publication_registry_lookup_packet_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_lookup_inputs(root)
    packet = build_randomized_holdout_publication_registry_lookup_packet(review, registry_manifest_review_path=review_path)
    outputs = write_randomized_holdout_publication_registry_lookup_packet_outputs(packet, root / "lookup-packet")
    path = Path(outputs["json"])
    expected = root / "lookup-packet" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME
    assert path == expected
    return packet, path


if __name__ == "__main__":
    unittest.main()
