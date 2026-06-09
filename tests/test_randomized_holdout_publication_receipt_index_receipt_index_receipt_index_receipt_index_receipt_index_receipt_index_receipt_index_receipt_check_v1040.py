from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1040_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040,
    locate_receipt_v1040,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_artifacts import (
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_html,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_markdown,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_text,
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_outputs,
)
from minigpt.randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039 import (
    RECEIPT_STATUS,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039,
)
from minigpt.randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039_outputs
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1040 import main as cli_main
from tests.test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039 import ready_receipt_inputs


class RandomizedHoldoutPublicationReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptCheckV1040Tests(unittest.TestCase):
    def test_receipt_check_accepts_rebuildable_receipt(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1040_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["rebuilt_receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["original_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_granted_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["original_promotion_ready"])
        self.assertFalse(report["summary"]["rebuilt_promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1040")
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_receipt_check_fails_when_granted_use_is_tampered(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            receipt["receipt"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("summary.granted_use", [issue["id"] for issue in report["issues"]])
        self.assertIn("receipt.granted_use", [issue["id"] for issue in report["issues"]])

    def test_receipt_check_fails_when_source_review_is_missing(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["receipt_index_review_path"] = "missing-review.json"
            receipt["receipt"]["receipt_index_review_path"] = "missing-review.json"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("source_receipt_index_review_exists", [issue["id"] for issue in report["issues"]])

    def test_receipt_check_fails_when_source_digest_is_tampered(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["receipt_index_review_sha256"] = "bad"
            receipt["receipt"]["receipt_index_review_sha256"] = "bad"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "fail")
        self.assertIn("receipt_index_review_sha256", [issue["id"] for issue in report["issues"]])
        self.assertIn("receipt.receipt_index_review_sha256", [issue["id"] for issue in report["issues"]])

    def test_cli_require_pass_returns_one_on_tampered_receipt(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_check_inputs(root)
            receipt["summary"]["granted_use"] = "production_promotion"
            write_json_payload(receipt, receipt_path)

            with self.assertRaises(SystemExit) as raised:
                cli_main([str(receipt_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

            self.assertEqual(raised.exception.code, 1)
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1040_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_check_inputs(root)
            self.assertEqual(locate_receipt_v1040(receipt_path.parent), receipt_path)
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(
                receipt,
                receipt_path=receipt_path,
            )
            outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_outputs(report, root / "check")
            cli_main([str(receipt_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1040_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_markdown(report))
        self.assertIn("receipt", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_receipt_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039(
        review,
        receipt_index_review_path=review_path,
    )
    outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039_outputs(receipt, root / "receipt")
    return receipt, Path(outputs["json"])


def short_temp_dir() -> tempfile.TemporaryDirectory[str]:
    root = Path("runs") / "test-temp-v1040"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
