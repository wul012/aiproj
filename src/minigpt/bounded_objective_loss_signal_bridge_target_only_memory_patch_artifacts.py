from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_patch import (
    TARGET_ONLY_MEMORY_PATCH_CORPUS_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_CSV_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_HTML_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_JSONL_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_PATCH_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_target_only_memory_patch_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"target_only_memory_patch_ready={summary.get('bounded_objective_loss_signal_bridge_target_only_memory_patch_ready')}",
            f"patch_example_count={summary.get('patch_example_count')}",
            f"target_only_example_count={summary.get('target_only_example_count')}",
            f"prompt_target_memory_count={summary.get('prompt_target_memory_count')}",
            f"label_target_memory_count={summary.get('label_target_memory_count')}",
            f"decoder_anchor_example_count={summary.get('decoder_anchor_example_count')}",
            f"model_quality_claim={summary.get('model_quality_claim')}",
            f"next_step={summary.get('next_step')}",
            "",
        ]
    )


def render_target_only_memory_patch_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory patch'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Patch examples: `{summary.get('patch_example_count')}`",
        f"- Target-only examples: `{summary.get('target_only_example_count')}`",
        f"- Prompt-target memory: `{summary.get('prompt_target_memory_count')}`",
        f"- Label-target memory: `{summary.get('label_target_memory_count')}`",
        f"- Claim: `{summary.get('model_quality_claim')}`",
        "",
        "## Patch Examples",
        "",
        "| Example | Kind | Text | Source | Class |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("patch_examples")):
        lines.append("| " + " | ".join([
            markdown_cell(row.get("example_id")),
            markdown_cell(row.get("kind")),
            markdown_cell(row.get("text")),
            markdown_cell(row.get("source_case_id")),
            markdown_cell(row.get("source_continuation_class")),
        ]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_target_only_memory_patch_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Examples", summary.get("patch_example_count")),
        ("Target only", summary.get("target_only_example_count")),
        ("Prompt target", summary.get("prompt_target_memory_count")),
        ("Label target", summary.get("label_target_memory_count")),
        ("Anchors", summary.get("decoder_anchor_example_count")),
        ("Claim", summary.get("model_quality_claim")),
    ]
    rows = "".join(_row(row) for row in list_of_dicts(report.get("patch_examples")))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory patch'))}</title>{_style()}</head>
<body><main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective loss signal bridge target-only memory patch'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Patch Examples</h2><div class="table-wrap"><table><thead><tr><th>Example</th><th>Kind</th><th>Text</th><th>Source</th><th>Class</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main></body></html>"""


def write_target_only_memory_patch_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_PATCH_CSV_FILENAME,
        "jsonl": root / TARGET_ONLY_MEMORY_PATCH_JSONL_FILENAME,
        "corpus": root / TARGET_ONLY_MEMORY_PATCH_CORPUS_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_PATCH_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_PATCH_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_PATCH_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    _write_jsonl(report, paths["jsonl"])
    paths["corpus"].write_text(str(report.get("patched_corpus_text") or ""), encoding="utf-8")
    paths["text"].write_text(render_target_only_memory_patch_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_target_only_memory_patch_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_target_only_memory_patch_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["example_id", "kind", "text", "source_case_id", "source_continuation_class", "decoder_anchor"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("patch_examples")):
            writer.writerow({field: row.get(field) for field in fieldnames})


def _write_jsonl(report: dict[str, Any], path: Path) -> None:
    rows = [json.dumps(row, ensure_ascii=False) for row in list_of_dicts(report.get("patch_examples"))]
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('example_id'))}</td>"
        f"<td>{html_escape(row.get('kind'))}</td>"
        f"<td>{html_escape(row.get('text'))}</td>"
        f"<td>{html_escape(row.get('source_case_id'))}</td>"
        f"<td>{html_escape(row.get('source_continuation_class'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#166534}
*{box-sizing:border-box}body{margin:0;background:#f4f7f4;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_target_only_memory_patch_html",
    "render_target_only_memory_patch_markdown",
    "render_target_only_memory_patch_text",
    "write_target_only_memory_patch_outputs",
]
