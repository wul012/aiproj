from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_manifest import build_randomized_holdout_publication_registry_manifest
from minigpt.randomized_holdout_publication_registry_manifest_artifacts import write_randomized_holdout_publication_registry_manifest_outputs
from minigpt.randomized_holdout_publication_registry_manifest_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_manifest_review,
    locate_randomized_holdout_publication_registry_manifest,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_manifest_review_artifacts import (
    render_randomized_holdout_publication_registry_manifest_review_html,
    render_randomized_holdout_publication_registry_manifest_review_markdown,
    render_randomized_holdout_publication_registry_manifest_review_text,
    write_randomized_holdout_publication_registry_manifest_review_outputs,
)
from scripts.build_randomized_holdout_publication_registry_manifest_review import main as cli_main
from tests.test_randomized_holdout_publication_registry_manifest import ready_manifest_inputs


class RandomizedHoldoutPublicationRegistryManifestReviewTests(unittest.TestCase):
    def test_review_accepts_ready_manifest_for_lookup_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest, manifest_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_manifest_review(manifest, registry_manifest_path=manifest_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_manifest_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_manifest_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_governance_lookup_only")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["bounded_publication_accepted"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["allowed_use"], "governance_lookup_only")
        self.assertEqual(report["summary"]["rejected_use"], "production_promotion")
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_publication_registry_lookup_packet")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_review_fails_when_consumer_boundary_widens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest, manifest_path = ready_review_inputs(Path(tmp))
            manifest["summary"]["consumer_boundary"] = "production_lookup"
            report = build_randomized_holdout_publication_registry_manifest_review(manifest, registry_manifest_path=manifest_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("consumer_boundary_governance", [issue["id"] for issue in report["issues"]])

    def test_review_fails_when_manifest_entry_is_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest, manifest_path = ready_review_inputs(Path(tmp))
            manifest["manifest"]["entries"][0]["promotion_ready"] = True
            report = build_randomized_holdout_publication_registry_manifest_review(manifest, registry_manifest_path=manifest_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("entries_not_promoted", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest, manifest_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_manifest(manifest_path.parent), manifest_path)
            report = build_randomized_holdout_publication_registry_manifest_review(manifest, registry_manifest_path=manifest_path)
            outputs = write_randomized_holdout_publication_registry_manifest_review_outputs(report, root / "review")
            cli_main(
                [
                    "--registry-manifest",
                    str(manifest_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_MANIFEST_REVIEW_JSON_FILENAME))
        self.assertIn(
            "randomized_holdout_publication_registry_manifest_review_ready=True",
            render_randomized_holdout_publication_registry_manifest_review_text(report),
        )
        self.assertIn("approved_for_governance_lookup_only", render_randomized_holdout_publication_registry_manifest_review_markdown(report))
        self.assertIn("publication registry manifest review", render_randomized_holdout_publication_registry_manifest_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    packet, packet_path = ready_manifest_inputs(root)
    manifest = build_randomized_holdout_publication_registry_manifest(packet, registry_packet_path=packet_path)
    manifest_outputs = write_randomized_holdout_publication_registry_manifest_outputs(manifest, root / "manifest")
    return manifest, Path(manifest_outputs["json"])


if __name__ == "__main__":
    unittest.main()
