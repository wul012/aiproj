"""v1293: whole-codebase elegance ratchet — freeze the structural debt.

The elegance program (v1290+) burns down duplication, lint debt, pathological
names, and namespace flatness. This ratchet makes the burn-down one-way: each
metric is compared against a committed baseline and may only shrink. The
baseline updates only from a passing state, so the stock of structural debt
can never quietly regrow while the batched rename/sub-packaging versions
proceed.

Metrics over ``src/minigpt/*.py``:

- ``flat_dir_file_count`` — modules directly in the flat namespace directory;
  sub-packaging batches push this down.
- ``long_name_stock`` — module stems longer than ``LONG_NAME_THRESHOLD``
  characters (the historic receipt-index name family).
- ``max_stem_length`` — the single worst module name.
- ``dup_def_stock`` — function bodies (positionless AST dump, name included)
  repeated across ``DUP_MIN_MODULES``-or-more modules; the v1290 ``_median``
  class of copy-paste debt.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from minigpt.report_check_common import (
    check_row,
    collect_failures,
    resolve_exit_code,
)
from minigpt.report_utils import utc_now, write_json_payload

DEFAULT_BASELINE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs" / "static-analysis" / "elegance-baseline.json"
)
LONG_NAME_THRESHOLD = 120
DUP_MIN_MODULES = 3
METRIC_KEYS = ("flat_dir_file_count", "long_name_stock", "max_stem_length",
               "dup_def_stock")


def _is_shim(tree: ast.Module) -> bool:
    """A forwarding module (v1294 rename batches): nothing but a docstring,
    imports, and the sys.modules self-replacement. Shims are graves with
    forwarding addresses — they keep old import paths alive but are not
    real residents of the flat namespace, so the flat/name metrics skip
    them (the dup metric never sees them: shims define no functions)."""
    body = tree.body
    if body and isinstance(body[0], ast.Expr):
        body = body[1:]
    saw_forward = False
    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Subscript):
            saw_forward = True
            continue
        return False
    return saw_forward


def measure_elegance(project_root: str | Path) -> dict[str, int]:
    src = Path(project_root) / "src" / "minigpt"
    flat_stems = []
    for f in sorted(src.glob("*.py")):
        if not _is_shim(ast.parse(f.read_text(encoding="utf-8"))):
            flat_stems.append(f.stem)
    body_modules: dict[str, set[str]] = {}
    for f in sorted(src.rglob("*.py")):  # dup debt follows moved modules
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_modules.setdefault(ast.dump(node), set()).add(f.name)
    return {
        "flat_dir_file_count": len(flat_stems),
        "long_name_stock": sum(1 for s in flat_stems
                               if len(s) > LONG_NAME_THRESHOLD),
        "max_stem_length": max((len(s) for s in flat_stems), default=0),
        "dup_def_stock": sum(1 for mods in body_modules.values()
                             if len(mods) >= DUP_MIN_MODULES),
    }


def load_baseline(path: str | Path) -> dict[str, int]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {key: int(payload["metrics"][key]) for key in METRIC_KEYS}


def build_elegance_ratchet_report(
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    *,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root) if project_root is not None \
        else DEFAULT_BASELINE_PATH.parents[2]
    baseline = load_baseline(baseline_path)
    metrics = measure_elegance(root)
    checks = [
        check_row(f"elegance:{key}", metrics[key] <= baseline[key],
                  f"<= {baseline[key]}", metrics[key],
                  "ratchet only tightens")
        for key in METRIC_KEYS
    ]
    failures = collect_failures(checks)
    status = "pass" if not failures else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT whole-codebase elegance ratchet",
        "generated_at": utc_now(),
        "status": status,
        "decision": status,
        "baseline_path": str(baseline_path),
        "metrics": metrics,
        "baseline": baseline,
        "checks": checks,
        "failures": failures,
        "summary": {
            "metric_count": len(METRIC_KEYS),
            "failure_count": len(failures),
            "tightened_candidates": [
                key for key in METRIC_KEYS if metrics[key] < baseline[key]
            ],
        },
    }


def update_baseline(report: dict[str, Any],
                    baseline_path: str | Path) -> bool:
    """Tighten the baseline to the measured values; refused unless the
    report passes (the ratchet never loosens)."""
    if report["status"] != "pass":
        return False
    write_json_payload({"schema_version": 1, "updated_at": utc_now(),
                        "metrics": report["metrics"]}, baseline_path)
    return True


def write_elegance_ratchet_outputs(report: dict[str, Any],
                                   out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "elegance_ratchet.json"
    write_json_payload(report, json_path)
    lines = [f"status={report['status']}"]
    lines += [f"{key}={report['metrics'][key]} (baseline "
              f"{report['baseline'][key]})" for key in METRIC_KEYS]
    text_path = out / "elegance_ratchet.txt"
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "text": str(text_path)}


__all__ = [
    "DEFAULT_BASELINE_PATH",
    "METRIC_KEYS",
    "build_elegance_ratchet_report",
    "load_baseline",
    "measure_elegance",
    "resolve_exit_code",
    "update_baseline",
    "write_elegance_ratchet_outputs",
]
