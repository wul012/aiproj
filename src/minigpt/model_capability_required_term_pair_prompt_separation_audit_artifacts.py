from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_prompt_separation_audit import (
    REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_HTML_FILENAME,
    REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_JSON_FILENAME,
    REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_prompt_separation_audit_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("prompt_separation_audit_decision", summary.get("prompt_separation_audit_decision")),
        ("source_pair_decoding_sweep_decision", summary.get("source_pair_decoding_sweep_decision")),
        ("target_count", summary.get("target_count")),
        ("corpus_readable_target_count", summary.get("corpus_readable_target_count")),
        ("term_row_count", summary.get("term_row_count")),
        ("prompt_separation_ready", summary.get("prompt_separation_ready")),
        ("direct_prompt_other_term_leak_count", summary.get("direct_prompt_other_term_leak_count")),
        ("negative_contrast_leak_count", summary.get("negative_contrast_leak_count")),
        ("pair_header_shared_context_count", summary.get("pair_header_shared_context_count")),
        ("corpus_revision_recommended", summary.get("corpus_revision_recommended")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_prompt_separation_audit_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "target_id",
        "pair_id",
        "variant_id",
        "capacity_run_id",
        "case",
        "term",
        "scaffold_prompt",
        "other_terms",
        "prompt_prefix_line_count",
        "exact_target_line_count",
        "spaced_target_line_count",
        "target_after_prompt_line_count",
        "other_after_prompt_line_count",
        "negative_contrast_leak_count",
        "pair_header_shared_context_count",
        "prompt_separation_ready",
        "example_leak_line",
        "example_pair_header_line",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("term_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_prompt_separation_audit_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    target_table = [
        "| Target | Variant | Direct leak | Negative leak | Pair context | Ready |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("target_rows")):
        target_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("target_id")),
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("direct_prompt_other_term_leak_count")),
                    markdown_cell(row.get("negative_contrast_leak_count")),
                    markdown_cell(row.get("pair_header_shared_context_count")),
                    markdown_cell(row.get("prompt_separation_ready")),
                ]
            )
            + " |"
        )
    term_table = [
        "| Target | Term | Prompt | Other-after-prompt | Example leak |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("term_rows"))[:40]:
        term_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("target_id")),
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("scaffold_prompt")),
                    markdown_cell(row.get("other_after_prompt_line_count")),
                    markdown_cell(row.get("example_leak_line")),
                ]
            )
            + " |"
        )
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Prompt Separation Audit",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Audit decision: `{summary.get('prompt_separation_audit_decision')}`",
            f"- Prompt separation ready: `{summary.get('prompt_separation_ready')}`",
            f"- Direct other-term leaks: `{summary.get('direct_prompt_other_term_leak_count')}`",
            f"- Negative contrast leaks: `{summary.get('negative_contrast_leak_count')}`",
            f"- Corpus revision recommended: `{summary.get('corpus_revision_recommended')}`",
            "",
            "## Target Summary",
            "",
            *target_table,
            "",
            "## Term Rows",
            "",
            *term_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_prompt_separation_audit_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("prompt_separation_audit_decision")),
        ("Targets", summary.get("target_count")),
        ("Ready", summary.get("prompt_separation_ready")),
        ("Direct leaks", summary.get("direct_prompt_other_term_leak_count")),
        ("Negative leaks", summary.get("negative_contrast_leak_count")),
        ("Pair contexts", summary.get("pair_header_shared_context_count")),
        ("Revise corpus", summary.get("corpus_revision_recommended")),
    ]
    target_rows = "\n".join(_target_row_html(row) for row in list_of_dicts(report.get("target_rows")))
    term_rows = "\n".join(_term_row_html(row) for row in list_of_dicts(report.get("term_rows"))[:80])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair prompt separation audit</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair prompt separation audit</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Target Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Target</th><th>Variant</th><th>Corpus</th><th>Direct leak</th><th>Negative leak</th><th>Pair context</th><th>Ready</th></tr></thead>
<tbody>{target_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Term Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Target</th><th>Term</th><th>Prompt</th><th>Target rows</th><th>Other leak</th><th>Example</th></tr></thead>
<tbody>{term_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_prompt_separation_audit_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_prompt_separation_audit.csv",
        "text": root / REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_PROMPT_SEPARATION_AUDIT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_prompt_separation_audit_csv(report, paths["csv"])
    paths["text"].write_text(
        render_model_capability_required_term_pair_prompt_separation_audit_text(report),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_prompt_separation_audit_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_model_capability_required_term_pair_prompt_separation_audit_html(report),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _target_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('target_id'))}</td>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('line_count'))}</td>"
        f"<td>{html_escape(row.get('direct_prompt_other_term_leak_count'))}</td>"
        f"<td>{html_escape(row.get('negative_contrast_leak_count'))}</td>"
        f"<td>{html_escape(row.get('pair_header_shared_context_count'))}</td>"
        f"<td>{html_escape(row.get('prompt_separation_ready'))}</td>"
        "</tr>"
    )


def _term_row_html(row: dict[str, Any]) -> str:
    target_rows = int(row.get("target_after_prompt_line_count") or 0)
    leak_rows = int(row.get("other_after_prompt_line_count") or 0)
    return (
        "<tr>"
        f"<td>{html_escape(row.get('target_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td><code>{html_escape(row.get('scaffold_prompt'))}</code></td>"
        f"<td>{html_escape(target_rows)}</td>"
        f"<td>{html_escape(leak_rows)}</td>"
        f"<td><code>{html_escape(row.get('example_leak_line'))}</code></td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e;--warn:#b45309}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
header{margin-bottom:18px}
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
code{white-space:pre-wrap;color:var(--warn)}
</style>"""


def _csv_clean(value: Any) -> Any:
    cell = csv_cell(value)
    return cell.rstrip() if isinstance(cell, str) else cell
