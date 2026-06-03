from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("replay_ready", summary.get("decoder_anchor_policy_replay_ready")),
        ("passed_case_count", summary.get("passed_case_count")),
        ("policy_applied_case_count", summary.get("policy_applied_case_count")),
        ("policy_applied_pass_count", summary.get("policy_applied_pass_count")),
        ("policy_replay_success", summary.get("policy_replay_success")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "policy_applied", "profile_id", "anchor", "case_pass", "combined_hit_terms", "new_text_hit_terms", "missed_terms"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("replay_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy replay'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('decoder_anchor_policy_replay_ready')}`",
        f"- Passed cases: `{summary.get('passed_case_count')}/{summary.get('case_count')}`",
        f"- Policy applied: `{summary.get('policy_applied_case_count')}`",
        f"- Policy applied pass: `{summary.get('policy_applied_pass_count')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        "",
        "## Replay Rows",
        "",
        "| Case | Policy | Profile | Anchor | Pass | Combined hits | New hits | Misses |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("replay_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("policy_applied")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("anchor")),
                    markdown_cell(row.get("case_pass")),
                    markdown_cell(",".join(str(item) for item in row.get("combined_hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("new_text_hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Passed", f"{summary.get('passed_case_count')}/{summary.get('case_count')}"),
        ("Applied", summary.get("policy_applied_case_count")),
        ("Applied pass", summary.get("policy_applied_pass_count")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("replay_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy replay'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor policy replay'))}</h1><p>Replays a guarded decoder-anchor policy. Passing anchored rows remain anchor-assisted and do not unblock promotion.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Policy</th><th>Profile</th><th>Anchor</th><th>Pass</th><th>Combined hits</th><th>New hits</th><th>Misses</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('policy_applied'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('anchor'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('combined_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('new_text_hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


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
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_html",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_text",
    "write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_outputs",
]
