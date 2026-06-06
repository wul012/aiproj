from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_holdout_publication_registry_downstream_guard import (
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_CSV_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_HTML_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_MARKDOWN_FILENAME,
    RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_holdout_publication_registry_downstream_guard_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_holdout_publication_registry_downstream_guard_ready", summary.get("randomized_holdout_publication_registry_downstream_guard_ready")),
        ("guard_id", summary.get("guard_id")),
        ("guard_status", summary.get("guard_status")),
        ("entry_count", summary.get("entry_count")),
        ("downstream_ready", summary.get("downstream_ready")),
        ("lookup_ready", summary.get("lookup_ready")),
        ("contract_check_ready", summary.get("contract_check_ready")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("allowed_use", summary.get("allowed_use")),
        ("blocked_uses", summary.get("blocked_uses")),
        ("next_step", summary.get("next_step")),
        ("passed_check_count", summary.get("passed_check_count")),
        ("failed_check_count", summary.get("failed_check_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_holdout_publication_registry_downstream_guard_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["lookup_key", "entry_id", "registry_status", "bounded_publication_accepted", "promotion_ready", "consumer_boundary", "model_quality_claim"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("entry_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_randomized_holdout_publication_registry_downstream_guard_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized holdout publication registry downstream guard'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Guard ready: `{summary.get('randomized_holdout_publication_registry_downstream_guard_ready')}`",
        f"- Guard status: `{summary.get('guard_status')}`",
        f"- Downstream ready: `{summary.get('downstream_ready')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Allowed use: `{summary.get('allowed_use')}`",
        f"- Blocked uses: `{summary.get('blocked_uses')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Entries",
        "",
        "| Lookup key | Entry | Status | Bounded | Promotion | Boundary | Claim |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("entry_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("lookup_key")),
                    markdown_cell(row.get("entry_id")),
                    markdown_cell(row.get("registry_status")),
                    markdown_cell(row.get("bounded_publication_accepted")),
                    markdown_cell(row.get("promotion_ready")),
                    markdown_cell(row.get("consumer_boundary")),
                    markdown_cell(row.get("model_quality_claim")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_holdout_publication_registry_downstream_guard_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Guard ready", summary.get("randomized_holdout_publication_registry_downstream_guard_ready")),
        ("Downstream", summary.get("downstream_ready")),
        ("Lookup", summary.get("lookup_ready")),
        ("Promotion", summary.get("promotion_ready")),
        ("Failed", report.get("failed_count")),
    ]
    entries = "".join(_entry_row(row) for row in list_of_dicts(report.get("entry_rows")))
    checks = "".join(_check_row(row) for row in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream guard'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT randomized holdout publication registry downstream guard'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Guard Boundary</h2><dl>
<dt>Allowed use</dt><dd>{html_escape(summary.get('allowed_use'))}</dd>
<dt>Blocked uses</dt><dd>{html_escape(summary.get('blocked_uses'))}</dd>
<dt>Next step</dt><dd>{html_escape(summary.get('next_step'))}</dd>
</dl></section>
<section class="panel"><h2>Entries</h2><div class="table-wrap"><table>
<thead><tr><th>Lookup key</th><th>Entry</th><th>Status</th><th>Bounded</th><th>Promotion</th><th>Boundary</th><th>Claim</th></tr></thead>
<tbody>{entries}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{checks}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_randomized_holdout_publication_registry_downstream_guard_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_JSON_FILENAME,
        "csv": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_CSV_FILENAME,
        "text": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_GUARD_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_holdout_publication_registry_downstream_guard_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_holdout_publication_registry_downstream_guard_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_holdout_publication_registry_downstream_guard_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_holdout_publication_registry_downstream_guard_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _entry_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('lookup_key'))}</td>"
        f"<td>{html_escape(row.get('entry_id'))}</td>"
        f"<td>{html_escape(row.get('registry_status'))}</td>"
        f"<td>{html_escape(row.get('bounded_publication_accepted'))}</td>"
        f"<td>{html_escape(row.get('promotion_ready'))}</td>"
        f"<td>{html_escape(row.get('consumer_boundary'))}</td>"
        f"<td>{html_escape(row.get('model_quality_claim'))}</td>"
        "</tr>"
    )


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1160px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:16px;line-height:1.25;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
dl{display:grid;grid-template-columns:minmax(150px,220px) 1fr;gap:8px 16px;margin:0;font-size:14px}
dt{color:#334155;font-weight:700}
dd{margin:0;overflow-wrap:anywhere}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_randomized_holdout_publication_registry_downstream_guard_html",
    "render_randomized_holdout_publication_registry_downstream_guard_markdown",
    "render_randomized_holdout_publication_registry_downstream_guard_text",
    "write_randomized_holdout_publication_registry_downstream_guard_outputs",
]
