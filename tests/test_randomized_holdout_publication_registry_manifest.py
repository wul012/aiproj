from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_constants import RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY
from minigpt.randomized_holdout_publication_registry_manifest import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME,
    build_randomized_holdout_publication_registry_manifest,
    locate_randomized_holdout_publication_registry_packet,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_manifest_artifacts import (
    render_randomized_holdout_publication_registry_manifest_html,
    render_randomized_holdout_publication_registry_manifest_markdown,
    render_randomized_holdout_publication_registry_manifest_text,
    write_randomized_holdout_publication_registry_manifest_outputs,
)
from minigpt.randomized_holdout_publication_registry_packet import build_randomized_holdout_publication_registry_packet
from minigpt.randomized_holdout_publication_registry_packet_artifacts import write_randomized_holdout_publication_registry_packet_outputs
from scripts.build_randomized_holdout_publication_registry_manifest import main as cli_main
from tests.test_randomized_holdout_publication_registry_packet import ready_packet_inputs


class RandomizedHoldoutPublicationRegistryManifestTests(unittest.TestCase):
    def test_manifest_accepts_ready_registry_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_manifest_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_manifest(packet, registry_packet_path=packet_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_manifest_ready")
        self.assertEqual(report["failed_count"], 0)
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_manifest_ready"])
        self.assertEqual(report["summary"]["manifest_id"], "randomized-holdout-publication-registry-manifest-v932")
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["registry_status"], "registered")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["consumer_boundary"], RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY)
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_manifest")
        self.assertEqual(resolve_exit_code(report, require_manifest_ready=True, require_bounded_publication=True), 0)
        self.assertEqual(resolve_exit_code(report, require_manifest_ready=True, require_promotion_ready=True), 1)

    def test_manifest_fails_when_contract_check_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_manifest_inputs(Path(tmp))
            packet["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_manifest(packet, registry_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_manifest_fails_when_consumer_boundary_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, packet_path = ready_manifest_inputs(Path(tmp))
            packet["summary"]["consumer_boundary"] = "production_lookup"
            report = build_randomized_holdout_publication_registry_manifest(packet, registry_packet_path=packet_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("consumer_boundary_governance", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, packet_path = ready_manifest_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_packet(packet_path.parent), packet_path)
            report = build_randomized_holdout_publication_registry_manifest(packet, registry_packet_path=packet_path)
            outputs = write_randomized_holdout_publication_registry_manifest_outputs(report, root / "manifest")
            cli_main(
                [
                    "--registry-packet",
                    str(packet_path.parent),
                    "--out-dir",
                    str(root / "cli-manifest"),
                    "--require-manifest-ready",
                    "--require-bounded-publication",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_JSON_FILENAME))
        self.assertIn(
            "randomized_holdout_publication_registry_manifest_ready=True",
            render_randomized_holdout_publication_registry_manifest_text(report),
        )
        self.assertIn("review_randomized_holdout_publication_registry_manifest", render_randomized_holdout_publication_registry_manifest_markdown(report))
        self.assertIn("publication registry manifest", render_randomized_holdout_publication_registry_manifest_html(report))


def ready_manifest_inputs(root: Path) -> tuple[dict[str, object], Path]:
    entry, check, entry_path, check_path = ready_packet_inputs(root)
    packet = build_randomized_holdout_publication_registry_packet(
        entry,
        check,
        registry_entry_path=entry_path,
        registry_entry_check_path=check_path,
    )
    packet_outputs = write_randomized_holdout_publication_registry_packet_outputs(packet, root / "packet")
    return packet, Path(packet_outputs["json"])


if __name__ == "__main__":
    unittest.main()
