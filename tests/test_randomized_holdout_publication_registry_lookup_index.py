from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_lookup_index import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_index,
    locate_randomized_holdout_publication_registry_lookup_packet,
    locate_randomized_holdout_publication_registry_lookup_packet_check,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_lookup_index_artifacts import (
    render_randomized_holdout_publication_registry_lookup_index_html,
    render_randomized_holdout_publication_registry_lookup_index_markdown,
    render_randomized_holdout_publication_registry_lookup_index_text,
    write_randomized_holdout_publication_registry_lookup_index_outputs,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet_check import build_randomized_holdout_publication_registry_lookup_packet_check
from minigpt.randomized_holdout_publication_registry_lookup_packet_check_artifacts import write_randomized_holdout_publication_registry_lookup_packet_check_outputs
from scripts.build_randomized_holdout_publication_registry_lookup_index import main as cli_main
from tests.test_randomized_holdout_publication_registry_lookup_packet_check import ready_check_inputs


class RandomizedHoldoutPublicationRegistryLookupIndexTests(unittest.TestCase):
    def test_lookup_index_accepts_packet_and_contract_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, check, packet_path, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_lookup_index(
                packet,
                check,
                lookup_packet_path=packet_path,
                lookup_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_lookup_index_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_lookup_index_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["rejected_use"], "production_promotion")
        self.assertEqual(report["lookup_index"]["lookup_keys"], ["publication:randomized-holdout-publication-v928"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_registry_lookup_index")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_lookup_index_fails_when_contract_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, check, packet_path, check_path = ready_index_inputs(Path(tmp))
            check["status"] = "fail"
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_registry_lookup_index(
                packet,
                check,
                lookup_packet_path=packet_path,
                lookup_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_packet_check_passed", [issue["id"] for issue in report["issues"]])
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_lookup_index_fails_when_lookup_keys_drift_from_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet, check, packet_path, check_path = ready_index_inputs(Path(tmp))
            packet["lookup_packet"]["lookup_keys"] = ["publication:changed"]
            report = build_randomized_holdout_publication_registry_lookup_index(
                packet,
                check,
                lookup_packet_path=packet_path,
                lookup_packet_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_keys_match_check", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet, check, packet_path, check_path = ready_index_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_lookup_packet(packet_path.parent), packet_path)
            self.assertEqual(locate_randomized_holdout_publication_registry_lookup_packet_check(check_path.parent), check_path)
            report = build_randomized_holdout_publication_registry_lookup_index(packet, check, lookup_packet_path=packet_path, lookup_packet_check_path=check_path)
            outputs = write_randomized_holdout_publication_registry_lookup_index_outputs(report, root / "index")
            cli_main(
                [
                    "--lookup-packet",
                    str(packet_path.parent),
                    "--lookup-packet-check",
                    str(check_path.parent),
                    "--out-dir",
                    str(root / "cli-index"),
                    "--require-index-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_INDEX_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_lookup_index_ready=True", render_randomized_holdout_publication_registry_lookup_index_text(report))
        self.assertIn("publication:randomized-holdout-publication-v928", render_randomized_holdout_publication_registry_lookup_index_markdown(report))
        self.assertIn("publication registry lookup index", render_randomized_holdout_publication_registry_lookup_index_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    packet, packet_path = ready_check_inputs(root)
    check = build_randomized_holdout_publication_registry_lookup_packet_check(packet, lookup_packet_path=packet_path)
    check_outputs = write_randomized_holdout_publication_registry_lookup_packet_check_outputs(check, root / "check")
    return packet, check, packet_path, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()
