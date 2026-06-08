from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_REVIEW_V994_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994,
    locate_publication_index_v994,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs
from minigpt.report_utils import write_json_payload
from scripts.review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v994 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 import ready_index_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationIndexReviewV994Tests(unittest.TestCase):
    def test_publication_index_review_accepts_ready_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994(index, publication_index_path=index_path)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_ready"])
        self.assertEqual(report["summary"]["review_status"], "approved_for_publication_index_receipt_lookup_only")
        self.assertTrue(report["summary"]["publication_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v994")
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_publication_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_review_ready=True, require_promotion_ready=True), 1)

    def test_publication_index_review_fails_on_bad_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            index, index_path = ready_review_inputs(Path(tmp))
            index["publication_index"]["source_evidence_rows"][0]["sha256"] = "bad"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994(index, publication_index_path=index_path)

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_evidence_digests", [issue["id"] for issue in report["issues"]])

    def test_cli_require_review_ready_returns_one_on_tampered_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            index["summary"]["lookup_scope"] = "production_promotion"
            write_json_payload(index, index_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(index_path.parent), "--out-dir", str(root / "cli-review"), "--require-review-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-review" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_REVIEW_V994_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index, index_path = ready_review_inputs(root)
            self.assertEqual(locate_publication_index_v994(index_path.parent), index_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994(index, publication_index_path=index_path)
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_outputs(report, root / "review")
            cli_main([str(index_path.parent), "--out-dir", str(root / "cli-review"), "--require-review-ready", "--require-publication-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_REVIEW_V994_JSON_FILENAME))
        self.assertIn("review_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_text(report))
        self.assertIn("Review", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_markdown(report))
        self.assertIn("publication index", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_html(report))


def ready_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    publication, publication_path, check, check_path = ready_index_inputs(root)
    index = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993(
        publication,
        check,
        publication_path=publication_path,
        publication_check_path=check_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_outputs(index, root / "publication-index")
    return index, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
