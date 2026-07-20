from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_gap import (
    REQUIRED_TERM_PAIR_GENERATION_GAP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_GENERATION_GAP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_GENERATION_GAP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_GENERATION_GAP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_generation_gap_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("generation_gap_decision", summary.get("generation_gap_decision")),
        ("source_forced_choice_decision", summary.get("source_forced_choice_decision")),
        ("source_branch_retention_sweep_decision", summary.get("source_branch_retention_sweep_decision")),
        ("prompt_count", summary.get("prompt_count")),
        ("variant_count", summary.get("variant_count")),
        ("forced_choice_full_match_variant_count", summary.get("forced_choice_full_match_variant_count")),
        ("generation_full_match_variant_count", summary.get("generation_full_match_variant_count")),
        ("forced_generation_gap_variant_count", summary.get("forced_generation_gap_variant_count")),
        ("aligned_hit_prompt_count", summary.get("aligned_hit_prompt_count")),
        ("internal_only_prompt_count", summary.get("internal_only_prompt_count")),
        ("generation_only_prompt_count", summary.get("generation_only_prompt_count")),
        ("aligned_miss_prompt_count", summary.get("aligned_miss_prompt_count")),
        ("best_gap_variant_id", summary.get("best_gap_variant_id")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_generation_gap_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "variant_id",
        "run_id",
        "prompt_term",
        "expected_term",
        "forced_best_candidate_term",
        "forced_expected_is_best",
        "generation_continuation_hit",
        "gap_class",
        "generation_continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("gap_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_generation_gap_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    gap_table = [
        "| Variant | Prompt | Forced best | Generation hit | Gap class | Continuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("gap_rows")):
        gap_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("prompt_term")),
                    markdown_cell(row.get("forced_best_candidate_term")),
                    markdown_cell(row.get("generation_continuation_hit")),
                    markdown_cell(row.get("gap_class")),
                    markdown_cell(row.get("generation_continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Generation Gap",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Gap decision: `{summary.get('generation_gap_decision')}`",
            f"- Internal-only prompts: `{summary.get('internal_only_prompt_count')}`",
            f"- Forced-generation gap variants: `{summary.get('forced_generation_gap_variant_count')}`",
            f"- Best gap variant: `{summary.get('best_gap_variant_id')}`",
            "",
            "## Gap Rows",
            "",
            *gap_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_generation_gap_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("generation_gap_decision")),
        ("Prompts", summary.get("prompt_count")),
        ("Internal only", summary.get("internal_only_prompt_count")),
        ("Aligned hits", summary.get("aligned_hit_prompt_count")),
        ("Gap variants", summary.get("forced_generation_gap_variant_count")),
        ("Best gap", summary.get("best_gap_variant_id")),
    ]
    gap_rows = "\n".join(_gap_row_html(row) for row in list_of_dicts(report.get("gap_rows")))
    variant_rows = "\n".join(_variant_row_html(row) for row in list_of_dicts(report.get("variant_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair generation gap</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair generation gap</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Gap Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Prompt</th><th>Forced best</th><th>Generation hit</th><th>Gap class</th><th>Continuation</th></tr></thead>
<tbody>{gap_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Variant Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Forced full</th><th>Generation full</th><th>Gap</th><th>Counts</th></tr></thead>
<tbody>{variant_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_generation_gap_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_GENERATION_GAP_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_generation_gap.csv",
        "text": root / REQUIRED_TERM_PAIR_GENERATION_GAP_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_GENERATION_GAP_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_GENERATION_GAP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_generation_gap_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_generation_gap_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_generation_gap_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_generation_gap_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _gap_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('prompt_term'))}</td>"
        f"<td>{html_escape(row.get('forced_best_candidate_term'))}</td>"
        f"<td>{html_escape(row.get('generation_continuation_hit'))}</td>"
        f"<td>{html_escape(row.get('gap_class'))}</td>"
        f"<td>{html_escape(row.get('generation_continuation_preview'))}</td>"
        "</tr>"
    )


def _variant_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('forced_choice_full_match'))}</td>"
        f"<td>{html_escape(row.get('generation_pair_full_hit'))}</td>"
        f"<td>{html_escape(row.get('forced_generation_gap'))}</td>"
        f"<td>{html_escape(row.get('gap_counts'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#7c3aed}
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
