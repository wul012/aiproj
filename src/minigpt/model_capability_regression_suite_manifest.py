from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, utc_now

INVENTORY_JSON = "model_capability_regression_inventory_v1136.json"
SUITE_STEM = "model_capability_regression_suite_manifest_v1137"


def locate_inventory_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / INVENTORY_JSON
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("model capability regression inventory must be a JSON object")
    return dict(payload)


def build_model_capability_regression_suite_manifest(
    inventory_report: dict[str, Any],
    *,
    inventory_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    inventory = as_dict(inventory_report.get("inventory"))
    inventory_rows = list_of_dicts(inventory_report.get("rows"))
    suite_rows = [_suite_row(index, row) for index, row in enumerate(inventory_rows, start=1) if row.get("status") == "ready"]
    checks = _checks(inventory_report, inventory, inventory_rows, suite_rows, inventory_path)
    issues = [row for row in checks if row["status"] != "pass"]
    suite_ready = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression suite manifest v1137",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if suite_ready else "fail",
        "decision": "model_capability_regression_suite_manifest_ready" if suite_ready else "repair_model_capability_regression_suite_manifest",
        "failed_count": len(issues),
        "issues": issues,
        "source_inventory_path": str(inventory_path or ""),
        "source_inventory_summary": as_dict(inventory_report.get("summary")),
        "rows": suite_rows,
        "check_rows": checks,
        "suite": {
            "suite_ready": suite_ready,
            "suite_item_count": len(suite_rows),
            "execution_mode": "reuse_existing_evidence_paths",
            "next_step": "check_model_capability_regression_suite_readiness_v1138" if suite_ready else "repair_model_capability_regression_suite_manifest_v1137",
            "promotion_ready": False,
            "model_quality_claim": "manifest_only",
        },
        "summary": {
            "suite_ready": suite_ready,
            "suite_item_count": len(suite_rows),
            "source_inventory_ready": inventory.get("inventory_ready"),
            "promotion_ready": False,
            "model_quality_claim": "manifest_only",
            "next_step": "check_model_capability_regression_suite_readiness_v1138" if suite_ready else "repair_model_capability_regression_suite_manifest_v1137",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
        },
        "recommendations": [
            "Use the manifest to run a bounded regression readiness check before claiming capability evidence.",
            "Keep suite rows tied to existing files so the regression is maintainable.",
            "Treat this manifest as an execution map, not a model result.",
        ],
        "csv_fieldnames": ["suite_id", "check_id", "primary_source", "primary_test", "artifact_hint", "status", "boundary"],
    }


def write_model_capability_regression_suite_manifest_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=SUITE_STEM, row_title="Regression Suite Manifest")


def resolve_exit_code(report: dict[str, Any], *, require_suite_ready: bool = False) -> int:
    if require_suite_ready and as_dict(report.get("summary")).get("suite_ready") is not True:
        return 1
    return 0


def _suite_row(index: int, inventory_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "suite_id": f"capability-regression-{index:02d}",
        "check_id": inventory_row.get("check_id"),
        "primary_source": inventory_row.get("sample_source") or inventory_row.get("sample_script"),
        "primary_test": inventory_row.get("sample_test"),
        "artifact_hint": inventory_row.get("sample_artifact"),
        "status": "manifested",
        "boundary": "evidence_lookup_not_model_promotion",
    }


def _checks(
    inventory_report: dict[str, Any],
    inventory: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
    suite_rows: list[dict[str, Any]],
    inventory_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _check("inventory_file_exists", bool(inventory_path) and Path(str(inventory_path)).is_file(), str(inventory_path or "")),
        _check("inventory_status_passed", inventory_report.get("status") == "pass", inventory_report.get("status")),
        _check("inventory_ready", inventory.get("inventory_ready") is True, inventory.get("inventory_ready")),
        _check("inventory_rows_present", len(inventory_rows) > 0, len(inventory_rows)),
        _check("suite_rows_match_ready_inventory", len(suite_rows) == sum(1 for row in inventory_rows if row.get("status") == "ready"), {"suite": len(suite_rows), "ready": sum(1 for row in inventory_rows if row.get("status") == "ready")}),
        _check("suite_rows_have_tests", all(row.get("primary_test") for row in suite_rows), [row.get("primary_test") for row in suite_rows]),
        _check("suite_rows_keep_boundary", all(row.get("boundary") == "evidence_lookup_not_model_promotion" for row in suite_rows), [row.get("boundary") for row in suite_rows]),
    ]


def _check(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}


__all__ = [
    "INVENTORY_JSON",
    "SUITE_STEM",
    "build_model_capability_regression_suite_manifest",
    "locate_inventory_report",
    "read_json_report",
    "resolve_exit_code",
    "write_model_capability_regression_suite_manifest_outputs",
]
