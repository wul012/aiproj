from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from minigpt.baseline_candidate_eval_loop import (
    build_baseline_candidate_eval_loop_report,
    render_baseline_candidate_eval_loop_text,
    write_baseline_candidate_eval_loop_outputs,
)
from scripts.run_baseline_candidate_eval_loop import (
    annotate_execution_summary,
    build_smoke_command,
    main,
    prepare_output_dir,
    resolve_exit_code,
)


class BaselineCandidateEvalLoopTests(unittest.TestCase):
    def test_report_accepts_promoted_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text(
                json.dumps(_summary(decision_status="promote", selected_name="tiny-candidate"), ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_baseline_candidate_eval_loop_report(summary_path, generated_at="2026-05-25T00:00:00Z")
            text = render_baseline_candidate_eval_loop_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "accept_candidate")
            self.assertEqual(report["experiment"]["controlled_variable"], "max_iters")
            self.assertEqual(report["delta_report"]["overall_score_delta"], 3.5)
            self.assertEqual(report["control_summary"]["status"], "pass")
            self.assertEqual(report["control_summary"]["failed_count"], 0)
            self.assertEqual(report["acceptance_criteria"]["status"], "pass")
            self.assertEqual(report["acceptance_criteria"]["failed_count"], 0)
            self.assertEqual(report["acceptance_criteria"]["min_overall_score_delta"], 0.0)
            self.assertTrue(report["promotion_decision"]["accepted"])
            self.assertEqual(report["promotion_decision"]["rejected_reasons"], [])
            self.assertEqual(report["next_action"], "accept_candidate_as_next_experiment_baseline")
            self.assertIn("decision=accept_candidate", text)
            self.assertIn("promotion_accepted=True", text)
            self.assertIn("control_status=pass", text)
            self.assertIn("acceptance_status=pass", text)
            self.assertIn("min_overall_score_delta=0.0", text)
            self.assertIn("overall_score_delta=3.5", text)

    def test_report_rejects_blocked_candidate_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text(
                json.dumps(
                    _summary(
                        decision_status="blocked",
                        selected_name=None,
                        first_blocker="rubric_avg_score below 60.0",
                        first_recommendation="Keep the current baseline and improve candidate evidence.",
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_baseline_candidate_eval_loop_report(summary_path, generated_at="2026-05-25T00:00:00Z")
            text = render_baseline_candidate_eval_loop_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "reject_candidate")
            self.assertFalse(report["promotion_decision"]["accepted"])
            rejected_reasons = report["promotion_decision"]["rejected_reasons"]
            self.assertIn("rubric_avg_score below 60.0", rejected_reasons)
            self.assertIn("Keep the current baseline and improve candidate evidence.", rejected_reasons)
            self.assertIn("scorecard_decision_promote expected promote, got blocked", rejected_reasons)
            self.assertIn("selected_candidate expected tiny-candidate, got None", rejected_reasons)
            self.assertEqual(report["next_action"], "keep_baseline_and_fix_candidate")
            self.assertIn("decision=reject_candidate", text)
            self.assertIn("promotion_status=blocked", text)
            self.assertIn("rubric_avg_score below 60.0", text)

    def test_report_rejects_promoted_candidate_when_control_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text(
                json.dumps(
                    _summary(
                        decision_status="promote",
                        selected_name="tiny-candidate",
                        baseline_score=75.5,
                        candidate_score=72.0,
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            report = build_baseline_candidate_eval_loop_report(summary_path, generated_at="2026-05-25T00:00:00Z")
            text = render_baseline_candidate_eval_loop_text(report)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "reject_candidate")
            self.assertEqual(report["control_summary"]["status"], "fail")
            self.assertEqual(report["acceptance_criteria"]["status"], "fail")
            self.assertFalse(report["promotion_decision"]["accepted"])
            self.assertIn("candidate_not_lower_overall_score", report["promotion_decision"]["rejected_reasons"][0])
            self.assertIn("control_failed_count=1", text)
            self.assertIn("acceptance_failed_count=2", text)

    def test_report_rejects_promoted_candidate_when_min_score_delta_not_met(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text(
                json.dumps(_summary(decision_status="promote", selected_name="tiny-candidate"), ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_baseline_candidate_eval_loop_report(
                summary_path,
                generated_at="2026-05-25T00:00:00Z",
                min_overall_score_delta=4.0,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decision"], "reject_candidate")
            self.assertEqual(report["control_summary"]["status"], "pass")
            self.assertEqual(report["acceptance_criteria"]["status"], "fail")
            self.assertFalse(report["promotion_decision"]["accepted"])
            self.assertEqual(report["promotion_decision"]["rejected_reasons"], ["min_overall_score_delta expected >= 4.0, got 3.5"])

    def test_write_outputs_persists_all_loop_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "smoke.json"
            summary_path.write_text(json.dumps(_summary(decision_status="promote", selected_name="tiny-candidate")), encoding="utf-8")
            report = build_baseline_candidate_eval_loop_report(summary_path, generated_at="2026-05-25T00:00:00Z")

            outputs = write_baseline_candidate_eval_loop_outputs(report, root / "loop")

            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["text"]).is_file())
            self.assertTrue(Path(outputs["markdown"]).is_file())
            self.assertTrue(Path(outputs["html"]).is_file())
            self.assertEqual(json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))["decision"], "accept_candidate")
            self.assertIn("Candidate accepted: `True`", Path(outputs["markdown"]).read_text(encoding="utf-8"))

    def test_smoke_command_uses_fixed_baseline_and_candidate_inputs(self) -> None:
        class Args:
            suite_name = "standard-zh"
            case_token_cap = 3
            baseline_max_iters = 1
            candidate_max_iters = 2
            decision_min_rubric_score = 60.0
            min_overall_score_delta = 0.0
            eval_iters = 1
            batch_size = 2
            block_size = 8
            n_layer = 1
            n_head = 1
            n_embd = 8
            baseline_seed = 1337
            candidate_seed = 2026

        command = build_smoke_command(Args(), Path("out/smoke"), Path("out/check"))
        command_text = " ".join(command)

        self.assertIn("run_tiny_scorecard_comparison_smoke.py", command_text)
        self.assertIn("--baseline-max-iters 1", command_text)
        self.assertIn("--candidate-max-iters 2", command_text)
        self.assertIn(f"--summary-check-out-dir {Path('out/check')}", command_text)

    def test_exit_code_keeps_reject_as_success_for_experiment_mode(self) -> None:
        report = {"status": "pass", "decision": "reject_candidate"}

        self.assertEqual(resolve_exit_code(report, smoke_returncode=0, fail_on_reject=False), 0)

    def test_exit_code_fails_reject_for_gate_mode(self) -> None:
        reject_report = {"status": "pass", "decision": "reject_candidate"}
        accept_report = {"status": "pass", "decision": "accept_candidate"}
        failed_report = {"status": "fail", "decision": "fix_loop"}

        self.assertEqual(resolve_exit_code(reject_report, smoke_returncode=0, fail_on_reject=True), 2)
        self.assertEqual(resolve_exit_code(accept_report, smoke_returncode=0, fail_on_reject=True), 0)
        self.assertEqual(resolve_exit_code(failed_report, smoke_returncode=7, fail_on_reject=True), 7)

    def test_annotate_execution_summary_records_gate_mode(self) -> None:
        report = {"status": "pass", "decision": "reject_candidate"}

        result = annotate_execution_summary(report, source_mode="reuse_summary", fail_on_reject=True, expected_exit_code=2)

        self.assertIs(result, report)
        self.assertEqual(report["execution"]["source_mode"], "reuse_summary")
        self.assertEqual(report["execution"]["gate_mode"], "strict")
        self.assertTrue(report["execution"]["fail_on_reject"])
        self.assertEqual(report["execution"]["expected_exit_code"], 2)
        self.assertIn("execution_expected_exit_code=2", render_baseline_candidate_eval_loop_text(report))

    def test_main_reuses_existing_smoke_summary_without_rerunning_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = root / "tiny_scorecard_comparison_smoke_summary.json"
            out_dir = root / "loop"
            summary_path.write_text(
                json.dumps(_summary(decision_status="promote", selected_name="tiny-candidate"), ensure_ascii=False),
                encoding="utf-8",
            )

            main(["--smoke-summary", str(summary_path), "--out-dir", str(out_dir), "--force"])

            payload = json.loads((out_dir / "baseline_candidate_eval_loop.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "accept_candidate")
            self.assertEqual(payload["execution"]["source_mode"], "reuse_summary")
            self.assertEqual(payload["execution"]["gate_mode"], "exploratory")
            self.assertEqual(payload["execution"]["expected_exit_code"], 0)
            self.assertEqual(payload["command_result"]["name"], "existing_tiny_scorecard_comparison_smoke_summary")
            self.assertEqual(payload["command_result"]["source_summary"], str(summary_path))

    def test_prepare_output_dir_protects_smoke_summary_inside_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "loop"
            out_dir.mkdir()
            summary_path = out_dir / "tiny_scorecard_comparison_smoke_summary.json"
            summary_path.write_text("{}", encoding="utf-8")

            with self.assertRaises(SystemExit):
                prepare_output_dir(out_dir, force=True, protected_path=summary_path)


def _summary(
    *,
    decision_status: str,
    selected_name: str | None,
    first_blocker: str | None = None,
    first_recommendation: str | None = None,
    baseline_score: float = 72.0,
    candidate_score: float = 75.5,
) -> dict[str, object]:
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
            "scorecard_overall_score": baseline_score,
            "eval_suite_case_count": 10,
            "pair_same_checkpoint_baseline": True,
        },
        "candidate_smoke": {
            "status": "pass",
            "scorecard_overall_status": "pass",
            "scorecard_overall_score": candidate_score,
            "eval_suite_case_count": 10,
            "pair_same_checkpoint_baseline": True,
        },
        "scorecard_comparison": {
            "best_by_overall_score": "tiny-candidate",
            "best_by_rubric_avg_score": "tiny-candidate",
            "improved_overall_count": 1,
            "regressed_overall_count": 0,
            "case_delta_count": 10,
            "case_regression_count": 0,
            "generation_quality_flag_improvement_count": 1,
            "generation_quality_flag_regression_count": 0,
            "non_comparison_ready_count": 0,
        },
        "scorecard_decision": {
            "decision_status": decision_status,
            "recommended_action": "promote_selected_scorecard" if decision_status == "promote" else "keep_baseline_or_fix_candidate",
            "selected_name": selected_name,
            "first_blocker": first_blocker,
            "first_review_item": None,
            "first_recommendation": first_recommendation,
            "first_threshold_margin": None,
            "remediation_count": 0 if decision_status == "promote" else 1,
        },
        "benchmark_history": {
            "entry_count": 1,
            "ready_count": 0,
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
