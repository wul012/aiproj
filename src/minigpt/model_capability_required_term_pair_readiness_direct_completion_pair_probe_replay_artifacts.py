from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay_artifacts import (
    write_model_capability_required_term_pair_generation_profile_replay_outputs,
)
from minigpt.model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay import (
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_CSV_FILENAME,
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_HTML_FILENAME,
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME,
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME,
    PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_direct_completion_pair_probe_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("prompt_spec_count", summary.get("prompt_spec_count")),
        ("pair_full_count", summary.get("pair_full_count")),
        ("required_all_pair_full", summary.get("required_all_pair_full")),
        ("exact_heldout_pair_full", summary.get("exact_heldout_pair_full")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_direct_completion_pair_probe_replay_markdown(report: dict[str, Any]) -> str:
    rows = ["| Spec | Prompt | Required | Pair-full | Default full | Suppression full |", "| --- | --- | --- | --- | ---: | ---: |"]
    for row in list_of_dicts(report.get("replay_rows")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("spec_id")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("required_for_ready")),
                    markdown_cell(row.get("replay_pair_full")),
                    markdown_cell(row.get("default_pair_full_variant_count")),
                    markdown_cell(row.get("suppression_pair_full_variant_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Pair-Readiness Direct-Completion Pair-Probe Replay",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Selected training report: `{report.get('selected_training_report')}`",
            "",
            "## Replay Rows",
            "",
            *rows,
            "",
        ]
    )


def render_direct_completion_pair_probe_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Specs", summary.get("prompt_spec_count")),
        ("Pair-full", f"{summary.get('pair_full_count')}/{summary.get('row_count')}"),
        ("Required all", summary.get("required_all_pair_full")),
        ("Exact pair", summary.get("exact_heldout_pair_full")),
    ]
    rows = "".join(_row_html(row) for row in list_of_dicts(report.get("replay_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT direct-completion pair-probe replay</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT direct-completion pair-probe replay</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Selected Training Report</h2><p>{html_escape(report.get('selected_training_report'))}</p></section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Spec</th><th>Prompt</th><th>Required</th><th>Pair-full</th><th>Default full</th><th>Suppression full</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_direct_completion_pair_probe_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "spec_id",
        "prompt",
        "required_for_ready",
        "status",
        "replay_decision",
        "replay_pair_full",
        "default_pair_full_variant_count",
        "suppression_pair_full_variant_count",
        "default_continuation_hit_count",
        "suppression_continuation_hit_count",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("replay_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_direct_completion_pair_probe_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    sidecar_outputs = {}
    for entry in list_of_dicts(report.get("replay_reports")):
        spec_id = str(entry.get("spec_id"))
        child = as_dict(entry.get("report"))
        if spec_id and child:
            sidecar_outputs[spec_id] = write_model_capability_required_term_pair_generation_profile_replay_outputs(
                child,
                root / "pair-probe-replay-reports" / spec_id,
            )
    report["sidecar_outputs"] = {"replay_reports": sidecar_outputs}
    paths = {
        "json": root / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_JSON_FILENAME,
        "csv": root / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_CSV_FILENAME,
        "text": root / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_TEXT_FILENAME,
        "markdown": root / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME,
        "html": root / PAIR_READINESS_DIRECT_COMPLETION_PAIR_PROBE_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_direct_completion_pair_probe_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_direct_completion_pair_probe_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_direct_completion_pair_probe_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_direct_completion_pair_probe_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('spec_id'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('required_for_ready'))}</td>"
        f"<td>{html_escape(row.get('replay_pair_full'))}</td>"
        f"<td>{html_escape(row.get('default_pair_full_variant_count'))}</td>"
        f"<td>{html_escape(row.get('suppression_pair_full_variant_count'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#166534}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
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
    "render_direct_completion_pair_probe_replay_html",
    "render_direct_completion_pair_probe_replay_markdown",
    "render_direct_completion_pair_probe_replay_text",
    "write_direct_completion_pair_probe_replay_outputs",
]
