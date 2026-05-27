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

from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke import (  # noqa: E402
    render_failure_smoke_html,
    render_failure_smoke_markdown,
    render_failure_smoke_text,
    run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke,
    write_failure_smoke_outputs,
)
from test_promoted_training_scale_seed_handoff_receipt_contract_check import write_summary  # noqa: E402
from test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class PromotedTrainingScaleSeedHandoffReceiptContractCheckFailureSmokeTests(unittest.TestCase):
    def test_failure_smoke_verifies_expected_family_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)

            smoke = run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke(
                summary_dir,
                root / "failure-smoke",
            )
            text = render_failure_smoke_text(smoke)
            markdown = render_failure_smoke_markdown(smoke)
            html = render_failure_smoke_html(smoke)

            self.assertEqual(smoke["status"], "pass")
            self.assertEqual(smoke["decision"], "failure_matrix_verified")
            self.assertEqual(smoke["scenario_count"], 4)
            self.assertEqual(smoke["verified_scenario_count"], 4)
            self.assertEqual(smoke["failed_verification_count"], 0)
            by_name = {row["scenario"]: row for row in smoke["scenario_rows"]}
            self.assertEqual(by_name["baseline"]["status"], "pass")
            self.assertEqual(by_name["baseline"]["failed_families"], [])
            self.assertEqual(by_name["tamper_summary_field"]["failed_families"], ["summary_field"])
            self.assertIn("summary.receipt_schema_version", by_name["tamper_summary_field"]["failed_targets"])
            self.assertEqual(
                by_name["tamper_contract_profile"]["failed_families"],
                ["contract_profile", "summary_field"],
            )
            self.assertIn("summary.contract_check_type_summary", by_name["tamper_contract_profile"]["failed_targets"])
            self.assertEqual(by_name["tamper_sidecar"]["failed_families"], ["sidecar"])
            self.assertTrue(
                any(
                    target.endswith("promoted_training_scale_seed_handoff_receipt_contract_summary.html")
                    for target in by_name["tamper_sidecar"]["failed_targets"]
                )
            )
            self.assertIn("receipt_contract_summary_check_failure_smoke_status=pass", text)
            self.assertIn("| tamper_contract_profile | contract_check_type_summary | fail | pass |", markdown)
            self.assertIn("<h2>Scenarios</h2>", html)
            self.assertIn("<td>tamper_sidecar</td>", html)

    def test_failure_smoke_writes_outputs_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            summary_dir = write_summary(paths["handoff"], root)
            smoke_dir = root / "failure-smoke"
            cli_dir = root / "failure-smoke-cli"

            smoke = run_promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke(summary_dir, smoke_dir)
            outputs = write_failure_smoke_outputs(smoke, smoke_dir)

            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["csv"]).is_file())
            self.assertTrue(Path(outputs["markdown"]).is_file())
            written = json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "pass")
            self.assertIn("tamper_sidecar", Path(outputs["csv"]).read_text(encoding="utf-8"))

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py"),
                    str(summary_dir),
                    "--out-dir",
                    str(cli_dir),
                    "--force",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("receipt_contract_summary_check_failure_smoke_status=pass", completed.stdout)
            self.assertTrue(
                (
                    cli_dir
                    / "promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.json"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
