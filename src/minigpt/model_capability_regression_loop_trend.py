from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, locate_upstream_report, read_json_object, utc_now
from minigpt.report_check_common import check_entry_no_detail as _check

LOOP_TREND_STEM = "model_capability_regression_loop_trend_v1141"

STAGE_SPECS = [
    {
        "version": "v1135",
        "stage": "plan",
        "dir": "model-capability-regression-plan-v1135",
        "json": "model_capability_regression_plan_v1135.json",
        "ready_key": "plan_ready",
        "next_step": "inventory_model_capability_regression_evidence_v1136",
        "source_key": "source_cadence_path",
    },
    {
        "version": "v1136",
        "stage": "inventory",
        "dir": "model-capability-regression-inventory-v1136",
        "json": "model_capability_regression_inventory_v1136.json",
        "ready_key": "inventory_ready",
        "next_step": "build_model_capability_regression_suite_manifest_v1137",
        "source_key": "source_plan_path",
    },
    {
        "version": "v1137",
        "stage": "suite_manifest",
        "dir": "model-capability-regression-suite-manifest-v1137",
        "json": "model_capability_regression_suite_manifest_v1137.json",
        "ready_key": "suite_ready",
        "next_step": "check_model_capability_regression_suite_readiness_v1138",
        "source_key": "source_inventory_path",
    },
    {
        "version": "v1138",
        "stage": "suite_readiness",
        "dir": "model-capability-regression-suite-readiness-v1138",
        "json": "model_capability_regression_suite_readiness_v1138.json",
        "ready_key": "readiness_ready",
        "next_step": "close_model_capability_regression_followup_v1139",
        "source_key": "source_suite_manifest_path",
    },
    {
        "version": "v1139",
        "stage": "followup_closeout",
        "dir": "model-capability-regression-followup-closeout-v1139",
        "json": "model_capability_regression_followup_closeout_v1139.json",
        "ready_key": "closeout_ready",
        "next_step": "run_selected_model_capability_regression_execution",
        "source_key": "source_readiness_path",
    },
]


def load_model_capability_regression_loop_reports(root: str | Path = ".") -> list[dict[str, Any]]:
    project_root = Path(root)
    entries: list[dict[str, Any]] = []
    for spec in STAGE_SPECS:
        version_number = str(spec["version"]).removeprefix("v")
        report_dir = project_root / "f" / version_number / "解释" / str(spec["dir"])
        path = locate_upstream_report(report_dir, str(spec["json"]))
        report = read_json_object(path, description=f"{spec['version']} {spec['stage']} report") if path.is_file() else {}
        entries.append({**spec, "path": _project_relative_path(path, project_root), "artifact_exists": path.is_file(), "report": report})
    return entries


def build_model_capability_regression_loop_trend(
    stage_reports: list[dict[str, Any]],
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    rows = [_stage_row(entry) for entry in stage_reports]
    checks = _checks(stage_reports, rows)
    issues = [row for row in checks if row["status"] != "pass"]
    closed = not issues
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression loop trend v1141",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if closed else "fail",
        "decision": "model_capability_regression_loop_closed" if closed else "repair_model_capability_regression_loop",
        "failed_count": len(issues),
        "issues": issues,
        "rows": rows,
        "check_rows": checks,
        "loop": {
            "closed": closed,
            "stage_count": len(rows),
            "ready_stage_count": sum(1 for row in rows if row["ready"] is True),
            "first_version": rows[0]["version"] if rows else "",
            "last_version": rows[-1]["version"] if rows else "",
            "closeout_ready": rows[-1]["ready"] if rows else False,
            "promotion_ready": False,
            "model_quality_claim": "loop_trend_read_only",
            "next_step": "publish_model_capability_cadence_watch_v1142" if closed else "repair_model_capability_regression_loop_v1141",
        },
        "summary": {
            "loop_closed": closed,
            "stage_count": len(rows),
            "ready_stage_count": sum(1 for row in rows if row["ready"] is True),
            "artifact_present_count": sum(1 for row in rows if row["artifact_exists"] is True),
            "first_version": rows[0]["version"] if rows else "",
            "last_version": rows[-1]["version"] if rows else "",
            "closeout_ready": rows[-1]["ready"] if rows else False,
            "promotion_ready": False,
            "model_quality_claim": "loop_trend_read_only",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
            "next_step": "publish_model_capability_cadence_watch_v1142" if closed else "repair_model_capability_regression_loop_v1141",
        },
        "recommendations": [
            "Cite this report as the read-only closure evidence for v1135-v1139.",
            "Do not treat loop closure as model quality improvement.",
            "Use the cadence watch next to choose the next concrete model-capability execution item.",
        ],
        "csv_fieldnames": [
            "version",
            "stage",
            "artifact_exists",
            "status",
            "decision",
            "ready_key",
            "ready",
            "next_step",
            "source_path",
            "artifact_path",
        ],
    }


