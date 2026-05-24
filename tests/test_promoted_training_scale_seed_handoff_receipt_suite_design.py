from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    RECEIPT_TYPE,
    check_promoted_training_scale_seed_handoff_automation_receipt,
    render_promoted_training_scale_seed_handoff_automation_receipt_check,
)
from test_promoted_training_scale_seed_handoff_suite_design import write_suite_design_seed_tree  # noqa: E402


class PromotedTrainingScaleSeedHandoffReceiptSuiteDesignTests(unittest.TestCase):
    def test_receipt_checker_requires_schema_v3_suite_design_contract_fields(self) -> None:
        missing_fields = {
            "schema_version": 3,
            "receipt_type": RECEIPT_TYPE,
            "automation_decision": "continue",
            "automation_exit_code": 0,
            "automation_blocking_source": None,
            "failed_requirements": [],
            "selected_handoff_batch_maturity_ci_regression_count": 0,
            "handoff_batch_maturity_ci_regression_count": 0,
            "comparison_exclusion_reasons": [],
        }
        valid = {
            **missing_fields,
            "selected_handoff_batch_maturity_suite_design_regression_count": 0,
            "selected_handoff_batch_maturity_suite_design_regression_names": [],
            "handoff_batch_maturity_suite_design_regression_count": 2,
            "handoff_batch_maturity_suite_design_regression_names": ["beta-suite", "standard"],
            "comparison_ready_handoff_batch_maturity_suite_design_regression_count": 0,
            "comparison_ready_handoff_batch_maturity_suite_design_regression_names": [],
        }

        failed = check_promoted_training_scale_seed_handoff_automation_receipt(missing_fields)
        passed = check_promoted_training_scale_seed_handoff_automation_receipt(valid)
        rendered = render_promoted_training_scale_seed_handoff_automation_receipt_check(passed)

        self.assertEqual(failed["status"], "fail")
        self.assertTrue(
            any(
                "schema_version >= 3 receipt must include handoff_batch_maturity_suite_design_regression_count"
                in issue
                for issue in failed["issues"]
            )
        )
        self.assertEqual(passed["status"], "pass")
        self.assertEqual(passed["schema_version"], 3)
        self.assertEqual(passed["handoff_batch_maturity_suite_design_regression_count"], 2)
        self.assertEqual(passed["handoff_batch_maturity_suite_design_regression_names"], ["beta-suite", "standard"])
        self.assertIn("receipt_handoff_batch_maturity_suite_design_regression_count=2", rendered)

    def test_script_embeds_suite_design_receipt_contract_through_assurance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_suite_design_seed_tree(root)
            handoff_dir = root / "handoff"
            receipt_check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-check"
            assurance_dir = root / "assurance"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(handoff_dir),
                    "--require-clean-batch-review",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                    "--assurance-out-dir",
                    str(assurance_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            receipt = json.loads(
                (handoff_dir / "promoted_training_scale_seed_handoff_automation_receipt.json").read_text(
                    encoding="utf-8"
                )
            )
            receipt_check = json.loads(
                (receipt_check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.json").read_text(
                    encoding="utf-8"
                )
            )
            embedded_check = json.loads(
                (embedded_check_dir / "promoted_training_scale_seed_handoff_embedded_receipt_check.json").read_text(
                    encoding="utf-8"
                )
            )
            assurance = json.loads(
                (assurance_dir / "promoted_training_scale_seed_handoff_assurance.json").read_text(encoding="utf-8")
            )
            report = json.loads(
                (handoff_dir / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8")
            )
            csv_text = (handoff_dir / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (handoff_dir / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")

            self.assertEqual(receipt["schema_version"], 3)
            self.assertEqual(receipt["selected_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(receipt["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(receipt["handoff_batch_maturity_suite_design_regression_names"], ["beta-suite", "standard"])
            self.assertEqual(receipt["comparison_ready_handoff_batch_maturity_suite_design_regression_count"], 0)
            self.assertEqual(receipt_check["schema_version"], 3)
            self.assertEqual(receipt_check["handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(embedded_check["receipt_schema_version"], 3)
            self.assertEqual(embedded_check["receipt_handoff_batch_maturity_suite_design_regression_count"], 2)
            self.assertEqual(assurance["embedded_receipt_check_receipt_schema_version"], 3)
            self.assertEqual(
                assurance["embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count"],
                2,
            )
            self.assertEqual(
                report["handoff_assurance"][
                    "embedded_receipt_check_receipt_comparison_ready_handoff_batch_maturity_suite_design_regression_count"
                ],
                0,
            )
            self.assertIn(
                "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count",
                csv_text,
            )
            self.assertIn("Handoff assurance receipt suite-design regressions", markdown)
            self.assertIn("receipt_handoff_batch_maturity_suite_design_regression_count=2", completed.stdout)
            self.assertIn(
                "embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count=2",
                completed.stdout,
            )
            self.assertIn(
                "handoff_assurance_embedded_receipt_check_receipt_handoff_batch_maturity_suite_design_regression_count=2",
                completed.stdout,
            )


if __name__ == "__main__":
    unittest.main()
