from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_replay import PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_selector import PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_SURFACE_POLICY_MINIMALITY_CHECK_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_minimality_check.json"
PAIR_SURFACE_POLICY_MINIMALITY_CHECK_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_minimality_check.csv"
PAIR_SURFACE_POLICY_MINIMALITY_CHECK_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_minimality_check.txt"
PAIR_SURFACE_POLICY_MINIMALITY_CHECK_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_minimality_check.md"
PAIR_SURFACE_POLICY_MINIMALITY_CHECK_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_minimality_check.html"


def locate_surface_policy_minimality_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
    return source


def locate_surface_policy_minimality_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy minimality input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_policy_minimality_check(
    selector_report: dict[str, Any],
    replay_report: dict[str, Any],
    *,
    selector_source_path: str | Path | None = None,
    replay_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    check_rows = _check_rows(selector_report, replay_report)
    issues = _issues(selector_report, replay_report, check_rows)
    summary = _summary(check_rows, selector_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy minimality check",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_selector_path": str(selector_source_path or ""),
        "source_replay_path": str(replay_source_path or ""),
        "check_rows": check_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _check_rows(selector_report: dict[str, Any], replay_report: dict[str, Any]) -> list[dict[str, Any]]:
    selected = as_dict(selector_report.get("selected_policy"))
    selected_id = str(selected.get("policy_id") or "")
    policy_rows = list_of_dicts(replay_report.get("policy_summaries"))
    rows = [
        _check("selected_policy_present", bool(selected_id), selected_id, "selector must name a selected policy"),
        _check(
            "selected_policy_stable",
            _policy(policy_rows, selected_id).get("stable_pair_full") is True,
            selected_id,
            "selected policy must be stable across seeds",
        ),
        _check(
            "non_leaking_baseline_not_stable",
            not any(_is_non_leaking(row.get("policy_id")) and row.get("stable_pair_full") for row in policy_rows),
            selected_id,
            "minimal non-leaking baselines are not stable, so contextual anchoring is still required",
        ),
        _check(
            "selected_policy_contextual_anchor",
            selected.get("leakage_level") == "contextual_anchor",
            selected_id,
            "selected policy should be marked as contextual anchor, not model baseline",
        ),
        _check(
            "promotion_blocked",
            as_dict(selector_report.get("summary")).get("promotion_ready") is False,
            selected_id,
            "selector must block promotion before leakage/minimality is reviewed",
        ),
    ]
    return rows


def _issues(selector_report: dict[str, Any], replay_report: dict[str, Any], check_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if selector_report.get("status") != "pass":
        issues.append("source selector report is not pass")
    if replay_report.get("status") != "pass":
        issues.append("source replay report is not pass")
    for row in check_rows:
        if row.get("status") != "pass":
            issues.append(str(row.get("detail")))
    return issues


def _summary(check_rows: list[dict[str, Any]], selector_report: dict[str, Any]) -> dict[str, Any]:
    selected = as_dict(selector_report.get("selected_policy"))
    passed_count = sum(1 for row in check_rows if row.get("status") == "pass")
    return {
        "selected_policy_id": selected.get("policy_id", ""),
        "selected_leakage_level": selected.get("leakage_level", ""),
        "check_count": len(check_rows),
        "passed_check_count": passed_count,
        "failed_check_count": len(check_rows) - passed_count,
        "contextual_anchor_required": _row_passed(check_rows, "non_leaking_baseline_not_stable"),
        "promotion_ready": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_minimality"
    if summary.get("contextual_anchor_required"):
        return "required_term_pair_surface_policy_contextual_anchor_required"
    return "required_term_pair_surface_policy_minimal_baseline_possible"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "One or more minimality checks failed."
        next_action = "repair selector/replay evidence before policy promotion"
        claim = "not_claimed"
    elif summary.get("contextual_anchor_required"):
        reason = "The selected policy is stable, but non-leaking minimal baselines are not stable."
        next_action = "treat the selected policy as a contextual decoding aid and run leakage-risk documentation"
        claim = "contextual_decode_policy_only"
    else:
        reason = "A non-leaking minimal baseline appears sufficient."
        next_action = "test the minimal baseline on held-out surfaces"
        claim = "minimal_decode_policy_candidate"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


def _check(check_id: str, condition: bool, target: str, detail: str) -> dict[str, Any]:
    return {"id": check_id, "target": target, "status": "pass" if condition else "fail", "detail": detail}


def _policy(rows: list[dict[str, Any]], policy_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("policy_id") == policy_id:
            return row
    return {}


def _is_non_leaking(policy_id: object) -> bool:
    return str(policy_id or "").startswith("single_label")


def _row_passed(rows: list[dict[str, Any]], check_id: str) -> bool:
    return any(row.get("id") == check_id and row.get("status") == "pass" for row in rows)


__all__ = [
    "PAIR_SURFACE_POLICY_MINIMALITY_CHECK_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_MINIMALITY_CHECK_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_MINIMALITY_CHECK_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_MINIMALITY_CHECK_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_MINIMALITY_CHECK_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_policy_minimality_check",
    "locate_surface_policy_minimality_replay_source",
    "locate_surface_policy_minimality_selector_source",
    "read_json_report",
    "resolve_exit_code",
]
