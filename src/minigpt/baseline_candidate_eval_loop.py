from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.baseline_candidate_eval_loop_artifacts import (
    LOOP_HTML_FILENAME,
    LOOP_JSON_FILENAME,
    LOOP_MARKDOWN_FILENAME,
    LOOP_TEXT_FILENAME,
    render_baseline_candidate_eval_loop_html,
    render_baseline_candidate_eval_loop_markdown,
    render_baseline_candidate_eval_loop_text,
    write_baseline_candidate_eval_loop_outputs,
)
from minigpt.report_utils import as_dict, number_or_none, string_list, utc_now


SMOKE_SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"


def load_baseline_candidate_eval_loop_smoke_summary(path: str | Path) -> dict[str, Any]:
    resolved = resolve_baseline_candidate_eval_loop_smoke_summary(path)
    payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("baseline-candidate smoke summary must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(resolved)
    return payload


def resolve_baseline_candidate_eval_loop_smoke_summary(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / SMOKE_SUMMARY_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def build_baseline_candidate_eval_loop_report(
    smoke_summary_path: str | Path,
    *,
    title: str = "MiniGPT baseline-candidate eval loop",
    generated_at: str | None = None,
    command_result: dict[str, Any] | None = None,
    min_overall_score_delta: float = 0.0,
) -> dict[str, Any]:
    smoke = load_baseline_candidate_eval_loop_smoke_summary(smoke_summary_path)
    run_config = as_dict(smoke.get("run_config"))
    baseline = as_dict(smoke.get("baseline_smoke"))
    candidate = as_dict(smoke.get("candidate_smoke"))
    comparison = as_dict(smoke.get("scorecard_comparison"))
    decision = as_dict(smoke.get("scorecard_decision"))
    history = as_dict(smoke.get("benchmark_history"))
    interpretation = as_dict(smoke.get("interpretation"))
    status = "pass" if smoke.get("status") == "pass" else "fail"
    baseline_score = number_or_none(baseline.get("scorecard_overall_score"))
    candidate_score = number_or_none(candidate.get("scorecard_overall_score"))
    baseline_best_loss = number_or_none(baseline.get("training_best_val_loss"))
    candidate_best_loss = number_or_none(candidate.get("training_best_val_loss"))
    baseline_final_loss = number_or_none(baseline.get("training_final_val_loss"))
    candidate_final_loss = number_or_none(candidate.get("training_final_val_loss"))
    baseline_quality_flags = number_or_none(baseline.get("generation_quality_total_flags"), int)
    candidate_quality_flags = number_or_none(candidate.get("generation_quality_total_flags"), int)
    score_delta = None if baseline_score is None or candidate_score is None else round(float(candidate_score) - float(baseline_score), 4)
    best_loss_delta = _metric_delta(candidate_best_loss, baseline_best_loss)
    final_loss_delta = _metric_delta(candidate_final_loss, baseline_final_loss)
    quality_flag_delta = _metric_delta(candidate_quality_flags, baseline_quality_flags)
    control_checks = _control_checks(
        status=status,
        run_config=run_config,
        baseline=baseline,
        candidate=candidate,
        comparison=comparison,
        baseline_score=baseline_score,
        candidate_score=candidate_score,
    )
    failed_control_reasons = _failed_control_reasons(control_checks)
    acceptance = _acceptance_criteria(
        status=status,
        decision=decision,
        control_checks=control_checks,
        score_delta=score_delta,
        min_overall_score_delta=min_overall_score_delta,
    )
    promotion = _promotion_decision(decision, acceptance=acceptance)
    loop_decision = "fix_loop" if status != "pass" else ("accept_candidate" if promotion["accepted"] else "reject_candidate")
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": loop_decision,
        "source_smoke_summary": smoke.get("_source_path"),
        "experiment": {
            "loop_type": "baseline_candidate_eval_loop",
            "baseline_name": "tiny-baseline",
            "candidate_name": "tiny-candidate",
            "suite_name": run_config.get("suite_name"),
            "case_token_cap": run_config.get("case_token_cap"),
            "controlled_variable": _controlled_variable(run_config),
            "baseline_max_iters": run_config.get("baseline_max_iters"),
            "candidate_max_iters": run_config.get("candidate_max_iters"),
            "max_iters_delta": run_config.get("max_iters_delta"),
            "budget_mode": run_config.get("budget_mode"),
            "baseline_seed": run_config.get("baseline_seed"),
            "candidate_seed": run_config.get("candidate_seed"),
            "min_overall_score_delta": min_overall_score_delta,
        },
        "baseline_metrics": {
            "status": baseline.get("status"),
            "scorecard_status": baseline.get("scorecard_overall_status"),
            "overall_score": baseline_score,
            "training_best_val_loss": baseline_best_loss,
            "training_final_val_loss": baseline_final_loss,
            "generation_quality_status": baseline.get("generation_quality_status"),
            "generation_quality_total_flags": baseline_quality_flags,
            "eval_suite_case_count": baseline.get("eval_suite_case_count"),
            "pair_same_checkpoint_baseline": baseline.get("pair_same_checkpoint_baseline"),
        },
        "candidate_metrics": {
            "status": candidate.get("status"),
            "scorecard_status": candidate.get("scorecard_overall_status"),
            "overall_score": candidate_score,
            "training_best_val_loss": candidate_best_loss,
            "training_final_val_loss": candidate_final_loss,
            "generation_quality_status": candidate.get("generation_quality_status"),
            "generation_quality_total_flags": candidate_quality_flags,
            "eval_suite_case_count": candidate.get("eval_suite_case_count"),
            "pair_same_checkpoint_baseline": candidate.get("pair_same_checkpoint_baseline"),
        },
        "delta_report": {
            "overall_score_delta": score_delta,
            "training_best_val_loss_delta": best_loss_delta,
            "training_final_val_loss_delta": final_loss_delta,
            "generation_quality_total_flags_delta": quality_flag_delta,
            "loss_delta_interpretation": "negative_is_better",
            "generation_flag_delta_interpretation": "negative_is_better",
            "best_by_overall_score": comparison.get("best_by_overall_score"),
            "best_by_rubric_avg_score": comparison.get("best_by_rubric_avg_score"),
            "improved_overall_count": comparison.get("improved_overall_count"),
            "regressed_overall_count": comparison.get("regressed_overall_count"),
            "case_delta_count": comparison.get("case_delta_count"),
            "case_regression_count": comparison.get("case_regression_count"),
            "generation_quality_flag_improvement_count": comparison.get("generation_quality_flag_improvement_count"),
            "generation_quality_flag_regression_count": comparison.get("generation_quality_flag_regression_count"),
            "non_comparison_ready_count": comparison.get("non_comparison_ready_count"),
        },
        "benchmark_history": {
            "entry_count": history.get("entry_count"),
            "ready_count": history.get("ready_count"),
            "model_quality_claim": history.get("model_quality_claim"),
            "readiness_requirement_status": history.get("readiness_requirement_status"),
            "readiness_requirement_decision": history.get("readiness_requirement_decision"),
            "readiness_requirement_failed_reasons": history.get("readiness_requirement_failed_reasons", []),
            "outputs": as_dict(history.get("outputs")),
        },
        "control_summary": {
            "status": "pass" if not failed_control_reasons else "fail",
            "check_count": len(control_checks),
            "failed_count": len(failed_control_reasons),
            "failed_reasons": failed_control_reasons,
        },
        "control_checks": control_checks,
        "acceptance_criteria": acceptance,
        "promotion_decision": promotion,
        "next_action": _next_action(status, promotion),
        "command_result": command_result or {},
        "boundary": {
            "model_quality_claim": interpretation.get("model_quality_claim") or "not_claimed",
            "reason": interpretation.get("reason")
            or "This loop verifies a tiny reproducible baseline-candidate experiment; it is not a production model-quality claim.",
        },
    }


def _promotion_decision(decision: dict[str, Any], *, acceptance: dict[str, Any]) -> dict[str, Any]:
    status = decision.get("decision_status")
    selected_name = decision.get("selected_name")
    acceptance_failed_reasons = string_list(acceptance.get("failed_reasons"))
    accepted = acceptance.get("status") == "pass"
    rejected_reasons = []
    if not accepted:
        for key in ("first_blocker", "first_review_item"):
            value = decision.get(key)
            if value:
                rejected_reasons.append(str(value))
        if status != "promote" and decision.get("first_recommendation"):
            rejected_reasons.append(str(decision.get("first_recommendation")))
        if not rejected_reasons and status != "promote":
            rejected_reasons.append(f"promotion status is {status}")
        if selected_name and selected_name != "tiny-candidate":
            rejected_reasons.append(f"selected run is {selected_name}, not tiny-candidate")
        for reason in acceptance_failed_reasons:
            if reason not in rejected_reasons:
                rejected_reasons.append(reason)
    return {
        "status": status,
        "action": decision.get("recommended_action"),
        "selected_name": selected_name,
        "accepted": accepted,
        "rejected_reasons": rejected_reasons,
        "threshold_margin": decision.get("first_threshold_margin"),
        "remediation_count": decision.get("remediation_count"),
    }


def _acceptance_criteria(
    *,
    status: str,
    decision: dict[str, Any],
    control_checks: list[dict[str, Any]],
    score_delta: int | float | None,
    min_overall_score_delta: float,
) -> dict[str, Any]:
    selected_name = decision.get("selected_name")
    criteria = [
        _criterion("smoke_status_pass", status == "pass", "pass", status),
        _criterion("scorecard_decision_promote", decision.get("decision_status") == "promote", "promote", decision.get("decision_status")),
        _criterion("selected_candidate", selected_name == "tiny-candidate", "tiny-candidate", selected_name),
        _criterion("control_checks_pass", not _failed_control_reasons(control_checks), "no failed control checks", _failed_control_reasons(control_checks)),
        _criterion(
            "min_overall_score_delta",
            score_delta is not None and float(score_delta) >= float(min_overall_score_delta),
            f">= {min_overall_score_delta}",
            score_delta,
        ),
    ]
    failed_reasons = [str(item.get("reason")) for item in criteria if item.get("status") != "pass" and item.get("reason")]
    return {
        "mode": "strict_tiny_candidate_promotion",
        "status": "pass" if not failed_reasons else "fail",
        "min_overall_score_delta": min_overall_score_delta,
        "criteria_count": len(criteria),
        "failed_count": len(failed_reasons),
        "failed_reasons": failed_reasons,
        "criteria": criteria,
    }


def _criterion(check_id: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "expected": expected,
        "actual": actual,
        "reason": "" if passed else f"{check_id} expected {expected}, got {actual}",
    }


def _control_checks(
    *,
    status: str,
    run_config: dict[str, Any],
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    comparison: dict[str, Any],
    baseline_score: int | float | None,
    candidate_score: int | float | None,
) -> list[dict[str, Any]]:
    baseline_case_count = number_or_none(baseline.get("eval_suite_case_count"), int)
    candidate_case_count = number_or_none(candidate.get("eval_suite_case_count"), int)
    non_ready_count = number_or_none(comparison.get("non_comparison_ready_count"), int)
    controlled_variable = _controlled_variable(run_config)
    return [
        _control_check("smoke_status", status == "pass", "pass", status),
        _control_check("controlled_variable", controlled_variable != "fixed_config", "max_iters or seed", controlled_variable),
        _control_check("baseline_score_present", baseline_score is not None, "numeric score", baseline_score),
        _control_check("candidate_score_present", candidate_score is not None, "numeric score", candidate_score),
        _control_check(
            "case_count_match",
            baseline_case_count is not None and baseline_case_count > 0 and baseline_case_count == candidate_case_count,
            "same positive case count",
            f"baseline={baseline_case_count}, candidate={candidate_case_count}",
        ),
        _control_check("comparison_ready", non_ready_count == 0, "0", non_ready_count),
        _control_check(
            "candidate_not_lower_overall_score",
            baseline_score is not None and candidate_score is not None and float(candidate_score) >= float(baseline_score),
            "candidate >= baseline",
            f"baseline={baseline_score}, candidate={candidate_score}",
        ),
    ]


def _control_check(check_id: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "expected": expected,
        "actual": actual,
        "reason": "" if passed else f"{check_id} expected {expected}, got {actual}",
    }


def _failed_control_reasons(control_checks: list[dict[str, Any]]) -> list[str]:
    return [str(check.get("reason")) for check in control_checks if check.get("status") != "pass" and check.get("reason")]


def _controlled_variable(run_config: dict[str, Any]) -> str:
    if run_config.get("baseline_max_iters") != run_config.get("candidate_max_iters"):
        return "max_iters"
    if run_config.get("baseline_seed") != run_config.get("candidate_seed"):
        return "seed"
    return "fixed_config"


def _metric_delta(candidate: int | float | None, baseline: int | float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return round(float(candidate) - float(baseline), 4)


def _next_action(status: str, promotion: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_loop_execution"
    if promotion.get("accepted"):
        return "accept_candidate_as_next_experiment_baseline"
    return "keep_baseline_and_fix_candidate"


__all__ = [
    "LOOP_HTML_FILENAME",
    "LOOP_JSON_FILENAME",
    "LOOP_MARKDOWN_FILENAME",
    "LOOP_TEXT_FILENAME",
    "build_baseline_candidate_eval_loop_report",
    "load_baseline_candidate_eval_loop_smoke_summary",
    "render_baseline_candidate_eval_loop_html",
    "render_baseline_candidate_eval_loop_markdown",
    "render_baseline_candidate_eval_loop_text",
    "resolve_baseline_candidate_eval_loop_smoke_summary",
    "write_baseline_candidate_eval_loop_outputs",
]
