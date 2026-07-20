from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_one_term_seed_stability import (
    REQUIRED_TERM_ONE_TERM_SEED_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_ONE_TERM_SEED_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_ONE_TERM_SEED_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_ONE_TERM_SEED_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_one_term_seed_stability_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("one_term_seed_stability_decision", summary.get("one_term_seed_stability_decision")),
        ("source_successful_term_count", summary.get("source_successful_term_count")),
        ("selected_term_count", summary.get("selected_term_count")),
        ("seed_count", summary.get("seed_count")),
        ("seed_run_count", summary.get("seed_run_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("continuation_hit_count", summary.get("continuation_hit_count")),
        ("term_seed_hit_count", summary.get("term_seed_hit_count")),
        ("term_seed_success_rate", summary.get("term_seed_success_rate")),
        ("stable_term_count", summary.get("stable_term_count")),
        ("partial_stable_term_count", summary.get("partial_stable_term_count")),
        ("single_term_capacity_stable", summary.get("single_term_capacity_stable")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_one_term_seed_stability_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "one_term_seed_run_id",
        "case",
        "term",
        "seed",
        "scaffold_prompt",
        "source_continuation_hit_count",
        "training_status",
        "checkpoint_exists",
        "one_term_line_count",
        "one_term_repeat",
        "generation_seed",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
        "checkpoint_path",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("seed_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_one_term_seed_stability_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Term | Source hit | Hit seeds | Missed seeds | Hit rate | Stable |",
        "| --- | ---: | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("term_seed_summaries")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("term")),
                    markdown_cell(row.get("source_continuation_hit_count")),
                    markdown_cell(", ".join(str(seed) for seed in row.get("hit_seeds") or [])),
                    markdown_cell(", ".join(str(seed) for seed in row.get("missed_seeds") or [])),
                    markdown_cell(row.get("hit_rate")),
                    markdown_cell(row.get("stable_across_seeds")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term One-Term Seed Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Seed-stability decision: `{summary.get('one_term_seed_stability_decision')}`",
            f"- Source successful terms: `{summary.get('source_successful_term_count')}`",
            f"- Selected terms: `{summary.get('selected_term_count')}`",
            f"- Seeds: `{summary.get('seed_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Checkpoints: `{summary.get('checkpoint_exists_count')}`",
            f"- Term-seed hits: `{summary.get('term_seed_hit_count')}`",
            f"- Stable terms: `{summary.get('stable_term_count')}`",
            f"- Partial terms: `{summary.get('partial_stable_term_count')}`",
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


def render_model_capability_required_term_one_term_seed_stability_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("one_term_seed_stability_decision")),
        ("Terms", summary.get("selected_term_count")),
        ("Seeds", summary.get("seed_count")),
        ("Runs", summary.get("seed_run_count")),
        ("Training pass", summary.get("training_pass_count")),
        ("Checkpoints", summary.get("checkpoint_exists_count")),
        ("Term-seed hits", summary.get("term_seed_hit_count")),
        ("Stable terms", summary.get("stable_term_count")),
        ("Stable capacity", summary.get("single_term_capacity_stable")),
    ]
    term_rows = "\n".join(_term_summary_html(row) for row in list_of_dicts(report.get("term_seed_summaries")))
    seed_rows = "\n".join(_seed_run_html(row) for row in list_of_dicts(report.get("seed_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT one-term seed stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term one-term seed stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Stability Boundary</h2><p>Only v492 terms that already produced a one-term continuation hit are selected by default. This report does not claim general language ability; it checks whether isolated prompt-to-term uptake survives seed changes.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Term Stability</h2>
<div class="table-wrap"><table>
<thead><tr><th>Term</th><th>Source hit</th><th>Hit seeds</th><th>Missed seeds</th><th>Hit rate</th><th>Stable</th></tr></thead>
<tbody>{term_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Seed Runs</h2>
<div class="table-wrap"><table>
<thead><tr><th>Run</th><th>Term</th><th>Seed</th><th>Training</th><th>Checkpoint</th><th>Continuation hit</th><th>Preview</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_one_term_seed_stability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_ONE_TERM_SEED_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_required_term_one_term_seed_stability.csv",
        "text": root / REQUIRED_TERM_ONE_TERM_SEED_STABILITY_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_ONE_TERM_SEED_STABILITY_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_ONE_TERM_SEED_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_one_term_seed_stability_csv(report, paths["csv"])
    paths["text"].write_text(
        render_model_capability_required_term_one_term_seed_stability_text(report),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_model_capability_required_term_one_term_seed_stability_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_model_capability_required_term_one_term_seed_stability_html(report),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _term_summary_html(row: dict[str, Any]) -> str:
    hit_seeds = ", ".join(str(seed) for seed in row.get("hit_seeds") or [])
    missed_seeds = ", ".join(str(seed) for seed in row.get("missed_seeds") or [])
    return (
        "<tr>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('source_continuation_hit_count'))}</td>"
        f"<td>{html_escape(hit_seeds)}</td>"
        f"<td>{html_escape(missed_seeds)}</td>"
        f"<td>{html_escape(row.get('hit_rate'))}</td>"
        f"<td>{html_escape(row.get('stable_across_seeds'))}</td>"
        "</tr>"
    )


def _seed_run_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('one_term_seed_run_id'))}</td>"
        f"<td>{html_escape(row.get('term'))}</td>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(row.get('training_status'))}</td>"
        f"<td>{html_escape(row.get('checkpoint_exists'))}</td>"
        f"<td>{html_escape(row.get('continuation_hit_count'))}</td>"
        f"<td>{html_escape(row.get('continuation_preview'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f4f6f1; color: #17211e; }
body { margin: 0; padding: 28px; }
main { max-width: 1220px; margin: 0 auto; }
header { border-bottom: 1px solid #dce1d5; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #59665f; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dce1d5; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 33, 30, 0.05); }
.card span { display: block; color: #657269; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 920px; }
th, td { text-align: left; border-bottom: 1px solid #e5eadf; padding: 10px; vertical-align: top; }
th { color: #52605a; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
