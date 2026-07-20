from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.curriculum_patch_shape_diag import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready={summary.get('bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready')}",
            f"case_count={summary.get('case_count')}",
            f"improved_case_count={summary.get('improved_case_count')}",
            f"regressed_case_count={summary.get('regressed_case_count')}",
            f"stable_partial_case_count={summary.get('stable_partial_case_count')}",
            f"any_hit_case_delta={summary.get('any_hit_case_delta')}",
            f"zero_hit_case_delta={summary.get('zero_hit_case_delta')}",
            f"loss_missed_after_count={summary.get('loss_missed_after_count')}",
            f"next_action={summary.get('next_action')}",
            "",
        ]
    )


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Bounded Objective Curriculum Patch Shape Migration Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Improved cases: `{summary.get('improved_case_count')}`",
            f"- Regressed cases: `{summary.get('regressed_case_count')}`",
            f"- Stable partial cases: `{summary.get('stable_partial_case_count')}`",
            f"- Any-hit delta: `{summary.get('any_hit_case_delta')}`",
            f"- Zero-hit delta: `{summary.get('zero_hit_case_delta')}`",
            f"- Claim: `{summary.get('model_quality_claim')}`",
            "",
            "## Case Migration",
            "",
            *_migration_table(report),
            "",
            "## Root Causes",
            "",
            *_cause_table(report),
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: `{interpretation.get('next_action')}`",
            "",
        ]
    )


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Improved", summary.get("improved_case_count")),
        ("Regressed", summary.get("regressed_case_count")),
        ("Stable partial", summary.get("stable_partial_case_count")),
        ("Any-hit delta", summary.get("any_hit_case_delta")),
        ("Zero-hit delta", summary.get("zero_hit_case_delta")),
        ("Loss missed after", summary.get("loss_missed_after_count")),
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
main{{max-width:1180px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}}
.card{{border:1px solid #d8dee4;border-radius:8px;padding:10px;background:#fbfcfd}}
.label{{font-size:12px;color:#57606a}}strong{{display:block;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
</style>
</head>
<body><main>
<header><h1>{html_escape(report.get('title'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section><h2>Case Migration</h2>{_migration_html(report)}</section>
<section><h2>Root Causes</h2>{_cause_html(report)}</section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["case_id", "migration_class", "pre_hit_terms", "post_hit_terms", "pre_missed_terms", "post_missed_terms", "pre_continuation", "post_continuation"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("migration_rows")):
            writer.writerow({field: row.get(field) for field in fieldnames})


def _migration_table(report: dict[str, Any]) -> list[str]:
    rows = ["| Case | Migration | Pre hit | Post hit | Pre missed | Post missed |", "| --- | --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("migration_rows")):
        rows.append("| " + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(row.get("migration_class")), markdown_cell(row.get("pre_hit_terms")), markdown_cell(row.get("post_hit_terms")), markdown_cell(row.get("pre_missed_terms")), markdown_cell(row.get("post_missed_terms"))]) + " |")
    return rows


def _cause_table(report: dict[str, Any]) -> list[str]:
    rows = ["| Cause | Severity | Detail | Evidence |", "| --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("root_causes")):
        rows.append("| " + " | ".join([markdown_cell(row.get("cause_id")), markdown_cell(row.get("severity")), markdown_cell(row.get("detail")), markdown_cell(row.get("evidence"))]) + " |")
    return rows


def _migration_html(report: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('migration_class'))}</td>"
        f"<td>{html_escape(row.get('pre_hit_terms'))}</td>"
        f"<td>{html_escape(row.get('post_hit_terms'))}</td>"
        f"<td>{html_escape(row.get('pre_missed_terms'))}</td>"
        f"<td>{html_escape(row.get('post_missed_terms'))}</td>"
        f"<td><pre>{html_escape(row.get('post_continuation'))}</pre></td>"
        "</tr>"
        for row in list_of_dicts(report.get("migration_rows"))
    )
    return f"<table><thead><tr><th>Case</th><th>Migration</th><th>Pre hit</th><th>Post hit</th><th>Pre missed</th><th>Post missed</th><th>Post continuation</th></tr></thead><tbody>{body}</tbody></table>"


def _cause_html(report: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('cause_id'))}</td>"
        f"<td>{html_escape(row.get('severity'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        f"<td>{html_escape(row.get('evidence'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("root_causes"))
    )
    return f"<table><thead><tr><th>Cause</th><th>Severity</th><th>Detail</th><th>Evidence</th></tr></thead><tbody>{body}</tbody></table>"


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{html_escape(label)}</div><strong>{html_escape(value)}</strong></div>'


__all__ = [
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_html",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_markdown",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_text",
    "write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_outputs",
]
