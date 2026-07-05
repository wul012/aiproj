from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

SCRIPT = ROOT / "scripts" / "check_release_readiness_drift_contract_smoke.py"


class ReleaseReadinessDriftContractSmokeTests(unittest.TestCase):
    def test_smoke_script_writes_summary_and_contract_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "smoke"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--out-dir", str(out_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("status=pass", result.stdout)
            summary_path = out_dir / "release_readiness_drift_contract_smoke_summary.json"
            check_path = out_dir / "check" / "release_readiness_drift_contract_check.json"
            comparison_path = out_dir / "comparison" / "release_readiness_comparison.json"
            self.assertTrue(summary_path.exists())
            self.assertTrue(check_path.exists())
            self.assertTrue(comparison_path.exists())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            check = json.loads(check_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["check_status"], "pass")
            self.assertEqual(summary["check_expected_mixed_delta_count"], 1)
            self.assertEqual(summary["check_actual_mixed_delta_count"], 1)
            self.assertEqual(check["expected_summary"]["benchmark_history_readiness_requirement_failed_reason_drift_status_counts"], {"mixed": 1})
            self.assertTrue((out_dir / "release_readiness_drift_contract_smoke_summary.txt").exists())
            self.assertTrue((out_dir / "check" / "release_readiness_drift_contract_check.txt").exists())


if __name__ == "__main__":
    unittest.main()
