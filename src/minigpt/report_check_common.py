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


__all__ = ["check_row", "collect_failures", "resolve_exit_code"]
