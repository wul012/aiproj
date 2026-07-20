from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CORPUS_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSONL_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("prompt_aligned_seed_ready", summary.get("prompt_aligned_seed_revision_ready")),
        ("original_example_count", summary.get("original_example_count")),
        ("added_example_count", summary.get("added_example_count")),
        ("example_count", summary.get("example_count")),
        ("exact_prompt_answer_count", summary.get("exact_prompt_answer_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["example_id", "case_id", "revision_type", "completion", "guardrail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_examples")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_jsonl(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in list_of_dicts(report.get("seed_examples"))]
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_corpus(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    texts = [str(row.get("text") or "") for row in list_of_dicts(report.get("seed_examples")) if row.get("text")]
    out_path.write_text("\n\n".join(texts) + ("\n" if texts else ""), encoding="utf-8")


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned seed revision'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('prompt_aligned_seed_revision_ready')}`",
        f"- Total examples: `{summary.get('example_count')}`",
        f"- Exact prompt answers: `{summary.get('exact_prompt_answer_count')}`",
        "",
        "## Seed Examples",
        "",
        "| Example | Case | Type | Completion | Guardrail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("seed_examples")):
        lines.append("| " + " | ".join([markdown_cell(row.get("example_id")), markdown_cell(row.get("case_id")), markdown_cell(row.get("revision_type")), markdown_cell(row.get("completion")), markdown_cell(row.get("guardrail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("prompt_aligned_seed_revision_ready")),
        ("Added", summary.get("added_example_count")),
        ("Total", summary.get("example_count")),
        ("Exact prompts", summary.get("exact_prompt_answer_count")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("seed_examples")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned seed revision'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay prompt-aligned seed revision'))}</h1><p>Adds exact benchmark prompt completions to close the prompt/corpus gap found by the failure alignment diagnostic.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Seed Examples</h2><div class="table-wrap"><table>
<thead><tr><th>Example</th><th>Case</th><th>Type</th><th>Completion</th><th>Guardrail</th><th>Prompt</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CSV_FILENAME,
        "jsonl": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSONL_FILENAME,
        "corpus": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CORPUS_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_csv(report, paths["csv"])
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_jsonl(report, paths["jsonl"])
    write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_corpus(report, paths["corpus"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('example_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('revision_type'))}</td>"
        f"<td>{html_escape(row.get('completion'))}</td>"
        f"<td>{html_escape(row.get('guardrail'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#16212a;--muted:#667381;--line:#d8dee4;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#edf3f4;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_html",
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_text",
    "write_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_outputs",
]
