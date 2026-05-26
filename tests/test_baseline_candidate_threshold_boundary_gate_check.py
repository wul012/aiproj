from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from minigpt.baseline_candidate_threshold_boundary_gate_check import (
    build_threshold_boundary_gate_check,
    render_threshold_boundary_gate_check_text,
    write_threshold_boundary_gate_check_outputs,
)
from scripts.check_baseline_candidate_threshold_boundary_gate import main


class BaselineCandidateThresholdBoundaryGateCheckTests(unittest.TestCase):
    def test_gate_check_passes_when_actual_exit_matches_expected_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_boundary_summary(root / "summary.json", expected_exit=2, diagnosis="candidate_not_accepted")

            report = build_threshold_boundary_gate_check(
                summary_path,
                actual_exit_code=2,
                expected_exit_code=2,
                expected_diagnosis_decision="candidate_not_accepted",
                generated_at="2026-05-26T00:00:00Z",
            )
            text = render_threshold_boundary_gate_check_text(report)
            outputs = write_threshold_boundary_gate_check_outputs(report, root / "out")

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "expected_exit_verified")
            self.assertEqual(report["actual_exit_code"], 2)
            self.assertIn("failed_count=0", text)
            self.assertTrue(Path(outputs["html"]).is_file())

    def test_gate_check_fails_when_actual_exit_differs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_boundary_summary(root / "summary.json", expected_exit=2, diagnosis="candidate_not_accepted")

            report = build_threshold_boundary_gate_check(
                summary_path,
                actual_exit_code=0,
                expected_exit_code=2,
                expected_diagnosis_decision="candidate_not_accepted",
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["failed_count"], 1)
            self.assertEqual(_check_by_id(report, "actual_exit_matches_expected")["status"], "fail")

    def test_gate_check_writes_failure_report_when_summary_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_summary = root / "missing.json"

            report = build_threshold_boundary_gate_check(
                missing_summary,
                actual_exit_code=1,
                expected_exit_code=2,
                expected_diagnosis_decision="candidate_not_accepted",
            )
            outputs = write_threshold_boundary_gate_check_outputs(report, root / "out")

            self.assertEqual(report["status"], "fail")
            self.assertEqual(_check_by_id(report, "summary_exists")["status"], "fail")
            self.assertEqual(_check_by_id(report, "summary_loads")["status"], "fail")
            self.assertTrue(Path(outputs["json"]).is_file())

    def test_cli_wraps_expected_nonzero_exit_as_passing_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            smoke_summary = _write_smoke_summary(root / "smoke" / "tiny_scorecard_comparison_smoke_summary.json")
            out_dir = root / "gate"

            with patch("scripts.check_baseline_candidate_threshold_boundary_gate.subprocess.run", side_effect=_fake_runner(2)):
                main(
                    [
                        "--smoke-summary",
                        str(smoke_summary),
                        "--out-dir",
                        str(out_dir),
                        "--require-diagnosis-pass",
                        "--expected-exit-code",
                        "2",
                        "--expected-diagnosis-decision",
                        "candidate_not_accepted",
                        "--require-pass",
                        "--force",
                    ]
                )

            payload = json.loads((out_dir / "gate-check" / "baseline_candidate_threshold_boundary_gate_check.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["actual_exit_code"], 2)
            self.assertEqual(payload["expected_exit_code"], 2)

    def test_cli_require_pass_fails_on_unexpected_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            smoke_summary = _write_smoke_summary(root / "smoke" / "tiny_scorecard_comparison_smoke_summary.json")
            out_dir = root / "gate"

            with patch("scripts.check_baseline_candidate_threshold_boundary_gate.subprocess.run", side_effect=_fake_runner(2)):
                with self.assertRaises(SystemExit) as raised:
                    main(
                        [
                            "--smoke-summary",
                            str(smoke_summary),
                            "--out-dir",
                            str(out_dir),
                            "--require-diagnosis-pass",
                            "--expected-exit-code",
                            "0",
                            "--require-pass",
                            "--force",
                        ]
                    )

            self.assertEqual(raised.exception.code, 1)
            payload = json.loads((out_dir / "gate-check" / "baseline_candidate_threshold_boundary_gate_check.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "fail")


def _fake_runner(returncode: int):
    def run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        out_dir = Path(command[command.index("--out-dir") + 1])
        _write_boundary_summary(
            out_dir / "live-boundary-summary" / "baseline_candidate_threshold_boundary_smoke.json",
            expected_exit=returncode,
            diagnosis="candidate_not_accepted",
        )
        return subprocess.CompletedProcess(command, returncode, stdout="runner stdout", stderr="")

    return run


def _write_smoke_summary(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": "pass"}, ensure_ascii=False), encoding="utf-8")
    return path


def _write_boundary_summary(path: Path, *, expected_exit: int, diagnosis: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "pass",
        "decision": "live_threshold_boundary_review",
        "execution": {
            "gate_mode": "diagnosis_strict",
            "require_diagnosis_pass": True,
            "expected_exit_code": expected_exit,
        },
        "review_diagnosis": {"status": "review", "decision": diagnosis},
        "threshold_boundary": {"status": "review", "decision": "no_accepting_threshold"},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _check_by_id(report: dict[str, object], check_id: str) -> dict[str, object]:
    checks = report.get("checks")
    if not isinstance(checks, list):
        raise AssertionError("report checks must be a list")
    for check in checks:
        if isinstance(check, dict) and check.get("id") == check_id:
            return check
    raise AssertionError(f"missing check: {check_id}")


if __name__ == "__main__":
    unittest.main()
