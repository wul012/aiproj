from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_artifacts import (
    write_model_capability_route_promotion_bounded_real_replay_csv,
)
from minigpt.randomized_target_hidden_holdout_real_replay import (
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_CSV_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_HTML_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_MARKDOWN_FILENAME,
    RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_randomized_target_hidden_holdout_real_replay_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("randomized_target_hidden_holdout_real_replay_ready", summary.get("randomized_target_hidden_holdout_real_replay_ready")),
        ("randomized_holdout_model_quality_ready", summary.get("randomized_holdout_model_quality_ready")),
        ("case_count", summary.get("case_count")),
        ("source_random_seed", summary.get("source_random_seed")),
        ("source_randomized_case_factor", summary.get("source_randomized_case_factor")),
        ("executed_case_count", summary.get("executed_case_count")),
        ("passed_case_count", summary.get("passed_case_count")),
        ("failed_case_count", summary.get("failed_case_count")),
        ("any_hit_case_count", summary.get("any_hit_case_count")),
        ("zero_hit_case_count", summary.get("zero_hit_case_count")),
        ("pass_rate", summary.get("pass_rate")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("model_quality_claim", summary.get("model_quality_claim")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_randomized_target_hidden_holdout_real_replay_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT randomized target-hidden holdout real replay'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Model quality ready: `{summary.get('randomized_holdout_model_quality_ready')}`",
        f"- Passed cases: `{summary.get('passed_case_count')}/{summary.get('case_count')}`",
        f"- Any-hit cases: `{summary.get('any_hit_case_count')}`",
        f"- Zero-hit cases: `{summary.get('zero_hit_case_count')}`",
        f"- Pass rate: `{summary.get('pass_rate')}`",
        f"- Next step: `{summary.get('next_step')}`",
        "",
        "## Replay Rows",
        "",
        "| Case | Draw | Pass | Hit terms | Missed terms | Continuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("replay_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("random_draw_index")),
                    markdown_cell(row.get("case_pass")),
                    markdown_cell(_join_terms(row.get("hit_terms"))),
                    markdown_cell(_join_terms(row.get("missed_terms"))),
                    markdown_cell(row.get("continuation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_randomized_target_hidden_holdout_real_replay_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Quality ready", summary.get("randomized_holdout_model_quality_ready")),
        ("Passed", f"{summary.get('passed_case_count')}/{summary.get('case_count')}"),
        ("Any hits", summary.get("any_hit_case_count")),
        ("Zero hits", summary.get("zero_hit_case_count")),
        ("Pass rate", summary.get("pass_rate")),
        ("Promotion", summary.get("promotion_ready")),
        ("Next", summary.get("next_step")),
    ]
    rows = "".join(_row(item) for item in list_of_dicts(report.get("replay_rows")))
    checks = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT randomized target-hidden holdout real replay'))}</title>{_style()}</head>
<body><main><header><h1>{html_escape(report.get('title', 'MiniGPT randomized target-hidden holdout real replay'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Replay Rows</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Draw</th><th>Pass</th><th>Hit</th><th>Missed</th><th>Continuation</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table><thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead><tbody>{checks}</tbody></table></div></section>
</main></body></html>
"""


def write_randomized_target_hidden_holdout_real_replay_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_JSON_FILENAME,
        "csv": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_CSV_FILENAME,
        "text": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_TEXT_FILENAME,
        "markdown": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_MARKDOWN_FILENAME,
        "html": root / RANDOMIZED_TARGET_HIDDEN_HOLDOUT_REAL_REPLAY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_csv(report, paths["csv"])
    paths["text"].write_text(render_randomized_target_hidden_holdout_real_replay_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_randomized_target_hidden_holdout_real_replay_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_randomized_target_hidden_holdout_real_replay_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('random_draw_index'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(_join_terms(row.get('hit_terms')))}</td>"
        f"<td>{html_escape(_join_terms(row.get('missed_terms')))}</td>"
        f"<td>{html_escape(row.get('continuation'))}</td>"
        "</tr>"
    )


def _check_row(row: dict[str, Any]) -> str:
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"


def _join_terms(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ",".join(str(item) for item in value)


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>:root{color-scheme:light;--ink:#17212b;--muted:#62717d;--line:#d7dee5;--panel:#f8fafc;--accent:#0f766e}*{box-sizing:border-box}body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}main{max-width:1240px;margin:0 auto;padding:28px}h1{font-size:30px;margin:0 0 8px;letter-spacing:0}h2{font-size:18px;margin:0 0 12px;letter-spacing:0}p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}.card{padding:14px}.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}.panel{padding:16px;margin:14px 0}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:var(--panel);color:#334155}td{overflow-wrap:anywhere;white-space:pre-wrap}</style>"""


__all__ = [
    "render_randomized_target_hidden_holdout_real_replay_html",
    "render_randomized_target_hidden_holdout_real_replay_markdown",
    "render_randomized_target_hidden_holdout_real_replay_text",
    "write_randomized_target_hidden_holdout_real_replay_outputs",
]
