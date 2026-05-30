from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_loss_alias_focus import REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
from minigpt.model_capability_required_term_pair_loss_alias_metrics import normalize_for_required_term
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_decode_cleanup.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_decode_cleanup.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_decode_cleanup.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_DECODE_CLEANUP_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_decode_cleanup.html"
)


CleanupFunc = Callable[[str], str]
CLEANUP_STRATEGIES: tuple[tuple[str, CleanupFunc], ...] = (
    ("raw", lambda value: value),
    ("strip", lambda value: value.strip()),
    ("remove_newlines", lambda value: value.replace("\r", "").replace("\n", "")),
    ("collapse_whitespace", lambda value: re.sub(r"\s+", " ", value).strip()),
    ("remove_all_whitespace", lambda value: re.sub(r"\s+", "", value)),
    ("alnum_only", normalize_for_required_term),
)


def locate_loss_alias_decode_cleanup_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_model_capability_required_term_pair_loss_alias_decode_cleanup(
    focus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _input_issues(focus_report)
    rows = [] if issues else _cleanup_rows(focus_report)
    summary = _summary(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias decode cleanup",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_loss_alias_focus": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "case_rows": rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _input_issues(focus_report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not focus_report:
        issues.append("source loss-alias focus report is missing or invalid")
    elif focus_report.get("status") != "pass":
        issues.append("source loss-alias focus report is not pass")
    if focus_report and not list_of_dicts(focus_report.get("seed_reports")):
        issues.append("source loss-alias focus report has no seed reports")
    return issues


def _cleanup_rows(focus_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_report in list_of_dicts(focus_report.get("seed_reports")):
        seed = as_dict(seed_report.get("settings")).get("generation_seed")
        for generation in list_of_dicts(seed_report.get("generation_rows")):
            continuation = str(generation.get("continuation") or "")
            expected = str(generation.get("expected_term") or "loss")
            strategy_hits = _strategy_hits(continuation, expected)
            rows.append(
                {
                    "seed": seed,
                    "case_id": generation.get("case_id"),
                    "case_type": generation.get("case_type"),
                    "alias_group": generation.get("alias_group"),
                    "expected_term": expected,
                    "raw_hit": strategy_hits["raw"],
                    "normalized_hit": bool(generation.get("normalized_hit")),
                    "normalization_gain": bool(generation.get("normalization_gain")),
                    "remove_newlines_hit": strategy_hits["remove_newlines"],
                    "collapse_whitespace_hit": strategy_hits["collapse_whitespace"],
                    "remove_all_whitespace_hit": strategy_hits["remove_all_whitespace"],
                    "alnum_only_hit": strategy_hits["alnum_only"],
                    "minimal_recovery_strategy": _minimal_recovery_strategy(strategy_hits),
                    "continuation_preview": _preview(continuation),
                    "remove_newlines_preview": _preview(_strategy_text("remove_newlines", continuation)),
                }
            )
    return rows


def _strategy_hits(continuation: str, expected: str) -> dict[str, bool]:
    expected_text = expected.casefold()
    normalized_expected = normalize_for_required_term(expected)
    hits: dict[str, bool] = {}
    for name, func in CLEANUP_STRATEGIES:
        cleaned = func(continuation)
        needle = normalized_expected if name == "alnum_only" else expected_text
        haystack = cleaned if name == "alnum_only" else cleaned.casefold()
        hits[name] = bool(needle) and needle in haystack
    return hits


def _strategy_text(name: str, continuation: str) -> str:
    for strategy_name, func in CLEANUP_STRATEGIES:
        if strategy_name == name:
            return func(continuation)
    return continuation


def _minimal_recovery_strategy(strategy_hits: dict[str, bool]) -> str:
    for name, _func in CLEANUP_STRATEGIES:
        if strategy_hits.get(name):
            return name
    return "none"


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw_hit_count = sum(1 for row in rows if row.get("raw_hit"))
    remove_newlines_count = sum(1 for row in rows if row.get("remove_newlines_hit"))
    collapse_whitespace_count = sum(1 for row in rows if row.get("collapse_whitespace_hit"))
    remove_all_whitespace_count = sum(1 for row in rows if row.get("remove_all_whitespace_hit"))
    alnum_count = sum(1 for row in rows if row.get("alnum_only_hit"))
    return {
        "decode_cleanup_decision": _cleanup_decision(len(rows), raw_hit_count, remove_newlines_count, remove_all_whitespace_count),
        "case_count": len(rows),
        "raw_hit_count": raw_hit_count,
        "remove_newlines_hit_count": remove_newlines_count,
        "collapse_whitespace_hit_count": collapse_whitespace_count,
        "remove_all_whitespace_hit_count": remove_all_whitespace_count,
        "alnum_only_hit_count": alnum_count,
        "remove_newlines_full_coverage": bool(rows) and remove_newlines_count == len(rows),
        "remove_all_whitespace_full_coverage": bool(rows) and remove_all_whitespace_count == len(rows),
        "alnum_only_full_coverage": bool(rows) and alnum_count == len(rows),
        "minimal_recovery_strategy": _dominant_minimal_strategy(rows),
    }


def _cleanup_decision(row_count: int, raw_hit_count: int, remove_newlines_count: int, remove_all_whitespace_count: int) -> str:
    if row_count == 0:
        return "loss_alias_decode_cleanup_no_rows"
    if raw_hit_count == row_count:
        return "loss_alias_decode_cleanup_raw_already_full"
    if remove_newlines_count == row_count:
        return "loss_alias_decode_cleanup_remove_newlines_full"
    if remove_all_whitespace_count == row_count:
        return "loss_alias_decode_cleanup_remove_all_whitespace_full"
    if remove_newlines_count > raw_hit_count or remove_all_whitespace_count > raw_hit_count:
        return "loss_alias_decode_cleanup_partial_recovery"
    return "loss_alias_decode_cleanup_no_recovery"


def _dominant_minimal_strategy(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        strategy = str(row.get("minimal_recovery_strategy") or "none")
        counts[strategy] = counts.get(strategy, 0) + 1
    if not counts:
        return "none"
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_decode_cleanup"
    if summary.get("decode_cleanup_decision") == "loss_alias_decode_cleanup_remove_newlines_full":
        return "required_term_pair_loss_alias_remove_newlines_cleanup_recovers_full"
    if summary.get("decode_cleanup_decision") == "loss_alias_decode_cleanup_remove_all_whitespace_full":
        return "required_term_pair_loss_alias_whitespace_cleanup_recovers_full"
    if int(summary.get("remove_newlines_hit_count") or 0) > int(summary.get("raw_hit_count") or 0):
        return "required_term_pair_loss_alias_decode_cleanup_partial_recovery"
    return "required_term_pair_loss_alias_decode_cleanup_no_recovery"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("remove_newlines_full_coverage"):
        return "tiny_loss_alias_newline_cleanup_recovers_strict_surface"
    if summary.get("remove_all_whitespace_full_coverage"):
        return "tiny_loss_alias_whitespace_cleanup_recovers_strict_surface"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source focus report could not be audited."
    if summary.get("remove_newlines_full_coverage"):
        return "Removing newline separators would recover strict loss hits for every focused row."
    if summary.get("remove_all_whitespace_full_coverage"):
        return "Removing all whitespace would recover strict loss hits, but newline-only cleanup is not sufficient."
    return "Cleanup strategies did not recover full strict loss hits."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the focus metrics report before cleanup analysis"
    if summary.get("remove_newlines_full_coverage"):
        return "test a bounded newline cleanup evaluation before changing the training objective"
    if summary.get("remove_all_whitespace_full_coverage"):
        return "inspect whether cleanup would be too broad before using it in evaluation"
    return "return to corpus or decoding changes because cleanup did not recover strict hits"


def _preview(value: str, limit: int = 80) -> str:
    text = value.replace("\n", "\\n").replace("\r", "\\r")
    return text if len(text) <= limit else text[: limit - 3] + "..."
