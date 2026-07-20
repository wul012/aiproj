from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("policy_ready", summary.get("decoder_anchor_policy_ready")),
        ("policy_case_count", summary.get("policy_case_count")),
        ("uncovered_case_count", summary.get("uncovered_case_count")),
        ("coverage_is_partial", summary.get("coverage_is_partial")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "profile_id", "anchor", "anchor_length", "completion_hit_terms", "new_text_hit_terms", "claim_boundary", "recommended_use"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("policy_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('decoder_anchor_policy_ready')}`",
        f"- Policy cases: `{summary.get('policy_case_count')}`",
        f"- Uncovered cases: `{summary.get('uncovered_case_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        "",
        "## Policy Rows",
        "",
        "| Case | Profile | Anchor | Completion hits | Claim boundary | Use |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("policy_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(row.get("profile_id")), markdown_cell(row.get("anchor")), markdown_cell(",".join(str(item) for item in row.get("completion_hit_terms", []))), markdown_cell(row.get("claim_boundary")), markdown_cell(row.get("recommended_use"))]) + " |")
    lines.extend(["", "## Guardrails", "", "| ID | Severity | Detail |", "| --- | --- | --- |"])
    for row in list_of_dicts(report.get("guardrails")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("severity")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Policy cases", summary.get("policy_case_count")),
        ("Uncovered", summary.get("uncovered_case_count")),
        ("Partial", summary.get("coverage_is_partial")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    policy_rows = "".join(_policy_row(item) for item in list_of_dicts(report.get("policy_rows")))
    guardrail_rows = "".join(_guardrail_row(item) for item in list_of_dicts(report.get("guardrails")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy'))}</h1><p>Turns successful decoder anchor probe rows into a guarded policy for controlled replay. The policy is not promotion evidence.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Policy Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Profile</th><th>Anchor</th><th>Hits</th><th>Boundary</th><th>Use</th></tr></thead>
<tbody>{policy_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Guardrails</h2><div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Severity</th><th>Detail</th></tr></thead>
<tbody>{guardrail_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _policy_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('anchor'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('completion_hit_terms', [])))}</td>"
        f"<td>{html_escape(row.get('claim_boundary'))}</td>"
        f"<td>{html_escape(row.get('recommended_use'))}</td>"
        "</tr>"
    )


def _guardrail_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('severity'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#155e75}
*{box-sizing:border-box}
body{margin:0;background:#f0f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_html",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_text",
    "write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_outputs",
]
