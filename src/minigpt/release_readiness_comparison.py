from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.release_readiness_comparison_artifacts import (
    render_release_readiness_comparison_html,
    render_release_readiness_comparison_markdown,
    write_release_readiness_comparison_csv,
    write_release_readiness_comparison_html,
    write_release_readiness_comparison_json,
    write_release_readiness_comparison_markdown,
    write_release_readiness_comparison_outputs,
    write_release_readiness_delta_csv,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
)


STATUS_ORDER = {
    "blocked": 0,
    "incomplete": 1,
    "review": 2,
    "ready": 3,
}

CI_STATUS_ORDER = {
    "missing": 0,
    "fail": 0,
    "warn": 1,
    "review": 1,
    "pass": 2,
}


def build_release_readiness_comparison(
    readiness_paths: list[str | Path],
    *,
    baseline_path: str | Path | None = None,
    title: str = "MiniGPT release readiness comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    paths = [Path(path) for path in readiness_paths]
    if baseline_path is not None:
        baseline = Path(baseline_path)
        paths = [baseline] + [path for path in paths if path != baseline]
    if not paths:
        raise ValueError("at least one release_readiness.json path is required")
    reports = [_read_required_json(path) for path in paths]
    rows = [_row_from_report(path, report) for path, report in zip(paths, reports)]
    baseline_row = rows[0]
    deltas = [_delta_from_baseline(baseline_row, row) for row in rows[1:]]
    summary = _summary(rows, deltas, baseline_row)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "baseline_path": str(paths[0]),
        "readiness_paths": [str(path) for path in paths],
        "summary": summary,
        "rows": rows,
        "deltas": deltas,
        "recommendations": _recommendations(summary, deltas),
    }


