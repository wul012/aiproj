from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, list_of_dicts
from scripts.check_tiny_scorecard_comparison_smoke import (  # noqa: E402
    check_summary as check_smoke_summary,
    write_check_outputs as write_smoke_check_outputs,
)


SUMMARY_JSON_FILENAME = "tiny_scorecard_comparison_smoke_summary.json"
SUMMARY_TEXT_FILENAME = "tiny_scorecard_comparison_smoke_summary.txt"


def format_counts(value: Any) -> str:
    counts = as_dict(value)
    return ",".join(f"{key}:{counts[key]}" for key in sorted(counts))


def render_summary(summary: dict[str, Any]) -> str:
    baseline = as_dict(summary.get("baseline_smoke"))
    candidate = as_dict(summary.get("candidate_smoke"))
    comparison = as_dict(summary.get("scorecard_comparison"))
    decision = as_dict(summary.get("scorecard_decision"))
    history = as_dict(summary.get("benchmark_history"))
    remediation_gate = as_dict(summary.get("remediation_gate"))
    remediation_gate_issues = list_of_dicts(remediation_gate.get("issues"))
    first_remediation_gate_issue = remediation_gate_issues[0] if remediation_gate_issues else {}
    run_config = as_dict(summary.get("run_config"))
    interpretation = as_dict(summary.get("interpretation"))
    rows = [
        ("status", summary.get("status")),
        ("decision", summary.get("decision")),
        ("issue_count", summary.get("issue_count")),
        ("config_suite_name", run_config.get("suite_name")),
        ("config_case_token_cap", run_config.get("case_token_cap")),
        ("config_baseline_max_iters", run_config.get("baseline_max_iters")),
        ("config_candidate_max_iters", run_config.get("candidate_max_iters")),
        ("config_max_iters_delta", run_config.get("max_iters_delta")),
        ("config_budget_mode", run_config.get("budget_mode")),
        ("config_decision_min_rubric_score", run_config.get("decision_min_rubric_score")),
        ("config_require_clean_remediation", run_config.get("require_clean_remediation")),
        ("config_summary_check_requested", run_config.get("summary_check_requested")),
        ("config_summary_check_allow_gate_stop", run_config.get("summary_check_allow_gate_stop")),
        ("config_summary_check_no_fail", run_config.get("summary_check_no_fail")),
        ("baseline_scorecard_status", baseline.get("scorecard_overall_status")),
        ("baseline_scorecard_score", baseline.get("scorecard_overall_score")),
        ("baseline_training_best_val_loss", baseline.get("training_best_val_loss")),
        ("baseline_training_final_val_loss", baseline.get("training_final_val_loss")),
        ("baseline_generation_quality_status", baseline.get("generation_quality_status")),
        ("baseline_generation_quality_total_flags", baseline.get("generation_quality_total_flags")),
        ("candidate_scorecard_status", candidate.get("scorecard_overall_status")),
        ("candidate_scorecard_score", candidate.get("scorecard_overall_score")),
        ("candidate_training_best_val_loss", candidate.get("training_best_val_loss")),
        ("candidate_training_final_val_loss", candidate.get("training_final_val_loss")),
        ("candidate_generation_quality_status", candidate.get("generation_quality_status")),
        ("candidate_generation_quality_total_flags", candidate.get("generation_quality_total_flags")),
        ("baseline_pair_same_checkpoint", baseline.get("pair_same_checkpoint_baseline")),
        ("candidate_pair_same_checkpoint", candidate.get("pair_same_checkpoint_baseline")),
        ("comparison_scorecard_count", comparison.get("scorecard_count")),
        ("comparison_baseline", comparison.get("baseline_name")),
        ("comparison_best_overall", comparison.get("best_by_overall_score")),
        ("comparison_improved_overall_count", comparison.get("improved_overall_count")),
        ("comparison_regressed_overall_count", comparison.get("regressed_overall_count")),
        ("comparison_case_delta_count", comparison.get("case_delta_count")),
        ("comparison_non_ready_count", comparison.get("non_comparison_ready_count")),
        ("history_entry_count", history.get("entry_count")),
        ("history_ready_count", history.get("ready_count")),
        ("history_model_quality_claim", history.get("model_quality_claim")),
        ("history_readiness_requirement_status", history.get("readiness_requirement_status")),
        ("history_readiness_requirement_decision", history.get("readiness_requirement_decision")),
        ("history_readiness_requirement_exit_code", history.get("readiness_requirement_exit_code")),
        (
            "history_readiness_requirement_failed_reasons",
            ",".join(str(item) for item in history.get("readiness_requirement_failed_reasons", [])),
        ),
        ("history_json", as_dict(history.get("outputs")).get("json")),
        ("decision_status", decision.get("decision_status")),
        ("decision_action", decision.get("recommended_action")),
        ("decision_selected_name", decision.get("selected_name")),
        ("decision_candidate_evaluation_count", decision.get("candidate_evaluation_count")),
        ("decision_blocked_candidate_count", decision.get("blocked_candidate_count")),
        ("decision_blocked_candidates", ",".join(str(item) for item in decision.get("blocked_candidate_names", []))),
        ("decision_dominant_blocker_category", decision.get("dominant_blocker_category")),
        ("decision_dominant_review_category", decision.get("dominant_review_category")),
        ("decision_remediation_plan_count", decision.get("remediation_plan_count")),
        ("decision_remediation_blocker_count", decision.get("remediation_blocker_count")),
        ("decision_remediation_review_count", decision.get("remediation_review_count")),
        ("decision_dominant_remediation_kind", decision.get("dominant_remediation_kind")),
        ("decision_dominant_remediation_category", decision.get("dominant_remediation_category")),
        ("decision_dominant_remediation_action", decision.get("dominant_remediation_action")),
        ("decision_blocker_category_counts", format_counts(decision.get("blocker_category_counts"))),
        ("decision_review_category_counts", format_counts(decision.get("review_category_counts"))),
        ("decision_first_blocker", decision.get("first_blocker")),
        ("decision_first_threshold_candidate", decision.get("first_threshold_blocked_candidate")),
        ("decision_first_threshold_score", decision.get("first_threshold_rubric_score")),
        ("decision_first_threshold_min", decision.get("first_threshold_min_rubric_score")),
        ("decision_first_threshold_margin", decision.get("first_threshold_margin")),
        ("decision_threshold_blocked_count", decision.get("threshold_blocked_candidate_count")),
        ("decision_threshold_blocked_candidates", ",".join(str(item) for item in decision.get("threshold_blocked_candidate_names", []))),
        ("decision_threshold_closest_candidate", decision.get("threshold_closest_candidate")),
        ("decision_threshold_closest_margin", decision.get("threshold_closest_margin")),
        ("decision_threshold_largest_gap_candidate", decision.get("threshold_largest_gap_candidate")),
        ("decision_threshold_largest_gap_margin", decision.get("threshold_largest_gap_margin")),
        ("decision_review_candidates", ",".join(str(item) for item in decision.get("review_candidate_names", []))),
        ("decision_first_review_item", decision.get("first_review_item")),
        ("decision_remediation_count", decision.get("remediation_count")),
        ("decision_first_remediation_category", decision.get("first_remediation_category")),
        ("decision_first_remediation_action_code", decision.get("first_remediation_action_code")),
        ("decision_first_remediation_severity", decision.get("first_remediation_severity")),
        ("decision_first_remediation_owner_scope", decision.get("first_remediation_owner_scope")),
        ("decision_first_remediation_action", decision.get("first_remediation_action")),
        ("remediation_gate_required", remediation_gate.get("required")),
        ("remediation_gate_status", remediation_gate.get("status")),
        ("remediation_gate_decision", remediation_gate.get("decision")),
        ("remediation_gate_count", remediation_gate.get("remediation_count")),
        ("remediation_gate_issue_count", remediation_gate.get("issue_count")),
        ("remediation_gate_first_issue_code", first_remediation_gate_issue.get("code")),
        ("remediation_gate_first_issue_severity", first_remediation_gate_issue.get("severity")),
        ("remediation_gate_first_issue_category", first_remediation_gate_issue.get("category")),
        ("remediation_gate_first_issue_action_code", first_remediation_gate_issue.get("action_code")),
        ("remediation_gate_first_issue_owner_scope", first_remediation_gate_issue.get("owner_scope")),
        ("remediation_gate_first_category", remediation_gate.get("first_category")),
        ("remediation_gate_first_action_code", remediation_gate.get("first_action_code")),
        ("remediation_gate_first_severity", remediation_gate.get("first_severity")),
        ("remediation_gate_first_owner_scope", remediation_gate.get("first_owner_scope")),
        ("decision_first_recommendation", decision.get("first_recommendation")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
    ]
    summary_check = as_dict(summary.get("summary_check"))
    summary_check_outputs = as_dict(summary.get("summary_check_outputs"))
    summary_check_issues = list_of_dicts(summary_check.get("issues"))
    first_summary_check_issue = summary_check_issues[0] if summary_check_issues else {}
    rows.extend(
        [
            ("summary_check_status", summary_check.get("status")),
            ("summary_check_decision", summary_check.get("decision")),
            ("summary_check_issue_count", summary_check.get("issue_count")),
            ("summary_check_allowed_gate_stop", summary_check.get("allowed_gate_stop")),
            ("summary_check_first_issue_code", first_summary_check_issue.get("code")),
            ("summary_check_json", summary_check_outputs.get("json")),
            ("summary_check_text", summary_check_outputs.get("text")),
        ]
    )
    rows.extend((f"command_{item['name']}", item["status"]) for item in list_of_dicts(summary.get("commands")))
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_summary_outputs(summary: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": out_dir / SUMMARY_JSON_FILENAME,
        "text": out_dir / SUMMARY_TEXT_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_summary(summary), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def write_summary_and_optional_check(
    summary: dict[str, Any],
    out_dir: Path,
    *,
    summary_check_out_dir: Path | None = None,
    summary_check_allow_gate_stop: bool = False,
) -> dict[str, str]:
    outputs = write_summary_outputs(summary, out_dir)
    if summary_check_out_dir is None:
        return outputs
    summary_check = check_smoke_summary(
        summary,
        summary_path=Path(outputs["json"]),
        allow_gate_stop=summary_check_allow_gate_stop,
    )
    summary_check_outputs = write_smoke_check_outputs(summary_check, summary_check_out_dir)
    summary["summary_check"] = summary_check
    summary["summary_check_outputs"] = summary_check_outputs
    return write_summary_outputs(summary, out_dir)


def print_summary(summary: dict[str, Any], outputs: dict[str, str]) -> None:
    print(render_summary(summary), end="")
    print(f"summary_json={outputs['json']}")
    print(f"summary_text={outputs['text']}")


__all__ = [
    "SUMMARY_JSON_FILENAME",
    "SUMMARY_TEXT_FILENAME",
    "format_counts",
    "print_summary",
    "render_summary",
    "write_summary_and_optional_check",
    "write_summary_outputs",
]
