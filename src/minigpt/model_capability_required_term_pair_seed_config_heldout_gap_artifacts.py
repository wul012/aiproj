from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_seed_config_heldout_gap import (
    PAIR_SEED_CONFIG_HELDOUT_GAP_CSV_FILENAME,
    PAIR_SEED_CONFIG_HELDOUT_GAP_HTML_FILENAME,
    PAIR_SEED_CONFIG_HELDOUT_GAP_JSON_FILENAME,
    PAIR_SEED_CONFIG_HELDOUT_GAP_MARKDOWN_FILENAME,
    PAIR_SEED_CONFIG_HELDOUT_GAP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, format_mapping, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_seed_config_heldout_gap_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("row_count", summary.get("row_count")),
        ("gap_count", summary.get("gap_count")),
        ("gap_rate", summary.get("gap_rate")),
        ("gap_class_counts", format_mapping(summary.get("gap_class_counts"))),
        ("spec_gap_counts", format_mapping(summary.get("spec_gap_counts"))),
        ("seed_gap_counts", format_mapping(summary.get("seed_gap_counts"))),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_seed_config_heldout_gap_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "spec_id",
        "seed",
        "selected_config_id",
        "gap_class",
        "missed_terms",
        "best_profile_id",
        "best_profile_hit_count",
        "fixed_prompt",
        "loss_prompt",
        "top_k",
        "temperature",
        "replay_decision",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("gap_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_seed_config_heldout_gap_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        "| Spec | Seed | Config | Gap class | Missed terms | Best profile | Prompts |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("gap_rows")):
        prompts = f"{row.get('fixed_prompt')} / {row.get('loss_prompt')}"
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("spec_id")),
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("selected_config_id")),
                    markdown_cell(row.get("gap_class")),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("best_profile_id")),
                    markdown_cell(prompts),
                ]
            )
            + " |"
        )
    profile_rows = _profile_markdown_rows(report)
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Seed Config Held-Out Gap Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Gap rows: `{summary.get('gap_count')}/{summary.get('row_count')}`",
            f"- Gap classes: `{format_mapping(summary.get('gap_class_counts'))}`",
            "",
            "## Gap Rows",
            "",
            *rows,
            "",
            "## Profile Evidence",
            "",
            *profile_rows,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_seed_config_heldout_gap_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Gaps", f"{summary.get('gap_count')}/{summary.get('row_count')}"),
        ("Gap rate", summary.get("gap_rate")),
        ("Gap classes", format_mapping(summary.get("gap_class_counts"))),
    ]
    rows = "\n".join(_row_html(row) for row in list_of_dicts(report.get("gap_rows")))
    profiles = "\n".join(_profile_html(row, profile) for row in list_of_dicts(report.get("gap_rows")) for profile in list_of_dicts(row.get("profile_details")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT held-out gap diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT held-out gap diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Gap Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Spec</th><th>Seed</th><th>Config</th><th>Class</th><th>Missed</th><th>Prompts</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Profile Evidence</h2>
<div class="table-wrap"><table>
<thead><tr><th>Spec</th><th>Profile</th><th>Hit terms</th><th>Missed terms</th><th>Previews</th></tr></thead>
<tbody>{profiles}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_seed_config_heldout_gap_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_SEED_CONFIG_HELDOUT_GAP_JSON_FILENAME,
        "csv": root / PAIR_SEED_CONFIG_HELDOUT_GAP_CSV_FILENAME,
        "text": root / PAIR_SEED_CONFIG_HELDOUT_GAP_TEXT_FILENAME,
        "markdown": root / PAIR_SEED_CONFIG_HELDOUT_GAP_MARKDOWN_FILENAME,
        "html": root / PAIR_SEED_CONFIG_HELDOUT_GAP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_seed_config_heldout_gap_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_seed_config_heldout_gap_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_seed_config_heldout_gap_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_seed_config_heldout_gap_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _profile_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = [
        "| Spec | Profile | Hit terms | Missed terms | Continuation previews |",
        "| --- | --- | --- | --- | --- |",
    ]
    for gap in list_of_dicts(report.get("gap_rows")):
        for profile in list_of_dicts(gap.get("profile_details")):
            rows.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(gap.get("spec_id")),
                        markdown_cell(profile.get("profile_id")),
                        markdown_cell(",".join(str(item) for item in profile.get("hit_terms", []))),
                        markdown_cell(",".join(str(item) for item in profile.get("missed_terms", []))),
                        markdown_cell(_preview_text(profile)),
                    ]
                )
                + " |"
            )
    return rows


def _row_html(row: dict[str, Any]) -> str:
    prompts = f"{row.get('fixed_prompt')} / {row.get('loss_prompt')}"
    missed = ",".join(str(item) for item in row.get("missed_terms", []))
    return (
        "<tr>"
        f"<td>{html_escape(row.get('spec_id'))}</td>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('selected_config_id'))}</td>"
        f"<td>{html_escape(row.get('gap_class'))}</td>"
        f"<td>{html_escape(missed)}</td>"
        f"<td>{html_escape(prompts)}</td>"
        "</tr>"
    )


def _profile_html(gap: dict[str, Any], profile: dict[str, Any]) -> str:
    hit_terms = ",".join(str(item) for item in profile.get("hit_terms", []))
    missed_terms = ",".join(str(item) for item in profile.get("missed_terms", []))
    return (
        "<tr>"
        f"<td>{html_escape(gap.get('spec_id'))}</td>"
        f"<td>{html_escape(profile.get('profile_id'))}</td>"
        f"<td>{html_escape(hit_terms)}</td>"
        f"<td>{html_escape(missed_terms)}</td>"
        f"<td>{html_escape(_preview_text(profile))}</td>"
        "</tr>"
    )


def _preview_text(profile: dict[str, Any]) -> str:
    pieces = []
    for case in list_of_dicts(profile.get("case_previews")):
        pieces.append(f"{case.get('term')}={case.get('continuation_preview')}")
    return "; ".join(pieces)


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
</style>"""


__all__ = [
    "render_model_capability_required_term_pair_seed_config_heldout_gap_html",
    "render_model_capability_required_term_pair_seed_config_heldout_gap_markdown",
    "render_model_capability_required_term_pair_seed_config_heldout_gap_text",
    "write_model_capability_required_term_pair_seed_config_heldout_gap_outputs",
]
