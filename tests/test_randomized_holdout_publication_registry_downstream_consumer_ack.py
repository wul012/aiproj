from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_ack,
    locate_randomized_holdout_publication_registry_downstream_consumer_index_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_ack_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_ack_html,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_ack_text,
    write_randomized_holdout_publication_registry_downstream_consumer_ack_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_review import build_randomized_holdout_publication_registry_downstream_consumer_index_review
from minigpt.randomized_holdout_publication_registry_downstream_consumer_index_review_artifacts import write_randomized_holdout_publication_registry_downstream_consumer_index_review_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_ack import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_consumer_index_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerAckTests(unittest.TestCase):
    def test_consumer_ack_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_ack_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack(
                review,
                consumer_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_ack_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_ack_ready"])
        self.assertEqual(report["summary"]["ack_status"], "downstream_consumer_acknowledged")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertTrue(report["summary"]["downstream_ready"])
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["acked_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_downstream_consumer_ack")
        self.assertEqual(resolve_exit_code(report, require_ack_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_ack_ready=True, require_promotion_ready=True), 1)

    def test_consumer_ack_fails_when_review_points_to_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_ack_inputs(Path(tmp))
            review["review"]["consumer_index_path"] = "missing-consumer-index.json"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack(
                review,
                consumer_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("consumer_index_file_exists", [issue["id"] for issue in report["issues"]])

    def test_consumer_ack_fails_when_review_use_is_not_lookup_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_ack_inputs(Path(tmp))
            review["summary"]["allowed_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack(
                review,
                consumer_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("allowed_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_ack_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_consumer_index_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_ack(
                review,
                consumer_index_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_ack_outputs(report, root / "ack")
            cli_main(
                [
                    "--consumer-index-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-ack"),
                    "--require-ack-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_ack_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_ack_text(report))
        self.assertIn("downstream_consumer_acknowledged", render_randomized_holdout_publication_registry_downstream_consumer_ack_markdown(report))
        self.assertIn("downstream consumer ack", render_randomized_holdout_publication_registry_downstream_consumer_ack_html(report))


def ready_ack_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_downstream_consumer_index_review(index, consumer_index_path=index_path)
    outputs = write_randomized_holdout_publication_registry_downstream_consumer_index_review_outputs(review, root / "consumer-index-review")
    return review, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
