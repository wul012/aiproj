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
from minigpt.model_capability_required_term_pair_seed_config_replay import (
    _read_source_report,
    _seed_report_for_seed,
)
from minigpt.model_capability_required_term_pair_seed_config_selection import (
    PAIR_SEED_CONFIG_SELECTION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_SEED_CONFIG_HELDOUT_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_seed_config_heldout_replay.json"
PAIR_SEED_CONFIG_HELDOUT_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_seed_config_heldout_replay.csv"
PAIR_SEED_CONFIG_HELDOUT_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_seed_config_heldout_replay.txt"
PAIR_SEED_CONFIG_HELDOUT_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_seed_config_heldout_replay.md"
PAIR_SEED_CONFIG_HELDOUT_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_seed_config_heldout_replay.html"

DEFAULT_HELDOUT_PROMPT_SPECS = (
    {"spec_id": "colon-spaced", "fixed_prompt": "fixed: ", "loss_prompt": "loss: "},
    {"spec_id": "equals", "fixed_prompt": "fixed=", "loss_prompt": "loss="},
    {"spec_id": "arrow", "fixed_prompt": "fixed -> ", "loss_prompt": "loss -> "},
)


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


def build_model_capability_required_term_pair_seed_config_heldout_replay(
    selection_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    prompt_specs: tuple[dict[str, str], ...] = DEFAULT_HELDOUT_PROMPT_SPECS,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    source_reports_by_config: dict[str, dict[str, Any]] | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    selection_rows = list_of_dicts(selection_report.get("selection_rows"))
    config_rows = list_of_dicts(selection_report.get("config_rows"))
    issues = _input_issues(selection_report, selection_rows, config_rows, prompt_specs)
    config_map = {str(row.get("config_id")): row for row in config_rows if row.get("config_id")}
    sources = source_reports_by_config or {}
    replay_rows: list[dict[str, Any]] = []
    replay_reports: list[dict[str, Any]] = []

    if not issues:
        for selection in selection_rows:
            seed = int(selection.get("seed") or 0)
            config_id = str(selection.get("selected_config_id") or "")
            config = config_map.get(config_id)
            source_report = sources.get(config_id) or _read_source_report(config)
            seed_report = _seed_report_for_seed(source_report, seed) if source_report else {}
            if not source_report or not seed_report:
                issues.append(f"missing selected source for config {config_id} seed {seed}")
                replay_rows.extend(_missing_rows(selection, config_id, prompt_specs))
                continue
            for spec in prompt_specs:
                replay = build_model_capability_required_term_pair_generation_profile_replay(
                    _source_report_for_prompt_spec(selection, seed_report, spec),
                    out_dir=root / "heldout-replay-runs" / str(spec["spec_id"]) / config_id / f"seed-{seed}",
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
                replay_reports.append({"spec_id": spec["spec_id"], "config_id": config_id, "seed": seed, "report": replay})
                replay_rows.append(_replay_row(selection, config_id, config, source_report, spec, replay))
                if replay.get("status") != "pass":
                    issues.append(f"held-out replay failed for {spec['spec_id']} config {config_id} seed {seed}")

    summary = _summary(replay_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair seed config held-out replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_config_selection": "" if source_path is None else str(source_path),
        "out_dir": str(root),
        "settings": {
            "prompt_specs": list(prompt_specs),
            "profiles": list(profiles),
            "device": device,
            "experiment_boundary": "test selected configs on held-out prompt surfaces without retraining",
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
    prompt_specs: tuple[dict[str, str], ...],
) -> list[str]:
    issues: list[str] = []
    if selection_report.get("status") != "pass":
        issues.append("seed config selection report status is not pass")
    if not selection_rows:
        issues.append("seed config selection report has no selection_rows")
    if not config_rows:
        issues.append("seed config selection report has no config_rows")
    if not prompt_specs:
        issues.append("held-out prompt specs are empty")
    return issues


def _source_report_for_prompt_spec(
    selection: dict[str, Any],
    seed_report: dict[str, Any],
    spec: dict[str, str],
) -> dict[str, Any]:
    seed = int(selection.get("seed") or as_dict(seed_report.get("settings")).get("seed") or 0)
    training = as_dict(seed_report.get("training"))
    variant_id = f"heldout-{spec['spec_id']}-seed-{seed}"
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {
                        "case": f"{spec['spec_id']}-fixed",
                        "term": "fixed",
                        "scaffold_prompt": spec["fixed_prompt"],
                        "source_hit_rate": 0.0,
                    },
                    {
                        "case": f"{spec['spec_id']}-loss",
                        "term": "loss",
                        "scaffold_prompt": spec["loss_prompt"],
                        "source_hit_rate": 0.0,
                    },
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


def _missing_rows(
    selection: dict[str, Any],
    config_id: str,
    prompt_specs: tuple[dict[str, str], ...],
) -> list[dict[str, Any]]:
    return [
        {
            "spec_id": spec.get("spec_id"),
            "seed": selection.get("seed"),
            "selected_config_id": config_id,
            "status": "fail",
            "replay_pair_full": False,
            "reason": "missing_selected_source",
        }
        for spec in prompt_specs
    ]


def _replay_row(
    selection: dict[str, Any],
    config_id: str,
    config: dict[str, Any] | None,
    source_report: dict[str, Any],
    spec: dict[str, str],
    replay: dict[str, Any],
) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    pair_full_count = max(
        int(summary.get("default_pair_full_variant_count") or 0),
        int(summary.get("suppression_pair_full_variant_count") or 0),
    )
    settings = as_dict(source_report.get("settings"))
    return {
        "spec_id": spec.get("spec_id"),
        "seed": selection.get("seed"),
        "selected_config_id": config_id,
        "status": replay.get("status"),
        "replay_decision": replay.get("decision"),
        "fixed_prompt": spec.get("fixed_prompt"),
        "loss_prompt": spec.get("loss_prompt"),
        "replay_pair_full": pair_full_count > 0,
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count", 0),
        "top_k": settings.get("top_k"),
        "temperature": settings.get("temperature"),
        "source_path": as_dict(config).get("source_path", ""),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    pair_full_count = sum(1 for row in rows if row.get("replay_pair_full"))
    spec_rows = []
    for spec_id in sorted({str(row.get("spec_id")) for row in rows}):
        scoped = [row for row in rows if row.get("spec_id") == spec_id]
        spec_rows.append(
            {
                "spec_id": spec_id,
                "row_count": len(scoped),
                "pair_full_count": sum(1 for row in scoped if row.get("replay_pair_full")),
            }
        )
    return {
        "row_count": row_count,
        "seed_count": len({row.get("seed") for row in rows}),
        "heldout_spec_count": len(spec_rows),
        "heldout_pair_full_count": pair_full_count,
        "heldout_pair_full_rate": round(pair_full_count / row_count, 4) if row_count else 0.0,
        "heldout_all_pair_full": bool(rows) and pair_full_count == row_count,
        "heldout_any_pair_full": pair_full_count > 0,
        "spec_rows": spec_rows,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_seed_config_heldout_replay"
    if summary.get("heldout_all_pair_full"):
        return "required_term_pair_seed_config_heldout_replay_ready"
    if summary.get("heldout_any_pair_full"):
        return "required_term_pair_seed_config_heldout_replay_partial"
    return "required_term_pair_seed_config_heldout_replay_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one held-out selected config replay could not execute."
        next_action = "repair selected source paths before judging held-out prompt transfer"
        claim = "not_claimed"
    elif summary.get("heldout_all_pair_full"):
        reason = "Every selected config also replayed pair-full coverage across held-out prompt surfaces."
        next_action = "test fresh seeds or a larger corpus before raising the capability claim"
        claim = "targeted_seed_config_heldout_ready"
    elif summary.get("heldout_any_pair_full"):
        reason = "Some selected config held-out prompt surfaces replayed pair-full coverage, but the policy is not broadly robust."
        next_action = "inspect which prompt surfaces transfer before adding more training variants"
        claim = "targeted_seed_config_heldout_partial"
    else:
        reason = "No selected config replayed pair-full coverage on held-out prompt surfaces."
        next_action = "treat the policy as memorized prompt-shape coverage and repair prompt generalization"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "DEFAULT_HELDOUT_PROMPT_SPECS",
    "PAIR_SEED_CONFIG_HELDOUT_REPLAY_CSV_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_REPLAY_HTML_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_REPLAY_JSON_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_REPLAY_MARKDOWN_FILENAME",
    "PAIR_SEED_CONFIG_HELDOUT_REPLAY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_seed_config_heldout_replay",
    "locate_pair_seed_config_selection",
    "read_json_report",
    "resolve_exit_code",
]
