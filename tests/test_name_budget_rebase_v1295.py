"""v1295 name-budget rename rebase: the neutrality proof and its refusals.

Pytest-style but pytest-import-free (the CI unit-test runner is plain
unittest without pytest installed).
"""
from __future__ import annotations

from minigpt.name_budget import rebase_renamed_paths


def _item(kind, path, qualname, length, digest):
    return {"kind": kind, "path": path, "qualname": qualname,
            "name": qualname, "length": length, "line": 1, "digest": digest}


LONG = "x" * 50
KEPT = _item("function", "src/other.py", "unchanged_" + LONG, 60, "d-kept")


def test_neutral_rename_is_accepted():
    old = [KEPT, _item("function", "src/old_name.py", LONG, 50, "d-old")]
    cur = [KEPT, _item("function", "src/new_name.py", LONG, 50, "d-new")]
    rebased = rebase_renamed_paths(old, cur, {"d-kept", "d-old"})
    assert rebased == cur


def test_changed_signature_is_refused():
    old = [_item("function", "src/old_name.py", LONG, 50, "d-old")]
    grown = [_item("function", "src/new_name.py", LONG + "y", 51, "d-new")]
    assert rebase_renamed_paths(old, grown, {"d-old"}) is None


def test_extra_new_violation_is_refused():
    old = [_item("function", "src/old_name.py", LONG, 50, "d-old")]
    cur = [_item("function", "src/new_name.py", LONG, 50, "d-new"),
           _item("variable", "src/new_name.py", "ALSO_" + LONG, 55, "d-x")]
    assert rebase_renamed_paths(old, cur, {"d-old"}) is None


def test_unprovable_resolved_metadata_is_refused():
    # the resolved digest is absent from the old-tree scan -> cannot prove
    cur = [_item("function", "src/new_name.py", LONG, 50, "d-new")]
    assert rebase_renamed_paths([], cur, {"d-ghost"}) is None


def test_pure_removal_is_refused():
    # removals alone are not a rename; the normal update path owns them
    old = [_item("function", "src/old_name.py", LONG, 50, "d-old")]
    assert rebase_renamed_paths(old, [], {"d-old"}) is None
