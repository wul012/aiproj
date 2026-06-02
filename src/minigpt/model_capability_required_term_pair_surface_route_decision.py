from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_baseline_contrast import PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_variant_selector import PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, markdown_cell, utc_now, write_json_payload


PAIR_SURFACE_ROUTE_DECISION_JSON_FILENAME = "model_capability_required_term_pair_surface_route_decision.json"
PAIR_SURFACE_ROUTE_DECISION_CSV_FILENAME = "model_capability_required_term_pair_surface_route_decision.csv"
PAIR_SURFACE_ROUTE_DECISION_TEXT_FILENAME = "model_capability_required_term_pair_surface_route_decision.txt"
PAIR_SURFACE_ROUTE_DECISION_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_route_decision.md"
PAIR_SURFACE_ROUTE_DECISION_HTML_FILENAME = "model_capability_required_term_pair_surface_route_decision.html"


def locate_surface_route_decision_contrast_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME
    return source


def locate_surface_route_decision_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_VARIANT_SELECTOR_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface route decision input must be a JSON object")
    return dict(payload)


def build_surface_route_decision(
    baseline_contrast: dict[str, Any],
    variant_selector: dict[str, Any],
    *,
    contrast_source_path: str | Path | None = None,
    selector_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    contrast_summary = as_dict(baseline_contrast.get("summary"))
    selected = as_dict(variant_selector.get("selected_variant"))
    issues = _issues(baseline_contrast, variant_selector, contrast_summary, selected)
    route = _route(contrast_summary, selected) if not issues else {}
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface route decision",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, route),
        "failed_count": len(issues),
        "issues": issues,
        "source_baseline_contrast_path": str(contrast_source_path or ""),
        "source_variant_selector_path": str(selector_source_path or ""),
        "route": route,
        "summary": _summary(route),
        "interpretation": _interpretation(status, route),
    }


def write_surface_route_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_ROUTE_DECISION_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_ROUTE_DECISION_CSV_FILENAME,
        "text": root / PAIR_SURFACE_ROUTE_DECISION_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_ROUTE_DECISION_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_ROUTE_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_text(report: dict[str, Any]) -> str:
    route = as_dict(report.get("route"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"selected_variant_id={route.get('selected_variant_id')}",
            f"current_route={route.get('current_route')}",
            f"recommended_next_route={route.get('recommended_next_route')}",
            f"promotion_allowed={route.get('promotion_allowed')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    route = as_dict(report.get("route"))
    rows = ["| Field | Value |", "| --- | --- |"]
    for key in ("selected_variant_id", "current_route", "recommended_next_route", "allowed_use", "blocked_use", "promotion_allowed"):
        rows.append(f"| {markdown_cell(key)} | {markdown_cell(route.get(key))} |")
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Route Decision",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    route = as_dict(report.get("route"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(
        f"<tr><td>{html_escape(key)}</td><td>{html_escape(route.get(key))}</td></tr>"
        for key in ("selected_variant_id", "current_route", "recommended_next_route", "allowed_use", "blocked_use", "promotion_allowed")
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface route decision</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface route decision</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Current</span><strong>{html_escape(route.get('current_route'))}</strong></div>
<div><span>Next</span><strong>{html_escape(route.get('recommended_next_route'))}</strong></div>
<div><span>Promotion</span><strong>{html_escape(route.get('promotion_allowed'))}</strong></div>
</section>
<section><h2>Route</h2><table><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _issues(
    baseline_contrast: dict[str, Any],
    variant_selector: dict[str, Any],
    contrast_summary: dict[str, Any],
    selected: dict[str, Any],
) -> list[dict[str, str]]:
    issues = []
    if baseline_contrast.get("status") != "pass":
        issues.append({"id": "bad_baseline_contrast_source", "detail": "source baseline contrast is not pass"})
    if variant_selector.get("status") != "pass":
        issues.append({"id": "bad_variant_selector_source", "detail": "source variant selector is not pass"})
    if not contrast_summary.get("contextual_anchor_required"):
        issues.append({"id": "contextual_anchor_boundary_missing", "detail": "baseline contrast must prove contextual anchor is required"})
    if not selected.get("variant_id"):
        issues.append({"id": "missing_selected_variant", "detail": "variant selector has no selected variant"})
    return issues


def _route(contrast_summary: dict[str, Any], selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_variant_id": selected.get("variant_id"),
        "current_route": "contextual_decode_aid_closeout",
        "recommended_next_route": "minimal_prompt_surface_objective",
        "allowed_use": "demo_and_diagnostic_contextual_decode",
        "blocked_use": "baseline_promotion_or_minimal_prompt_claim",
        "contextual_anchor_required": contrast_summary.get("contextual_anchor_required"),
        "stable_non_leaking_baseline_count": contrast_summary.get("stable_non_leaking_baseline_count"),
        "promotion_allowed": False,
    }


def _summary(route: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_variant_id": route.get("selected_variant_id", ""),
        "current_route": route.get("current_route", ""),
        "recommended_next_route": route.get("recommended_next_route", ""),
        "promotion_ready": False,
    }


def _decision(status: str, route: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_route_decision"
    if route.get("recommended_next_route") == "minimal_prompt_surface_objective":
        return "close_contextual_decode_branch_and_design_minimal_prompt_objective"
    return "continue_required_term_pair_surface_route"


def _interpretation(status: str, route: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Route decision inputs are invalid.", "next_action": "repair contrast or selector evidence"}
    return {
        "model_quality_claim": "contextual_decode_aid_not_baseline",
        "reason": "The selected contextual variant is useful, but the baseline contrast proves non-leaking prompts are still unstable.",
        "next_action": "close this branch and only start a new objective if minimal-prompt capability is required",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    route = as_dict(report.get("route"))
    fieldnames = ["selected_variant_id", "current_route", "recommended_next_route", "allowed_use", "blocked_use", "promotion_allowed"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({field: csv_cell(route.get(field)) for field in fieldnames})


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
</style>"""


__all__ = [
    "PAIR_SURFACE_ROUTE_DECISION_CSV_FILENAME",
    "PAIR_SURFACE_ROUTE_DECISION_HTML_FILENAME",
    "PAIR_SURFACE_ROUTE_DECISION_JSON_FILENAME",
    "PAIR_SURFACE_ROUTE_DECISION_MARKDOWN_FILENAME",
    "PAIR_SURFACE_ROUTE_DECISION_TEXT_FILENAME",
    "build_surface_route_decision",
    "locate_surface_route_decision_contrast_source",
    "locate_surface_route_decision_selector_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_route_decision_outputs",
]
