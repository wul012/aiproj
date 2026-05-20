from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from scripts.check_tiny_scorecard_comparison_smoke import (  # noqa: E402
    CHECK_JSON_FILENAME,
    CHECK_TEXT_FILENAME,
    SUMMARY_JSON_FILENAME,
    check_summary,
    render_check,
    resolve_summary_path,
)


def valid_summary() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "comparison-evidence-ready",
        "commands": [
            {"name": "baseline_smoke", "status": "pass"},
            {"name": "candidate_smoke", "status": "pass"},
            {"name": "scorecard_comparison", "status": "pass"},
            {"name": "scorecard_decision", "status": "pass"},
        ],
        "artifacts": {
            "baseline_smoke_summary_exists": True,
            "baseline_scorecard_exists": True,
            "candidate_smoke_summary_exists": True,
            "candidate_scorecard_exists": True,
            "comparison_json_exists": True,
            "comparison_html_exists": True,
            "decision_json_exists": True,
            "decision_remediation_csv_exists": True,
            "decision_html_exists": True,
        },
        "remediation_gate": {
            "status": "pass",
            "decision": "continue",
            "issue_count": 0,
            "issues": [],
        },
        "interpretation": {"model_quality_claim": "not_claimed"},
    }


class TinyScorecardComparisonSmokeCheckTests(unittest.TestCase):
    def test_check_summary_accepts_valid_summary(self) -> None:
        report = check_summary(valid_summary(), summary_path=Path("summary.json"))

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "continue")
        self.assertEqual(report["command_count"], 4)
        self.assertEqual(report["command_failure_count"], 0)
        self.assertEqual(report["required_artifact_failure_count"], 0)
        self.assertEqual(report["model_quality_claim"], "not_claimed")
        text = render_check(report)
        self.assertIn("status=pass", text)
        self.assertIn("decision=continue", text)
        self.assertIn("remediation_gate_issue_count=0", text)
        self.assertIn("decision_remediation_csv_exists=True", text)

    def test_check_summary_blocks_unexpected_gate_stop(self) -> None:
        summary = valid_summary()
        summary["status"] = "fail"
        summary["decision"] = "fix-comparison-smoke-chain"
        summary["remediation_gate"] = {
            "status": "fail",
            "decision": "stop",
            "issue_count": 1,
            "issues": [
                {
                    "code": "remediation_rows_present",
                    "severity": "blocker",
                    "category": "threshold",
                    "action_code": "raise_candidate_rubric_or_change_policy",
                    "owner_scope": "model-eval",
                }
            ],
        }

        report = check_summary(summary)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "fix-smoke-summary")
        self.assertFalse(report["allowed_gate_stop"])
        self.assertEqual(report["remediation_gate_first_issue_code"], "remediation_rows_present")
        self.assertEqual(report["remediation_gate_first_issue_action_code"], "raise_candidate_rubric_or_change_policy")
        self.assertEqual(report["issues"][0]["code"], "smoke_status_not_pass")

    def test_check_summary_can_allow_expected_gate_stop(self) -> None:
        summary = valid_summary()
        summary["status"] = "fail"
        summary["decision"] = "fix-comparison-smoke-chain"
        summary["remediation_gate"] = {
            "status": "fail",
            "decision": "stop",
            "issue_count": 1,
            "issues": [{"code": "remediation_rows_present", "severity": "blocker"}],
        }

        report = check_summary(summary, allow_gate_stop=True)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "allowed-gate-stop")
        self.assertTrue(report["allowed_gate_stop"])
        self.assertEqual(report["issue_count"], 0)
        self.assertEqual(report["remediation_gate_first_issue_code"], "remediation_rows_present")

    def test_check_summary_reports_missing_artifacts_and_claims(self) -> None:
        summary = valid_summary()
        summary["artifacts"] = {}
        summary["interpretation"] = {"model_quality_claim": "claimed"}
        summary["remediation_gate"] = {"status": "pass", "decision": "continue", "issue_count": "not-a-number"}

        report = check_summary(summary)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["remediation_gate_issue_count"], 0)
        self.assertEqual(report["required_artifact_failure_count"], 9)
        self.assertIn("baseline_smoke_summary_exists", report["required_artifact_failures"])
        issue_codes = [issue["code"] for issue in report["issues"]]
        self.assertIn("model_quality_claim_not_guarded", issue_codes)
        self.assertIn("required_artifact_missing", issue_codes)

    def test_cli_writes_check_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_dir = root / "smoke"
            out_dir = root / "check"
            summary_dir.mkdir()
            (summary_dir / SUMMARY_JSON_FILENAME).write_text(json.dumps(valid_summary()), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_tiny_scorecard_comparison_smoke.py"),
                    str(summary_dir),
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("status=pass", completed.stdout)
            self.assertEqual(resolve_summary_path(summary_dir), summary_dir / SUMMARY_JSON_FILENAME)
            self.assertTrue((out_dir / CHECK_JSON_FILENAME).is_file())
            self.assertTrue((out_dir / CHECK_TEXT_FILENAME).is_file())
            report = json.loads((out_dir / CHECK_JSON_FILENAME).read_text(encoding="utf-8"))
            self.assertEqual(report["decision"], "continue")


if __name__ == "__main__":
    unittest.main()
