from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_consumer_packet,
    locate_randomized_holdout_publication_registry_downstream_receipt_review,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_consumer_packet_artifacts import (
    render_randomized_holdout_publication_registry_downstream_consumer_packet_html,
    render_randomized_holdout_publication_registry_downstream_consumer_packet_markdown,
    render_randomized_holdout_publication_registry_downstream_consumer_packet_text,
    write_randomized_holdout_publication_registry_downstream_consumer_packet_outputs,
)
from minigpt.randomized_holdout_publication_registry_downstream_receipt_review import build_randomized_holdout_publication_registry_downstream_receipt_review
from minigpt.randomized_holdout_publication_registry_downstream_receipt_review_artifacts import write_randomized_holdout_publication_registry_downstream_receipt_review_outputs
from scripts.build_randomized_holdout_publication_registry_downstream_consumer_packet import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_receipt_review import ready_review_inputs


class RandomizedHoldoutPublicationRegistryDownstreamConsumerPacketTests(unittest.TestCase):
    def test_consumer_packet_accepts_ready_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_consumer_packet_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_consumer_packet_ready"])
        self.assertEqual(report["summary"]["packet_status"], "downstream_consumer_packet_ready")
        self.assertTrue(report["summary"]["lookup_ready"])
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["entry_count"], 1)
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertIn("model_quality_expansion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_registry_downstream_consumer_packet")
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_packet_ready=True, require_promotion_ready=True), 1)

    def test_consumer_packet_fails_when_review_grants_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            review["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_consumer_packet_fails_when_lookup_key_namespace_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review, review_path = ready_packet_inputs(Path(tmp))
            review["consumer_receipts"][0]["lookup_key"] = "model:randomized-holdout-publication-v928"
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet(
                review,
                receipt_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("lookup_keys_publication_namespace", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review, review_path = ready_packet_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_receipt_review(review_path.parent), review_path)
            report = build_randomized_holdout_publication_registry_downstream_consumer_packet(
                review,
                receipt_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_consumer_packet_outputs(report, root / "packet")
            cli_main(
                [
                    "--receipt-review",
                    str(review_path.parent),
                    "--out-dir",
                    str(root / "cli-packet"),
                    "--require-packet-ready",
                    "--require-lookup-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_PACKET_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_consumer_packet_ready=True", render_randomized_holdout_publication_registry_downstream_consumer_packet_text(report))
        self.assertIn("downstream_consumer_packet_ready", render_randomized_holdout_publication_registry_downstream_consumer_packet_markdown(report))
        self.assertIn("publication registry downstream consumer packet", render_randomized_holdout_publication_registry_downstream_consumer_packet_html(report))


def ready_packet_inputs(root: Path) -> tuple[dict[str, object], Path]:
    receipt, receipt_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_registry_downstream_receipt_review(receipt, downstream_receipt_path=receipt_path)
    review_outputs = write_randomized_holdout_publication_registry_downstream_receipt_review_outputs(review, root / "review")
    return review, Path(review_outputs["json"])


if __name__ == "__main__":
    unittest.main()
