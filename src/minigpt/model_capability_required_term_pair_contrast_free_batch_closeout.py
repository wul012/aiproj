from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.report_utils import as_dict, utc_now


PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_contrast_free_batch_closeout.json"
PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_contrast_free_batch_closeout.csv"
PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_contrast_free_batch_closeout.txt"
PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_contrast_free_batch_closeout.md"
PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_contrast_free_batch_closeout.html"
CONTRAST_FREE_CORPUS_CONTRACT_JSON_FILENAME = "model_capability_required_term_pair_contrast_free_objective_corpus_contract.json"


def locate_batch_report(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    direct = source / filename
    if direct.is_file():
        return direct
    matches = sorted(source.rglob(filename)) if source.is_dir() else []
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(f"missing {filename} under {source}")
    raise ValueError(f"ambiguous {filename} under {source}: {len(matches)} matches")


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("contrast-free batch closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_contrast_free_batch_closeout(
    *,
    corpus_contract: dict[str, Any],
    refresh_reports: Sequence[dict[str, Any]],
    comparison: dict[str, Any],
    route_decision: dict[str, Any],
    forced_choice: dict[str, Any],
    paths: dict[str, str | Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    resolved_paths = {key: str(value) for key, value in (paths or {}).items()}
    evidence_rows = _evidence_rows(corpus_contract, refresh_reports, comparison, route_decision, forced_choice, resolved_paths)
    summary = _summary(corpus_contract, refresh_reports, comparison, route_decision, forced_choice)
    issues = _issues(evidence_rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair contrast-free batch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "version_range": "v609-v618",
        "summary": summary,
        "evidence_rows": evidence_rows,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _evidence_rows(
    corpus_contract: dict[str, Any],
    refresh_reports: Sequence[dict[str, Any]],
    comparison: dict[str, Any],
    route_decision: dict[str, Any],
    forced_choice: dict[str, Any],
    paths: dict[str, str],
) -> list[dict[str, Any]]:
    rows = [
        _row("v610-corpus-contract", "corpus_contract", corpus_contract, paths, _contract_result),
    ]
    for index, report in enumerate(refresh_reports, start=611):
        rows.append(_row(f"v{index}-refresh", f"v{index}", report, paths, _refresh_result))
    rows.extend(
        [
            _row("v614-comparison", "comparison", comparison, paths, _comparison_result),
            _row("v615-route-decision", "route_decision", route_decision, paths, _route_result),
            _row("v617-forced-choice", "forced_choice", forced_choice, paths, _forced_choice_result),
        ]
    )
    return rows


def _row(label: str, key: str, report: dict[str, Any], paths: dict[str, str], key_result: Any) -> dict[str, Any]:
    return {
        "label": label,
        "path": paths.get(key, ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "key_result": key_result(report),
    }


def _summary(
    corpus_contract: dict[str, Any],
    refresh_reports: Sequence[dict[str, Any]],
    comparison: dict[str, Any],
    route_decision: dict[str, Any],
    forced_choice: dict[str, Any],
) -> dict[str, Any]:
    contract_summary = as_dict(corpus_contract.get("summary"))
    comparison_summary = as_dict(comparison.get("summary"))
    route_summary = as_dict(route_decision.get("summary"))
    forced_summary = as_dict(forced_choice.get("summary"))
    refresh_summaries = [as_dict(report.get("summary")) for report in refresh_reports]
    return {
        "new_mode_count": int(contract_summary.get("new_mode_count") or 0),
        "refresh_report_count": len(refresh_reports),
        "refresh_pair_full_count": sum(1 for summary in refresh_summaries if summary.get("pair_full_observed")),
        "all_refresh_training_passed": all(summary.get("training_status") == "pass" for summary in refresh_summaries),
        "comparison_pair_full_report_count": int(comparison_summary.get("pair_full_report_count") or 0),
        "comparison_union_hit_terms": [str(value) for value in comparison_summary.get("union_hit_terms", [])],
        "route_requires_forced_choice": bool(route_summary.get("requires_forced_choice_diagnostic")),
        "route_decision": route_decision.get("decision"),
        "forced_choice_expected_best_prompt_count": int(forced_summary.get("expected_best_prompt_count") or 0),
        "forced_choice_full_match_source_count": int(forced_summary.get("forced_choice_full_match_source_count") or 0),
        "forced_choice_best_internal_sources": [str(value) for value in forced_summary.get("best_internal_sources", [])],
        "closeout_ready": len(refresh_reports) == 3
        and int(comparison_summary.get("pair_full_report_count") or 0) == 0
        and route_decision.get("decision") == "stop_contrast_free_routes_and_run_forced_choice_diagnostic"
        and int(forced_summary.get("forced_choice_full_match_source_count") or 0) == 0,
    }


def _issues(evidence_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for row in evidence_rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('label')} status is not pass")
    if int(summary.get("new_mode_count") or 0) != 3:
        issues.append("contrast-free corpus contract does not define three modes")
    if int(summary.get("refresh_report_count") or 0) != 3:
        issues.append("three contrast-free refresh reports are required")
    if not summary.get("all_refresh_training_passed"):
        issues.append("not all contrast-free refresh runs trained successfully")
    if int(summary.get("comparison_pair_full_report_count") or 0) != 0:
        issues.append("comparison unexpectedly contains pair-full route")
    if not summary.get("route_requires_forced_choice"):
        issues.append("route decision does not require forced-choice diagnostic")
    if int(summary.get("forced_choice_full_match_source_count") or 0) != 0:
        issues.append("forced-choice diagnostic found a full internal match")
    if not summary.get("closeout_ready"):
        issues.append("contrast-free closeout is not ready")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_contrast_free_batch_closeout_inputs"
    return "close_contrast_free_batch_and_design_loss_internal_preference_objective"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The contrast-free batch evidence is incomplete or contradictory.",
            "next_action": "repair closeout inputs before new objective design",
        }
    return {
        "model_quality_claim": "negative_internal_preference_evidence",
        "reason": "Contrast-free routes did not reach pair-full and forced-choice scoring found no full internal match.",
        "next_action": "design a loss-internal-preference objective instead of more contrast-free variants",
    }


def _contract_result(report: dict[str, Any]) -> str:
    return f"modes={as_dict(report.get('summary')).get('new_mode_count')}"


def _refresh_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"pair_full={summary.get('pair_full_observed')}; training={summary.get('training_status')}"


def _comparison_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"pair_full={summary.get('pair_full_report_count')}; union={summary.get('union_hit_terms')}"


def _route_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"forced_choice={summary.get('requires_forced_choice_diagnostic')}"


def _forced_choice_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"full_match={summary.get('forced_choice_full_match_source_count')}; expected_best={summary.get('expected_best_prompt_count')}"


__all__ = [
    "CONTRAST_FREE_CORPUS_CONTRACT_JSON_FILENAME",
    "PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_CONTRAST_FREE_BATCH_CLOSEOUT_TEXT_FILENAME",
    "build_model_capability_required_term_pair_contrast_free_batch_closeout",
    "locate_batch_report",
    "read_json_report",
    "resolve_exit_code",
]
