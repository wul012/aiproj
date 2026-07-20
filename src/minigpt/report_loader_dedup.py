from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now
from minigpt.report_check_common import check_entry_no_detail as _check

REPORT_LOADER_DEDUP_STEM = "report_loader_dedup_v1140"
LOCATE_AND_READ_MIGRATED_MODULES = [
    "model_capability_regression_plan.py",
    "model_capability_regression_inventory.py",
    "model_capability_regression_suite_manifest.py",
    "model_capability_regression_suite_readiness.py",
    "model_capability_regression_followup_closeout.py",
]
GOVERNANCE_READER_MIGRATED_MODULES = [
    "benchmark_scorecard_comparison.py",
    "benchmark_scorecard_decision.py",
    "training_scale_handoff.py",
    "training_scale_promotion.py",
    "training_scale_run_comparison.py",
    "training_scale_run_decision.py",
    "training_portfolio_comparison.py",
    "promoted_training_scale_comparison.py",
    "promoted_training_scale_decision.py",
]
MIGRATED_MODULES = LOCATE_AND_READ_MIGRATED_MODULES + GOVERNANCE_READER_MIGRATED_MODULES


def build_report_loader_dedup_report(root: str | Path = ".", *, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    source_root = project_root / "src" / "minigpt"
    python_files = sorted(source_root.rglob("*.py"))
    read_json_definition_count = _count_text(python_files, "def read_json_report(")
    private_loader_copy_count = sum(1 for path in python_files if _private_loader_copy_present(_source_text(path)))
    rows = [_module_row(source_root / module_name) for module_name in MIGRATED_MODULES]
    checks = _checks(rows)
    issues = [row for row in checks if row["status"] != "pass"]
    ready = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT report loader dedup v1140",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if ready else "fail",
        "decision": "report_loader_dedup_ready" if ready else "repair_report_loader_dedup",
        "failed_count": len(issues),
        "issues": issues,
        "summary": {
            "dedup_ready": ready,
            "read_json_report_definition_count": read_json_definition_count,
            "private_loader_copy_count": private_loader_copy_count,
            "migrated_module_count": len(MIGRATED_MODULES),
            "locate_and_read_migrated_module_count": len(LOCATE_AND_READ_MIGRATED_MODULES),
            "governance_reader_migrated_module_count": len(GOVERNANCE_READER_MIGRATED_MODULES),
            "migrated_private_loader_copy_count": sum(1 for row in rows if row["private_loader_copy_present"]),
            "left_for_future_count": max(0, private_loader_copy_count),
            "boundary": "contract_preserving_thin_wrappers_only",
            "next_step": "continue_opportunistic_loader_migration_without_bulk_rewrite",
        },
        "rows": rows,
        "check_rows": checks,
        "recommendations": [
            "Keep the old public locate/read_json_report names as compatibility wrappers.",
            "Migrate older report loaders in future maintenance batches only when touching their area.",
            "Use this report as refactor evidence, not model capability evidence.",
        ],
        "csv_fieldnames": [
            "module",
            "exists",
            "requires_locate_helper",
            "imports_locate_upstream_report",
            "imports_read_json_object",
            "private_loader_copy_present",
            "status",
        ],
    }


def write_report_loader_dedup_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report, out_dir, stem=REPORT_LOADER_DEDUP_STEM, row_title="Migrated Report Loaders"
    )


def resolve_exit_code(report: dict[str, Any], *, require_dedup_ready: bool = False) -> int:
    if require_dedup_ready and report.get("status") != "pass":
        return 1
    return 0


def _module_row(path: Path) -> dict[str, Any]:
    text = _source_text(path)
    requires_locate = path.name in LOCATE_AND_READ_MIGRATED_MODULES
    imports_locate = "locate_upstream_report" in text
    imports_reader = "read_json_object" in text
    private_loader = _private_loader_copy_present(text)
    ready = path.is_file() and (imports_locate or not requires_locate) and imports_reader and not private_loader
    return {
        "module": path.name,
        "path": path.as_posix(),
        "exists": path.is_file(),
        "requires_locate_helper": requires_locate,
        "imports_locate_upstream_report": imports_locate,
        "imports_read_json_object": imports_reader,
        "private_loader_copy_present": private_loader,
        "status": "migrated" if ready else "needs_repair",
    }


def _checks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check(
            "all_target_modules_exist",
            all(row["exists"] for row in rows),
            [row["module"] for row in rows if not row["exists"]],
        ),
        _check(
            "all_required_modules_import_locate_helper",
            all(not row["requires_locate_helper"] or row["imports_locate_upstream_report"] for row in rows),
            [
                row["module"]
                for row in rows
                if row["requires_locate_helper"] and not row["imports_locate_upstream_report"]
            ],
        ),
        _check(
            "all_target_modules_import_reader_helper",
            all(row["imports_read_json_object"] for row in rows),
            [row["module"] for row in rows if not row["imports_read_json_object"]],
        ),
        _check(
            "no_target_private_loader_copy",
            not any(row["private_loader_copy_present"] for row in rows),
            [row["module"] for row in rows if row["private_loader_copy_present"]],
        ),
    ]


def _count_text(paths: list[Path], needle: str) -> int:
    count = 0
    for path in paths:
        try:
            count += path.read_text(encoding="utf-8").count(needle)
        except UnicodeDecodeError:
            continue
    return count


def _source_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except UnicodeDecodeError:
        return ""


def _private_loader_copy_present(text: str) -> bool:
    return "json.loads(" in text and "read_text(" in text and "utf-8-sig" in text


__all__ = [
    "MIGRATED_MODULES",
    "GOVERNANCE_READER_MIGRATED_MODULES",
    "LOCATE_AND_READ_MIGRATED_MODULES",
    "REPORT_LOADER_DEDUP_STEM",
    "build_report_loader_dedup_report",
    "resolve_exit_code",
    "write_report_loader_dedup_outputs",
]
