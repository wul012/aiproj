from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tests._bootstrap import ensure_src_path

ensure_src_path()

from minigpt.ack_bundle_index import build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index
from minigpt.ack_bundle_index_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_outputs
from minigpt.ack_bundle_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review,
    locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index,
    resolve_exit_code,
)
from minigpt.ack_bundle_review_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_outputs,
)
from scripts.build_ack_bundle_review import main as cli_main
from tests.test_ack_bundle_index import ready_index_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckBundlePublicationReceiptPacketIndexPublicationIndexReviewTests(unittest.TestCase):
    def test_publication_index_review_accepts_ready_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(
                index,
                publication_index_path=index_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_receipt_packet_index_publication_receipt")
        self.assertEqual(report["summary"]["publication_index_row_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertTrue(report["summary"]["downstream_ready"])
        self.assertTrue(report["summary"]["receipt_ready"])
        self.assertEqual(report["summary"]["allowed_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_downstream_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_publication_index_review_fails_when_source_publication_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["publication_index"]["publication_path"] = str(Path(tmp) / "missing-publication.json")
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(
                index,
                publication_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_publication_file_exists", [issue["id"] for issue in report["issues"]])

    def test_publication_index_review_fails_when_published_use_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["summary"]["published_use"] = "production_promotion"
            index["publication_index"]["published_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(
                index,
                publication_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("published_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_cli_require_review_ready_returns_one_on_tampered_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            index["summary"]["next_step"] = "skip_review"
            tampered_path = root / "tampered-index.json"
            tampered_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(tampered_path), "--out-dir", str(root / "cli-review"), "--require-review-ready", "--force"])
            self.assertTrue(index_path.exists())

        self.assertEqual(raised.exception.code, 1)

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index(index_path.parent), index_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review(
                index,
                publication_index_path=index_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_outputs(report, root / "review")
            cli_main(
                [
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-downstream-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_text(report))
        self.assertIn("Publication index rows", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_markdown(report))
        self.assertIn("publication index review", render_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    publication, publication_path, check, check_path = ready_index_inputs(root)
    index = build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index(
        publication,
        check,
        publication_path=publication_path,
        publication_check_path=check_path,
    )
    index_outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_outputs(index, root / "publication-index")
    return index, Path(index_outputs["json"])


if __name__ == "__main__":
    unittest.main()
