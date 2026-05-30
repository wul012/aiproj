from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_forced_choice_diagnostic import (
    REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_generation_gap_components import (
    build_generation_gap_rows,
    summarize_generation_gap_variants,
    summarize_required_term_pair_generation_gap,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, utc_now


REQUIRED_TERM_PAIR_GENERATION_GAP_JSON_FILENAME = "model_capability_required_term_pair_generation_gap.json"
REQUIRED_TERM_PAIR_GENERATION_GAP_TEXT_FILENAME = "model_capability_required_term_pair_generation_gap.txt"
REQUIRED_TERM_PAIR_GENERATION_GAP_MARKDOWN_FILENAME = "model_capability_required_term_pair_generation_gap.md"
REQUIRED_TERM_PAIR_GENERATION_GAP_HTML_FILENAME = "model_capability_required_term_pair_generation_gap.html"


def locate_model_capability_required_term_pair_generation_gap_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_generation_gap(
    forced_choice_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    branch_retention_report: dict[str, Any] | None = None,
    branch_retention_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_branch_path = branch_retention_path or forced_choice_report.get("source_required_term_pair_branch_retention_sweep")
    branch_report = branch_retention_report or _read_source_branch_report(source_branch_path)
    issues = _input_issues(forced_choice_report, branch_report, source_branch_path)
    gap_rows = build_generation_gap_rows(forced_choice_report, branch_report) if not issues else []
    variant_summaries = (
        summarize_generation_gap_variants(forced_choice_report, branch_report, gap_rows) if not issues else []
    )
    summary = summarize_required_term_pair_generation_gap(forced_choice_report, branch_report, gap_rows, variant_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair generation gap",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_forced_choice_diagnostic": str(source_path) if source_path else None,
        "source_required_term_pair_branch_retention_sweep": str(source_branch_path) if source_branch_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "experiment_boundary": "read-only comparison of teacher-forced choices and archived free-generation probes",
        },
        "source_baseline": _source_baseline(forced_choice_report, branch_report),
        "gap_rows": gap_rows,
        "variant_summaries": variant_summaries,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _read_source_branch_report(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return read_json_report(Path(path))
    except (OSError, ValueError):
        return {}


def _input_issues(
    forced_choice_report: dict[str, Any],
    branch_retention_report: dict[str, Any],
    source_branch_path: str | Path | None,
) -> list[str]:
    issues: list[str] = []
    if not forced_choice_report:
        issues.append("source forced-choice diagnostic report is missing or invalid")
    if forced_choice_report and forced_choice_report.get("status") != "pass":
        issues.append("source forced-choice diagnostic report is not pass")
    if not source_branch_path:
        issues.append("source forced-choice diagnostic does not point to a branch-retention sweep")
    if source_branch_path and not branch_retention_report:
        issues.append("source branch-retention sweep report could not be read")
    if branch_retention_report and branch_retention_report.get("status") != "pass":
        issues.append("source branch-retention sweep report is not pass")
    if forced_choice_report and not forced_choice_report.get("prompt_summaries"):
        issues.append("source forced-choice diagnostic has no prompt summaries")
    if branch_retention_report and not branch_retention_report.get("probe_rows"):
        issues.append("source branch-retention sweep has no generation probe rows")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_generation_gap"
    decision = str(summary.get("generation_gap_decision") or "")
    if decision == "generation_gap_internal_signal_not_expressed":
        return "required_term_pair_generation_gap_observed"
    if decision == "generation_gap_generation_aligned":
        return "required_term_pair_generation_aligned"
    return "required_term_pair_generation_gap_not_observed"


def _source_baseline(forced_choice_report: dict[str, Any], branch_retention_report: dict[str, Any]) -> dict[str, Any]:
    forced = as_dict(forced_choice_report.get("summary"))
    branch = as_dict(branch_retention_report.get("summary"))
    return {
        "forced_choice_diagnostic_decision": forced.get("forced_choice_diagnostic_decision"),
        "forced_choice_full_match_variant_count": forced.get("forced_choice_full_match_variant_count"),
        "branch_retention_sweep_decision": branch.get("branch_retention_sweep_decision"),
        "generation_pair_full_hit_variant_count": branch.get("pair_full_hit_variant_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("forced_generation_gap_variant_count") or 0) > 0:
        return "internal_signal_not_free_generation_quality"
    if int(summary.get("generation_full_match_variant_count") or 0) > 0:
        return "generation_alignment_observed"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The forced-choice diagnostic and source generation probes were not both readable."
    if int(summary.get("forced_generation_gap_variant_count") or 0) > 0:
        return "At least one checkpoint has a forced-choice full match that is not expressed by archived free generation."
    if int(summary.get("generation_full_match_variant_count") or 0) > 0:
        return "Archived free generation already expresses at least one full-match variant."
    return "No forced-choice/free-generation gap was observed."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair source report links before comparing generation behavior"
    if int(summary.get("forced_generation_gap_variant_count") or 0) > 0:
        return "probe deterministic decoding around the best gap variant before changing corpus weights again"
    return "continue with the smallest generation-side diagnostic that preserves existing checkpoints"
