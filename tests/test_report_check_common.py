"""Tests for report_check_common — the shared check scaffolding extracted in
v1187 from the grokking-audit modules. Includes identity guards that each
migrated module uses the single source (not a re-pasted copy)."""

from __future__ import annotations

from minigpt import (
    grok_evidence_check_v1180,
    grok_paired_contrast_v1182,
    grok_trajectory_phases_v1181,
    grok_wd_law_check_v1184,
)
from minigpt.report_check_common import check_row, collect_failures, resolve_exit_code

AUDIT_MODULES = [
    grok_evidence_check_v1180,
    grok_trajectory_phases_v1181,
    grok_paired_contrast_v1182,
    grok_wd_law_check_v1184,
]


def test_check_row_shape():
    assert check_row("c1", True, "exp", "act", "why") == {
        "id": "c1", "status": "pass", "expected": "exp", "actual": "act", "detail": "why",
    }
    assert check_row("c2", False, 1, 2, "")["status"] == "fail"


def test_collect_failures_keeps_only_non_pass():
    rows = [check_row("a", True, "", "", ""), check_row("b", False, "", "", ""), {"id": "c"}]
    failures = collect_failures(rows)
    assert [f["id"] for f in failures] == ["b", "c"]  # missing status counts as failure


def test_resolve_exit_code():
    assert resolve_exit_code({"status": "pass"}, require_pass=True) == 0
    assert resolve_exit_code({"status": "fail"}, require_pass=True) == 1
    assert resolve_exit_code({"status": "fail"}, require_pass=False) == 0  # no gate -> always 0
    assert resolve_exit_code({}, require_pass=True) == 1


def test_audit_modules_use_the_single_source():
    # each migrated module must reference the shared functions, not a re-pasted copy
    for module in AUDIT_MODULES:
        assert module.resolve_exit_code is resolve_exit_code
        assert module._check is check_row
        assert module.collect_failures is collect_failures
