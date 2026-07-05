from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import minigpt
from minigpt.model_capability_route_promotion_release_readiness_receipt_index import (
    build_model_capability_route_promotion_release_readiness_receipt_index,
)
from minigpt.model_capability_route_promotion_release_readiness_receipt_index_artifacts import (
    write_model_capability_route_promotion_release_readiness_receipt_index_outputs,
)
from minigpt.model_capability_route_promotion_release_readiness_receipt_index_review import (
    build_model_capability_route_promotion_release_readiness_receipt_index_review,
    locate_route_promotion_release_readiness_receipt_index,
    resolve_exit_code,
)
from minigpt.model_capability_route_promotion_release_readiness_receipt_index_review_artifacts import (
    render_model_capability_route_promotion_release_readiness_receipt_index_review_html,
    render_model_capability_route_promotion_release_readiness_receipt_index_review_markdown,
    render_model_capability_route_promotion_release_readiness_receipt_index_review_text,
    write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs,
)
from scripts.review_model_capability_route_promotion_release_readiness_receipt_index import main as cli_main
from tests.test_model_capability_route_promotion_release_readiness_receipt_index import ready_downstream_receipt


def ready_receipt_index(root: Path) -> tuple[dict, Path]:
    receipt, receipt_path = ready_downstream_receipt(root / "receipt-source")
    index = build_model_capability_route_promotion_release_readiness_receipt_index(
        receipt,
        downstream_receipt_path=receipt_path,
    )
    outputs = write_model_capability_route_promotion_release_readiness_receipt_index_outputs(index, root / "index")
    return index, Path(outputs["json"])


class ModelCapabilityRoutePromotionReleaseReadinessReceiptIndexReviewTests(unittest.TestCase):
    def test_root_facade_exports_receipt_index_review(self) -> None:
        self.assertIs(
            minigpt.build_model_capability_route_promotion_release_readiness_receipt_index_review,
            build_model_capability_route_promotion_release_readiness_receipt_index_review,
        )
        self.assertIs(
            minigpt.write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs,
            write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs,
        )

    def test_receipt_index_review_is_ready_for_ready_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_receipt_index(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_receipt_index_review(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "model_capability_route_promotion_release_readiness_receipt_index_review_ready")
        self.assertTrue(report["summary"]["receipt_index_review_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["route_id"], "objective_level_contrast")
        self.assertEqual(report["summary"]["source_digest_count"], 3)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(len(report["review"]["receipt_index_digest"]), 64)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_lookup_ready=True), 0)

    def test_receipt_index_review_blocks_missing_index_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, _ = ready_receipt_index(Path(tmp))
            report = build_model_capability_route_promotion_release_readiness_receipt_index_review(
                index,
                receipt_index_path=Path(tmp) / "missing-index.json",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("receipt_index_file_exists", [issue["id"] for issue in report["issues"]])
        self.assertIn("receipt_index_digest_present", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_review_blocks_promoted_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_receipt_index(Path(tmp))
            index["summary"]["promotion_ready"] = True
            index["receipt_index"]["promotion_ready"] = True
            index["receipt_index"]["approved_for_promotion"] = True
            index["receipt_index"]["index_rows"][0]["promotion_ready"] = True
            report = build_model_capability_route_promotion_release_readiness_receipt_index_review(
                index,
                receipt_index_path=index_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("promotion_still_false", [issue["id"] for issue in report["issues"]])
        self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_receipt_index(root)
            self.assertEqual(locate_route_promotion_release_readiness_receipt_index(index_path.parent), index_path)

            report = build_model_capability_route_promotion_release_readiness_receipt_index_review(
                index,
                receipt_index_path=index_path,
            )
            outputs = write_model_capability_route_promotion_release_readiness_receipt_index_review_outputs(report, root / "review")
            cli_main(
                [
                    "--receipt-index",
                    str(index_path.parent),
                    "--out-dir",
                    str(root / "cli-review"),
                    "--require-review-ready",
                    "--force",
                ]
            )

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertIn("receipt_index_review_ready=True", render_model_capability_route_promotion_release_readiness_receipt_index_review_text(report))
        self.assertIn("Lookup Keys", render_model_capability_route_promotion_release_readiness_receipt_index_review_markdown(report))
        self.assertIn("receipt index review", render_model_capability_route_promotion_release_readiness_receipt_index_review_html(report))


if __name__ == "__main__":
    unittest.main()
