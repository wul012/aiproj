from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, locate_upstream_report, read_json_object, utc_now

SUITE_JSON = "model_capability_regression_suite_manifest_v1137.json"
READINESS_STEM = "model_capability_regression_suite_readiness_v1138"


def locate_suite_manifest(path: str | Path) -> Path:
    return locate_upstream_report(path, SUITE_JSON)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="model capability regression suite manifest")


def build_model_capability_regression_suite_readiness(
    suite_report: dict[str, Any],
    *,
    suite_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(suite_report.get("suite"))
    suite_rows = list_of_dicts(suite_report.get("rows"))
    rows = [_readiness_row(row) for row in suite_rows]
    checks = _checks(suite_report, suite, suite_rows, rows, suite_path)
    issues = [row for row in checks if row["status"] != "pass"]
    readiness_ready = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression suite readiness v1138",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if readiness_ready else "fail",
        "decision": "model_capability_regression_suite_readiness_ready" if readiness_ready else "repair_model_capability_regression_suite_readiness",
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_manifest_path": str(suite_path or ""),
        "source_suite_summary": as_dict(suite_report.get("summary")),
        "rows": rows,
        "check_rows": checks,
        "readiness": {
            "readiness_ready": readiness_ready,
            "ready_item_count": sum(1 for row in rows if row["status"] == "ready"),
            "suite_item_count": len(suite_rows),
            "next_step": "close_model_capability_regression_followup_v1139" if readiness_ready else "repair_model_capability_regression_suite_readiness_v1138",
            "promotion_ready": False,
            "model_quality_claim": "readiness_only",
        },
        "summary": {
            "readiness_ready": readiness_ready,
            "ready_item_count": sum(1 for row in rows if row["status"] == "ready"),
            "suite_item_count": len(suite_rows),
            "source_suite_ready": suite.get("suite_ready"),
            "promotion_ready": False,
            "model_quality_claim": "readiness_only",
            "next_step": "close_model_capability_regression_followup_v1139" if readiness_ready else "repair_model_capability_regression_suite_readiness_v1138",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
        },
        "recommendations": [
            "Use readiness output to close the follow-up loop before adding more governance-only work.",
            "Keep the next closeout honest: readiness is not a model quality score.",
            "If any source/test path drifts, repair the manifest before execution.",
        ],
        "csv_fieldnames": ["suite_id", "check_id", "source_exists", "test_exists", "boundary_ok", "status", "recommendation"],
    }


def write_model_capability_regression_suite_readiness_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=READINESS_STEM, row_title="Regression Suite Readiness")


def resolve_exit_code(report: dict[str, Any], *, require_readiness_ready: bool = False) -> int:
    if require_readiness_ready and as_dict(report.get("summary")).get("readiness_ready") is not True:
        return 1
    return 0


def _readiness_row(row: dict[str, Any]) -> dict[str, Any]:
    source = str(row.get("primary_source") or "")
    test = str(row.get("primary_test") or "")
    source_exists = bool(source) and Path(source).is_file()
    test_exists = bool(test) and Path(test).is_file()
    boundary_ok = row.get("boundary") == "evidence_lookup_not_model_promotion"
    ready = source_exists and test_exists and boundary_ok
    return {
        "suite_id": row.get("suite_id"),
        "check_id": row.get("check_id"),
        "source_exists": source_exists,
        "test_exists": test_exists,
        "boundary_ok": boundary_ok,
        "primary_source": source,
        "primary_test": test,
        "status": "ready" if ready else "blocked",
        "recommendation": "ready for bounded regression follow-up" if ready else "repair source/test path or boundary",
    }


def _checks(
    suite_report: dict[str, Any],
    suite: dict[str, Any],
    suite_rows: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    suite_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("suite_file_exists", bool(suite_path) and Path(str(suite_path)).is_file(), str(suite_path or "")),
        _check("suite_status_passed", suite_report.get("status") == "pass", suite_report.get("status")),
        _check("suite_ready", suite.get("suite_ready") is True, suite.get("suite_ready")),
        _check("suite_rows_present", len(suite_rows) > 0, len(suite_rows)),
        _check("readiness_rows_match_suite", len(rows) == len(suite_rows), {"rows": len(rows), "suite": len(suite_rows)}),
        _check("all_readiness_rows_ready", all(row["status"] == "ready" for row in rows), [row["status"] for row in rows]),
    ]


def _check(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}


__all__ = [
    "READINESS_STEM",
    "SUITE_JSON",
    "build_model_capability_regression_suite_readiness",
    "locate_suite_manifest",
    "read_json_report",
    "resolve_exit_code",
    "write_model_capability_regression_suite_readiness_outputs",
]
