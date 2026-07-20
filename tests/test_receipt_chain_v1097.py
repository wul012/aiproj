from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from minigpt.receipt_chain_check_v1096 import build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096
from minigpt.receipt_chain_check_v1096_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096_outputs
from minigpt.receipt_chain_v1097 import (
    LOOKUP_KEY_PREFIX,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_JSON_FILENAME,
    READY_KEY,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097,
    locate_receipt_check_v1097,
    locate_receipt_v1097,
    resolve_exit_code,
)
from minigpt.receipt_chain_v1097_artifacts import (
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_html,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_markdown,
    render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_text,
    write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_outputs,
)
from minigpt.receipt_chain_v1095 import (
    RECEIPT_STATUS,
    SOURCE_LOOKUP_KEY_PREFIX,
    SOURCE_REVIEW_JSON_FILENAME,
    SOURCE_REVIEW_READY_KEY,
    SOURCE_REVIEW_STATUS,
    build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095,
)
from minigpt.receipt_chain_v1095_artifacts import write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095_outputs
from minigpt.randomized_holdout_publication_constants import (
    RANDOMIZED_HOLDOUT_PUBLICATION_CONSUMER_BOUNDARY,
    RANDOMIZED_HOLDOUT_PUBLICATION_MODEL_QUALITY_CLAIM,
    RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1094_NEXT_STEP,
)
from minigpt.report_utils import write_json_payload
from scripts.build_receipt_chain_v1097 import main as cli_main


class RandomizedHoldoutPublicationReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexReceiptIndexV1097Tests(unittest.TestCase):
    def test_receipt_index_accepts_ready_receipt_and_check(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_ready")
        self.assertTrue(report["summary"][READY_KEY])
        self.assertEqual(report["summary"]["lookup_key_count"], 1)
        self.assertEqual(report["summary"]["source_evidence_count"], 2)
        self.assertEqual(report["summary"]["receipt_status"], RECEIPT_STATUS)
        self.assertEqual(report["summary"]["granted_use"], "downstream_governance_lookup_only")
        self.assertTrue(report["summary"]["contract_check_ready"])
        self.assertFalse(report["summary"]["promotion_ready"])
        self.assertEqual(report["summary"]["next_step"], "review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097")
        self.assertTrue(report["receipt_index_rows"][0]["lookup_key"].startswith(LOOKUP_KEY_PREFIX))
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_lookup_ready=True), 0)
        self.assertEqual(resolve_exit_code(report, require_index_ready=True, require_promotion_ready=True), 1)

    def test_receipt_index_fails_when_granted_use_changes(self) -> None:
        with short_temp_dir() as tmp:
            receipt, receipt_path, check, check_path = ready_index_inputs(Path(tmp))
            receipt["summary"]["granted_use"] = "production_promotion"
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097(
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
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097(
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
            self.assertEqual(locate_receipt_v1097(receipt_path.parent), receipt_path)
            self.assertEqual(locate_receipt_check_v1097(check_path.parent), check_path)
            report = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097(
                receipt,
                check,
                receipt_path=receipt_path,
                receipt_check_path=check_path,
            )
            outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_outputs(report, root / "index")
            cli_main(["--receipt", str(receipt_path.parent), "--receipt-check", str(check_path.parent), "--out-dir", str(root / "cli-index"), "--require-index-ready", "--require-lookup-ready", "--force"])

        self.assertEqual(set(outputs), {"json", "csv", "text", "markdown", "html"})
        self.assertTrue(outputs["json"].endswith(RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1097_JSON_FILENAME))
        self.assertIn("index_ready=True", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_text(report))
        self.assertIn("Receipt Index Rows", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_markdown(report))
        self.assertIn("receipt index", render_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_html(report))


def ready_index_inputs(root: Path) -> tuple[dict[str, object], Path, dict[str, object], Path]:
    review, review_path = ready_receipt_review_inputs(root)
    receipt = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095(
        review,
        receipt_index_review_path=review_path,
    )
    receipt_outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095_outputs(receipt, root / "receipt")
    receipt_path = Path(receipt_outputs["json"])
    check = build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096(receipt, receipt_path=receipt_path)
    check_outputs = write_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096_outputs(check, root / "receipt-check")
    return receipt, receipt_path, check, Path(check_outputs["json"])


def ready_receipt_review_inputs(root: Path) -> tuple[dict[str, object], Path]:
    source_dir = root / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    receipt_index_path = source_dir / "receipt-index-v1073.json"
    source_receipt_path = source_dir / "receipt-v1071.json"
    source_receipt_check_path = source_dir / "receipt-check-v1072.json"
    source_review_path = source_dir / "review-v1094-origin.json"
    for path in [receipt_index_path, source_receipt_path, source_receipt_check_path, source_review_path]:
        write_json_payload({"status": "pass", "path": str(path)}, path)

    lookup_key = SOURCE_LOOKUP_KEY_PREFIX + "sample"
    review = {
        "schema_version": 1,
        "status": "pass",
        "decision": "randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1094_ready",
        "failed_count": 0,
        "summary": {
            SOURCE_REVIEW_READY_KEY: True,
            "review_id": "review-v1094",
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
            "next_step": RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1094_NEXT_STEP,
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
                "receipt_index_id": "receipt-index-row-v1073",
                "lookup_key": lookup_key,
                "receipt_id": "source-receipt-v1071",
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
    root = Path("runs") / "test-temp-v1097"
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()
