from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.benchmark_history import build_benchmark_history, write_benchmark_history_outputs
from minigpt.report_utils import as_dict, list_of_dicts

from .tiny_scorecard_comparison_smoke_outputs import SUMMARY_JSON_FILENAME, SUMMARY_TEXT_FILENAME


def build_summary(
    *,
    out_dir: Path,
    baseline_dir: Path,
    candidate_dir: Path,
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
    run_config: dict[str, Any],
    command_results: list[dict[str, Any]],
    issues: list[str],
) -> dict[str, Any]:
    history_report, history_outputs = build_tiny_benchmark_history(comparison_dir, decision_dir, history_dir)
    artifacts = artifact_status(baseline_dir, candidate_dir, comparison_dir, decision_dir, history_dir)
    issue_list = list(issues)
    for key, value in artifacts.items():
        if key.endswith("_exists") and not value:
            issue_list.append(f"missing artifact: {key}")
    status = "pass" if not issue_list else "fail"
    baseline_smoke = read_json(baseline_dir / "tiny_standard_benchmark_smoke_summary.json")
    candidate_smoke = read_json(candidate_dir / "tiny_standard_benchmark_smoke_summary.json")
    comparison = read_json(comparison_dir / "benchmark_scorecard_comparison.json")
    decision = read_json(decision_dir / "benchmark_scorecard_decision.json")
    decision_view = decision_summary(decision)
    remediation_gate = remediation_gate_status(run_config, decision_view)
    if remediation_gate["decision"] == "stop":
        issue_list.append("remediation gate blocked: decision contains remediation rows")
    status = "pass" if not issue_list else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "decision": "comparison-evidence-ready" if status == "pass" else "fix-comparison-smoke-chain",
        "issue_count": len(issue_list),
        "issues": issue_list,
        "out_dir": str(out_dir),
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "comparison_dir": str(comparison_dir),
        "decision_dir": str(decision_dir),
        "benchmark_history_dir": str(history_dir),
        "run_config": run_config,
        "commands": command_results,
        "artifacts": artifacts,
        "baseline_smoke": smoke_summary(baseline_smoke),
        "candidate_smoke": smoke_summary(candidate_smoke),
        "scorecard_comparison": comparison_summary(comparison),
        "scorecard_decision": decision_view,
        "benchmark_history": history_summary(history_report, history_outputs),
        "remediation_gate": remediation_gate,
        "interpretation": {
            "comparison_is_smoke_only": True,
            "model_quality_claim": "not_claimed",
            "reason": "Tiny CPU scorecard deltas and decisions verify benchmark plumbing and configuration routing, not robust model improvement.",
        },
        "outputs": {
            "summary_json": str(out_dir / SUMMARY_JSON_FILENAME),
            "summary_text": str(out_dir / SUMMARY_TEXT_FILENAME),
        },
    }


def build_tiny_benchmark_history(
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
) -> tuple[dict[str, Any], dict[str, str]]:
    comparison_json = comparison_dir / "benchmark_scorecard_comparison.json"
    decision_json = decision_dir / "benchmark_scorecard_decision.json"
    if not comparison_json.is_file() or not decision_json.is_file():
        return {}, {}
    report = build_benchmark_history(
        [comparison_json],
        decision_paths=[decision_json],
        names=["tiny-scorecard-smoke"],
        evidence_kind="tiny-smoke",
        title="MiniGPT tiny scorecard smoke benchmark history",
    )
    outputs = write_benchmark_history_outputs(report, history_dir)
    return report, outputs


