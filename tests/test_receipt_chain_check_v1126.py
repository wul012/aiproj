from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.receipt_chain_check_v1126 import (
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_JSON_FILENAME,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126,
    locate_receipt_v1126,
    resolve_exit_code,
)
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1124_NEXT_STEP,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_NEXT_STEP,
)
from minigpt.receipt_chain_check_v1126_artifacts import (
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_html,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_markdown,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_text,
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_outputs,
)
from minigpt.receipt_chain_v1125 import (
    RECEIPT_STATUS,
    SOURCE_LOOKUP_KEY_PREFIX,
    SOURCE_REVIEW_JSON_FILENAME,
    SOURCE_REVIEW_READY_KEY,
    SOURCE_REVIEW_STATUS,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125,
)
from minigpt.receipt_chain_v1125_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_outputs
from minigpt.report_utils import write_json_payload
from scripts.check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1126 import main as cli_main


class RandomizedHoldoutPublicationReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptCheckV1126Tests(unittest.TestCase):
    def test_receipt_check_accepts_rebuildable_receipt(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126(
                receipt,
                receipt_path=receipt_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1126_passed")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertEqual(report["summary"]["original_receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["rebuilt_receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["original_granted_use"], "downstream_governance_lookup_only")
        self.assertEqual(report["summary"]["rebuilt_granted_use"], "downstream_governance_lookup_only")
        self.assertFalse(report["summary"]["original_promotion_ready"])
        self.assertFalse(report["summary"]["rebuilt_promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_NEXT_STEP)
        self.assertEqual(resolve_exit_code(report, require_pass=True), 0)

    def test_receipt_check_fails_when_granted_use_is_tampered(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path = ready_check_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            receipt["receipt"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126(
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
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126(
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
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126(
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
            self.assertTrue((root / "cli-check" / RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_JSON_FILENAME).is_file())

    def test_outputs_and_cli_are_wired(self) -> None:
        with short_temp_dir() as tmp:
            root = Path(tmp)
            receipt, receipt_path = ready_check_inputs(root)
            self.assertEqual(locate_receipt_v1126(receipt_path.parent), receipt_path)
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126(
                receipt,
                receipt_path=receipt_path,
            )
            outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_outputs(report, root / "check")
            cli_main([str(receipt_path.parent), "--out-dir", str(root / "cli-check"), "--require-pass", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1126_JSON_FILENAME))
        self.assertIn("contract_check_ready=True", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_text(report))
        self.assertIn("Checks", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_markdown(report))
        self.assertIn("receipt", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126_html(report))


def ready_check_inputs(root: Path) -> tuple[dict[str, object], Path]:
    review, review_path = ready_receipt_review_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125(
        review,
        receipt_index_review_path=review_path,
    )
    outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_outputs(receipt, root / "receipt")
    return receipt, Path(outputs["json"])


def ready_receipt_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    source_dir = root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    receipt_index_path = source_dir / "receipt-index-v1081.json"
    source_receipt_path = source_dir / "receipt-v1075.json"
    source_receipt_check_path = source_dir / "receipt-check-v1076.json"
    source_review_path = source_dir / "review-v1124-origin.json"
    for path in [receipt_index_path, source_receipt_path, source_receipt_check_path, source_review_path]:
        write_json_payload({"status": "pass", "path": str(path)}, path)

    lookup_key = SOURCE_LOOKUP_KEY_PREFIX + "sample"
    review = {
        "schema_version": 1,
        "status": "pass",
        "decision": "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124_ready",
        "failed_count": 0,
        "summary": {
            SOURCE_REVIEW_READY_KEY: True,
            "review_id": "review-v1124",
            "review_status": SOURCE_REVIEW_STATUS,
            "granted_use": "downstream_governance_lookup_only",
            "receipt_index_ready": True,
            "lookup_ready": True,
            "contract_check_ready": True,
            "receipt_index_row_count": 1,
            "source_evidence_count": 2,
            "promotion_ready": False,
            "approved_for_promotion": False,
            "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
            "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
            "failed_check_count": 0,
            "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1124_NEXT_STEP,
        },
        "review": {
            "review_ready": True,
            "review_status": SOURCE_REVIEW_STATUS,
            "granted_use": "downstream_governance_lookup_only",
            "lookup_ready": True,
            "contract_check_ready": True,
            "lookup_keys": [lookup_key],
            "promotion_ready": False,
            "approved_for_promotion": False,
            "consumer_boundary": RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
            "model_quality_claim": RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
            "receipt_index_path": str(receipt_index_path),
            "source_receipt_index_path": str(receipt_index_path),
            "source_receipt_path": str(source_receipt_path),
            "source_receipt_check_path": str(source_receipt_check_path),
            "source_review_path": str(source_review_path),
        },
        "receipt_index_rows": [
            {
                "receipt_index_id": "receipt-index-row-v1081",
                "lookup_key": lookup_key,
                "receipt_id": "source-receipt-v1075",
                "promotion_ready": False,
            }
        ],
        "source_evidence_rows": [
            {"source": "receipt", "path": str(source_receipt_path), "sha256": "a" * 64, "status": "pass"},
            {"source": "receipt_check", "path": str(source_receipt_check_path), "sha256": "b" * 64, "status": "pass"},
        ],
    }
    review_path = root / "review" / SOURCE_REVIEW_JSON_FILENAME
    write_json_payload(review, review_path)
    return review, review_path


def short_temp_dir() -> tempfile.TemporaryDirectory[str]:
    root = Path("runs") / "test-temp-v1126"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
