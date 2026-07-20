from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_history import MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, number_or_default, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME = "model_capability_route_promotion_portfolio.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_CSV_FILENAME = "model_capability_route_promotion_portfolio.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_TEXT_FILENAME = "model_capability_route_promotion_portfolio.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_MARKDOWN_FILENAME = "model_capability_route_promotion_portfolio.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_HTML_FILENAME = "model_capability_route_promotion_portfolio.html"


def locate_route_promotion_history(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_HISTORY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion portfolio input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_portfolio(
    history: dict[str, Any],
    *,
    source_history_path: str | Path | None = None,
    min_ready_routes: int = 1,
    required_boundary: str = "tiny_required_term_pair_probe_only",
    title: str = "MiniGPT model capability route promotion portfolio",
    generated_at: str | None = None,
) -> dict[str, Any]:
    entries = [_route_card(row, source_history_path=source_history_path, required_boundary=required_boundary) for row in list_of_dicts(history.get("entries"))]
    checks = _checks(history, entries, min_ready_routes=min_ready_routes, required_boundary=required_boundary)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    portfolio = _portfolio(status, entries, required_boundary)
    summary = _summary(status, entries, portfolio, checks)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_history_path": str(source_history_path or ""),
        "source_history": {
            "status": history.get("status"),
            "decision": history.get("decision"),
            "summary": as_dict(history.get("summary")),
            "readiness_requirement": as_dict(history.get("readiness_requirement")),
        },
        "check_rows": checks,
        "route_cards": entries,
        "portfolio": portfolio,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_portfolio: bool) -> int:
    return 1 if require_ready_portfolio and report.get("status") != "pass" else 0


def _route_card(row: dict[str, Any], *, source_history_path: str | Path | None, required_boundary: str) -> dict[str, Any]:
    boundary = str(row.get("boundary") or "")
    ready = row.get("promotion_readiness") == "ready" and boundary == required_boundary
    return {
        "name": row.get("name"),
        "route_id": row.get("route_id"),
        "portfolio_status": "active" if ready else "blocked",
        "promotion_readiness": row.get("promotion_readiness"),
        "route_status": row.get("route_status"),
        "history_entry_status": row.get("history_entry_status"),
        "boundary": boundary,
        "boundary_matches": boundary == required_boundary,
        "model_quality_claim": row.get("model_quality_claim") or "not_claimed",
        "seed_count": number_or_default(row.get("seed_count"), 0, int),
        "min_pair_full_count": row.get("min_pair_full_count"),
        "pair_full_strength_spread": row.get("pair_full_strength_spread"),
        "source_history_path": str(source_history_path or ""),
        "source_manifest_path": row.get("source_manifest_path") or "",
        "source_acceptance_review_path": row.get("source_acceptance_review_path") or "",
        "source_seed_stability_rollup_path": row.get("source_seed_stability_rollup_path") or "",
    }


def _checks(
    history: dict[str, Any],
    route_cards: list[dict[str, Any]],
    *,
    min_ready_routes: int,
    required_boundary: str,
) -> list[dict[str, Any]]:
    summary = as_dict(history.get("summary"))
    requirement = as_dict(history.get("readiness_requirement"))
    ready_routes = [row for row in route_cards if row.get("portfolio_status") == "active"]
    boundary_mismatches = [row for row in route_cards if row.get("boundary_matches") is not True]
    blocked = [row for row in route_cards if row.get("portfolio_status") != "active"]
    bounded_claims = all(str(row.get("model_quality_claim") or "").startswith("seed_stable_pair_probe_route") for row in route_cards)
    return [
        _check("history_passed", history.get("status") == "pass", history.get("status"), "source history must pass"),
        _check("history_readiness_passed", requirement.get("status") == "pass", requirement.get("status"), "source history readiness requirement must pass"),
        _check(
            "minimum_ready_routes",
            len(ready_routes) >= max(0, int(min_ready_routes)),
            {"ready": len(ready_routes), "required": max(0, int(min_ready_routes))},
            "portfolio must carry enough active route promotions",
        ),
        _check("no_blocked_routes", not blocked, len(blocked), "route portfolio should not include blocked routes"),
        _check("no_boundary_mismatches", not boundary_mismatches, len(boundary_mismatches), "all routes must keep the required boundary"),
        _check("boundary_matches_history", summary.get("required_boundary") == required_boundary, summary.get("required_boundary"), "history boundary must match portfolio boundary"),
        _check("claims_are_bounded", bounded_claims, [row.get("model_quality_claim") for row in route_cards], "claims must remain pair-probe scoped"),
    ]


def _portfolio(status: str, route_cards: list[dict[str, Any]], required_boundary: str) -> dict[str, Any]:
    active = [row for row in route_cards if row.get("portfolio_status") == "active"]
    blocked = [row for row in route_cards if row.get("portfolio_status") != "active"]
    return {
        "portfolio_type": "model_capability_route_promotion",
        "portfolio_ready": status == "pass",
        "boundary": required_boundary,
        "active_routes": [row.get("route_id") for row in active],
        "blocked_routes": [row.get("route_id") for row in blocked],
        "route_count": len(route_cards),
        "active_route_count": len(active),
        "blocked_route_count": len(blocked),
        "next_consumers": ["route_promotion_regression_monitor", "model_capability_portfolio_review"],
    }


def _summary(status: str, route_cards: list[dict[str, Any]], portfolio: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    claims = sorted({str(row.get("model_quality_claim")) for row in route_cards if row.get("model_quality_claim")})
    return {
        "route_promotion_portfolio_ready": status == "pass",
        "route_count": len(route_cards),
        "active_route_count": portfolio.get("active_route_count"),
        "blocked_route_count": portfolio.get("blocked_route_count"),
        "active_routes": portfolio.get("active_routes"),
        "boundary": portfolio.get("boundary"),
        "model_quality_claim": claims[0] if len(claims) == 1 else "mixed_or_not_claimed",
        "min_seed_count": min((int(row.get("seed_count") or 0) for row in route_cards), default=0),
        "min_pair_full_count": min(
            (int(row.get("min_pair_full_count") or 0) for row in route_cards if row.get("min_pair_full_count") is not None),
            default=0,
        ),
        "max_pair_full_strength_spread": max(
            (int(row.get("pair_full_strength_spread") or 0) for row in route_cards if row.get("pair_full_strength_spread") is not None),
            default=0,
        ),
        "passed_check_count": sum(1 for row in checks if row["status"] == "pass"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_portfolio_ready"
    return "fix_model_capability_route_promotion_portfolio"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The route promotion history is not ready to become a portfolio snapshot.",
            "next_action": "repair route history readiness or boundary mismatches before portfolio review",
        }
    routes = ", ".join(str(item) for item in summary.get("active_routes", [])) or "none"
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": f"Ready route promotions are now grouped into a bounded portfolio snapshot: {routes}.",
        "next_action": "use the portfolio snapshot as input to route regression monitoring",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_PORTFOLIO_TEXT_FILENAME",
    "build_model_capability_route_promotion_portfolio",
    "locate_route_promotion_history",
    "read_json_report",
    "resolve_exit_code",
]
