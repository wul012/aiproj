from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay import (
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, utc_now


PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.json"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.csv"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.txt"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.md"
)
PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_repair_plan.html"
)


def locate_pair_prompt_transfer_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair prompt transfer repair plan input must be a JSON object")
    return dict(payload)


def build_pair_prompt_transfer_repair_plan(
    pair_probe_replay: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(pair_probe_replay.get("summary"))
    checks = _checks(pair_probe_replay, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness pair prompt transfer repair plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_pair_probe_replay_path": str(source_path or ""),
        "source_pair_probe_replay": {
            "status": pair_probe_replay.get("status"),
            "decision": pair_probe_replay.get("decision"),
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


def _checks(pair_probe_replay: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("pair_probe_replay_passed", pair_probe_replay.get("status") == "pass", pair_probe_replay.get("status"), "pair-probe replay must execute successfully"),
        _check(
            "pair_probe_not_ready",
            pair_probe_replay.get("decision") == "pair_readiness_direct_completion_pair_probe_replay_not_ready",
            pair_probe_replay.get("decision"),
            "repair follows only the not-ready direct-completion pair-probe replay result",
        ),
        _check("exact_pair_failed", summary.get("exact_heldout_pair_full") is False, summary.get("exact_heldout_pair_full"), "exact heldout pair prompt must be the observed failure"),
        _check("no_pair_prompt_full", int(summary.get("pair_full_count") or 0) == 0, summary.get("pair_full_count"), "plan assumes no pair prompt surface replayed pair-full"),
        _check("heldout_pair_remains_heldout", HELDOUT_PAIR_PROBE == "fixed=|loss=", HELDOUT_PAIR_PROBE, "heldout pair prompt identity must stay explicit"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "closed_claim": "direct_completion_surface_is_promotion_ready",
        "confirmed_boundary": "v738 is direct-probe-only evidence until pair prompt transfer is repaired",
        "proposed_next_artifact": "pair_readiness_pair_prompt_transfer_contract_patch",
        "base_contract_artifact": "pair_readiness_direct_completion_surface_contract",
        "repair_requirements": [
            "add surrogate pair-transfer rows that bind fixed and loss in one training line without using the exact heldout pair probe",
            "cover more than one non-heldout separator style so transfer is not tied to a single string template",
            "preserve fixed=fixed and loss=loss direct-completion rows from the base contract",
            "keep heldout pair prompt fixed=|loss= out of training rows and materialized corpus lines",
            "require pair-probe replay before any promotion claim",
        ],
        "non_goals": [
            "do not train on the exact fixed=|loss= heldout pair prompt",
            "do not increase model size before testing the transfer patch",
            "do not reinterpret v738 as promotion-ready without pair-probe evidence",
        ],
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_ready": bool(plan.get("ready")),
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "repair_requirement_count": len(plan.get("repair_requirements", [])),
        "non_goal_count": len(plan.get("non_goals", [])),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_pair_prompt_transfer_repair_plan_ready"
    return "fix_pair_readiness_pair_prompt_transfer_repair_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The pair-probe replay result does not justify this transfer repair plan.",
            "next_action": "repair or rerun pair-probe replay before patching the contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "Direct-completion training helps direct probes but does not transfer to pair prompts, so the next patch must target non-leaking pair-transfer rows.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_PAIR_PROMPT_TRANSFER_REPAIR_PLAN_TEXT_FILENAME",
    "build_pair_prompt_transfer_repair_plan",
    "locate_pair_prompt_transfer_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
