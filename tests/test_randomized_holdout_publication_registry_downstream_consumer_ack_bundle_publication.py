from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationTests(unittest.TestCase):
    def test_ack_bundle_publication_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
                review,
                ack_bundle_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready"])
        self.assertEqual(report["summary"]["publication_status"], "published_for_downstream_consumer_lookup_only")
        self.assertTrue(report["summary"]["publish_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertEqual(report["summary"]["published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication")
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_publication_ready=True, require_promotion_ready=True), 1)

    def test_ack_bundle_publication_fails_when_review_not_publish_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["summary"]["publish_ready"] = False
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
                review,
                ack_bundle_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("publish_ready", [issue["id"] for issue in report["issues"]])

    def test_ack_bundle_publication_fails_when_review_points_to_missing_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_publication_inputs(Path(tmp))
            review["review"]["ack_bundle_path"] = "missing-bundle.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
                review,
                ack_bundle_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("ack_bundle_file_exists", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_publication_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
                review,
                ack_bundle_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_outputs(report, root / "publication")
            cli_main(
                [
                    "--ack-bundle-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-publication"),
                    "--require-publication-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_text(report))
        self.assertIn("Evidence", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_markdown(report))
        self.assertIn("consumer ack bundle publication", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_html(report))


def ready_publication_inputs(root: Path) -> tuple[dict[str, object], Path]:
    bundle, bundle_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(bundle, ack_bundle_path=bundle_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_outputs(review, root / "ack-bundle-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
