from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_decoding_gap_probe import (
    REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_decoding_gap_probe_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("decoding_gap_probe_decision", summary.get("decoding_gap_probe_decision")),
        ("target_count", summary.get("target_count")),
        ("profile_count", summary.get("profile_count")),
        ("probe_count", summary.get("probe_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("profile_full_hit_count", summary.get("profile_full_hit_count")),
        ("best_variant_id", summary.get("best_variant_id")),
        ("best_profile_id", summary.get("best_profile_id")),
        ("best_profile_hit_count", summary.get("best_profile_hit_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_decoding_gap_probe_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "variant_id",
        "profile_id",
        "prompt_term",
        "expected_term",
        "continuation_hit",
        "generated_hit",
        "continuation_preview",
        "max_new_tokens",
        "temperature",
        "top_k",
        "seed",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_decoding_gap_probe_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    probe_table = [
        "| Variant | Profile | Prompt | Hit | Continuation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("probe_rows")):
        probe_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("prompt_term")),
                    markdown_cell(row.get("continuation_hit")),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Decoding Gap Probe",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Probe decision: `{summary.get('decoding_gap_probe_decision')}`",
            f"- Continuation hits: `{summary.get('continuation_hit_count')}`",
            f"- Full-hit profiles: `{summary.get('profile_full_hit_count')}`",
            f"- Best profile: `{summary.get('best_profile_id')}`",
            "",
            "## Probe Rows",
            "",
            *probe_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_decoding_gap_probe_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("decoding_gap_probe_decision")),
        ("Targets", summary.get("target_count")),
        ("Profiles", summary.get("profile_count")),
        ("Hits", summary.get("continuation_hit_count")),
        ("Full profiles", summary.get("profile_full_hit_count")),
        ("Best profile", summary.get("best_profile_id")),
    ]
    probe_rows = "\n".join(_probe_row_html(row) for row in list_of_dicts(report.get("probe_rows")))
    profile_rows = "\n".join(_profile_row_html(row) for row in list_of_dicts(report.get("profile_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair decoding gap probe</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair decoding gap probe</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Probe Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Profile</th><th>Prompt</th><th>Hit</th><th>Continuation</th></tr></thead>
<tbody>{probe_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Profile Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Profile</th><th>Hits</th><th>Prompts</th><th>Full hit</th><th>Missed</th></tr></thead>
<tbody>{profile_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_decoding_gap_probe_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_decoding_gap_probe.csv",
        "text": root / REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_decoding_gap_probe_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_decoding_gap_probe_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_decoding_gap_probe_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_decoding_gap_probe_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _probe_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('prompt_term'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _profile_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('prompt_count'))}</td>"
        f"<td>{html_escape(row.get('profile_full_hit'))}</td>"
        f"<td>{html_escape(row.get('missed_terms'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#b45309}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
p{color:var(--muted);line-height:1.55}
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


def _csv_clean(value: Any) -> Any:
    cell = csv_cell(value)
    return cell.rstrip() if isinstance(cell, str) else cell
