from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    GenerateFunc,
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code as _replay_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_selection import (
    PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_SEED_CONFIG_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_seed_config_replay.json"
PAIR_SEED_CONFIG_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_seed_config_replay.csv"
PAIR_SEED_CONFIG_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_seed_config_replay.txt"
PAIR_SEED_CONFIG_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_seed_config_replay.md"
PAIR_SEED_CONFIG_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_seed_config_replay.html"


def locate_pair_seed_config_selection(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("seed config selection report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_seed_config_replay(
    selection_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    source_reports_by_config: dict[str, dict[str, Any]] | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    selection_rows = list_of_dicts(selection_report.get("selection_rows"))
    config_rows = list_of_dicts(selection_report.get("config_rows"))
    issues = _input_issues(selection_report, selection_rows, config_rows)
    config_map = {str(row.get("config_id")): row for row in config_rows if row.get("config_id")}
    replay_rows: list[dict[str, Any]] = []
    replay_reports: list[dict[str, Any]] = []
    sources = source_reports_by_config or {}

    if not issues:
        for selection in selection_rows:
            seed = int(selection.get("seed") or 0)
            config_id = str(selection.get("selected_config_id") or "")
            config = config_map.get(config_id)
            source_report = sources.get(config_id) or _read_source_report(config)
            seed_report = _seed_report_for_seed(source_report, seed) if source_report else {}
            if not source_report:
                issues.append(f"missing source report for config {config_id}")
                replay_rows.append(_missing_row(selection, config_id, "missing_source_report"))
                continue
            if not seed_report:
                issues.append(f"missing seed report for config {config_id} seed {seed}")
                replay_rows.append(_missing_row(selection, config_id, "missing_seed_report"))
                continue
            replay = build_model_capability_required_term_pair_generation_profile_replay(
                _source_report_for_seed(selection, seed_report),
                out_dir=root / "selected-replay-runs" / config_id / f"seed-{seed}",
                source_path=seed_report.get("out_dir") or as_dict(config).get("source_path"),
                profiles=profiles,
                variant_limit=1,
                max_new_tokens=int(as_dict(source_report.get("settings")).get("max_new_tokens") or 12),
                temperature=float(as_dict(source_report.get("settings")).get("temperature") or 0.2),
                top_k=int(as_dict(source_report.get("settings")).get("top_k") or 1),
                device=device,
                generated_at=generated_at,
                generate_func=generate_func,
            )
            replay_reports.append({"config_id": config_id, "seed": seed, "report": replay})
            replay_rows.append(_replay_row(selection, config_id, config, source_report, replay))
            if replay.get("status") != "pass":
                issues.append(f"selected replay failed for config {config_id} seed {seed}")

    summary = _summary(replay_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair seed config replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_config_selection": "" if source_path is None else str(source_path),
        "out_dir": str(root),
        "settings": {
            "profiles": list(profiles),
            "device": device,
            "experiment_boundary": "replay selected per-seed configs from the policy without retraining",
        },
        "replay_rows": replay_rows,
        "replay_reports": replay_reports,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    for entry in list_of_dicts(report.get("replay_reports")):
        child = as_dict(entry.get("report"))
        if child and _replay_exit_code(child, require_pass=require_pass):
            return 1
    return 0


def _input_issues(
    selection_report: dict[str, Any],
    selection_rows: list[dict[str, Any]],
    config_rows: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if selection_report.get("status") != "pass":
        issues.append("seed config selection report status is not pass")
    if not selection_rows:
        issues.append("seed config selection report has no selection_rows")
    if not config_rows:
        issues.append("seed config selection report has no config_rows")
    return issues


def _read_source_report(config: dict[str, Any] | None) -> dict[str, Any]:
    source = as_dict(config).get("source_path")
    if not source or not Path(str(source)).is_file():
        return {}
    payload = json.loads(Path(str(source)).read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def _seed_report_for_seed(source_report: dict[str, Any], seed: int) -> dict[str, Any]:
    for report in list_of_dicts(source_report.get("seed_reports")):
        if int(as_dict(report.get("settings")).get("seed") or 0) == seed:
            return report
    return {}


def _source_report_for_seed(selection: dict[str, Any], seed_report: dict[str, Any]) -> dict[str, Any]:
    seed = int(selection.get("seed") or as_dict(seed_report.get("settings")).get("seed") or 0)
    training = as_dict(seed_report.get("training"))
    variant_id = f"selected-seed-{seed}"
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {"case": "comparison-baseline", "term": "fixed", "scaffold_prompt": "fixed:", "source_hit_rate": 1.0},
                    {"case": "factual-val-loss", "term": "loss", "scaffold_prompt": "loss:", "source_hit_rate": 1.0},
                ],
            }
        ],
        "training_rows": [
            {
                "branch_retention_run_id": variant_id,
                "pair_id": "01-fixed-loss",
                "variant_id": variant_id,
                "seed": seed,
                "checkpoint_path": training.get("checkpoint_path"),
                "tokenizer_path": training.get("tokenizer_path"),
            }
        ],
        "probe_rows": [
            {"variant_id": variant_id, "term": "fixed", "generation_seed": seed},
            {"variant_id": variant_id, "term": "loss", "generation_seed": seed + 1},
        ],
    }


def _missing_row(selection: dict[str, Any], config_id: str, reason: str) -> dict[str, Any]:
    return {
        "seed": selection.get("seed"),
        "selected_config_id": config_id,
        "status": "fail",
        "reason": reason,
        "policy_selection_ready": bool(selection.get("selection_ready")),
        "policy_selected_pair_full": bool(selection.get("selected_pair_full")),
        "replay_pair_full": False,
    }


def _replay_row(
    selection: dict[str, Any],
    config_id: str,
    config: dict[str, Any] | None,
    source_report: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    pair_full_count = max(
        int(summary.get("default_pair_full_variant_count") or 0),
        int(summary.get("suppression_pair_full_variant_count") or 0),
    )
    settings = as_dict(source_report.get("settings"))
    return {
        "seed": selection.get("seed"),
        "selected_config_id": config_id,
        "status": replay.get("status"),
        "replay_decision": replay.get("decision"),
        "policy_selection_ready": bool(selection.get("selection_ready")),
        "policy_selected_pair_full": bool(selection.get("selected_pair_full")),
        "replay_pair_full": pair_full_count > 0,
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count", 0),
        "top_k": settings.get("top_k"),
        "temperature": settings.get("temperature"),
        "source_path": as_dict(config).get("source_path", ""),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(rows)
    replay_pair_full_count = sum(1 for row in rows if row.get("replay_pair_full"))
    policy_ready_count = sum(1 for row in rows if row.get("policy_selection_ready"))
    return {
        "seed_count": seed_count,
        "policy_selection_ready_seed_count": policy_ready_count,
        "replay_pair_full_seed_count": replay_pair_full_count,
        "replay_pair_full_seed_rate": round(replay_pair_full_count / seed_count, 4) if seed_count else 0.0,
        "selected_replay_ready": bool(rows) and replay_pair_full_count == seed_count,
        "policy_replay_gap_count": sum(
            1 for row in rows if row.get("policy_selected_pair_full") and not row.get("replay_pair_full")
        ),
        "selected_config_ids": sorted({str(row.get("selected_config_id")) for row in rows if row.get("selected_config_id")}),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_seed_config_replay"
    if summary.get("selected_replay_ready"):
        return "required_term_pair_seed_config_replay_ready"
    if summary.get("replay_pair_full_seed_count"):
        return "required_term_pair_seed_config_replay_partial"
    return "required_term_pair_seed_config_replay_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one selected config replay could not execute."
        next_action = "repair selected source reports or checkpoint paths before testing held-out prompts"
        claim = "not_claimed"
    elif summary.get("selected_replay_ready"):
        reason = "Every selected per-seed config replayed pair-full coverage from its source checkpoint."
        next_action = "test selected configs against held-out prompt variants or fresh seeds"
        claim = "targeted_seed_config_replay_ready"
    elif summary.get("replay_pair_full_seed_count"):
        reason = "Only part of the selected policy replayed pair-full coverage."
        next_action = "inspect policy replay gaps before claiming config-selection readiness"
        claim = "targeted_seed_config_replay_partial"
    else:
        reason = "No selected config replayed pair-full coverage."
        next_action = "return to selected source reports before extending policy checks"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_SEED_CONFIG_REPLAY_CSV_FILENAME",
    "PAIR_SEED_CONFIG_REPLAY_HTML_FILENAME",
    "PAIR_SEED_CONFIG_REPLAY_JSON_FILENAME",
    "PAIR_SEED_CONFIG_REPLAY_MARKDOWN_FILENAME",
    "PAIR_SEED_CONFIG_REPLAY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_seed_config_replay",
    "locate_pair_seed_config_selection",
    "read_json_report",
    "resolve_exit_code",
]
