from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision.html"


def locate_repair_checkpoint_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_CHECKPOINT_COMPARISON_JSON_FILENAME
    return source


def locate_repair_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME
    return source


def locate_repair_seed(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME
    return source


def locate_repair_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded real replay repair strategy revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision(
    comparison_report: dict[str, Any],
    repair_plan_report: dict[str, Any],
    repair_seed_report: dict[str, Any],
    training_run_report: dict[str, Any],
    *,
    comparison_path: str | Path | None = None,
    repair_plan_path: str | Path | None = None,
    repair_seed_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay repair strategy revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    comparison_summary = as_dict(comparison_report.get("summary"))
    plan_summary = as_dict(repair_plan_report.get("summary"))
    seed_summary = as_dict(repair_seed_report.get("summary"))
    training_summary = as_dict(training_run_report.get("summary"))
    case_rows = list_of_dicts(comparison_report.get("case_rows"))
    case_actions = _case_actions(case_rows)
    strategy_actions = _strategy_actions(comparison_summary, plan_summary, seed_summary, training_summary)
    checks = _checks(comparison_report, repair_plan_report, repair_seed_report, training_run_report, comparison_summary, case_rows, case_actions)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    strategy = _strategy(status, comparison_summary, case_actions, strategy_actions)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, strategy),
        "failed_count": len(issues),
        "issues": issues,
        "source_comparison": str(comparison_path or ""),
        "source_repair_plan": str(repair_plan_path or ""),
        "source_repair_seed": str(repair_seed_path or ""),
        "source_training_run": str(training_run_path or ""),
        "source_summaries": {
            "comparison": comparison_summary,
            "repair_plan": plan_summary,
            "repair_seed": seed_summary,
            "training_run": training_summary,
        },
        "case_actions": case_actions,
        "strategy_actions": strategy_actions,
        "check_rows": checks,
        "strategy_revision": strategy,
        "summary": _summary(status, checks, strategy),
        "interpretation": _interpretation(status, strategy),
    }


def resolve_exit_code(report: dict[str, Any], *, require_revision_ready: bool) -> int:
    return 1 if require_revision_ready and report.get("status") != "pass" else 0


def _case_actions(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions = []
    for row in case_rows:
        if row.get("repair_pass") is True:
            continue
        case_id = str(row.get("case_id") or "unknown-case")
        baseline_pass = row.get("baseline_pass") is True
        actions.append(
            {
                "case_id": case_id,
                "severity": "regression" if baseline_pass else "persistent_gap",
                "baseline_pass": baseline_pass,
                "repair_pass": False,
                "baseline_hit_terms": row.get("baseline_hit_terms", []),
                "repair_hit_terms": row.get("repair_hit_terms", []),
                "repair_missed_terms": row.get("repair_missed_terms", []),
                "recommended_seed_change": _recommended_seed_change(row, baseline_pass),
                "required_guardrail": "preserve_baseline_pass_before_accepting_repair_checkpoint" if baseline_pass else "prove_failed_case_recovery_before_promotion",
            }
        )
    return actions


def _recommended_seed_change(row: dict[str, Any], baseline_pass: bool) -> str:
    missed = [str(item) for item in row.get("repair_missed_terms", [])]
    if baseline_pass:
        return "add_baseline_preservation_and_contrastive_repair_examples"
    if "fixed" in missed and "loss" in missed:
        return "add_direct_prompt_to_fixed_loss_bridge_examples"
    return "add_missing_term_retention_examples"


def _strategy_actions(
    comparison_summary: dict[str, Any],
    plan_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    training_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _action("block_current_repair_checkpoint", "gate", "Do not promote the v810 repair checkpoint after replay regression.", comparison_summary.get("passed_case_delta")),
        _action("add_baseline_preservation_examples", "seed", "Include examples that protect cases the baseline already passed.", comparison_summary.get("baseline_passed_case_count")),
        _action("balance_direct_and_self_check_examples", "seed", "Keep direct answers and self-check answers, but add preservation and contrastive coverage.", seed_summary.get("example_count")),
        _action("short_training_with_replay_first", "training", "Keep repair training bounded and require immediate replay comparison before promotion.", training_summary.get("final_step")),
        _action("retain_original_repair_tasks", "plan", "Carry the original failed-case repair tasks forward instead of inventing unrelated objectives.", plan_summary.get("task_count")),
    ]


def _action(action_id: str, category: str, detail: str, evidence: Any) -> dict[str, Any]:
    return {"action_id": action_id, "category": category, "detail": detail, "evidence": evidence}


def _checks(
    comparison: dict[str, Any],
    repair_plan: dict[str, Any],
    repair_seed: dict[str, Any],
    training_run: dict[str, Any],
    comparison_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
    case_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "comparison evidence must pass"),
        _check("comparison_ready", comparison_summary.get("bounded_repair_checkpoint_comparison_ready") is True, comparison_summary.get("bounded_repair_checkpoint_comparison_ready"), "comparison summary must be ready"),
        _check("repair_not_improved", comparison_summary.get("repair_checkpoint_improved") is not True, comparison_summary.get("repair_checkpoint_improved"), "strategy revision is only needed when repair checkpoint did not improve"),
        _check("promotion_blocked", comparison_summary.get("promotion_ready") is False, comparison_summary.get("promotion_ready"), "promotion must already be blocked by comparison"),
        _check("repair_plan_passed", repair_plan.get("status") == "pass", repair_plan.get("status"), "source repair plan must pass"),
        _check("repair_seed_passed", repair_seed.get("status") == "pass", repair_seed.get("status"), "source repair seed must pass"),
        _check("training_run_passed", training_run.get("status") == "pass", training_run.get("status"), "source training evidence must pass"),
        _check("case_rows_present", bool(case_rows), len(case_rows), "strategy revision must inspect case rows"),
        _check("case_actions_present", bool(case_actions), len(case_actions), "strategy revision must create case actions for failed repair replay cases"),
    ]


