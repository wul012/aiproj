from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    GenerateFunc,
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code as _profile_replay_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_direct_completion_route_comparison import (
    PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path, utc_now


PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.json"
)
PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.csv"
)
PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.txt"
)
PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.md"
)
PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay.html"
)

PAIR_PROBE_PROMPT_SPECS = (
    {"spec_id": "exact-heldout-pair", "prompt": HELDOUT_PAIR_PROBE, "required_for_ready": True},
    {"spec_id": "spaced-heldout-pair", "prompt": "fixed= | loss=", "required_for_ready": False},
    {"spec_id": "arrow-heldout-pair", "prompt": "fixed -> | loss ->", "required_for_ready": False},
)


def locate_direct_completion_pair_probe_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_DIRECT_COMPLETION_ROUTE_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("direct-completion pair-probe replay input must be a JSON object")
    return dict(payload)


def build_direct_completion_pair_probe_replay(
    route_comparison: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    prompt_specs: tuple[dict[str, Any], ...] = PAIR_PROBE_PROMPT_SPECS,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    selected_training_report: dict[str, Any] | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    selected = _selected_row(route_comparison)
    issues = _input_issues(route_comparison, selected, prompt_specs)
    selected_path = _selected_path(selected, source_path)
    training_report = selected_training_report or _read_training_report(selected_path, issues)
    training = as_dict(training_report.get("training"))
    settings = as_dict(training_report.get("settings"))
    replay_rows: list[dict[str, Any]] = []
    replay_reports: list[dict[str, Any]] = []
    if not issues:
        for spec in prompt_specs:
            replay = build_model_capability_required_term_pair_generation_profile_replay(
                _source_report_for_pair_prompt(training, settings, spec),
                out_dir=root / "pair-probe-replay-runs" / str(spec["spec_id"]),
                source_path=selected_path,
                profiles=profiles,
                variant_limit=1,
                max_new_tokens=int(settings.get("max_new_tokens") or 12),
                temperature=float(settings.get("temperature") or 0.2),
                top_k=int(settings.get("top_k") or 1),
                device=device,
                generated_at=generated_at,
                generate_func=generate_func,
            )
            replay_reports.append({"spec_id": spec["spec_id"], "report": replay})
            replay_rows.append(_replay_row(spec, replay))
            if replay.get("status") != "pass":
                issues.append(f"pair-probe replay failed for {spec['spec_id']}")
    summary = _summary(replay_rows, prompt_specs)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness direct-completion pair-probe replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_route_comparison": "" if source_path is None else str(source_path),
        "selected_training_report": str(selected_path or ""),
        "out_dir": str(root),
        "settings": {
            "prompt_specs": list(prompt_specs),
            "profiles": list(profiles),
            "device": device,
            "experiment_boundary": "replay the selected direct-completion checkpoint on heldout pair prompt surfaces without retraining",
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
        if child and _profile_replay_exit_code(child, require_pass=require_pass):
            return 1
    return 0


def _selected_row(route_comparison: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(route_comparison.get("summary"))
    selected_label = str(summary.get("selected_route") or "direct-completion-surface")
    for row in list_of_dicts(route_comparison.get("comparison_rows")):
        if row.get("label") == selected_label:
            return row
    return {}


def _input_issues(route_comparison: dict[str, Any], selected: dict[str, Any], prompt_specs: tuple[dict[str, Any], ...]) -> list[str]:
    issues: list[str] = []
    summary = as_dict(route_comparison.get("summary"))
    if route_comparison.get("status") != "pass":
        issues.append("route comparison status is not pass")
    if route_comparison.get("decision") != "pair_readiness_direct_completion_route_candidate_found":
        issues.append("route comparison did not select a direct-completion candidate")
    if summary.get("selected_route") != "direct-completion-surface":
        issues.append("selected route is not direct-completion-surface")
    if not selected:
        issues.append("selected comparison row is missing")
    elif not selected.get("path"):
        issues.append("selected comparison row has no training-report path")
    if not prompt_specs:
        issues.append("pair-probe prompt specs are empty")
    return issues


def _selected_path(selected: dict[str, Any], source_path: str | Path | None) -> Path | None:
    raw_path = selected.get("path")
    if not raw_path:
        return None
    base_dir = Path(source_path).parent if source_path is not None else Path.cwd()
    return resolve_archived_reference_path(raw_path, base_dir=base_dir)


def _read_training_report(path: Path | None, issues: list[str]) -> dict[str, Any]:
    if path is None:
        return {}
    if not path.is_file():
        issues.append(f"selected training report is missing: {path}")
        return {}
    return read_json_report(path)


def _source_report_for_pair_prompt(training: dict[str, Any], settings: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    seed = int(settings.get("seed") or 0)
    variant_id = f"pair-probe-{spec['spec_id']}-seed-{seed}"
    prompt = str(spec.get("prompt") or HELDOUT_PAIR_PROBE)
    return {
        "targets": [
            {
                "pair_id": "01-fixed-loss",
                "terms": [
                    {"case": f"{spec['spec_id']}-fixed", "term": "fixed", "scaffold_prompt": prompt, "source_hit_rate": 0.0},
                    {"case": f"{spec['spec_id']}-loss", "term": "loss", "scaffold_prompt": prompt, "source_hit_rate": 0.0},
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


def _replay_row(spec: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    default_full = int(summary.get("default_pair_full_variant_count") or 0)
    suppression_full = int(summary.get("suppression_pair_full_variant_count") or 0)
    return {
        "spec_id": spec.get("spec_id"),
        "prompt": spec.get("prompt"),
        "required_for_ready": bool(spec.get("required_for_ready")),
        "status": replay.get("status"),
        "replay_decision": replay.get("decision"),
        "replay_pair_full": max(default_full, suppression_full) > 0,
        "default_pair_full_variant_count": default_full,
        "suppression_pair_full_variant_count": suppression_full,
        "default_continuation_hit_count": summary.get("default_continuation_hit_count", 0),
        "suppression_continuation_hit_count": summary.get("suppression_continuation_hit_count", 0),
    }


def _summary(rows: list[dict[str, Any]], prompt_specs: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    required_ids = {str(spec.get("spec_id")) for spec in prompt_specs if spec.get("required_for_ready")}
    required_rows = [row for row in rows if str(row.get("spec_id")) in required_ids]
    pair_full_count = sum(1 for row in rows if row.get("replay_pair_full"))
    required_pair_full_count = sum(1 for row in required_rows if row.get("replay_pair_full"))
    return {
        "row_count": len(rows),
        "prompt_spec_count": len(prompt_specs),
        "required_prompt_spec_count": len(required_ids),
        "pair_full_count": pair_full_count,
        "pair_full_rate": round(pair_full_count / len(rows), 4) if rows else 0.0,
        "required_pair_full_count": required_pair_full_count,
        "required_all_pair_full": bool(required_rows) and required_pair_full_count == len(required_rows),
        "any_pair_full": pair_full_count > 0,
        "exact_heldout_pair_full": any(row.get("spec_id") == "exact-heldout-pair" and row.get("replay_pair_full") for row in rows),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_direct_completion_pair_probe_replay"
    if summary.get("required_all_pair_full"):
        return "pair_readiness_direct_completion_pair_probe_replay_ready"
    if summary.get("any_pair_full"):
        return "pair_readiness_direct_completion_pair_probe_replay_partial"
    return "pair_readiness_direct_completion_pair_probe_replay_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The selected direct-completion route could not be replayed on heldout pair probes.",
            "next_action": "repair selected route paths or checkpoint artifacts before promotion checks",
        }
    if summary.get("required_all_pair_full"):
        return {
            "model_quality_claim": "pair_probe_replay_ready",
            "reason": "The exact heldout pair probe replayed pair-full on the selected direct-completion checkpoint.",
            "next_action": "run stricter promotion guard and seed-stability checks before accepting the route",
        }
    if summary.get("any_pair_full"):
        return {
            "model_quality_claim": "pair_probe_replay_partial",
            "reason": "At least one pair prompt surface replayed pair-full, but the required exact heldout pair probe did not fully pass.",
            "next_action": "diagnose pair prompt transfer before promotion",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The selected direct-completion checkpoint did not replay pair-full on pair prompt surfaces.",
        "next_action": "treat v738 as direct-probe-only evidence and repair pair prompt transfer",
    }


__all__ = [
    "PAIR_PROBE_PROMPT_SPECS",
    "PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_CSV_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_HTML_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_TEXT_FILENAME",
    "build_direct_completion_pair_probe_replay",
    "locate_direct_completion_pair_probe_replay_source",
    "read_json_report",
    "resolve_exit_code",
]
