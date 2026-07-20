from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_CSV_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_HTML_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_TEXT_FILENAME,
    replay_rows,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_fixed_preserving_transfer_pair_probe_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("exact_heldout_pair_full", summary.get("exact_heldout_pair_full")),
        ("required_all_pair_full", summary.get("required_all_pair_full")),
        ("pair_full_count", summary.get("pair_full_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_fixed_preserving_transfer_pair_probe_replay_markdown(report: dict[str, Any]) -> str:
    rows = ["| Spec | Prompt | Required | Replay full | Default hits | Suppression hits |", "| --- | --- | --- | --- | --- | --- |"]
    for row in replay_rows(report):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("spec_id")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("required_for_ready")),
                    markdown_cell(row.get("replay_pair_full")),
                    markdown_cell(row.get("default_continuation_hit_count")),
                    markdown_cell(row.get("suppression_continuation_hit_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Fixed-Preserving Transfer Pair-Probe Replay",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Training decision: `{report.get('training_decision')}`",
            "",
            "## Replay Rows",
            "",
            *rows,
            "",
        ]
    )


def render_fixed_preserving_transfer_pair_probe_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Exact pair", summary.get("exact_heldout_pair_full")),
        ("Required all", summary.get("required_all_pair_full")),
        ("Pair-full count", summary.get("pair_full_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_row_html(row) for row in replay_rows(report))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT fixed-preserving transfer pair-probe replay</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT fixed-preserving transfer pair-probe replay</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Spec</th><th>Prompt</th><th>Required</th><th>Replay full</th><th>Default hits</th><th>Suppression hits</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_fixed_preserving_transfer_pair_probe_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "spec_id",
        "prompt",
        "required_for_ready",
        "replay_pair_full",
        "default_continuation_hit_count",
        "suppression_continuation_hit_count",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in replay_rows(report):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_fixed_preserving_transfer_pair_probe_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME,
        "csv": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_CSV_FILENAME,
        "text": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_fixed_preserving_transfer_pair_probe_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_fixed_preserving_transfer_pair_probe_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_fixed_preserving_transfer_pair_probe_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_fixed_preserving_transfer_pair_probe_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('spec_id'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('required_for_ready'))}</td>"
        f"<td>{html_escape(row.get('replay_pair_full'))}</td>"
        f"<td>{html_escape(row.get('default_continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('suppression_continuation_hit_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#1d4ed8}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
</style>"""


__all__ = [
    "render_fixed_preserving_transfer_pair_probe_replay_html",
    "render_fixed_preserving_transfer_pair_probe_replay_markdown",
    "render_fixed_preserving_transfer_pair_probe_replay_text",
    "write_fixed_preserving_transfer_pair_probe_replay_outputs",
]
