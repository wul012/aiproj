from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_first_token_preference_diagnostic import (
    PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.json"
PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.csv"
PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.txt"
PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.md"
PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.html"

BALANCED_REPAIR_CORPUS_MODE = "minimal_prompt_balanced_first_token_repair_objective"


def locate_balanced_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("balanced repair plan input must be a JSON object")
    return dict(payload)


def build_balanced_repair_plan(
    tradeoff_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(tradeoff_report.get("summary"))
    checks = _check_rows(tradeoff_report, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    plan = _plan(status)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt balanced repair plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_tradeoff_path": str(source_path or ""),
        "source_tradeoff": {
            "status": tradeoff_report.get("status"),
            "decision": tradeoff_report.get("decision"),
            "summary": summary,
        },
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, checks, plan),
        "interpretation": _interpretation(status, plan),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _check_rows(report: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("tradeoff_passed", report.get("status") == "pass", report.get("status"), "tradeoff diagnostic must pass"),
        _check(
            "tradeoff_confirmed",
            report.get("decision") == "first_token_preference_tradeoff_confirmed",
            report.get("decision"),
            "balanced repair requires confirmed first-token tradeoff",
        ),
        _check(
            "mixed_branch_tradeoff",
            summary.get("mixed_branch_tradeoff_confirmed") is True,
            summary.get("mixed_branch_tradeoff_confirmed"),
            "source reports must include fixed-only and loss-only outcomes",
        ),
        _check(
            "no_pair_full_candidate",
            int(summary.get("pair_full_report_count") or 0) == 0,
            summary.get("pair_full_report_count"),
            "plan should only run when no pair-full candidate exists",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_corpus_mode": BALANCED_REPAIR_CORPUS_MODE,
        "seed_to_rerun": 3535,
        "repair_focus": "balanced_first_token_and_direct_target_retention",
        "kept_boundary": "minimal prompt only; no contextual answer-bearing anchor",
        "expected_prompt_surface": ["fixed=", "loss="],
        "expected_change": "balance fixed/loss first-token pressure after v696 fixed-only and v699 loss-only tradeoff",
        "recommended_next_action": f"rerun seed 3535 with corpus_mode={BALANCED_REPAIR_CORPUS_MODE}",
    }


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "plan_ready": status == "pass" and bool(plan.get("ready")),
        "proposed_corpus_mode": plan.get("proposed_corpus_mode", ""),
        "seed_to_rerun": plan.get("seed_to_rerun"),
        "repair_focus": plan.get("repair_focus", ""),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "minimal_prompt_balanced_repair_plan_ready"
    return "fix_minimal_prompt_balanced_repair_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The tradeoff evidence is not sufficient for a balanced repair plan.",
            "next_action": "repair tradeoff comparison before changing corpus",
        }
    return {
        "model_quality_claim": "repair_plan_only",
        "reason": "The two real runs form fixed-only and loss-only outcomes, so the next corpus should balance first-token pressure.",
        "next_action": plan.get("recommended_next_action", ""),
    }


__all__ = [
    "BALANCED_REPAIR_CORPUS_MODE",
    "PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_BALANCED_REPAIR_PLAN_TEXT_FILENAME",
    "build_balanced_repair_plan",
    "locate_balanced_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
