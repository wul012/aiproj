from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CORPUS_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSONL_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_bounded_objective_unassisted_repair_seed_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_unassisted_repair_seed_ready", summary.get("bounded_objective_unassisted_repair_seed_ready")),
        ("example_count", summary.get("example_count")),
        ("neutral_prompt_example_count", summary.get("neutral_prompt_example_count")),
        ("decoder_anchor_example_count", summary.get("decoder_anchor_example_count")),
        ("corpus_char_count", summary.get("corpus_char_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_unassisted_repair_seed_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["example_id", "case_id", "example_mode", "completion", "prompt_contains_target_terms", "decoder_anchor_used", "guardrail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_examples")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_bounded_objective_unassisted_repair_seed_jsonl(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in list_of_dicts(report.get("seed_examples"))]
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_bounded_objective_unassisted_repair_seed_corpus(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(str(report.get("corpus_text") or ""), encoding="utf-8")


def render_bounded_objective_unassisted_repair_seed_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective unassisted repair seed'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('bounded_objective_unassisted_repair_seed_ready')}`",
        f"- Examples: `{summary.get('example_count')}`",
        f"- Neutral prompt examples: `{summary.get('neutral_prompt_example_count')}`",
        f"- Decoder anchor examples: `{summary.get('decoder_anchor_example_count')}`",
        "",
        "## Seed Examples",
        "",
        "| Example | Case | Mode | Prompt Has Terms | Completion | Guardrail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("seed_examples")):
        lines.append("| " + " | ".join([markdown_cell(row.get("example_id")), markdown_cell(row.get("case_id")), markdown_cell(row.get("example_mode")), markdown_cell(row.get("prompt_contains_target_terms")), markdown_cell(row.get("completion")), markdown_cell(row.get("guardrail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_unassisted_repair_seed_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Ready", summary.get("bounded_objective_unassisted_repair_seed_ready")),
        ("Examples", summary.get("example_count")),
        ("Neutral", summary.get("neutral_prompt_example_count")),
        ("Anchors", summary.get("decoder_anchor_example_count")),
        ("Corpus chars", summary.get("corpus_char_count")),
        ("Claim", interpretation.get("model_quality_claim")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("seed_examples")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective unassisted repair seed'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective unassisted repair seed'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Seed Examples</h2><div class="table-wrap"><table>
<thead><tr><th>Example</th><th>Case</th><th>Mode</th><th>Prompt Has Terms</th><th>Completion</th><th>Prompt</th></tr></thead>
<tbody>{rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_unassisted_repair_seed_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CSV_FILENAME,
        "jsonl": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSONL_FILENAME,
        "corpus": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CORPUS_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_unassisted_repair_seed_csv(report, paths["csv"])
    write_bounded_objective_unassisted_repair_seed_jsonl(report, paths["jsonl"])
    write_bounded_objective_unassisted_repair_seed_corpus(report, paths["corpus"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_seed_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_seed_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_seed_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('example_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('example_mode'))}</td>"
        f"<td>{html_escape(row.get('prompt_contains_target_terms'))}</td>"
        f"<td>{html_escape(row.get('completion'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#155e75}
*{box-sizing:border-box}
body{margin:0;background:#eef3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
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
td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_unassisted_repair_seed_html",
    "render_bounded_objective_unassisted_repair_seed_markdown",
    "render_bounded_objective_unassisted_repair_seed_text",
    "write_bounded_objective_unassisted_repair_seed_outputs",
]
