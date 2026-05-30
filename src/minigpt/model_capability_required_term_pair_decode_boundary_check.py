from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_colon_immediate_stability import (
    PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    DEFAULT_PROFILE_IDS,
    GenerateFunc,
    build_model_capability_required_term_pair_generation_profile_replay,
    resolve_exit_code as _replay_exit_code,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_DECODE_BOUNDARY_CHECK_JSON_FILENAME = "model_capability_required_term_pair_decode_boundary_check.json"
PAIR_DECODE_BOUNDARY_CHECK_CSV_FILENAME = "model_capability_required_term_pair_decode_boundary_check.csv"
PAIR_DECODE_BOUNDARY_CHECK_TEXT_FILENAME = "model_capability_required_term_pair_decode_boundary_check.txt"
PAIR_DECODE_BOUNDARY_CHECK_MARKDOWN_FILENAME = "model_capability_required_term_pair_decode_boundary_check.md"
PAIR_DECODE_BOUNDARY_CHECK_HTML_FILENAME = "model_capability_required_term_pair_decode_boundary_check.html"

DEFAULT_DECODE_SPECS = (
    {"spec_id": "greedy-k1-t020-n12", "top_k": 1, "temperature": 0.2, "max_new_tokens": 12},
    {"spec_id": "wider-k2-t020-n12", "top_k": 2, "temperature": 0.2, "max_new_tokens": 12},
    {"spec_id": "wider-k4-t020-n12", "top_k": 4, "temperature": 0.2, "max_new_tokens": 12},
    {"spec_id": "greedy-k1-t020-n20", "top_k": 1, "temperature": 0.2, "max_new_tokens": 20},
)


def locate_pair_colon_immediate_stability(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("colon-immediate stability report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_decode_boundary_check(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    decode_specs: tuple[dict[str, Any], ...] = DEFAULT_DECODE_SPECS,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    seed_rows = list_of_dicts(stability_report.get("seed_rows"))
    seed_reports = _seed_reports_by_seed(stability_report)
    issues = _input_issues(stability_report, seed_rows, seed_reports, decode_specs)
    rows: list[dict[str, Any]] = []
    replay_reports: list[dict[str, Any]] = []

    if not issues:
        for spec in decode_specs:
            for seed_row in seed_rows:
                seed = int(seed_row.get("seed") or 0)
                seed_report = seed_reports.get(seed)
                if seed_report is None:
                    issues.append(f"missing seed report for seed {seed}")
                    continue
                replay = build_model_capability_required_term_pair_generation_profile_replay(
                    _source_report_for_seed(seed_row, seed_report),
                    out_dir=root / "replay-runs" / str(spec["spec_id"]) / f"seed-{seed}",
                    profiles=profiles,
                    variant_limit=1,
                    max_new_tokens=int(spec["max_new_tokens"]),
                    temperature=float(spec["temperature"]),
                    top_k=int(spec["top_k"]),
                    device=device,
                    generated_at=generated_at,
                    generate_func=generate_func,
                )
                replay_reports.append({"spec_id": spec["spec_id"], "seed": seed, "report": replay})
                rows.append(_row(seed_row, spec, replay))
                if replay.get("status") != "pass":
                    issues.append(f"decode replay failed for {spec['spec_id']} seed {seed}")

    summary = _summary(rows, stability_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair decode boundary check",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_colon_immediate_stability": "" if source_path is None else str(source_path),
        "out_dir": str(root),
        "settings": {
            "decode_specs": list(decode_specs),
            "profiles": list(profiles),
            "device": device,
            "experiment_boundary": "rerun fixed/loss replay under decode boundaries without retraining",
        },
        "rows": rows,
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


def _seed_reports_by_seed(stability_report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    reports: dict[int, dict[str, Any]] = {}
    for report in list_of_dicts(stability_report.get("seed_reports")):
        seed = as_dict(report.get("settings")).get("seed")
        if seed is not None:
            reports[int(seed)] = report
    return reports


def _input_issues(
    stability_report: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    seed_reports: dict[int, dict[str, Any]],
    decode_specs: tuple[dict[str, Any], ...],
) -> list[str]:
    issues: list[str] = []
    if stability_report.get("status") != "pass":
        issues.append("stability report status is not pass")
    if not seed_rows:
        issues.append("stability report has no seed_rows")
    if not seed_reports:
        issues.append("stability report has no embedded seed_reports")
    if not decode_specs:
        issues.append("decode_specs is empty")
    for spec in decode_specs:
        if not spec.get("spec_id"):
            issues.append("decode spec is missing spec_id")
    return issues


def _source_report_for_seed(seed_row: dict[str, Any], seed_report: dict[str, Any]) -> dict[str, Any]:
    seed = int(seed_row.get("seed") or as_dict(seed_report.get("settings")).get("seed") or 0)
    training = as_dict(seed_report.get("training"))
    variant_id = f"seed-{seed}"
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


def _row(seed_row: dict[str, Any], spec: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    pair_full = max(
        int(summary.get("default_pair_full_variant_count") or 0),
        int(summary.get("suppression_pair_full_variant_count") or 0),
    )
    return {
        "spec_id": spec.get("spec_id"),
        "seed": seed_row.get("seed"),
        "source_pair_full_observed": bool(seed_row.get("pair_full_observed")),
        "replay_status": replay.get("status"),
        "replay_decision": replay.get("decision"),
        "top_k": spec.get("top_k"),
        "temperature": spec.get("temperature"),
        "max_new_tokens": spec.get("max_new_tokens"),
        "default_pair_full_variant_count": summary.get("default_pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": summary.get("suppression_pair_full_variant_count", 0),
        "default_continuation_hit_count": summary.get("default_continuation_hit_count", 0),
        "suppression_continuation_hit_count": summary.get("suppression_continuation_hit_count", 0),
        "pair_full_observed": pair_full > 0,
    }


def _summary(rows: list[dict[str, Any]], stability_report: dict[str, Any]) -> dict[str, Any]:
    baseline = as_dict(stability_report.get("summary"))
    spec_rows: list[dict[str, Any]] = []
    for spec_id in sorted({str(row.get("spec_id")) for row in rows}):
        scoped = [row for row in rows if row.get("spec_id") == spec_id]
        spec_rows.append(
            {
                "spec_id": spec_id,
                "seed_count": len(scoped),
                "pair_full_seed_count": sum(1 for row in scoped if row.get("pair_full_observed")),
                "continuation_hit_total": sum(int(row.get("default_continuation_hit_count") or 0) for row in scoped),
            }
        )
    best = max(spec_rows, key=lambda row: (int(row.get("pair_full_seed_count") or 0), int(row.get("continuation_hit_total") or 0)), default={})
    baseline_pair_full = int(baseline.get("pair_full_seed_count") or 0)
    best_pair_full = int(best.get("pair_full_seed_count") or 0)
    return {
        "baseline_pair_full_seed_count": baseline_pair_full,
        "decode_spec_count": len(spec_rows),
        "seed_count": int(baseline.get("seed_count") or 0),
        "best_spec_id": best.get("spec_id", ""),
        "best_pair_full_seed_count": best_pair_full,
        "best_continuation_hit_total": best.get("continuation_hit_total", 0),
        "decode_improved_pair_full": best_pair_full > baseline_pair_full,
        "decode_any_pair_full": best_pair_full > 0,
        "spec_rows": spec_rows,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_decode_boundary_check"
    if summary.get("decode_improved_pair_full"):
        return "required_term_pair_decode_boundary_improves_pair_surface"
    if summary.get("decode_any_pair_full"):
        return "required_term_pair_decode_boundary_partial_pair_surface"
    return "required_term_pair_decode_boundary_no_pair_surface_gain"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The decode boundary check could not replay every requested case."
        next_action = "repair replay inputs before changing training"
    elif summary.get("decode_improved_pair_full"):
        reason = "At least one decode boundary improves pair-full coverage over the source stability report."
        next_action = "promote the best decode spec into the next stability check before retraining"
    elif summary.get("decode_any_pair_full"):
        reason = "A decode boundary surfaces partial pair-full coverage, but does not improve the source result."
        next_action = "keep decode settings visible while continuing corpus repair"
    else:
        reason = "No tested decode boundary surfaces fixed/loss pair-full coverage."
        next_action = "treat the current issue as training objective/data design rather than replay configuration"
    return {
        "model_quality_claim": "targeted_decode_boundary_diagnostic_only" if status == "pass" else "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "DEFAULT_DECODE_SPECS",
    "PAIR_DECODE_BOUNDARY_CHECK_CSV_FILENAME",
    "PAIR_DECODE_BOUNDARY_CHECK_HTML_FILENAME",
    "PAIR_DECODE_BOUNDARY_CHECK_JSON_FILENAME",
    "PAIR_DECODE_BOUNDARY_CHECK_MARKDOWN_FILENAME",
    "PAIR_DECODE_BOUNDARY_CHECK_TEXT_FILENAME",
    "build_model_capability_required_term_pair_decode_boundary_check",
    "locate_pair_colon_immediate_stability",
    "read_json_report",
    "resolve_exit_code",
]
