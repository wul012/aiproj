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
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
)
from test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class PromotedTrainingScaleSeedHandoffReceiptContractTests(unittest.TestCase):
    def test_contract_summary_flattens_schema_v3_suite_design_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_suite_design_handoff_with_sidecars(Path(tmp))

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])
            text = render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary)
            markdown = render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary)
            html = render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary)

            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["receipt_schema_version"], 3)
            self.assertTrue(summary["schema_v3_ready"])
            self.assertEqual(summary["embedded_receipt_check_sidecar_status"], "pass")
            self.assertEqual(
                {
                    item["scope"]: (item["count"], item["names"], item["count_matches_names"])
                    for item in summary["suite_design_scopes"]
                },
                {
                    "selected": (0, [], True),
                    "handoff": (2, ["beta-suite", "standard"], True),
                    "comparison_ready": (0, [], True),
                },
            )
            self.assertIn("receipt_contract_handoff_suite_design_count=2", text)
            self.assertIn("| handoff | 2 | beta-suite, standard | True |", markdown)
            self.assertIn("<td>handoff</td>", html)

    def test_contract_summary_rejects_tampered_suite_design_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_suite_design_handoff_with_sidecars(Path(tmp))
            check_path = paths["receipt_check"] / "promoted_training_scale_seed_handoff_automation_receipt_check.json"
            payload = json.loads(check_path.read_text(encoding="utf-8"))
            payload["handoff_batch_maturity_suite_design_regression_names"] = ["beta-suite"]
            check_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(paths["handoff"])

            self.assertEqual(summary["status"], "fail")
            self.assertEqual(summary["assurance_status"], "fail")
            self.assertTrue(any("handoff assurance must pass" in issue for issue in summary["issues"]))
            self.assertTrue(
                any(
                    "receipt_check_outputs.json.handoff_batch_maturity_suite_design_regression_names"
                    in issue
                    for issue in summary["issues"]
                )
            )

    def test_cli_writes_contract_summary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            out_dir = root / "contract-summary"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_promoted_seed_handoff_receipt_contract.py"),
                    str(paths["handoff"]),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            summary = json.loads(
                (out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(summary["status"], "pass")
            self.assertIn("receipt_contract_status=pass", completed.stdout)
            self.assertIn("receipt_contract_html=", completed.stdout)
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.txt").is_file())
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.md").is_file())
            self.assertTrue((out_dir / "promoted_training_scale_seed_handoff_receipt_contract_summary.html").is_file())


if __name__ == "__main__":
    unittest.main()
