from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_diagnostic_rollup import (
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_diagnostic_rollup_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    plan = as_dict(report.get("next_experiment_plan"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("rollup_decision", summary.get("rollup_decision")),
        ("next_plan_id", plan.get("plan_id")),
        ("next_plan_recommended", plan.get("recommended")),
        ("stage_count", summary.get("stage_count")),
        ("passing_stage_count", summary.get("passing_stage_count")),
        ("decoding_profile_full_hit_count", summary.get("decoding_profile_full_hit_count")),
        ("span_completion_gap_probe_count", summary.get("span_completion_gap_probe_count")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_diagnostic_rollup_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["stage", "label", "status", "decision", "key_metric", "source_path"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("stage_rows")):
            output_row = {field: _csv_clean(row.get(field)) for field in fieldnames}
            output_row["key_metric"] = _csv_clean(_stage_metric(row))
            writer.writerow(output_row)


def render_model_capability_required_term_pair_diagnostic_rollup_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    plan = as_dict(report.get("next_experiment_plan"))
    table = ["| Stage | Status | Decision | Key metric | Source |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("stage_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("label")),
                    markdown_cell(row.get("status")),
                    markdown_cell(row.get("decision")),
                    markdown_cell(_stage_metric(row)),
                    markdown_cell(row.get("source_path")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Diagnostic Rollup",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Rollup decision: `{summary.get('rollup_decision')}`",
            f"- Passing stages: `{summary.get('passing_stage_count')}/{summary.get('stage_count')}`",
            "",
            "## Stages",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
            "## Next Experiment Plan",
            "",
            f"- Plan: `{plan.get('plan_id')}`",
            f"- Recommended: `{plan.get('recommended')}`",
            f"- Reason: {plan.get('reason')}",
            "",
            "### Steps",
            "",
            *[f"- {markdown_cell(step)}" for step in _list(plan.get("steps"))],
            "",
            "### Minimum Success Criteria",
            "",
            *[f"- {markdown_cell(item)}" for item in _list(plan.get("minimum_success_criteria"))],
            "",
            "### Excluded Options",
            "",
            *[f"- {markdown_cell(item)}" for item in _list(plan.get("excluded_options"))],
            "",
        ]
    )


def render_model_capability_required_term_pair_diagnostic_rollup_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    plan = as_dict(report.get("next_experiment_plan"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("rollup_decision")),
        ("Stages", summary.get("stage_count")),
        ("Full profiles", summary.get("decoding_profile_full_hit_count")),
        ("Late hits", summary.get("path_late_hit_count")),
        ("Improved", summary.get("first_token_repair_improved_prompt_count")),
        ("Span gaps", summary.get("span_completion_gap_probe_count")),
    ]
    rows = "\n".join(_stage_row_html(row) for row in list_of_dicts(report.get("stage_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair diagnostic rollup</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair diagnostic rollup</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Next Experiment Plan</h2>
<p><strong>{html_escape(plan.get('plan_id'))}</strong> · recommended={html_escape(plan.get('recommended'))}</p>
<p>{html_escape(plan.get('reason'))}</p>
<div class="cols">
<div><h3>Steps</h3>{_items(plan.get('steps'))}</div>
<div><h3>Success Criteria</h3>{_items(plan.get('minimum_success_criteria'))}</div>
<div><h3>Excluded</h3>{_items(plan.get('excluded_options'))}</div>
</div>
</section>
<section class="panel">
<h2>Stages</h2>
<div class="table-wrap"><table>
<thead><tr><th>Stage</th><th>Status</th><th>Decision</th><th>Key metric</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_diagnostic_rollup_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_diagnostic_rollup.csv",
        "text": root / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_diagnostic_rollup_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_diagnostic_rollup_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_model_capability_required_term_pair_diagnostic_rollup_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_model_capability_required_term_pair_diagnostic_rollup_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _stage_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('label'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('decision'))}</td>"
        f"<td>{html_escape(_stage_metric(row))}</td>"
        f"<td class=\"path\">{html_escape(row.get('source_path'))}</td>"
        "</tr>"
    )


def _items(values: Any) -> str:
    rows = "".join(f"<li>{html_escape(value)}</li>" for value in _list(values))
    return f"<ul>{rows}</ul>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#4f46e5}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
h3{font-size:14px;margin:8px 0;color:#334155}
p{color:var(--muted);line-height:1.55}
ul{margin:8px 0 0;padding-left:18px;color:var(--muted);line-height:1.5}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
.path{font-family:Consolas,"Courier New",monospace;font-size:12px;overflow-wrap:anywhere;color:#475569}
</style>"""


def _csv_clean(value: Any) -> Any:
    cell = csv_cell(value)
    return cell.rstrip() if isinstance(cell, str) else cell


def _stage_metric(row: dict[str, Any]) -> str:
    summary = as_dict(row.get("summary"))
    stage = str(row.get("stage") or "")
    metrics = {
        "forced_choice": f"full_match_variants={summary.get('forced_choice_full_match_variant_count')}",
        "generation_gap": f"internal_only_prompts={summary.get('internal_only_prompt_count')}",
        "decoding_gap": f"continuation_hits={summary.get('continuation_hit_count')}; full_profiles={summary.get('profile_full_hit_count')}",
        "path_trace": f"first_sample_matches={summary.get('first_sample_match_count')}; late_hits={summary.get('late_hit_after_first_miss_count')}",
        "first_token_repair": f"improved_prompts={summary.get('improved_prompt_count')}; full_profiles={summary.get('repaired_profile_full_hit_count')}",
        "prefix_completion": f"one_token_hits={summary.get('one_token_prefix_hit_probe_count')}; span_gaps={summary.get('span_completion_gap_probe_count')}",
    }
    return metrics.get(stage, "")


def _list(values: Any) -> list[Any]:
    return values if isinstance(values, list) else []
