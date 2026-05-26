from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from minigpt.baseline_candidate_threshold_boundary_smoke import (
    build_baseline_candidate_threshold_boundary_smoke_summary,
    build_threshold_boundary_smoke_diagnosis,
    render_baseline_candidate_threshold_boundary_smoke_text,
    write_baseline_candidate_threshold_boundary_smoke_outputs,
)
from minigpt.baseline_candidate_threshold_matrix import build_baseline_candidate_threshold_matrix, write_baseline_candidate_threshold_matrix_outputs
from scripts.run_baseline_candidate_threshold_boundary_smoke import annotate_execution_summary, main, resolve_exit_code


class BaselineCandidateThresholdBoundarySmokeTests(unittest.TestCase):
    def test_summary_records_live_smoke_matrix_and_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root / "source")
            matrix = build_baseline_candidate_threshold_matrix(summary_path, root / "matrix", thresholds="0:1:0.5")
            matrix_outputs = write_baseline_candidate_threshold_matrix_outputs(matrix, root / "matrix")

            report = build_baseline_candidate_threshold_boundary_smoke_summary(
                smoke_summary_path=summary_path,
                smoke_result={"returncode": 0, "stdout": "stdout.txt", "stderr": "stderr.txt", "command_text": "tiny smoke"},
                matrix_report=matrix,
                matrix_outputs=matrix_outputs,
                generated_at="2026-05-26T00:00:00Z",
            )
            text = render_baseline_candidate_threshold_boundary_smoke_text(report)
            outputs = write_baseline_candidate_threshold_boundary_smoke_outputs(report, root / "summary")

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "live_threshold_boundary_ready")
            self.assertEqual(report["source_mode"], "rerun_smoke")
            self.assertEqual(report["matrix"]["accept_count"], 1)
            self.assertEqual(report["matrix"]["reject_count"], 2)
            self.assertEqual(report["threshold_boundary"]["decision"], "accept_reject_boundary_observed")
            self.assertEqual(report["review_diagnosis"]["decision"], "threshold_boundary_ready")
            self.assertIn("first_rejecting_threshold=0.5", text)
            self.assertIn("review_diagnosis_status=pass", text)
            self.assertTrue(Path(outputs["json"]).is_file())

    def test_resolve_exit_code_can_require_boundary_pass(self) -> None:
        self.assertEqual(resolve_exit_code({"status": "pass", "threshold_boundary": {"status": "pass"}}, require_boundary_pass=True), 0)
        self.assertEqual(resolve_exit_code({"status": "pass", "threshold_boundary": {"status": "review"}}, require_boundary_pass=True), 2)
        self.assertEqual(resolve_exit_code({"status": "fail", "threshold_boundary": {"status": "pass"}}, require_boundary_pass=False), 1)

    def test_resolve_exit_code_can_require_diagnosis_pass(self) -> None:
        self.assertEqual(
            resolve_exit_code({"status": "pass", "review_diagnosis": {"status": "pass"}}, require_boundary_pass=False, require_diagnosis_pass=True),
            0,
        )
        self.assertEqual(
            resolve_exit_code({"status": "pass", "review_diagnosis": {"status": "review"}}, require_boundary_pass=False, require_diagnosis_pass=True),
            2,
        )
        self.assertEqual(
            resolve_exit_code({"status": "pass", "review_diagnosis": {"status": "fail"}}, require_boundary_pass=False, require_diagnosis_pass=True),
            1,
        )

    def test_execution_annotation_records_strict_gate_mode(self) -> None:
        report: dict[str, object] = {}

        annotate_execution_summary(
            report,
            require_boundary_pass=False,
            require_diagnosis_pass=True,
            expected_exit_code=2,
        )

        self.assertEqual(report["execution"]["gate_mode"], "diagnosis_strict")
        self.assertTrue(report["execution"]["require_diagnosis_pass"])
        self.assertEqual(report["execution"]["expected_exit_code"], 2)

    def test_summary_can_pass_with_review_boundary_when_smoke_and_matrix_pass(self) -> None:
        report = build_baseline_candidate_threshold_boundary_smoke_summary(
            smoke_summary_path="summary.json",
            smoke_result={"returncode": 0},
            matrix_report={"status": "pass", "threshold_boundary": {"status": "review", "decision": "no_accepting_threshold"}},
            matrix_outputs={},
            generated_at="2026-05-26T00:00:00Z",
        )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["decision"], "live_threshold_boundary_review")
        self.assertEqual(report["review_diagnosis"]["status"], "review")
        self.assertEqual(report["review_diagnosis"]["decision"], "candidate_not_accepted")
        self.assertEqual(report["review_diagnosis"]["issues"][0]["code"], "no_accepting_threshold")

    def test_diagnosis_flags_handoff_check_failures_as_blockers(self) -> None:
        diagnosis = build_threshold_boundary_smoke_diagnosis(
            smoke_status="pass",
            matrix={"status": "pass", "handoff_check_failure_count": 1, "accept_count": 0, "reject_count": 1},
            boundary={"status": "review", "decision": "no_accepting_threshold"},
        )

        self.assertEqual(diagnosis["status"], "fail")
        self.assertEqual(diagnosis["decision"], "fix_live_threshold_boundary")
        self.assertEqual(diagnosis["issues"][0]["code"], "handoff_check_failures")

    def test_cli_builds_matrix_from_mocked_live_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root / "source")
            out_dir = root / "live"

            with patch(
                "scripts.run_baseline_candidate_threshold_boundary_smoke.run_live_smoke",
                return_value=(summary_path, {"returncode": 0, "stdout": "stdout.txt", "stderr": "stderr.txt", "command_text": "tiny smoke"}),
            ):
                main(["--out-dir", str(out_dir), "--thresholds", "0:1:0.5", "--require-boundary-pass", "--force"])

            payload = json.loads((out_dir / "live-boundary-summary" / "baseline_candidate_threshold_boundary_smoke.json").read_text(encoding="utf-8"))
            matrix = json.loads((out_dir / "threshold-boundary-matrix" / "baseline_candidate_threshold_matrix.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["threshold_boundary"]["first_rejecting_threshold"], 0.5)
            self.assertEqual(matrix["threshold_count"], 3)
            self.assertEqual(payload["source_mode"], "rerun_smoke")
            self.assertEqual(payload["execution"]["gate_mode"], "boundary_strict")
            self.assertEqual(payload["execution"]["expected_exit_code"], 0)

    def test_cli_can_reuse_existing_smoke_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root / "source")
            out_dir = root / "reuse"

            with patch("scripts.run_baseline_candidate_threshold_boundary_smoke.run_live_smoke", side_effect=AssertionError("should not rerun smoke")):
                main(["--smoke-summary", str(summary_path), "--out-dir", str(out_dir), "--thresholds", "0:1:0.5", "--force"])

            payload = json.loads((out_dir / "live-boundary-summary" / "baseline_candidate_threshold_boundary_smoke.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["source_mode"], "reuse_summary")
            self.assertEqual(payload["smoke"]["source_mode"], "reuse_summary")
            self.assertEqual(payload["review_diagnosis"]["decision"], "threshold_boundary_ready")
            self.assertEqual(payload["execution"]["gate_mode"], "exploratory")

    def test_cli_diagnosis_gate_exits_two_for_review_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_rejected_smoke_summary(root / "source")
            out_dir = root / "strict"

            with self.assertRaises(SystemExit) as raised:
                main(["--smoke-summary", str(summary_path), "--out-dir", str(out_dir), "--thresholds", "0:1:0.5", "--require-diagnosis-pass", "--force"])

            self.assertEqual(raised.exception.code, 2)
            payload = json.loads((out_dir / "live-boundary-summary" / "baseline_candidate_threshold_boundary_smoke.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["review_diagnosis"]["decision"], "candidate_not_accepted")
            self.assertEqual(payload["execution"]["gate_mode"], "diagnosis_strict")
            self.assertEqual(payload["execution"]["expected_exit_code"], 2)


def _write_smoke_summary(root: Path) -> Path:
    smoke_dir = root / "smoke"
    baseline_dir = smoke_dir / "baseline"
    candidate_dir = smoke_dir / "candidate"
    (baseline_dir / "run").mkdir(parents=True)
    (candidate_dir / "run").mkdir(parents=True)
    (baseline_dir / "run" / "checkpoint.pt").write_text("baseline checkpoint", encoding="utf-8")
    (candidate_dir / "run" / "checkpoint.pt").write_text("candidate checkpoint", encoding="utf-8")
    summary_path = smoke_dir / "tiny_scorecard_comparison_smoke_summary.json"
    summary = _summary()
    summary.update(
        {
            "baseline_dir": str(baseline_dir),
            "candidate_dir": str(candidate_dir),
            "artifacts": {
                "candidate_scorecard_path": str(candidate_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json"),
                "candidate_pair_batch_path": str(candidate_dir / "run" / "pair_batch" / "pair_generation_batch.json"),
                "benchmark_history_json_path": str(smoke_dir / "benchmark-history" / "benchmark_history.json"),
            },
        }
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    return summary_path


def _write_rejected_smoke_summary(root: Path) -> Path:
    summary_path = _write_smoke_summary(root)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["scorecard_decision"] = {
        "decision_status": "blocked",
        "recommended_action": "keep_current_baseline",
        "selected_name": "tiny-baseline",
        "remediation_count": 1,
    }
    summary["candidate_smoke"]["scorecard_overall_score"] = 80.0
    summary["scorecard_comparison"]["best_by_overall_score"] = "tiny-baseline"
    summary["scorecard_comparison"]["best_by_rubric_avg_score"] = "tiny-baseline"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    return summary_path


def _summary() -> dict[str, object]:
    return {
        "status": "pass",
        "decision": "comparison-evidence-ready",
        "run_config": {
            "suite_name": "standard-zh",
            "case_token_cap": 3,
            "baseline_max_iters": 1,
            "candidate_max_iters": 2,
            "max_iters_delta": 1,
            "budget_mode": "candidate_more_iters",
            "baseline_seed": 1337,
            "candidate_seed": 2026,
        },
        "baseline_smoke": {"status": "pass", "scorecard_overall_score": 81.17, "eval_suite_case_count": 10, "pair_same_checkpoint_baseline": True},
        "candidate_smoke": {"status": "pass", "scorecard_overall_score": 81.17, "eval_suite_case_count": 10, "pair_same_checkpoint_baseline": True},
        "scorecard_comparison": {
            "best_by_overall_score": "tiny-candidate",
            "best_by_rubric_avg_score": "tiny-candidate",
            "improved_overall_count": 0,
            "regressed_overall_count": 0,
            "case_delta_count": 20,
            "case_regression_count": 0,
            "generation_quality_flag_improvement_count": 0,
            "generation_quality_flag_regression_count": 0,
            "non_comparison_ready_count": 0,
        },
        "scorecard_decision": {
            "decision_status": "promote",
            "recommended_action": "promote_selected_scorecard",
            "selected_name": "tiny-candidate",
            "remediation_count": 0,
        },
        "benchmark_history": {
            "entry_count": 1,
            "ready_count": 1,
            "model_quality_claim": "not_claimed",
            "readiness_requirement_status": "fail",
            "readiness_requirement_decision": "stop",
            "readiness_requirement_failed_reasons": ["not_real_benchmark_evidence"],
        },
        "interpretation": {"model_quality_claim": "not_claimed"},
    }


if __name__ == "__main__":
    unittest.main()
