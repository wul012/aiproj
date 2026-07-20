from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_decoding_sweep import (
    REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, resolve_archived_reference_path, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_JSON_FILENAME = (
    "model_capability_required_term_pair_prompt_separation_audit.json"
)
REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_TEXT_FILENAME = (
    "model_capability_required_term_pair_prompt_separation_audit.txt"
)
REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_prompt_separation_audit.md"
)
REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_HTML_FILENAME = (
    "model_capability_required_term_pair_prompt_separation_audit.html"
)


def locate_model_capability_required_term_pair_prompt_separation_audit_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_prompt_separation_audit(
    pair_decoding_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    source_capacity_report: dict[str, Any] | None = None,
    source_capacity_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    source_base = Path(source_path).parent if source_path else None
    resolved_capacity_path = _resolve_capacity_path(pair_decoding_report, source_capacity_path, source_base)
    if source_capacity_report is not None:
        capacity_report = source_capacity_report
    else:
        capacity_report = read_json_report(resolved_capacity_path) if resolved_capacity_path else {}
    capacity_by_run = {
        str(row.get("capacity_run_id") or ""): row for row in list_of_dicts(capacity_report.get("capacity_rows"))
    }
    targets = _targets_with_corpus(pair_decoding_report, capacity_by_run, resolved_capacity_path)
    issues = _input_issues(pair_decoding_report, capacity_report, targets)
    term_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []

    if not issues:
        for target in targets:
            analysis = _analyze_target(target, source_base=source_base, capacity_base=_parent(resolved_capacity_path))
            term_rows.extend(analysis["term_rows"])
            target_rows.append(analysis["target_row"])

    summary = summarize_required_term_pair_prompt_separation_audit(
        targets,
        target_rows,
        term_rows,
        source_summary=as_dict(pair_decoding_report.get("summary")),
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair prompt separation audit",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_decoding_sweep": str(source_path) if source_path else None,
        "source_required_term_pair_capacity_sweep": str(resolved_capacity_path) if resolved_capacity_path else None,
        "out_dir": str(root),
        "settings": {
            "experiment_boundary": "inspect prompt-target corpus rows after v498 decoding failed to recover pair full-hit",
            "model_quality_claim": "not_claimed",
        },
        "summary": summary,
        "targets": targets,
        "target_rows": target_rows,
        "term_rows": term_rows,
        "interpretation": {
            "model_quality_claim": "not_claimed",
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def summarize_required_term_pair_prompt_separation_audit(
    targets: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    term_rows: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    direct_leaks = sum(int(row.get("other_after_prompt_line_count") or 0) for row in term_rows)
    negative_leaks = sum(int(row.get("negative_contrast_leak_count") or 0) for row in term_rows)
    shared_contexts = sum(int(row.get("pair_header_shared_context_count") or 0) for row in term_rows)
    ready_targets = sum(1 for row in target_rows if row.get("prompt_separation_ready"))
    readable_targets = sum(1 for row in target_rows if row.get("corpus_exists"))
    return {
        "prompt_separation_audit_decision": _audit_decision(targets, target_rows, direct_leaks, negative_leaks),
        "source_pair_decoding_sweep_decision": source.get("pair_decoding_sweep_decision"),
        "source_decoding_full_hit_observed": bool(source.get("decoding_full_hit_observed")),
        "target_count": len(targets),
        "corpus_readable_target_count": readable_targets,
        "term_row_count": len(term_rows),
        "prompt_separation_ready_target_count": ready_targets,
        "prompt_separation_ready": bool(target_rows) and ready_targets == len(target_rows),
        "direct_prompt_other_term_leak_count": direct_leaks,
        "negative_contrast_leak_count": negative_leaks,
        "pair_header_shared_context_count": shared_contexts,
        "target_with_direct_leak_count": sum(1 for row in target_rows if row.get("direct_prompt_leak_observed")),
        "target_with_negative_leak_count": sum(1 for row in target_rows if row.get("negative_contrast_leak_observed")),
        "target_with_shared_pair_context_count": sum(1 for row in target_rows if row.get("shared_pair_context_observed")),
        "corpus_revision_recommended": direct_leaks > 0 or negative_leaks > 0,
    }


def _targets_with_corpus(
    pair_decoding_report: dict[str, Any],
    capacity_by_run: dict[str, dict[str, Any]],
    capacity_path: Path | None,
) -> list[dict[str, Any]]:
    capacity_base = _parent(capacity_path)
    rows: list[dict[str, Any]] = []
    for target in list_of_dicts(pair_decoding_report.get("targets")):
        run_id = str(target.get("capacity_run_id") or "")
        capacity = capacity_by_run.get(run_id, {})
        corpus_ref = capacity.get("capacity_corpus_path")
        corpus_path = resolve_archived_reference_path(corpus_ref, capacity_base) if corpus_ref else None
        rows.append(
            {
                **target,
                "capacity_corpus_path": str(corpus_path) if corpus_path else None,
                "capacity_corpus_exists": bool(corpus_path and corpus_path.is_file()),
                "capacity_line_count": capacity.get("capacity_line_count"),
                "capacity_repeat": capacity.get("repeat") or target.get("capacity_repeat"),
                "isolated_repeat": capacity.get("isolated_repeat"),
            }
        )
    return rows


def _analyze_target(
    target: dict[str, Any],
    *,
    source_base: Path | None,
    capacity_base: Path | None,
) -> dict[str, Any]:
    corpus_path = resolve_archived_reference_path(
        target.get("capacity_corpus_path"),
        capacity_base or source_base,
    )
    lines = _read_lines(corpus_path)
    pair_terms = [str(term) for term in target.get("term_names") or []]
    term_rows = [_analyze_term(target, term, pair_terms, lines) for term in list_of_dicts(target.get("terms"))]
    direct_leaks = sum(int(row.get("other_after_prompt_line_count") or 0) for row in term_rows)
    negative_leaks = sum(int(row.get("negative_contrast_leak_count") or 0) for row in term_rows)
    shared_contexts = sum(int(row.get("pair_header_shared_context_count") or 0) for row in term_rows)
    target_ready = bool(term_rows) and direct_leaks == 0 and negative_leaks == 0 and all(
        int(row.get("target_after_prompt_line_count") or 0) > 0 for row in term_rows
    )
    return {
        "target_row": {
            "target_id": target.get("target_id"),
            "pair_id": target.get("pair_id"),
            "variant_id": target.get("variant_id"),
            "capacity_run_id": target.get("capacity_run_id"),
            "capacity_corpus_path": str(corpus_path) if corpus_path else target.get("capacity_corpus_path"),
            "corpus_exists": bool(corpus_path and corpus_path.is_file()),
            "line_count": len(lines),
            "term_count": len(term_rows),
            "direct_prompt_other_term_leak_count": direct_leaks,
            "negative_contrast_leak_count": negative_leaks,
            "pair_header_shared_context_count": shared_contexts,
            "direct_prompt_leak_observed": direct_leaks > 0,
            "negative_contrast_leak_observed": negative_leaks > 0,
            "shared_pair_context_observed": shared_contexts > 0,
            "prompt_separation_ready": target_ready,
        },
        "term_rows": term_rows,
    }


def _analyze_term(
    target: dict[str, Any],
    term_row: dict[str, Any],
    pair_terms: list[str],
    lines: list[str],
) -> dict[str, Any]:
    term = str(term_row.get("term") or "")
    prompt = str(term_row.get("scaffold_prompt") or f"{term}:")
    other_terms = [item for item in pair_terms if item and item != term]
    prefix_lines = [line for line in lines if line.startswith(prompt)]
    target_after = [line for line in prefix_lines if _contains_after_prompt(line, prompt, term)]
    other_after = [
        line for line in prefix_lines if any(_contains_after_prompt(line, prompt, other) for other in other_terms)
    ]
    negative = [
        line
        for line in prefix_lines
        if any(f" not {other}".casefold() in line[len(prompt) :].casefold() for other in other_terms)
    ]
    pair_headers = [
        line
        for line in lines
        if "pair " in line.casefold() and prompt in line and all(term_name.casefold() in line.casefold() for term_name in pair_terms)
    ]
    return {
        "target_id": target.get("target_id"),
        "pair_id": target.get("pair_id"),
        "variant_id": target.get("variant_id"),
        "capacity_run_id": target.get("capacity_run_id"),
        "case": term_row.get("case"),
        "term": term,
        "scaffold_prompt": prompt,
        "other_terms": other_terms,
        "prompt_prefix_line_count": len(prefix_lines),
        "exact_target_line_count": sum(1 for line in lines if line == f"{prompt}{term}"),
        "spaced_target_line_count": sum(1 for line in lines if line == f"{prompt} {term}"),
        "target_after_prompt_line_count": len(target_after),
        "other_after_prompt_line_count": len(other_after),
        "negative_contrast_leak_count": len(negative),
        "pair_header_shared_context_count": len(pair_headers),
        "prompt_separation_ready": len(other_after) == 0 and len(negative) == 0 and bool(target_after),
        "example_leak_line": _preview(other_after[0]) if other_after else "",
        "example_pair_header_line": _preview(pair_headers[0]) if pair_headers else "",
    }


def _input_issues(
    pair_decoding_report: dict[str, Any],
    capacity_report: dict[str, Any],
    targets: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not pair_decoding_report:
        issues.append("source pair decoding sweep report is missing or invalid")
    if pair_decoding_report and pair_decoding_report.get("status") != "pass":
        issues.append("source pair decoding sweep report is not pass")
    source_decision = as_dict(pair_decoding_report.get("summary")).get("pair_decoding_sweep_decision")
    if source_decision != "pair_decoding_sweep_partial_only":
        issues.append("source pair decoding sweep is not the expected partial-only prompt-separation target")
    if not capacity_report:
        issues.append("source pair capacity sweep report is missing or invalid")
    if not targets:
        issues.append("source pair decoding sweep has no targets to audit")
    missing_corpora = [str(row.get("target_id") or "") for row in targets if not row.get("capacity_corpus_exists")]
    if missing_corpora:
        issues.append(f"{len(missing_corpora)} target capacity corpora are missing: {', '.join(missing_corpora[:3])}")
    return issues


def _resolve_capacity_path(
    pair_decoding_report: dict[str, Any],
    source_capacity_path: str | Path | None,
    source_base: Path | None,
) -> Path | None:
    if source_capacity_path:
        return Path(source_capacity_path)
    value = pair_decoding_report.get("source_required_term_pair_capacity_sweep")
    return resolve_archived_reference_path(value, source_base) if value else None


def _read_lines(path: Path | None) -> list[str]:
    if not path or not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def _contains_after_prompt(line: str, prompt: str, term: str) -> bool:
    return term.casefold() in line[len(prompt) :].casefold()


def _audit_decision(
    targets: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    direct_leaks: int,
    negative_leaks: int,
) -> str:
    if not targets:
        return "prompt_separation_no_targets"
    if not target_rows:
        return "prompt_separation_audit_missing_corpus"
    if direct_leaks > 0 or negative_leaks > 0:
        return "prompt_separation_corpus_revision_needed"
    if all(row.get("prompt_separation_ready") for row in target_rows):
        return "prompt_separation_ready"
    return "prompt_separation_review_needed"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_prompt_separation_audit"
    if summary.get("prompt_separation_ready"):
        return "required_term_pair_prompt_separation_ready"
    if summary.get("corpus_revision_recommended"):
        return "required_term_pair_prompt_separation_revision_needed"
    return "required_term_pair_prompt_separation_review"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The v498 or v497 source artifacts are incomplete, so prompt separation cannot be audited."
    if summary.get("corpus_revision_recommended"):
        return "The same scaffold prompt is followed by the other required term in corpus rows, so the pair corpus mixes target separation with contrast examples."
    if summary.get("prompt_separation_ready"):
        return "Every audited prompt has target rows without direct other-term leakage."
    return "The corpus is readable but needs manual review before another training variant is useful."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair missing source artifacts before changing corpus design"
    if summary.get("corpus_revision_recommended"):
        return "build a contrast-free pair corpus variant before running another capacity or decoding sweep"
    if summary.get("prompt_separation_ready"):
        return "run a small retraining check using this separated corpus design"
    return "review prompt rows and decide whether to split pair targets into separate local contexts"


def _parent(path: Path | None) -> Path | None:
    return path.parent if path else None


def _preview(value: str, limit: int = 120) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."
