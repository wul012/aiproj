from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_scaffold_probe import (
    REQUIRED_TERM_SCAFFOLD_PROBE_HTML_FILENAME,
    REQUIRED_TERM_SCAFFOLD_PROBE_JSON_FILENAME,
    REQUIRED_TERM_SCAFFOLD_PROBE_MARKDOWN_FILENAME,
    REQUIRED_TERM_SCAFFOLD_PROBE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_scaffold_probe_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("probe_decision", summary.get("probe_decision")),
        ("case_group_count", summary.get("case_group_count")),
        ("probe_count", summary.get("probe_count")),
        ("required_term_count", summary.get("required_term_count")),
        ("baseline_continuation_hit_count", summary.get("baseline_continuation_hit_count")),
        ("scaffold_continuation_hit_count", summary.get("scaffold_continuation_hit_count")),
        ("scaffold_generated_hit_count", summary.get("scaffold_generated_hit_count")),
        ("case_with_scaffold_hit_count", summary.get("case_with_scaffold_hit_count")),
        ("prompt_truncated_count", summary.get("prompt_truncated_count")),
        ("prompt_over_block_count", summary.get("prompt_over_block_count")),
        ("source_ready_count", summary.get("source_ready_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_scaffold_probe_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "seed",
        "token_cap",
        "case",
        "task_type",
        "max_iters",
        "terms",
        "term_count",
        "generation_seed",
        "baseline_continuation_hit_count",
        "scaffold_prompt_hit_count",
        "scaffold_generated_hit_count",
        "scaffold_continuation_hit_count",
        "prompt_truncated",
        "prompt_over_block",
        "checkpoint_block_size",
        "scaffold_prompt_char_count",
        "baseline_continuation_preview",
        "scaffold_continuation_preview",
        "checkpoint_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_scaffold_probe_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Seed | Case | Terms | Baseline hits | Scaffold hits | Block | Prompt chars | Preview |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("probe_rows"))[:30]:
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("seed")),
                    markdown_cell(row.get("case")),
                    markdown_cell(", ".join(str(term) for term in row.get("terms") or [])),
                    markdown_cell(row.get("baseline_continuation_hit_count")),
                    markdown_cell(row.get("scaffold_continuation_hit_count")),
                    markdown_cell(row.get("checkpoint_block_size")),
                    markdown_cell(row.get("scaffold_prompt_char_count")),
                    markdown_cell(row.get("scaffold_continuation_preview")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Scaffold Probe",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Probe decision: `{summary.get('probe_decision')}`",
            f"- Probe count: `{summary.get('probe_count')}`",
            f"- Required terms: `{summary.get('required_term_count')}`",
            f"- Baseline continuation hits: `{summary.get('baseline_continuation_hit_count')}`",
            f"- Scaffold continuation hits: `{summary.get('scaffold_continuation_hit_count')}`",
            f"- Prompt truncated: `{summary.get('prompt_truncated_count')}`",
            f"- Prompt over block: `{summary.get('prompt_over_block_count')}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_scaffold_probe_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Probe decision", summary.get("probe_decision")),
        ("Probes", summary.get("probe_count")),
        ("Terms", summary.get("required_term_count")),
        ("Baseline hits", summary.get("baseline_continuation_hit_count")),
        ("Scaffold hits", summary.get("scaffold_continuation_hit_count")),
        ("Case hits", summary.get("case_with_scaffold_hit_count")),
        ("Prompt truncated", summary.get("prompt_truncated_count")),
        ("Over block", summary.get("prompt_over_block_count")),
    ]
    source_rows = "\n".join(_source_html(row) for row in list_of_dicts(report.get("source_rows")))
    probe_rows = "\n".join(_probe_html(row) for row in list_of_dicts(report.get("probe_rows"))[:30])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT required-term scaffold probe</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term scaffold probe</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Checkpoint Sources</h2>
<div class="table-wrap"><table>
<thead><tr><th>Status</th><th>Eval suite</th><th>Checkpoint</th><th>Tokenizer</th></tr></thead>
<tbody>{source_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Scaffold Probe Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Seed</th><th>Case</th><th>Terms</th><th>Baseline</th><th>Scaffold</th><th>Block</th><th>Prompt chars</th><th>Continuation preview</th></tr></thead>
<tbody>{probe_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_scaffold_probe_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_SCAFFOLD_PROBE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_scaffold_probe.csv",
        "text": root / REQUIRED_TERM_SCAFFOLD_PROBE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_SCAFFOLD_PROBE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_SCAFFOLD_PROBE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_scaffold_probe_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_scaffold_probe_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_scaffold_probe_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_scaffold_probe_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _source_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('eval_suite_path'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_path'))}</td>"
        f"<td>{html_escape(row.get('tokenizer_path'))}</td>"
        "</tr>"
    )


def _probe_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('case'))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('terms') or []))}</td>"
        f"<td>{html_escape(row.get('baseline_continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('scaffold_continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_block_size'))}</td>"
        f"<td>{html_escape(row.get('scaffold_prompt_char_count'))}</td>"
        f"<td>{html_escape(row.get('scaffold_continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f6f2; color: #172026; }
body { margin: 0; padding: 28px; }
main { max-width: 1180px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #635f57; line-height: 1.55; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #e2ded6; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #6b655c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 980px; }
th, td { text-align: left; border-bottom: 1px solid #e7e2dc; padding: 10px; vertical-align: top; }
th { color: #4d4942; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