def _strategy(
    status: str,
    comparison_summary: dict[str, Any],
    case_actions: list[dict[str, Any]],
    strategy_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "blocked_checkpoint": True,
        "regression_detected": comparison_summary.get("repair_checkpoint_regressed") is True,
        "repair_checkpoint_improved": comparison_summary.get("repair_checkpoint_improved") is True,
        "passed_case_delta": comparison_summary.get("passed_case_delta"),
        "pass_rate_delta": comparison_summary.get("pass_rate_delta"),
        "case_action_count": len(case_actions),
        "strategy_action_count": len(strategy_actions),
        "required_guardrails": [
            "do_not_promote_regressed_checkpoint",
            "preserve_baseline_passed_cases",
            "require_replay_comparison_after_each_repair_training",
        ],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_repair_seed_revision",
        "next_step": "build_bounded_real_replay_repair_seed_revision" if status == "pass" else "repair_strategy_revision_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], strategy: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_repair_strategy_revision_ready": status == "pass" and strategy.get("ready") is True,
        "blocked_checkpoint": strategy.get("blocked_checkpoint"),
        "regression_detected": strategy.get("regression_detected"),
        "repair_checkpoint_improved": strategy.get("repair_checkpoint_improved"),
        "passed_case_delta": strategy.get("passed_case_delta"),
        "pass_rate_delta": strategy.get("pass_rate_delta"),
        "case_action_count": strategy.get("case_action_count"),
        "strategy_action_count": strategy.get("strategy_action_count"),
        "proposed_next_artifact": strategy.get("proposed_next_artifact"),
        "next_step": strategy.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, strategy: dict[str, Any]) -> str:
    if status == "pass" and strategy.get("ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_strategy_revision_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision"


def _interpretation(status: str, strategy: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Strategy revision inputs are incomplete.", "next_action": "repair strategy revision inputs"}
    return {
        "model_quality_claim": "repair_strategy_only",
        "reason": "The strategy revises the repair route after regression; it does not prove model improvement until a revised seed is trained and replayed.",
        "next_action": strategy.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_repair_strategy_revision",
    "locate_repair_checkpoint_comparison",
    "locate_repair_plan",
    "locate_repair_seed",
    "locate_repair_training_run",
    "read_json_report",
    "resolve_exit_code",
]
