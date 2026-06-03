from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_gate import MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME
from minigpt.model_capability_route_promotion_portfolio import MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
from minigpt.model_capability_route_promotion_regression_monitor import MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME = "model_capability_route_promotion_release_packet.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_CSV_FILENAME = "model_capability_route_promotion_release_packet.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_TEXT_FILENAME = "model_capability_route_promotion_release_packet.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_MARKDOWN_FILENAME = "model_capability_route_promotion_release_packet.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_HTML_FILENAME = "model_capability_route_promotion_release_packet.html"


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


def locate_route_promotion_gate(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_GATE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion release packet input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_release_packet(
    portfolio: dict[str, Any],
    regression_monitor: dict[str, Any],
    gate: dict[str, Any],
    *,
    portfolio_path: str | Path | None = None,
    regression_monitor_path: str | Path | None = None,
    gate_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion release packet",
    generated_at: str | None = None,
) -> dict[str, Any]:
    portfolio_summary = as_dict(portfolio.get("summary"))
    monitor_summary = as_dict(regression_monitor.get("summary"))
    gate_summary = as_dict(gate.get("summary"))
    route_cards = list_of_dicts(portfolio.get("route_cards"))
    evidence_rows = _evidence_rows(portfolio_path, regression_monitor_path, gate_path)
    checks = _checks(portfolio, regression_monitor, gate, portfolio_summary, monitor_summary, gate_summary, evidence_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    packet = _packet(status, portfolio_summary, monitor_summary, gate_summary, route_cards, evidence_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "portfolio_summary": portfolio_summary,
        "regression_monitor_summary": monitor_summary,
        "gate_summary": gate_summary,
        "route_cards": route_cards,
        "evidence_rows": evidence_rows,
        "check_rows": checks,
        "packet": packet,
        "summary": _summary(status, checks, packet),
        "interpretation": _interpretation(status, packet),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _evidence_rows(
    portfolio_path: str | Path | None,
    regression_monitor_path: str | Path | None,
    gate_path: str | Path | None,
) -> list[dict[str, Any]]:
    return [
        _evidence("portfolio", portfolio_path),
        _evidence("regression_monitor", regression_monitor_path),
        _evidence("gate", gate_path),
    ]


def _evidence(kind: str, path: str | Path | None) -> dict[str, Any]:
    text = str(path or "")
    exists = Path(text).exists() if text else False
    return {"kind": kind, "path": text, "exists": exists}


def _checks(
    portfolio: dict[str, Any],
    regression_monitor: dict[str, Any],
    gate: dict[str, Any],
    portfolio_summary: dict[str, Any],
    monitor_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("portfolio_passed", portfolio.get("status") == "pass", portfolio.get("status"), "portfolio must pass"),
        _check("regression_monitor_passed", regression_monitor.get("status") == "pass", regression_monitor.get("status"), "regression monitor must pass"),
        _check("gate_passed", gate.get("status") == "pass", gate.get("status"), "gate must pass"),
        _check(
            "gate_ready",
            gate_summary.get("route_promotion_gate_ready") is True,
            gate_summary.get("route_promotion_gate_ready"),
            "gate summary must be ready",
        ),
        _check("active_routes_present", int(portfolio_summary.get("active_route_count") or 0) > 0, portfolio_summary.get("active_route_count"), "release packet needs active routes"),
        _check("no_lost_active_routes", int(monitor_summary.get("lost_active_route_count") or 0) == 0, monitor_summary.get("lost_active_route_count"), "release packet blocks active-route regressions"),
        _check("boundary_stable", monitor_summary.get("boundary_changed") is False, monitor_summary.get("boundary_changed"), "release packet boundary must be stable"),
        _check("claim_not_widened", monitor_summary.get("model_quality_claim_changed") is False, monitor_summary.get("model_quality_claim_changed"), "release packet claim must not widen"),
        _check("evidence_files_exist", all(row.get("exists") is True for row in evidence_rows), evidence_rows, "packet evidence source files must exist"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _packet(
    status: str,
    portfolio_summary: dict[str, Any],
    monitor_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    route_cards: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "packet_ready": status == "pass",
        "handoff_status": "ready_for_route_promotion_review" if status == "pass" else "blocked",
        "active_routes": portfolio_summary.get("active_routes") or [],
        "active_route_count": portfolio_summary.get("active_route_count"),
        "boundary": portfolio_summary.get("boundary"),
        "model_quality_claim": portfolio_summary.get("model_quality_claim"),
        "gate_decision": gate_summary.get("gate_decision"),
        "lost_active_route_count": monitor_summary.get("lost_active_route_count"),
        "boundary_changed": monitor_summary.get("boundary_changed"),
        "model_quality_claim_changed": monitor_summary.get("model_quality_claim_changed"),
        "route_cards": route_cards,
        "evidence_rows": evidence_rows,
    }


def _summary(status: str, checks: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "release_packet_ready": status == "pass" and packet.get("packet_ready") is True,
        "handoff_status": packet.get("handoff_status"),
        "active_route_count": packet.get("active_route_count"),
        "active_routes": packet.get("active_routes"),
        "boundary": packet.get("boundary"),
        "model_quality_claim": packet.get("model_quality_claim"),
        "evidence_count": len(packet.get("evidence_rows") or []),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_release_packet_ready"
    return "fix_model_capability_route_promotion_release_packet"


def _interpretation(status: str, packet: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route promotion release packet is blocked by missing evidence or failed gate inputs.",
            "next_action": "repair portfolio, regression monitor, gate, or evidence paths before handoff",
        }
    return {
        "model_quality_claim": packet.get("model_quality_claim"),
        "reason": "Portfolio, regression, and gate evidence are packaged for bounded route promotion review.",
        "next_action": "review the packet before adding any broader model-quality claim",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_RELEASE_PACKET_TEXT_FILENAME",
    "build_model_capability_route_promotion_release_packet",
    "locate_route_promotion_gate",
    "locate_route_promotion_portfolio",
    "locate_route_promotion_regression_monitor",
    "read_json_report",
    "resolve_exit_code",
]
