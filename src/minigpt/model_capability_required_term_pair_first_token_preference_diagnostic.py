from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_first_token_preference_diagnostic.json"
)
PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_first_token_preference_diagnostic.csv"
)
PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_first_token_preference_diagnostic.txt"
)
PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_first_token_preference_diagnostic.md"
)
PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_first_token_preference_diagnostic.html"
)


def locate_first_token_preference_refresh_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("first-token preference diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_first_token_preference_diagnostic(
    reports: Sequence[dict[str, Any]],
    *,
    source_paths: Sequence[str | Path] | None = None,
    source_labels: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_rows = [
        _source_row(index, report, _source_path(source_paths, index), _source_label(source_labels, index, report))
        for index, report in enumerate(reports)
    ]
    prompt_rows = [row for index, report in enumerate(reports) for row in _prompt_rows(source_rows[index], report)]
    summary = _summary(source_rows, prompt_rows)
    issues = _issues(source_rows, prompt_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair first-token preference diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_reports": source_rows,
        "prompt_rows": prompt_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _source_path(paths: Sequence[str | Path] | None, index: int) -> str:
    if paths is None or index >= len(paths):
        return ""
    return str(paths[index])


def _source_label(labels: Sequence[str] | None, index: int, report: dict[str, Any]) -> str:
    if labels is not None and index < len(labels) and labels[index]:
        return str(labels[index])
    mode = str(as_dict(report.get("settings")).get("corpus_mode") or "")
    return Path(mode).name or f"first-token-source-{index + 1}"


def _source_row(index: int, report: dict[str, Any], path: str, label: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    return {
        "index": index,
        "source_label": label,
        "source_path": path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "seed": settings.get("seed"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "pair_full_observed": bool(summary.get("pair_full_observed")),
    }


def _prompt_rows(source: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    replay = as_dict(report.get("replay_report"))
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(replay.get("case_rows")):
        term = str(row.get("term") or "")
        if term not in TARGET_TERMS:
            continue
        continuation = str(row.get("continuation") or "")
        branch_vote = _branch_vote(continuation)
        rows.append(
            {
                "source_label": source.get("source_label"),
                "source_path": source.get("source_path"),
                "corpus_mode": source.get("corpus_mode"),
                "seed": source.get("seed"),
                "profile_id": row.get("profile_id"),
                "term": term,
                "prompt": row.get("prompt"),
                "expected_first_char": term[:1],
                "observed_first_char": _first_visible_char(continuation),
                "first_char_expected": _first_visible_char(continuation) == term[:1],
                "expected_term_at_start": continuation.startswith(term),
                "other_term_at_start": any(continuation.startswith(other) for other in TARGET_TERMS if other != term),
                "branch_vote": branch_vote,
                "continuation_hit": bool(row.get("continuation_hit")),
                "newline_cleanup_hit": bool(row.get("newline_cleanup_hit")),
                "generated_preview": str(row.get("generated") or row.get("generated_preview") or "")[:120],
                "continuation_preview": continuation.replace("\n", "\\n").replace("\r", "\\r")[:120],
            }
        )
    return rows


def _first_visible_char(text: str) -> str:
    for char in text:
        if not char.isspace():
            return char
    return ""


def _branch_vote(text: str) -> str:
    for term in TARGET_TERMS:
        if text.startswith(term):
            return f"{term}-start"
    return "other"


def _summary(source_rows: list[dict[str, Any]], prompt_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fixed_rows = [row for row in prompt_rows if row.get("term") == "fixed"]
    loss_rows = [row for row in prompt_rows if row.get("term") == "loss"]
    source_branch_classes = [_source_branch_class(source.get("source_label"), prompt_rows) for source in source_rows]
    return {
        "source_report_count": len(source_rows),
        "prompt_row_count": len(prompt_rows),
        "first_char_match_count": sum(1 for row in prompt_rows if row.get("first_char_expected")),
        "expected_term_start_count": sum(1 for row in prompt_rows if row.get("expected_term_at_start")),
        "other_term_start_count": sum(1 for row in prompt_rows if row.get("other_term_at_start")),
        "fixed_prompt_count": len(fixed_rows),
        "loss_prompt_count": len(loss_rows),
        "fixed_prompt_loss_start_count": sum(1 for row in fixed_rows if row.get("branch_vote") == "loss-start"),
        "loss_prompt_fixed_start_count": sum(1 for row in loss_rows if row.get("branch_vote") == "fixed-start"),
        "pair_full_report_count": sum(1 for row in source_branch_classes if row.get("branch_class") == "pair-full"),
        "fixed_only_report_count": sum(1 for row in source_branch_classes if row.get("branch_class") == "fixed-only"),
        "loss_only_report_count": sum(1 for row in source_branch_classes if row.get("branch_class") == "loss-only"),
        "all_miss_report_count": sum(1 for row in source_branch_classes if row.get("branch_class") == "all-miss"),
        "source_branch_classes": source_branch_classes,
        "first_token_conflict_confirmed": any(row.get("other_term_at_start") for row in prompt_rows),
        "mixed_branch_tradeoff_confirmed": _mixed_tradeoff(source_branch_classes),
    }


def _source_branch_class(label: Any, prompt_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scoped = [row for row in prompt_rows if row.get("source_label") == label and row.get("continuation_hit")]
    hit_terms = sorted({str(row.get("term")) for row in scoped})
    if set(TARGET_TERMS).issubset(hit_terms):
        branch_class = "pair-full"
    elif hit_terms == ["fixed"]:
        branch_class = "fixed-only"
    elif hit_terms == ["loss"]:
        branch_class = "loss-only"
    elif hit_terms:
        branch_class = "partial"
    else:
        branch_class = "all-miss"
    return {"source_label": label, "hit_terms": hit_terms, "branch_class": branch_class}


def _mixed_tradeoff(rows: list[dict[str, Any]]) -> bool:
    classes = {str(row.get("branch_class")) for row in rows}
    return "pair-full" not in classes and "fixed-only" in classes and "loss-only" in classes


def _issues(source_rows: list[dict[str, Any]], prompt_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(source_rows) < 2:
        issues.append("at least two refresh reports are required")
    for row in source_rows:
        label = row.get("source_label")
        if row.get("status") != "pass":
            issues.append(f"{label} report status is not pass")
        if row.get("training_status") != "pass":
            issues.append(f"{label} training status is not pass")
        if not row.get("checkpoint_exists"):
            issues.append(f"{label} checkpoint is missing")
    if not prompt_rows:
        issues.append("no fixed/loss prompt rows found")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_first_token_preference_inputs"
    if int(summary.get("pair_full_report_count") or 0) > 0:
        return "first_token_preference_has_pair_full_candidate"
    if summary.get("first_token_conflict_confirmed") and summary.get("mixed_branch_tradeoff_confirmed"):
        return "first_token_preference_tradeoff_confirmed"
    if summary.get("first_token_conflict_confirmed"):
        return "first_token_cross_branch_conflict_confirmed"
    return "first_token_preference_diagnostic_recorded"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The diagnostic inputs are incomplete or not scoreable.",
            "next_action": "repair refresh reports before designing a new objective",
        }
    if int(summary.get("pair_full_report_count") or 0) > 0:
        return {
            "model_quality_claim": "pair_full_candidate_observed",
            "reason": "At least one source report already shows both target terms.",
            "next_action": "run seed stability before adding more objective variants",
        }
    return {
        "model_quality_claim": "diagnostic_only",
        "reason": "The same prompt surface flips between fixed-only and loss-only outcomes without a pair-full route.",
        "next_action": "design a contrast-free objective that separates first-token choice from repeated term loops",
    }


__all__ = [
    "PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_required_term_pair_first_token_preference_diagnostic",
    "locate_first_token_preference_refresh_report",
    "read_json_report",
    "resolve_exit_code",
]
