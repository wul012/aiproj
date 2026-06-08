from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000_outputs
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1001_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001,
    locate_receipt_check_v1001,
    locate_receipt_v1001,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_artifacts import (
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_html,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_markdown,
    render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_text,
    write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_outputs,
)
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999 import build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999
from minigpt.randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_artifacts import write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_outputs
from scripts.build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999 import ready_receipt_inputs


class RandomizedHoldoutPublicationReceiptPacketIndexPublicationReceiptIndexReceiptIndexPublicationIndexReceiptIndexReceiptIndexV1001Tests(unittest.TestCase):
    def test_receipt_index_accepts_ready_receipt_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_ready")
        self.assertTrue(report["summary"]["randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_ready"])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001")
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_receipt_index_fails_when_granted_use_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_fails_when_contract_check_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, receipt_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_receipt_v1001(receipt_path.parent), receipt_path)
            self.assertEqual(locate_receipt_check_v1001(check_path.parent), check_path)
            report = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_outputs(report, root / "index")
            cli_main(["--receipt", str(receipt_path.parent), "--receipt-check", str(check_path.parent), "--out-dir", str(root / "cli-index"), "--require-index-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_PUBLICATION_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1001_JSON_FILENAME))
        self.assertIn("index_ready=True", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_text(report))
        self.assertIn("Receipt Index Rows", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_markdown(report))
        self.assertIn("receipt index", render_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    review, review_path = ready_receipt_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999(
        review,
        receipt_index_review_path=review_path,
    )
    receipt_outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_outputs(receipt, root / "receipt")
    receipt_path = Path(receipt_outputs["json"])
    check = build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000(receipt, receipt_path=receipt_path)
    check_outputs = write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000_outputs(check, root / "receipt-check")
    return receipt, receipt_path, check, Path(check_outputs["json"])


if __name__ == "__main__":
    unittest.main()

