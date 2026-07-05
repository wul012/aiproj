from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from scripts.run_ci_promoted_seed_receipt_contract_failure_smoke import (  # noqa: E402
    DEFAULT_SOURCE_HANDOFF,
    PLAN_JSON_FILENAME,
    PLAN_TEXT_FILENAME,
    build_failure_smoke_summary,
    render_invocation_plan,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (  # noqa: E402
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
)
from tests.test_promoted_training_scale_seed_handoff_receipt_suite_design import (  # noqa: E402
    write_suite_design_handoff_with_sidecars,
)


class CiPromotedSeedReceiptContractFailureSmokeTests(unittest.TestCase):
    def test_default_source_handoff_stays_repository_relative(self) -> None:
        self.assertEqual(
            DEFAULT_SOURCE_HANDOFF,
            Path("d") / "448" / "解释" / "promoted-handoff",
        )

    def test_default_archived_source_handoff_contract_summary_accepts_windows_path_sidecars(self) -> None:
        source_handoff = DEFAULT_SOURCE_HANDOFF
        if not (ROOT / source_handoff).is_dir():
            self.skipTest(f"archived source handoff fixture is unavailable: {ROOT / source_handoff}")

        summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(source_handoff)

        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["assurance_status"], "pass")
        self.assertEqual(summary["embedded_receipt_check_status"], "pass")
        self.assertEqual(summary["embedded_receipt_check_sidecar_status"], "pass")
        self.assertTrue(summary["receipt_check_output_json_exists"])
        self.assertTrue(summary["receipt_check_output_text_exists"])

    def test_wrapper_runs_summary_and_failure_smoke_with_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_suite_design_handoff_with_sidecars(root)
            out_dir = root / "ci-receipt-failure-smoke"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_ci_promoted_seed_receipt_contract_failure_smoke.py"),
                    "--source-handoff",
                    str(paths["handoff"]),
                    "--out-dir",
                    str(out_dir),
                    "--force",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            plan_path = out_dir / PLAN_JSON_FILENAME
            text_path = out_dir / PLAN_TEXT_FILENAME
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            smoke_summary = build_failure_smoke_summary(out_dir / "receipt-contract-failure-smoke")
            text = text_path.read_text(encoding="utf-8")

            self.assertIn("ci_promoted_receipt_failure_smoke_plan_json=", completed.stdout)
            self.assertEqual(plan["status"], "pass")
            self.assertEqual(plan["decision"], "receipt_contract_failure_smoke_verified")
            self.assertEqual(plan["wrapper"], "run_ci_promoted_seed_receipt_contract_failure_smoke")
            self.assertEqual(plan["commands"][0]["name"], "receipt_contract_summary")
            self.assertEqual(plan["commands"][0]["returncode"], 0)
            self.assertEqual(plan["commands"][1]["name"], "receipt_contract_failure_smoke")
            self.assertEqual(plan["commands"][1]["returncode"], 0)
            self.assertEqual(plan["failure_smoke_summary"]["status"], "pass")
            self.assertEqual(plan["failure_smoke_summary"]["scenario_count"], 4)
            self.assertEqual(plan["failure_smoke_summary"]["failed_verification_count"], 0)
            self.assertEqual(smoke_summary["status"], "pass")
            self.assertIn("failure_smoke_status=pass", text)
            self.assertIn("failure_smoke_failed_verification_count=0", render_invocation_plan(plan))
            self.assertTrue(
                plan["artifact_digest"]["artifacts"]["contract_summary_json"]["exists"]
            )
            self.assertTrue(plan["artifact_digest"]["artifacts"]["failure_smoke_json"]["exists"])
            self.assertTrue(plan["artifact_digest"]["artifacts"]["failure_smoke_html"]["sha256"])


if __name__ == "__main__":
    unittest.main()
