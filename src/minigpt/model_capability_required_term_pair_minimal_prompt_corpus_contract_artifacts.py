from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_minimal_prompt_corpus_contract import (
    PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_CSV_FILENAME,
    PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_HTML_FILENAME,
    PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_JSON_FILENAME,
    PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_MARKDOWN_FILENAME,
    PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_minimal_prompt_corpus_contract_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    corpus = as_dict(report.get("corpus"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("contract_ready", summary.get("contract_ready")),
        ("corpus_mode", summary.get("corpus_mode")),
        ("source_prompts", summary.get("source_prompts")),
        ("line_count", summary.get("line_count")),
        ("fixed_direct_count", corpus.get("fixed_direct_count")),
        ("loss_direct_count", corpus.get("loss_direct_count")),
        ("anchor_hit_count", summary.get("anchor_hit_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_minimal_prompt_corpus_contract_markdown(report: dict[str, Any]) -> str:
    corpus = as_dict(report.get("corpus"))
    interpretation = as_dict(report.get("interpretation"))
    checks = ["| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("check_rows")):
        checks.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("id")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("actual")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    sample = "\n".join(f"- `{line}`" for line in report.get("sample_lines", []))
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Minimal Prompt Corpus Contract",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Corpus mode: `{corpus.get('corpus_mode')}`",
            f"- Source prompts: `{corpus.get('source_prompts')}`",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            "",
            "## Checks",
            "",
            *checks,
            "",
            "## Sample Lines",
            "",
            sample,
            "",
            "## Next Action",
            "",
            str(interpretation.get("next_action")),
            "",
        ]
    )


def render_minimal_prompt_corpus_contract_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    corpus = as_dict(report.get("corpus"))
    interpretation = as_dict(report.get("interpretation"))
    check_rows = "".join(_check_html(row) for row in list_of_dicts(report.get("check_rows")))
    sample_rows = "".join(f"<li>{html_escape(line)}</li>" for line in report.get("sample_lines", []))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Contract ready", summary.get("contract_ready")),
        ("Corpus mode", summary.get("corpus_mode")),
        ("Source prompts", summary.get("source_prompts")),
        ("Anchor hits", summary.get("anchor_hit_count")),
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT minimal prompt corpus contract</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT minimal prompt corpus contract</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Corpus Summary</h2><p>Direct rows: fixed={html_escape(corpus.get('fixed_direct_count'))}, loss={html_escape(corpus.get('loss_direct_count'))}. Lines: {html_escape(corpus.get('line_count'))}.</p></section>
<section class="panel">
<h2>Contract Checks</h2>
<div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{check_rows}</tbody>
</table></div>
</section>
<section class="panel"><h2>Sample Lines</h2><ul>{sample_rows}</ul></section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main>
</body>
</html>
"""


def write_minimal_prompt_corpus_contract_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["id", "status", "actual", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("check_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def write_minimal_prompt_corpus_contract_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_JSON_FILENAME,
        "csv": root / PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_CSV_FILENAME,
        "text": root / PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_TEXT_FILENAME,
        "markdown": root / PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_MARKDOWN_FILENAME,
        "html": root / PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_minimal_prompt_corpus_contract_csv(report, paths["csv"])
    paths["text"].write_text(render_minimal_prompt_corpus_contract_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_minimal_prompt_corpus_contract_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_minimal_prompt_corpus_contract_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _check_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('id'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('actual'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p,li{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
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
ul{padding-left:20px}
</style>"""


__all__ = [
    "render_minimal_prompt_corpus_contract_html",
    "render_minimal_prompt_corpus_contract_markdown",
    "render_minimal_prompt_corpus_contract_text",
    "write_minimal_prompt_corpus_contract_outputs",
]