def _row_from_report(path: Path, report: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(report.get("summary"))
    panels = _list_of_dicts(report.get("panels"))
    status = str(summary.get("readiness_status") or "missing")
    return {
        "readiness_path": str(path),
        "release_name": summary.get("release_name"),
        "readiness_status": status,
        "decision": summary.get("decision"),
        "readiness_score": STATUS_ORDER.get(status, -1),
        "gate_status": summary.get("gate_status"),
        "audit_status": summary.get("audit_status"),
        "audit_score_percent": summary.get("audit_score_percent"),
        "ci_workflow_status": summary.get("ci_workflow_status"),
        "ci_workflow_failed_checks": summary.get("ci_workflow_failed_checks"),
        "ci_workflow_node24_actions": summary.get("ci_workflow_node24_actions"),
        "request_history_status": summary.get("request_history_status"),
        "maturity_status": summary.get("maturity_status"),
        "ready_runs": summary.get("ready_runs"),
        "missing_artifacts": summary.get("missing_artifacts"),
        "fail_panel_count": summary.get("fail_panel_count"),
        "warn_panel_count": summary.get("warn_panel_count"),
        "action_count": len(_string_list(report.get("actions"))),
        "panel_statuses": {str(panel.get("key")): panel.get("status") for panel in panels if panel.get("key")},
    }


def _delta_from_baseline(baseline: dict[str, Any], compared: dict[str, Any]) -> dict[str, Any]:
    status_delta = int(compared.get("readiness_score") or 0) - int(baseline.get("readiness_score") or 0)
    baseline_panels = _dict(baseline.get("panel_statuses"))
    compared_panels = _dict(compared.get("panel_statuses"))
    changed = []
    for key in sorted(set(baseline_panels) | set(compared_panels)):
        before = baseline_panels.get(key)
        after = compared_panels.get(key)
        if before != after:
            changed.append(f"{key}:{before}->{after}")
    delta = {
        "baseline_path": baseline.get("readiness_path"),
        "compared_path": compared.get("readiness_path"),
        "baseline_release": baseline.get("release_name"),
        "compared_release": compared.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "compared_status": compared.get("readiness_status"),
        "baseline_ci_workflow_status": baseline.get("ci_workflow_status"),
        "compared_ci_workflow_status": compared.get("ci_workflow_status"),
        "status_delta": status_delta,
        "delta_status": _delta_status(status_delta, changed),
        "audit_score_delta": _number_delta(compared.get("audit_score_percent"), baseline.get("audit_score_percent")),
        "ci_workflow_failed_check_delta": _number_delta(compared.get("ci_workflow_failed_checks"), baseline.get("ci_workflow_failed_checks")),
        "ci_workflow_status_changed": compared.get("ci_workflow_status") != baseline.get("ci_workflow_status"),
        "missing_artifact_delta": _number_delta(compared.get("missing_artifacts"), baseline.get("missing_artifacts")),
        "fail_panel_delta": _number_delta(compared.get("fail_panel_count"), baseline.get("fail_panel_count")),
        "warn_panel_delta": _number_delta(compared.get("warn_panel_count"), baseline.get("warn_panel_count")),
        "changed_panels": changed,
    }
    delta["explanation"] = _delta_explanation(delta)
    return delta


def _delta_status(status_delta: int, changed_panels: list[str]) -> str:
    if status_delta > 0:
        return "improved"
    if status_delta < 0:
        return "regressed"
    if changed_panels:
        return "panel-changed"
    return "same"


def _delta_explanation(delta: dict[str, Any]) -> str:
    compared = delta.get("compared_release") or delta.get("compared_path")
    status = delta.get("delta_status")
    parts = [
        f"{compared} moves from {delta.get('baseline_status')} to {delta.get('compared_status')} ({status_delta_label(delta.get('status_delta'))})."
    ]
    changed = _string_list(delta.get("changed_panels"))
    if changed:
        parts.append("Changed panel(s): " + ", ".join(changed) + ".")
    if delta.get("audit_score_delta") not in {None, 0, 0.0}:
        parts.append(f"Audit score delta is {delta.get('audit_score_delta')}.")
    if delta.get("ci_workflow_status_changed"):
        parts.append("CI workflow status changed.")
    if delta.get("ci_workflow_failed_check_delta") not in {None, 0, 0.0}:
        parts.append(f"CI workflow failed check delta is {delta.get('ci_workflow_failed_check_delta')}.")
    if status == "same" and not changed:
        parts.append("No readiness status or panel delta is present.")
    return " ".join(parts)


def status_delta_label(value: Any) -> str:
    delta = int(value or 0)
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def _summary(rows: list[dict[str, Any]], deltas: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "readiness_count": len(rows),
        "baseline_release": baseline.get("release_name"),
        "baseline_status": baseline.get("readiness_status"),
        "ready_count": sum(1 for row in rows if row.get("readiness_status") == "ready"),
        "review_count": sum(1 for row in rows if row.get("readiness_status") == "review"),
        "blocked_count": sum(1 for row in rows if row.get("readiness_status") == "blocked"),
        "incomplete_count": sum(1 for row in rows if row.get("readiness_status") == "incomplete"),
        "improved_count": sum(1 for delta in deltas if delta.get("delta_status") == "improved"),
        "regressed_count": sum(1 for delta in deltas if delta.get("delta_status") == "regressed"),
        "changed_panel_delta_count": sum(1 for delta in deltas if delta.get("changed_panels")),
        "ci_workflow_regression_count": sum(1 for delta in deltas if _is_ci_workflow_regression(delta)),
    }


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    if int(summary.get("ci_workflow_regression_count") or 0):
        return ["At least one readiness comparison shows CI workflow hygiene regression; inspect CI failed-check deltas before release handoff."]
    if int(summary.get("regressed_count") or 0):
        return ["At least one readiness report regressed from the baseline; inspect delta explanations before release handoff."]
    if int(summary.get("improved_count") or 0):
        return ["Readiness improved against the baseline; keep the comparison report with release evidence."]
    if int(summary.get("blocked_count") or 0):
        return ["At least one readiness report is blocked; fix failed panels before comparing release quality as improved."]
    if any(delta.get("changed_panels") for delta in deltas):
        return ["Readiness status stayed stable, but panel-level changes should be reviewed."]
    return ["Readiness reports are stable against the baseline."]


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release readiness comparison input must be a JSON object: {path}")
    return payload


def _number_delta(left: Any, right: Any) -> float | int | None:
    if left is None or right is None:
        return None
    delta = float(left) - float(right)
    return int(delta) if delta.is_integer() else round(delta, 4)


def _is_ci_workflow_regression(delta: dict[str, Any]) -> bool:
    failed_delta = delta.get("ci_workflow_failed_check_delta")
    if isinstance(failed_delta, (int, float)) and failed_delta > 0:
        return True
    if delta.get("ci_workflow_status_changed"):
        return _ci_status_score(delta.get("compared_ci_workflow_status")) < _ci_status_score(delta.get("baseline_ci_workflow_status"))
    return False


def _ci_status_score(value: Any) -> int:
    return CI_STATUS_ORDER.get(str(value or "missing"), 0)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


__all__ = [
    "build_release_readiness_comparison",
    "render_release_readiness_comparison_html",
    "render_release_readiness_comparison_markdown",
    "status_delta_label",
    "write_release_readiness_comparison_csv",
    "write_release_readiness_comparison_html",
    "write_release_readiness_comparison_json",
    "write_release_readiness_comparison_markdown",
    "write_release_readiness_comparison_outputs",
    "write_release_readiness_delta_csv",
]
