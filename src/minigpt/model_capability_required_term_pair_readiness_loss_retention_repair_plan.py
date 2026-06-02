from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_heldout_failure_diagnostic import (
    PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_loss_retention_repair_plan.json"
PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_loss_retention_repair_plan.csv"
PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_loss_retention_repair_plan.txt"
PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_loss_retention_repair_plan.md"
PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_loss_retention_repair_plan.html"


def locate_loss_retention_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_HELDOUT_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-retention repair plan input must be a JSON object")
    return dict(payload)


def build_loss_retention_repair_plan(
    diagnostic_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(diagnostic_report.get("summary"))
    checks = _checks(diagnostic_report, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness loss-retention repair plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_diagnostic_path": str(source_path or ""),
        "source_diagnostic": {
            "status": diagnostic_report.get("status"),
            "decision": diagnostic_report.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _checks(diagnostic_report: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic_report.get("status") == "pass", diagnostic_report.get("status"), "source diagnostic must pass"),
        _check(
            "diagnostic_decision",
            diagnostic_report.get("decision") == "pair_readiness_loss_prompt_absorbed_by_fixed",
            diagnostic_report.get("decision"),
            "loss-retention repair follows only loss-prompt fixed-pollution",
        ),
        _check(
            "loss_missing",
            int(summary.get("loss_hit_count") or 0) == 0,
            summary.get("loss_hit_count"),
            "loss direct probe should be missing before this repair",
        ),
        _check(
            "fixed_dominance_observed",
            int(summary.get("loss_prompt_fixed_pollution_count") or 0) > 0,
            summary.get("loss_prompt_fixed_pollution_count"),
            "loss prompt must show fixed pollution",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_next_artifact": "pair_readiness_loss_retention_contract_patch",
        "repair_focus": "restore loss direct retention without sacrificing fixed direct retention",
        "contract_patch": [
            "duplicate loss prefix progression rows",
            "add loss anti-fixed contamination rows",
            "keep fixed direct rows unchanged",
            "keep heldout pair probe excluded from training",
        ],
        "training_policy": "rebalance loss rows in corpus materialization before another real training run",
        "success_guard": "loss= and fixed= must both hit on heldout direct replay",
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "repair_focus": plan.get("repair_focus"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_loss_retention_repair_plan_ready"
    return "fix_pair_readiness_loss_retention_repair_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The diagnostic does not support a loss-retention repair plan.",
            "next_action": "repair diagnostic evidence before patching the contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The heldout loss prompt is absorbed by fixed, so the next contract patch should reinforce loss retention.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_LOSS_RETENTION_REPAIR_PLAN_TEXT_FILENAME",
    "build_loss_retention_repair_plan",
    "locate_loss_retention_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
