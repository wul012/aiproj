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

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check import (  # noqa: E402
    check_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text,
)
from test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class PromotedTrainingScaleSeedHandoffReceiptContractCheckTests(unittest.TestCase):
    def test_contract_summary_check_rebuilds_expected_summary_and_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check)

            self.assertEqual(check["status"], "pass")
            self.assertEqual(check["actual_summary_status"], "pass")
            self.assertEqual(check["expected_summary_status"], "pass")
            self.assertEqual(check["sidecar_status"], "pass")
            self.assertIn("receipt_contract_summary_check_status=pass", text)
            self.assertIn("- Sidecar status: `pass`", markdown)
            self.assertIn("<strong>pass</strong>", html)

    def test_contract_summary_check_rejects_tampered_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["receipt_schema_version"] = 2
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertTrue(any("summary.receipt_schema_version expected 4 but got 2" in issue for issue in check["issues"]))

    def test_contract_summary_check_rejects_tampered_boundary_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            summary_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["ci_boundary_plan_check_scopes"][1]["handoff_count"] = 9
            summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertTrue(
                any("summary.ci_boundary_plan_check_scopes" in issue for issue in check["issues"])
            )

    def test_contract_summary_check_rejects_tampered_html_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            html_path = summary_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.html"
            html_path.write_text(html_path.read_text(encoding="utf-8") + "\n<!-- stale -->\n", encoding="utf-8")

            check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(summary_dir)

            self.assertEqual(check["status"], "fail")
            self.assertEqual(check["sidecar_status"], "fail")
            self.assertTrue(any("contract_summary.html content does not match" in issue for issue in check["issues"]))

    def test_cli_writes_contract_summary_check_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            check_dir = root / "contract-summary-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt_contract_summary.py"),
                    str(summary_dir),
                    "--out-dir",
                    str(check_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            check = json.loads(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(check["status"], "pass")
            self.assertIn("receipt_contract_summary_check_status=pass", completed.stdout)
            self.assertIn("receipt_contract_summary_check_html=", completed.stdout)
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt").is_file()
            )
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.md").is_file()
            )
            self.assertTrue(
                (check_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary_check.html").is_file()
            )


def write_summary(handoff_dir: Path, root: Path) -> Path:
    summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(handoff_dir)
    summary_dir = root / "contract-summary"
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(summary, summary_dir)
    return summary_dir


if __name__ == "__main__":
    unittest.main()