def write_model_capability_regression_loop_trend_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=LOOP_TREND_STEM, row_title="Regression Loop Stages")


def resolve_exit_code(report: dict[str, Any], *, require_loop_closed: bool = False) -> int:
    if require_loop_closed and as_dict(report.get("summary")).get("loop_closed") is not True:
        return 1
    return 0


def _stage_row(entry: dict[str, Any]) -> dict[str, Any]:
    report = as_dict(entry.get("report"))
    summary = as_dict(report.get("summary"))
    ready_key = str(entry.get("ready_key"))
    source_key = str(entry.get("source_key"))
    return {
        "version": entry.get("version"),
        "stage": entry.get("stage"),
        "artifact_exists": entry.get("artifact_exists") is True,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "ready_key": ready_key,
        "ready": summary.get(ready_key),
        "next_step": summary.get("next_step"),
        "source_path": report.get(source_key, ""),
        "artifact_path": entry.get("path", ""),
        "promotion_ready": summary.get("promotion_ready"),
        "model_quality_claim": summary.get("model_quality_claim"),
    }


def _checks(stage_reports: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_versions = [spec["version"] for spec in STAGE_SPECS]
    actual_versions = [row.get("version") for row in rows]
    expected_next_steps = [spec["next_step"] for spec in STAGE_SPECS]
    actual_next_steps = [row.get("next_step") for row in rows]
    return [
        _check("all_five_artifacts_present", len(rows) == 5 and all(row["artifact_exists"] for row in rows), [row.get("artifact_path") for row in rows if not row.get("artifact_exists")]),
        _check("version_order_strict", actual_versions == expected_versions, actual_versions),
        _check("all_stage_status_pass", all(row.get("status") == "pass" for row in rows), [row.get("status") for row in rows]),
        _check("all_stage_ready_flags_true", all(row.get("ready") is True for row in rows), [{row.get("version"): row.get("ready")} for row in rows]),
        _check("closeout_ready_true", bool(rows) and rows[-1].get("version") == "v1139" and rows[-1].get("ready") is True, rows[-1].get("ready") if rows else None),
        _check("next_steps_align", actual_next_steps == expected_next_steps, actual_next_steps),
        _check("source_paths_chain_back", _source_paths_chain_back(rows), [row.get("source_path") for row in rows[1:]]),
        _check("non_promotion_boundary_preserved", all(row.get("promotion_ready") is False for row in rows), [{row.get("version"): row.get("promotion_ready")} for row in rows]),
        _check("reports_are_parseable_objects", all(isinstance(entry.get("report"), dict) and bool(entry.get("report")) for entry in stage_reports), [entry.get("version") for entry in stage_reports if not entry.get("report")]),
    ]


def _source_paths_chain_back(rows: list[dict[str, Any]]) -> bool:
    if len(rows) != 5:
        return False
    for previous, current in zip(rows, rows[1:]):
        if _normalize_path(current.get("source_path")) != _normalize_path(previous.get("artifact_path")):
            return False
    return True


def _normalize_path(value: Any) -> str:
    return Path(str(value).replace("\\", "/")).as_posix()


def _project_relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "LOOP_TREND_STEM",
    "STAGE_SPECS",
    "build_model_capability_regression_loop_trend",
    "load_model_capability_regression_loop_reports",
    "resolve_exit_code",
    "write_model_capability_regression_loop_trend_outputs",
]
