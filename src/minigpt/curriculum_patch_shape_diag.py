from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME = (
    "bounded_objective_curriculum_patch_shape_migration_diagnostic.json"
)
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_CSV_FILENAME = (
    "bounded_objective_curriculum_patch_shape_migration_diagnostic.csv"
)
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_TEXT_FILENAME = (
    "bounded_objective_curriculum_patch_shape_migration_diagnostic.txt"
)
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "bounded_objective_curriculum_patch_shape_migration_diagnostic.md"
)
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_HTML_FILENAME = (
    "bounded_objective_curriculum_patch_shape_migration_diagnostic.html"
)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def locate_seed_revision_replay_comparison(path: str | Path) -> Path:
    return _locate(path, BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME)


def locate_curriculum_patch_replay_comparison(path: str | Path) -> Path:
    return _locate(path, BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_REPLAY_COMPARISON_JSON_FILENAME)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic(
    seed_revision_replay: dict[str, Any],
    curriculum_patch_replay: dict[str, Any],
    *,
    seed_revision_replay_path: str | Path | None = None,
    curriculum_patch_replay_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision curriculum patch shape migration diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    seed_summary = as_dict(seed_revision_replay.get("summary"))
    patch_summary = as_dict(curriculum_patch_replay.get("summary"))
    seed_rows = list_of_dicts(seed_revision_replay.get("replay_rows"))
    patch_rows = list_of_dicts(curriculum_patch_replay.get("replay_rows"))
    migration_rows = _migration_rows(seed_rows, patch_rows)
    checks = _checks(seed_revision_replay, seed_summary, curriculum_patch_replay, patch_summary, seed_rows, patch_rows, migration_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    root_causes = _root_causes(migration_rows, patch_summary)
    summary = _summary(status, migration_rows, seed_summary, patch_summary, root_causes)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_seed_revision_replay_comparison": str(seed_revision_replay_path or ""),
        "source_curriculum_patch_replay_comparison": str(curriculum_patch_replay_path or ""),
        "seed_revision_replay_summary": seed_summary,
        "curriculum_patch_replay_summary": patch_summary,
        "migration_rows": migration_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary, root_causes),
    }


