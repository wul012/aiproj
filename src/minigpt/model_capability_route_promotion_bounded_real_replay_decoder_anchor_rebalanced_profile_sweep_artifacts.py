from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_CSV_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_HTML_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_MARKDOWN_FILENAME,
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card
from minigpt.report_utils import html_check_row as _check_row


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("profile_sweep_ready", summary.get("rebalanced_profile_sweep_ready")),
        ("profile_count", summary.get("profile_count")),
        ("case_count", summary.get("case_count")),
        ("best_profile_id", summary.get("best_profile_id")),
        ("best_passed_case_count", summary.get("best_passed_case_count")),
        ("best_pass_rate", summary.get("best_pass_rate")),
        ("best_any_hit_case_count", summary.get("best_any_hit_case_count")),
        ("any_profile_recovered", summary.get("any_profile_recovered")),
        ("promotion_ready", summary.get("promotion_ready")),
        ("next_step", summary.get("next_step")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "profile_id",
        "case_id",
        "case_pass",
        "zero_hit",
        "fragment_like_generation",
        "hit_terms",
        "missed_terms",
        "max_new_tokens",
        "temperature",
        "top_k",
        "seed",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("case_profile_rows")):
            writer.writerow({field: csv_cell(_csv_value(field, row.get(field))) for field in fieldnames})


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT rebalanced decoder profile sweep'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Ready: `{summary.get('rebalanced_profile_sweep_ready')}`",
        f"- Best profile: `{summary.get('best_profile_id')}`",
        f"- Best passed cases: `{summary.get('best_passed_case_count')}/{summary.get('case_count')}`",
        f"- Any profile recovered: `{summary.get('any_profile_recovered')}`",
        f"- Promotion ready: `{summary.get('promotion_ready')}`",
        f"- Model-quality claim: `{interpretation.get('model_quality_claim')}`",
        "",
        "## Profiles",
        "",
        "| Profile | Tokens | Temp | Top-k | Passed | Hits | Zero-hit | Fragments | Pass rate |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("profile_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("max_new_tokens")),
                    markdown_cell(row.get("temperature")),
                    markdown_cell(row.get("top_k")),
                    markdown_cell(f"{row.get('passed_case_count')}/{row.get('case_count')}"),
                    markdown_cell(row.get("any_hit_case_count")),
                    markdown_cell(row.get("zero_hit_case_count")),
                    markdown_cell(row.get("fragment_like_case_count")),
                    markdown_cell(row.get("pass_rate")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Case Profile Rows", "", "| Profile | Case | Pass | Hit terms | Missed terms | Continuation |", "| --- | --- | --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("case_profile_rows")):
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(row.get("case_id")),
                    markdown_cell(row.get("case_pass")),
                    markdown_cell(",".join(str(item) for item in row.get("hit_terms", []))),
                    markdown_cell(",".join(str(item) for item in row.get("missed_terms", []))),
                    markdown_cell(row.get("continuation_preview")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Actual | Detail |", "| --- | --- | --- | --- |"])
    for row in list_of_dicts(report.get("check_rows")):
        lines.append("| " + " | ".join([markdown_cell(row.get("id")), markdown_cell(row.get("status")), markdown_cell(row.get("actual")), markdown_cell(row.get("detail"))]) + " |")
    return "\n".join(lines).rstrip() + "\n"


def render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Best profile", summary.get("best_profile_id")),
        ("Best pass", f"{summary.get('best_passed_case_count')}/{summary.get('case_count')}"),
        ("Best hits", summary.get("best_any_hit_case_count")),
        ("Recovered", summary.get("any_profile_recovered")),
        ("Promotion", summary.get("promotion_ready")),
        ("Claim", interpretation.get("model_quality_claim")),
        ("Next", summary.get("next_step")),
    ]
    profile_rows = "".join(_profile_row(item) for item in list_of_dicts(report.get("profile_rows")))
    case_rows = "".join(_case_row(item) for item in list_of_dicts(report.get("case_profile_rows")))
    check_rows = "".join(_check_row(item) for item in list_of_dicts(report.get("check_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT rebalanced decoder profile sweep'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT rebalanced decoder profile sweep'))}</h1><p>Runs the same rebalanced checkpoint through bounded replay with multiple decoding profiles before choosing whether to train again.</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Profiles</h2><div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Tokens</th><th>Temp</th><th>Top-k</th><th>Passed</th><th>Hits</th><th>Zero-hit</th><th>Fragments</th><th>Pass rate</th></tr></thead>
<tbody>{profile_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Case Profile Rows</h2><div class="table-wrap"><table>
<thead><tr><th>Profile</th><th>Case</th><th>Pass</th><th>Hit terms</th><th>Missed terms</th><th>Continuation</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div></section>
<section class="panel"><h2>Checks</h2><div class="table-wrap"><table>
<thead><tr><th>Check</th><th>Status</th><th>Actual</th><th>Detail</th></tr></thead>
<tbody>{check_rows}</tbody>
</table></div></section>
</main>
</body>
</html>
"""


def write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME,
        "csv": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_CSV_FILENAME,
        "text": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_TEXT_FILENAME,
        "markdown": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_MARKDOWN_FILENAME,
        "html": root / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _profile_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('max_new_tokens'))}</td>"
        f"<td>{html_escape(row.get('temperature'))}</td>"
        f"<td>{html_escape(row.get('top_k'))}</td>"
        f"<td>{html_escape(row.get('passed_case_count'))}/{html_escape(row.get('case_count'))}</td>"
        f"<td>{html_escape(row.get('any_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('zero_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('fragment_like_case_count'))}</td>"
        f"<td>{html_escape(row.get('pass_rate'))}</td>"
        "</tr>"
    )


def _csv_value(field: str, value: Any) -> Any:
    if field == "continuation_preview" and isinstance(value, str):
        return value.rstrip()
    return value


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('case_pass'))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('hit_terms', [])))}</td>"
        f"<td>{html_escape(','.join(str(item) for item in row.get('missed_terms', [])))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#365314}
*{box-sizing:border-box}
body{margin:0;background:#f2f4f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1280px;margin:0 auto;padding:28px}
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
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_html",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_markdown",
    "render_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_text",
    "write_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_outputs",
]
