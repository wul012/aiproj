from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_CHECK_V988_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988,
    locate_receipt_v988,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_outputs
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v988 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987 import ready_receipt_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptCheckV988Tests(unittest.TestCase):
    def test_receipt_check_accepts_rebuildable_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_contract_check_v988_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_receipt_status"], "publication_receipt_index_lookup_receipted")
        self.assertEqual(report["summary"]["rebuilt_receipt_status"], "publication_receipt_index_lookup_receipted")
        self.assertEqual(report["summary"]["original_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_granted_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["original_promotion_ready"])
        self.assertFalse(report["summary"]["rebuilt_promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v988")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_receipt_check_fails_when_granted_use_is_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            receipt["receipt"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("summary.granted_use", [issue["id"] for issue in report["issues"]])
        self.assertIn("receipt.granted_use", [issue["id"] for issue in report["issues"]])

    def test_receipt_check_fails_when_source_review_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["receipt_index_review_path"] = "missing-review.json"
            receipt["receipt"]["receipt_index_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_index_review_exists", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_check_inputs(root)
            receipt["summary"]["granted_use"] = "production_promotion"
            write_json_payload(receipt, receipt_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(receipt_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_CHECK_V988_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_check_inputs(root)
            self.assertEqual(locate_receipt_v988(receipt_path.parent), receipt_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988(
                receipt,
                receipt_path=receipt_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_outputs(report, root / "check")
            cli_main([str(receipt_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_CHECK_V988_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_markdown(report))
        self.assertIn("receipt check", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_receipt_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987(
        review,
        receipt_index_review_path=review_path,
    )
    outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_outputs(receipt, root / "receipt")
    return receipt, Path(outputs["json"])


if __name__ == "__main__":
    unittest.main()
