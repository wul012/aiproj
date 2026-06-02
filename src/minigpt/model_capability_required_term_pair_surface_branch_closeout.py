from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_surface_baseline_contrast import PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_failure_diagnostic import PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_budget_sweep import PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_leakage_risk import PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_policy_replay import PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_route_decision import PAIR_SURFACE_ROUTE_DECISION_JSON_FILENAME
from minigpt.model_capability_required_term_pair_surface_variant_replay import PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME
from minigpt.report_utils import as_dict, csv_cell, html_escape, markdown_cell, utc_now, write_json_payload


PAIR_SURFACE_BRANCH_CLOSEOUT_JSON_FILENAME = "model_capability_required_term_pair_surface_branch_closeout.json"
PAIR_SURFACE_BRANCH_CLOSEOUT_CSV_FILENAME = "model_capability_required_term_pair_surface_branch_closeout.csv"
PAIR_SURFACE_BRANCH_CLOSEOUT_TEXT_FILENAME = "model_capability_required_term_pair_surface_branch_closeout.txt"
PAIR_SURFACE_BRANCH_CLOSEOUT_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_branch_closeout.md"
PAIR_SURFACE_BRANCH_CLOSEOUT_HTML_FILENAME = "model_capability_required_term_pair_surface_branch_closeout.html"

SOURCE_FILENAMES = {
    "surface_failure": PAIR_SURFACE_FAILURE_DIAGNOSTIC_JSON_FILENAME,
    "policy_replay": PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME,
    "leakage_risk": PAIR_SURFACE_POLICY_LEAKAGE_RISK_JSON_FILENAME,
    "budget_sweep": PAIR_SURFACE_POLICY_BUDGET_SWEEP_JSON_FILENAME,
    "variant_replay": PAIR_SURFACE_VARIANT_REPLAY_JSON_FILENAME,
    "baseline_contrast": PAIR_SURFACE_BASELINE_CONTRAST_JSON_FILENAME,
    "route_decision": PAIR_SURFACE_ROUTE_DECISION_JSON_FILENAME,
}


def locate_closeout_source(path: str | Path, source_id: str) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / SOURCE_FILENAMES[source_id]
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface branch closeout input must be a JSON object")
    return dict(payload)


