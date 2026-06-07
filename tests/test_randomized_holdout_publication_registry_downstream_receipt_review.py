from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_registry_downstream_receipt import build_randomized_holdout_publication_registry_downstream_receipt
from minigpt.randomized_holdout_publication_registry_downstream_receipt_artifacts import write_randomized_holdout_publication_registry_downstream_receipt_outputs
from minigpt.randomized_holdout_publication_registry_downstream_receipt_review import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_JSON_FILENAME,
    build_randomized_holdout_publication_registry_downstream_receipt_review,
    locate_randomized_holdout_publication_registry_downstream_receipt,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_registry_downstream_receipt_review_artifacts import (
    render_randomized_holdout_publication_registry_downstream_receipt_review_html,
    render_randomized_holdout_publication_registry_downstream_receipt_review_markdown,
    render_randomized_holdout_publication_registry_downstream_receipt_review_text,
    write_randomized_holdout_publication_registry_downstream_receipt_review_outputs,
)
from scripts.review_randomized_holdout_publication_registry_downstream_receipt import main as cli_main
from tests.test_randomized_holdout_publication_registry_downstream_receipt import ready_receipt_inputs


class RandomizedHoldoutPublicationRegistryDownstreamReceiptReviewTests(unittest.TestCase):
    def test_receipt_review_accepts_ready_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_registry_downstream_receipt_review(
                receipt,
                downstream_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_registry_downstream_receipt_review_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_registry_downstream_receipt_review_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_downstream_consumer_packet")
        self.assertTrue(report["summary"]["consumer_ready"])
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertFalse(report["summary"]["approved_for_promotion"])
        self.assertIn("training_data_claim_expansion", report["summary"]["blocked_uses"])
        self.assertEqual(report["summary"]["next_step"], "build_randomized_holdout_publication_registry_downstream_consumer_packet")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_consumer_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_receipt_review_fails_when_source_digest_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            receipt["downstream_guard_sha256"] = "0" * 64
            report = build_randomized_holdout_publication_registry_downstream_receipt_review(
                receipt,
                downstream_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_guard_digest_matches", [issue["id"] for issue in report["issues"]])

    def test_receipt_review_fails_when_granted_use_expands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_review_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_registry_downstream_receipt_review(
                receipt,
                downstream_receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_review_inputs(root)
            self.assertEqual(locate_randomized_holdout_publication_registry_downstream_receipt(receipt_path.parent), receipt_path)
            report = build_randomized_holdout_publication_registry_downstream_receipt_review(
                receipt,
                downstream_receipt_path=receipt_path,
            )
            outputs = write_randomized_holdout_publication_registry_downstream_receipt_review_outputs(report, root / "review")
            cli_main(
                [
                    "--receipt",
                    str(receipt_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--require-consumer-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_RECEIPT_REVIEW_JSON_FILENAME))
        self.assertIn("randomized_holdout_publication_registry_downstream_receipt_review_ready=True", render_randomized_holdout_publication_registry_downstream_receipt_review_text(report))
        self.assertIn("approved_for_downstream_consumer_packet", render_randomized_holdout_publication_registry_downstream_receipt_review_markdown(report))
        self.assertIn("publication registry downstream receipt review", render_randomized_holdout_publication_registry_downstream_receipt_review_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    guard, guard_path = ready_receipt_inputs(root)
    receipt = build_randomized_holdout_publication_registry_downstream_receipt(guard, downstream_guard_path=guard_path)
    receipt_outputs = write_randomized_holdout_publication_registry_downstream_receipt_outputs(receipt, root / "receipt")
    return receipt, Path(receipt_outputs["json"])


if __name__ == "__main__":
    unittest.main()
