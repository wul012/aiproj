from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review import (
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME,
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME,
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME,
    TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_target_hidden_tokenizer_covered_holdout_replay_review_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        (
            "target_hidden_tokenizer_covered_holdout_replay_review_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_target_hidden_tokenizer_covered_holdout_replay_review_ready"),
        ),
        ("source_holdout_model_quality_ready", summary.get("source_holdout_model_quality_ready")),
        ("case_count", summary.get("case_count")),
        ("target_leakage_case_count", summary.get("target_leakage_case_count")),
        ("target_hidden_case_count", summary.get("target_hidden_case_count")),
        ("task_hint_case_count", summary.get("task_hint_case_count")),
        ("approved_for_wider_holdout", summary.get("approved_for_wider_holdout")),
        ("approved_for_promotion", summary.get("approved_for_promotion")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_target_hidden_tokenizer_covered_holdout_replay_review_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "source_case_id", "target_leakage", "leaked_terms", "task_hint", "task_hint_terms", "review_status", "detail"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("review_rows")):
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "source_case_id": csv_cell(row.get("source_case_id")),
                    "target_leakage": csv_cell(row.get("target_leakage")),
                    "leaked_terms": csv_cell(_join_terms(row.get("leaked_terms"))),
                    "task_hint": csv_cell(row.get("task_hint")),
                    "task_hint_terms": csv_cell(_join_terms(row.get("task_hint_terms"))),
                    "review_status": csv_cell(row.get("review_status")),
                    "detail": csv_cell(row.get("detail")),
                }
            )


def render_target_hidden_tokenizer_covered_holdout_replay_review_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT target-hidden holdout replay review'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Source model quality ready: `{summary.get('source_holdout_model_quality_ready')}`",
        f"- Target leakage cases: `{summary.get('target_leakage_case_count')}`",
        f"- Task hint cases: `{summary.get('task_hint_case_count')}`",
        f"- Approved for wider holdout: `{summary.get('approved_for_wider_holdout')}`",
        f"- Approved for promotion: `{summary.get('approved_for_promotion')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Review Rows",
        "",
        "| Case | Source | Leakage | Leaked | Hint | Hint terms | Status | Detail |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("review_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("source_case_id")),
                    markdown_cell(row.get("target_leakage")),
                    markdown_cell(_join_terms(row.get("leaked_terms"))),
                    markdown_cell(row.get("task_hint")),
                    markdown_cell(_join_terms(row.get("task_hint_terms"))),
                    markdown_cell(row.get("review_status")),
                    markdown_cell(row.get("detail")),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_target_hidden_tokenizer_covered_holdout_replay_review_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Model ready", summary.get("source_holdout_model_quality_ready")),
        ("Leakage cases", summary.get("target_leakage_case_count")),
        ("Hint cases", summary.get("task_hint_case_count")),
        ("Wider holdout", summary.get("approved_for_wider_holdout")),
        ("Promotion", summary.get("approved_for_promotion")),
        ("Claim", summary.get("model_quality_claim")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("review_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT target-hidden holdout replay review'))}</title>{_style()}</head>
<body><main><header><h1>{html_escape(report.get('title', 'MiniGPT target-hidden holdout replay review'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Review Rows</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Source</th><th>Leakage</th><th>Leaked</th><th>Hint</th><th>Hint terms</th><th>Status</th><th>Detail</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main></body></html>
"""


def write_target_hidden_tokenizer_covered_holdout_replay_review_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_JSON_FILENAME,
        "csv": root / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_CSV_FILENAME,
        "text": root / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_TEXT_FILENAME,
        "markdown": root / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_MARKDOWN_FILENAME,
        "html": root / TARGET_ONLY_MEMORY_TARGET_HIDDEN_TOKENIZER_COVERED_HOLDOUT_REPLAY_REVIEW_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_target_hidden_tokenizer_covered_holdout_replay_review_csv(report, paths["csv"])
    paths["text"].write_text(render_target_hidden_tokenizer_covered_holdout_replay_review_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_target_hidden_tokenizer_covered_holdout_replay_review_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_target_hidden_tokenizer_covered_holdout_replay_review_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(
        f"<td>{html_escape(value)}</td>"
        for value in [
            row.get("case_id"),
            row.get("source_case_id"),
            row.get("target_leakage"),
            _join_terms(row.get("leaked_terms")),
            row.get("task_hint"),
            _join_terms(row.get("task_hint_terms")),
            row.get("review_status"),
            row.get("detail"),
        ]
    ) + "</tr>"


def _join_terms(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ",".join(str(item) for item in value)


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#b45309}
*{box-sizing:border-box}body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_target_hidden_tokenizer_covered_holdout_replay_review_html",
    "render_target_hidden_tokenizer_covered_holdout_replay_review_markdown",
    "render_target_hidden_tokenizer_covered_holdout_replay_review_text",
    "write_target_hidden_tokenizer_covered_holdout_replay_review_outputs",
]
