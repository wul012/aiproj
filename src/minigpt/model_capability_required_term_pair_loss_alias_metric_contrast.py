from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_loss_alias_focus import REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
from minigpt.model_capability_required_term_pair_loss_alias_stability import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_metric_contrast.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_metric_contrast.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_metric_contrast.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_METRIC_CONTRAST_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_metric_contrast.html"
)


def locate_loss_alias_metric_contrast_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME
    return source


def locate_loss_alias_metric_contrast_focus_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_model_capability_required_term_pair_loss_alias_metric_contrast(
    stability_report: dict[str, Any],
    focus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    stability_source_path: str | Path | None = None,
    focus_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _input_issues(stability_report, focus_report)
    stage_rows = _stage_rows(stability_report, focus_report, stability_source_path, focus_source_path)
    summary = _summary(stage_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias metric contrast",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(out_dir),
        "stage_rows": stage_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def _input_issues(stability_report: dict[str, Any], focus_report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not stability_report:
        issues.append("source loss-alias stability report is missing or invalid")
    elif stability_report.get("status") != "pass":
        issues.append("source loss-alias stability report is not pass")
    if not focus_report:
        issues.append("source loss-alias focus report is missing or invalid")
    elif focus_report.get("status") != "pass":
        issues.append("source loss-alias focus report is not pass")
    return issues


def _stage_rows(
    stability_report: dict[str, Any],
    focus_report: dict[str, Any],
    stability_source_path: str | Path | None,
    focus_source_path: str | Path | None,
) -> list[dict[str, Any]]:
    stability = as_dict(stability_report.get("summary"))
    focus = as_dict(focus_report.get("summary"))
    return [
        {
            "stage": "stability-source",
            "label": "seed stability source",
            "status": stability_report.get("status"),
            "decision": stability_report.get("decision"),
            "strict_decision": stability.get("loss_alias_stability_decision"),
            "metric_decision": stability.get("loss_alias_stability_metric_decision"),
            "seed_count": stability.get("seed_count"),
            "strict_full_seed_count": stability.get("heldout_loss_alias_full_seed_count"),
            "normalized_full_seed_count": stability.get("heldout_loss_alias_normalized_full_seed_count"),
            "stable_strict_full": stability.get("stable_loss_alias_full_coverage"),
            "stable_normalized_full": stability.get("stable_loss_alias_normalized_full_coverage"),
            "normalization_gain_count": stability.get("normalization_gain_count"),
            "source_path": str(stability_source_path) if stability_source_path else "",
        },
        {
            "stage": "focused-repair",
            "label": "focused repair metrics",
            "status": focus_report.get("status"),
            "decision": focus_report.get("decision"),
            "strict_decision": focus.get("loss_alias_focus_decision"),
            "metric_decision": focus.get("loss_alias_focus_metric_decision"),
            "seed_count": focus.get("seed_count"),
            "strict_full_seed_count": focus.get("support_full_seed_count"),
            "normalized_full_seed_count": focus.get("support_normalized_full_seed_count"),
            "stable_strict_full": focus.get("stable_support_full_coverage"),
            "stable_normalized_full": focus.get("stable_support_normalized_full_coverage"),
            "normalization_gain_count": focus.get("normalization_gain_count"),
            "source_path": str(focus_source_path) if focus_source_path else "",
        },
    ]


def _summary(stage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source = next((row for row in stage_rows if row.get("stage") == "stability-source"), {})
    focus = next((row for row in stage_rows if row.get("stage") == "focused-repair"), {})
    source_gain = int(source.get("normalization_gain_count") or 0)
    focus_gain = int(focus.get("normalization_gain_count") or 0)
    return {
        "metric_contrast_decision": _metric_contrast_decision(source, focus, source_gain, focus_gain),
        "stage_count": len(stage_rows),
        "passing_stage_count": sum(1 for row in stage_rows if row.get("status") == "pass"),
        "source_strict_decision": source.get("strict_decision"),
        "source_metric_decision": source.get("metric_decision"),
        "focus_strict_decision": focus.get("strict_decision"),
        "focus_metric_decision": focus.get("metric_decision"),
        "source_normalization_gain_count": source_gain,
        "focus_normalization_gain_count": focus_gain,
        "normalization_gain_delta": focus_gain - source_gain,
        "source_stable_normalized_full": bool(source.get("stable_normalized_full")),
        "focus_stable_normalized_full": bool(focus.get("stable_normalized_full")),
        "source_stable_strict_full": bool(source.get("stable_strict_full")),
        "focus_stable_strict_full": bool(focus.get("stable_strict_full")),
    }


def _metric_contrast_decision(source: dict[str, Any], focus: dict[str, Any], source_gain: int, focus_gain: int) -> str:
    if focus.get("stable_strict_full"):
        return "loss_alias_focus_strict_full_repair"
    if not source.get("stable_normalized_full") and focus.get("stable_normalized_full") and focus_gain > source_gain:
        return "loss_alias_focus_introduced_normalized_full_signal"
    if focus_gain > source_gain:
        return "loss_alias_focus_increased_normalization_signal"
    return "loss_alias_metric_contrast_no_new_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_metric_contrast"
    if summary.get("metric_contrast_decision") == "loss_alias_focus_strict_full_repair":
        return "required_term_pair_loss_alias_focus_strict_repair_confirmed"
    if summary.get("metric_contrast_decision") == "loss_alias_focus_introduced_normalized_full_signal":
        return "required_term_pair_loss_alias_focus_normalized_delta_observed"
    if summary.get("metric_contrast_decision") == "loss_alias_focus_increased_normalization_signal":
        return "required_term_pair_loss_alias_focus_normalization_delta_observed"
    return "required_term_pair_loss_alias_metric_contrast_no_new_signal"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("focus_stable_strict_full"):
        return "tiny_loss_alias_focus_strict_repair_signal"
    if summary.get("focus_stable_normalized_full") and int(summary.get("normalization_gain_delta") or 0) > 0:
        return "tiny_loss_alias_focus_formatting_sensitive_signal"
    return "contrast_only_not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source reports were missing or structurally failing."
    if summary.get("focus_stable_strict_full"):
        return "Focused repair reached strict full coverage."
    if summary.get("focus_stable_normalized_full") and int(summary.get("normalization_gain_delta") or 0) > 0:
        return "The stability source had no normalized full delta, while focus produced a normalized full signal."
    if int(summary.get("normalization_gain_delta") or 0) > 0:
        return "The focused run increased formatting-sensitive normalized hits, but not enough for full coverage."
    return "The focused run did not add a new normalized or strict signal over the stability source."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair source reports before comparing loss-alias metric stages"
    if summary.get("focus_stable_strict_full"):
        return "recombine loss aliases with fixed aliases and test whether strict recovery survives"
    if summary.get("focus_stable_normalized_full") and int(summary.get("normalization_gain_delta") or 0) > 0:
        return "inspect decoding or tokenization shape before treating normalized full signal as strict recovery"
    return "change training shape only after the contrast explains whether the issue is semantic or formatting-sensitive"
