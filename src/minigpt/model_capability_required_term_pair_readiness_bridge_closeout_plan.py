from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_bridge_comparison import (
    PAIR_READINESS_BRIDGE_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_JSON_FILENAME = "model_capability_required_term_pair_readiness_bridge_closeout_plan.json"
PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_CSV_FILENAME = "model_capability_required_term_pair_readiness_bridge_closeout_plan.csv"
PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_readiness_bridge_closeout_plan.txt"
PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_bridge_closeout_plan.md"
PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_HTML_FILENAME = "model_capability_required_term_pair_readiness_bridge_closeout_plan.html"


def locate_bridge_closeout_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_BRIDGE_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bridge closeout plan input must be a JSON object")
    return dict(payload)


def build_bridge_closeout_plan(
    bridge_comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(bridge_comparison.get("summary"))
    checks = _checks(bridge_comparison, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness bridge closeout plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_bridge_comparison_path": str(source_path or ""),
        "source_bridge_comparison": {
            "status": bridge_comparison.get("status"),
            "decision": bridge_comparison.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def _checks(bridge_comparison: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("comparison_passed", bridge_comparison.get("status") == "pass", bridge_comparison.get("status"), "bridge comparison must pass"),
        _check(
            "comparison_decision",
            bridge_comparison.get("decision") == "pair_readiness_bridge_no_improvement_introduced_fixed_pollution",
            bridge_comparison.get("decision"),
            "closeout follows only a bridge route with no improvement and introduced fixed pollution",
        ),
        _check("no_hit_delta", int(summary.get("default_hit_delta") or 0) == 0, summary.get("default_hit_delta"), "bridge route must show no hit-count improvement"),
        _check("pollution_introduced", summary.get("bridge_pollution_introduced") is True, summary.get("bridge_pollution_introduced"), "bridge route must introduce loss-prompt fixed pollution"),
        _check("bridge_not_improved", summary.get("bridge_improved") is False, summary.get("bridge_improved"), "bridge route must not be an improved candidate"),
    ]


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "closed_route": "direct_prompt_bridge_contract_patch",
        "proposed_next_artifact": "pair_readiness_direct_completion_surface_contract",
        "route_change": "replace descriptive bridge rows with compact direct-completion surfaces",
        "next_contract_requirements": [
            "include balanced completion rows such as fixed=fixed and loss=loss without adding the heldout pair probe",
            "include short prefix ladder rows only when both fixed and loss ladders are symmetric",
            "keep paired order rows separate from direct completion rows",
            "surface checks must count exact direct completions and pair-probe leakage separately",
        ],
        "non_goals": [
            "do not add more direct-prompt bridge prose rows",
            "do not increase model size before the new surface contract is trained",
            "do not train on the exact heldout pair probe",
        ],
    }


def _summary(checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": bool(plan.get("ready")),
        "closed_route": plan.get("closed_route"),
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "next_contract_requirement_count": len(plan.get("next_contract_requirements", [])),
        "non_goal_count": len(plan.get("non_goals", [])),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_bridge_closeout_plan_ready"
    return "fix_pair_readiness_bridge_closeout_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The bridge comparison does not justify closing the bridge patch route.",
            "next_action": "repair bridge comparison evidence before planning a new surface contract",
        }
    return {
        "model_quality_claim": "plan_only",
        "reason": "The direct-prompt bridge route did not improve hits and introduced fixed pollution, so it should be closed.",
        "next_action": f"build {plan.get('proposed_next_artifact')}",
    }


__all__ = [
    "PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_CSV_FILENAME",
    "PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_HTML_FILENAME",
    "PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_JSON_FILENAME",
    "PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_MARKDOWN_FILENAME",
    "PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_TEXT_FILENAME",
    "build_bridge_closeout_plan",
    "locate_bridge_closeout_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
