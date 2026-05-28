from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, number_or_none, string_list, utc_now


SMOKE_SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"
LOOP_JSON_FILENAME = "baseline_candidate_eval_loop.json"
LOOP_TEXT_FILENAME = "baseline_candidate_eval_loop.txt"
LOOP_MARKDOWN_FILENAME = "baseline_candidate_eval_loop.md"
LOOP_HTML_FILENAME = "baseline_candidate_eval_loop.html"


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


def render_baseline_candidate_eval_loop_text(report: dict[str, Any]) -> str:
    experiment = as_dict(report.get("experiment"))
    baseline = as_dict(report.get("baseline_metrics"))
    candidate = as_dict(report.get("candidate_metrics"))
    delta = as_dict(report.get("delta_report"))
    history = as_dict(report.get("benchmark_history"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    promotion = as_dict(report.get("promotion_decision"))
    execution = as_dict(report.get("execution"))
    boundary = as_dict(report.get("boundary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("execution_source_mode", execution.get("source_mode")),
        ("execution_gate_mode", execution.get("gate_mode")),
        ("execution_fail_on_reject", execution.get("fail_on_reject")),
        ("execution_expected_exit_code", execution.get("expected_exit_code")),
        ("controlled_variable", experiment.get("controlled_variable")),
        ("suite_name", experiment.get("suite_name")),
        ("baseline_max_iters", experiment.get("baseline_max_iters")),
        ("candidate_max_iters", experiment.get("candidate_max_iters")),
        ("min_overall_score_delta", experiment.get("min_overall_score_delta")),
        ("baseline_score", baseline.get("overall_score")),
        ("candidate_score", candidate.get("overall_score")),
        ("overall_score_delta", delta.get("overall_score_delta")),
        ("baseline_best_val_loss", baseline.get("training_best_val_loss")),
        ("candidate_best_val_loss", candidate.get("training_best_val_loss")),
        ("best_val_loss_delta", delta.get("training_best_val_loss_delta")),
        ("baseline_final_val_loss", baseline.get("training_final_val_loss")),
        ("candidate_final_val_loss", candidate.get("training_final_val_loss")),
        ("final_val_loss_delta", delta.get("training_final_val_loss_delta")),
        ("baseline_generation_flags", baseline.get("generation_quality_total_flags")),
        ("candidate_generation_flags", candidate.get("generation_quality_total_flags")),
        ("generation_flags_delta", delta.get("generation_quality_total_flags_delta")),
        ("case_delta_count", delta.get("case_delta_count")),
        ("case_regression_count", delta.get("case_regression_count")),
        ("benchmark_history_entry_count", history.get("entry_count")),
        ("benchmark_history_ready_count", history.get("ready_count")),
        ("benchmark_history_model_quality_claim", history.get("model_quality_claim")),
        ("control_status", control.get("status")),
        ("control_failed_count", control.get("failed_count")),
        ("acceptance_status", acceptance.get("status")),
        ("acceptance_failed_count", acceptance.get("failed_count")),
        ("promotion_status", promotion.get("status")),
        ("promotion_action", promotion.get("action")),
        ("promotion_selected_name", promotion.get("selected_name")),
        ("promotion_accepted", promotion.get("accepted")),
        ("promotion_rejected_reasons", ",".join(string_list(promotion.get("rejected_reasons")))),
        ("next_action", report.get("next_action")),
        ("model_quality_claim", boundary.get("model_quality_claim")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_eval_loop_markdown(report: dict[str, Any]) -> str:
    experiment = as_dict(report.get("experiment"))
    promotion = as_dict(report.get("promotion_decision"))
    delta = as_dict(report.get("delta_report"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    execution = as_dict(report.get("execution"))
    baseline = as_dict(report.get("baseline_metrics"))
    candidate = as_dict(report.get("candidate_metrics"))
    rejected_reasons = string_list(promotion.get("rejected_reasons"))
    control_failed_reasons = string_list(control.get("failed_reasons"))
    acceptance_failed_reasons = string_list(acceptance.get("failed_reasons"))
    reason_lines = ["- none"] if not rejected_reasons else [f"- {reason}" for reason in rejected_reasons]
    control_lines = ["- none"] if not control_failed_reasons else [f"- {reason}" for reason in control_failed_reasons]
    acceptance_lines = ["- none"] if not acceptance_failed_reasons else [f"- {reason}" for reason in acceptance_failed_reasons]
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Eval Loop",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Source mode: `{execution.get('source_mode')}`",
            f"- Gate mode: `{execution.get('gate_mode')}`",
            f"- Expected exit code: `{execution.get('expected_exit_code')}`",
            f"- Suite: `{experiment.get('suite_name')}`",
            f"- Controlled variable: `{experiment.get('controlled_variable')}`",
            f"- Min overall score delta: `{experiment.get('min_overall_score_delta')}`",
            f"- Overall score delta: `{delta.get('overall_score_delta')}`",
            f"- Best val loss delta: `{delta.get('training_best_val_loss_delta')}`",
            f"- Final val loss delta: `{delta.get('training_final_val_loss_delta')}`",
            f"- Generation flags delta: `{delta.get('generation_quality_total_flags_delta')}`",
            f"- Control status: `{control.get('status')}`",
            f"- Acceptance status: `{acceptance.get('status')}`",
            f"- Promotion status: `{promotion.get('status')}`",
            f"- Candidate accepted: `{promotion.get('accepted')}`",
            f"- Next action: `{report.get('next_action')}`",
            "",
            "## Rejected Reasons",
            "",
            *reason_lines,
            "",
            "## Capability Metrics",
            "",
            "| Metric | Baseline | Candidate | Delta | Direction |",
            "| --- | ---: | ---: | ---: | --- |",
            f"| Overall score | {baseline.get('overall_score')} | {candidate.get('overall_score')} | {delta.get('overall_score_delta')} | higher is better |",
            f"| Best val loss | {baseline.get('training_best_val_loss')} | {candidate.get('training_best_val_loss')} | {delta.get('training_best_val_loss_delta')} | lower is better |",
            f"| Final val loss | {baseline.get('training_final_val_loss')} | {candidate.get('training_final_val_loss')} | {delta.get('training_final_val_loss_delta')} | lower is better |",
            f"| Generation flags | {baseline.get('generation_quality_total_flags')} | {candidate.get('generation_quality_total_flags')} | {delta.get('generation_quality_total_flags_delta')} | lower is better |",
            "",
            "## Control Checks",
            "",
            *control_lines,
            "",
            "## Acceptance Criteria",
            "",
            *acceptance_lines,
            "",
        ]
    )


def render_baseline_candidate_eval_loop_html(report: dict[str, Any]) -> str:
    promotion = as_dict(report.get("promotion_decision"))
    control = as_dict(report.get("control_summary"))
    acceptance = as_dict(report.get("acceptance_criteria"))
    execution = as_dict(report.get("execution"))
    delta = as_dict(report.get("delta_report"))
    reasons = string_list(promotion.get("rejected_reasons"))
    control_reasons = string_list(control.get("failed_reasons"))
    acceptance_reasons = string_list(acceptance.get("failed_reasons"))
    reason_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in reasons) or "<li>none</li>"
    control_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in control_reasons) or "<li>none</li>"
    acceptance_items = "\n".join(f"<li>{html_escape(reason)}</li>" for reason in acceptance_reasons) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate eval loop</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f6f8f7; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dfdb; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dfdb; border-radius: 8px; padding: 10px; background: #fbfcfb; }}
.metric span {{ display: block; color: #5c6c65; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate eval loop</h1>
<section>
<h2>Decision</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(report.get('decision'))}</strong></div>
<div class="metric"><span>Source</span><strong>{html_escape(execution.get('source_mode'))}</strong></div>
<div class="metric"><span>Gate</span><strong>{html_escape(execution.get('gate_mode'))}</strong></div>
<div class="metric"><span>Exit</span><strong>{html_escape(execution.get('expected_exit_code'))}</strong></div>
<div class="metric"><span>Promotion</span><strong>{html_escape(promotion.get('status'))}</strong></div>
<div class="metric"><span>Score Delta</span><strong>{html_escape(delta.get('overall_score_delta'))}</strong></div>
<div class="metric"><span>Best Loss Delta</span><strong>{html_escape(delta.get('training_best_val_loss_delta'))}</strong></div>
<div class="metric"><span>Final Loss Delta</span><strong>{html_escape(delta.get('training_final_val_loss_delta'))}</strong></div>
<div class="metric"><span>Gen Flags Delta</span><strong>{html_escape(delta.get('generation_quality_total_flags_delta'))}</strong></div>
<div class="metric"><span>Control</span><strong>{html_escape(control.get('status'))}</strong></div>
<div class="metric"><span>Acceptance</span><strong>{html_escape(acceptance.get('status'))}</strong></div>
<div class="metric"><span>Accepted</span><strong>{html_escape(promotion.get('accepted'))}</strong></div>
<div class="metric"><span>Selected</span><strong>{html_escape(promotion.get('selected_name'))}</strong></div>
<div class="metric"><span>Min Delta</span><strong>{html_escape(acceptance.get('min_overall_score_delta'))}</strong></div>
<div class="metric"><span>Next</span><strong>{html_escape(report.get('next_action'))}</strong></div>
</div>
</section>
<section>
<h2>Rejected Reasons</h2>
<ul>
{reason_items}
</ul>
</section>
<section>
<h2>Control Checks</h2>
<ul>
{control_items}
</ul>
</section>
<section>
<h2>Acceptance Criteria</h2>
<ul>
{acceptance_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_baseline_candidate_eval_loop_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / LOOP_JSON_FILENAME,
        "text": root / LOOP_TEXT_FILENAME,
        "markdown": root / LOOP_MARKDOWN_FILENAME,
        "html": root / LOOP_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_eval_loop_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_eval_loop_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_eval_loop_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


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
