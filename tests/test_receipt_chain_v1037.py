from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.receipt_chain_check_v1036 import build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036
from minigpt.receipt_chain_check_v1036_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036_outputs
from minigpt.receipt_chain_v1037 import (
    LOOKUP_KEY_PREFIX,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1037_JSON_FILENAME,
    READY_KEY,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037,
    locate_receipt_check_v1037,
    locate_receipt_v1037,
    resolve_exit_code,
)
from minigpt.receipt_chain_v1037_artifacts import (
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_html,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_markdown,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_text,
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_outputs,
)
from minigpt.receipt_chain_v1035 import RECEIPT_STATUS, build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035
from minigpt.receipt_chain_v1035_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_outputs
from scripts.build_receipt_chain_v1037 import main as cli_main
from tests.test_receipt_chain_v1035 import ready_receipt_inputs


class RandomizedHoldoutPublicationReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexV1037Tests(unittest.TestCase):
    def test_receipt_index_accepts_ready_receipt_and_check(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_ready")
        self.assertTrue(report["summary"][READY_KEY])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037")
        self.assertTrue(report["receipt_index_rows"][0]["lookup_key"].startswith(LOOKUP_KEY_PREFIX))
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_receipt_index_fails_when_granted_use_changes(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("granted_use_lookup_only", [issue["id"] for issue in report["issues"]])

    def test_receipt_index_fails_when_contract_check_is_not_ready(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            check["summary"]["contract_check_ready"] = False
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("contract_check_ready", [issue["id"] for issue in report["issues"]])

    def test_outputs_and_cli_are_wired(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            receipt, receipt_path, check, check_path = ready_index_inputs(root)
            self.assertEqual(locate_receipt_v1037(receipt_path.parent), receipt_path)
            self.assertEqual(locate_receipt_check_v1037(check_path.parent), check_path)
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_outputs(report, root / "index")
            cli_main(["--receipt", str(receipt_path.parent), "--receipt-check", str(check_path.parent), "--out-dir", str(root / "cli-index"), "--require-index-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1037_JSON_FILENAME))
        self.assertIn("index_ready=True", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_text(report))
        self.assertIn("Receipt Index Rows", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_markdown(report))
        self.assertIn("receipt index", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    review, review_path = ready_receipt_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035(
        review,
        receipt_index_review_path=review_path,
    )
    receipt_outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_outputs(receipt, root / "receipt")
    receipt_path = Path(receipt_outputs["json"])
    check = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036(receipt, receipt_path=receipt_path)
    check_outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036_outputs(check, root / "receipt-check")
    return receipt, receipt_path, check, Path(check_outputs["json"])


def short_temp_dir() -> tempfile.TemporaryDirectory[str]:
    root = Path("runs") / "test-temp-v1037"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()


