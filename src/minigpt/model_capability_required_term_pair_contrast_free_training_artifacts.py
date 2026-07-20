from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_contrast_free_training import (
    REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_contrast_free_training_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("contrast_free_training_decision", summary.get("contrast_free_training_decision")),
        ("source_prompt_separation_audit_decision", summary.get("source_prompt_separation_audit_decision")),
        ("selected_pair_count", summary.get("selected_pair_count")),
        ("variant_count", summary.get("variant_count")),
        ("training_run_count", summary.get("training_run_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("probe_count", summary.get("probe_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("variant_pair_full_hit_count", summary.get("variant_pair_full_hit_count")),
        ("variant_pair_partial_hit_count", summary.get("variant_pair_partial_hit_count")),
        ("contrast_free_full_hit_observed", summary.get("contrast_free_full_hit_observed")),
        ("best_variant_id", summary.get("best_variant_id")),
        ("best_variant_hit_count", summary.get("best_variant_hit_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_contrast_free_training_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "contrast_free_run_id",
        "pair_id",
        "variant_id",
        "variant_label",
        "term",
        "generation_seed",
        "training_status",
        "checkpoint_exists",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
        "checkpoint_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_contrast_free_training_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    variant_table = [
        "| Pair | Variant | Hits | Missed | Hit rate | Full hit |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("variant_summaries")):
        variant_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("pair_id")),
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(", ".join(str(term) for term in row.get("hit_terms") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("missed_terms") or [])),
                    markdown_cell(row.get("hit_rate")),
                    markdown_cell(row.get("pair_full_hit")),
                ]
            )
            + " |"
        )
    pair_table = [
        "| Pair | Full-hit variants | Partial variants | Best variant | Best hit count |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("pair_summaries")):
        pair_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("pair_id")),
                    markdown_cell(", ".join(str(item) for item in row.get("full_hit_variants") or [])),
                    markdown_cell(", ".join(str(item) for item in row.get("partial_hit_variants") or [])),
                    markdown_cell(row.get("best_variant_id")),
                    markdown_cell(row.get("best_variant_hit_count")),
                ]
            )
            + " |"
        )
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Contrast-Free Training",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Training decision: `{summary.get('contrast_free_training_decision')}`",
            f"- Source audit: `{summary.get('source_prompt_separation_audit_decision')}`",
            f"- Selected pairs: `{summary.get('selected_pair_count')}`",
            f"- Variants: `{summary.get('variant_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Full-hit variants: `{summary.get('variant_pair_full_hit_count')}`",
            f"- Contrast-free full hit observed: `{summary.get('contrast_free_full_hit_observed')}`",
            "",
            "## Variant Results",
            "",
            *variant_table,
            "",
            "## Pair Summary",
            "",
            *pair_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_contrast_free_training_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("contrast_free_training_decision")),
        ("Variants", summary.get("variant_count")),
        ("Runs", summary.get("training_run_count")),
        ("Probe hits", summary.get("probe_hit_count")),
        ("Full variants", summary.get("variant_pair_full_hit_count")),
        ("Recovered", summary.get("contrast_free_full_hit_observed")),
        ("Best variant", summary.get("best_variant_id")),
    ]
    variant_rows = "\n".join(_variant_row_html(row) for row in list_of_dicts(report.get("variant_summaries")))
    train_rows = "\n".join(_training_row_html(row) for row in list_of_dicts(report.get("training_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair contrast-free training</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair contrast-free training</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Variant Results</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Variant</th><th>Hit terms</th><th>Missed terms</th><th>Rate</th><th>Full hit</th></tr></thead>
<tbody>{variant_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Training Runs</h2>
<div class="table-wrap"><table>
<thead><tr><th>Run</th><th>Lines</th><th>Iters</th><th>Repeat</th><th>Checkpoint</th></tr></thead>
<tbody>{train_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_contrast_free_training_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_contrast_free_training.csv",
        "text": root / REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_CONTRAST_FREE_TRAINING_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_contrast_free_training_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_contrast_free_training_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_contrast_free_training_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_contrast_free_training_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _variant_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('pair_id'))}</td>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('missed_terms') or []))}</td>"
        f"<td>{html_escape(row.get('hit_rate'))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        "</tr>"
    )


def _training_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('contrast_free_run_id'))}</td>"
        f"<td>{html_escape(row.get('contrast_free_line_count'))}</td>"
        f"<td>{html_escape(row.get('max_iters'))}</td>"
        f"<td>{html_escape(row.get('repeat'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_exists'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
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
