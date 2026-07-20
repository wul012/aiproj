from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_minimal_prompt_batch_closeout import (
    PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_SPLIT_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_split_plan.json"
PAIR_READINESS_SPLIT_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_split_plan.csv"
PAIR_READINESS_SPLIT_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_split_plan.txt"
PAIR_READINESS_SPLIT_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_split_plan.md"
PAIR_READINESS_SPLIT_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_split_plan.html"


def locate_pair_readiness_split_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_MINIMAL_PROMPT_BATCH_CLOSEOUT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness split plan input must be a JSON object")
    return dict(payload)


def build_pair_readiness_split_plan(
    closeout_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(closeout_report.get("summary"))
    checks = _checks(closeout_report, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair-readiness split plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_closeout_path": str(source_path or ""),
        "source_closeout": {
            "status": closeout_report.get("status"),
            "decision": closeout_report.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def _checks(closeout_report: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("closeout_passed", closeout_report.get("status") == "pass", closeout_report.get("status"), "minimal prompt closeout must pass"),
        _check(
            "closeout_decision",
            closeout_report.get("decision") == "minimal_prompt_batch_closed_without_pair_full",
            closeout_report.get("decision"),
            "split plan only follows a closed no-pair-full minimal-prompt batch",
        ),
        _check("three_real_reports", int(summary.get("report_count") or 0) >= 3, summary.get("report_count"), "need at least three real attempts"),
        _check(
            "no_pair_full",
            int(summary.get("pair_full_report_count") or 0) == 0,
            summary.get("pair_full_report_count"),
            "pair-full candidate should be promoted instead of planning a split",
        ),
        _check(
            "mixed_failures",
            int(summary.get("fixed_only_report_count") or 0) > 0 and int(summary.get("loss_only_report_count") or 0) > 0,
            f"fixed={summary.get('fixed_only_report_count')}, loss={summary.get('loss_only_report_count')}",
            "split plan needs evidence that both branches can win separately",
        ),
    ]


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_next_artifact": "pair_readiness_split_contract",
        "training_split": [
            "direct_branch_completion_rows",
            "anti_contamination_rows",
            "balanced_prefix_progression_rows",
        ],
        "evaluation_split": ["fixed=", "loss=", "heldout_fixed_loss_pair_probe"],
        "holdout_rule": "do not train on the exact heldout pair probe used for promotion",
        "promotion_guard": "claim pair capability only when heldout fixed and loss continuations both hit",
        "stop_condition": "if split contract cannot separate train/eval rows, pause training and redesign objective",
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "proposed_next_artifact": plan.get("proposed_next_artifact", ""),
        "training_split_count": len(plan.get("training_split", [])),
        "evaluation_split_count": len(plan.get("evaluation_split", [])),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_split_plan_ready"
    return "fix_pair_readiness_split_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The closeout evidence is not sufficient to plan a pair-readiness split.",
            "next_action": "repair closeout evidence before defining a new training/evaluation split",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "Repeated minimal-prompt training produced separate branch wins but no pair-full candidate, so the next step should separate train/eval readiness.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_SPLIT_PLAN_CSV_FILENAME",
    "PAIR_READINESS_SPLIT_PLAN_HTML_FILENAME",
    "PAIR_READINESS_SPLIT_PLAN_JSON_FILENAME",
    "PAIR_READINESS_SPLIT_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_SPLIT_PLAN_TEXT_FILENAME",
    "build_pair_readiness_split_plan",
    "locate_pair_readiness_split_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
