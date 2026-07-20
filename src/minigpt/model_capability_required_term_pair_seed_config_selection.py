from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_seed_coverage_tradeoff import (
    PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME = "model_capability_required_term_pair_seed_config_selection.json"
PAIR_SEED_CONFIG_SELECTION_CSV_FILENAME = "model_capability_required_term_pair_seed_config_selection.csv"
PAIR_SEED_CONFIG_SELECTION_TEXT_FILENAME = "model_capability_required_term_pair_seed_config_selection.txt"
PAIR_SEED_CONFIG_SELECTION_MARKDOWN_FILENAME = "model_capability_required_term_pair_seed_config_selection.md"
PAIR_SEED_CONFIG_SELECTION_HTML_FILENAME = "model_capability_required_term_pair_seed_config_selection.html"


def locate_pair_seed_coverage_tradeoff(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("seed coverage tradeoff report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_seed_config_selection(
    tradeoff_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    seed_rows = list_of_dicts(tradeoff_report.get("seed_rows"))
    config_rows = list_of_dicts(tradeoff_report.get("config_rows"))
    issues = _input_issues(tradeoff_report, seed_rows, config_rows)
    selections = [_selection_row(row) for row in seed_rows] if not issues else []
    issues.extend(_selection_issues(selections))
    summary = _summary(selections, config_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair seed config selection",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_coverage_tradeoff": "" if source_path is None else str(source_path),
        "out_dir": str(root),
        "settings": {
            "selection_strategy": "first_covering_config_per_seed",
            "experiment_boundary": "derive a deterministic per-seed config policy from coverage tradeoff evidence",
        },
        "config_rows": _policy_config_rows(config_rows, selections),
        "selection_rows": selections,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _input_issues(
    tradeoff_report: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    config_rows: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if tradeoff_report.get("status") != "pass":
        issues.append("seed coverage tradeoff report status is not pass")
    if not seed_rows:
        issues.append("seed coverage tradeoff report has no seed_rows")
    if not config_rows:
        issues.append("seed coverage tradeoff report has no config_rows")
    return issues


def _selection_row(seed_row: dict[str, Any]) -> dict[str, Any]:
    per_config = as_dict(seed_row.get("per_config_pair_full"))
    covering_configs = [str(item) for item in seed_row.get("covering_config_ids", [])]
    selected = str(seed_row.get("winning_config_id") or (covering_configs[0] if covering_configs else ""))
    selected_pair_full = bool(per_config.get(selected)) if selected else False
    return {
        "seed": seed_row.get("seed"),
        "selected_config_id": selected,
        "selection_ready": bool(selected and selected_pair_full),
        "selected_pair_full": selected_pair_full,
        "covering_config_ids": covering_configs,
        "covering_config_count": len(covering_configs),
        "fallback_required": len(covering_configs) == 1,
        "per_config_pair_full": per_config,
    }


def _selection_issues(rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for row in rows:
        if not row.get("selection_ready"):
            issues.append(f"seed {row.get('seed')} has no pair-full selected config")
    return issues


def _policy_config_rows(config_rows: list[dict[str, Any]], selections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected_counts: dict[str, int] = {}
    for row in selections:
        config_id = str(row.get("selected_config_id") or "")
        if config_id:
            selected_counts[config_id] = selected_counts.get(config_id, 0) + 1
    return [
        {
            "config_id": row.get("config_id"),
            "source_path": row.get("source_path"),
            "pair_full_seed_count": row.get("pair_full_seed_count"),
            "selected_seed_count": selected_counts.get(str(row.get("config_id")), 0),
            "corpus_mode": row.get("corpus_mode"),
            "top_k": row.get("top_k"),
            "temperature": row.get("temperature"),
        }
        for row in config_rows
    ]


def _summary(selections: list[dict[str, Any]], config_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(selections)
    selected_count = sum(1 for row in selections if row.get("selection_ready"))
    selected_config_ids = sorted({str(row.get("selected_config_id")) for row in selections if row.get("selected_config_id")})
    return {
        "seed_count": seed_count,
        "selection_ready_seed_count": selected_count,
        "selection_ready_seed_rate": round(selected_count / seed_count, 4) if seed_count else 0.0,
        "all_seeds_selection_ready": bool(selections) and selected_count == seed_count,
        "selected_config_ids": selected_config_ids,
        "selected_config_count": len(selected_config_ids),
        "source_config_count": len(config_rows),
        "requires_multi_config_policy": len(selected_config_ids) > 1,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_seed_config_selection"
    if summary.get("all_seeds_selection_ready") and summary.get("requires_multi_config_policy"):
        return "required_term_pair_seed_config_selection_multi_config_ready"
    if summary.get("all_seeds_selection_ready"):
        return "required_term_pair_seed_config_selection_single_config_ready"
    return "required_term_pair_seed_config_selection_partial"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one seed has no verified pair-full selected config."
        next_action = "repair coverage tradeoff inputs before testing a fallback policy"
        claim = "not_claimed"
    elif summary.get("requires_multi_config_policy"):
        reason = "Every seed has a verified selected config, and more than one config is needed."
        next_action = "test this explicit config-selection policy against held-out prompts or fresh seeds"
        claim = "targeted_seed_config_selection_ready"
    else:
        reason = "Every seed can use a single selected config."
        next_action = "promote the selected config to held-out evaluation"
        claim = "targeted_pair_refresh_stable_signal"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_SEED_CONFIG_SELECTION_CSV_FILENAME",
    "PAIR_SEED_CONFIG_SELECTION_HTML_FILENAME",
    "PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME",
    "PAIR_SEED_CONFIG_SELECTION_MARKDOWN_FILENAME",
    "PAIR_SEED_CONFIG_SELECTION_TEXT_FILENAME",
    "build_model_capability_required_term_pair_seed_config_selection",
    "locate_pair_seed_coverage_tradeoff",
    "read_json_report",
    "resolve_exit_code",
]
