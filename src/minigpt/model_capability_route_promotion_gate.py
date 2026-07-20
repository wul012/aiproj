from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_portfolio import MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
from minigpt.model_capability_route_promotion_regression_monitor import MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME = "model_capability_route_promotion_gate.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_CSV_FILENAME = "model_capability_route_promotion_gate.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_TEXT_FILENAME = "model_capability_route_promotion_gate.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_MARKDOWN_FILENAME = "model_capability_route_promotion_gate.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_HTML_FILENAME = "model_capability_route_promotion_gate.html"


def locate_route_promotion_portfolio(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
    return source


def locate_route_promotion_regression_monitor(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion gate input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_gate(
    portfolio: dict[str, Any],
    regression_monitor: dict[str, Any],
    *,
    portfolio_path: str | Path | None = None,
    regression_monitor_path: str | Path | None = None,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion gate",
    generated_at: str | None = None,
) -> dict[str, Any]:
    portfolio_summary = as_dict(portfolio.get("summary"))
    monitor_summary = as_dict(regression_monitor.get("summary"))
    checks = _checks(portfolio, regression_monitor, portfolio_summary, monitor_summary, required_boundary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    gate = _gate(status, portfolio_summary, monitor_summary, required_boundary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "exit_code": 0 if status == "pass" else 1,
        "failed_count": len(issues),
        "issues": issues,
        "portfolio_path": str(portfolio_path or ""),
        "regression_monitor_path": str(regression_monitor_path or ""),
        "portfolio_summary": portfolio_summary,
        "regression_monitor_summary": monitor_summary,
        "check_rows": checks,
        "gate": gate,
        "summary": _summary(status, checks, gate),
        "interpretation": _interpretation(status, gate),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return int(report.get("exit_code") or 0) if require_pass else 0


def _checks(
    portfolio: dict[str, Any],
    regression_monitor: dict[str, Any],
    portfolio_summary: dict[str, Any],
    monitor_summary: dict[str, Any],
    required_boundary: str,
) -> list[dict[str, Any]]:
    active_routes = list(portfolio_summary.get("active_routes") or [])
    return [
        _check("portfolio_passed", portfolio.get("status") == "pass", portfolio.get("status"), "route promotion portfolio must pass"),
        _check(
            "portfolio_decision_ready",
            portfolio.get("decision") == "model_capability_route_promotion_portfolio_ready",
            portfolio.get("decision"),
            "route promotion portfolio must be ready",
        ),
        _check(
            "regression_monitor_passed",
            regression_monitor.get("status") == "pass",
            regression_monitor.get("status"),
            "route promotion regression monitor must pass",
        ),
        _check(
            "regression_decision_passed",
            regression_monitor.get("decision") == "model_capability_route_promotion_regression_monitor_passed",
            regression_monitor.get("decision"),
            "regression monitor decision must pass",
        ),
        _check("active_routes_present", bool(active_routes), active_routes, "at least one active route is required"),
        _check(
            "portfolio_boundary_scoped",
            portfolio_summary.get("boundary") == required_boundary,
            portfolio_summary.get("boundary"),
            "portfolio must keep the required boundary",
        ),
        _check(
            "regression_boundary_stable",
            monitor_summary.get("boundary_changed") is False and monitor_summary.get("current_boundary") == required_boundary,
            {"changed": monitor_summary.get("boundary_changed"), "current": monitor_summary.get("current_boundary")},
            "regression monitor must preserve the required boundary",
        ),
        _check(
            "no_lost_active_routes",
            int(monitor_summary.get("lost_active_route_count") or 0) == 0,
            monitor_summary.get("lost_active_route_count"),
            "gate blocks when active routes are lost",
        ),
        _check(
            "no_claim_widening",
            monitor_summary.get("model_quality_claim_changed") is False,
            monitor_summary.get("model_quality_claim_changed"),
            "gate blocks claim widening",
        ),
        _check(
            "portfolio_checks_clean",
            int(portfolio_summary.get("failed_check_count") or 0) == 0,
            portfolio_summary.get("failed_check_count"),
            "portfolio should have no failed checks",
        ),
        _check(
            "regression_checks_clean",
            int(monitor_summary.get("failed_check_count") or 0) == 0,
            monitor_summary.get("failed_check_count"),
            "regression monitor should have no failed checks",
        ),
    ]


def _gate(status: str, portfolio_summary: dict[str, Any], monitor_summary: dict[str, Any], required_boundary: str) -> dict[str, Any]:
    active_routes = list(portfolio_summary.get("active_routes") or [])
    return {
        "gate_ready": status == "pass",
        "gate_decision": "allow_downstream_model_capability_review" if status == "pass" else "stop_for_route_promotion_review",
        "allowed_next_steps": ["route_promotion_release_packet", "model_capability_route_review"] if status == "pass" else [],
        "blocked_next_steps": [] if status == "pass" else ["route_promotion_release_packet", "model_capability_route_review"],
        "active_routes": active_routes,
        "active_route_count": len(active_routes),
        "boundary": required_boundary,
        "model_quality_claim": portfolio_summary.get("model_quality_claim") or monitor_summary.get("current_model_quality_claim") or "not_claimed",
        "lost_active_route_count": monitor_summary.get("lost_active_route_count"),
        "boundary_changed": monitor_summary.get("boundary_changed"),
        "claim_changed": monitor_summary.get("model_quality_claim_changed"),
    }


def _summary(status: str, checks: list[dict[str, Any]], gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_promotion_gate_ready": status == "pass" and gate.get("gate_ready") is True,
        "gate_decision": gate.get("gate_decision"),
        "active_route_count": gate.get("active_route_count"),
        "active_routes": gate.get("active_routes"),
        "boundary": gate.get("boundary"),
        "model_quality_claim": gate.get("model_quality_claim"),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_gate_passed"
    return "fix_model_capability_route_promotion_gate"


def _interpretation(status: str, gate: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route promotion portfolio cannot pass the downstream review gate.",
            "next_action": "repair portfolio readiness, active-route loss, boundary changes, or claim widening before release-packet handoff",
        }
    return {
        "model_quality_claim": gate.get("model_quality_claim"),
        "reason": "The active route portfolio and regression monitor are clean enough for bounded downstream model capability review.",
        "next_action": "build a route-promotion release packet that carries the portfolio and regression gate evidence",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_TEXT_FILENAME",
    "build_model_capability_route_promotion_gate",
    "locate_route_promotion_portfolio",
    "locate_route_promotion_regression_monitor",
    "read_json_report",
    "resolve_exit_code",
]
