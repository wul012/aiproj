from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_ci_baseline_candidate_threshold_boundary_gate_plan import (  # noqa: E402
    check_plan,
    render_check,
    resolve_plan_path,
    write_check_outputs,
)
from scripts.run_ci_baseline_candidate_threshold_boundary_gate_check import (  # noqa: E402
    PLAN_JSON_FILENAME,
    build_artifact_digest,
    build_gate_check_summary,
)


class CIBaselineCandidateThresholdBoundaryGatePlanCheckTests(unittest.TestCase):
    def test_check_plan_passes_when_recorded_digests_and_gate_summary_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "gate"
            _write_gate_outputs(out_dir)
            plan = _build_plan(out_dir)

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)
            text = render_check(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "continue")
            self.assertEqual(report["artifact_count"], 5)
            self.assertEqual(report["artifact_failure_count"], 0)
            self.assertEqual(report["gate_check"]["status"], "pass")
            self.assertIn("gate_check_status=pass", text)
            self.assertIn("gate_check_actual_exit_code=2", text)
            self.assertIn("gate_check_json_status=pass", text)

    def test_check_plan_fails_when_gate_check_digest_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "gate"
            _write_gate_outputs(out_dir)
            plan = _build_plan(out_dir)
            (out_dir / "gate-check" / "baseline_candidate_threshold_boundary_gate_check.txt").write_text(
                "status=changed\n",
                encoding="utf-8",
            )

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["artifact_failure_count"], 1)
            self.assertEqual(report["issues"][0]["code"], "artifact_digest_mismatch")
            self.assertEqual(report["issues"][0]["target"], "gate_check_text")

    def test_check_plan_fails_when_expected_exit_contract_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "gate"
            _write_gate_outputs(out_dir)
            plan = _build_plan(out_dir)
            plan["gate_check_summary"]["expected_exit_code"] = 0

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)
            issue_codes = {issue["code"] for issue in report["issues"]}

            self.assertEqual(report["status"], "fail")
            self.assertIn("gate_summary_mismatch", issue_codes)

    def test_write_check_outputs_and_resolve_plan_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / PLAN_JSON_FILENAME
            plan_path.write_text('{"returncode": 0, "artifact_digest": {"artifacts": {}}}\n', encoding="utf-8")
            report = {"status": "pass", "decision": "continue", "artifacts": [], "issues": []}

            outputs = write_check_outputs(report, root / "check")

            self.assertEqual(resolve_plan_path(root), plan_path)
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["text"]).is_file())

    def test_checker_cli_validates_real_wrapper_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "boundary-gate-ci"
            plan_check_dir = root / "plan-check"

            subprocess.run(
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
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_ci_baseline_candidate_threshold_boundary_gate_plan.py"),
                    str(out_dir),
                    "--out-dir",
                    str(plan_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report = json.loads(
                (plan_check_dir / "ci_baseline_candidate_threshold_boundary_gate_check_plan_check.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["artifact_failure_count"], 0)
            self.assertEqual(report["artifact_count"], 5)
            self.assertEqual(report["gate_check"]["actual_exit_code"], 2)
            self.assertEqual(report["gate_check"]["expected_exit_code"], 2)
            self.assertIn("status=pass", completed.stdout)
            self.assertIn("gate_check_json_status=pass", completed.stdout)
            self.assertIn("gate_check_actual_exit_code=2", completed.stdout)


def _build_plan(out_dir: Path) -> dict[str, object]:
    return {
        "wrapper": "run_ci_baseline_candidate_threshold_boundary_gate_check",
        "returncode": 0,
        "config": {
            "thresholds": "0:1:0.5",
            "require_diagnosis_pass": True,
            "expected_exit_code": 2,
            "expected_diagnosis_decision": "candidate_not_accepted",
            "require_pass": True,
        },
        "gate_check_summary": build_gate_check_summary(out_dir),
        "artifact_digest": build_artifact_digest(out_dir),
    }


def _write_gate_outputs(out_dir: Path) -> None:
    gate_dir = out_dir / "gate-check"
    smoke_dir = out_dir / "threshold-boundary-smoke" / "live-boundary-summary"
    gate_dir.mkdir(parents=True, exist_ok=True)
    smoke_dir.mkdir(parents=True, exist_ok=True)
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
    (gate_dir / "baseline_candidate_threshold_boundary_gate_check.txt").write_text("status=pass\n", encoding="utf-8")
    (gate_dir / "baseline_candidate_threshold_boundary_gate_check.md").write_text("# Gate Check\n", encoding="utf-8")
    (gate_dir / "baseline_candidate_threshold_boundary_gate_check.html").write_text("<!doctype html><title>Gate</title>\n", encoding="utf-8")
    (smoke_dir / "baseline_candidate_threshold_boundary_smoke.json").write_text('{"status":"pass"}\n', encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
