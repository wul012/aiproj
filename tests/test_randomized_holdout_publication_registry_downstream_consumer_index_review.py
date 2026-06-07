from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_index import build_randomized_holdout_publication_registry_downstream_consumer_index
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_index_outputs
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_index_review,
    locate_randomized_holdout_publication_registry_downstream_consumer_index,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_review_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_index_review_html,
    render_randomized_holdout_publication_registry_downstream_consumer_index_review_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_index_review_text,
    write_randomized_holdout_publication_registry_downstream_consumer_index_review_outputs,
)
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_index_review import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_index import ready_index_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerIndexReviewTests(unittest.TestCase):
    def test_consumer_index_review_accepts_ready_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_index_review(
                index,
                consumer_index_path=index_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_index_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_index_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_consumer_lookup_only")
        self.assertTrue(report["summary"]["downstream_ready"])
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["allowed_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertIn("production_promotion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_registry_downstream_consumer_ack")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_downstream_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_consumer_index_review_fails_when_source_packet_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["consumer_index"]["consumer_packet_path"] = "missing-consumer-packet.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_index_review(
                index,
                consumer_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_packet_file_exists", [issue["id"] for issue in report["issues"]])

    def test_consumer_index_review_fails_when_blocked_uses_are_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["summary"]["blocked_uses"] = ["production_promotion"]
            report = build_randomized_holdout_publication_registry_downstream_consumer_index_review(
                index,
                consumer_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("blocked_uses_complete", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_index(index_path.parent), index_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_index_review(
                index,
                consumer_index_path=index_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_index_review_outputs(report, root / "review")
            cli_main(
                [
                    "--consumer-index",
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-downstream-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_INDEX_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_index_review_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_index_review_text(report))
        self.assertIn("approved_for_downstream_consumer_lookup_only", render_randomized_holdout_publication_registry_downstream_consumer_index_review_markdown(report))
        self.assertIn("downstream consumer index review", render_randomized_holdout_publication_registry_downstream_consumer_index_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    packet, packet_path, check, check_path = ready_index_inputs(root)
    index = build_randomized_holdout_publication_registry_downstream_consumer_index(
        packet,
        check,
        consumer_packet_path=packet_path,
        consumer_packet_check_path=check_path,
    )
    index_outputs = write_randomized_holdout_publication_registry_downstream_consumer_index_outputs(index, root / "consumer-index")
    return index, Path(index_outputs["json"])


if __name__ == "__main__":
    unittest.main()
