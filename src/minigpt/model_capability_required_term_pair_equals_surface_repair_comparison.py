from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from minigpt.model_capability_required_term_pair_colon_immediate_stability import PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME = "model_capability_required_term_pair_equals_surface_repair_comparison.json"
PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_CSV_FILENAME = "model_capability_required_term_pair_equals_surface_repair_comparison.csv"
PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_TEXT_FILENAME = "model_capability_required_term_pair_equals_surface_repair_comparison.txt"
PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_MARKDOWN_FILENAME = "model_capability_required_term_pair_equals_surface_repair_comparison.md"
PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_HTML_FILENAME = "model_capability_required_term_pair_equals_surface_repair_comparison.html"

TARGET_TERMS = ("fixed", "loss")


def locate_pair_equals_surface_repair_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COLON_IMMEDIATE_STABILITY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("equals-surface repair comparison input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_equals_surface_repair_comparison(
    reports: Sequence[dict[str, Any]],
    *,
    source_paths: Sequence[str | Path] | None = None,
    source_labels: Sequence[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = [str(path) for path in source_paths] if source_paths is not None else []
    labels = [str(label) for label in source_labels] if source_labels is not None else []
    report_rows = [_report_row(index, report, _source_path(paths, index), _source_label(labels, index, report, paths)) for index, report in enumerate(reports)]
    term_rows = [row for index, report in enumerate(reports) for row in _term_rows(report_rows[index], report)]
    branch_rows = _branch_rows(report_rows, term_rows)
    issues = _input_issues(report_rows, term_rows)
    summary = _summary(report_rows, term_rows, branch_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair equals-surface repair comparison",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_reports": report_rows,
        "term_rows": term_rows,
        "branch_rows": branch_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _source_path(paths: Sequence[str], index: int) -> str:
    return paths[index] if index < len(paths) else ""


def _source_label(labels: Sequence[str], index: int, report: dict[str, Any], paths: Sequence[str]) -> str:
    if index < len(labels) and labels[index]:
        return labels[index]
    corpus_mode = str(as_dict(report.get("settings")).get("corpus_mode") or "")
    if corpus_mode:
        return corpus_mode
    if index < len(paths) and paths[index]:
        return Path(paths[index]).parent.name
    return f"report-{index + 1}"


def _report_row(index: int, report: dict[str, Any], source_path: str, source_label: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    return {
        "index": index,
        "source_label": source_label,
        "source_path": source_path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "seed_count": summary.get("seed_count"),
        "pair_full_seed_count": summary.get("pair_full_seed_count"),
        "pair_full_seed_rate": summary.get("pair_full_seed_rate"),
        "stable_pair_full": summary.get("stable_pair_full"),
    }


def _term_rows(report_row: dict[str, Any], report: dict[str, Any]) -> list[dict[str, Any]]:
    seed_rows = list_of_dicts(report.get("seed_rows"))
    seed_reports = list_of_dicts(report.get("seed_reports"))
    rows: list[dict[str, Any]] = []
    for index, seed_report in enumerate(seed_reports):
        seed = _seed_value(seed_rows, index, seed_report)
        replay = as_dict(seed_report.get("replay_report"))
        for case in list_of_dicts(replay.get("case_rows")):
            term = str(case.get("term") or "")
            if term not in TARGET_TERMS:
                continue
            rows.append(
                {
                    "source_label": report_row.get("source_label"),
                    "source_path": report_row.get("source_path"),
                    "corpus_mode": report_row.get("corpus_mode"),
                    "seed": seed,
                    "profile_id": case.get("profile_id"),
                    "term": term,
                    "prompt": case.get("prompt"),
                    "continuation_hit": bool(case.get("continuation_hit")),
                    "newline_cleanup_hit": bool(case.get("newline_cleanup_hit")),
                    "blocked_token_count": int(case.get("blocked_token_count") or 0),
                    "generated_preview": case.get("generated_preview"),
                    "continuation_preview": case.get("continuation_preview"),
                }
            )
    return rows


def _seed_value(seed_rows: list[dict[str, Any]], index: int, seed_report: dict[str, Any]) -> int | str:
    if index < len(seed_rows) and seed_rows[index].get("seed") is not None:
        return seed_rows[index].get("seed")
    settings = as_dict(seed_report.get("settings"))
    if settings.get("seed") is not None:
        return settings.get("seed")
    return index + 1


def _branch_rows(report_rows: list[dict[str, Any]], term_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seeds = sorted({str(row.get("seed")) for row in term_rows if row.get("seed") is not None})
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        scoped = [row for row in term_rows if str(row.get("seed")) == seed]
        fixed_hit_reports = _hit_reports(scoped, "fixed")
        loss_hit_reports = _hit_reports(scoped, "loss")
        pair_full_profile_reports = _pair_full_profile_reports(scoped)
        compared_reports = sorted({str(row.get("source_label")) for row in scoped})
        union_hit_terms = [term for term in TARGET_TERMS if _hit_reports(scoped, term)]
        branch_competition = len(union_hit_terms) == len(TARGET_TERMS) and not pair_full_profile_reports
        rows.append(
            {
                "seed": seed,
                "compared_report_count": len(compared_reports),
                "compared_reports": compared_reports,
                "fixed_hit_reports": fixed_hit_reports,
                "loss_hit_reports": loss_hit_reports,
                "union_hit_terms": union_hit_terms,
                "pair_full_profile_reports": pair_full_profile_reports,
                "branch_competition": branch_competition,
                "best_next_action": _branch_next_action(branch_competition, pair_full_profile_reports),
            }
        )
    if not rows and report_rows:
        return [
            {
                "seed": "",
                "compared_report_count": len(report_rows),
                "compared_reports": [str(row.get("source_label")) for row in report_rows],
                "fixed_hit_reports": [],
                "loss_hit_reports": [],
                "union_hit_terms": [],
                "pair_full_profile_reports": [],
                "branch_competition": False,
                "best_next_action": "repair missing term-level case rows before comparing equals-surface repairs",
            }
        ]
    return rows


def _hit_reports(rows: list[dict[str, Any]], term: str) -> list[str]:
    return sorted({str(row.get("source_label")) for row in rows if row.get("term") == term and row.get("continuation_hit")})


def _pair_full_profile_reports(rows: list[dict[str, Any]]) -> list[str]:
    grouped: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        if not row.get("continuation_hit"):
            continue
        key = (str(row.get("source_label")), str(row.get("profile_id")))
        grouped.setdefault(key, set()).add(str(row.get("term")))
    return sorted({label for (label, _profile), terms in grouped.items() if set(TARGET_TERMS).issubset(terms)})


def _branch_next_action(branch_competition: bool, pair_full_profile_reports: list[str]) -> str:
    if pair_full_profile_reports:
        return "promote the pair-full repair report and test fresh held-out prompts"
    if branch_competition:
        return "tie fixed/loss branches in one objective or isolate branch prompts before another full seed sweep"
    return "collect another comparable equals-surface repair report before changing the objective"


def _input_issues(report_rows: list[dict[str, Any]], term_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(report_rows) < 2:
        issues.append("at least two repair reports are required for comparison")
    for row in report_rows:
        label = row.get("source_label")
        if row.get("status") != "pass":
            issues.append(f"{label} report status is not pass")
        if "equals_surface" not in str(row.get("corpus_mode") or ""):
            issues.append(f"{label} report is not an equals-surface corpus mode")
    if not term_rows:
        issues.append("no fixed/loss term case rows were found")
    return issues


def _summary(report_rows: list[dict[str, Any]], term_rows: list[dict[str, Any]], branch_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pair_full_report_count = sum(1 for row in report_rows if int(row.get("pair_full_seed_count") or 0) > 0)
    branch_competition_seed_count = sum(1 for row in branch_rows if row.get("branch_competition"))
    pair_full_profile_seed_count = sum(1 for row in branch_rows if row.get("pair_full_profile_reports"))
    union_hit_terms = sorted({str(term) for row in branch_rows for term in row.get("union_hit_terms", [])})
    return {
        "compared_report_count": len(report_rows),
        "term_case_row_count": len(term_rows),
        "compared_seed_count": len(branch_rows),
        "branch_competition_seed_count": branch_competition_seed_count,
        "pair_full_report_count": pair_full_report_count,
        "pair_full_profile_seed_count": pair_full_profile_seed_count,
        "union_hit_terms": union_hit_terms,
        "union_hit_term_count": len(union_hit_terms),
        "all_target_terms_seen": set(TARGET_TERMS).issubset(set(union_hit_terms)),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_equals_surface_repair_comparison_input"
    if int(summary.get("branch_competition_seed_count") or 0) > 0:
        return "required_term_pair_equals_surface_branch_competition_detected"
    if int(summary.get("pair_full_profile_seed_count") or 0) > 0:
        return "required_term_pair_equals_surface_pair_full_found"
    return "required_term_pair_equals_surface_repair_comparison_recorded"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The source reports are not structurally comparable.",
            "next_action": "repair comparison inputs before planning another equals-surface training run",
        }
    if int(summary.get("branch_competition_seed_count") or 0) > 0:
        return {
            "model_quality_claim": "diagnostic_only",
            "reason": "The compared repairs cover fixed and loss across runs, but no single run/profile keeps both terms together.",
            "next_action": "tie the two branches in one objective or isolate prompt branches before spending more seed budget",
        }
    if int(summary.get("pair_full_profile_seed_count") or 0) > 0:
        return {
            "model_quality_claim": "targeted_equals_surface_pair_full_signal",
            "reason": "At least one compared repair report produced a pair-full profile.",
            "next_action": "promote that repair candidate into held-out replay before changing the corpus again",
        }
    return {
        "model_quality_claim": "comparison_only",
        "reason": "The compared reports do not yet show complementary fixed/loss evidence.",
        "next_action": "add one stronger targeted repair or reduce the comparison scope",
    }


__all__ = [
    "PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_CSV_FILENAME",
    "PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_HTML_FILENAME",
    "PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_JSON_FILENAME",
    "PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_MARKDOWN_FILENAME",
    "PAIR_EQUALS_SURFACE_REPAIR_COMPARISON_TEXT_FILENAME",
    "build_model_capability_required_term_pair_equals_surface_repair_comparison",
    "locate_pair_equals_surface_repair_report",
    "read_json_report",
    "resolve_exit_code",
]
