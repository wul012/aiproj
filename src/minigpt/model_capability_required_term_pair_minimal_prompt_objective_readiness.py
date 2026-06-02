from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_branch_closeout import (
    PAIR_SURFACE_BRANCH_CLOSEOUT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_objective_readiness.json"
PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_objective_readiness.csv"
PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_objective_readiness.txt"
PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_objective_readiness.md"
PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_objective_readiness.html"


def locate_minimal_prompt_objective_readiness_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_BRANCH_CLOSEOUT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("minimal prompt objective readiness input must be a JSON object")
    return dict(payload)


def build_minimal_prompt_objective_readiness(
    surface_branch_closeout: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(surface_branch_closeout.get("summary"))
    interpretation = as_dict(surface_branch_closeout.get("interpretation"))
    checks = _check_rows(surface_branch_closeout, summary, interpretation)
    failed_checks = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    objective = _objective(status, summary)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt objective readiness",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, objective),
        "failed_count": len(failed_checks),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed_checks],
        "source_surface_branch_closeout_path": str(source_path or ""),
        "source_surface_branch_closeout": {
            "status": surface_branch_closeout.get("status"),
            "decision": surface_branch_closeout.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "objective": objective,
        "summary": _summary(status, checks, objective),
        "interpretation": _interpretation(status, objective),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _check_rows(closeout: dict[str, Any], summary: dict[str, Any], interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        _check(
            "closeout_passed",
            closeout.get("status") == "pass",
            closeout.get("status"),
            "surface branch closeout must pass before opening the next objective",
        ),
        _check(
            "contextual_aid_closed",
            summary.get("contextual_decode_aid_ready") is True,
            summary.get("contextual_decode_aid_ready"),
            "previous branch must be closed as contextual decode aid",
        ),
        _check(
            "promotion_blocked",
            summary.get("promotion_allowed") is False,
            summary.get("promotion_allowed"),
            "previous branch must not be promotable as a baseline",
        ),
        _check(
            "minimal_prompt_route_selected",
            summary.get("recommended_next_route") == "minimal_prompt_surface_objective",
            summary.get("recommended_next_route"),
            "recommended next route must be minimal_prompt_surface_objective",
        ),
        _check(
            "model_quality_not_promoted",
            interpretation.get("model_quality_claim") == "contextual_decode_aid_closed_branch",
            interpretation.get("model_quality_claim"),
            "readiness must preserve the no-promotion model-quality boundary",
        ),
    ]
    return rows


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if passed else "fail",
        "actual": actual,
        "detail": detail,
    }


def _objective(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "objective_id": "minimal_prompt_surface_objective",
        "ready": ready,
        "claim_boundary": "minimal prompt only; no contextual answer-bearing anchor",
        "source_branch": "required_term_pair_contextual_surface_policy",
        "entry_condition": "contextual decode aid closed and promotion blocked",
        "target_prompt_surface": "fixed= / loss=",
        "blocked_prompt_surface": "contextual variants that reveal the other answer before the target prompt",
        "success_criterion": "both fixed= and loss= produce their exact terms without contextual anchor across selected seeds",
        "recommended_corpus_mode": "minimal_prompt_equals_surface_objective",
        "recommended_next_version": "v695",
        "recommended_next_action": "add a minimal-prompt corpus contract before running another real checkpoint",
        "source_recommended_route": summary.get("recommended_next_route", ""),
    }


def _summary(status: str, checks: list[dict[str, Any]], objective: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "objective_ready": status == "pass" and bool(objective.get("ready")),
        "objective_id": objective.get("objective_id", ""),
        "recommended_corpus_mode": objective.get("recommended_corpus_mode", ""),
        "recommended_next_version": objective.get("recommended_next_version", ""),
    }


def _decision(status: str, objective: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_minimal_prompt_objective_readiness_input"
    if objective.get("ready"):
        return "minimal_prompt_surface_objective_ready_for_corpus_contract"
    return "minimal_prompt_surface_objective_not_ready"


def _interpretation(status: str, objective: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The previous surface branch closeout is not sufficient to open a minimal-prompt objective.",
            "next_action": "repair closeout evidence before designing a new corpus",
        }
    return {
        "model_quality_claim": "objective_readiness_only",
        "reason": "The previous branch is closed as contextual decode aid, so the next model-quality question must remove the contextual anchor.",
        "next_action": objective.get("recommended_next_action", ""),
    }


__all__ = [
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_TEXT_FILENAME",
    "build_minimal_prompt_objective_readiness",
    "locate_minimal_prompt_objective_readiness_source",
    "read_json_report",
    "resolve_exit_code",
]
