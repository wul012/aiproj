from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_plan import PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_replay import PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_selector.json"
PAIR_SURFACE_POLICY_SELECTOR_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_selector.csv"
PAIR_SURFACE_POLICY_SELECTOR_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_selector.txt"
PAIR_SURFACE_POLICY_SELECTOR_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_selector.md"
PAIR_SURFACE_POLICY_SELECTOR_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_selector.html"

LEAKAGE_RANK = {"none": 0, "contextual_anchor": 1, "target_echo": 9}


def locate_surface_policy_selector_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME
    return source


def locate_surface_policy_selector_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy selector input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_policy_selector(
    policy_plan: dict[str, Any],
    policy_replay: dict[str, Any],
    *,
    plan_source_path: str | Path | None = None,
    replay_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = _candidate_rows(policy_plan, policy_replay)
    issues = _issues(policy_plan, policy_replay, rows)
    selected = _selected_row(rows)
    summary = _summary(rows, selected)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy selector",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_policy_plan_path": str(plan_source_path or ""),
        "source_policy_replay_path": str(replay_source_path or ""),
        "candidate_rows": rows,
        "selected_policy": selected,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _candidate_rows(policy_plan: dict[str, Any], policy_replay: dict[str, Any]) -> list[dict[str, Any]]:
    plan_by_id = {str(row.get("policy_id")): row for row in list_of_dicts(policy_plan.get("policy_rows"))}
    rows = []
    for replay in list_of_dicts(policy_replay.get("policy_summaries")):
        policy_id = str(replay.get("policy_id") or "")
        plan = as_dict(plan_by_id.get(policy_id))
        leakage = str(plan.get("leakage_level") or "")
        template = str(plan.get("prompt_template") or "")
        stable = bool(replay.get("stable_pair_full"))
        rows.append(
            {
                "policy_id": policy_id,
                "stable_pair_full": stable,
                "pair_full_seed_count": replay.get("pair_full_seed_count"),
                "hit_case_count": replay.get("hit_case_count"),
                "leakage_level": leakage,
                "leakage_rank": LEAKAGE_RANK.get(leakage, 5),
                "prompt_template": template,
                "prompt_template_length": len(template),
                "uses_boundary_sentence": "dual boundary" in template,
                "included_in_replay": plan.get("included_in_replay"),
                "selection_score": _selection_score(stable, leakage, template),
                "selection_reason": _selection_reason(stable, leakage, template),
            }
        )
    return rows


def _issues(policy_plan: dict[str, Any], policy_replay: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if policy_plan.get("status") != "pass":
        issues.append("source policy plan is not pass")
    if policy_replay.get("status") != "pass":
        issues.append("source policy replay is not pass")
    if not rows:
        issues.append("policy replay has no candidate rows")
    if rows and not any(row.get("stable_pair_full") for row in rows):
        issues.append("policy replay has no stable pair-full policy")
    return issues


def _selected_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stable = [row for row in rows if row.get("stable_pair_full")]
    if not stable:
        return {}
    ordered = sorted(
        stable,
        key=lambda row: (
            int(row.get("leakage_rank") or 0),
            bool(row.get("uses_boundary_sentence")),
            int(row.get("prompt_template_length") or 0),
            str(row.get("policy_id") or ""),
        ),
    )
    return ordered[0]


def _summary(rows: list[dict[str, Any]], selected: dict[str, Any]) -> dict[str, Any]:
    stable_rows = [row for row in rows if row.get("stable_pair_full")]
    return {
        "candidate_count": len(rows),
        "stable_candidate_count": len(stable_rows),
        "selected_policy_id": selected.get("policy_id", ""),
        "selected_leakage_level": selected.get("leakage_level", ""),
        "selected_uses_boundary_sentence": selected.get("uses_boundary_sentence", False),
        "selected_prompt_template": selected.get("prompt_template", ""),
        "promotion_ready": False,
        "requires_minimality_check": bool(selected),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_selector_inputs"
    if summary.get("selected_policy_id"):
        return "required_term_pair_surface_policy_selected_for_minimality_check"
    return "required_term_pair_surface_policy_not_selected"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "Selector inputs do not provide a stable policy candidate."
        next_action = "repair policy replay before selecting a route"
        claim = "not_claimed"
    else:
        reason = "A stable contextual policy was selected by leakage rank and prompt minimality, but it is not promotion-ready."
        next_action = "run minimality and leakage checks for the selected policy"
        claim = "decode_surface_policy_selected_not_promoted"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


def _selection_score(stable: bool, leakage: str, template: str) -> int:
    if not stable:
        return -1000
    return 100 - (LEAKAGE_RANK.get(leakage, 5) * 20) - len(template)


def _selection_reason(stable: bool, leakage: str, template: str) -> str:
    if not stable:
        return "not stable across seeds"
    if "dual boundary" in template:
        return "stable but longer and tied to training boundary wording"
    if leakage == "contextual_anchor":
        return "stable contextual anchor with shorter prompt template"
    return "stable non-leaking policy"


__all__ = [
    "PAIR_SURFACE_POLICY_SELECTOR_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_SELECTOR_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_SELECTOR_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_SELECTOR_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_policy_selector",
    "locate_surface_policy_selector_plan_source",
    "locate_surface_policy_selector_replay_source",
    "read_json_report",
    "resolve_exit_code",
]
