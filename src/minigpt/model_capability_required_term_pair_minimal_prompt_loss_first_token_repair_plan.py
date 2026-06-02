from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_minimal_prompt_branch_bias_diagnostic import (
    PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.json"
PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.csv"
PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.txt"
PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.md"
PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.html"

LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE = "minimal_prompt_loss_first_token_repair_objective"


def locate_loss_first_token_repair_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_MINIMAL_PROMPT_BRANCH_BIAS_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-first-token repair plan input must be a JSON object")
    return dict(payload)


def build_loss_first_token_repair_plan(
    branch_bias_diagnostic: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(branch_bias_diagnostic.get("summary"))
    checks = _check_rows(branch_bias_diagnostic, summary)
    failed_checks = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    plan = _plan(status, summary)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt loss-first-token repair plan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed_checks),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed_checks],
        "source_branch_bias_diagnostic_path": str(source_path or ""),
        "source_branch_bias_diagnostic": {
            "status": branch_bias_diagnostic.get("status"),
            "decision": branch_bias_diagnostic.get("decision"),
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


def _check_rows(diagnostic: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "branch-bias diagnostic must pass"),
        _check(
            "fixed_absorbs_loss_confirmed",
            diagnostic.get("decision") == "minimal_prompt_branch_bias_fixed_absorbs_loss",
            diagnostic.get("decision"),
            "repair plan requires confirmed fixed-absorbs-loss failure",
        ),
        _check(
            "loss_hit_absent",
            int(summary.get("loss_hit_count") or 0) == 0,
            summary.get("loss_hit_count"),
            "loss branch should be absent before applying loss-first-token repair",
        ),
        _check(
            "fixed_hit_present",
            int(summary.get("fixed_hit_count") or 0) > 0,
            summary.get("fixed_hit_count"),
            "fixed branch should remain a known signal while repairing loss",
        ),
        _check(
            "dominant_bias_fixed",
            summary.get("dominant_bias") == "fixed",
            summary.get("dominant_bias"),
            "dominant bias must be fixed",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "proposed_corpus_mode": LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE,
        "source_corpus_mode": summary.get("corpus_mode", ""),
        "seed_to_rerun": summary.get("seed"),
        "repair_focus": "loss_first_token_and_branch_separation",
        "kept_boundary": "minimal prompt only; no contextual answer-bearing anchor",
        "expected_prompt_surface": ["fixed=", "loss="],
        "expected_change": "increase loss first-token pressure while retaining fixed direct rows",
        "recommended_next_action": f"rerun seed {summary.get('seed')} with corpus_mode={LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE}",
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
        return "minimal_prompt_loss_first_token_repair_plan_ready"
    return "fix_minimal_prompt_loss_first_token_repair_plan_input"


def _interpretation(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The branch-bias diagnostic does not justify a loss-first-token repair plan.",
            "next_action": "repair diagnostic evidence before changing corpus",
        }
    return {
        "model_quality_claim": "repair_plan_only",
        "reason": "The previous run learned fixed but started loss prompts with fixed, so the next corpus should strengthen loss first-token pressure.",
        "next_action": plan.get("recommended_next_action", ""),
    }


__all__ = [
    "LOSS_FIRST_TOKEN_REPAIR_CORPUS_MODE",
    "PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_LOSS_FIRST_TOKEN_REPAIR_PLAN_TEXT_FILENAME",
    "build_loss_first_token_repair_plan",
    "locate_loss_first_token_repair_plan_source",
    "read_json_report",
    "resolve_exit_code",
]
