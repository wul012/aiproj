from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_first_token_route_decision import (
    PAIR_FIRST_TOKEN_ROUTE_DECISION_CSV_FILENAME,
    PAIR_FIRST_TOKEN_ROUTE_DECISION_HTML_FILENAME,
    PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME,
    PAIR_FIRST_TOKEN_ROUTE_DECISION_MARKDOWN_FILENAME,
    PAIR_FIRST_TOKEN_ROUTE_DECISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_first_token_route_decision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    selected = as_dict(report.get("selected_route"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("source_report_count", summary.get("source_report_count")),
        ("first_token_density_route_count", summary.get("first_token_density_route_count")),
        ("stable_route_count", summary.get("stable_route_count")),
        ("max_pair_full_seed_count", summary.get("max_pair_full_seed_count")),
        ("selected_source_label", selected.get("source_label")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_model_capability_required_term_pair_first_token_route_decision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    selected = as_dict(report.get("selected_route"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair First-Token Route Decision",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Source reports: `{summary.get('source_report_count')}`",
            f"- First-token density routes: `{summary.get('first_token_density_route_count')}`",
            f"- Stable routes: `{summary.get('stable_route_count')}`",
            f"- Selected route: `{selected.get('source_label')}`",
            f"- Source comparison: `{report.get('source_comparison')}`",
            "",
            "## Selected Route",
            "",
            *_selected_markdown_rows(selected),
            "",
            "## Rejected Routes",
            "",
            *_rejected_markdown_rows(report),
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_first_token_route_decision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    selected = as_dict(report.get("selected_route"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Source reports", summary.get("source_report_count")),
        ("Density routes", summary.get("first_token_density_route_count")),
        ("Stable routes", summary.get("stable_route_count")),
        ("Selected", selected.get("source_label")),
    ]
    rejected = "\n".join(_rejected_html(row) for row in list_of_dicts(report.get("rejected_routes")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT first-token route decision</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT first-token route decision</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Selected Route</h2>{_selected_html(selected)}</section>
<section class="panel"><h2>Rejected Routes</h2><div class="table-wrap"><table>
<thead><tr><th>Label</th><th>Corpus mode</th><th>Pair-full seeds</th><th>Reasons</th></tr></thead>
<tbody>{rejected}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel"><h2>Source Comparison</h2><p>{html_escape(report.get('source_comparison'))}</p></section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_first_token_route_decision_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_FIRST_TOKEN_ROUTE_DECISION_JSON_FILENAME,
        "csv": root / PAIR_FIRST_TOKEN_ROUTE_DECISION_CSV_FILENAME,
        "text": root / PAIR_FIRST_TOKEN_ROUTE_DECISION_TEXT_FILENAME,
        "markdown": root / PAIR_FIRST_TOKEN_ROUTE_DECISION_MARKDOWN_FILENAME,
        "html": root / PAIR_FIRST_TOKEN_ROUTE_DECISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_first_token_route_decision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_first_token_route_decision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_first_token_route_decision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["source_label", "corpus_mode", "pair_full_seed_count", "seed_count", "selected", "reasons"]
    selected = as_dict(report.get("selected_route"))
    rows = [
        {
            "source_label": selected.get("source_label"),
            "corpus_mode": selected.get("corpus_mode"),
            "pair_full_seed_count": selected.get("pair_full_seed_count"),
            "seed_count": selected.get("seed_count"),
            "selected": True,
            "reasons": selected.get("rationale"),
        },
        *[
            {
                "source_label": row.get("source_label"),
                "corpus_mode": row.get("corpus_mode"),
                "pair_full_seed_count": row.get("pair_full_seed_count"),
                "seed_count": row.get("seed_count"),
                "selected": False,
                "reasons": row.get("reasons"),
            }
            for row in list_of_dicts(report.get("rejected_routes"))
        ],
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _selected_markdown_rows(selected: dict[str, Any]) -> list[str]:
    return [
        "| Label | Corpus mode | Pair-full seeds | Stable | Rationale |",
        "| --- | --- | ---: | --- | --- |",
        "| "
        + " | ".join(
            [
                markdown_cell(selected.get("source_label")),
                markdown_cell(selected.get("corpus_mode")),
                markdown_cell(f"{selected.get('pair_full_seed_count')}/{selected.get('seed_count')}"),
                markdown_cell(selected.get("stable_pair_full")),
                markdown_cell(selected.get("rationale")),
            ]
        )
        + " |",
    ]


def _rejected_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ["| Label | Corpus mode | Pair-full seeds | Reasons |", "| --- | --- | ---: | --- |"]
    for row in list_of_dicts(report.get("rejected_routes")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("source_label")),
                    markdown_cell(row.get("corpus_mode")),
                    markdown_cell(f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"),
                    markdown_cell(",".join(str(reason) for reason in row.get("reasons", []))),
                ]
            )
            + " |"
        )
    return rows


def _selected_html(selected: dict[str, Any]) -> str:
    pair_full = _pair_full_display(selected)
    return (
        "<dl>"
        f"<dt>Label</dt><dd>{html_escape(selected.get('source_label'))}</dd>"
        f"<dt>Corpus mode</dt><dd>{html_escape(selected.get('corpus_mode'))}</dd>"
        f"<dt>Pair-full seeds</dt><dd>{html_escape(pair_full)}</dd>"
        f"<dt>Rationale</dt><dd>{html_escape(selected.get('rationale'))}</dd>"
        "</dl>"
    )


def _rejected_html(row: dict[str, Any]) -> str:
    pair_full = _pair_full_display(row)
    return (
        "<tr>"
        f"<td>{html_escape(row.get('source_label'))}</td>"
        f"<td>{html_escape(row.get('corpus_mode'))}</td>"
        f"<td>{html_escape(pair_full)}</td>"
        f"<td>{html_escape(','.join(str(reason) for reason in row.get('reasons', [])))}</td>"
        "</tr>"
    )


def _pair_full_display(row: dict[str, Any]) -> str:
    return f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
dt{font-weight:700;margin-top:8px}
dd{margin:3px 0 8px;color:var(--muted);overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_model_capability_required_term_pair_first_token_route_decision_html",
    "render_model_capability_required_term_pair_first_token_route_decision_markdown",
    "render_model_capability_required_term_pair_first_token_route_decision_text",
    "write_model_capability_required_term_pair_first_token_route_decision_outputs",
]
