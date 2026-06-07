from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_CHECK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_outputs,
)
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication import ready_publication_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationCheckTests(unittest.TestCase):
    def test_contract_check_passes_for_rebuildable_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_contract_check_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_publication_status"], "published_for_downstream_consumer_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_publication_status"], "published_for_downstream_consumer_lookup_only")
        self.assertEqual(report["summary"]["original_published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_published_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["original_evidence_count"], 2)
        self.assertEqual(report["summary"]["rebuilt_evidence_count"], 2)
        self.assertEqual(report["summary"]["original_promotion_ready"], False)
        self.assertEqual(report["summary"]["rebuilt_promotion_ready"], False)
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_contract_check_fails_when_publication_use_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            publication["summary"]["published_use"] = "production_promotion"
            publication["publication"]["published_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "fail")
        ids = [issue["id"] for issue in report["issues"]]
        self.assertIn("summary.published_use", ids)
        self.assertIn("publication.published_use", ids)

    def test_contract_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            publication, publication_path = ready_check_inputs(Path(tmp))
            publication["ack_bundle_review_path"] = "missing-review.json"
            publication["publication"]["ack_bundle_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(
                publication,
                publication_path=publication_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_ack_bundle_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path = ready_check_inputs(root)
            publication["summary"]["published_use"] = "production_promotion"
            write_json_payload(publication, publication_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(publication_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_CHECK_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publication, publication_path = ready_check_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(publication_path.parent), publication_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check(
                publication,
                publication_path=publication_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_outputs(report, root / "check")
            cli_main([str(publication_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_CHECK_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_markdown(report))
        self.assertIn("publication contract check", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_publication_inputs(root)
    publication = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication(
        review,
        ack_bundle_review_path=review_path,
    )
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_outputs(publication, root / "publication")
    return publication, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
