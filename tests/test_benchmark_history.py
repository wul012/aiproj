from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt import build_benchmark_history as facade_build_benchmark_history
from minigpt.benchmark_history import (
    build_benchmark_history,
    build_benchmark_history_readiness_requirement,
    render_benchmark_history_html,
    render_benchmark_history_markdown,
    write_benchmark_history_outputs,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def make_comparison(root: Path, name: str, *, decision_status: str = "promote", rubric_delta: float = 5.0, flags_delta: int = -2) -> tuple[Path, Path]:
    comparison_path = root / name / "benchmark_scorecard_comparison.json"
    decision_path = root / name / "decision" / "benchmark_scorecard_decision.json"
    comparison = {
        "schema_version": 1,
        "title": f"{name} comparison",
        "scorecard_count": 2,
        "baseline": {"name": "baseline", "source_path": str(root / name / "baseline.json")},
        "summary": {
            "baseline_name": "baseline",
            "scorecard_count": 2,
            "case_regression_count": 0 if decision_status == "promote" else 1,
            "case_improvement_count": 2,
            "non_comparison_ready_count": 0 if decision_status != "review" else 1,
        },
        "runs": [
            {
                "name": "baseline",
                "overall_score": 80.0,
                "rubric_avg_score": 80.0,
                "generation_quality_total_flags": 4,
                "eval_suite_comparison_status": "pass",
            },
            {
                "name": "candidate",
                "overall_score": 84.0,
                "rubric_avg_score": 80.0 + rubric_delta,
                "generation_quality_total_flags": 4 + flags_delta,
                "eval_suite_comparison_status": "pass" if decision_status != "review" else "warn",
            },
        ],
        "baseline_deltas": [
            {"name": "baseline", "is_baseline": True, "overall_score_delta": 0.0, "rubric_avg_score_delta": 0.0},
            {
                "name": "candidate",
                "is_baseline": False,
                "overall_score_delta": 4.0,
                "rubric_avg_score_delta": rubric_delta,
                "overall_relation": "improved" if rubric_delta >= 0 else "regressed",
                "rubric_relation": "improved" if rubric_delta >= 0 else "regressed",
                "generation_quality_total_flags_delta": flags_delta,
                "generation_quality_flag_relation": "improved" if flags_delta < 0 else "regressed" if flags_delta > 0 else "same",
                "generation_quality_dominant_flag_changed": flags_delta > 0,
                "generation_quality_worst_case_changed": flags_delta > 0,
            },
        ],
    }
    selected = None if decision_status == "blocked" else {
        "name": "candidate",
        "overall_score": 84.0,
        "rubric_avg_score": 80.0 + rubric_delta,
        "eval_suite_comparison_status": "pass" if decision_status != "review" else "warn",
        "case_regression_count": 0 if decision_status == "promote" else 1,
        "case_improvement_count": 2,
    }
    decision = {
        "schema_version": 1,
        "decision_status": decision_status,
        "recommended_action": "promote_selected_scorecard" if decision_status == "promote" else "review_generation_flags_and_case_deltas",
        "selected_run": selected,
        "summary": {
            "decision_status": decision_status,
            "remediation_plan_count": 0 if decision_status == "promote" else 1,
        },
    }
    write_json(comparison_path, comparison)
    write_json(decision_path, decision)
    return comparison_path, decision_path


class BenchmarkHistoryTests(unittest.TestCase):
    def test_build_history_records_decision_and_delta_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison, decision = make_comparison(Path(tmp), "round-1")

            report = build_benchmark_history([comparison], decision_paths=[decision], names=["round 1"], generated_at="2026-05-21T00:00:00Z")

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["summary"]["entry_count"], 1)
            self.assertEqual(report["summary"]["promote_count"], 1)
            self.assertEqual(report["summary"]["ready_count"], 1)
            self.assertEqual(report["summary"]["best_candidate_name"], "candidate")
            self.assertEqual(report["summary"]["model_quality_claim"], "candidate_evidence")
            self.assertEqual(report["readiness_requirement"]["status"], "pass")
            self.assertEqual(report["readiness_requirement"]["exit_code"], 0)
            entry = report["entries"][0]
            self.assertEqual(entry["name"], "round 1")
            self.assertEqual(entry["baseline_name"], "baseline")
            self.assertEqual(entry["candidate_name"], "candidate")
            self.assertEqual(entry["promotion_readiness"], "ready")
            self.assertEqual(entry["rubric_avg_score_delta"], 5.0)
            self.assertEqual(entry["generation_quality_total_flags_delta"], -2)
            self.assertEqual(entry["boundary"], "standard-benchmark-candidate-evidence")
            self.assertIn("real benchmark comparisons", " ".join(report["recommendations"]))

    def test_history_keeps_tiny_smoke_boundary_and_review_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            comparison, decision = make_comparison(Path(tmp), "tiny", decision_status="review", rubric_delta=2.0, flags_delta=3)

            report = build_benchmark_history([comparison], decision_paths=[decision], evidence_kind="tiny-smoke")

            self.assertEqual(report["summary"]["review_count"], 1)
            self.assertEqual(report["summary"]["generation_quality_flag_regression_entry_count"], 1)
            self.assertEqual(report["summary"]["model_quality_claim"], "not_claimed")
            self.assertEqual(report["readiness_requirement"]["status"], "fail")
            self.assertIn("not_real_benchmark_evidence", report["readiness_requirement"]["failed_reasons"])
            self.assertEqual(report["entries"][0]["promotion_readiness"], "review")
            self.assertEqual(report["entries"][0]["boundary"], "tiny-smoke-plumbing-evidence")
            self.assertIn("Tiny-smoke history is plumbing evidence", " ".join(report["recommendations"]))

    def test_write_outputs_renderers_and_facade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison, decision = make_comparison(root, "round-1")
            report = build_benchmark_history([comparison], decision_paths=[decision], title="<History>")

            outputs = write_benchmark_history_outputs(report, root / "out")
            markdown = render_benchmark_history_markdown(report)
            html = render_benchmark_history_html(report)

            self.assertIs(facade_build_benchmark_history, build_benchmark_history)
            self.assertEqual(set(outputs), {"json", "csv", "markdown", "html"})
            self.assertIn("benchmark_history", Path(outputs["json"]).name)
            self.assertIn("rubric_avg_score_delta", Path(outputs["csv"]).read_text(encoding="utf-8"))
            self.assertIn("## Ledger", markdown)
            self.assertIn("Readiness requirement: `pass`", markdown)
            self.assertIn("&lt;History&gt;", html)
            self.assertIn("Readiness Requirement", html)
            self.assertIn("standard-benchmark-candidate-evidence", html)

    def test_readiness_requirement_can_require_more_ready_entries(self) -> None:
        requirement = build_benchmark_history_readiness_requirement(
            {
                "entry_count": 1,
                "ready_count": 1,
                "case_regression_entry_count": 0,
                "generation_quality_flag_regression_entry_count": 0,
            },
            evidence_kind="real-benchmark",
            min_ready_entries=2,
        )

        self.assertEqual(requirement["status"], "fail")
        self.assertEqual(requirement["decision"], "stop")
        self.assertEqual(requirement["exit_code"], 1)
        self.assertIn("insufficient_ready_entries", requirement["failed_reasons"])

    def test_cli_writes_history_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison, decision = make_comparison(root, "round-1")
            out_dir = root / "history"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_benchmark_history.py"),
                    str(comparison),
                    "--decisions",
                    str(decision),
                    "--names",
                    "round-1",
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("entry_count=1", completed.stdout)
            self.assertIn("model_quality_claim=candidate_evidence", completed.stdout)
            self.assertIn("readiness_requirement_status=pass", completed.stdout)
            self.assertTrue((out_dir / "benchmark_history.json").is_file())

    def test_cli_can_fail_on_missing_real_ready_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison, decision = make_comparison(root, "tiny", decision_status="review", rubric_delta=1.0, flags_delta=2)
            out_dir = root / "history"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(ROOT / "scripts" / "build_benchmark_history.py"),
                    str(comparison),
                    "--decisions",
                    str(decision),
                    "--evidence-kind",
                    "tiny-smoke",
                    "--require-ready-history",
                    "--out-dir",
                    str(out_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("readiness_requirement_status=fail", completed.stdout)
            self.assertIn("readiness_requirement_exit_code=1", completed.stdout)
            self.assertIn("not_real_benchmark_evidence", completed.stdout)
            payload = json.loads((out_dir / "benchmark_history.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["readiness_requirement"]["status"], "fail")

    def test_directory_resolution_accepts_smoke_style_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            comparison, decision = make_comparison(root, "round-1")
            smoke_root = root / "smoke"
            smoke_comparison = smoke_root / "scorecard-comparison" / "benchmark_scorecard_comparison.json"
            smoke_decision = smoke_root / "scorecard-decision" / "benchmark_scorecard_decision.json"
            smoke_comparison.parent.mkdir(parents=True, exist_ok=True)
            smoke_decision.parent.mkdir(parents=True, exist_ok=True)
            smoke_comparison.write_text(comparison.read_text(encoding="utf-8"), encoding="utf-8")
            smoke_decision.write_text(decision.read_text(encoding="utf-8"), encoding="utf-8")

            report = build_benchmark_history([smoke_root], decision_paths=[smoke_root])

            self.assertEqual(report["summary"]["entry_count"], 1)
            self.assertTrue(report["entries"][0]["comparison_path"].endswith("scorecard-comparison\\benchmark_scorecard_comparison.json") or report["entries"][0]["comparison_path"].endswith("scorecard-comparison/benchmark_scorecard_comparison.json"))
            self.assertTrue(report["entries"][0]["decision_path"].endswith("scorecard-decision\\benchmark_scorecard_decision.json") or report["entries"][0]["decision_path"].endswith("scorecard-decision/benchmark_scorecard_decision.json"))


if __name__ == "__main__":
    unittest.main()
