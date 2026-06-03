from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_portfolio import MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME = "model_capability_route_promotion_regression_monitor.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_CSV_FILENAME = "model_capability_route_promotion_regression_monitor.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_TEXT_FILENAME = "model_capability_route_promotion_regression_monitor.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_MARKDOWN_FILENAME = "model_capability_route_promotion_regression_monitor.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_HTML_FILENAME = "model_capability_route_promotion_regression_monitor.html"


def locate_route_promotion_portfolio(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion regression monitor input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_regression_monitor(
    current_portfolio: dict[str, Any],
    *,
    baseline_portfolio: dict[str, Any] | None = None,
    current_path: str | Path | None = None,
    baseline_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion regression monitor",
    generated_at: str | None = None,
) -> dict[str, Any]:
    baseline = baseline_portfolio or current_portfolio
    route_deltas = _route_deltas(baseline, current_portfolio)
    checks = _checks(baseline, current_portfolio, route_deltas)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, baseline, current_portfolio, route_deltas, checks)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "baseline_path": str(baseline_path or current_path or ""),
        "current_path": str(current_path or ""),
        "baseline_summary": as_dict(baseline.get("summary")),
        "current_summary": as_dict(current_portfolio.get("summary")),
        "check_rows": checks,
        "route_deltas": route_deltas,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _route_deltas(baseline: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_cards = _cards_by_route(baseline)
    current_cards = _cards_by_route(current)
    rows: list[dict[str, Any]] = []
    for route_id in sorted(set(baseline_cards) | set(current_cards)):
        base = baseline_cards.get(route_id, {})
        cur = current_cards.get(route_id, {})
        base_status = base.get("portfolio_status") or "missing"
        current_status = cur.get("portfolio_status") or "missing"
        relation = _relation(base_status, current_status)
        rows.append(
            {
                "route_id": route_id,
                "baseline_status": base_status,
                "current_status": current_status,
                "relation": relation,
                "baseline_boundary": base.get("boundary") or "",
                "current_boundary": cur.get("boundary") or "",
                "baseline_claim": base.get("model_quality_claim") or "not_claimed",
                "current_claim": cur.get("model_quality_claim") or "not_claimed",
                "baseline_seed_count": base.get("seed_count"),
                "current_seed_count": cur.get("seed_count"),
            }
        )
    return rows


def _cards_by_route(portfolio: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cards = {}
    for row in list_of_dicts(portfolio.get("route_cards")):
        route_id = str(row.get("route_id") or "")
        if route_id:
            cards[route_id] = row
    return cards


def _relation(baseline_status: Any, current_status: Any) -> str:
    if baseline_status == "active" and current_status == "active":
        return "stable_active"
    if baseline_status == "active" and current_status != "active":
        return "lost_active_route"
    if baseline_status != "active" and current_status == "active":
        return "gained_active_route"
    return "stable_blocked_or_missing"


def _checks(baseline: dict[str, Any], current: dict[str, Any], route_deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline_summary = as_dict(baseline.get("summary"))
    current_summary = as_dict(current.get("summary"))
    lost = [row for row in route_deltas if row.get("relation") == "lost_active_route"]
    boundary_changes = [row for row in route_deltas if row.get("baseline_boundary") and row.get("current_boundary") and row.get("baseline_boundary") != row.get("current_boundary")]
    claim_widened = [row for row in route_deltas if _claim_widened(row.get("baseline_claim"), row.get("current_claim"))]
    return [
        _check("baseline_portfolio_passed", baseline.get("status") == "pass", baseline.get("status"), "baseline portfolio must pass"),
        _check("current_portfolio_passed", current.get("status") == "pass", current.get("status"), "current portfolio must pass"),
        _check(
            "current_portfolio_ready",
            current_summary.get("route_promotion_portfolio_ready") is True,
            current_summary.get("route_promotion_portfolio_ready"),
            "current portfolio must be ready",
        ),
        _check("no_active_route_loss", not lost, [row.get("route_id") for row in lost], "current portfolio must not lose baseline active routes"),
        _check(
            "no_boundary_changes",
            baseline_summary.get("boundary") == current_summary.get("boundary") and not boundary_changes,
            {"baseline": baseline_summary.get("boundary"), "current": current_summary.get("boundary"), "route_changes": len(boundary_changes)},
            "portfolio boundary must stay stable",
        ),
        _check("no_claim_widening", not claim_widened, [row.get("route_id") for row in claim_widened], "model quality claim must not widen"),
        _check(
            "active_route_count_not_decreased",
            int(current_summary.get("active_route_count") or 0) >= int(baseline_summary.get("active_route_count") or 0),
            {"baseline": baseline_summary.get("active_route_count"), "current": current_summary.get("active_route_count")},
            "active route count must not decrease",
        ),
    ]


def _claim_widened(baseline_claim: Any, current_claim: Any) -> bool:
    base = str(baseline_claim or "")
    cur = str(current_claim or "")
    if cur in {"", "not_claimed"}:
        return False
    if cur.startswith("seed_stable_pair_probe_route"):
        return False
    return cur != base


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    baseline: dict[str, Any],
    current: dict[str, Any],
    route_deltas: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_summary = as_dict(baseline.get("summary"))
    current_summary = as_dict(current.get("summary"))
    return {
        "regression_monitor_passed": status == "pass",
        "baseline_active_route_count": baseline_summary.get("active_route_count"),
        "current_active_route_count": current_summary.get("active_route_count"),
        "lost_active_route_count": sum(1 for row in route_deltas if row.get("relation") == "lost_active_route"),
        "gained_active_route_count": sum(1 for row in route_deltas if row.get("relation") == "gained_active_route"),
        "boundary_changed": baseline_summary.get("boundary") != current_summary.get("boundary"),
        "baseline_boundary": baseline_summary.get("boundary"),
        "current_boundary": current_summary.get("boundary"),
        "model_quality_claim_changed": baseline_summary.get("model_quality_claim") != current_summary.get("model_quality_claim"),
        "baseline_model_quality_claim": baseline_summary.get("model_quality_claim"),
        "current_model_quality_claim": current_summary.get("model_quality_claim"),
        "route_delta_count": len(route_deltas),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_regression_monitor_passed"
    return "fix_model_capability_route_promotion_regressions"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The current route promotion portfolio regressed against its baseline.",
            "next_action": "repair lost active routes, boundary changes, or widened claims before accepting the portfolio",
        }
    return {
        "model_quality_claim": summary.get("current_model_quality_claim"),
        "reason": "No active route loss, boundary change, or claim widening was detected.",
        "next_action": "use this monitor as the regression guard for the next route portfolio update",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_REGRESSION_TEXT_FILENAME",
    "build_model_capability_route_promotion_regression_monitor",
    "locate_route_promotion_portfolio",
    "read_json_report",
    "resolve_exit_code",
]
