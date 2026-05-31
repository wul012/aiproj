from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_first_token_route_decision import PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME
from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    GenerateFunc,
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code as _replay_exit_code,
)
from minigpt.model_capability_required_term_pair_seed_config_heldout_replay import DEFAULT_HELDOUT_PROMPT_SPECS
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path, utc_now


PAIR_ROUTE_HELDOUT_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_route_heldout_replay.json"
PAIR_ROUTE_HELDOUT_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_route_heldout_replay.csv"
PAIR_ROUTE_HELDOUT_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_route_heldout_replay.txt"
PAIR_ROUTE_HELDOUT_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_route_heldout_replay.md"
PAIR_ROUTE_HELDOUT_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_route_heldout_replay.html"


def locate_pair_route_decision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route held-out replay input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_route_heldout_replay(
    route_decision: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    prompt_specs: tuple[dict[str, str], ...] = DEFAULT_HELDOUT_PROMPT_SPECS,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    selected_source_report: dict[str, Any] | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    selected = as_dict(route_decision.get("selected_route"))
    issues = _input_issues(route_decision, selected, prompt_specs)
    source_report_path = _selected_source_path(selected, source_path)
    source_report = selected_source_report or _read_source_report(source_report_path, issues)
    seed_reports = _pair_full_seed_reports(source_report)
    if not seed_reports and not issues:
        issues.append("selected source report has no pair-full seed reports")

    replay_rows: list[dict[str, Any]] = []
    replay_reports: list[dict[str, Any]] = []
    if not issues:
        for seed_report in seed_reports:
            seed = int(as_dict(seed_report.get("settings")).get("seed") or 0)
            for spec in prompt_specs:
                replay = build_model_capability_required_term_pair_generation_profile_replay(
                    _source_report_for_prompt_spec(seed_report, spec),
                    out_dir=root / "route-heldout-replay-runs" / str(spec["spec_id"]) / f"seed-{seed}",
                    source_path=seed_report.get("out_dir") or source_report_path,
                    profiles=profiles,
                    variant_limit=1,
                    max_new_tokens=int(as_dict(source_report.get("settings")).get("max_new_tokens") or 12),
                    temperature=float(as_dict(source_report.get("settings")).get("temperature") or 0.8),
                    top_k=int(as_dict(source_report.get("settings")).get("top_k") or 2),
                    device=device,
                    generated_at=generated_at,
                    generate_func=generate_func,
                )
                replay_reports.append({"spec_id": spec["spec_id"], "seed": seed, "report": replay})
                replay_rows.append(_replay_row(selected, source_report, seed_report, spec, replay))
                if replay.get("status") != "pass":
                    issues.append(f"held-out replay failed for {spec['spec_id']} seed {seed}")

    summary = _summary(replay_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair route held-out replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_route_decision": "" if source_path is None else str(source_path),
        "selected_source_report": str(source_report_path or selected.get("source_path") or ""),
        "out_dir": str(root),
        "settings": {
            "prompt_specs": list(prompt_specs),
            "profiles": list(profiles),
            "device": device,
            "experiment_boundary": "replay selected route pair-full seeds on held-out prompt surfaces without retraining",
        },
        "selected_route": selected,
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


def _input_issues(route_decision: dict[str, Any], selected: dict[str, Any], prompt_specs: tuple[dict[str, str], ...]) -> list[str]:
    issues: list[str] = []
    if route_decision.get("status") != "pass":
        issues.append("route decision status is not pass")
    if not selected:
        issues.append("route decision has no selected_route")
    if not selected.get("source_path"):
        issues.append("selected_route has no source_path")
    if not prompt_specs:
        issues.append("held-out prompt specs are empty")
    return issues


def _selected_source_path(selected: dict[str, Any], source_path: str | Path | None) -> Path | None:
    selected_path = selected.get("source_path")
    if not selected_path:
        return None
    base_dir = Path(source_path).parent if source_path is not None else Path.cwd()
    return resolve_archived_reference_path(selected_path, base_dir=base_dir)


def _read_source_report(path: Path | None, issues: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.is_file():
        issues.append(f"selected source report is missing: {path}")
        return {}
    return read_json_report(path)


def _pair_full_seed_reports(source_report: dict[str, Any]) -> list[dict[str, Any]]:
    seed_rows = [row for row in list_of_dicts(source_report.get("seed_rows")) if row.get("pair_full_observed")]
    seed_reports = list_of_dicts(source_report.get("seed_reports"))
    pair_full_seeds = {int(row.get("seed") or 0) for row in seed_rows}
    return [report for report in seed_reports if int(as_dict(report.get("settings")).get("seed") or 0) in pair_full_seeds]


def _source_report_for_prompt_spec(seed_report: dict[str, Any], spec: dict[str, str]) -> dict[str, Any]:
    seed = int(as_dict(seed_report.get("settings")).get("seed") or 0)
    training = as_dict(seed_report.get("training"))
    variant_id = f"route-heldout-{spec['spec_id']}-seed-{seed}"
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {"case": f"{spec['spec_id']}-fixed", "term": "fixed", "scaffold_prompt": spec["fixed_prompt"], "source_hit_rate": 0.0},
                    {"case": f"{spec['spec_id']}-loss", "term": "loss", "scaffold_prompt": spec["loss_prompt"], "source_hit_rate": 0.0},
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


def _replay_row(
    selected: dict[str, Any],
    source_report: dict[str, Any],
    seed_report: dict[str, Any],
    spec: dict[str, str],
    replay: dict[str, Any],
) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    pair_full_count = max(int(summary.get("default_pair_full_variant_count") or 0), int(summary.get("suppression_pair_full_variant_count") or 0))
    settings = as_dict(source_report.get("settings"))
    seed = int(as_dict(seed_report.get("settings")).get("seed") or 0)
    return {
        "spec_id": spec.get("spec_id"),
        "seed": seed,
        "selected_source_label": selected.get("source_label"),
        "corpus_mode": selected.get("corpus_mode"),
        "status": replay.get("status"),
        "replay_decision": replay.get("decision"),
        "fixed_prompt": spec.get("fixed_prompt"),
        "loss_prompt": spec.get("loss_prompt"),
        "replay_pair_full": pair_full_count > 0,
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count", 0),
        "top_k": settings.get("top_k"),
        "temperature": settings.get("temperature"),
        "seed_report_out_dir": seed_report.get("out_dir", ""),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    pair_full_count = sum(1 for row in rows if row.get("replay_pair_full"))
    return {
        "row_count": row_count,
        "seed_count": len({row.get("seed") for row in rows}),
        "heldout_spec_count": len({row.get("spec_id") for row in rows}),
        "heldout_pair_full_count": pair_full_count,
        "heldout_pair_full_rate": round(pair_full_count / row_count, 4) if row_count else 0.0,
        "heldout_all_pair_full": bool(rows) and pair_full_count == row_count,
        "heldout_any_pair_full": pair_full_count > 0,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_route_heldout_replay"
    if summary.get("heldout_all_pair_full"):
        return "required_term_pair_route_heldout_replay_ready"
    if summary.get("heldout_any_pair_full"):
        return "required_term_pair_route_heldout_replay_partial"
    return "required_term_pair_route_heldout_replay_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one selected route held-out replay could not execute."
        next_action = "repair selected route source paths before judging held-out prompt transfer"
        claim = "not_claimed"
    elif summary.get("heldout_all_pair_full"):
        reason = "Every selected route pair-full seed also replayed pair-full coverage across held-out prompt surfaces."
        next_action = "test a fresh seed or larger prompt suite before raising the capability claim"
        claim = "targeted_route_heldout_ready"
    elif summary.get("heldout_any_pair_full"):
        reason = "Some held-out prompt surfaces replayed pair-full coverage, but the selected route is not broadly robust."
        next_action = "diagnose which prompt surfaces transfer before training another objective"
        claim = "targeted_route_heldout_partial"
    else:
        reason = "No held-out prompt surface replayed pair-full coverage for the selected route."
        next_action = "treat the selected route as source-prompt memorization and repair prompt generalization"
        claim = "not_claimed"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


__all__ = [
    "PAIR_ROUTE_HELDOUT_REPLAY_CSV_FILENAME",
    "PAIR_ROUTE_HELDOUT_REPLAY_HTML_FILENAME",
    "PAIR_ROUTE_HELDOUT_REPLAY_JSON_FILENAME",
    "PAIR_ROUTE_HELDOUT_REPLAY_MARKDOWN_FILENAME",
    "PAIR_ROUTE_HELDOUT_REPLAY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_route_heldout_replay",
    "locate_pair_route_decision",
    "read_json_report",
    "resolve_exit_code",
]
