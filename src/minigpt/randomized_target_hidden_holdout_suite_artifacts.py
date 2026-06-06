from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.randomized_target_hidden_holdout_suite import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_CSV_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_HTML_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_MARKDOWN_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_target_hidden_holdout_suite_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_target_hidden_holdout_suite_ready", summary.get("randomized_target_hidden_holdout_suite_ready")),
        ("source_case_count", summary.get("source_case_count")),
        ("candidate_case_count", summary.get("candidate_case_count")),
        ("random_seed", summary.get("random_seed")),
        ("randomized_case_factor", summary.get("randomized_case_factor")),
        ("tokenizer_covered_case_count", summary.get("tokenizer_covered_case_count")),
        ("target_hidden_case_count", summary.get("target_hidden_case_count")),
        ("task_hint_case_count", summary.get("task_hint_case_count")),
        ("unique_prompt_count", summary.get("unique_prompt_count")),
        ("new_vs_source_prompt_count", summary.get("new_vs_source_prompt_count")),
        ("candidate_prompt_unknown_token_count", summary.get("candidate_prompt_unknown_token_count")),
        ("source_prompt_mutation_clean_case_count", summary.get("source_prompt_mutation_clean_case_count")),
        ("source_pass_rate", summary.get("source_pass_rate")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_randomized_target_hidden_holdout_suite_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "source_case_id", "draw", "covered", "target_hidden", "hint", "unique", "unknown", "prompt"]
    cases_by_id = _cases_by_id(report)
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("coverage_rows")):
            prompt = as_dict(as_dict(cases_by_id.get(str(row.get("case_id")))).get("prompt_case")).get("prompt")
            writer.writerow(
                {
                    "case_id": csv_cell(row.get("case_id")),
                    "source_case_id": csv_cell(row.get("source_case_id")),
                    "draw": csv_cell(row.get("random_draw_index")),
                    "covered": csv_cell(row.get("tokenizer_covered")),
                    "target_hidden": csv_cell(row.get("target_hidden")),
                    "hint": csv_cell(row.get("task_hint")),
                    "unique": csv_cell(row.get("unique_prompt")),
                    "unknown": csv_cell(row.get("prompt_unknown_count")),
                    "prompt": csv_cell(prompt),
                }
            )


def render_randomized_target_hidden_holdout_suite_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized target-hidden holdout suite'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Candidate cases: `{summary.get('candidate_case_count')}`",
        f"- Random seed: `{summary.get('random_seed')}`",
        f"- Randomized factor: `{summary.get('randomized_case_factor')}`",
        f"- Tokenizer-covered cases: `{summary.get('tokenizer_covered_case_count')}`",
        f"- Target-hidden cases: `{summary.get('target_hidden_case_count')}`",
        f"- Task-hint cases: `{summary.get('task_hint_case_count')}`",
        f"- Unique prompts: `{summary.get('unique_prompt_count')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Coverage Rows",
        "",
        "| Case | Source | Draw | Covered | Target Hidden | Hint | Unique | Unknown | Prompt |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("coverage_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("source_case_id")),
                    markdown_cell(row.get("random_draw_index")),
                    markdown_cell(row.get("tokenizer_covered")),
                    markdown_cell(row.get("target_hidden")),
                    markdown_cell(row.get("task_hint")),
                    markdown_cell(row.get("unique_prompt")),
                    markdown_cell(row.get("prompt_unknown_count")),
                    markdown_cell(_prompt_for_case(report, row.get("case_id"))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_target_hidden_holdout_suite_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Candidates", summary.get("candidate_case_count")),
        ("Seed", summary.get("random_seed")),
        ("Covered", summary.get("tokenizer_covered_case_count")),
        ("Target-hidden", summary.get("target_hidden_case_count")),
        ("Hints", summary.get("task_hint_case_count")),
        ("Unique", summary.get("unique_prompt_count")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_coverage_row(item, report) for item in list_of_dicts(report.get("coverage_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized target-hidden holdout suite'))}</title>{_style()}</head>
<body><main><header><h1>{html_escape(report.get('title', 'MiniGPT randomized target-hidden holdout suite'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Coverage Rows</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Source</th><th>Draw</th><th>Covered</th><th>Target Hidden</th><th>Hint</th><th>Unique</th><th>Unknown</th><th>Prompt</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table><thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead><tbody>{checks}</tbody></table></div></section>
</main></body></html>
"""


def write_randomized_target_hidden_holdout_suite_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_JSON_FILENAME,
        "csv": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_CSV_FILENAME,
        "text": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_SUITE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_randomized_target_hidden_holdout_suite_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_target_hidden_holdout_suite_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_target_hidden_holdout_suite_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_target_hidden_holdout_suite_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _coverage_row(row: dict[str, Any], report: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('source_case_id'))}</td>"
        f"<td>{html_escape(row.get('random_draw_index'))}</td>"
        f"<td>{html_escape(row.get('tokenizer_covered'))}</td>"
        f"<td>{html_escape(row.get('target_hidden'))}</td>"
        f"<td>{html_escape(row.get('task_hint'))}</td>"
        f"<td>{html_escape(row.get('unique_prompt'))}</td>"
        f"<td>{html_escape(row.get('prompt_unknown_count'))}</td>"
        f"<td>{html_escape(_prompt_for_case(report, row.get('case_id')))}</td>"
        "</tr>"
    )


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _prompt_for_case(report: dict[str, Any], case_id: Any) -> Any:
    return as_dict(as_dict(_cases_by_id(report).get(str(case_id))).get("prompt_case")).get("prompt")


def _cases_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    suite = as_dict(report.get("benchmark_suite"))
    return {str(item.get("case_id")): item for item in list_of_dicts(suite.get("cases"))}


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere;white-space:pre-wrap}
</style>"""


__all__ = [
    "render_randomized_target_hidden_holdout_suite_html",
    "render_randomized_target_hidden_holdout_suite_markdown",
    "render_randomized_target_hidden_holdout_suite_text",
    "write_randomized_target_hidden_holdout_suite_outputs",
]
