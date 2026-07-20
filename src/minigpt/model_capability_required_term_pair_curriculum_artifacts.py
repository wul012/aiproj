from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_curriculum import (
    REQUIRED_TERM_PAIR_CURRICULUM_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CURRICULUM_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_curriculum_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("pair_curriculum_decision", summary.get("pair_curriculum_decision")),
        ("source_stable_term_count", summary.get("source_stable_term_count")),
        ("selected_term_count", summary.get("selected_term_count")),
        ("pair_count", summary.get("pair_count")),
        ("pair_run_count", summary.get("pair_run_count")),
        ("probe_count", summary.get("probe_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("probe_success_rate", summary.get("probe_success_rate")),
        ("pair_full_hit_count", summary.get("pair_full_hit_count")),
        ("pair_partial_hit_count", summary.get("pair_partial_hit_count")),
        ("pair_full_success_rate", summary.get("pair_full_success_rate")),
        ("multi_target_pair_capacity_observed", summary.get("multi_target_pair_capacity_observed")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_curriculum_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "pair_id",
        "pair_terms",
        "term",
        "case",
        "scaffold_prompt",
        "generation_seed",
        "training_status",
        "checkpoint_exists",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
        "checkpoint_path",
    ]
    pair_rows = {str(row.get("pair_id") or ""): row for row in list_of_dicts(report.get("pair_rows"))}
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            pair = pair_rows.get(str(row.get("pair_id") or ""), {})
            writer.writerow({field: csv_cell(_probe_csv_value(field, row, pair)) for field in fieldnames})


def render_model_capability_required_term_pair_curriculum_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Pair | Hit terms | Missed terms | Hit rate | Full hit |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("pair_summaries")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(", ".join(str(term) for term in row.get("term_names") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("hit_terms") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("missed_terms") or [])),
                    markdown_cell(row.get("hit_rate")),
                    markdown_cell(row.get("pair_full_hit")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Pair Curriculum",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Pair decision: `{summary.get('pair_curriculum_decision')}`",
            f"- Source stable terms: `{summary.get('source_stable_term_count')}`",
            f"- Selected terms: `{summary.get('selected_term_count')}`",
            f"- Pairs: `{summary.get('pair_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Checkpoints: `{summary.get('checkpoint_exists_count')}`",
            f"- Probe hits: `{summary.get('probe_hit_count')}`",
            f"- Full-hit pairs: `{summary.get('pair_full_hit_count')}`",
            f"- Partial pairs: `{summary.get('pair_partial_hit_count')}`",
            "",
            *table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_curriculum_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("pair_curriculum_decision")),
        ("Stable source terms", summary.get("source_stable_term_count")),
        ("Selected terms", summary.get("selected_term_count")),
        ("Pairs", summary.get("pair_count")),
        ("Training pass", summary.get("training_pass_count")),
        ("Checkpoints", summary.get("checkpoint_exists_count")),
        ("Probe hits", summary.get("probe_hit_count")),
        ("Full-hit pairs", summary.get("pair_full_hit_count")),
        ("Pair capacity", summary.get("multi_target_pair_capacity_observed")),
    ]
    pair_rows = "\n".join(_pair_summary_html(row) for row in list_of_dicts(report.get("pair_summaries")))
    probe_rows = "\n".join(_probe_html(row) for row in list_of_dicts(report.get("probe_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair curriculum</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term pair curriculum</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Curriculum Boundary</h2><p>Only v493 terms that were stable across every configured seed are selected by default. Each row below trains two targets in one checkpoint; it is a controlled interference probe, not a broad language-quality benchmark.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Pair Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Hit terms</th><th>Missed terms</th><th>Hit rate</th><th>Full hit</th></tr></thead>
<tbody>{pair_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Probe Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Term</th><th>Seed</th><th>Hit</th><th>Preview</th><th>Checkpoint</th></tr></thead>
<tbody>{probe_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_curriculum_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_CURRICULUM_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_curriculum.csv",
        "text": root / REQUIRED_TERM_PAIR_CURRICULUM_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_CURRICULUM_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_CURRICULUM_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_curriculum_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_curriculum_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_curriculum_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_curriculum_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _probe_csv_value(field: str, row: dict[str, Any], pair: dict[str, Any]) -> Any:
    if field == "training_status":
        return pair.get("training_status")
    if field == "checkpoint_exists":
        return pair.get("checkpoint_exists")
    return row.get(field)


def _pair_summary_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('term_names') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('missed_terms') or []))}</td>"
        f"<td>{html_escape(row.get('hit_rate'))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        "</tr>"
    )


def _probe_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('pair_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('generation_seed'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_path'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f5f6f2; color: #17211f; }
body { margin: 0; padding: 28px; }
main { max-width: 1220px; margin: 0 auto; }
header { border-bottom: 1px solid #dce1d5; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #5a675f; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dce1d5; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 33, 31, 0.05); }
.card span { display: block; color: #657269; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 940px; }
th, td { text-align: left; border-bottom: 1px solid #e5eadf; padding: 10px; vertical-align: top; }
th { color: #52605a; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
