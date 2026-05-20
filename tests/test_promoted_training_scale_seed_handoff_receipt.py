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
from minigpt.promoted_training_scale_seed_handoff_assurance import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_assurance,
    render_promoted_training_scale_seed_handoff_assurance_check,
    write_promoted_training_scale_seed_handoff_assurance_check_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt import (  # noqa: E402
    RECEIPT_FILENAME,
    RECEIPT_TYPE,
    check_promoted_training_scale_seed_handoff_embedded_receipt_check,
    check_promoted_training_scale_seed_handoff_automation_receipt,
    load_promoted_training_scale_seed_handoff_report,
    render_promoted_training_scale_seed_handoff_embedded_receipt_check,
    load_promoted_training_scale_seed_handoff_automation_receipt,
    render_promoted_training_scale_seed_handoff_automation_receipt_check,
    resolve_promoted_training_scale_seed_handoff_report_path,
    resolve_promoted_training_scale_seed_handoff_automation_receipt_path,
    write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs,
    write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs,
)
from tests.test_promoted_training_scale_seed_handoff import write_seed_tree  # noqa: E402


class PromotedTrainingScaleSeedHandoffReceiptTests(unittest.TestCase):
    def _write_inline_checked_handoff(
        self,
        root: Path,
        *,
        clean_batch_review_status: str | None = None,
    ) -> tuple[Path, Path, Path]:
        seed = write_seed_tree(
            root,
            suite_name="standard-zh",
            include_handoff_suite_guard=True,
            include_handoff_clean_batch_review=clean_batch_review_status is not None,
            clean_batch_review_status=clean_batch_review_status or "clean",
        )
        script_out = root / "script-out"
        check_dir = root / "receipt-check"
        embedded_check_dir = root / "embedded-receipt-check"
        args = [
            sys.executable,
            "-B",
            str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
            str(seed),
            "--out-dir",
            str(script_out),
            "--execute",
            "--require-clean-evidence",
            "--receipt-check-out-dir",
            str(check_dir),
            "--embedded-receipt-check-out-dir",
            str(embedded_check_dir),
        ]
        if clean_batch_review_status is not None:
            args.append("--require-clean-batch-review")
        subprocess.run(args, check=clean_batch_review_status != "review", capture_output=True, text=True)
        return script_out, check_dir, embedded_check_dir

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
            self.assertIn("receipt_path=", completed.stdout)

    def test_script_accepts_handoff_output_directory_and_writes_check_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            report = build_promoted_training_scale_seed_handoff(
                seed,
                execute=True,
                require_clean_evidence=True,
                generated_at="2026-05-14T00:00:00Z",
            )
            handoff_dir = root / "handoff"
            check_dir = root / "receipt-check"
            write_promoted_training_scale_seed_handoff_outputs(report, handoff_dir)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt.py"),
                    str(handoff_dir),
                    "--out-dir",
                    str(check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                resolve_promoted_training_scale_seed_handoff_automation_receipt_path(handoff_dir),
                handoff_dir / RECEIPT_FILENAME,
            )
            check_json = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.json"
            check_text = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.txt"
            self.assertTrue(check_json.exists())
            self.assertTrue(check_text.exists())
            self.assertEqual(json.loads(check_json.read_text(encoding="utf-8"))["decision"], "continue")
            self.assertIn("receipt_check_json=", completed.stdout)
            self.assertIn("receipt_check_text=", completed.stdout)
            self.assertIn("receipt_decision=continue", check_text.read_text(encoding="utf-8"))

    def test_execute_script_can_write_receipt_check_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            check_dir = root / "receipt-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            check_json = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.json"
            check_text = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            check_payload = json.loads(check_json.read_text(encoding="utf-8"))
            self.assertEqual(check_payload["status"], "pass")
            self.assertEqual(check_payload["decision"], "continue")
            self.assertEqual(check_payload["checker_exit_code"], 0)
            self.assertEqual(payload["receipt_check"]["status"], "pass")
            self.assertEqual(payload["receipt_check"]["decision"], "continue")
            self.assertEqual(payload["receipt_check_outputs"]["json"], str(check_json))
            self.assertIn("receipt_check_status", csv_text)
            self.assertIn("receipt_check_decision", csv_text)
            self.assertIn("Receipt check status", markdown)
            self.assertIn("Receipt Check", html)
            self.assertIn("receipt_check_status=pass", completed.stdout)
            self.assertIn("receipt_decision=continue", completed.stdout)
            self.assertIn("receipt_check_outputs=", completed.stdout)
            self.assertIn("receipt_check_json=", completed.stdout)
            self.assertIn("receipt_check_text=", completed.stdout)
            self.assertIn("receipt_decision=continue", check_text.read_text(encoding="utf-8"))

    def test_execute_script_can_write_embedded_receipt_check_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-receipt-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(check_dir),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            embedded_json = embedded_check_dir / "promoted_training_scale_seed_handoff_embedded_receipt_check.json"
            embedded_text = embedded_check_dir / "promoted_training_scale_seed_handoff_embedded_receipt_check.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            embedded_payload = json.loads(embedded_json.read_text(encoding="utf-8"))
            self.assertEqual(embedded_payload["status"], "pass")
            self.assertEqual(embedded_payload["sidecar_status"], "pass")
            self.assertTrue(embedded_payload["receipt_path_exists"])
            self.assertTrue(embedded_payload["receipt_check_json_exists"])
            self.assertTrue(embedded_payload["receipt_check_text_exists"])
            self.assertEqual(payload["embedded_receipt_check"]["status"], "pass")
            self.assertEqual(payload["embedded_receipt_check"]["sidecar_status"], "pass")
            self.assertTrue(payload["embedded_receipt_check"]["receipt_path_exists"])
            self.assertTrue(payload["embedded_receipt_check"]["receipt_check_json_exists"])
            self.assertTrue(payload["embedded_receipt_check"]["receipt_check_text_exists"])
            self.assertEqual(payload["embedded_receipt_check_outputs"]["json"], str(embedded_json))
            self.assertIn("embedded_receipt_check_status", csv_text)
            self.assertIn("embedded_receipt_check_sidecar_status", csv_text)
            self.assertIn("Embedded receipt check status", markdown)
            self.assertIn("Embedded Receipt Check", html)
            self.assertIn("embedded_receipt_check_status=pass", completed.stdout)
            self.assertIn("embedded_receipt_check_sidecar_status=pass", completed.stdout)
            self.assertIn("embedded_receipt_check_output_json=", completed.stdout)
            self.assertIn("embedded_receipt_check_sidecar_status=pass", embedded_text.read_text(encoding="utf-8"))

    def test_execute_script_can_write_handoff_assurance_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-receipt-check"
            assurance_dir = root / "assurance"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(check_dir),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                    "--assurance-out-dir",
                    str(assurance_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            assurance_json = assurance_dir / "promoted_training_scale_seed_handoff_assurance.json"
            assurance_text = assurance_dir / "promoted_training_scale_seed_handoff_assurance.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            csv_text = (script_out / "promoted_training_scale_seed_handoff.csv").read_text(encoding="utf-8")
            markdown = (script_out / "promoted_training_scale_seed_handoff.md").read_text(encoding="utf-8")
            html = (script_out / "promoted_training_scale_seed_handoff.html").read_text(encoding="utf-8")
            assurance_payload = json.loads(assurance_json.read_text(encoding="utf-8"))
            self.assertEqual(assurance_payload["status"], "pass")
            self.assertEqual(assurance_payload["embedded_receipt_check_status"], "pass")
            self.assertEqual(assurance_payload["embedded_receipt_check_sidecar_status"], "pass")
            self.assertTrue(assurance_payload["embedded_receipt_check_output_json_exists"])
            self.assertTrue(assurance_payload["embedded_receipt_check_output_text_exists"])
            self.assertEqual(payload["handoff_assurance"]["status"], "pass")
            self.assertEqual(payload["handoff_assurance"]["embedded_receipt_check_sidecar_status"], "pass")
            self.assertEqual(payload["handoff_assurance_outputs"]["json"], str(assurance_json))
            self.assertIn("handoff_assurance_status", csv_text)
            self.assertIn("handoff_assurance_embedded_receipt_check_sidecar_status", csv_text)
            self.assertIn("Handoff assurance status", markdown)
            self.assertIn("Handoff Assurance", html)
            self.assertIn("handoff_assurance_status=pass", completed.stdout)
            self.assertIn("handoff_assurance_output_json=", completed.stdout)
            self.assertIn("handoff_assurance_status=pass", assurance_text.read_text(encoding="utf-8"))

    def test_execute_script_writes_receipt_check_before_stop_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"
            check_dir = root / "receipt-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                    "--receipt-check-out-dir",
                    str(check_dir),
                ],
                capture_output=True,
                text=True,
            )

            check_json = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.json"
            check_text = check_dir / "promoted_training_scale_seed_handoff_automation_receipt_check.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            check_payload = json.loads(check_json.read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(check_payload["status"], "pass")
            self.assertEqual(check_payload["decision"], "stop")
            self.assertEqual(check_payload["checker_exit_code"], 1)
            self.assertEqual(check_payload["blocking_source"], "automation_gate")
            self.assertEqual(check_payload["failed_requirements"], ["clean_batch_review"])
            self.assertEqual(payload["receipt_check"]["status"], "pass")
            self.assertEqual(payload["receipt_check"]["decision"], "stop")
            self.assertEqual(payload["receipt_check"]["blocking_source"], "automation_gate")
            self.assertEqual(payload["receipt_check_outputs"]["text"], str(check_text))
            self.assertIn("receipt_check_status=pass", completed.stdout)
            self.assertIn("receipt_decision=stop", completed.stdout)
            self.assertIn("receipt_blocking_source=automation_gate", completed.stdout)
            self.assertIn("automation_summary_decision=stop", completed.stdout)
            self.assertIn("receipt_decision=stop", check_text.read_text(encoding="utf-8"))

    def test_execute_script_writes_embedded_receipt_check_before_stop_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"
            check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-receipt-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                    "--receipt-check-out-dir",
                    str(check_dir),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                ],
                capture_output=True,
                text=True,
            )

            embedded_json = embedded_check_dir / "promoted_training_scale_seed_handoff_embedded_receipt_check.json"
            embedded_text = embedded_check_dir / "promoted_training_scale_seed_handoff_embedded_receipt_check.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            embedded_payload = json.loads(embedded_json.read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(embedded_payload["status"], "pass")
            self.assertEqual(embedded_payload["decision"], "stop")
            self.assertEqual(embedded_payload["sidecar_status"], "pass")
            self.assertTrue(embedded_payload["receipt_check_json_exists"])
            self.assertEqual(payload["embedded_receipt_check"]["status"], "pass")
            self.assertEqual(payload["embedded_receipt_check"]["decision"], "stop")
            self.assertEqual(payload["embedded_receipt_check"]["sidecar_status"], "pass")
            self.assertEqual(payload["embedded_receipt_check_outputs"]["text"], str(embedded_text))
            self.assertIn("embedded_receipt_check_status=pass", completed.stdout)
            self.assertIn("embedded_receipt_check_decision=stop", completed.stdout)
            self.assertIn("automation_summary_decision=stop", completed.stdout)
            self.assertIn("embedded_receipt_check_decision=stop", embedded_text.read_text(encoding="utf-8"))

    def test_execute_script_writes_handoff_assurance_before_stop_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"
            check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-receipt-check"
            assurance_dir = root / "assurance"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                    "--receipt-check-out-dir",
                    str(check_dir),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                    "--assurance-out-dir",
                    str(assurance_dir),
                ],
                capture_output=True,
                text=True,
            )

            assurance_json = assurance_dir / "promoted_training_scale_seed_handoff_assurance.json"
            assurance_text = assurance_dir / "promoted_training_scale_seed_handoff_assurance.txt"
            payload = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            assurance_payload = json.loads(assurance_json.read_text(encoding="utf-8"))
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(assurance_payload["status"], "pass")
            self.assertEqual(assurance_payload["decision"], "stop")
            self.assertEqual(payload["handoff_assurance"]["status"], "pass")
            self.assertEqual(payload["handoff_assurance"]["decision"], "stop")
            self.assertEqual(payload["handoff_assurance_outputs"]["text"], str(assurance_text))
            self.assertIn("handoff_assurance_status=pass", completed.stdout)
            self.assertIn("handoff_assurance_decision=stop", completed.stdout)
            self.assertIn("automation_summary_decision=stop", completed.stdout)
            self.assertIn("handoff_assurance_decision=stop", assurance_text.read_text(encoding="utf-8"))

    def test_execute_script_requires_receipt_check_for_embedded_receipt_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            embedded_check_dir = root / "embedded-receipt-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--embedded-receipt-check-out-dir",
                    str(embedded_check_dir),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--embedded-receipt-check-out-dir requires --receipt-check-out-dir", completed.stderr)

    def test_execute_script_requires_embedded_receipt_check_for_assurance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            check_dir = root / "receipt-check"
            assurance_dir = root / "assurance"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--receipt-check-out-dir",
                    str(check_dir),
                    "--assurance-out-dir",
                    str(assurance_dir),
                ],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--assurance-out-dir requires --embedded-receipt-check-out-dir", completed.stderr)

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

    def test_receipt_check_outputs_can_be_written_from_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check = check_promoted_training_scale_seed_handoff_automation_receipt(
                {
                    "schema_version": 1,
                    "receipt_type": RECEIPT_TYPE,
                    "automation_decision": "continue",
                    "automation_exit_code": 0,
                    "automation_blocking_source": None,
                    "failed_requirements": [],
                }
            )

            outputs = write_promoted_training_scale_seed_handoff_automation_receipt_check_outputs(check, tmp)

            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["status"], "pass")
            self.assertIn("receipt_check_status=pass", Path(outputs["text"]).read_text(encoding="utf-8"))

    def test_embedded_receipt_check_accepts_inline_handoff_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"
            embedded_check_dir = root / "embedded-receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_embedded_receipt.py"),
                    str(script_out),
                    "--out-dir",
                    str(embedded_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report_path = resolve_promoted_training_scale_seed_handoff_report_path(script_out)
            report = load_promoted_training_scale_seed_handoff_report(report_path)
            check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
                report,
                base_dir=report_path.parent,
            )
            outputs = write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs(
                check,
                root / "library-embedded-check",
            )
            self.assertEqual(report_path, script_out / "promoted_training_scale_seed_handoff.json")
            self.assertEqual(check["status"], "pass")
            self.assertEqual(check["decision"], "continue")
            self.assertEqual(check["checker_exit_code"], 0)
            self.assertEqual(check["sidecar_status"], "pass")
            self.assertTrue(check["receipt_path_exists"])
            self.assertTrue(check["receipt_check_json_exists"])
            self.assertTrue(check["receipt_check_text_exists"])
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["status"], "pass")
            self.assertIn("embedded_receipt_check_status=pass", completed.stdout)
            self.assertIn("embedded_receipt_check_decision=continue", completed.stdout)
            self.assertIn("embedded_receipt_check_sidecar_status=pass", completed.stdout)
            self.assertIn("embedded_receipt_check_output_json=", completed.stdout)
            self.assertIn("embedded_receipt_check_status=pass", Path(outputs["text"]).read_text(encoding="utf-8"))
            self.assertIn("embedded_receipt_check_decision=continue", render_promoted_training_scale_seed_handoff_embedded_receipt_check(check))

    def test_embedded_receipt_check_rejects_tampered_inline_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report_path = script_out / "promoted_training_scale_seed_handoff.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            payload["receipt_check"]["decision"] = "stop"
            tampered_path = root / "tampered_handoff.json"
            tampered_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(payload)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_embedded_receipt.py"),
                    str(tampered_path),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(check["status"], "fail")
            self.assertTrue(any("receipt_check.decision" in issue for issue in check["issues"]))
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("embedded_receipt_check_status=fail", completed.stdout)

    def test_embedded_receipt_check_exits_nonzero_for_stop_unless_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(
                root,
                suite_name="standard-zh",
                include_handoff_suite_guard=True,
                include_handoff_clean_batch_review=True,
                clean_batch_review_status="review",
            )
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--require-clean-batch-review",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                capture_output=True,
                text=True,
            )
            command = [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "check_promoted_seed_handoff_embedded_receipt.py"),
                str(script_out),
            ]

            failed = subprocess.run(command, capture_output=True, text=True)
            allowed = subprocess.run(command + ["--allow-stop"], check=True, capture_output=True, text=True)

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("embedded_receipt_check_status=pass", failed.stdout)
            self.assertIn("embedded_receipt_check_decision=stop", failed.stdout)
            self.assertIn("embedded_receipt_check_status=pass", allowed.stdout)

    def test_embedded_receipt_check_rejects_tampered_check_json_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_promoted_training_scale_seed_handoff_report(script_out)
            check_json = Path(report["receipt_check_outputs"]["json"])
            payload = json.loads(check_json.read_text(encoding="utf-8"))
            payload["decision"] = "stop"
            check_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
                report,
                base_dir=script_out,
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_embedded_receipt.py"),
                    str(script_out),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(check["status"], "fail")
            self.assertEqual(check["sidecar_status"], "fail")
            self.assertTrue(any("receipt_check_outputs.json.decision" in issue for issue in check["issues"]))
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("embedded_receipt_check_sidecar_status=fail", completed.stdout)

    def test_embedded_receipt_check_rejects_tampered_check_text_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_promoted_training_scale_seed_handoff_report(script_out)
            Path(report["receipt_check_outputs"]["text"]).write_text("tampered=true\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
                report,
                base_dir=script_out,
            )

            self.assertEqual(check["status"], "fail")
            self.assertEqual(check["sidecar_status"], "fail")
            self.assertTrue(any("receipt_check_outputs.text content" in issue for issue in check["issues"]))

    def test_embedded_receipt_check_rejects_missing_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seed = write_seed_tree(root, suite_name="standard-zh", include_handoff_suite_guard=True)
            script_out = root / "script-out"
            receipt_check_dir = root / "receipt-check"

            subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "execute_promoted_training_scale_seed.py"),
                    str(seed),
                    "--out-dir",
                    str(script_out),
                    "--execute",
                    "--require-clean-evidence",
                    "--receipt-check-out-dir",
                    str(receipt_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = load_promoted_training_scale_seed_handoff_report(script_out)
            Path(report["receipt_check_outputs"]["json"]).unlink()

            check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
                report,
                base_dir=script_out,
            )

            self.assertEqual(check["status"], "fail")
            self.assertFalse(check["receipt_check_json_exists"])
            self.assertTrue(any("receipt_check_outputs.json does not exist" in issue for issue in check["issues"]))

    def test_handoff_assurance_accepts_inline_embedded_receipt_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_out, _, _ = self._write_inline_checked_handoff(root)
            out_dir = root / "assurance"

            check = check_promoted_training_scale_seed_handoff_assurance(script_out)
            outputs = write_promoted_training_scale_seed_handoff_assurance_check_outputs(check, out_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_assurance.py"),
                    str(script_out),
                    "--out-dir",
                    str(out_dir / "cli"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(check["status"], "pass")
            self.assertEqual(check["decision"], "continue")
            self.assertEqual(check["embedded_receipt_check_status"], "pass")
            self.assertEqual(check["embedded_receipt_check_sidecar_status"], "pass")
            self.assertTrue(check["embedded_receipt_check_output_json_exists"])
            self.assertTrue(check["embedded_receipt_check_output_text_exists"])
            self.assertIn("handoff_assurance_status=pass", completed.stdout)
            self.assertIn("handoff_assurance_embedded_receipt_check_sidecar_status=pass", completed.stdout)
            self.assertIn("handoff_assurance_json=", completed.stdout)
            self.assertIn("handoff_assurance_status=pass", render_promoted_training_scale_seed_handoff_assurance_check(check))
            self.assertIn("handoff_assurance_status=pass", Path(outputs["text"]).read_text(encoding="utf-8"))

    def test_handoff_assurance_smoke_script_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "smoke"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_assurance_smoke.py"),
                    "--out-dir",
                    str(out_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report_path = out_dir / "handoff" / "promoted_training_scale_seed_handoff.json"
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["handoff_assurance"]["status"], "pass")
            self.assertEqual(payload["handoff_assurance"]["decision"], "continue")
            self.assertEqual(payload["handoff_assurance"]["embedded_receipt_check_sidecar_status"], "pass")
            self.assertTrue(Path(payload["handoff_assurance_outputs"]["json"]).is_file())
            self.assertIn("status=pass", completed.stdout)
            self.assertIn("handoff_assurance_status=pass", completed.stdout)
            self.assertIn("handoff_assurance_embedded_receipt_check_sidecar_status=pass", completed.stdout)

    def test_handoff_assurance_rejects_tampered_main_embedded_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_out, _, _ = self._write_inline_checked_handoff(root)
            report_path = script_out / "promoted_training_scale_seed_handoff.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["embedded_receipt_check"]["sidecar_status"] = "fail"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_assurance(script_out)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_assurance.py"),
                    str(script_out),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(check["status"], "fail")
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(any("embedded_receipt_check.sidecar_status" in issue for issue in check["issues"]))
            self.assertIn("handoff_assurance_status=fail", completed.stdout)

    def test_handoff_assurance_rejects_missing_embedded_check_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_out, _, _ = self._write_inline_checked_handoff(root)
            report = json.loads((script_out / "promoted_training_scale_seed_handoff.json").read_text(encoding="utf-8"))
            Path(report["embedded_receipt_check_outputs"]["json"]).unlink()

            check = check_promoted_training_scale_seed_handoff_assurance(script_out)

            self.assertEqual(check["status"], "fail")
            self.assertFalse(check["embedded_receipt_check_output_json_exists"])
            self.assertTrue(any("embedded_receipt_check_outputs.json does not exist" in issue for issue in check["issues"]))


if __name__ == "__main__":
    unittest.main()
