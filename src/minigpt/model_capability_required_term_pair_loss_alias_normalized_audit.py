from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_focus import REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME, read_json_report as read_json_report
from minigpt.model_capability_required_term_pair_loss_alias_metrics import normalize_for_required_term as normalize_for_required_term, required_term_hit_metrics
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_NORMALIZED_AUDIT_JSON_FILENAME = "model_capability_required_term_pair_loss_alias_normalized_audit.json"
REQUIRED_TERM_PAIR_LOSS_ALIAS_NORMALIZED_AUDIT_TEXT_FILENAME = "model_capability_required_term_pair_loss_alias_normalized_audit.txt"
REQUIRED_TERM_PAIR_LOSS_ALIAS_NORMALIZED_AUDIT_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_alias_normalized_audit.md"
REQUIRED_TERM_PAIR_LOSS_ALIAS_NORMALIZED_AUDIT_HTML_FILENAME = "model_capability_required_term_pair_loss_alias_normalized_audit.html"


def locate_model_capability_required_term_pair_loss_alias_normalized_audit_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_loss_alias_normalized_audit(
    focus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = build_normalized_rows(focus_report)
    issues = _input_issues(focus_report, rows)
    summary = summarize_normalized_rows(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias normalized audit",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_alias_focus": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "normalization": "casefold and remove non-alphanumeric characters before required-term containment check",
            "experiment_boundary": "read-only audit of v516 outputs; no retraining and no relaxed promotion gate",
        },
        "normalized_rows": rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def build_normalized_rows(focus_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed_report in list_of_dicts(focus_report.get("seed_reports")):
        seed = as_dict(seed_report.get("settings")).get("generation_seed")
        for row in list_of_dicts(seed_report.get("generation_rows")):
            expected = str(row.get("expected_term") or "loss")
            continuation = str(row.get("continuation") or "")
            strict_hit = bool(row.get("continuation_hit"))
            metrics = required_term_hit_metrics(continuation, expected, strict_hit=strict_hit)
            rows.append(
                {
                    "seed": seed,
                    "case_id": row.get("case_id"),
                    "case_type": row.get("case_type"),
                    "prompt": row.get("prompt"),
                    "expected_term": expected,
                    "is_focus_case": bool(row.get("is_focus_case")),
                    "strict_hit": strict_hit,
                    "normalized_hit": metrics["normalized_hit"],
                    "normalization_gain": metrics["normalization_gain"],
                    "continuation_preview": row.get("continuation_preview"),
                    "normalized_continuation_preview": _preview(metrics["normalized_continuation"]),
                }
            )
    return rows


def summarize_normalized_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    focus_rows = [row for row in rows if row.get("is_focus_case")]
    strict_hits = sum(1 for row in rows if row.get("strict_hit"))
    normalized_hits = sum(1 for row in rows if row.get("normalized_hit"))
    gains = sum(1 for row in rows if row.get("normalization_gain"))
    focus_normalized_hits = sum(1 for row in focus_rows if row.get("normalized_hit"))
    return {
        "normalized_audit_decision": _normalized_decision(rows, focus_rows, normalized_hits, gains),
        "generation_count": len(rows),
        "focus_generation_count": len(focus_rows),
        "strict_hit_count": strict_hits,
        "normalized_hit_count": normalized_hits,
        "normalization_gain_count": gains,
        "focus_normalized_hit_count": focus_normalized_hits,
        "strict_full_coverage": bool(rows) and strict_hits == len(rows),
        "normalized_full_coverage": bool(rows) and normalized_hits == len(rows),
        "focus_normalized_full_coverage": bool(focus_rows) and focus_normalized_hits == len(focus_rows),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _input_issues(focus_report: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not focus_report:
        issues.append("source loss-alias focus report is missing or invalid")
    if focus_report and focus_report.get("status") != "pass":
        issues.append("source loss-alias focus report is not pass")
    if not rows:
        issues.append("source loss-alias focus report has no generation rows")
    return issues


def _normalized_decision(rows: list[dict[str, Any]], focus_rows: list[dict[str, Any]], normalized_hits: int, gains: int) -> str:
    if not rows:
        return "normalized_audit_no_generation_rows"
    if normalized_hits == len(rows) and gains > 0:
        return "normalized_hidden_full_signal"
    if focus_rows and sum(1 for row in focus_rows if row.get("normalized_hit")) == len(focus_rows) and gains > 0:
        return "normalized_hidden_focus_signal"
    if gains > 0:
        return "normalized_hidden_partial_signal"
    return "normalized_audit_no_hidden_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_normalized_audit"
    if summary.get("normalized_full_coverage"):
        return "required_term_pair_loss_alias_normalized_full_signal"
    if summary.get("focus_normalized_full_coverage"):
        return "required_term_pair_loss_alias_normalized_focus_signal"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_normalized_partial_signal"
    return "required_term_pair_loss_alias_normalized_no_signal"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("normalized_full_coverage"):
        return "tiny_loss_alias_normalized_full_signal"
    if summary.get("focus_normalized_full_coverage"):
        return "tiny_loss_alias_normalized_focus_signal"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "tiny_loss_alias_normalized_partial_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The normalized audit could not be run cleanly."
    if summary.get("normalized_full_coverage"):
        return "Every strict miss becomes a required-term hit after removing formatting separators."
    if summary.get("focus_normalized_full_coverage"):
        return "Every focused miss becomes a required-term hit after normalization."
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "Some strict misses are hidden formatting-separated required-term outputs."
    return "Normalization did not reveal hidden required-term outputs."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair normalized audit inputs before changing training"
    if summary.get("normalized_full_coverage") or summary.get("focus_normalized_full_coverage"):
        return "add a separate strict-vs-normalized metric before deciding whether to train again"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "inspect which cases gain under normalization before changing the corpus"
    return "return to corpus shape or decoding path analysis"


def _preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."