def _migration_rows(seed_rows: list[dict[str, Any]], patch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patch_by_case = {str(row.get("case_id") or ""): row for row in patch_rows}
    rows: list[dict[str, Any]] = []
    for seed_row in seed_rows:
        case_id = str(seed_row.get("case_id") or "")
        patch_row = patch_by_case.get(case_id, {})
        pre_hit = _terms(seed_row.get("hit_terms"))
        post_hit = _terms(patch_row.get("hit_terms"))
        pre_missed = _terms(seed_row.get("missed_terms"))
        post_missed = _terms(patch_row.get("missed_terms"))
        rows.append(
            {
                "case_id": case_id,
                "pre_case_pass": seed_row.get("case_pass") is True,
                "post_case_pass": patch_row.get("case_pass") is True,
                "pre_any_hit": seed_row.get("any_hit") is True,
                "post_any_hit": patch_row.get("any_hit") is True,
                "pre_hit_terms": pre_hit,
                "post_hit_terms": post_hit,
                "pre_missed_terms": pre_missed,
                "post_missed_terms": post_missed,
                "pre_continuation": str(seed_row.get("continuation") or ""),
                "post_continuation": str(patch_row.get("continuation") or ""),
                "migration_class": _migration_class(seed_row, patch_row, pre_hit, post_hit, pre_missed, post_missed),
            }
        )
    return rows


def _migration_class(seed_row: dict[str, Any], patch_row: dict[str, Any], pre_hit: list[str], post_hit: list[str], pre_missed: list[str], post_missed: list[str]) -> str:
    if not patch_row:
        return "missing_post_case"
    pre_pass = seed_row.get("case_pass") is True
    post_pass = patch_row.get("case_pass") is True
    if post_pass and not pre_pass:
        return "recovered_case"
    if pre_pass and not post_pass:
        return "lost_case"
    if len(post_hit) > len(pre_hit):
        return "improved_to_partial"
    if len(post_hit) < len(pre_hit):
        return "regressed_to_zero"
    if pre_hit == post_hit and pre_missed == post_missed:
        return "stable_partial" if post_hit and post_missed else "stable_zero"
    return "changed_same_hit_count"


def _checks(
    seed_replay: dict[str, Any],
    seed_summary: dict[str, Any],
    patch_replay: dict[str, Any],
    patch_summary: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    patch_rows: list[dict[str, Any]],
    migration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seed_ids = sorted(str(row.get("case_id") or "") for row in seed_rows)
    patch_ids = sorted(str(row.get("case_id") or "") for row in patch_rows)
    return [
        _check("seed_revision_replay_passed", seed_replay.get("status") == "pass", seed_replay.get("status"), "seed revision replay must pass structurally"),
        _check(
            "seed_revision_replay_ready",
            seed_summary.get("bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready") is True,
            seed_summary.get("bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready"),
            "seed revision replay must be ready",
        ),
        _check("curriculum_patch_replay_passed", patch_replay.get("status") == "pass", patch_replay.get("status"), "curriculum patch replay must pass structurally"),
        _check(
            "curriculum_patch_replay_ready",
            patch_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready") is True,
            patch_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_ready"),
            "curriculum patch replay must be ready",
        ),
        _check("same_case_ids", seed_ids == patch_ids and bool(seed_ids), {"seed": seed_ids, "patch": patch_ids}, "both replays must cover the same non-empty contract cases"),
        _check("post_cases_not_missing", not any(row["migration_class"] == "missing_post_case" for row in migration_rows), [row["case_id"] for row in migration_rows if row["migration_class"] == "missing_post_case"], "every seed revision case needs a post-patch row"),
    ]


def _root_causes(migration_rows: list[dict[str, Any]], patch_summary: dict[str, Any]) -> list[dict[str, Any]]:
    causes: list[dict[str, Any]] = []
    improved = [row["case_id"] for row in migration_rows if row["migration_class"] == "improved_to_partial"]
    regressed = [row["case_id"] for row in migration_rows if row["migration_class"] == "regressed_to_zero"]
    loss_missing = [row["case_id"] for row in migration_rows if "loss" in row["post_missed_terms"]]
    if improved and regressed:
        causes.append(_cause("summary_masked_case_migration", "high", "Aggregate any-hit counts stayed flat while case-level surfaces moved in opposite directions.", improved + regressed))
    if improved:
        causes.append(_cause("completion_surface_fixed_only_improved", "medium", "At least one post-patch surface gained the `fixed` term but still missed `loss`.", improved))
    if regressed:
        causes.append(_cause("minimal_surface_regressed_to_zero_hit", "high", "At least one previously partial-hit surface became zero-hit after the curriculum patch.", regressed))
    if loss_missing:
        causes.append(_cause("loss_term_still_missing_after_patch", "high", "`loss` remains absent from post-patch replay continuations.", loss_missing))
    if patch_summary.get("objective_contract_recovered") is not True:
        causes.append(_cause("contract_not_recovered", "high", "No case-level migration is enough to recover the bounded objective contract.", []))
    return causes


def _summary(status: str, rows: list[dict[str, Any]], seed_summary: dict[str, Any], patch_summary: dict[str, Any], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    classes = [row["migration_class"] for row in rows]
    return {
        "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready": status == "pass",
        "case_count": len(rows),
        "improved_case_count": classes.count("improved_to_partial"),
        "regressed_case_count": classes.count("regressed_to_zero"),
        "stable_case_count": sum(1 for item in classes if item.startswith("stable_")),
        "stable_partial_case_count": classes.count("stable_partial"),
        "recovered_case_count": classes.count("recovered_case"),
        "lost_case_count": classes.count("lost_case"),
        "pre_any_hit_case_count": int(seed_summary.get("any_hit_case_count") or 0),
        "post_any_hit_case_count": int(patch_summary.get("any_hit_case_count") or 0),
        "any_hit_case_delta": int(patch_summary.get("any_hit_case_count") or 0) - int(seed_summary.get("any_hit_case_count") or 0),
        "pre_zero_hit_case_count": int(seed_summary.get("zero_hit_case_count") or 0),
        "post_zero_hit_case_count": int(patch_summary.get("zero_hit_case_count") or 0),
        "zero_hit_case_delta": int(patch_summary.get("zero_hit_case_count") or 0) - int(seed_summary.get("zero_hit_case_count") or 0),
        "passed_case_delta": int(patch_summary.get("passed_case_count") or 0) - int(seed_summary.get("passed_case_count") or 0),
        "loss_missed_after_count": sum(1 for row in rows if "loss" in row["post_missed_terms"]),
        "fixed_missed_after_count": sum(1 for row in rows if "fixed" in row["post_missed_terms"]),
        "objective_contract_recovered_after": patch_summary.get("objective_contract_recovered") is True,
        "root_cause_count": len(root_causes),
        "model_quality_claim": "partial_signal_shape_migration_without_contract_recovery",
        "next_action": "run_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_profile_sweep_before_more_training",
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_blocked"
    if summary.get("objective_contract_recovered_after") is True:
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_contract_recovered_holdout_required"
    if int(summary.get("improved_case_count") or 0) or int(summary.get("regressed_case_count") or 0):
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnosed_profile_sweep_required"
    return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_no_case_progress"


def _interpretation(status: str, summary: dict[str, Any], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    if status != "pass":
        reason = "The two replay reports could not be compared structurally."
    elif summary.get("objective_contract_recovered_after") is True:
        reason = "The curriculum patch recovered all bounded objective cases; holdout replay is required before promotion."
    else:
        reason = "The curriculum patch changed which prompt surfaces show partial signal, but it did not recover `fixed loss`."
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": reason,
        "root_cause_ids": [row["cause_id"] for row in root_causes],
        "next_action": summary.get("next_action"),
    }


def _locate(path: str | Path, filename: str) -> Path:
    candidate = Path(path)
    if candidate.is_file():
        return candidate
    nested = candidate / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {candidate}")


def _terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(term).lower() for term in value)


def _cause(cause_id: str, severity: str, detail: str, evidence: list[str]) -> dict[str, Any]:
    return {"cause_id": cause_id, "severity": severity, "detail": detail, "evidence": evidence}


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic",
    "locate_curriculum_patch_replay_comparison",
    "locate_seed_revision_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
