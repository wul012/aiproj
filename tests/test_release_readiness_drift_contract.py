from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from minigpt.release_readiness_drift_contract import (
    check_release_readiness_drift_contract,
    resolve_release_readiness_comparison_path,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_release_readiness_drift_contract.py"


def make_mixed_comparison() -> dict:
    return {
        "schema_version": 1,
        "summary": {
            "benchmark_history_readiness_requirement_failed_reason_added_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_removed_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_added": ["tiny_smoke_only"],
            "benchmark_history_readiness_requirement_failed_reason_removed": ["legacy_fixture_gap"],
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count": 0,
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count": 1,
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts": {"mixed": 1},
        },
        "deltas": [
            {
                "baseline_release": "baseline",
                "compared_release": "candidate",
                "baseline_benchmark_history_readiness_requirement_failed_reasons": [
                    "insufficient_ready_entries",
                    "legacy_fixture_gap",
                ],
                "compared_benchmark_history_readiness_requirement_failed_reasons": [
                    "insufficient_ready_entries",
                    "tiny_smoke_only",
                ],
                "benchmark_history_readiness_requirement_failed_reason_added_count": 1,
                "benchmark_history_readiness_requirement_failed_reason_removed_count": 1,
                "benchmark_history_readiness_requirement_failed_reason_added": ["tiny_smoke_only"],
                "benchmark_history_readiness_requirement_failed_reason_removed": ["legacy_fixture_gap"],
                "benchmark_history_readiness_requirement_failed_reason_drift_status": "mixed",
            }
        ],
    }


class ReleaseReadinessDriftContractTests(unittest.TestCase):
    def test_check_release_readiness_drift_contract_accepts_valid_mixed_report(self) -> None:
        report = check_release_readiness_drift_contract(make_mixed_comparison(), comparison_path="comparison.json")

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "continue")
        self.assertEqual(report["delta_fail_count"], 0)
        self.assertEqual(report["expected_summary"]["benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"], 1)
        self.assertEqual(
            report["actual_summary"]["benchmark_history_readiness_requirement_failed_reason_drift_status_counts"],
            {"mixed": 1},
        )

    def test_check_release_readiness_drift_contract_reports_summary_mixed_count_mismatch(self) -> None:
        comparison = make_mixed_comparison()
        comparison["summary"]["benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"] = 0

        report = check_release_readiness_drift_contract(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertIn("summary_mixed_delta_count_mismatch", {issue["code"] for issue in report["issues"]})
        self.assertEqual(report["delta_fail_count"], 0)

    def test_check_release_readiness_drift_contract_reports_delta_status_mismatch(self) -> None:
        comparison = make_mixed_comparison()
        comparison["deltas"][0]["benchmark_history_readiness_requirement_failed_reason_drift_status"] = "recovered"

        report = check_release_readiness_drift_contract(comparison)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["delta_fail_count"], 1)
        self.assertIn("delta_failed_reason_drift_status_mismatch", {issue["code"] for issue in report["issues"]})

    def test_resolve_release_readiness_comparison_path_accepts_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison_path = root / "release_readiness_comparison.json"
            comparison_path.write_text(json.dumps(make_mixed_comparison()), encoding="utf-8")

            self.assertEqual(resolve_release_readiness_comparison_path(root), comparison_path)

    def test_script_writes_outputs_and_exits_nonzero_for_invalid_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison = make_mixed_comparison()
            comparison["summary"]["benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"] = 0
            comparison_path = root / "release_readiness_comparison.json"
            comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
            out_dir = root / "check"

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--out-dir", str(out_dir)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("status=fail", result.stdout)
            self.assertTrue((out_dir / "release_readiness_drift_contract_check.json").exists())
            self.assertTrue((out_dir / "release_readiness_drift_contract_check.txt").exists())


if __name__ == "__main__":
    unittest.main()
