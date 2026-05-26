from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.baseline_candidate_threshold_matrix import (
    build_baseline_candidate_threshold_matrix,
    parse_thresholds,
    render_baseline_candidate_threshold_matrix_text,
    summarize_threshold_boundary,
    write_baseline_candidate_threshold_matrix_outputs,
)
from scripts.run_baseline_candidate_threshold_matrix import main, resolve_exit_code


class BaselineCandidateThresholdMatrixTests(unittest.TestCase):
    def test_matrix_records_accept_and_reject_threshold_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root)

            report = build_baseline_candidate_threshold_matrix(
                summary_path,
                root / "matrix",
                thresholds=[0.0, 0.5, 1.0],
                generated_at="2026-05-26T00:00:00Z",
            )
            text = render_baseline_candidate_threshold_matrix_text(report)
            boundary = report["threshold_boundary"]

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["accept_count"], 1)
            self.assertEqual(report["reject_count"], 2)
            self.assertEqual(report["handoff_check_failure_count"], 0)
            self.assertEqual(report["rows"][0]["loop_decision"], "accept_candidate")
            self.assertEqual(report["rows"][0]["next_baseline_source"], "candidate")
            self.assertEqual(report["rows"][1]["loop_decision"], "reject_candidate")
            self.assertEqual(report["rows"][1]["next_baseline_source"], "current_baseline")
            self.assertEqual(boundary["status"], "pass")
            self.assertEqual(boundary["decision"], "accept_reject_boundary_observed")
            self.assertEqual(boundary["strictest_accepting_threshold"], 0.0)
            self.assertEqual(boundary["first_rejecting_threshold"], 0.5)
            self.assertTrue(boundary["is_monotonic_acceptance"])
            self.assertEqual(boundary["transition_count"], 1)
            self.assertIn("accept_count=1", text)
            self.assertIn("threshold_boundary_decision=accept_reject_boundary_observed", text)
            self.assertIn("first_rejecting_threshold=0.5", text)
            self.assertEqual(resolve_exit_code(report, require_both_outcomes=True), 0)

    def test_matrix_writes_outputs_and_embedded_handoff_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root)
            out_dir = root / "matrix"
            report = build_baseline_candidate_threshold_matrix(summary_path, out_dir, thresholds=[0.0], generated_at="2026-05-26T00:00:00Z")

            outputs = write_baseline_candidate_threshold_matrix_outputs(report, out_dir)

            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["text"]).is_file())
            self.assertTrue((out_dir / "threshold-0" / "loop" / "baseline_candidate_eval_loop.json").is_file())
            handoff = json.loads((out_dir / "threshold-0" / "handoff" / "baseline_candidate_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["handoff_check"]["status"], "pass")
            self.assertTrue((out_dir / "threshold-0" / "handoff-check" / "baseline_candidate_handoff_check.json").is_file())

    def test_parse_thresholds_rejects_empty_values(self) -> None:
        self.assertEqual(parse_thresholds("0, 1.5"), [0.0, 1.5])
        self.assertEqual(parse_thresholds("0:1:0.5"), [0.0, 0.5, 1.0])
        with self.assertRaises(ValueError):
            parse_thresholds("")
        with self.assertRaises(ValueError):
            parse_thresholds("0:1:0")

    def test_boundary_summary_marks_non_monotonic_rows_for_review(self) -> None:
        summary = summarize_threshold_boundary(
            [
                {"threshold": 0.0, "loop_decision": "accept_candidate"},
                {"threshold": 0.5, "loop_decision": "reject_candidate"},
                {"threshold": 1.0, "loop_decision": "accept_candidate"},
            ]
        )

        self.assertEqual(summary["status"], "review")
        self.assertEqual(summary["decision"], "non_monotonic_threshold_outcomes")
        self.assertFalse(summary["is_monotonic_acceptance"])
        self.assertEqual(summary["transition_count"], 2)

    def test_cli_require_both_outcomes_returns_two_when_only_accepts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = _write_smoke_summary(root)

            with self.assertRaises(SystemExit) as raised:
                main([str(summary_path), "--out-dir", str(root / "matrix"), "--thresholds", "0", "--require-both-outcomes", "--force"])

            self.assertEqual(raised.exception.code, 2)
            payload = json.loads((root / "matrix" / "baseline_candidate_threshold_matrix.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["accept_count"], 1)
            self.assertEqual(payload["reject_count"], 0)


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
        "baseline_smoke": {
            "status": "pass",
            "scorecard_overall_status": "pass",
            "scorecard_overall_score": 81.17,
            "eval_suite_case_count": 10,
            "pair_same_checkpoint_baseline": True,
        },
        "candidate_smoke": {
            "status": "pass",
            "scorecard_overall_status": "pass",
            "scorecard_overall_score": 81.17,
            "eval_suite_case_count": 10,
            "pair_same_checkpoint_baseline": True,
        },
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
            "first_blocker": None,
            "first_review_item": None,
            "first_recommendation": None,
            "first_threshold_margin": None,
            "remediation_count": 0,
        },
        "benchmark_history": {
            "entry_count": 1,
            "ready_count": 1,
            "model_quality_claim": "not_claimed",
            "readiness_requirement_status": "fail",
            "readiness_requirement_decision": "stop",
            "readiness_requirement_failed_reasons": ["not_real_benchmark_evidence"],
            "outputs": {"json": "history/benchmark_history.json"},
        },
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": "Tiny CPU scorecard deltas verify benchmark plumbing, not robust model improvement.",
        },
    }


if __name__ == "__main__":
    unittest.main()
