from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs,
)
from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check import (
    check_promoted_training_scale_seed_handoff_receipt_contract_summary,
    write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs,
)


CONTRACT_SMOKE_OUTPUT_KEYS = (
    "receipt_contract_summary_json",
    "receipt_contract_summary_text",
    "receipt_contract_summary_markdown",
    "receipt_contract_summary_html",
    "receipt_contract_summary_check_json",
    "receipt_contract_summary_check_text",
    "receipt_contract_summary_check_markdown",
    "receipt_contract_summary_check_html",
)


def build_receipt_contract_smoke_checks(
    *,
    handoff_dir: str | Path,
    contract_summary_dir: str | Path,
    contract_summary_check_dir: str | Path,
    base_dir: str | Path,
) -> tuple[dict[str, object], list[str]]:
    contract_summary = build_promoted_training_scale_seed_handoff_receipt_contract_summary(handoff_dir)
    contract_summary_outputs = write_promoted_training_scale_seed_handoff_receipt_contract_summary_outputs(
        contract_summary,
        contract_summary_dir,
    )
    contract_summary_check = check_promoted_training_scale_seed_handoff_receipt_contract_summary(contract_summary_dir)
    contract_summary_check_outputs = write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(
        contract_summary_check,
        contract_summary_check_dir,
    )
    checks: dict[str, object] = {
        "receipt_contract_status": contract_summary.get("status"),
        "receipt_contract_decision": contract_summary.get("decision"),
        "receipt_contract_schema_version": contract_summary.get("receipt_schema_version"),
        "receipt_contract_sidecar_status": contract_summary.get("embedded_receipt_check_sidecar_status"),
        "receipt_contract_issue_count": contract_summary.get("issue_count"),
        "receipt_contract_summary_json": contract_summary_outputs.get("json"),
        "receipt_contract_summary_text": contract_summary_outputs.get("text"),
        "receipt_contract_summary_markdown": contract_summary_outputs.get("markdown"),
        "receipt_contract_summary_html": contract_summary_outputs.get("html"),
        "receipt_contract_summary_check_status": contract_summary_check.get("status"),
        "receipt_contract_summary_check_decision": contract_summary_check.get("decision"),
        "receipt_contract_summary_check_sidecar_status": contract_summary_check.get("sidecar_status"),
        "receipt_contract_summary_check_issue_count": contract_summary_check.get("issue_count"),
        "receipt_contract_summary_check_json": contract_summary_check_outputs.get("json"),
        "receipt_contract_summary_check_text": contract_summary_check_outputs.get("text"),
        "receipt_contract_summary_check_markdown": contract_summary_check_outputs.get("markdown"),
        "receipt_contract_summary_check_html": contract_summary_check_outputs.get("html"),
    }
    issues: list[str] = []
    _check(checks["receipt_contract_status"] == "pass", "receipt contract summary status must pass", issues)
    _check(checks["receipt_contract_decision"] == "continue", "receipt contract summary decision must continue", issues)
    _check(checks["receipt_contract_schema_version"] == 3, "receipt contract summary schema must be v3", issues)
    _check(checks["receipt_contract_sidecar_status"] == "pass", "receipt contract sidecar status must pass", issues)
    _check(checks["receipt_contract_issue_count"] == 0, "receipt contract summary must have no issues", issues)
    _check(
        checks["receipt_contract_summary_check_status"] == "pass",
        "receipt contract summary check status must pass",
        issues,
    )
    _check(
        checks["receipt_contract_summary_check_decision"] == "continue",
        "receipt contract summary check decision must continue",
        issues,
    )
    _check(
        checks["receipt_contract_summary_check_sidecar_status"] == "pass",
        "receipt contract summary check sidecar status must pass",
        issues,
    )
    _check(
        checks["receipt_contract_summary_check_issue_count"] == 0,
        "receipt contract summary check must have no issues",
        issues,
    )
    for key in CONTRACT_SMOKE_OUTPUT_KEYS:
        _check(_is_file_reference(checks[key], Path(base_dir)), f"{key} must be a file", issues)
    return checks, issues


def _check(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def _is_file_reference(value: object, base_dir: Path) -> bool:
    if not value:
        return False
    candidate = Path(str(value))
    if candidate.is_file():
        return True
    if candidate.is_absolute():
        return False
    return (base_dir / candidate).is_file()


__all__ = [
    "CONTRACT_SMOKE_OUTPUT_KEYS",
    "build_receipt_contract_smoke_checks",
]
