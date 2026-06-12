from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, utc_now

READINESS_JSON = "model_capability_regression_suite_readiness_v1138.json"
CLOSEOUT_STEM = "model_capability_regression_followup_closeout_v1139"


def locate_readiness_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / READINESS_JSON
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("model capability regression readiness report must be a JSON object")
    return dict(payload)


def build_model_capability_regression_followup_closeout(
    readiness_report: dict[str, Any],
    *,
    readiness_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    readiness = as_dict(readiness_report.get("readiness"))
    readiness_rows = list_of_dicts(readiness_report.get("rows"))
    closeout_rows = [_closeout_row(row) for row in readiness_rows]
    checks = _checks(readiness_report, readiness, readiness_rows, closeout_rows, readiness_path)
    issues = [row for row in checks if row["status"] != "pass"]
    closeout_ready = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression follow-up closeout v1139",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if closeout_ready else "fail",
        "decision": "model_capability_regression_followup_closeout_ready" if closeout_ready else "repair_model_capability_regression_followup_closeout",
        "failed_count": len(issues),
        "issues": issues,
        "source_readiness_path": str(readiness_path or ""),
        "source_readiness_summary": as_dict(readiness_report.get("summary")),
        "rows": closeout_rows,
        "check_rows": checks,
        "closeout": {
            "closeout_ready": closeout_ready,
            "closed_stage": "plan_inventory_manifest_readiness",
            "ready_item_count": sum(1 for row in closeout_rows if row["status"] == "closed"),
            "next_step": "run_selected_model_capability_regression_execution",
            "promotion_ready": False,
            "model_quality_claim": "pre_execution_closeout_only",
        },
        "summary": {
            "closeout_ready": closeout_ready,
            "closed_stage": "plan_inventory_manifest_readiness",
            "ready_item_count": sum(1 for row in closeout_rows if row["status"] == "closed"),
            "source_readiness_ready": readiness.get("readiness_ready"),
            "promotion_ready": False,
            "model_quality_claim": "pre_execution_closeout_only",
            "next_step": "run_selected_model_capability_regression_execution",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
        },
        "recommendations": [
            "Treat v1135-v1139 as preparation closeout, not model-quality improvement.",
            "Run one selected regression item next, preferably required term coverage or holdout scorecard smoke.",
            "Keep execution evidence separate from this closeout so capability claims stay honest.",
        ],
        "csv_fieldnames": ["suite_id", "check_id", "readiness_status", "closeout_scope", "status", "next_action"],
    }


def write_model_capability_regression_followup_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=CLOSEOUT_STEM, row_title="Regression Follow-up Closeout")


def resolve_exit_code(report: dict[str, Any], *, require_closeout_ready: bool = False) -> int:
    if require_closeout_ready and as_dict(report.get("summary")).get("closeout_ready") is not True:
        return 1
    return 0


def _closeout_row(row: dict[str, Any]) -> dict[str, Any]:
    closed = row.get("status") == "ready" and row.get("boundary_ok") is True
    return {
        "suite_id": row.get("suite_id"),
        "check_id": row.get("check_id"),
        "readiness_status": row.get("status"),
        "closeout_scope": "pre_execution_readiness",
        "status": "closed" if closed else "blocked",
        "next_action": "eligible_for_selected_execution" if closed else "repair_readiness_before_execution",
    }


def _checks(
    readiness_report: dict[str, Any],
    readiness: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
    closeout_rows: list[dict[str, Any]],
    readiness_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("readiness_file_exists", bool(readiness_path) and Path(str(readiness_path)).is_file(), str(readiness_path or "")),
        _check("readiness_status_passed", readiness_report.get("status") == "pass", readiness_report.get("status")),
        _check("readiness_ready", readiness.get("readiness_ready") is True, readiness.get("readiness_ready")),
        _check("readiness_rows_present", len(readiness_rows) > 0, len(readiness_rows)),
        _check("closeout_rows_match_readiness", len(closeout_rows) == len(readiness_rows), {"closeout": len(closeout_rows), "readiness": len(readiness_rows)}),
        _check("all_rows_closed", all(row["status"] == "closed" for row in closeout_rows), [row["status"] for row in closeout_rows]),
    ]


def _check(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}


__all__ = [
    "CLOSEOUT_STEM",
    "READINESS_JSON",
    "build_model_capability_regression_followup_closeout",
    "locate_readiness_report",
    "read_json_report",
    "resolve_exit_code",
    "write_model_capability_regression_followup_closeout_outputs",
]
