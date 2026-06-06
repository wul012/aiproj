from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_entry_check import build_randomized_holdout_publication_registry_entry_check
from minigpt.randomized_holdout_publication_registry_entry_check_artifacts import write_randomized_holdout_publication_registry_entry_check_outputs
from minigpt.randomized_holdout_publication_registry_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_packet,
    locate_randomized_holdout_publication_registry_entry,
    locate_randomized_holdout_publication_registry_entry_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_packet_artifacts import (
    render_randomized_holdout_publication_registry_packet_html,
    render_randomized_holdout_publication_registry_packet_markdown,
    render_randomized_holdout_publication_registry_packet_text,
    write_randomized_holdout_publication_registry_packet_outputs,
)
from scripts.build_randomized_holdout_publication_registry_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_entry_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryPacketTests(unittest.TestCase):
    def test_packet_accepts_registered_entry_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, check, entry_path, check_path = ready_packet_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_packet(
                entry,
                check,
                registry_entry_path=entry_path,
                registry_entry_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_packet_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_packet_ready"])
        self.assertEqual(report["summary"]["handoff_status"], "ready_for_publication_registry_manifest")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["consumer_boundary"], "governance_lookup_only")
        self.assertEqual(report["summary"]["evidence_count"], 2)
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_publication_registry_manifest")
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_bounded_publication=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_packet_fails_when_contract_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, check, entry_path, check_path = ready_packet_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_packet(
                entry,
                check,
                registry_entry_path=entry_path,
                registry_entry_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_passed", [issue["id"] for issue in report["issues"]])

    def test_packet_fails_when_consumer_boundary_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry, check, entry_path, check_path = ready_packet_inputs(Path(tmp))
            entry["summary"]["consumer_boundary"] = "production_lookup"
            report = build_randomized_holdout_publication_registry_packet(
                entry,
                check,
                registry_entry_path=entry_path,
                registry_entry_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("consumer_boundary_governance", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry, check, entry_path, check_path = ready_packet_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_entry(entry_path.parent), entry_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_entry_check(check_path.parent), check_path)
            report = build_randomized_holdout_publication_registry_packet(entry, check, registry_entry_path=entry_path, registry_entry_check_path=check_path)
            outputs = write_randomized_holdout_publication_registry_packet_outputs(report, root / "packet")
            cli_main(
                [
                    "--registry-entry",
                    str(entry_path.parent),
                    "--registry-entry-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-packet"),
                    "--require-packet-ready",
                    "--require-bounded-publication",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_PACKET_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_packet_ready=True", render_randomized_holdout_publication_registry_packet_text(report))
        self.assertIn("ready_for_publication_registry_manifest", render_randomized_holdout_publication_registry_packet_markdown(report))
        self.assertIn("publication registry packet", render_randomized_holdout_publication_registry_packet_html(report))


def ready_packet_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    entry, entry_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_registry_entry_check(entry, registry_entry_path=entry_path)
    check_outputs = write_randomized_holdout_publication_registry_entry_check_outputs(check, root / "check")
    return entry, check, entry_path, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
