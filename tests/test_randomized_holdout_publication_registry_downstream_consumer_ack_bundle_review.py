from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_outputs,
)
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle import ready_bundle_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundleReviewTests(unittest.TestCase):
    def test_ack_bundle_review_accepts_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle, bundle_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(
                bundle,
                ack_bundle_path=bundle_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_consumer_ack_bundle_publication")
        self.assertTrue(report["summary"]["publish_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertEqual(report["summary"]["evidence_count"], 2)
        self.assertEqual(report["summary"]["acked_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_publish_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_ack_bundle_review_fails_when_digest_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle, bundle_path = ready_review_inputs(Path(tmp))
            bundle["evidence_rows"][0]["sha256"] = "0" * 64
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(
                bundle,
                ack_bundle_path=bundle_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("evidence_digests_match", [issue["id"] for issue in report["issues"]])

    def test_ack_bundle_review_fails_when_evidence_kind_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundle, bundle_path = ready_review_inputs(Path(tmp))
            bundle["evidence_rows"] = bundle["evidence_rows"][:1]
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(
                bundle,
                ack_bundle_path=bundle_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("evidence_count", ids)
        self.assertIn("evidence_kinds", ids)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle, bundle_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(bundle_path.parent), bundle_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review(
                bundle,
                ack_bundle_path=bundle_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_outputs(report, root / "review")
            cli_main(
                [
                    "--ack-bundle",
                    str(bundle_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-publish-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_text(report))
        self.assertIn("Evidence", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_markdown(report))
        self.assertIn("consumer ack bundle review", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    ack, ack_path, ack_check, ack_check_path = ready_bundle_inputs(root)
    bundle = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle(
        ack,
        ack_check,
        consumer_ack_path=ack_path,
        consumer_ack_check_path=ack_check_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_outputs(bundle, root / "ack-bundle")
    return bundle, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
