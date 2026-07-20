from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CORPUS_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSONL_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("seed_ready", summary.get("decoder_anchor_seed_revision_ready")),
        ("example_count", summary.get("example_count")),
        ("added_example_count", summary.get("added_example_count")),
        ("bridge_example_count", summary.get("bridge_example_count")),
        ("unanchored_direct_example_count", summary.get("unanchored_direct_example_count")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["example_id", "case_id", "revision_type", "prompt", "completion", "guardrail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_examples")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_jsonl(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in list_of_dicts(report.get("seed_examples")):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus(report: dict[str, Any], path: str | Path) -> None:
    text = "\n\n".join(str(row.get("text") or "") for row in list_of_dicts(report.get("seed_examples")) if str(row.get("text") or "").strip())
    Path(path).write_text(text.rstrip() + "\n", encoding="utf-8")


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor seed revision'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('decoder_anchor_seed_revision_ready')}`",
        f"- Examples: `{summary.get('example_count')}`",
        f"- Added examples: `{summary.get('added_example_count')}`",
        f"- Bridge examples: `{summary.get('bridge_example_count')}`",
        f"- Direct examples: `{summary.get('unanchored_direct_example_count')}`",
        "",
        "## Seed Examples",
        "",
        "| ID | Case | Type | Completion | Guardrail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("seed_examples")):
        lines.append("| " + " | ".join([markdown_cell(row.get("example_id")), markdown_cell(row.get("case_id")), markdown_cell(row.get("revision_type")), markdown_cell(row.get("completion")), markdown_cell(row.get("guardrail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Examples", summary.get("example_count")),
        ("Added", summary.get("added_example_count")),
        ("Bridge", summary.get("bridge_example_count")),
        ("Direct", summary.get("unanchored_direct_example_count")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("seed_examples")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor seed revision'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT model capability route promotion bounded real replay decoder anchor seed revision'))}</h1><p>Builds a decoder-anchor-informed corpus with direct answers and bridge completions. This is training data only, not model-quality evidence.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Seed Examples</h2><div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Case</th><th>Type</th><th>Completion</th><th>Guardrail</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CSV_FILENAME,
        "jsonl": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSONL_FILENAME,
        "corpus": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CORPUS_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_csv(report, paths["csv"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_jsonl(report, paths["jsonl"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus(report, paths["corpus"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('example_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('revision_type'))}</td>"
        f"<td>{html_escape(row.get('completion'))}</td>"
        f"<td>{html_escape(row.get('guardrail'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#667381;--line:#d8dee5;--panel:#f7f9fb;--accent:#155e75}
*{box-sizing:border-box}
body{margin:0;background:#f0f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
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
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_html",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_text",
    "write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_outputs",
]
