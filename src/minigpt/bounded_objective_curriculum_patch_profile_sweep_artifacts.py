from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_curriculum_patch_profile_sweep import (
    CURRICULUM_PATCH_PROFILE_SWEEP_CSV_FILENAME,
    CURRICULUM_PATCH_PROFILE_SWEEP_HTML_FILENAME,
    CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME,
    CURRICULUM_PATCH_PROFILE_SWEEP_MARKDOWN_FILENAME,
    CURRICULUM_PATCH_PROFILE_SWEEP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_curriculum_patch_profile_sweep_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"bounded_objective_curriculum_patch_profile_sweep_ready={summary.get('bounded_objective_curriculum_patch_profile_sweep_ready')}",
            f"profile_count={summary.get('profile_count')}",
            f"sweep_row_count={summary.get('sweep_row_count')}",
            f"any_profile_recovered={summary.get('any_profile_recovered')}",
            f"profile_with_loss_hit_count={summary.get('profile_with_loss_hit_count')}",
            f"max_loss_hit_case_count={summary.get('max_loss_hit_case_count')}",
            f"best_profile_id={summary.get('best_profile_id')}",
            f"next_action={summary.get('next_action')}",
            "",
        ]
    )


def render_curriculum_patch_profile_sweep_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Bounded Objective Curriculum Patch Profile Sweep",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Profiles: `{summary.get('profile_count')}`",
            f"- Rows: `{summary.get('sweep_row_count')}`",
            f"- Any profile recovered: `{summary.get('any_profile_recovered')}`",
            f"- Profiles with loss hit: `{summary.get('profile_with_loss_hit_count')}`",
            f"- Best profile: `{summary.get('best_profile_id')}`",
            "",
            "## Profile Summaries",
            "",
            *_profile_table(report),
            "",
            "## Sweep Rows",
            "",
            *_sweep_table(report),
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: `{interpretation.get('next_action')}`",
            "",
        ]
    )


def render_curriculum_patch_profile_sweep_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Profiles", summary.get("profile_count")),
        ("Rows", summary.get("sweep_row_count")),
        ("Recovered", summary.get("any_profile_recovered")),
        ("Loss profiles", summary.get("profile_with_loss_hit_count")),
        ("Max loss hits", summary.get("max_loss_hit_case_count")),
        ("Best profile", summary.get("best_profile_id")),
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title'))}</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#f6f8fa;color:#172033;line-height:1.5}}
main{{max-width:1200px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}}
.card{{border:1px solid #d8dee4;border-radius:8px;padding:10px;background:#fbfcfd}}
.label{{font-size:12px;color:#57606a}}strong{{display:block;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
</style>
</head>
<body><main>
<header><h1>{html_escape(report.get('title'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section><h2>Profile Summaries</h2>{_profile_html(report)}</section>
<section><h2>Sweep Rows</h2>{_sweep_html(report)}</section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def write_curriculum_patch_profile_sweep_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME,
        "csv": root / CURRICULUM_PATCH_PROFILE_SWEEP_CSV_FILENAME,
        "text": root / CURRICULUM_PATCH_PROFILE_SWEEP_TEXT_FILENAME,
        "markdown": root / CURRICULUM_PATCH_PROFILE_SWEEP_MARKDOWN_FILENAME,
        "html": root / CURRICULUM_PATCH_PROFILE_SWEEP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_curriculum_patch_profile_sweep_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_curriculum_patch_profile_sweep_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_curriculum_patch_profile_sweep_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["profile_id", "case_id", "case_pass", "hit_terms", "missed_terms", "loss_hit", "fixed_hit", "continuation"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("sweep_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def _profile_table(report: dict[str, Any]) -> list[str]:
    rows = ["| Profile | Passed | Any hit | Zero hit | Loss hits | Recovered |", "| --- | ---: | ---: | ---: | ---: | --- |"]
    for row in list_of_dicts(report.get("profile_summaries")):
        rows.append("| " + " | ".join([markdown_cell(row.get("profile_id")), markdown_cell(row.get("passed_case_count")), markdown_cell(row.get("any_hit_case_count")), markdown_cell(row.get("zero_hit_case_count")), markdown_cell(row.get("loss_hit_case_count")), markdown_cell(row.get("objective_contract_recovered"))]) + " |")
    return rows


def _sweep_table(report: dict[str, Any]) -> list[str]:
    rows = ["| Profile | Case | Hit | Missed | Continuation |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("sweep_rows")):
        rows.append("| " + " | ".join([markdown_cell(row.get("profile_id")), markdown_cell(row.get("case_id")), markdown_cell(row.get("hit_terms")), markdown_cell(row.get("missed_terms")), markdown_cell(row.get("continuation"))]) + " |")
    return rows


def _profile_html(report: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('passed_case_count'))}</td>"
        f"<td>{html_escape(row.get('any_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('zero_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('loss_hit_case_count'))}</td>"
        f"<td>{html_escape(row.get('objective_contract_recovered'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("profile_summaries"))
    )
    return f"<table><thead><tr><th>Profile</th><th>Passed</th><th>Any hit</th><th>Zero hit</th><th>Loss hits</th><th>Recovered</th></tr></thead><tbody>{body}</tbody></table>"


def _sweep_html(report: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('hit_terms'))}</td>"
        f"<td>{html_escape(row.get('missed_terms'))}</td>"
        f"<td><pre>{html_escape(row.get('continuation'))}</pre></td>"
        "</tr>"
        for row in list_of_dicts(report.get("sweep_rows"))
    )
    return f"<table><thead><tr><th>Profile</th><th>Case</th><th>Hit</th><th>Missed</th><th>Continuation</th></tr></thead><tbody>{body}</tbody></table>"


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{html_escape(label)}</div><strong>{html_escape(value)}</strong></div>'


__all__ = [
    "render_curriculum_patch_profile_sweep_html",
    "render_curriculum_patch_profile_sweep_markdown",
    "render_curriculum_patch_profile_sweep_text",
    "write_curriculum_patch_profile_sweep_outputs",
]
