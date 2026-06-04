from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME = "model_capability_route_promotion_bounded_rebalanced_intervention_decision.json"
BOUNDED_REBALANCED_INTERVENTION_DECISION_CSV_FILENAME = "model_capability_route_promotion_bounded_rebalanced_intervention_decision.csv"
BOUNDED_REBALANCED_INTERVENTION_DECISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_rebalanced_intervention_decision.txt"
BOUNDED_REBALANCED_INTERVENTION_DECISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_rebalanced_intervention_decision.md"
BOUNDED_REBALANCED_INTERVENTION_DECISION_HTML_FILENAME = "model_capability_route_promotion_bounded_rebalanced_intervention_decision.html"


def locate_rebalanced_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME
    return source


def locate_rebalanced_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME
    return source


def locate_rebalanced_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME
    return source


def locate_rebalanced_failure_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_rebalanced_profile_sweep(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded rebalanced intervention decision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_rebalanced_intervention_decision(
    rebalanced_seed_revision: dict[str, Any],
    rebalanced_training_run: dict[str, Any],
    rebalanced_comparison: dict[str, Any],
    failure_diagnostic: dict[str, Any],
    profile_sweep: dict[str, Any],
    *,
    seed_revision_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    comparison_path: str | Path | None = None,
    failure_diagnostic_path: str | Path | None = None,
    profile_sweep_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded rebalanced intervention decision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    signals = _signals(rebalanced_seed_revision, rebalanced_training_run, rebalanced_comparison, failure_diagnostic, profile_sweep)
    evidence_rows = _evidence_rows(signals)
    issues = _issues(rebalanced_seed_revision, rebalanced_training_run, rebalanced_comparison, failure_diagnostic, profile_sweep, signals)
    status = "pass" if not issues else "fail"
    route = _route(status, signals)
    summary = _summary(status, issues, signals, route, evidence_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, signals, route),
        "failed_count": len(issues),
        "issues": issues,
        "source_rebalanced_seed_revision": str(seed_revision_path or ""),
        "source_rebalanced_training_run": str(training_run_path or ""),
        "source_rebalanced_comparison": str(comparison_path or ""),
        "source_failure_diagnostic": str(failure_diagnostic_path or ""),
        "source_profile_sweep": str(profile_sweep_path or ""),
        "evidence_rows": evidence_rows,
        "route": route,
        "signals": signals,
        "summary": summary,
        "interpretation": _interpretation(status, signals, route),
    }


def resolve_exit_code(report: dict[str, Any], *, require_decision_ready: bool, require_intervention_selected: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_decision_ready and report.get("status") != "pass":
        return 1
    if require_intervention_selected and summary.get("intervention_selected") is not True:
        return 1
    return 0


def _signals(
    seed: dict[str, Any],
    training: dict[str, Any],
    comparison: dict[str, Any],
    diagnostic: dict[str, Any],
    profile_sweep: dict[str, Any],
) -> dict[str, Any]:
    seed_summary = as_dict(seed.get("summary")) or as_dict(training.get("rebalanced_seed_summary"))
    training_summary = as_dict(training.get("summary"))
    comparison_summary = as_dict(comparison.get("summary"))
    diagnostic_summary = as_dict(diagnostic.get("summary"))
    sweep_summary = as_dict(profile_sweep.get("summary"))
    case_count = int(sweep_summary.get("case_count") or diagnostic_summary.get("case_count") or comparison_summary.get("case_count") or 0)
    distribution_repaired = float(seed_summary.get("direct_answer_share") or 0.0) >= 0.2 and float(seed_summary.get("carry_forward_share") or 1.0) <= 0.5
    zero_hit_all_cases = int(diagnostic_summary.get("zero_hit_case_count") or 0) == case_count and case_count > 0
    sweep_no_recovery = sweep_summary.get("any_profile_recovered") is False and sweep_summary.get("promotion_ready") is False
    return {
        "case_count": case_count,
        "distribution_repaired": distribution_repaired,
        "direct_answer_share": seed_summary.get("direct_answer_share"),
        "carry_forward_share": seed_summary.get("carry_forward_share"),
        "decoder_bridge_share": seed_summary.get("decoder_bridge_share"),
        "training_ready": training_summary.get("decoder_anchor_rebalanced_training_ready") is True,
        "final_val_loss": training_summary.get("final_val_loss"),
        "rebalanced_vs_baseline_pass_rate_delta": comparison_summary.get("rebalanced_vs_baseline_pass_rate_delta"),
        "rebalanced_vs_decoder_anchor_pass_rate_delta": comparison_summary.get("rebalanced_vs_decoder_anchor_pass_rate_delta"),
        "rebalanced_passed_case_count": comparison_summary.get("rebalanced_passed_case_count"),
        "comparison_promotion_ready": comparison_summary.get("promotion_ready") is True,
        "zero_hit_all_cases": zero_hit_all_cases,
        "zero_hit_case_count": diagnostic_summary.get("zero_hit_case_count"),
        "fragment_like_case_count": diagnostic_summary.get("fragment_like_case_count"),
        "root_cause_count": diagnostic_summary.get("root_cause_count"),
        "profile_sweep_no_recovery": sweep_no_recovery,
        "best_profile_id": sweep_summary.get("best_profile_id"),
        "best_passed_case_count": sweep_summary.get("best_passed_case_count"),
        "best_any_hit_case_count": sweep_summary.get("best_any_hit_case_count"),
        "any_profile_recovered": sweep_summary.get("any_profile_recovered") is True,
        "profile_promotion_ready": sweep_summary.get("promotion_ready") is True,
    }


def _evidence_rows(signals: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _evidence("rebalanced_seed_revision", signals["distribution_repaired"], "direct/carry distribution repaired", {"direct_answer_share": signals.get("direct_answer_share"), "carry_forward_share": signals.get("carry_forward_share")}),
        _evidence("rebalanced_training_run", signals["training_ready"], "real checkpoint was trained from the rebalanced corpus", {"final_val_loss": signals.get("final_val_loss")}),
        _evidence("checkpoint_comparison", not signals["comparison_promotion_ready"], "rebalanced checkpoint did not beat baseline or recover promotion", {"delta_baseline": signals.get("rebalanced_vs_baseline_pass_rate_delta"), "passed": signals.get("rebalanced_passed_case_count")}),
        _evidence("failure_diagnostic", signals["zero_hit_all_cases"], "all replay cases remained zero-hit after rebalancing", {"zero_hit_case_count": signals.get("zero_hit_case_count"), "fragment_like_case_count": signals.get("fragment_like_case_count")}),
        _evidence("profile_sweep", signals["profile_sweep_no_recovery"], "decoder profile sweep did not recover required terms", {"best_profile_id": signals.get("best_profile_id"), "best_passed_case_count": signals.get("best_passed_case_count"), "best_any_hit_case_count": signals.get("best_any_hit_case_count")}),
    ]


def _evidence(stage: str, passed: bool, signal: str, values: dict[str, Any]) -> dict[str, Any]:
    return {"stage": stage, "status": "pass" if passed else "review", "signal": signal, "values": values}


def _issues(
    seed: dict[str, Any],
    training: dict[str, Any],
    comparison: dict[str, Any],
    diagnostic: dict[str, Any],
    profile_sweep: dict[str, Any],
    signals: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = [
        _check("seed_revision_passed", seed.get("status") == "pass", seed.get("status"), "rebalanced seed revision must pass"),
        _check("training_run_passed", training.get("status") == "pass", training.get("status"), "rebalanced training run must pass"),
        _check("comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "rebalanced checkpoint comparison must pass"),
        _check("failure_diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "failure diagnostic must pass"),
        _check("profile_sweep_passed", profile_sweep.get("status") == "pass", profile_sweep.get("status"), "profile sweep must pass"),
        _check("distribution_repaired", signals.get("distribution_repaired") is True, signals.get("direct_answer_share"), "decision should only close the branch after distribution repair"),
        _check("profile_sweep_requests_intervention", as_dict(profile_sweep.get("summary")).get("next_step") == "route_to_objective_or_architecture_intervention", as_dict(profile_sweep.get("summary")).get("next_step"), "profile sweep should request intervention routing"),
    ]
    return [row for row in checks if row["status"] != "pass"]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _route(status: str, signals: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {}
    if signals.get("profile_promotion_ready"):
        selected = "review_decoder_profile_recovery"
    elif signals.get("any_profile_recovered"):
        selected = "partial_decoder_profile_recovery_review"
    else:
        selected = "objective_contract_intervention_first"
    return {
        "closed_route": "decoder_anchor_rebalanced_rescue",
        "evidence_window": "v829-v833",
        "selected_intervention_track": selected,
        "fallback_intervention_track": "architecture_capacity_probe_if_objective_contract_fails",
        "recommended_next_artifact": "model_capability_route_promotion_bounded_objective_intervention_plan",
        "promotion_allowed": False,
        "new_training_allowed": False,
        "blocked_actions": [
            "do_not_continue_decoder_profile_rescue",
            "do_not_add_more_rebalanced_training_epochs_without_new_objective",
            "do_not_claim_model_quality_improvement",
        ],
        "stop_reasons": _stop_reasons(signals),
    }


def _stop_reasons(signals: dict[str, Any]) -> list[str]:
    reasons = []
    if signals.get("distribution_repaired"):
        reasons.append("distribution_repaired")
    if signals.get("zero_hit_all_cases"):
        reasons.append("rebalanced_replay_zero_hit")
    if signals.get("profile_sweep_no_recovery"):
        reasons.append("decoder_profile_sweep_no_recovery")
    if signals.get("best_any_hit_case_count") == 0:
        reasons.append("no_required_term_hit_across_profiles")
    return reasons


def _summary(
    status: str,
    issues: list[dict[str, Any]],
    signals: dict[str, Any],
    route: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "intervention_decision_ready": status == "pass",
        "intervention_selected": bool(route.get("selected_intervention_track")),
        "selected_intervention_track": route.get("selected_intervention_track"),
        "fallback_intervention_track": route.get("fallback_intervention_track"),
        "recommended_next_artifact": route.get("recommended_next_artifact"),
        "promotion_allowed": route.get("promotion_allowed", False),
        "new_training_allowed": route.get("new_training_allowed", False),
        "case_count": signals.get("case_count"),
        "distribution_repaired": signals.get("distribution_repaired"),
        "zero_hit_all_cases": signals.get("zero_hit_all_cases"),
        "profile_sweep_no_recovery": signals.get("profile_sweep_no_recovery"),
        "best_profile_id": signals.get("best_profile_id"),
        "best_passed_case_count": signals.get("best_passed_case_count"),
        "best_any_hit_case_count": signals.get("best_any_hit_case_count"),
        "stop_reason_count": len(route.get("stop_reasons", [])),
        "blocked_action_count": len(route.get("blocked_actions", [])),
        "evidence_row_count": len(evidence_rows),
        "failed_check_count": len(issues),
        "next_step": route.get("recommended_next_artifact") if status == "pass" else "repair_bounded_rebalanced_intervention_decision_inputs",
    }


def _decision(status: str, signals: dict[str, Any], route: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_rebalanced_intervention_decision"
    if signals.get("profile_promotion_ready"):
        return "review_rebalanced_decoder_profile_recovery_before_intervention"
    if signals.get("any_profile_recovered"):
        return "hold_rebalanced_decoder_rescue_for_partial_recovery_review"
    if route.get("selected_intervention_track") == "objective_contract_intervention_first":
        return "stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention"
    return "route_bounded_rebalanced_branch_to_manual_review"


def _interpretation(status: str, signals: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Intervention decision inputs are incomplete.", "next_action": "repair source evidence"}
    if signals.get("profile_promotion_ready"):
        return {"model_quality_claim": "decoder_profile_recovery_candidate", "reason": "A decoder profile produced a promotable replay result.", "next_action": "review recovery evidence before intervention"}
    if signals.get("any_profile_recovered"):
        return {"model_quality_claim": "partial_decoder_profile_recovery_only", "reason": "A decoder profile improved over default but did not pass the bounded route.", "next_action": "review partial recovery before changing objectives"}
    return {
        "model_quality_claim": "route_decision_only",
        "reason": "Distribution repair, training, comparison, diagnostic, and profile sweep all indicate the rebalanced decoder-rescue route has no required-term recovery.",
        "next_action": route.get("recommended_next_artifact"),
    }


__all__ = [
    "BOUNDED_REBALANCED_INTERVENTION_DECISION_CSV_FILENAME",
    "BOUNDED_REBALANCED_INTERVENTION_DECISION_HTML_FILENAME",
    "BOUNDED_REBALANCED_INTERVENTION_DECISION_JSON_FILENAME",
    "BOUNDED_REBALANCED_INTERVENTION_DECISION_MARKDOWN_FILENAME",
    "BOUNDED_REBALANCED_INTERVENTION_DECISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_rebalanced_intervention_decision",
    "locate_rebalanced_comparison",
    "locate_rebalanced_failure_diagnostic",
    "locate_rebalanced_profile_sweep",
    "locate_rebalanced_seed_revision",
    "locate_rebalanced_training_run",
    "read_json_report",
    "resolve_exit_code",
]
