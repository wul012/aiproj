from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay_artifacts import (
    write_model_capability_required_term_pair_generation_profile_replay_outputs,
)
from minigpt.model_capability_required_term_pair_seed_config_replay import (
    PAIR_SEED_CONFIG_REPLAY_CSV_FILENAME,
    PAIR_SEED_CONFIG_REPLAY_HTML_FILENAME,
    PAIR_SEED_CONFIG_REPLAY_JSON_FILENAME,
    PAIR_SEED_CONFIG_REPLAY_MARKDOWN_FILENAME,
    PAIR_SEED_CONFIG_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_seed_config_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("seed_count", summary.get("seed_count")),
        ("replay_pair_full_seed_count", summary.get("replay_pair_full_seed_count")),
        ("selected_replay_ready", summary.get("selected_replay_ready")),
        ("policy_replay_gap_count", summary.get("policy_replay_gap_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_seed_config_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "selected_config_id",
        "status",
        "policy_selected_pair_full",
        "replay_pair_full",
        "default_pair_full_variant_count",
        "suppression_pair_full_variant_count",
        "top_k",
        "temperature",
        "replay_decision",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("replay_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_seed_config_replay_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    replay_rows = [
        "| Seed | Selected config | Replay full | Default full | Suppression full |",
        "| ---: | --- | --- | ---: | ---: |",
    ]
    for row in list_of_dicts(report.get("replay_rows")):
        replay_rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("selected_config_id")),
                    markdown_cell(row.get("replay_pair_full")),
                    markdown_cell(row.get("default_pair_full_variant_count")),
                    markdown_cell(row.get("suppression_pair_full_variant_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Seed Config Replay",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Replay pair-full seeds: `{summary.get('replay_pair_full_seed_count')}/{summary.get('seed_count')}`",
            f"- Selected replay ready: `{summary.get('selected_replay_ready')}`",
            "",
            "## Replay Rows",
            "",
            *replay_rows,
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_seed_config_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Replay pair-full", f"{summary.get('replay_pair_full_seed_count')}/{summary.get('seed_count')}"),
        ("Ready", summary.get("selected_replay_ready")),
        ("Policy gaps", summary.get("policy_replay_gap_count")),
    ]
    replay_rows = "\n".join(_row_html(row) for row in list_of_dicts(report.get("replay_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair seed config replay</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair seed config replay</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Replay Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Selected config</th><th>Replay full</th><th>Default full</th><th>Suppression full</th><th>Decode</th></tr></thead>
<tbody>{replay_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_seed_config_replay_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    sidecar_outputs = {}
    for entry in list_of_dicts(report.get("replay_reports")):
        config_id = str(entry.get("config_id"))
        seed = entry.get("seed")
        child = as_dict(entry.get("report"))
        if config_id and seed and child:
            sidecar_outputs[f"{config_id}/seed-{seed}"] = write_model_capability_required_term_pair_generation_profile_replay_outputs(
                child,
                root / "replay-reports" / config_id / f"seed-{seed}",
            )
    report["sidecar_outputs"] = {"replay_reports": sidecar_outputs}
    paths = {
        "json": root / PAIR_SEED_CONFIG_REPLAY_JSON_FILENAME,
        "csv": root / PAIR_SEED_CONFIG_REPLAY_CSV_FILENAME,
        "text": root / PAIR_SEED_CONFIG_REPLAY_TEXT_FILENAME,
        "markdown": root / PAIR_SEED_CONFIG_REPLAY_MARKDOWN_FILENAME,
        "html": root / PAIR_SEED_CONFIG_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_seed_config_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_seed_config_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_seed_config_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_seed_config_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row_html(row: dict[str, Any]) -> str:
    decode = f"k={row.get('top_k')} t={row.get('temperature')}"
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('selected_config_id'))}</td>"
        f"<td>{html_escape(row.get('replay_pair_full'))}</td>"
        f"<td>{html_escape(row.get('default_pair_full_variant_count'))}</td>"
        f"<td>{html_escape(row.get('suppression_pair_full_variant_count'))}</td>"
        f"<td>{html_escape(decode)}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:18px 0}
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
    "render_model_capability_required_term_pair_seed_config_replay_html",
    "render_model_capability_required_term_pair_seed_config_replay_markdown",
    "render_model_capability_required_term_pair_seed_config_replay_text",
    "write_model_capability_required_term_pair_seed_config_replay_outputs",
]
