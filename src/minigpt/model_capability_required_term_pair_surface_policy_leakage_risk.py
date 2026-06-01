from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_policy_minimality_check import (
    PAIR_SURFACE_POLICY_MINIMALITY_CHECK_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_surface_policy_selector import PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
from minigpt.report_utils import as_dict, html_escape, markdown_cell, utc_now, write_csv_row, write_json_payload


PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_leakage_risk.json"
PAIR_SURFACE_POLICY_LEAKAGE_RISK_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_leakage_risk.csv"
PAIR_SURFACE_POLICY_LEAKAGE_RISK_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_leakage_risk.txt"
PAIR_SURFACE_POLICY_LEAKAGE_RISK_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_leakage_risk.md"
PAIR_SURFACE_POLICY_LEAKAGE_RISK_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_leakage_risk.html"


def locate_selector_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_SELECTOR_JSON_FILENAME
    return source


def locate_minimality_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_MINIMALITY_CHECK_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy leakage risk input must be a JSON object")
    return dict(payload)


def build_surface_policy_leakage_risk(
    selector_report: dict[str, Any],
    minimality_report: dict[str, Any],
    *,
    selector_source_path: str | Path | None = None,
    minimality_source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    selected = as_dict(selector_report.get("selected_policy"))
    minimality_summary = as_dict(minimality_report.get("summary"))
    issues = _issues(selector_report, minimality_report, selected)
    risk_rows = _risk_rows(selected, minimality_summary)
    summary = _summary(risk_rows, selected)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy leakage risk",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_selector_path": str(selector_source_path or ""),
        "source_minimality_path": str(minimality_source_path or ""),
        "selected_policy": selected,
        "risk_rows": risk_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_policy_leakage_risk_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_POLICY_LEAKAGE_RISK_CSV_FILENAME,
        "text": root / PAIR_SURFACE_POLICY_LEAKAGE_RISK_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_POLICY_LEAKAGE_RISK_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_POLICY_LEAKAGE_RISK_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_csv_row(
        _csv_row(report),
        paths["csv"],
        [
            "status",
            "decision",
            "selected_policy_id",
            "risk_level",
            "risk_count",
            "promotion_allowed",
            "model_quality_claim",
        ],
    )
    paths["text"].write_text(render_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def render_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"selected_policy_id={summary.get('selected_policy_id')}",
            f"risk_level={summary.get('risk_level')}",
            f"promotion_allowed={summary.get('promotion_allowed')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = ["| Risk | Level | Detail |", "| --- | --- | --- |"]
    for row in report.get("risk_rows", []):
        rows.append(f"| {markdown_cell(row.get('id'))} | {markdown_cell(row.get('level'))} | {markdown_cell(row.get('detail'))} |")
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Policy Leakage Risk",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected policy: `{summary.get('selected_policy_id')}`",
            f"- Risk level: `{summary.get('risk_level')}`",
            f"- Promotion allowed: `{summary.get('promotion_allowed')}`",
            "",
            "## Risks",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    risk_rows = "".join(
        f"<tr><td>{html_escape(row.get('id'))}</td><td>{html_escape(row.get('level'))}</td><td>{html_escape(row.get('detail'))}</td></tr>"
        for row in report.get("risk_rows", [])
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>MiniGPT surface policy leakage risk</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface policy leakage risk</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Selected</span><strong>{html_escape(summary.get('selected_policy_id'))}</strong></div>
<div><span>Risk</span><strong>{html_escape(summary.get('risk_level'))}</strong></div>
<div><span>Promotion</span><strong>{html_escape(summary.get('promotion_allowed'))}</strong></div>
</section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section><h2>Risks</h2><table><thead><tr><th>Risk</th><th>Level</th><th>Detail</th></tr></thead><tbody>{risk_rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _issues(selector_report: dict[str, Any], minimality_report: dict[str, Any], selected: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if selector_report.get("status") != "pass":
        issues.append("source selector report is not pass")
    if minimality_report.get("status") != "pass":
        issues.append("source minimality report is not pass")
    if not selected:
        issues.append("selected policy is missing")
    return issues


def _csv_row(report: dict[str, Any]) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return {
        "status": report.get("status"),
        "decision": report.get("decision"),
        "selected_policy_id": summary.get("selected_policy_id"),
        "risk_level": summary.get("risk_level"),
        "risk_count": summary.get("risk_count"),
        "promotion_allowed": summary.get("promotion_allowed"),
        "model_quality_claim": interpretation.get("model_quality_claim"),
    }


def _risk_rows(selected: dict[str, Any], minimality_summary: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    if selected.get("leakage_level") == "contextual_anchor":
        rows.append({"id": "contextual_anchor", "level": "medium", "detail": "Prompt supplies the other term as an anchor."})
    if minimality_summary.get("contextual_anchor_required"):
        rows.append({"id": "minimal_prompt_not_stable", "level": "medium", "detail": "Non-leaking single-label baselines are not stable."})
    if selected.get("uses_boundary_sentence"):
        rows.append({"id": "boundary_wording_reuse", "level": "medium", "detail": "Policy reuses training boundary wording."})
    return rows


def _summary(risk_rows: list[dict[str, str]], selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_policy_id": selected.get("policy_id", ""),
        "risk_count": len(risk_rows),
        "risk_level": "medium" if risk_rows else "low",
        "promotion_allowed": False,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_leakage_inputs"
    if summary.get("risk_level") == "medium":
        return "required_term_pair_surface_policy_contextual_risk_documented"
    return "required_term_pair_surface_policy_low_risk"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Leakage-risk inputs are invalid.", "next_action": "repair input reports"}
    return {
        "model_quality_claim": "contextual_decode_policy_only",
        "reason": "The selected surface policy is useful but carries contextual-anchor risk.",
        "next_action": "run budget and surface-variant checks without treating the policy as model baseline",
    }


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1040px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
</style>"""


__all__ = [
    "PAIR_SURFACE_POLICY_LEAKAGE_RISK_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_LEAKAGE_RISK_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_LEAKAGE_RISK_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_LEAKAGE_RISK_TEXT_FILENAME",
    "build_surface_policy_leakage_risk",
    "locate_minimality_source",
    "locate_selector_source",
    "read_json_report",
    "render_html",
    "render_markdown",
    "render_text",
    "resolve_exit_code",
    "write_surface_policy_leakage_risk_outputs",
]
