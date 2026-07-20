from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_colon_immediate_stability import (
    PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME = "model_capability_required_term_pair_seed_coverage_tradeoff.json"
PAIR_SEED_COVERAGE_TRADEOFF_CSV_FILENAME = "model_capability_required_term_pair_seed_coverage_tradeoff.csv"
PAIR_SEED_COVERAGE_TRADEOFF_TEXT_FILENAME = "model_capability_required_term_pair_seed_coverage_tradeoff.txt"
PAIR_SEED_COVERAGE_TRADEOFF_MARKDOWN_FILENAME = "model_capability_required_term_pair_seed_coverage_tradeoff.md"
PAIR_SEED_COVERAGE_TRADEOFF_HTML_FILENAME = "model_capability_required_term_pair_seed_coverage_tradeoff.html"


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


def build_model_capability_required_term_pair_seed_coverage_tradeoff(
    stability_reports: Sequence[dict[str, Any]],
    *,
    out_dir: str | Path,
    source_paths: Sequence[str | Path] | None = None,
    labels: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    sources = ["" if path is None else str(path) for path in (source_paths or [])]
    config_rows: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    issues = _input_issues(stability_reports)
    config_labels = _config_labels(stability_reports, sources, labels)

    if not issues:
        for index, report in enumerate(stability_reports):
            config_rows.append(_config_row(report, config_labels[index], sources[index] if index < len(sources) else ""))
        seed_rows = _seed_rows(stability_reports, config_rows)

    summary = _summary(config_rows, seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair seed coverage tradeoff",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_colon_immediate_stability_reports": sources,
        "out_dir": str(root),
        "settings": {
            "labels": config_labels,
            "experiment_boundary": "compare already trained colon-immediate stability reports without retraining",
        },
        "config_rows": config_rows,
        "seed_rows": seed_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _input_issues(stability_reports: Sequence[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not stability_reports:
        issues.append("no stability reports provided")
    for index, report in enumerate(stability_reports):
        if report.get("status") != "pass":
            issues.append(f"stability report {index + 1} status is not pass")
        if not list_of_dicts(report.get("seed_rows")):
            issues.append(f"stability report {index + 1} has no seed_rows")
    return issues


def _config_labels(
    stability_reports: Sequence[dict[str, Any]],
    source_paths: Sequence[str],
    labels: Sequence[str] | None,
) -> list[str]:
    raw_labels: list[str] = []
    for index, report in enumerate(stability_reports):
        if labels and index < len(labels) and labels[index]:
            raw_labels.append(str(labels[index]))
            continue
        source = source_paths[index] if index < len(source_paths) else ""
        raw_labels.append(_label_from_source(source) or _label_from_report(report, index))
    return _dedupe_labels(raw_labels)


def _label_from_source(source: str) -> str:
    if not source:
        return ""
    path = Path(source)
    if path.name == PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME:
        return path.parent.name
    return path.stem or path.name


def _label_from_report(report: dict[str, Any], index: int) -> str:
    settings = as_dict(report.get("settings"))
    corpus = str(settings.get("corpus_mode") or "colon-immediate").replace("_", "-")
    top_k = settings.get("top_k")
    temperature = settings.get("temperature")
    return f"{index + 1}-{corpus}-k{top_k}-t{temperature}"


def _dedupe_labels(labels: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for label in labels:
        base = label or "config"
        counts[base] = counts.get(base, 0) + 1
        result.append(base if counts[base] == 1 else f"{base}-{counts[base]}")
    return result


def _config_row(report: dict[str, Any], config_id: str, source_path: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    seed_rows = list_of_dicts(report.get("seed_rows"))
    pair_full_seeds = [int(row.get("seed")) for row in seed_rows if row.get("seed") is not None and row.get("pair_full_observed")]
    return {
        "config_id": config_id,
        "source_path": source_path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "top_k": settings.get("top_k"),
        "temperature": settings.get("temperature"),
        "max_iters": settings.get("max_iters"),
        "pair_full_seed_count": int(summary.get("pair_full_seed_count") or len(pair_full_seeds)),
        "seed_count": int(summary.get("seed_count") or len(seed_rows)),
        "pair_full_seeds": pair_full_seeds,
    }


def _seed_rows(stability_reports: Sequence[dict[str, Any]], config_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seeds = sorted({int(row.get("seed")) for report in stability_reports for row in list_of_dicts(report.get("seed_rows")) if row.get("seed") is not None})
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        covering = [row["config_id"] for row in config_rows if seed in row.get("pair_full_seeds", [])]
        per_config = {
            str(config["config_id"]): seed in config.get("pair_full_seeds", [])
            for config in config_rows
        }
        rows.append(
            {
                "seed": seed,
                "covered_by_union": bool(covering),
                "winning_config_id": covering[0] if covering else "",
                "covering_config_ids": covering,
                "covering_config_count": len(covering),
                "per_config_pair_full": per_config,
            }
        )
    return rows


def _summary(config_rows: list[dict[str, Any]], seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    union_count = sum(1 for row in seed_rows if row.get("covered_by_union"))
    best = max(
        config_rows,
        key=lambda row: (int(row.get("pair_full_seed_count") or 0), str(row.get("config_id"))),
        default={},
    )
    best_count = int(best.get("pair_full_seed_count") or 0)
    exclusive_seeds = _exclusive_seeds(config_rows, seed_rows)
    contributing_configs = sorted(exclusive_seeds)
    return {
        "config_count": len(config_rows),
        "seed_count": seed_count,
        "union_pair_full_seed_count": union_count,
        "union_pair_full_seed_rate": round(union_count / seed_count, 4) if seed_count else 0.0,
        "all_seed_covered_by_union": bool(seed_rows) and union_count == seed_count,
        "best_single_config_id": best.get("config_id", ""),
        "best_single_pair_full_seed_count": best_count,
        "best_single_pair_full_seed_rate": round(best_count / seed_count, 4) if seed_count else 0.0,
        "tradeoff_detected": union_count > best_count,
        "contributing_config_ids": contributing_configs,
        "exclusive_seed_map": exclusive_seeds,
        "uncovered_seeds": [row.get("seed") for row in seed_rows if not row.get("covered_by_union")],
    }


def _exclusive_seeds(config_rows: list[dict[str, Any]], seed_rows: list[dict[str, Any]]) -> dict[str, list[int]]:
    config_ids = [str(row.get("config_id")) for row in config_rows]
    result = {config_id: [] for config_id in config_ids}
    for row in seed_rows:
        covering = [str(config_id) for config_id in row.get("covering_config_ids", [])]
        if len(covering) == 1:
            result[covering[0]].append(int(row["seed"]))
    return {config_id: seeds for config_id, seeds in result.items() if seeds}


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_seed_coverage_tradeoff"
    if summary.get("all_seed_covered_by_union") and summary.get("tradeoff_detected"):
        return "required_term_pair_seed_coverage_tradeoff_complementary_full_union"
    if summary.get("all_seed_covered_by_union"):
        return "required_term_pair_seed_coverage_tradeoff_single_config_full_union"
    if summary.get("tradeoff_detected"):
        return "required_term_pair_seed_coverage_tradeoff_complementary_partial_union"
    if summary.get("union_pair_full_seed_count"):
        return "required_term_pair_seed_coverage_tradeoff_partial_coverage_observed"
    return "required_term_pair_seed_coverage_tradeoff_no_pair_full_coverage"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "At least one source stability report is missing or invalid."
        next_action = "repair source reports before judging configuration tradeoffs"
        claim = "not_claimed"
    elif summary.get("all_seed_covered_by_union") and summary.get("tradeoff_detected"):
        reason = "No single configuration covers every seed, but the compared configurations cover all seeds together."
        next_action = "test an explicit fallback or config-selection policy before more corpus changes"
        claim = "targeted_seed_coverage_tradeoff_signal"
    elif summary.get("all_seed_covered_by_union"):
        reason = "One configuration already covers every seed in the compared set."
        next_action = "promote the best single configuration to the next held-out check"
        claim = "targeted_pair_refresh_stable_signal"
    elif summary.get("tradeoff_detected"):
        reason = "The union improves over the best single configuration, but some seeds remain uncovered."
        next_action = "use the coverage map to choose the next repair seed instead of widening blindly"
        claim = "targeted_seed_coverage_tradeoff_signal"
    elif summary.get("union_pair_full_seed_count"):
        reason = "The compared configurations expose only partial pair-full coverage."
        next_action = "continue first-token and continuation diagnostics before claiming stability"
        claim = "targeted_pair_refresh_partial_signal"
    else:
        reason = "No compared configuration produced pair-full coverage."
        next_action = "return to corpus or objective design before comparing configs"
        claim = "not_claimed"
    return {
        "model_quality_claim": claim,
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_SEED_COVERAGE_TRADEOFF_CSV_FILENAME",
    "PAIR_SEED_COVERAGE_TRADEOFF_HTML_FILENAME",
    "PAIR_SEED_COVERAGE_TRADEOFF_JSON_FILENAME",
    "PAIR_SEED_COVERAGE_TRADEOFF_MARKDOWN_FILENAME",
    "PAIR_SEED_COVERAGE_TRADEOFF_TEXT_FILENAME",
    "build_model_capability_required_term_pair_seed_coverage_tradeoff",
    "locate_pair_colon_immediate_stability",
    "read_json_report",
    "resolve_exit_code",
]
