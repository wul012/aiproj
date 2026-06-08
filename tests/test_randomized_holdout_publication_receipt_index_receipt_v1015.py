from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_index_receipt_v1015 import (
    DEFAULT_CONSUMER_NAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_V1015_JSON_FILENAME,
    READY_KEY,
    RECEIPT_STATUS,
    build_randomized_holdout_publication_receipt_index_receipt_v1015,
    locate_receipt_index_review_v1015,
    read_json_report,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_index_receipt_v1015_artifacts import (
    render_randomized_holdout_publication_receipt_index_receipt_v1015_html,
    render_randomized_holdout_publication_receipt_index_receipt_v1015_markdown,
    render_randomized_holdout_publication_receipt_index_receipt_v1015_text,
    write_randomized_holdout_publication_receipt_index_receipt_v1015_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014_outputs
from minigpt.report_utils import write_json_payload
from scripts.record_randomized_holdout_publication_receipt_index_receipt_v1015 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014 import ready_review_inputs


class RandomizedHoldoutPublicationReceiptIndexReceiptV1015Tests(unittest.TestCase):
    def test_receipt_accepts_ready_review(self) -> None:
        with short_temp_dir() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_v1015(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_index_receipt_v1015_ready")
        self.assertTrue(report["summary"][READY_KEY])
        self.assertEqual(report["summary"]["receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["consumer_name"], DEFAULT_CONSUMER_NAME)
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "check_randomized_holdout_publication_receipt_index_receipt_v1015")
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_receipt_ready=True, require_promotion_ready=True), 1)

    def test_receipt_fails_when_requested_use_changes(self) -> None:
        with short_temp_dir() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_v1015(
                review,
                receipt_index_review_path=review_path,
                requested_use="production_promotion",
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("requested_use_allowed", [issue["id"] for issue in report["issues"]])

    def test_receipt_fails_when_source_receipt_index_is_missing(self) -> None:
        with short_temp_dir() as tmp:
            review, review_path = ready_receipt_inputs(Path(tmp))
            review["review"]["receipt_index_path"] = str(Path(tmp) / "missing-receipt-index.json")
            report = build_randomized_holdout_publication_receipt_index_receipt_v1015(
                review,
                receipt_index_review_path=review_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_index_file_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_receipt_ready_returns_one_on_bad_review(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            review, review_path = ready_receipt_inputs(root)
            review["summary"]["receipt_index_ready"] = False
            write_json_payload(review, review_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(review_path.parent), "--out-dir", str(root / "cli-receipt"), "--require-receipt-ready", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-receipt" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_V1015_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            review, review_path = ready_receipt_inputs(root)
            self.assertEqual(locate_receipt_index_review_v1015(review_path.parent), review_path)
            report = build_randomized_holdout_publication_receipt_index_receipt_v1015(
                review,
                receipt_index_review_path=review_path,
            )
            outputs = write_randomized_holdout_publication_receipt_index_receipt_v1015_outputs(report, root / "receipt")
            cli_main([str(review_path.parent), "--out-dir", str(root / "cli-receipt"), "--require-receipt-ready", "--force"])
            cli_report = read_json_report(root / "cli-receipt" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_V1015_JSON_FILENAME)

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_V1015_JSON_FILENAME))
        self.assertEqual(cli_report["summary"]["consumer_name"], DEFAULT_CONSUMER_NAME)
        self.assertIn("receipt_ready=True", render_randomized_holdout_publication_receipt_index_receipt_v1015_text(report))
        self.assertIn("Consumer Receipts", render_randomized_holdout_publication_receipt_index_receipt_v1015_markdown(report))
        self.assertIn("receipt", render_randomized_holdout_publication_receipt_index_receipt_v1015_html(report))


def ready_receipt_inputs(root: Path) -> tuple[dict[str, object], Path]:
    index, index_path = ready_review_inputs(root)
    review = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014(
        index,
        receipt_index_path=index_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014_outputs(review, root / "r")
    return review, Path(outputs["json"])


def short_temp_dir() -> tempfile.TemporaryDirectory[str]:
    root = Path("runs") / "test-temp-v1015"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