def build_surface_branch_closeout(
    reports: dict[str, dict[str, Any]],
    *,
    source_paths: dict[str, str | Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_paths = source_paths or {}
    rows = _milestone_rows(reports)
    issues = _issues(reports, rows)
    summary = _summary(reports, rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface branch closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_paths": {key: str(value) for key, value in source_paths.items()},
        "milestone_rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def write_surface_branch_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SURFACE_BRANCH_CLOSEOUT_JSON_FILENAME,
        "csv": root / PAIR_SURFACE_BRANCH_CLOSEOUT_CSV_FILENAME,
        "text": root / PAIR_SURFACE_BRANCH_CLOSEOUT_TEXT_FILENAME,
        "markdown": root / PAIR_SURFACE_BRANCH_CLOSEOUT_MARKDOWN_FILENAME,
        "html": root / PAIR_SURFACE_BRANCH_CLOSEOUT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
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
            f"milestone_count={summary.get('milestone_count')}",
            f"contextual_decode_aid_ready={summary.get('contextual_decode_aid_ready')}",
            f"promotion_allowed={summary.get('promotion_allowed')}",
            f"recommended_next_route={summary.get('recommended_next_route')}",
            f"model_quality_claim={interpretation.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_markdown(report: dict[str, Any]) -> str:
    rows = ["| Milestone | Version | Status | Finding |", "| --- | --- | --- | --- |"]
    for row in report.get("milestone_rows", []):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("version")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("finding")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Surface Branch Closeout",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            *rows,
            "",
        ]
    )


def render_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = "".join(_row_html(row) for row in report.get("milestone_rows", []))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>MiniGPT surface branch closeout</title>{_style()}</head>
<body><main>
<h1>MiniGPT surface branch closeout</h1>
<p>{html_escape(interpretation.get('reason'))}</p>
<section class="stats">
<div><span>Milestones</span><strong>{html_escape(summary.get('milestone_count'))}</strong></div>
<div><span>Contextual aid</span><strong>{html_escape(summary.get('contextual_decode_aid_ready'))}</strong></div>
<div><span>Next route</span><strong>{html_escape(summary.get('recommended_next_route'))}</strong></div>
</section>
<section><h2>Milestones</h2><table><thead><tr><th>Id</th><th>Version</th><th>Status</th><th>Finding</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _milestone_rows(reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _row("surface_failure", "v679", reports, as_dict(reports.get("surface_failure", {}).get("summary")).get("surface_failure_seeds"), "isolated generation surface failure"),
        _row("policy_replay", "v681", reports, as_dict(reports.get("policy_replay", {}).get("summary")).get("stable_pair_full_policy_ids"), "contextual policies recover pair-full"),
        _row("leakage_risk", "v684", reports, as_dict(reports.get("leakage_risk", {}).get("summary")).get("risk_level"), "contextual-anchor risk documented"),
        _row("budget_sweep", "v685", reports, as_dict(reports.get("budget_sweep", {}).get("summary")).get("minimal_stable_budget"), "minimal stable budget selected"),
        _row("variant_replay", "v688", reports, as_dict(reports.get("variant_replay", {}).get("summary")).get("stable_variant_ids"), "surface variants stable"),
        _row("baseline_contrast", "v690", reports, as_dict(reports.get("baseline_contrast", {}).get("summary")).get("contextual_anchor_required"), "non-leaking baselines remain unstable"),
        _row("route_decision", "v691", reports, as_dict(reports.get("route_decision", {}).get("summary")).get("recommended_next_route"), "route closed to contextual decode aid"),
    ]


def _row(source_id: str, version: str, reports: dict[str, dict[str, Any]], value: Any, finding: str) -> dict[str, Any]:
    report = reports.get(source_id, {})
    return {"id": source_id, "version": version, "status": report.get("status", "missing"), "decision": report.get("decision", ""), "value": value, "finding": finding}


def _issues(reports: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    issues = []
    for source_id in SOURCE_FILENAMES:
        if source_id not in reports:
            issues.append({"id": f"missing_{source_id}", "detail": f"{source_id} report is missing"})
    for row in rows:
        if row.get("status") != "pass":
            issues.append({"id": f"bad_{row.get('id')}", "detail": f"{row.get('id')} report is not pass"})
    return issues


def _summary(reports: dict[str, dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_summary = as_dict(reports.get("route_decision", {}).get("summary"))
    route = as_dict(reports.get("route_decision", {}).get("route"))
    return {
        "milestone_count": len(rows),
        "passed_milestone_count": sum(1 for row in rows if row.get("status") == "pass"),
        "contextual_decode_aid_ready": route_summary.get("current_route") == "contextual_decode_aid_closeout",
        "promotion_allowed": False,
        "recommended_next_route": route_summary.get("recommended_next_route") or route.get("recommended_next_route"),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_branch_closeout"
    if summary.get("contextual_decode_aid_ready"):
        return "required_term_pair_surface_branch_closed_as_contextual_decode_aid"
    return "required_term_pair_surface_branch_not_closed"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, str]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Closeout inputs are incomplete.", "next_action": "repair missing or failed milestone evidence"}
    return {
        "model_quality_claim": "contextual_decode_aid_closed_branch",
        "reason": "The branch produced a stable contextual decode aid but did not produce a promotable minimal-prompt baseline.",
        "next_action": "run final verification, then treat minimal-prompt capability as a new objective if needed",
    }


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "version", "status", "decision", "value", "finding"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in report.get("milestone_rows", []):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('version'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('finding'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
body{margin:0;background:#eef2f5;color:#172026;font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:18px 0}
.stats div,section{background:white;border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:14px 0}
span{display:block;color:#5d6975;font-size:12px;text-transform:uppercase}strong{display:block;color:#0f766e;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid #d8dee4;padding:9px;text-align:left;vertical-align:top}
th{background:#f7f9fb;color:#334155}
</style>"""


__all__ = [
    "PAIR_SURFACE_BRANCH_CLOSEOUT_CSV_FILENAME",
    "PAIR_SURFACE_BRANCH_CLOSEOUT_HTML_FILENAME",
    "PAIR_SURFACE_BRANCH_CLOSEOUT_JSON_FILENAME",
    "PAIR_SURFACE_BRANCH_CLOSEOUT_MARKDOWN_FILENAME",
    "PAIR_SURFACE_BRANCH_CLOSEOUT_TEXT_FILENAME",
    "SOURCE_FILENAMES",
    "build_surface_branch_closeout",
    "locate_closeout_source",
    "read_json_report",
    "resolve_exit_code",
    "write_surface_branch_closeout_outputs",
]
