from __future__ import annotations

import json
import hashlib
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
    build_benchmark_history_summary,
    build_ci_smoke_command,
    build_invocation_plan,
    build_summary_digest,
    parse_args,
    render_invocation_plan,
)


def write_history_artifacts(history_dir: Path) -> None:
    history_dir.mkdir(parents=True)
    payload = {
        "schema_version": 1,
        "evidence_kind": "tiny-smoke",
        "summary": {
            "entry_count": 1,
            "ready_count": 0,
            "model_quality_claim": "not_claimed",
        },
        "readiness_requirement": {
            "status": "fail",
            "decision": "stop",
            "exit_code": 1,
            "failed_reasons": ["insufficient_ready_entries", "not_real_benchmark_evidence"],
        },
        "entries": [{"name": "round", "boundary": "tiny-smoke-plumbing-evidence"}],
    }
    (history_dir / "benchmark_history.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (history_dir / "benchmark_history.csv").write_text("name,status\nround,blocked\n", encoding="utf-8")
    (history_dir / "benchmark_history.md").write_text("# Benchmark History\n", encoding="utf-8")
    (history_dir / "benchmark_history.html").write_text("<!doctype html><title>History</title>\n", encoding="utf-8")


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
        self.assertIn("summary_digest", plan)
        self.assertIn("run_tiny_scorecard_comparison_smoke.py", plan["command_text"])
        self.assertIn("suite_name=standard-zh", text)
        self.assertIn("candidate_max_iters=2", text)
        self.assertIn("decision_min_rubric_score=60.0", text)
        self.assertIn("summary_check_allow_gate_stop=True", text)
        self.assertIn("returncode=0", text)
        self.assertIn("benchmark_history_json_sha256=", text)
        self.assertIn("benchmark_history_html_sha256=", text)
        self.assertEqual(plan["benchmark_history_summary"]["parse_status"], "missing")
        self.assertIn("benchmark_history_parse_status=missing", text)

    def test_build_summary_digest_records_artifact_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "check"
            out_dir.mkdir()
            check_dir.mkdir()
            summary_json = b'{"status":"pass"}\n'
            check_json = b'{"status":"pass","decision":"continue"}\n'
            (out_dir / "tiny_scorecard_comparison_smoke_summary.json").write_bytes(summary_json)
            (out_dir / "tiny_scorecard_comparison_smoke_summary.txt").write_text("status=pass\n", encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.json").write_bytes(check_json)
            write_history_artifacts(out_dir / "benchmark-history")

            digest = build_summary_digest(out_dir, check_dir)
            artifacts = digest["artifacts"]

            self.assertTrue(artifacts["summary_json"]["exists"])
            self.assertEqual(artifacts["summary_json"]["sha256"], hashlib.sha256(summary_json).hexdigest())
            self.assertTrue(artifacts["summary_text"]["exists"])
            self.assertTrue(artifacts["summary_check_json"]["exists"])
            self.assertEqual(artifacts["summary_check_json"]["sha256"], hashlib.sha256(check_json).hexdigest())
            self.assertFalse(artifacts["summary_check_text"]["exists"])
            self.assertEqual(artifacts["summary_check_text"]["sha256"], "")
            self.assertTrue(artifacts["benchmark_history_json"]["exists"])
            self.assertTrue(artifacts["benchmark_history_csv"]["exists"])
            self.assertTrue(artifacts["benchmark_history_markdown"]["exists"])
            self.assertTrue(artifacts["benchmark_history_html"]["exists"])
            self.assertTrue(artifacts["benchmark_history_html"]["sha256"])

    def test_build_benchmark_history_summary_reads_tiny_smoke_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "smoke"
            write_history_artifacts(out_dir / "benchmark-history")

            summary = build_benchmark_history_summary(out_dir)

            self.assertTrue(summary["available"])
            self.assertEqual(summary["parse_status"], "pass")
            self.assertEqual(summary["evidence_kind"], "tiny-smoke")
            self.assertEqual(summary["entry_count"], 1)
            self.assertEqual(summary["ready_count"], 0)
            self.assertEqual(summary["model_quality_claim"], "not_claimed")
            self.assertEqual(summary["readiness_requirement_status"], "fail")
            self.assertIn("not_real_benchmark_evidence", summary["readiness_requirement_failed_reasons"])
            self.assertEqual(summary["latest_boundary"], "tiny-smoke-plumbing-evidence")

    def test_invocation_plan_renders_history_boundary_after_artifacts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "check"
            out_dir.mkdir()
            check_dir.mkdir()
            write_history_artifacts(out_dir / "benchmark-history")
            args = parse_args(["--out-dir", str(out_dir), "--summary-check-out-dir", str(check_dir)])
            command = build_ci_smoke_command(args)

            plan = build_invocation_plan(args, command, returncode=0)
            text = render_invocation_plan(plan)

            self.assertEqual(plan["benchmark_history_summary"]["evidence_kind"], "tiny-smoke")
            self.assertEqual(plan["benchmark_history_summary"]["model_quality_claim"], "not_claimed")
            self.assertIn("benchmark_history_evidence_kind=tiny-smoke", text)
            self.assertIn("benchmark_history_model_quality_claim=not_claimed", text)
            self.assertIn(
                "benchmark_history_readiness_requirement_failed_reasons=insufficient_ready_entries,not_real_benchmark_evidence",
                text,
            )
            self.assertIn("benchmark_history_latest_boundary=tiny-smoke-plumbing-evidence", text)

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
            self.assertEqual(plan["returncode"], 0)
            self.assertEqual(plan["benchmark_history_summary"]["evidence_kind"], "tiny-smoke")
            self.assertEqual(plan["benchmark_history_summary"]["model_quality_claim"], "not_claimed")
            self.assertEqual(plan["benchmark_history_summary"]["readiness_requirement_status"], "fail")
            self.assertIn("not_real_benchmark_evidence", plan["benchmark_history_summary"]["readiness_requirement_failed_reasons"])
            self.assertIn("benchmark_history_evidence_kind=tiny-smoke", plan_text_path.read_text(encoding="utf-8"))
            self.assertIn("benchmark_history_model_quality_claim=not_claimed", plan_text_path.read_text(encoding="utf-8"))
            artifacts = plan["summary_digest"]["artifacts"]
            self.assertTrue(artifacts["summary_json"]["exists"])
            self.assertTrue(artifacts["summary_json"]["sha256"])
            self.assertTrue(artifacts["summary_text"]["exists"])
            self.assertTrue(artifacts["summary_check_json"]["exists"])
            self.assertTrue(artifacts["summary_check_text"]["exists"])
            self.assertTrue(artifacts["benchmark_history_json"]["exists"])
            self.assertTrue(artifacts["benchmark_history_csv"]["exists"])
            self.assertTrue(artifacts["benchmark_history_markdown"]["exists"])
            self.assertTrue(artifacts["benchmark_history_html"]["exists"])
            self.assertIn("ci_plan_json=", completed.stdout)
            self.assertIn("ci_plan_text=", completed.stdout)
            self.assertTrue((out_dir / "tiny_scorecard_comparison_smoke_summary.json").is_file())
            self.assertTrue((out_dir / "benchmark-history" / "benchmark_history.json").is_file())
            self.assertTrue((check_dir / "tiny_scorecard_comparison_smoke_check.json").is_file())


if __name__ == "__main__":
    unittest.main()
