"""Measure archive roots and runs/ growth without moving any files.

This A0 production-excellence census is intentionally stdlib-only and warning-only.
It records the current size/file-count shape of the path-stable evidence archives
(`a/` through `f/`) and `runs/`, then exits 0 even when budgets are exceeded. Later
tracks may turn specific budgets into failing gates, but A0 is an inventory baseline.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
STEM = "archive_runs_inventory"
ARCHIVE_ROOTS = ("a", "b", "c", "d", "e", "f")
RUN_ROOTS = ("runs",)


@dataclass(frozen=True)
class InventoryBudget:
    archive_total_warning_mb: float = 512.0
    archive_root_warning_mb: float = 300.0
    runs_warning_mb: float = 64.0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def bytes_to_mb(size: int) -> float:
    return round(size / (1024 * 1024), 4)


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return (path for path in root.rglob("*") if path.is_file())


def measure_path(root: Path, category: str, budget_mb: float | None) -> dict[str, object]:
    exists = root.exists()
    file_count = 0
    dir_count = 0
    total_bytes = 0
    if exists:
        for path in root.rglob("*"):
            if path.is_file():
                file_count += 1
                try:
                    total_bytes += path.stat().st_size
                except OSError:
                    pass
            elif path.is_dir():
                dir_count += 1
    total_mb = bytes_to_mb(total_bytes)
    over_budget = bool(budget_mb is not None and total_mb > budget_mb)
    return {
        "category": category,
        "path": root.name,
        "exists": exists,
        "file_count": file_count,
        "directory_count": dir_count,
        "total_bytes": total_bytes,
        "total_mb": total_mb,
        "warning_budget_mb": budget_mb,
        "over_budget": over_budget,
    }


def build_inventory(
    project_root: Path = ROOT,
    *,
    generated_at: str | None = None,
    budget: InventoryBudget | None = None,
) -> dict[str, object]:
    budget = budget or InventoryBudget()
    archive_rows = [
        measure_path(project_root / name, "archive", budget.archive_root_warning_mb)
        for name in ARCHIVE_ROOTS
    ]
    run_rows = [measure_path(project_root / name, "run", budget.runs_warning_mb) for name in RUN_ROOTS]
    archive_total_mb = round(sum(float(row["total_mb"]) for row in archive_rows), 4)
    archive_total_bytes = sum(int(row["total_bytes"]) for row in archive_rows)
    warnings: list[dict[str, object]] = []
    if archive_total_mb > budget.archive_total_warning_mb:
        warnings.append(
            {
                "code": "ARCHIVE_TOTAL_OVER_BUDGET",
                "path": "a/..f/",
                "actual_mb": archive_total_mb,
                "budget_mb": budget.archive_total_warning_mb,
            }
        )
    for row in archive_rows + run_rows:
        if row["over_budget"]:
            warnings.append(
                {
                    "code": "PATH_OVER_BUDGET",
                    "path": row["path"],
                    "actual_mb": row["total_mb"],
                    "budget_mb": row["warning_budget_mb"],
                }
            )
        if not row["exists"]:
            warnings.append({"code": "PATH_MISSING", "path": row["path"]})

    return {
        "schema_version": 1,
        "title": "aiproj archive and runs inventory",
        "generated_at": generated_at or utc_now(),
        "status": "pass",
        "decision": "archive_runs_inventory_recorded_with_warnings" if warnings else "archive_runs_inventory_recorded",
        "warning_only": True,
        "project_root": str(project_root),
        "summary": {
            "archive_root_count": len(archive_rows),
            "run_root_count": len(run_rows),
            "archive_total_bytes": archive_total_bytes,
            "archive_total_mb": archive_total_mb,
            "archive_total_warning_mb": budget.archive_total_warning_mb,
            "archive_root_warning_mb": budget.archive_root_warning_mb,
            "runs_warning_mb": budget.runs_warning_mb,
            "warning_count": len(warnings),
        },
        "rows": archive_rows + run_rows,
        "warnings": warnings,
    }


def render_text(report: dict[str, object]) -> str:
    summary = report["summary"]
    rows = report["rows"]
    lines = [
        f"status={report['status']}",
        f"decision={report['decision']}",
        f"warning_only={report['warning_only']}",
        f"archive_total_mb={summary['archive_total_mb']}",
        f"warning_count={summary['warning_count']}",
    ]
    for row in rows:
        lines.append(
            "row="
            + ",".join(
                [
                    str(row["category"]),
                    str(row["path"]),
                    f"{row['total_mb']}MB",
                    f"files={row['file_count']}",
                    f"over_budget={row['over_budget']}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    lines = [
        "# aiproj archive and runs inventory",
        "",
        f"- status: `{report['status']}`",
        f"- decision: `{report['decision']}`",
        f"- warning-only: `{report['warning_only']}`",
        f"- archive total: `{summary['archive_total_mb']} MB` / warning budget `{summary['archive_total_warning_mb']} MB`",
        f"- warnings: `{summary['warning_count']}`",
        "",
        "| category | path | exists | files | directories | size MB | warning budget MB | over budget |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['category']} | `{row['path']}` | {row['exists']} | {row['file_count']} | "
            f"{row['directory_count']} | {row['total_mb']} | {row['warning_budget_mb']} | {row['over_budget']} |"
        )
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in report["warnings"]:
            lines.append(f"- `{warning['code']}` on `{warning['path']}`")
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, object]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['category']))}</td>"
        f"<td>{html.escape(str(row['path']))}</td>"
        f"<td>{row['exists']}</td>"
        f"<td>{row['file_count']}</td>"
        f"<td>{row['directory_count']}</td>"
        f"<td>{row['total_mb']}</td>"
        f"<td>{row['warning_budget_mb']}</td>"
        f"<td>{row['over_budget']}</td>"
        "</tr>"
        for row in report["rows"]
    )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>aiproj archive inventory</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:32px auto;line-height:1.45}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:6px;text-align:left}"
        "th{background:#eee}</style></head><body>"
        f"<h1>{html.escape(str(report['title']))}</h1>"
        f"<p><strong>status:</strong> {report['status']} | <strong>decision:</strong> {report['decision']} | "
        f"<strong>warning-only:</strong> {report['warning_only']}</p>"
        "<table><thead><tr><th>category</th><th>path</th><th>exists</th><th>files</th>"
        "<th>directories</th><th>size MB</th><th>warning budget MB</th><th>over budget</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></body></html>\n"
    )


def write_outputs(report: dict[str, object], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "json": out_dir / f"{STEM}.json",
        "csv": out_dir / f"{STEM}.csv",
        "text": out_dir / f"{STEM}.txt",
        "markdown": out_dir / f"{STEM}.md",
        "html": out_dir / f"{STEM}.html",
    }
    outputs["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with outputs["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "category",
                "path",
                "exists",
                "file_count",
                "directory_count",
                "total_bytes",
                "total_mb",
                "warning_budget_mb",
                "over_budget",
            ],
        )
        writer.writeheader()
        writer.writerows(report["rows"])
    outputs["text"].write_text(render_text(report), encoding="utf-8")
    outputs["markdown"].write_text(render_markdown(report), encoding="utf-8")
    outputs["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(path) for key, path in outputs.items()}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record archive roots and runs/ inventory.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "archive-runs-inventory")
    parser.add_argument("--archive-total-warning-mb", type=float, default=512.0)
    parser.add_argument("--archive-root-warning-mb", type=float, default=300.0)
    parser.add_argument("--runs-warning-mb", type=float, default=64.0)
    parser.add_argument("--force", action="store_true", help="Remove the output directory before writing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.out_dir.exists() and args.force:
        shutil.rmtree(args.out_dir)
    budget = InventoryBudget(
        archive_total_warning_mb=args.archive_total_warning_mb,
        archive_root_warning_mb=args.archive_root_warning_mb,
        runs_warning_mb=args.runs_warning_mb,
    )
    report = build_inventory(args.root, budget=budget)
    outputs = write_outputs(report, args.out_dir)
    print(render_text(report), end="")
    print("outputs=" + json.dumps(outputs, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
