"""Shared scaffolding for the upstream-artifact *check* modules.

The grokking-audit family — ``grok_evidence_check_v1180``,
``grok_trajectory_phases_v1181``, ``grok_paired_contrast_v1182``,
``grok_wd_law_check_v1184`` — each re-implemented the same three primitives,
byte-for-byte: a check-row builder, a failures collector, and a require-pass
exit-code resolver. This module is their single home (extracted in the v1187
maintenance pass, the v1159/v1163/v1167/v1171/v1174/v1176 cadence — add one
helper, migrate only the current active callers, leave others untouched).

Contract-preserving by construction: each function reproduces the prior inline
behavior exactly, and each migrated module keeps its public names (``_check``
via an aliased import, ``resolve_exit_code`` re-exported). Deliberately NOT
migrated yet: the PTQ check family (v1177/v1178) predates this pattern and uses
its own loaders; it can adopt these helpers later, same restraint as v1171
leaving the dual-corpus driver alone.
"""

from __future__ import annotations

from typing import Any

from minigpt.report_utils import as_dict


def check_row(check_id: str, passed: bool, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    """One structured check row. Identical to the ``_check`` helper that the
    v1180-v1184 audit modules each defined inline."""
    return {"id": check_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual, "detail": detail}


def collect_failures(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The check rows whose status is not ``pass`` (drives ``failed_count`` /
    ``issues`` and the report ``status``)."""
    return [check for check in checks if check.get("status") != "pass"]


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    """Return 1 iff ``--require-pass`` is set and the report did not pass — the
    CI-friendly exit code shared by every check CLI."""
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def check_entry(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    """The 4-field check row (no ``expected``) that hundreds of governance
    modules defined inline as ``_check``."""
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}

def check_entry_no_detail(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    """The 3-field variant of :func:`check_entry`."""
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}

def resolve_exit_code_strict(report: dict[str, Any], *, require_pass: bool) -> int:
    """:func:`resolve_exit_code` with ``require_pass`` required, matching the
    strict inline signature most check CLIs carried."""
    if require_pass and report.get("status") != "pass":
        return 1
    return 0

def resolve_exit_code_diagnostic_ready(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_diagnostic_ready``)."""
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0

def resolve_exit_code_training_ready(report: dict[str, Any], *, require_training_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_training_ready``)."""
    return 1 if require_training_ready and report.get("status") != "pass" else 0

def resolve_exit_code_patch_ready(report: dict[str, Any], *, require_patch_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_patch_ready``)."""
    return 1 if require_patch_ready and report.get("status") != "pass" else 0

def resolve_exit_code_dry_run_ready(report: dict[str, Any], *, require_dry_run_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_dry_run_ready``)."""
    return 1 if require_dry_run_ready and report.get("status") != "pass" else 0

def resolve_exit_code_suite_ready(report: dict[str, Any], *, require_suite_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_suite_ready``)."""
    return 1 if require_suite_ready and report.get("status") != "pass" else 0

def resolve_exit_code_seed_ready(report: dict[str, Any], *, require_seed_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_seed_ready``)."""
    return 1 if require_seed_ready and report.get("status") != "pass" else 0

def resolve_exit_code_plan_ready(report: dict[str, Any], *, require_plan_ready: bool) -> int:
    """Keyword-specific exit-code resolver (``--require-pass`` CLIs pass
    ``require_plan_ready``)."""
    return 1 if require_plan_ready and report.get("status") != "pass" else 0

def resolve_exit_code_comparison_objective(
    report: dict[str, Any], *, require_comparison_ready: bool, require_objective_pass: bool = False
) -> int:
    """Comparison-CLI exit code: status gate plus the recovered-objective gate."""
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_objective_pass and summary.get("objective_contract_recovered") is not True:
        return 1
    return 0

def resolve_exit_code_execution_model(
    report: dict[str, Any], *, require_execution_pass: bool, require_model_pass: bool = False
) -> int:
    """Replay-CLI exit code: execution gate plus holdout model-quality gate."""
    if require_execution_pass and report.get("status") != "pass":
        return 1
    if require_model_pass and as_dict(report.get("summary")).get("holdout_model_quality_ready") is not True:
        return 1
    return 0


__all__ = [
    "check_entry",
    "check_entry_no_detail",
    "check_row",
    "collect_failures",
    "resolve_exit_code",
    "resolve_exit_code_comparison_objective",
    "resolve_exit_code_diagnostic_ready",
    "resolve_exit_code_dry_run_ready",
    "resolve_exit_code_execution_model",
    "resolve_exit_code_patch_ready",
    "resolve_exit_code_plan_ready",
    "resolve_exit_code_seed_ready",
    "resolve_exit_code_strict",
    "resolve_exit_code_suite_ready",
    "resolve_exit_code_training_ready",
]
