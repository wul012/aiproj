from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_ci_tiny_scorecard_comparison_smoke import (  # noqa: E402
    CI_TINY_SCORECARD_CONFIG,
    PLAN_JSON_FILENAME,
    PLAN_TEXT_FILENAME,
    build_ci_smoke_command,
    build_invocation_plan,
    parse_args,
    render_invocation_plan,
)


class CITinyScorecardSmokeTests(unittest.TestCase):
    def test_build_ci_smoke_command_preserves_fixed_budget_and_summary_check_contract(self) -> None:
        args = parse_args(
            [
                "--out-dir",
                "runs/ci-smoke",
                "--summary-check-out-dir",
                "runs/ci-smoke-check",
                "--force",
            ]
        )

        command = build_ci_smoke_command(args)
        command_text = " ".join(command).replace("\\", "/")

        self.assertEqual(CI_TINY_SCORECARD_CONFIG["suite_name"], "standard-zh")
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["baseline_max_iters"], 1)
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["candidate_max_iters"], 2)
        self.assertEqual(CI_TINY_SCORECARD_CONFIG["decision_min_rubric_score"], 60.0)
        self.assertIn("scripts/run_tiny_scorecard_comparison_smoke.py", command_text)
        self.assertIn("--suite-name standard-zh", command_text)
        self.assertIn("--case-token-cap 3", command_text)
        self.assertIn("--baseline-max-iters 1", command_text)
        self.assertIn("--candidate-max-iters 2", command_text)
        self.assertIn("--decision-min-rubric-score 60.0", command_text)
        self.assertIn("--summary-check-out-dir runs/ci-smoke-check", command_text)
        self.assertTrue(command_text.endswith("--force"))

    def test_build_ci_smoke_command_preserves_optional_summary_check_flags(self) -> None:
        args = parse_args(
            [
                "--summary-check-allow-gate-stop",
                "--summary-check-no-fail",
            ]
        )

        command_text = " ".join(build_ci_smoke_command(args))

        self.assertIn("--summary-check-allow-gate-stop", command_text)
        self.assertIn("--summary-check-no-fail", command_text)

    def test_invocation_plan_records_wrapper_config_and_command(self) -> None:
        args = parse_args(
            [
                "--out-dir",
                "runs/ci-smoke",
                "--summary-check-out-dir",
                "runs/ci-smoke-check",
                "--summary-check-allow-gate-stop",
                "--force",
            ]
        )
        command = build_ci_smoke_command(args)

        plan = build_invocation_plan(args, command, returncode=0)
        text = render_invocation_plan(plan)

        self.assertEqual(plan["schema_version"], 1)
        self.assertEqual(plan["wrapper"], "run_ci_tiny_scorecard_comparison_smoke")
        self.assertEqual(plan["config"], CI_TINY_SCORECARD_CONFIG)
        self.assertTrue(plan["flags"]["summary_check_allow_gate_stop"])
        self.assertFalse(plan["flags"]["summary_check_no_fail"])
        self.assertTrue(plan["flags"]["force"])
        self.assertEqual(plan["returncode"], 0)
        self.assertIn("run_tiny_scorecard_comparison_smoke.py", plan["command_text"])
        self.assertIn("suite_name=standard-zh", text)
        self.assertIn("candidate_max_iters=2", text)
        self.assertIn("decision_min_rubric_score=60.0", text)
        self.assertIn("summary_check_allow_gate_stop=True", text)
        self.assertIn("returncode=0", text)

    def test_wrapper_writes_invocation_plan_after_running_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "ci-smoke"
            check_dir = Path(tmp) / "ci-smoke-check"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "run_ci_tiny_scorecard_comparison_smoke.py"),
                    "--out-dir",
                    str(out_dir),
                    "--summary-check-out-dir",
                    str(check_dir),
                    "--force",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            plan_path = out_dir / PLAN_JSON_FILENAME
            plan_text_path = out_dir / PLAN_TEXT_FILENAME
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            self.assertTrue(plan_path.is_file())
            self.assertTrue(plan_text_path.is_file())
            self.assertEqual(plan["config"]["suite_name"], "standard-zh")
            self.assertEqual(plan["config"]["candidate_max_iters"], 2)
            self.assertEqual(plan["config"]["decision_min_rubric_score"], 60.0)
            self.assertEqual(plan["summary_check_out_dir"], str(check_dir))
            self.assertIn("ci_plan_json=", completed.stdout)
            self.assertIn("ci_plan_text=", completed.stdout)
            self.assertTrue((out_dir / "tiny_scorecard_comparison_smoke_summary.json").is_file())
            self.assertTrue((check_dir / "tiny_scorecard_comparison_smoke_check.json").is_file())


if __name__ == "__main__":
    unittest.main()
