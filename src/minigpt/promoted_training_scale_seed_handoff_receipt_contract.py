from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_assurance import (
    check_promoted_training_scale_seed_handoff_assurance,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_context import (
    ci_boundary_plan_check_scopes,
    ci_reason_count_scopes,
    contract_issues,
    int_value,
    suite_design_scopes,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_render import (
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_rows import (
    build_contract_checks,
    contract_check_status_counts,
    contract_check_type_summary,
    failed_contract_check_count,
)


CONTRACT_SUMMARY_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.json"
CONTRACT_SUMMARY_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.txt"
CONTRACT_SUMMARY_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.md"
CONTRACT_SUMMARY_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary.html"


def build_promoted_training_scale_seed_handoff_receipt_contract_summary(path: str | Path) -> dict[str, Any]:
    assurance = check_promoted_training_scale_seed_handoff_assurance(path)
    scopes = suite_design_scopes(assurance)
    boundary_scopes = ci_boundary_plan_check_scopes(assurance)
    reason_scopes = ci_reason_count_scopes(assurance)
    contract_checks = build_contract_checks(assurance, scopes, boundary_scopes, reason_scopes)
    issues = contract_issues(assurance, scopes, boundary_scopes, reason_scopes)
    status = "pass" if not issues else "fail"
    decision = str(assurance.get("decision") or "")
    receipt_schema_version = int_value(assurance.get("embedded_receipt_check_receipt_schema_version"))
    return {
        "contract_summary_version": 1,
        "status": status,
        "decision": decision,
        "checker_exit_code": 0 if status == "pass" and decision == "continue" else 1,
        "handoff_report_path": assurance.get("handoff_report_path"),
        "receipt_schema_version": receipt_schema_version,
        "schema_v3_ready": receipt_schema_version >= 3,
        "schema_v4_ready": receipt_schema_version >= 4,
        "schema_v5_ready": receipt_schema_version >= 5,
        "assurance_status": assurance.get("status"),
        "embedded_receipt_check_status": assurance.get("embedded_receipt_check_status"),
        "embedded_receipt_check_sidecar_status": assurance.get("embedded_receipt_check_sidecar_status"),
        "main_embedded_receipt_check_status": assurance.get("main_embedded_receipt_check_status"),
        "receipt_check_output_json_exists": bool(assurance.get("embedded_receipt_check_output_json_exists")),
        "receipt_check_output_text_exists": bool(assurance.get("embedded_receipt_check_output_text_exists")),
        "suite_design_scopes": scopes,
        "ci_boundary_plan_check_scopes": boundary_scopes,
        "ci_reason_count_scopes": reason_scopes,
        "contract_checks": contract_checks,
        "contract_check_count": len(contract_checks),
        "failed_contract_check_count": failed_contract_check_count(contract_checks),
        "contract_check_status_counts": contract_check_status_counts(contract_checks),
        "contract_check_type_summary": contract_check_type_summary(contract_checks),
        "issue_count": len(issues),
        "issues": issues,
        "assurance": assurance,
    }


def write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(
    summary: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CONTRACT_SUMMARY_JSON_FILENAME,
        "text": root / CONTRACT_SUMMARY_TEXT_FILENAME,
        "markdown": root / CONTRACT_SUMMARY_MARKDOWN_FILENAME,
        "html": root / CONTRACT_SUMMARY_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(summary),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(summary),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(summary),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "CONTRACT_SUMMARY_HTML_FILENAME",
    "CONTRACT_SUMMARY_JSON_FILENAME",
    "CONTRACT_SUMMARY_MARKDOWN_FILENAME",
    "CONTRACT_SUMMARY_TEXT_FILENAME",
    "build_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_text",
    "write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs",
]
