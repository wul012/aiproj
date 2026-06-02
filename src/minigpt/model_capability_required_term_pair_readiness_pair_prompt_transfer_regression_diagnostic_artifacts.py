from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_pair_prompt_transfer_regression_diagnostic import (
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_CSV_FILENAME,
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_HTML_FILENAME,
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME,
    PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_pair_prompt_transfer_regression_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("direct_completion_default_hit_count", summary.get("direct_completion_default_hit_count")),
        ("transfer_default_hit_count", summary.get("transfer_default_hit_count")),
        ("transfer_hit_delta_from_direct", summary.get("transfer_hit_delta_from_direct")),
        ("fixed_regressed", summary.get("fixed_regressed")),
        ("pair_probe_exact_heldout_pair_full", summary.get("pair_probe_exact_heldout_pair_full")),
        ("transfer_route_closed", summary.get("transfer_route_closed")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_pair_prompt_transfer_regression_diagnostic_markdown(report: dict[str, Any]) -> str:
    rows = [
        "| Evidence | Kind | Hits | Pair-full | Missed | Decision |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("diagnostic_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("label")),
                    markdown_cell(row.get("kind")),
                    markdown_cell(row.get("default_hit_terms")),
                    markdown_cell(row.get("pair_full_observed")),
                    markdown_cell(row.get("default_missed_terms")),
                    markdown_cell(row.get("decision")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Pair Prompt Transfer Regression Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            "",
            "## Evidence Rows",
            "",
            *rows,
            "",
        ]
    )


def render_pair_prompt_transfer_regression_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Direct hits", summary.get("direct_completion_default_hit_count")),
        ("Transfer hits", summary.get("transfer_default_hit_count")),
        ("Hit delta", summary.get("transfer_hit_delta_from_direct")),
        ("Fixed regressed", summary.get("fixed_regressed")),
        ("Pair probe", summary.get("pair_probe_exact_heldout_pair_full")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    stat_html = "".join(
        f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"
        for label, value in stats
    )
    rows = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('kind'))}</td>"
        f"<td>{html_escape(row.get('default_hit_terms'))}</td>"
        f"<td>{html_escape(row.get('pair_full_observed'))}</td>"
        f"<td>{html_escape(row.get('default_missed_terms'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("diagnostic_rows"))
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair prompt transfer regression diagnostic</title>
<style>
:root{{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#92400e}}
*{{box-sizing:border-box}}
body{{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:28px}}
h1{{font-size:30px;margin:0 0 8px;letter-spacing:0}}
h2{{font-size:18px;margin:0 0 12px;letter-spacing:0}}
p{{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}}
.card,.panel{{background:white;border:1px solid var(--line);border-radius:8px}}
.card{{padding:14px}}
.card span{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}}
.card strong{{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}}
.panel{{padding:16px;margin:14px 0}}
.table-wrap{{overflow:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}}
th{{background:var(--panel);color:#334155}}
</style>
</head>
<body>
<main>
<header><h1>MiniGPT pair prompt transfer regression diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{stat_html}</section>
<section class="panel"><h2>Evidence Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Evidence</th><th>Kind</th><th>Hits</th><th>Pair-full</th><th>Missed</th><th>Decision</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_pair_prompt_transfer_regression_diagnostic_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["label", "kind", "default_hit_count", "pair_full_observed", "default_hit_terms", "default_missed_terms", "decision"]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("diagnostic_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_pair_prompt_transfer_regression_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_CSV_FILENAME,
        "text": root / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_PAIR_PROMPT_TRANSFER_REGRESSION_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_pair_prompt_transfer_regression_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_pair_prompt_transfer_regression_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_pair_prompt_transfer_regression_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_pair_prompt_transfer_regression_diagnostic_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


__all__ = [
    "render_pair_prompt_transfer_regression_diagnostic_html",
    "render_pair_prompt_transfer_regression_diagnostic_markdown",
    "render_pair_prompt_transfer_regression_diagnostic_text",
    "write_pair_prompt_transfer_regression_diagnostic_outputs",
]
