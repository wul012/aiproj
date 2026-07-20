from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay import (
    PAIR_GENERATION_PROFILE_REPLAY_CSV_FILENAME,
    PAIR_GENERATION_PROFILE_REPLAY_HTML_FILENAME,
    PAIR_GENERATION_PROFILE_REPLAY_JSON_FILENAME,
    PAIR_GENERATION_PROFILE_REPLAY_MARKDOWN_FILENAME,
    PAIR_GENERATION_PROFILE_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_generation_profile_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("variant_count", summary.get("variant_count")),
        ("term_count", summary.get("term_count")),
        ("default_pair_full_variant_count", summary.get("default_pair_full_variant_count")),
        ("suppression_pair_full_variant_count", summary.get("suppression_pair_full_variant_count")),
        ("suppression_hit_delta", summary.get("suppression_hit_delta")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_generation_profile_replay_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "variant_id",
        "profile_id",
        "term",
        "prompt",
        "generation_seed",
        "continuation_hit",
        "newline_cleanup_hit",
        "blocked_token_count",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_rows")):
            writer.writerow({field: csv_cell(_csv_value(row, field)) for field in fieldnames})


def _csv_value(row: dict[str, Any], field: str) -> Any:
    value = row.get(field)
    if field == "continuation_preview":
        return str(value or "").rstrip()
    return value


def render_model_capability_required_term_pair_generation_profile_replay_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    profile_table = [
        "| Profile | Hits | Pair-full variants | Blocked tokens |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in list_of_dicts(report.get("profile_rows")):
        profile_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(f"{row.get('continuation_hit_count')}/{row.get('case_count')}"),
                    markdown_cell(f"{row.get('pair_full_variant_count')}/{row.get('variant_count')}"),
                    markdown_cell(row.get("blocked_token_count_total")),
                ]
            )
            + " |"
        )
    variant_table = [
        "| Variant | Profile | Hit terms | Missed terms | Pair full |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("variant_rows")):
        variant_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("pair_full_hit")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Generation Profile Replay",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Failed count: `{report.get('failed_count')}`",
            f"- Suppression hit delta: `{summary.get('suppression_hit_delta')}`",
            f"- Suppression pair-full delta: `{summary.get('suppression_pair_full_delta')}`",
            "",
            "## Profiles",
            "",
            *profile_table,
            "",
            "## Variants",
            "",
            *variant_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_generation_profile_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Variants", summary.get("variant_count")),
        ("Terms", summary.get("term_count")),
        ("Default pair full", summary.get("default_pair_full_variant_count")),
        ("Suppression pair full", summary.get("suppression_pair_full_variant_count")),
        ("Suppression hit delta", summary.get("suppression_hit_delta")),
    ]
    profile_rows = "\n".join(_profile_html(row) for row in list_of_dicts(report.get("profile_rows")))
    variant_rows = "\n".join(_variant_html(row) for row in list_of_dicts(report.get("variant_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair generation profile replay</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair generation profile replay</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Profiles</h2>
<div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Hits</th><th>Pair-full variants</th><th>Blocked tokens</th></tr></thead>
<tbody>{profile_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Variants</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Profile</th><th>Hit terms</th><th>Missed terms</th><th>Pair full</th></tr></thead>
<tbody>{variant_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_generation_profile_replay_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_GENERATION_PROFILE_REPLAY_JSON_FILENAME,
        "csv": root / PAIR_GENERATION_PROFILE_REPLAY_CSV_FILENAME,
        "text": root / PAIR_GENERATION_PROFILE_REPLAY_TEXT_FILENAME,
        "markdown": root / PAIR_GENERATION_PROFILE_REPLAY_MARKDOWN_FILENAME,
        "html": root / PAIR_GENERATION_PROFILE_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_generation_profile_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_generation_profile_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_generation_profile_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_generation_profile_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _profile_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}/{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('pair_full_variant_count'))}/{html_escape(row.get('variant_count'))}</td>"
        f"<td>{html_escape(row.get('blocked_token_count_total'))}</td>"
        "</tr>"
    )


def _variant_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
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


__all__ = [
    "render_model_capability_required_term_pair_generation_profile_replay_html",
    "render_model_capability_required_term_pair_generation_profile_replay_markdown",
    "render_model_capability_required_term_pair_generation_profile_replay_text",
    "write_model_capability_required_term_pair_generation_profile_replay_outputs",
]
