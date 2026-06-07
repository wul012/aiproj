from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_index,
    locate_randomized_holdout_publication_registry_downstream_consumer_packet,
    locate_randomized_holdout_publication_registry_downstream_consumer_packet_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_index_html,
    render_randomized_holdout_publication_registry_downstream_consumer_index_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_index_text,
    write_randomized_holdout_publication_registry_downstream_consumer_index_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_check import build_randomized_holdout_publication_registry_downstream_consumer_packet_check
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_check_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_packet_check_outputs
from minigpt.report_utils import write_json_payload
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_index import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_packet_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerIndexTests(unittest.TestCase):
    def test_consumer_index_accepts_packet_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_index(
                packet,
                check,
                consumer_packet_path=packet_path,
                consumer_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_index_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertIn("training_data_claim_expansion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_downstream_consumer_index")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_consumer_index_fails_when_contract_check_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_downstream_consumer_index(
                packet,
                check,
                consumer_packet_path=packet_path,
                consumer_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("consumer_packet_check_passed", ids)
        self.assertIn("contract_check_ready", ids)

    def test_consumer_index_fails_when_lookup_keys_drift_from_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path, check, check_path = ready_index_inputs(Path(tmp))
            packet["packet"]["lookup_keys"] = ["model:randomized-holdout-publication-v928"]
            report = build_randomized_holdout_publication_registry_downstream_consumer_index(
                packet,
                check,
                consumer_packet_path=packet_path,
                consumer_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_keys_match_check", [issue["id"] for issue in report["issues"]])

    def test_cli_require_index_ready_returns_one_on_tampered_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path, _check, check_path = ready_index_inputs(root)
            packet["summary"]["granted_use"] = "production_promotion"
            write_json_payload(packet, packet_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "--consumer-packet",
                        str(packet_path.parent),
                        "--consumer-packet-check",
                        str(check_path.parent),
                        "--out-dir",
                        str(root / "cli-index"),
                        "--require-index-ready",
                        "--force",
                    ]
                )

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-index" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_packet(packet_path.parent), packet_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_packet_check(check_path.parent), check_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_index(
                packet,
                check,
                consumer_packet_path=packet_path,
                consumer_packet_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_index_outputs(report, root / "index")
            cli_main(
                [
                    "--consumer-packet",
                    str(packet_path.parent),
                    "--consumer-packet-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_index_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_index_text(report))
        self.assertIn("Source Evidence", render_randomized_holdout_publication_registry_downstream_consumer_index_markdown(report))
        self.assertIn("downstream consumer index", render_randomized_holdout_publication_registry_downstream_consumer_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    packet, packet_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_registry_downstream_consumer_packet_check(packet, consumer_packet_path=packet_path)
    check_outputs = write_randomized_holdout_publication_registry_downstream_consumer_packet_check_outputs(check, root / "consumer-packet-check")
    return packet, packet_path, check, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
