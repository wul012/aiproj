from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, utc_now

PLAN_JSON = "model_capability_regression_plan_v1135.json"
INVENTORY_STEM = "model_capability_regression_inventory_v1136"

KEYWORD_MAP = {
    "required_term_coverage": ("required_term", "coverage"),
    "loss_signal_bridge": ("loss_signal", "loss_signal_bridge"),
    "decoder_anchor_distribution": ("decoder_anchor", "anchor_distribution"),
    "holdout_scorecard_smoke": ("holdout", "scorecard"),
}


def locate_regression_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PLAN_JSON
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("model capability regression plan must be a JSON object")
    return dict(payload)


def build_model_capability_regression_inventory(
    plan_report: dict[str, Any],
    *,
    root: str | Path = ".",
    plan_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    plan = as_dict(plan_report.get("plan"))
    plan_rows = list_of_dicts(plan_report.get("rows"))
    rows = [_inventory_row(project_root, row) for row in plan_rows]
    checks = _checks(plan_report, plan, plan_rows, rows, plan_path)
    issues = [row for row in checks if row["status"] != "pass"]
    inventory_ready = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression evidence inventory v1136",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if inventory_ready else "fail",
        "decision": "model_capability_regression_inventory_ready" if inventory_ready else "repair_model_capability_regression_inventory",
        "failed_count": len(issues),
        "issues": issues,
        "source_plan_path": str(plan_path or ""),
        "source_plan_summary": as_dict(plan_report.get("summary")),
        "rows": rows,
        "check_rows": checks,
        "inventory": {
            "inventory_ready": inventory_ready,
            "planned_item_count": len(plan_rows),
            "ready_item_count": sum(1 for row in rows if row["status"] == "ready"),
            "next_step": "build_model_capability_regression_suite_manifest_v1137" if inventory_ready else "repair_model_capability_regression_inventory_v1136",
            "promotion_ready": False,
            "model_quality_claim": "inventory_only",
        },
        "summary": {
            "inventory_ready": inventory_ready,
            "planned_item_count": len(plan_rows),
            "ready_item_count": sum(1 for row in rows if row["status"] == "ready"),
            "source_plan_ready": plan.get("plan_ready"),
            "promotion_ready": False,
            "model_quality_claim": "inventory_only",
            "next_step": "build_model_capability_regression_suite_manifest_v1137" if inventory_ready else "repair_model_capability_regression_inventory_v1136",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
        },
        "recommendations": [
            "Use ready inventory rows to build a small regression suite manifest.",
            "Prefer existing scripts and tests before adding new capability machinery.",
            "Keep this as evidence availability, not a model quality result.",
        ],
        "csv_fieldnames": ["check_id", "script_count", "source_count", "test_count", "artifact_count", "status", "recommendation"],
    }


def write_model_capability_regression_inventory_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=INVENTORY_STEM, row_title="Regression Evidence Inventory")


def resolve_exit_code(report: dict[str, Any], *, require_inventory_ready: bool = False) -> int:
    if require_inventory_ready and as_dict(report.get("summary")).get("inventory_ready") is not True:
        return 1
    return 0


def _inventory_row(root: Path, plan_row: dict[str, Any]) -> dict[str, Any]:
    check_id = str(plan_row.get("check_id"))
    keywords = KEYWORD_MAP.get(check_id, (check_id,))
    scripts = _matching_files(root / "scripts", "*.py", keywords)
    sources = _matching_files(root / "src" / "minigpt", "*.py", keywords)
    tests = _matching_files(root / "tests", "*.py", keywords)
    artifacts = _matching_files(root / "f", "*.json", keywords)
    ready = bool(scripts or sources) and bool(tests)
    return {
        "check_id": check_id,
        "script_count": len(scripts),
        "source_count": len(sources),
        "test_count": len(tests),
        "artifact_count": len(artifacts),
        "sample_script": scripts[0] if scripts else "",
        "sample_source": sources[0] if sources else "",
        "sample_test": tests[0] if tests else "",
        "sample_artifact": artifacts[0] if artifacts else "",
        "status": "ready" if ready else "missing",
        "recommendation": "reuse existing evidence path" if ready else "add or locate source/test coverage before suite manifest",
    }


def _checks(plan_report: dict[str, Any], plan: dict[str, Any], plan_rows: list[dict[str, Any]], rows: list[dict[str, Any]], plan_path: str | Path | None) -> list[dict[str, Any]]:
    return [
        _check("plan_file_exists", bool(plan_path) and Path(str(plan_path)).is_file(), str(plan_path or "")),
        _check("plan_status_passed", plan_report.get("status") == "pass", plan_report.get("status")),
        _check("plan_ready", plan.get("plan_ready") is True, plan.get("plan_ready")),
        _check("plan_rows_present", len(plan_rows) > 0, len(plan_rows)),
        _check("inventory_rows_match_plan", len(rows) == len(plan_rows), {"rows": len(rows), "plan": len(plan_rows)}),
        _check("all_inventory_items_ready", all(row["status"] == "ready" for row in rows), [row["status"] for row in rows]),
    ]


def _matching_files(root: Path, pattern: str, keywords: tuple[str, ...]) -> list[str]:
    if not root.exists():
        return []
    matches: list[str] = []
    for path in root.rglob(pattern):
        name = path.as_posix().lower()
        if any(keyword.lower() in name for keyword in keywords):
            matches.append(path.as_posix())
    return sorted(matches)


def _check(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}


__all__ = [
    "INVENTORY_STEM",
    "KEYWORD_MAP",
    "PLAN_JSON",
    "build_model_capability_regression_inventory",
    "locate_regression_plan",
    "read_json_report",
    "resolve_exit_code",
    "write_model_capability_regression_inventory_outputs",
]
