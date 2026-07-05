from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from scripts.run_ci_baseline_candidate_threshold_boundary_gate_check import (  # noqa: E402
    CI_BOUNDARY_GATE_CONFIG,
    PLAN_JSON_FILENAME,
    PLAN_TEXT_FILENAME,
    build_ci_boundary_gate_command,
    build_gate_check_summary,
    build_invocation_plan,
    parse_args,
    render_invocation_plan,
)


class CIBaselineCandidateThresholdBoundaryGateCheckTests(unittest.TestCase):
    def test_build_ci_boundary_gate_command_preserves_expected_exit_contract(self) -> None:
        args = parse_args(["--out-dir", "runs/boundary-gate-ci", "--force"])

        command_text = " ".join(build_ci_boundary_gate_command(args)).replace("\\", "/")

        self.assertEqual(CI_BOUNDARY_GATE_CONFIG["thresholds"], "0:1:0.5")
        self.assertEqual(CI_BOUNDARY_GATE_CONFIG["expected_exit_code"], 2)
        self.assertEqual(CI_BOUNDARY_GATE_CONFIG["expected_diagnosis_decision"], "candidate_not_accepted")
        self.assertIn("scripts/check_baseline_candidate_threshold_boundary_gate.py", command_text)
        self.assertIn("--thresholds 0:1:0.5", command_text)
        self.assertIn("--require-diagnosis-pass", command_text)
        self.assertIn("--expected-exit-code 2", command_text)
        self.assertIn("--expected-diagnosis-decision candidate_not_accepted", command_text)
        self.assertIn("--require-pass", command_text)
        self.assertTrue(command_text.endswith("--force"))

    def test_invocation_plan_records_missing_gate_check_before_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "gate"
            args = parse_args(["--out-dir", str(out_dir)])
            command = build_ci_boundary_gate_command(args)

            plan = build_invocation_plan(args, command, returncode=None)
            text = render_invocation_plan(plan)

            self.assertEqual(plan["wrapper"], "run_ci_baseline_candidate_threshold_boundary_gate_check")
            self.assertEqual(plan["config"]["expected_exit_code"], 2)
            self.assertFalse(plan["gate_check_summary"]["available"])
            self.assertIn("gate_check_available=False", text)
            self.assertIn("gate_check_json_sha256=", text)

    def test_gate_check_summary_reads_expected_exit_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "gate"
            _write_gate_check(out_dir)

            summary = build_gate_check_summary(out_dir)

            self.assertTrue(summary["available"])
            self.assertEqual(summary["parse_status"], "pass")
            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["decision"], "expected_exit_verified")
            self.assertEqual(summary["actual_exit_code"], 2)
            self.assertEqual(summary["expected_exit_code"], 2)

    def test_wrapper_writes_invocation_plan_after_running_gate_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "boundary-gate-ci"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_ci_baseline_candidate_threshold_boundary_gate_check.py"),
                    "--out-dir",
                    str(out_dir),
                    "--force",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            plan_path = out_dir / PLAN_JSON_FILENAME
            plan_text_path = out_dir / PLAN_TEXT_FILENAME
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            self.assertIn("ci_boundary_gate_plan_json=", completed.stdout)
            self.assertIn("ci_boundary_gate_plan_text=", completed.stdout)
            self.assertTrue(plan_path.is_file())
            self.assertTrue(plan_text_path.is_file())
            self.assertEqual(plan["returncode"], 0)
            self.assertEqual(plan["config"]["expected_exit_code"], 2)
            self.assertEqual(plan["gate_check_summary"]["status"], "pass")
            self.assertEqual(plan["gate_check_summary"]["decision"], "expected_exit_verified")
            self.assertEqual(plan["gate_check_summary"]["actual_exit_code"], 2)
            self.assertEqual(plan["gate_check_summary"]["expected_exit_code"], 2)
            self.assertTrue(plan["artifact_digest"]["artifacts"]["gate_check_json"]["exists"])
            self.assertTrue(plan["artifact_digest"]["artifacts"]["gate_check_json"]["sha256"])
            self.assertTrue(plan["artifact_digest"]["artifacts"]["boundary_smoke_json"]["exists"])
            self.assertIn("gate_check_status=pass", plan_text_path.read_text(encoding="utf-8"))
            self.assertIn("gate_check_actual_exit_code=2", plan_text_path.read_text(encoding="utf-8"))


def _write_gate_check(out_dir: Path) -> None:
    gate_dir = out_dir / "gate-check"
    gate_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "pass",
        "decision": "expected_exit_verified",
        "failed_count": 0,
        "actual_exit_code": 2,
        "expected_exit_code": 2,
        "diagnosis_decision": "candidate_not_accepted",
        "boundary_decision": "no_accepting_threshold",
    }
    (gate_dir / "baseline_candidate_threshold_boundary_gate_check.json").write_text(
        json.dumps(payload, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