def artifact_status(
    baseline_dir: Path,
    candidate_dir: Path,
    comparison_dir: Path,
    decision_dir: Path,
    history_dir: Path,
) -> dict[str, Any]:
    paths = {
        "baseline_smoke_summary": baseline_dir / "tiny_standard_benchmark_smoke_summary.json",
        "baseline_scorecard": baseline_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json",
        "baseline_pair_batch": baseline_dir / "run" / "pair_batch" / "pair_generation_batch.json",
        "candidate_smoke_summary": candidate_dir / "tiny_standard_benchmark_smoke_summary.json",
        "candidate_scorecard": candidate_dir / "run" / "benchmark-scorecard" / "benchmark_scorecard.json",
        "candidate_pair_batch": candidate_dir / "run" / "pair_batch" / "pair_generation_batch.json",
        "comparison_json": comparison_dir / "benchmark_scorecard_comparison.json",
        "comparison_csv": comparison_dir / "benchmark_scorecard_comparison.csv",
        "comparison_case_delta_csv": comparison_dir / "benchmark_scorecard_case_deltas.csv",
        "comparison_markdown": comparison_dir / "benchmark_scorecard_comparison.md",
        "comparison_html": comparison_dir / "benchmark_scorecard_comparison.html",
        "decision_json": decision_dir / "benchmark_scorecard_decision.json",
        "decision_csv": decision_dir / "benchmark_scorecard_decision.csv",
        "decision_remediation_csv": decision_dir / "benchmark_scorecard_decision_remediation.csv",
        "decision_markdown": decision_dir / "benchmark_scorecard_decision.md",
        "decision_html": decision_dir / "benchmark_scorecard_decision.html",
        "benchmark_history_json": history_dir / "benchmark_history.json",
        "benchmark_history_csv": history_dir / "benchmark_history.csv",
        "benchmark_history_markdown": history_dir / "benchmark_history.md",
        "benchmark_history_html": history_dir / "benchmark_history.html",
    }
    return {f"{key}_path": str(path) for key, path in paths.items()} | {f"{key}_exists": path.is_file() for key, path in paths.items()}


def smoke_summary(payload: dict[str, Any]) -> dict[str, Any]:
    scorecard = as_dict(payload.get("benchmark_scorecard"))
    pair_batch = as_dict(payload.get("pair_batch"))
    eval_suite = as_dict(payload.get("eval_suite"))
    return {
        "available": bool(payload),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "eval_suite_case_count": eval_suite.get("case_count"),
        "scorecard_overall_status": scorecard.get("overall_status"),
        "scorecard_overall_score": scorecard.get("overall_score"),
        "pair_same_checkpoint_baseline": pair_batch.get("same_checkpoint_baseline"),
        "pair_generated_difference_count": pair_batch.get("generated_difference_count"),
    }


def comparison_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    baseline = as_dict(payload.get("baseline"))
    best_overall = as_dict(payload.get("best_by_overall_score"))
    best_rubric = as_dict(payload.get("best_by_rubric_avg_score"))
    return {
        "available": bool(payload),
        "scorecard_count": payload.get("scorecard_count"),
        "baseline_name": baseline.get("name"),
        "best_by_overall_score": best_overall.get("name"),
        "best_by_rubric_avg_score": best_rubric.get("name"),
        "improved_overall_count": summary.get("improved_overall_count"),
        "regressed_overall_count": summary.get("regressed_overall_count"),
        "improved_rubric_count": summary.get("improved_rubric_count"),
        "regressed_rubric_count": summary.get("regressed_rubric_count"),
        "case_delta_count": summary.get("case_delta_count"),
        "case_regression_count": summary.get("case_regression_count"),
        "generation_quality_flag_improvement_count": summary.get("generation_quality_flag_improvement_count"),
        "generation_quality_flag_regression_count": summary.get("generation_quality_flag_regression_count"),
        "non_comparison_ready_count": summary.get("non_comparison_ready_count"),
        "recommendation_count": len(payload.get("recommendations")) if isinstance(payload.get("recommendations"), list) else 0,
    }


