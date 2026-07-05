from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests._bootstrap import ROOT

from scripts.check_ci_tiny_scorecard_plan import (  # noqa: E402
    check_plan,
    render_check,
    resolve_plan_path,
    write_check_outputs,
)
from scripts.run_ci_tiny_scorecard_comparison_smoke import (  # noqa: E402
    PLAN_JSON_FILENAME,
    build_summary_digest,
)


def write_history_artifacts(history_dir: Path, *, evidence_kind: str = "tiny-smoke", model_quality_claim: str = "not_claimed") -> None:
    history_dir.mkdir()
    payload = {
        "schema_version": 1,
        "evidence_kind": evidence_kind,
        "summary": {
            "entry_count": 1,
            "ready_count": 0,
            "model_quality_claim": model_quality_claim,
        },
        "readiness_requirement": {
            "status": "fail",
            "decision": "stop",
            "exit_code": 1,
            "failed_reasons": ["insufficient_ready_entries", "not_real_benchmark_evidence"],
        },
        "entries": [
            {
                "name": "round",
                "boundary": "tiny-smoke-plumbing-evidence",
            }
        ],
    }
    (history_dir / "benchmark_history.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (history_dir / "benchmark_history.csv").write_text("name,status\nround,blocked\n", encoding="utf-8")
    (history_dir / "benchmark_history.md").write_text("# Benchmark History\n", encoding="utf-8")
    (history_dir / "benchmark_history.html").write_text("<!doctype html><title>History</title>\n", encoding="utf-8")


class CITinyScorecardPlanCheckTests(unittest.TestCase):
    def test_check_plan_passes_when_recorded_digests_match_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "check"
            out_dir.mkdir()
            check_dir.mkdir()
            (out_dir / "tiny_scorecard_comparison_smoke_summary.json").write_text('{"status":"pass"}\n', encoding="utf-8")
            (out_dir / "tiny_scorecard_comparison_smoke_summary.txt").write_text("status=pass\n", encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.json").write_text('{"status":"pass"}\n', encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.txt").write_text("status=pass\n", encoding="utf-8")
            write_history_artifacts(out_dir / "benchmark-history")
            plan = {
                "wrapper": "run_ci_tiny_scorecard_comparison_smoke",
                "returncode": 0,
                "summary_digest": build_summary_digest(out_dir, check_dir),
            }

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)
            text = render_check(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "continue")
            self.assertEqual(report["artifact_count"], 8)
            self.assertEqual(report["artifact_failure_count"], 0)
            self.assertTrue(report["benchmark_history"]["available"])
            self.assertEqual(report["benchmark_history"]["evidence_kind"], "tiny-smoke")
            self.assertEqual(report["benchmark_history"]["model_quality_claim"], "not_claimed")
            self.assertEqual(report["benchmark_history"]["readiness_requirement_status"], "fail")
            self.assertIn("summary_json_status=pass", text)
            self.assertIn("summary_check_text_status=pass", text)
            self.assertIn("benchmark_history_json_status=pass", text)
            self.assertIn("benchmark_history_html_status=pass", text)
            self.assertIn("benchmark_history_evidence_kind=tiny-smoke", text)
            self.assertIn("benchmark_history_model_quality_claim=not_claimed", text)
            self.assertIn("benchmark_history_readiness_requirement_failed_reasons=insufficient_ready_entries,not_real_benchmark_evidence", text)

    def test_check_plan_fails_when_artifact_digest_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "check"
            out_dir.mkdir()
            check_dir.mkdir()
            summary_path = out_dir / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            (out_dir / "tiny_scorecard_comparison_smoke_summary.txt").write_text("status=pass\n", encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.json").write_text('{"status":"pass"}\n', encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.txt").write_text("status=pass\n", encoding="utf-8")
            write_history_artifacts(out_dir / "benchmark-history")
            plan = {
                "wrapper": "run_ci_tiny_scorecard_comparison_smoke",
                "returncode": 0,
                "summary_digest": build_summary_digest(out_dir, check_dir),
            }
            summary_path.write_text('{"status":"changed"}\n', encoding="utf-8")

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["artifact_failure_count"], 1)
            self.assertEqual(report["issues"][0]["code"], "artifact_digest_mismatch")
            self.assertEqual(report["issues"][0]["target"], "summary_json")

    def test_check_plan_fails_when_ci_history_claims_real_benchmark_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "check"
            out_dir.mkdir()
            check_dir.mkdir()
            (out_dir / "tiny_scorecard_comparison_smoke_summary.json").write_text('{"status":"pass"}\n', encoding="utf-8")
            (out_dir / "tiny_scorecard_comparison_smoke_summary.txt").write_text("status=pass\n", encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.json").write_text('{"status":"pass"}\n', encoding="utf-8")
            (check_dir / "tiny_scorecard_comparison_smoke_check.txt").write_text("status=pass\n", encoding="utf-8")
            write_history_artifacts(out_dir / "benchmark-history", evidence_kind="real-benchmark", model_quality_claim="candidate_evidence")
            plan = {
                "wrapper": "run_ci_tiny_scorecard_comparison_smoke",
                "returncode": 0,
                "summary_digest": build_summary_digest(out_dir, check_dir),
            }

            report = check_plan(plan, plan_path=out_dir / PLAN_JSON_FILENAME)
            issue_codes = {issue["code"] for issue in report["issues"]}

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["benchmark_history"]["evidence_kind"], "real-benchmark")
            self.assertIn("benchmark_history_kind_mismatch", issue_codes)
            self.assertIn("benchmark_history_model_claim_unexpected", issue_codes)

    def test_write_check_outputs_and_resolve_plan_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / PLAN_JSON_FILENAME
            plan_path.write_text('{"returncode": 0, "summary_digest": {"artifacts": {}}}\n', encoding="utf-8")
            report = {"status": "pass", "decision": "continue", "artifacts": [], "issues": []}

            outputs = write_check_outputs(report, root / "check")

            self.assertEqual(resolve_plan_path(root), plan_path)
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["text"]).is_file())

    def test_checker_cli_validates_real_wrapper_smoke_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "smoke"
            check_dir = root / "summary-check"
            plan_check_dir = root / "plan-check"

            subprocess.run(
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
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "check_ci_tiny_scorecard_plan.py"),
                    str(out_dir),
                    "--out-dir",
                    str(plan_check_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report = json.loads((plan_check_dir / "ci_tiny_scorecard_smoke_plan_check.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["artifact_failure_count"], 0)
            self.assertEqual(report["artifact_count"], 8)
            self.assertEqual(report["benchmark_history"]["evidence_kind"], "tiny-smoke")
            self.assertEqual(report["benchmark_history"]["model_quality_claim"], "not_claimed")
            self.assertEqual(report["benchmark_history"]["readiness_requirement_status"], "fail")
            self.assertIn("not_real_benchmark_evidence", report["benchmark_history"]["readiness_requirement_failed_reasons"])
            self.assertIn("status=pass", completed.stdout)
            self.assertIn("summary_json_status=pass", completed.stdout)
            self.assertIn("benchmark_history_json_status=pass", completed.stdout)
            self.assertIn("benchmark_history_evidence_kind=tiny-smoke", completed.stdout)
            self.assertIn("benchmark_history_model_quality_claim=not_claimed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
