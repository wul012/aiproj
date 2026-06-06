from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_lookup_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_lookup_packet,
    locate_randomized_holdout_publication_registry_manifest_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_lookup_packet_artifacts import (
    render_randomized_holdout_publication_registry_lookup_packet_html,
    render_randomized_holdout_publication_registry_lookup_packet_markdown,
    render_randomized_holdout_publication_registry_lookup_packet_text,
    write_randomized_holdout_publication_registry_lookup_packet_outputs,
)
from minigpt.randomized_holdout_publication_registry_manifest_review import build_randomized_holdout_publication_registry_manifest_review
from minigpt.randomized_holdout_publication_registry_manifest_review_artifacts import write_randomized_holdout_publication_registry_manifest_review_outputs
from scripts.build_randomized_holdout_publication_registry_lookup_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_manifest_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryLookupPacketTests(unittest.TestCase):
    def test_lookup_packet_accepts_lookup_only_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_lookup_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_lookup_packet(review, registry_manifest_review_path=review_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_lookup_packet_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_lookup_packet_ready"])
        self.assertEqual(report["summary"]["lookup_scope"], "governance_lookup_only")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["rejected_use"], "production_promotion")
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_lookup_packet")
        self.assertEqual(report["lookup_packet"]["lookup_keys"], ["publication:randomized-holdout-publication-v928"])
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_lookup_packet_fails_when_review_is_not_lookup_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_lookup_inputs(Path(tmp))
            review["summary"]["lookup_ready"] = False
            report = build_randomized_holdout_publication_registry_lookup_packet(review, registry_manifest_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_ready", [issue["id"] for issue in report["issues"]])

    def test_lookup_packet_fails_when_rejected_use_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_lookup_inputs(Path(tmp))
            review["summary"]["rejected_use"] = "none"
            report = build_randomized_holdout_publication_registry_lookup_packet(review, registry_manifest_review_path=review_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("rejected_use_production_promotion", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_lookup_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_manifest_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_lookup_packet(review, registry_manifest_review_path=review_path)
            outputs = write_randomized_holdout_publication_registry_lookup_packet_outputs(report, root / "lookup-packet")
            cli_main(
                [
                    "--manifest-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-lookup-packet"),
                    "--require-packet-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_LOOKUP_PACKET_JSON_FILENAME))
        self.assertIn(
            "randomized_holdout_publication_registry_lookup_packet_ready=True",
            render_randomized_holdout_publication_registry_lookup_packet_text(report),
        )
        self.assertIn("publication:randomized-holdout-publication-v928", render_randomized_holdout_publication_registry_lookup_packet_markdown(report))
        self.assertIn("publication registry lookup packet", render_randomized_holdout_publication_registry_lookup_packet_html(report))


def ready_lookup_inputs(root: Path) -> tuple[dict[str, object], Path]:
    manifest, manifest_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_manifest_review(manifest, registry_manifest_path=manifest_path)
    review_outputs = write_randomized_holdout_publication_registry_manifest_review_outputs(review, root / "review")
    return review, Path(review_outputs["json"])


if __name__ == "__main__":
    unittest.main()