def history_summary(report: dict[str, Any], outputs: dict[str, str]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    requirement = as_dict(report.get("readiness_requirement"))
    return {
        "available": bool(report),
        "entry_count": summary.get("entry_count"),
        "ready_count": summary.get("ready_count"),
        "review_count": summary.get("review_count"),
        "blocked_count": summary.get("blocked_count"),
        "best_candidate_name": summary.get("best_candidate_name"),
        "model_quality_claim": summary.get("model_quality_claim"),
        "readiness_requirement_status": requirement.get("status"),
        "readiness_requirement_decision": requirement.get("decision"),
        "readiness_requirement_exit_code": requirement.get("exit_code"),
        "readiness_requirement_failed_reasons": requirement.get("failed_reasons", []),
        "outputs": outputs,
    }


def decision_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(payload.get("summary"))
    selected = as_dict(payload.get("selected_run"))
    evaluations = list_of_dicts(payload.get("candidate_evaluations"))
    nonbaseline = [item for item in evaluations if not item.get("is_baseline")]
    blocked = [item for item in nonbaseline if item.get("blockers")]
    review = [item for item in nonbaseline if item.get("review_items") and not item.get("blockers")]
    threshold_profile = threshold_block_profile(blocked, payload.get("min_rubric_score"), summary)
    threshold_block = first_threshold_block(blocked, payload.get("min_rubric_score"), summary)
    raw_recommendations = payload.get("recommendations")
    recommendations = [str(item) for item in raw_recommendations if isinstance(item, str)] if isinstance(raw_recommendations, list) else []
    remediation_plan = list_of_dicts(payload.get("remediation_plan"))
    first_remediation = remediation_plan[0] if remediation_plan else {}
    return {
        "available": bool(payload),
        "decision_status": payload.get("decision_status"),
        "recommended_action": payload.get("recommended_action"),
        "selected_name": selected.get("name"),
        "selected_relation": selected.get("decision_relation"),
        "candidate_evaluation_count": len(evaluations),
        "candidate_count": summary.get("candidate_count"),
        "clean_candidate_count": summary.get("clean_candidate_count"),
        "review_candidate_count": summary.get("review_candidate_count"),
        "blocked_candidate_count": summary.get("blocked_candidate_count"),
        "non_comparison_ready_candidate_count": summary.get("non_comparison_ready_candidate_count"),
        "blocker_category_counts": as_dict(summary.get("blocker_category_counts")),
        "dominant_blocker_category": summary.get("dominant_blocker_category"),
        "review_category_counts": as_dict(summary.get("review_category_counts")),
        "dominant_review_category": summary.get("dominant_review_category"),
        "remediation_plan_count": summary.get("remediation_plan_count"),
        "remediation_blocker_count": summary.get("remediation_blocker_count"),
        "remediation_review_count": summary.get("remediation_review_count"),
        "dominant_remediation_kind": summary.get("dominant_remediation_kind"),
        "dominant_remediation_category": summary.get("dominant_remediation_category"),
        "dominant_remediation_action": summary.get("dominant_remediation_action"),
        "blocked_candidate_names": [str(item.get("name")) for item in blocked if item.get("name") is not None],
        "review_candidate_names": [str(item.get("name")) for item in review if item.get("name") is not None],
        "first_blocked_candidate": first_name(blocked),
        "first_blocker": first_list_item(blocked, "blockers"),
        "first_threshold_blocked_candidate": threshold_block.get("name"),
        "first_threshold_blocker": threshold_block.get("blocker"),
        "first_threshold_rubric_score": threshold_block.get("rubric_avg_score"),
        "first_threshold_min_rubric_score": threshold_block.get("min_rubric_score"),
        "first_threshold_margin": threshold_block.get("margin"),
        "threshold_blocked_candidate_count": threshold_profile.get("blocked_candidate_count"),
        "threshold_blocked_candidate_names": threshold_profile.get("blocked_candidate_names"),
        "threshold_closest_candidate": threshold_profile.get("closest_candidate"),
        "threshold_closest_margin": threshold_profile.get("closest_margin"),
        "threshold_largest_gap_candidate": threshold_profile.get("largest_gap_candidate"),
        "threshold_largest_gap_margin": threshold_profile.get("largest_gap_margin"),
        "first_review_candidate": first_name(review),
        "first_review_item": first_list_item(review, "review_items"),
        "remediation_count": len(remediation_plan),
        "first_remediation_category": first_remediation.get("category"),
        "first_remediation_action_code": first_remediation.get("action_code"),
        "first_remediation_severity": first_remediation.get("severity"),
        "first_remediation_owner_scope": first_remediation.get("owner_scope"),
        "first_remediation_action": first_remediation.get("action"),
        "recommendation_count": len(recommendations),
        "first_recommendation": recommendations[0] if recommendations else None,
    }


def remediation_gate_status(run_config: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    required = bool(run_config.get("require_clean_remediation"))
    remediation_count = int(decision.get("remediation_count") or 0)
    failed = required and remediation_count > 0
    issues = []
    if failed:
        issues.append(
            {
                "code": "remediation_rows_present",
                "severity": decision.get("first_remediation_severity") or "blocker",
                "category": decision.get("first_remediation_category"),
                "action_code": decision.get("first_remediation_action_code"),
                "owner_scope": decision.get("first_remediation_owner_scope"),
                "count": remediation_count,
            }
        )
    return {
        "required": required,
        "status": "fail" if failed else "pass",
        "decision": "stop" if failed else "continue",
        "remediation_count": remediation_count,
        "issue_count": len(issues),
        "issues": issues,
        "first_category": decision.get("first_remediation_category"),
        "first_action_code": decision.get("first_remediation_action_code"),
        "first_severity": decision.get("first_remediation_severity"),
        "first_owner_scope": decision.get("first_remediation_owner_scope"),
        "reason": "remediation rows must be cleared before strict smoke promotion" if failed else "clean remediation is not required or no remediation rows were found",
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def first_name(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    value = rows[0].get("name")
    return None if value is None else str(value)


def first_list_item(rows: list[dict[str, Any]], key: str) -> str | None:
    for row in rows:
        values = row.get(key)
        if isinstance(values, list):
            for item in values:
                if item is not None:
                    return str(item)
    return None


def first_threshold_block(rows: list[dict[str, Any]], min_rubric_score: Any, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = as_dict(summary)
    if summary.get("first_threshold_blocked_candidate") is not None:
        return {
            "name": summary.get("first_threshold_blocked_candidate"),
            "blocker": summary.get("first_threshold_blocker"),
            "rubric_avg_score": summary.get("first_threshold_rubric_score"),
            "min_rubric_score": summary.get("first_threshold_min_rubric_score"),
            "margin": summary.get("first_threshold_margin"),
        }
    blocks = threshold_blocks(rows, min_rubric_score)
    return blocks[0] if blocks else {}


def threshold_block_profile(rows: list[dict[str, Any]], min_rubric_score: Any, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = as_dict(summary)
    if summary.get("threshold_blocked_candidate_count") is not None:
        return {
            "blocked_candidate_count": summary.get("threshold_blocked_candidate_count"),
            "blocked_candidate_names": summary.get("threshold_blocked_candidate_names"),
            "closest_candidate": summary.get("threshold_closest_candidate"),
            "closest_margin": summary.get("threshold_closest_margin"),
            "largest_gap_candidate": summary.get("threshold_largest_gap_candidate"),
            "largest_gap_margin": summary.get("threshold_largest_gap_margin"),
        }
    blocks = threshold_blocks(rows, min_rubric_score)
    if not blocks:
        return {
            "blocked_candidate_count": 0,
            "blocked_candidate_names": [],
            "closest_candidate": None,
            "closest_margin": None,
            "largest_gap_candidate": None,
            "largest_gap_margin": None,
        }
    with_margin = [item for item in blocks if item.get("margin") is not None]
    closest = max(with_margin, key=lambda item: float(item.get("margin") or 0.0)) if with_margin else {}
    largest_gap = min(with_margin, key=lambda item: float(item.get("margin") or 0.0)) if with_margin else {}
    return {
        "blocked_candidate_count": len(blocks),
        "blocked_candidate_names": [str(item.get("name")) for item in blocks if item.get("name") is not None],
        "closest_candidate": closest.get("name"),
        "closest_margin": closest.get("margin"),
        "largest_gap_candidate": largest_gap.get("name"),
        "largest_gap_margin": largest_gap.get("margin"),
    }


def threshold_blocks(rows: list[dict[str, Any]], min_rubric_score: Any) -> list[dict[str, Any]]:
    threshold = float_or_none(min_rubric_score)
    blocks = []
    for row in rows:
        blocker = first_matching_list_item(row, "blockers", "rubric_avg_score below")
        if blocker is None:
            continue
        rubric_score = float_or_none(row.get("rubric_avg_score"))
        margin = None if rubric_score is None or threshold is None else round(rubric_score - threshold, 4)
        blocks.append(
            {
                "name": None if row.get("name") is None else str(row.get("name")),
                "blocker": blocker,
                "rubric_avg_score": rubric_score,
                "min_rubric_score": threshold,
                "margin": margin,
            }
        )
    return blocks


def first_matching_list_item(row: dict[str, Any], key: str, prefix: str) -> str | None:
    values = row.get(key)
    if not isinstance(values, list):
        return None
    for item in values:
        text = str(item)
        if text.startswith(prefix):
            return text
    return None


def float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


__all__ = [
    "artifact_status",
    "build_summary",
    "build_tiny_benchmark_history",
    "comparison_summary",
    "decision_summary",
    "first_list_item",
    "first_matching_list_item",
    "first_name",
    "first_threshold_block",
    "float_or_none",
    "history_summary",
    "read_json",
    "remediation_gate_status",
    "smoke_summary",
    "threshold_block_profile",
    "threshold_blocks",
]
