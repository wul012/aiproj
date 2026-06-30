from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (
    CONTRACT_SUMMARY_JSON_FILENAME,
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_rows import (
    check_rows,
    check_summary_sidecars,
    contract_profile_checks as build_contract_profile_checks,
    contract_profile_issues,
    failed_check_count,
    missing_sidecars,
    summary_check_failed_targets,
    summary_check_family_summary,
    summary_field_checks as build_summary_field_checks,
    summary_field_issues,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_render import (
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text,
)
from minigpt.report_utils import archived_reference_path, string_list


CONTRACT_SUMMARY_CHECK_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.json"
CONTRACT_SUMMARY_CHECK_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt"
CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.md"
CONTRACT_SUMMARY_CHECK_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.html"

SUMMARY_COMPARE_KEYS = (
    "contract_summary_version",
    "status",
    "decision",
    "checker_exit_code",
    "handoff_report_path",
    "receipt_schema_version",
    "schema_v3_ready",
    "schema_v4_ready",
    "schema_v5_ready",
    "assurance_status",
    "embedded_receipt_check_status",
    "embedded_receipt_check_sidecar_status",
    "main_embedded_receipt_check_status",
    "receipt_check_output_json_exists",
    "receipt_check_output_text_exists",
    "suite_design_scopes",
    "ci_boundary_plan_check_scopes",
    "ci_reason_count_scopes",
    "contract_checks",
    "contract_check_count",
    "failed_contract_check_count",
    "contract_check_status_counts",
    "contract_check_type_summary",
    "issue_count",
    "issues",
)


def check_promoted_training_scale_seed_handoff_receipt_contract_summary(
    summary_path: str | Path,
    *,
    handoff_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_summary_path = resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(summary_path)
    actual = load_promoted_training_scale_seed_handoff_receipt_contract_summary(resolved_summary_path)
    source_path = Path(handoff_path) if handoff_path is not None else _handoff_path_from_summary(actual)
    issues: list[str] = []
    expected: dict[str, Any] = {}
    summary_field_checks: list[dict[str, Any]] = []
    contract_profile_checks = build_contract_profile_checks(actual)
    issues.extend(contract_profile_issues(contract_profile_checks))
    if source_path is None:
        issues.append("handoff report path is required for receipt contract summary check")
    else:
        try:
            expected = build_promoted_training_scale_seed_handoff_receipt_contract_summary(source_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"could not rebuild receipt contract summary from handoff path: {exc}")
    if expected:
        summary_field_checks = build_summary_field_checks(expected, actual, SUMMARY_COMPARE_KEYS)
        issues.extend(summary_field_issues(summary_field_checks))
        sidecars = check_summary_sidecars(resolved_summary_path.parent, expected)
    else:
        sidecars = missing_sidecars(resolved_summary_path.parent)
    sidecar_checks = check_rows(sidecars.get("checks"))
    issues.extend(string_list(sidecars.get("issues")))
    family_summary = summary_check_family_summary(summary_field_checks, contract_profile_checks, sidecar_checks)
    failed_targets = summary_check_failed_targets(summary_field_checks, contract_profile_checks, sidecar_checks)
    status = "pass" if not issues else "fail"
    decision = str((expected or actual).get("decision") or "")
    return {
        "summary_check_version": 1,
        "status": status,
        "decision": decision,
        "checker_exit_code": 0 if status == "pass" and decision == "continue" else 1,
        "summary_path": str(resolved_summary_path),
        "handoff_path": str(source_path) if source_path is not None else None,
        "actual_summary_status": actual.get("status"),
        "expected_summary_status": expected.get("status") if expected else None,
        "actual_schema_version": actual.get("receipt_schema_version"),
        "expected_schema_version": expected.get("receipt_schema_version") if expected else None,
        "summary_field_check_count": len(summary_field_checks),
        "failed_summary_field_check_count": failed_check_count(summary_field_checks),
        "summary_field_checks": summary_field_checks,
        "contract_profile_status": "pass" if failed_check_count(contract_profile_checks) == 0 else "fail",
        "contract_profile_check_count": len(contract_profile_checks),
        "failed_contract_profile_check_count": failed_check_count(contract_profile_checks),
        "contract_profile_checks": contract_profile_checks,
        "sidecar_status": sidecars.get("status"),
        "sidecar_check_count": len(sidecar_checks),
        "failed_sidecar_check_count": failed_check_count(sidecar_checks),
        "sidecar_checks": sidecar_checks,
        "check_family_summary": family_summary,
        "failed_check_target_count": len(failed_targets),
        "failed_check_targets": failed_targets,
        "sidecar_issue_count": sidecars.get("issue_count"),
        "sidecar_issues": sidecars.get("issues"),
        "text_path": sidecars.get("text_path"),
        "text_exists": sidecars.get("text_exists"),
        "markdown_path": sidecars.get("markdown_path"),
        "markdown_exists": sidecars.get("markdown_exists"),
        "html_path": sidecars.get("html_path"),
        "html_exists": sidecars.get("html_exists"),
        "issue_count": len(issues),
        "issues": issues,
        "actual_summary": actual,
        "expected_summary": expected,
    }


def load_promoted_training_scale_seed_handoff_receipt_contract_summary(path: str | Path) -> dict[str, Any]:
    payload = json.loads(
        resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path).read_text(
            encoding="utf-8-sig"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("receipt contract summary must be a JSON object")
    return dict(payload)


def resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / CONTRACT_SUMMARY_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CONTRACT_SUMMARY_CHECK_JSON_FILENAME,
        "text": root / CONTRACT_SUMMARY_CHECK_TEXT_FILENAME,
        "markdown": root / CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME,
        "html": root / CONTRACT_SUMMARY_CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _handoff_path_from_summary(summary: dict[str, Any]) -> Path | None:
    value = summary.get("handoff_report_path")
    return archived_reference_path(value) if value else None


__all__ = [
    "CONTRACT_SUMMARY_CHECK_HTML_FILENAME",
    "CONTRACT_SUMMARY_CHECK_JSON_FILENAME",
    "CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME",
    "CONTRACT_SUMMARY_CHECK_TEXT_FILENAME",
    "check_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "load_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text",
    "resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path",
    "write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs",
]
