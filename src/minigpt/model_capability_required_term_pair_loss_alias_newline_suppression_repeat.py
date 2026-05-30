from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_probe import (
    GenerateFunc,
    build_model_capability_required_term_pair_loss_alias_newline_suppression_probe,
    locate_loss_alias_newline_suppression_source,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_repeat.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_repeat.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_repeat.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_REPEAT_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_repeat.html"
)


def build_model_capability_required_term_pair_loss_alias_newline_suppression_repeat(
    focus_sources: list[str | Path],
    *,
    out_dir: str | Path,
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    source_paths = [locate_loss_alias_newline_suppression_source(source) for source in focus_sources]
    issues = _input_issues(source_paths)
    probe_reports = [] if issues else _probe_reports(source_paths, Path(out_dir), generate_func)
    source_rows = _source_rows(probe_reports)
    summary = _summary(source_rows)
    status = "pass" if not issues and all(report.get("status") == "pass" for report in probe_reports) else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias newline suppression repeat",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues) + sum(1 for report in probe_reports if report.get("status") != "pass"),
        "issues": issues,
        "out_dir": str(out_dir),
        "source_paths": [str(path) for path in source_paths],
        "source_rows": source_rows,
        "probe_reports": probe_reports,
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


def _input_issues(source_paths: list[Path]) -> list[str]:
    issues: list[str] = []
    if not source_paths:
        issues.append("at least one loss-alias focus source is required")
    for source in source_paths:
        if not source.exists():
            issues.append(f"source loss-alias focus report does not exist: {source}")
    return issues


def _probe_reports(source_paths: list[Path], out_dir: Path, generate_func: GenerateFunc | None) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for source in source_paths:
        source_id = _source_id(source)
        reports.append(
            build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
                read_json_report(source),
                out_dir=out_dir / "source-probes" / source_id,
                source_path=source,
                generate_func=generate_func,
            )
        )
    return reports


def _source_rows(probe_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in probe_reports:
        summary = as_dict(report.get("summary"))
        source_path = str(report.get("source_loss_alias_focus") or "")
        rows.append(
            {
                "source_id": _source_id(Path(source_path)) if source_path else "unknown",
                "source_loss_alias_focus": source_path,
                "status": report.get("status"),
                "decision": report.get("decision"),
                "case_count": summary.get("case_count"),
                "baseline_strict_hit_count": summary.get("baseline_strict_hit_count"),
                "baseline_strict_full_coverage": summary.get("baseline_strict_full_coverage"),
                "suppressed_strict_hit_count": summary.get("suppressed_strict_hit_count"),
                "suppressed_strict_full_coverage": summary.get("suppressed_strict_full_coverage"),
                "suppressed_focus_strict_hit_count": summary.get("suppressed_focus_strict_hit_count"),
                "suppressed_focus_strict_full_coverage": summary.get("suppressed_focus_strict_full_coverage"),
                "suppressed_strict_gain_count": summary.get("suppressed_strict_gain_count"),
            }
        )
    return rows


def _summary(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_count = len(source_rows)
    pass_count = sum(1 for row in source_rows if row.get("status") == "pass")
    suppressed_full_count = sum(1 for row in source_rows if row.get("suppressed_strict_full_coverage"))
    baseline_full_count = sum(1 for row in source_rows if row.get("baseline_strict_full_coverage"))
    gain_count = sum(int(row.get("suppressed_strict_gain_count") or 0) for row in source_rows)
    return {
        "newline_suppression_repeat_decision": _repeat_decision(source_count, pass_count, suppressed_full_count, baseline_full_count, gain_count),
        "source_count": source_count,
        "pass_source_count": pass_count,
        "suppressed_strict_full_source_count": suppressed_full_count,
        "baseline_strict_full_source_count": baseline_full_count,
        "suppressed_strict_gain_count": gain_count,
        "stable_suppressed_strict_full_coverage": source_count > 0 and suppressed_full_count == source_count,
        "stable_baseline_strict_full_coverage": source_count > 0 and baseline_full_count == source_count,
        "case_count_total": sum(int(row.get("case_count") or 0) for row in source_rows),
    }


def _repeat_decision(
    source_count: int,
    pass_count: int,
    suppressed_full_count: int,
    baseline_full_count: int,
    gain_count: int,
) -> str:
    if source_count == 0:
        return "loss_alias_newline_suppression_repeat_no_sources"
    if pass_count < source_count:
        return "loss_alias_newline_suppression_repeat_structural_failures"
    if suppressed_full_count == source_count and baseline_full_count < source_count and gain_count > 0:
        return "loss_alias_newline_suppression_repeat_stable_strict_recovery"
    if suppressed_full_count > 0 and gain_count > 0:
        return "loss_alias_newline_suppression_repeat_partial_strict_recovery"
    if baseline_full_count == source_count:
        return "loss_alias_newline_suppression_repeat_baseline_already_full"
    return "loss_alias_newline_suppression_repeat_no_strict_recovery"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_newline_suppression_repeat"
    if summary.get("stable_suppressed_strict_full_coverage") and not summary.get("stable_baseline_strict_full_coverage"):
        return "required_term_pair_loss_alias_newline_suppression_stable_strict_recovery"
    if int(summary.get("suppressed_strict_full_source_count") or 0) > 0:
        return "required_term_pair_loss_alias_newline_suppression_partial_repeat_recovery"
    return "required_term_pair_loss_alias_newline_suppression_repeat_no_recovery"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("stable_suppressed_strict_full_coverage") and not summary.get("stable_baseline_strict_full_coverage"):
        return "tiny_loss_alias_newline_suppression_stable_strict_surface_recovery"
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "tiny_loss_alias_newline_suppression_repeat_partial_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one source focus report could not be probed cleanly."
    if summary.get("stable_suppressed_strict_full_coverage") and not summary.get("stable_baseline_strict_full_coverage"):
        return "Newline-token suppression recovered strict loss hits for every compared focus report while baseline reruns did not."
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "Newline-token suppression recovered strict hits for at least one compared focus report."
    return "Newline-token suppression did not recover strict hits across the compared focus reports."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair repeat inputs before making a decoding recommendation"
    if summary.get("stable_suppressed_strict_full_coverage") and not summary.get("stable_baseline_strict_full_coverage"):
        return "promote newline-suppressed decoding as an experimental evaluation profile and compare it with fresh training"
    return "collect more focus checkpoints before changing the default decoding policy"


def _source_id(path: Path) -> str:
    parts = list(path.parts)
    for index, part in enumerate(parts):
        if part == "e" and index + 1 < len(parts):
            return f"v{parts[index + 1]}"
    return path.parent.name or path.stem
