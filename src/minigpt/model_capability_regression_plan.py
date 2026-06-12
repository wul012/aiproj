from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, locate_upstream_report, read_json_object, utc_now

CADENCE_JSON = "model_capability_cadence_v1133.json"
PLAN_STEM = "model_capability_regression_plan_v1135"

REGRESSION_ITEMS = [
    {
        "check_id": "required_term_coverage",
        "scope": "surface",
        "evidence_kind": "coverage",
        "reason": "Verify required terms are still visible in bounded prompts.",
    },
    {
        "check_id": "loss_signal_bridge",
        "scope": "training-signal",
        "evidence_kind": "diagnostic",
        "reason": "Reconnect governance cadence to a measurable loss or score signal.",
    },
    {
        "check_id": "decoder_anchor_distribution",
        "scope": "decoder",
        "evidence_kind": "distribution",
        "reason": "Inspect whether generated anchors remain bounded instead of echoing templates.",
    },
    {
        "check_id": "holdout_scorecard_smoke",
        "scope": "holdout",
        "evidence_kind": "scorecard",
        "reason": "Keep a small holdout scorecard in the loop after receipt-heavy runs.",
    },
]


def locate_cadence_report(path: str | Path) -> Path:
    return locate_upstream_report(path, CADENCE_JSON)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="model capability cadence report")


def build_model_capability_regression_plan(
    cadence_report: dict[str, Any],
    *,
    cadence_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(cadence_report.get("summary"))
    checks = _checks(cadence_report, summary, cadence_path)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan_ready = status == "pass"
    rows = _plan_rows(plan_ready)
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability regression plan v1135",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "model_capability_regression_plan_ready" if plan_ready else "repair_model_capability_regression_plan",
        "failed_count": len(issues),
        "issues": issues,
        "source_cadence_path": str(cadence_path or ""),
        "source_cadence_summary": summary,
        "plan": {
            "plan_ready": plan_ready,
            "plan_status": "scheduled" if plan_ready else "blocked",
            "source_watch_reason": "cadence_run_exceeded_limit" if plan_ready else "source_not_ready",
            "regression_item_count": len(rows) if plan_ready else 0,
            "next_step": "inventory_model_capability_regression_evidence_v1136" if plan_ready else "repair_model_capability_cadence_v1133",
            "promotion_ready": False,
            "model_quality_claim": "plan_only",
        },
        "rows": rows,
        "check_rows": checks,
        "summary": {
            "plan_ready": plan_ready,
            "regression_item_count": len(rows) if plan_ready else 0,
            "source_status": cadence_report.get("status"),
            "source_next_action": summary.get("next_action"),
            "leading_non_capability_run": summary.get("leading_non_capability_run"),
            "max_non_capability_run": summary.get("max_non_capability_run"),
            "promotion_ready": False,
            "model_quality_claim": "plan_only",
            "next_step": "inventory_model_capability_regression_evidence_v1136" if plan_ready else "repair_model_capability_cadence_v1133",
            "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
            "failed_check_count": len(issues),
        },
        "recommendations": [
            "Run a small model capability regression before adding more receipt-only versions.",
            "Keep the regression bounded: required terms, loss signal, decoder anchor, and holdout scorecard.",
            "Do not treat this plan as model improvement evidence; it only schedules the checks.",
        ],
        "csv_fieldnames": ["check_id", "scope", "evidence_kind", "status", "reason"],
    }


def write_model_capability_regression_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=PLAN_STEM, row_title="Regression Plan Items")


def resolve_exit_code(report: dict[str, Any], *, require_plan_ready: bool = False) -> int:
    if require_plan_ready and as_dict(report.get("summary")).get("plan_ready") is not True:
        return 1
    return 0


def _checks(cadence_report: dict[str, Any], summary: dict[str, Any], cadence_path: str | Path | None) -> list[dict[str, Any]]:
    return [
        _check("cadence_file_exists", bool(cadence_path) and Path(str(cadence_path)).is_file(), str(cadence_path or "")),
        _check("cadence_tool_ready", summary.get("cadence_ready") is True, summary.get("cadence_ready")),
        _check("cadence_watch_detected", cadence_report.get("status") == "watch", cadence_report.get("status")),
        _check("model_regression_requested", summary.get("next_action") == "schedule_model_capability_regression", summary.get("next_action")),
        _check("non_capability_run_exceeds_limit", int(summary.get("leading_non_capability_run") or 0) > int(summary.get("max_non_capability_run") or 0), {"run": summary.get("leading_non_capability_run"), "limit": summary.get("max_non_capability_run")}),
    ]


def _plan_rows(plan_ready: bool) -> list[dict[str, Any]]:
    if not plan_ready:
        return []
    return [{**item, "status": "planned"} for item in REGRESSION_ITEMS]


def _check(check_id: str, passed: bool, actual: Any) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual}


__all__ = [
    "CADENCE_JSON",
    "PLAN_STEM",
    "REGRESSION_ITEMS",
    "build_model_capability_regression_plan",
    "locate_cadence_report",
    "read_json_report",
    "resolve_exit_code",
    "write_model_capability_regression_plan_outputs",
]
