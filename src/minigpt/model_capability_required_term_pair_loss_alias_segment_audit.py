from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_focus import REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
from minigpt.model_capability_required_term_pair_loss_alias_metrics import normalize_for_required_term
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path, utc_now
from minigpt.tokenizer import load_tokenizer


REQUIRED_TERM_PAIR_LOSS_ALIAS_SEGMENT_AUDIT_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_segment_audit.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_SEGMENT_AUDIT_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_segment_audit.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_SEGMENT_AUDIT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_segment_audit.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_SEGMENT_AUDIT_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_segment_audit.html"
)


def locate_loss_alias_segment_audit_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_model_capability_required_term_pair_loss_alias_segment_audit(
    focus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _input_issues(focus_report)
    rows = [] if issues else _audit_rows(focus_report)
    summary = _summary(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias segment audit",
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


def _audit_rows(focus_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base_dir = Path(str(focus_report.get("out_dir") or "."))
    for seed_report in list_of_dicts(focus_report.get("seed_reports")):
        seed = as_dict(seed_report.get("settings")).get("generation_seed")
        tokenizer = _load_report_tokenizer(seed_report, base_dir)
        for generation in list_of_dicts(seed_report.get("generation_rows")):
            continuation = str(generation.get("continuation") or "")
            expected = str(generation.get("expected_term") or "loss")
            shape = _segment_shape(continuation, expected)
            token_shape = _token_shape(tokenizer, continuation)
            rows.append(
                {
                    "seed": seed,
                    "case_id": generation.get("case_id"),
                    "case_type": generation.get("case_type"),
                    "alias_group": generation.get("alias_group"),
                    "expected_term": expected,
                    "strict_hit": bool(generation.get("continuation_hit")),
                    "normalized_hit": bool(generation.get("normalized_hit")),
                    "normalization_gain": bool(generation.get("normalization_gain")),
                    "separator_kind": shape["separator_kind"],
                    "separator_text": shape["separator_text"],
                    "alnum_segment_count": shape["alnum_segment_count"],
                    "normalized_continuation": shape["normalized_continuation"],
                    "normalized_expected_index": shape["normalized_expected_index"],
                    "continuation_preview": _preview(continuation),
                    "tokenizer_loaded": token_shape["tokenizer_loaded"],
                    "tokenizer_name": token_shape["tokenizer_name"],
                    "token_count": token_shape["token_count"],
                    "token_pieces_preview": token_shape["token_pieces_preview"],
                }
            )
    return rows


def _load_report_tokenizer(seed_report: dict[str, Any], base_dir: Path) -> Any:
    tokenizer_path = as_dict(seed_report.get("training")).get("tokenizer_path")
    resolved = resolve_archived_reference_path(tokenizer_path, base_dir)
    if not resolved or not resolved.is_file():
        return None
    try:
        return load_tokenizer(resolved)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None


def _segment_shape(continuation: str, expected: str) -> dict[str, Any]:
    normalized = normalize_for_required_term(continuation)
    normalized_expected = normalize_for_required_term(expected)
    matched = _subsequence_match(continuation, expected)
    separator_text = matched["separator_text"]
    return {
        "separator_kind": _separator_kind(separator_text),
        "separator_text": separator_text,
        "alnum_segment_count": len(re.findall(r"[A-Za-z0-9]+", continuation)),
        "normalized_continuation": normalized,
        "normalized_expected_index": normalized.find(normalized_expected) if normalized_expected else -1,
    }


def _subsequence_match(text: str, expected: str) -> dict[str, str]:
    expected_chars = [char for char in expected if char.isalnum()]
    best_separators = ""
    for start, char in enumerate(text):
        if not expected_chars or char.casefold() != expected_chars[0].casefold():
            continue
        index = start
        separators: list[str] = []
        matched = True
        for expected_char in expected_chars[1:]:
            next_index = index + 1
            while next_index < len(text) and text[next_index].casefold() != expected_char.casefold():
                if text[next_index].isalnum():
                    break
                separators.append(text[next_index])
                next_index += 1
            if next_index >= len(text) or text[next_index].casefold() != expected_char.casefold():
                matched = False
                break
            index = next_index
        if matched:
            return {"separator_text": "".join(separators)}
        best_separators = "".join(separators)
    return {"separator_text": best_separators}


def _separator_kind(separator_text: str) -> str:
    if not separator_text:
        return "none"
    kinds = set()
    if "\n" in separator_text or "\r" in separator_text:
        kinds.add("newline")
    if any(char.isspace() and char not in "\r\n" for char in separator_text):
        kinds.add("space")
    if any((not char.isspace()) and (not char.isalnum()) for char in separator_text):
        kinds.add("punctuation")
    return next(iter(kinds)) if len(kinds) == 1 else "mixed"


def _token_shape(tokenizer: Any, continuation: str) -> dict[str, Any]:
    if tokenizer is None:
        return {"tokenizer_loaded": False, "tokenizer_name": None, "token_count": 0, "token_pieces_preview": ""}
    ids = tokenizer.encode(continuation)
    pieces = [tokenizer.decode([idx]) for idx in ids[:12]]
    return {
        "tokenizer_loaded": True,
        "tokenizer_name": getattr(tokenizer, "name", "unknown"),
        "token_count": len(ids),
        "token_pieces_preview": _preview("|".join(_display_piece(piece) for piece in pieces)),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gain_rows = [row for row in rows if row.get("normalization_gain")]
    newline_gain_count = sum(1 for row in gain_rows if row.get("separator_kind") == "newline")
    space_gain_count = sum(1 for row in gain_rows if row.get("separator_kind") == "space")
    mixed_gain_count = sum(1 for row in gain_rows if row.get("separator_kind") == "mixed")
    return {
        "segment_audit_decision": _segment_decision(len(gain_rows), newline_gain_count, space_gain_count, mixed_gain_count),
        "case_count": len(rows),
        "strict_miss_normalized_hit_count": sum(
            1 for row in rows if not row.get("strict_hit") and row.get("normalized_hit")
        ),
        "normalization_gain_count": len(gain_rows),
        "newline_gain_count": newline_gain_count,
        "space_gain_count": space_gain_count,
        "mixed_gain_count": mixed_gain_count,
        "tokenizer_loaded_count": sum(1 for row in rows if row.get("tokenizer_loaded")),
        "dominant_separator_kind": _dominant_separator(gain_rows),
    }


def _segment_decision(gain_count: int, newline_count: int, space_count: int, mixed_count: int) -> str:
    if gain_count == 0:
        return "loss_alias_segment_no_normalization_gain"
    if newline_count == gain_count:
        return "loss_alias_segment_newline_split"
    if space_count == gain_count:
        return "loss_alias_segment_space_split"
    if mixed_count == gain_count:
        return "loss_alias_segment_mixed_split"
    return "loss_alias_segment_multiple_separator_shapes"


def _dominant_separator(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("separator_kind") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return "none"
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_segment_audit"
    if summary.get("segment_audit_decision") == "loss_alias_segment_newline_split":
        return "required_term_pair_loss_alias_newline_segment_boundary"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_separator_segment_boundary"
    return "required_term_pair_loss_alias_no_segment_gain"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "tiny_loss_alias_formatting_boundary_observed"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source focus report could not be audited."
    if summary.get("segment_audit_decision") == "loss_alias_segment_newline_split":
        return "All normalization gains came from loss characters split by newline separators."
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "Normalization gains came from separator-delimited loss characters."
    return "The focus report did not contain strict misses that normalization could recover."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair the focus metrics report before segment analysis"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "test decoding cleanup or stop-token handling before changing the training corpus again"
    return "return to training objective changes because no segment-level formatting issue was found"


def _display_piece(piece: str) -> str:
    return piece.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _preview(value: str, limit: int = 80) -> str:
    text = value.replace("\n", "\\n").replace("\r", "\\r")
    return text if len(text) <= limit else text[: limit - 3] + "..."
