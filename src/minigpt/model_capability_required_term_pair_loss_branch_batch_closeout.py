from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, utc_now


PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_loss_branch_batch_closeout.json"
PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_loss_branch_batch_closeout.csv"
PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_loss_branch_batch_closeout.txt"
PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_branch_batch_closeout.md"
PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_loss_branch_batch_closeout.html"
PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_CONTRACT_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_branch_objective_corpus_contract.json"
)


def locate_loss_branch_batch_report(path: str | Path, filename: str) -> Path:
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


def read_loss_branch_batch_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss branch batch closeout input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_loss_branch_batch_closeout(
    *,
    corpus_contract: dict[str, Any],
    targeted_seed: dict[str, Any],
    dual_anchor_seed: dict[str, Any],
    micro_span_seed: dict[str, Any],
    comparison: dict[str, Any],
    route_decision: dict[str, Any],
    stability: dict[str, Any],
    diagnostic: dict[str, Any],
    readiness: dict[str, Any],
    paths: dict[str, str | Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    resolved_paths = {key: str(value) for key, value in (paths or {}).items()}
    reports = {
        "corpus_contract": corpus_contract,
        "targeted_seed": targeted_seed,
        "dual_anchor_seed": dual_anchor_seed,
        "micro_span_seed": micro_span_seed,
        "comparison": comparison,
        "route_decision": route_decision,
        "stability": stability,
        "diagnostic": diagnostic,
        "readiness": readiness,
    }
    evidence_rows = _evidence_rows(reports, resolved_paths)
    summary = _summary(reports)
    issues = _issues(evidence_rows, summary)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair loss-branch ten-version closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "version_range": "v589-v598",
        "source_report_count": len(reports),
        "summary": summary,
        "evidence_rows": evidence_rows,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _evidence_rows(reports: dict[str, dict[str, Any]], paths: dict[str, str]) -> list[dict[str, Any]]:
    return [
        _row("v589-corpus-contract", "v589", "corpus_contract", reports, paths, _corpus_key_result),
        _row("v590-targeted-seed", "v590", "targeted_seed", reports, paths, _seed_key_result),
        _row("v591-dual-anchor-seed", "v591", "dual_anchor_seed", reports, paths, _seed_key_result),
        _row("v592-micro-span-seed", "v592", "micro_span_seed", reports, paths, _seed_key_result),
        _row("v593-objective-comparison", "v593", "comparison", reports, paths, _comparison_key_result),
        _row("v594-route-decision", "v594", "route_decision", reports, paths, _route_key_result),
        _row("v595-targeted-stability", "v595", "stability", reports, paths, _stability_key_result),
        _row("v596-missed-seed-diagnostic", "v596", "diagnostic", reports, paths, _diagnostic_key_result),
        _row("v597-fixed-retention-readiness", "v597", "readiness", reports, paths, _readiness_key_result),
    ]


def _row(
    label: str,
    version: str,
    key: str,
    reports: dict[str, dict[str, Any]],
    paths: dict[str, str],
    key_result: Any,
) -> dict[str, Any]:
    report = reports[key]
    return {
        "label": label,
        "version": version,
        "path": paths.get(key, ""),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "key_result": key_result(report),
    }


def _summary(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    corpus_summary = as_dict(reports["corpus_contract"].get("summary"))
    comparison_summary = as_dict(reports["comparison"].get("summary"))
    route_summary = as_dict(reports["route_decision"].get("summary"))
    stability_summary = as_dict(reports["stability"].get("summary"))
    diagnostic_summary = as_dict(reports["diagnostic"].get("summary"))
    readiness_summary = as_dict(reports["readiness"].get("summary"))
    seed_reports = [reports["targeted_seed"], reports["dual_anchor_seed"], reports["micro_span_seed"]]
    seed_summaries = [as_dict(report.get("summary")) for report in seed_reports]
    pair_full_single_seed_count = sum(1 for summary in seed_summaries if summary.get("pair_full_observed"))
    return {
        "corpus_modes_ready": reports["corpus_contract"].get("status") == "pass"
        and int(corpus_summary.get("new_mode_count") or 0) >= 3
        and bool(corpus_summary.get("pair_id_removed")),
        "new_corpus_mode_count": int(corpus_summary.get("new_mode_count") or 0),
        "single_seed_report_count": len(seed_reports),
        "single_seed_pair_full_count": pair_full_single_seed_count,
        "comparison_pair_full_report_count": int(comparison_summary.get("pair_full_report_count") or 0),
        "comparison_loss_only_tradeoff_report_count": int(
            comparison_summary.get("loss_only_tradeoff_report_count") or 0
        ),
        "comparison_union_hit_terms": [str(value) for value in comparison_summary.get("union_hit_terms", [])],
        "route_selected_stability_route": route_summary.get("selected_stability_route"),
        "route_fixed_retention_required": bool(route_summary.get("fixed_retention_objective_required")),
        "stability_seed_count": int(stability_summary.get("seed_count") or 0),
        "stability_pair_full_seed_count": int(stability_summary.get("pair_full_seed_count") or 0),
        "stability_stable_pair_full": bool(stability_summary.get("stable_pair_full")),
        "diagnostic_missed_seed_count": int(diagnostic_summary.get("missed_seed_count") or 0),
        "diagnostic_first_token_gap_count": int(diagnostic_summary.get("missed_first_token_gap_count") or 0),
        "readiness_fixed_retention_required": bool(readiness_summary.get("fixed_retention_objective_required")),
        "readiness_ready_for_design": bool(readiness_summary.get("ready_for_fixed_retention_objective_design")),
        "readiness_required_requirement_count": int(readiness_summary.get("required_requirement_count") or 0),
    }


def _issues(evidence_rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for row in evidence_rows:
        if row.get("status") != "pass":
            issues.append(f"{row.get('label')} status is not pass")
    if not summary.get("corpus_modes_ready"):
        issues.append("loss-branch corpus modes are not contract-ready")
    if summary.get("single_seed_pair_full_count") != 0:
        issues.append("single-seed loss-branch route unexpectedly reached pair-full")
    if summary.get("comparison_pair_full_report_count") != 0:
        issues.append("comparison contains pair-full loss-branch route")
    if summary.get("comparison_loss_only_tradeoff_report_count") != 3:
        issues.append("comparison did not confirm three loss-only tradeoff routes")
    if summary.get("comparison_union_hit_terms") != ["loss"]:
        issues.append("comparison union hit terms are not loss-only")
    if not summary.get("route_fixed_retention_required"):
        issues.append("route decision does not require fixed retention")
    if summary.get("stability_seed_count") != 3:
        issues.append("targeted stability did not run three seeds")
    if summary.get("stability_pair_full_seed_count") != 0:
        issues.append("targeted stability unexpectedly reached pair-full")
    if summary.get("diagnostic_missed_seed_count") != 3:
        issues.append("diagnostic did not inspect three missed seeds")
    if summary.get("diagnostic_first_token_gap_count") != 3:
        issues.append("diagnostic did not confirm first-token gap on all missed seeds")
    if not summary.get("readiness_ready_for_design"):
        issues.append("fixed-retention readiness is not ready for objective design")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_branch_closeout_inputs"
    if summary.get("readiness_ready_for_design"):
        return "close_loss_branch_batch_and_start_fixed_retention_objective"
    return "record_loss_branch_batch_without_promotion"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The loss-branch batch evidence is incomplete or contradictory.",
            "next_action": "repair closeout inputs before designing another corpus objective",
        }
    return {
        "model_quality_claim": "batch_closeout_only",
        "reason": "Three loss-branch objectives and three targeted seeds improved loss visibility but never reached pair-full.",
        "next_action": "build and train a fixed-retention objective with balanced first-token rows",
    }


def _corpus_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"modes={summary.get('new_mode_count')}; pair_id_removed={summary.get('pair_id_removed')}"


def _seed_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"pair_full={summary.get('pair_full_observed')}; training={summary.get('training_status')}"


def _comparison_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    terms = ",".join(str(value) for value in summary.get("union_hit_terms", []))
    return f"pair_full={summary.get('pair_full_report_count')}; loss_only={summary.get('loss_only_tradeoff_report_count')}; terms={terms}"


def _route_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"selected={summary.get('selected_stability_route')}; fixed_required={summary.get('fixed_retention_objective_required')}"


def _stability_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"pair_full_seeds={summary.get('pair_full_seed_count')}/{summary.get('seed_count')}; stable={summary.get('stable_pair_full')}"


def _diagnostic_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"missed={summary.get('missed_seed_count')}; first_token_gaps={summary.get('missed_first_token_gap_count')}"


def _readiness_key_result(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return f"ready={summary.get('ready_for_fixed_retention_objective_design')}; requirements={summary.get('required_requirement_count')}"


__all__ = [
    "PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_LOSS_BRANCH_BATCH_CLOSEOUT_TEXT_FILENAME",
    "PAIR_LOSS_BRANCH_OBJECTIVE_CORPUS_CONTRACT_JSON_FILENAME",
    "build_model_capability_required_term_pair_loss_branch_batch_closeout",
    "locate_loss_branch_batch_report",
    "read_loss_branch_batch_report",
    "resolve_exit_code",
]
