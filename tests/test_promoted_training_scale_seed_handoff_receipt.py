from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.promoted_training_scale_seed_handoff import (  # noqa: E402
    build_promoted_training_scale_seed_handoff,
    write_promoted_training_scale_seed_handoff_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    RECEIPT_TYPE,
    check_promoted_training_scale_seed_handoff_automation_receipt,
    load_promoted_training_scale_seed_handoff_automation_receipt,
    render_promoted_training_scale_seed_handoff_automation_receipt_check,
)
from tests.test_promoted_training_scale_seed_handoff import write_seed_tree  # noqa: E402


class PromotedTrainingScaleSeedHandoffReceiptTests(unittest.TestCase):
    def test_receipt_checker_accepts_continue_receipt(self) -> None:
        receipt = {
            "schema_version": 1,
            "receipt_type": RECEIPT_TYPE,
            "automation_decision": "continue",
            "automation_exit_code": 0,
            "automation_blocking_source": None,
            "failed_requirements": [],
        }

        check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)
        text = render_promoted_training_scale_seed_handoff_automation_receipt_check(check)

        self.assertEqual(check["status"], "pass")
        self.assertEqual(check["checker_exit_code"], 0)
        self.assertIn("receipt_decision=continue", text)

    def test_receipt_checker_treats_valid_stop_as_automation_failure(self) -> None:
        receipt = {
            "schema_version": 1,
            "receipt_type": RECEIPT_TYPE,
            "automation_decision": "stop",
            "automation_exit_code": 1,
            "automation_blocking_source": "automation_gate",
            "failed_requirements": ["clean_evidence"],
        }

        check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)

        self.assertEqual(check["status"], "pass")
        self.assertEqual(check["checker_exit_code"], 1)
        self.assertEqual(check["blocking_source"], "automation_gate")
        self.assertEqual(check["failed_requirements"], ["clean_evidence"])

    def test_receipt_checker_rejects_inconsistent_receipt(self) -> None:
        receipt = {
            "schema_version": 1,
            "receipt_type": RECEIPT_TYPE,
            "automation_decision": "continue",
            "automation_exit_code": 2,
            "automation_blocking_source": "automation_gate",
            "failed_requirements": ["clean_evidence"],
        }

        check = check_promoted_training_scale_seed_handoff_automation_receipt(receipt)

        self.assertEqual(check["status"], "fail")
        self.assertGreaterEqual(check["issue_count"], 1)
        self.assertTrue(any("continue decision" in issue for issue in check["issues"]))

    def test_script_checks_generated_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                require_clean_evidence=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt.py"),
                    outputs["automation_receipt_json"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            loaded = load_promoted_training_scale_seed_handoff_automation_receipt(outputs["automation_receipt_json"])
            self.assertEqual(loaded["automation_decision"], "continue")
            self.assertIn("receipt_check_status=pass", completed.stdout)
            self.assertIn("receipt_decision=continue", completed.stdout)

    def test_script_exits_nonzero_for_stop_unless_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            report = build_promoted_training_scale_seed_handoff(
                seed,
                require_clean_evidence=True,
                require_clean_batch_review=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            outputs = write_promoted_training_scale_seed_handoff_outputs(report, root / "handoff")
            command = [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt.py"),
                outputs["automation_receipt_json"],
            ]

            failed = subprocess.run(command, capture_output=True, text=True)
            allowed = subprocess.run(command + ["--allow-stop"], check=True, capture_output=True, text=True)

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("receipt_decision=stop", failed.stdout)
            self.assertIn("receipt_blocking_source=automation_gate", failed.stdout)
            self.assertIn("receipt_check_status=pass", allowed.stdout)


if __name__ == "__main__":
    unittest.main()
