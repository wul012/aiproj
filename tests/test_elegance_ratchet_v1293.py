"""v1293 elegance ratchet: metric measurement + tighten-only baseline logic.

Synthetic mini-projects in a temp tree exercise every metric and both ratchet
directions without touching the real baseline. Pytest-style but
pytest-import-free (the CI unit-test runner is plain unittest without pytest
installed).
"""
from __future__ import annotations

import json

from minigpt.elegance_ratchet import (
    build_elegance_ratchet_report,
    load_baseline,
    measure_elegance,
    resolve_exit_code,
    update_baseline,
    write_elegance_ratchet_outputs,
)

DUP = "def helper():\n    return 1\n"


def _project(tmp_path, *, long_name=False, dups=0):
    src = tmp_path / "src" / "minigpt"
    src.mkdir(parents=True)
    (src / "alpha.py").write_text("def alpha():\n    return 0\n",
                                  encoding="utf-8")
    (src / "beta.py").write_text("x = 1\n", encoding="utf-8")
    if long_name:
        (src / ("very_" + "long_" * 25 + "name.py")).write_text(
            "y = 2\n", encoding="utf-8")
    for i in range(dups):
        (src / f"dup_{i}.py").write_text(DUP, encoding="utf-8")
    return tmp_path


def _baseline(tmp_path, metrics):
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps({"schema_version": 1, "metrics": metrics}),
                    encoding="utf-8")
    return path


SHIM = ('"""Forwarding shim."""\nimport sys\n\n'
        "from minigpt.core import target as _target\n\n"
        "sys.modules[__name__] = _target\n")


def test_measure_counts_files_names_and_dup_bodies(tmp_path):
    root = _project(tmp_path, long_name=True, dups=3)
    m = measure_elegance(root)
    assert m["flat_dir_file_count"] == 6
    assert m["long_name_stock"] == 1
    assert m["max_stem_length"] > 120
    assert m["dup_def_stock"] == 1  # one body shared by >= 3 modules
    m2 = measure_elegance(_project(tmp_path / "two", dups=2))
    assert m2["dup_def_stock"] == 0  # two copies stay under the threshold
    assert m2["long_name_stock"] == 0


def test_measure_skips_shims_and_follows_moved_dups(tmp_path):
    root = _project(tmp_path, dups=3)
    src = root / "src" / "minigpt"
    # a forwarding shim with a pathological name is not a flat resident
    (src / ("shim_" + "long_" * 25 + "name.py")).write_text(
        SHIM, encoding="utf-8")
    # a real module moved into a subpackage still carries its dup body
    sub = src / "receipts"
    sub.mkdir()
    (sub / "__init__.py").write_text("", encoding="utf-8")
    (sub / "dup_moved.py").write_text(DUP, encoding="utf-8")
    m = measure_elegance(root)
    assert m["flat_dir_file_count"] == 5  # shim excluded
    assert m["long_name_stock"] == 0      # the long name is a shim
    assert m["dup_def_stock"] == 1        # moved copy still counted


def test_report_passes_at_baseline_and_fails_on_growth(tmp_path):
    root = _project(tmp_path, dups=3)
    current = measure_elegance(root)
    ok = build_elegance_ratchet_report(_baseline(tmp_path, current),
                                       project_root=root)
    assert ok["status"] == "pass" and not ok["failures"]
    assert resolve_exit_code(ok, require_pass=True) == 0
    tighter = dict(current)
    tighter["flat_dir_file_count"] -= 1
    bad = build_elegance_ratchet_report(_baseline(tmp_path, tighter),
                                        project_root=root)
    assert bad["status"] == "fail"
    assert [c["id"] for c in bad["failures"]] \
        == ["elegance:flat_dir_file_count"]
    assert resolve_exit_code(bad, require_pass=True) == 1


def test_update_baseline_only_tightens(tmp_path):
    root = _project(tmp_path, dups=3)
    current = measure_elegance(root)
    loose = {k: v + 5 for k, v in current.items()}
    path = _baseline(tmp_path, loose)
    report = build_elegance_ratchet_report(path, project_root=root)
    assert report["status"] == "pass"
    assert sorted(report["summary"]["tightened_candidates"]) \
        == sorted(current.keys())
    assert update_baseline(report, path) is True
    assert load_baseline(path) == current
    tighter = {k: v - 1 for k, v in current.items()}
    path2 = _baseline(tmp_path, tighter)
    failing = build_elegance_ratchet_report(path2, project_root=root)
    assert failing["status"] == "fail"
    assert update_baseline(failing, path2) is False
    assert load_baseline(path2) == tighter  # untouched on refusal


def test_outputs_written(tmp_path):
    root = _project(tmp_path, dups=3)
    path = _baseline(tmp_path, measure_elegance(root))
    report = build_elegance_ratchet_report(path, project_root=root)
    outputs = write_elegance_ratchet_outputs(report, tmp_path / "out")
    payload = json.loads((tmp_path / "out" / "elegance_ratchet.json")
                         .read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    text = (tmp_path / "out" / "elegance_ratchet.txt").read_text(
        encoding="utf-8")
    assert "status=pass" in text and outputs["json"].endswith(".json")
