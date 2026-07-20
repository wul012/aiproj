from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CSV_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_HTML_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSONL_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card_label_value as _card


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            f"status={report.get('status')}",
            f"decision={report.get('decision')}",
            f"bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready={summary.get('bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready')}",
            f"patch_example_count={summary.get('patch_example_count')}",
            f"loss_focus_example_count={summary.get('loss_focus_example_count')}",
            f"completion_surface_example_count={summary.get('completion_surface_example_count')}",
            f"patched_corpus_char_count={summary.get('patched_corpus_char_count')}",
            f"model_quality_claim={summary.get('model_quality_claim')}",
            f"next_action={interpretation.get('next_action')}",
            "",
        ]
    )


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    return "\n".join(
        [
            "# MiniGPT Bounded Objective Seed Revision Curriculum Patch",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Patch examples: `{summary.get('patch_example_count')}`",
            f"- Loss-focus examples: `{summary.get('loss_focus_example_count')}`",
            f"- Completion-surface examples: `{summary.get('completion_surface_example_count')}`",
            f"- Patch kinds: `{summary.get('patch_kinds')}`",
            f"- Claim: `{summary.get('model_quality_claim')}`",
            "",
            "## Patch Examples",
            "",
            *_example_table(report),
            "",
            "## Boundary",
            "",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: `{interpretation.get('next_action')}`",
            "",
        ]
    )


def render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Patch examples", summary.get("patch_example_count")),
        ("Loss focus", summary.get("loss_focus_example_count")),
        ("Completion surface", summary.get("completion_surface_example_count")),
        ("Corpus chars", summary.get("patched_corpus_char_count")),
        ("Claim", summary.get("model_quality_claim")),
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
main{{max-width:1160px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}}
.card{{border:1px solid #d8dee4;border-radius:8px;padding:10px;background:#fbfcfd}}
.label{{font-size:12px;color:#57606a}}strong{{display:block;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
</style>
</head>
<body><main>
<header><h1>{html_escape(report.get('title'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section><h2>Patch Examples</h2>{_example_html(report)}</section>
<section><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
</main></body></html>"""


def write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CSV_FILENAME,
        "jsonl": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSONL_FILENAME,
        "corpus": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    _write_csv(report, paths["csv"])
    _write_jsonl(report, paths["jsonl"])
    paths["corpus"].write_text(str(report.get("patched_corpus_text") or ""), encoding="utf-8")
    paths["text"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["example_id", "kind", "prompt", "completion", "decoder_anchor", "purpose"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("patch_examples")):
            writer.writerow({field: row.get(field) for field in fieldnames})


def _write_jsonl(report: dict[str, Any], path: Path) -> None:
    rows = [json.dumps(row, ensure_ascii=False) for row in list_of_dicts(report.get("patch_examples"))]
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def _example_table(report: dict[str, Any]) -> list[str]:
    rows = ["| Example | Kind | Prompt | Completion | Purpose |", "| --- | --- | --- | --- | --- |"]
    for row in list_of_dicts(report.get("patch_examples")):
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("example_id")),
                    markdown_cell(row.get("kind")),
                    markdown_cell(row.get("prompt")),
                    markdown_cell(row.get("completion")),
                    markdown_cell(row.get("purpose")),
                ]
            )
            + " |"
        )
    return rows


def _example_html(report: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{html_escape(row.get('example_id'))}</td>"
        f"<td>{html_escape(row.get('kind'))}</td>"
        f"<td><pre>{html_escape(row.get('prompt'))}</pre></td>"
        f"<td><pre>{html_escape(row.get('completion'))}</pre></td>"
        f"<td>{html_escape(row.get('purpose'))}</td>"
        "</tr>"
        for row in list_of_dicts(report.get("patch_examples"))
    )
    return f"<table><thead><tr><th>Example</th><th>Kind</th><th>Prompt</th><th>Completion</th><th>Purpose</th></tr></thead><tbody>{body}</tbody></table>"


__all__ = [
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_html",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_markdown",
    "render_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_text",
    "write_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_outputs",
]
