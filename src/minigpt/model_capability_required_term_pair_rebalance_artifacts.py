from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_rebalance import (
    REQUIRED_TERM_PAIR_REBALANCE_HTML_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_rebalance_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("pair_rebalance_decision", summary.get("pair_rebalance_decision")),
        ("source_pair_curriculum_decision", summary.get("source_pair_curriculum_decision")),
        ("source_probe_hit_count", summary.get("source_probe_hit_count")),
        ("source_pair_full_hit_count", summary.get("source_pair_full_hit_count")),
        ("selected_pair_count", summary.get("selected_pair_count")),
        ("pair_run_count", summary.get("pair_run_count")),
        ("probe_count", summary.get("probe_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("probe_hit_delta", summary.get("probe_hit_delta")),
        ("pair_full_hit_count", summary.get("pair_full_hit_count")),
        ("pair_full_hit_delta", summary.get("pair_full_hit_delta")),
        ("pair_partial_hit_count", summary.get("pair_partial_hit_count")),
        ("pair_full_success_rate", summary.get("pair_full_success_rate")),
        ("rebalance_improved", summary.get("rebalance_improved")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_rebalance_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "pair_id",
        "term_names",
        "source_hit_terms",
        "source_missed_terms",
        "rebalance_hit_terms",
        "rebalance_missed_terms",
        "source_hit_count",
        "rebalance_hit_count",
        "hit_count_delta",
        "source_pair_full_hit",
        "rebalance_pair_full_hit",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("compare_rows")):
            writer.writerow({field: csv_cell(_compare_csv_value(field, row)) for field in fieldnames})


def render_model_capability_required_term_pair_rebalance_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Pair | Source hits | Rebalance hits | Delta | Full after |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("compare_rows")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(", ".join(str(term) for term in row.get("term_names") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("source_hit_terms") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("rebalance_hit_terms") or [])),
                    markdown_cell(row.get("hit_count_delta")),
                    markdown_cell(row.get("rebalance_pair_full_hit")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Pair Rebalance",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Rebalance decision: `{summary.get('pair_rebalance_decision')}`",
            f"- Source pair decision: `{summary.get('source_pair_curriculum_decision')}`",
            f"- Selected pairs: `{summary.get('selected_pair_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Checkpoints: `{summary.get('checkpoint_exists_count')}`",
            f"- Probe hits: `{summary.get('probe_hit_count')}`",
            f"- Probe hit delta: `{summary.get('probe_hit_delta')}`",
            f"- Full-hit pairs: `{summary.get('pair_full_hit_count')}`",
            f"- Full-hit delta: `{summary.get('pair_full_hit_delta')}`",
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


def render_model_capability_required_term_pair_rebalance_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("pair_rebalance_decision")),
        ("Source hits", summary.get("source_probe_hit_count")),
        ("Rebalance hits", summary.get("probe_hit_count")),
        ("Hit delta", summary.get("probe_hit_delta")),
        ("Full pairs", summary.get("pair_full_hit_count")),
        ("Full delta", summary.get("pair_full_hit_delta")),
        ("Improved", summary.get("rebalance_improved")),
    ]
    compare_rows = "\n".join(_compare_html(row) for row in list_of_dicts(report.get("compare_rows")))
    probe_rows = "\n".join(_probe_html(row) for row in list_of_dicts(report.get("probe_rows")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair rebalance</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term pair rebalance</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Experiment Boundary</h2><p>This run keeps the v494 pair set fixed and changes only the two-term corpus organization. It is a capacity probe, not a production-quality language benchmark.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Pair Comparison</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Before hits</th><th>After hits</th><th>Delta</th><th>Full after</th></tr></thead>
<tbody>{compare_rows}</tbody>
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


def write_model_capability_required_term_pair_rebalance_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_REBALANCE_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_rebalance.csv",
        "text": root / REQUIRED_TERM_PAIR_REBALANCE_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_REBALANCE_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_REBALANCE_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_rebalance_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_rebalance_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_rebalance_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_rebalance_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _compare_csv_value(field: str, row: dict[str, Any]) -> Any:
    value = row.get(field)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return value


def _compare_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('term_names') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('source_hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('rebalance_hit_terms') or []))}</td>"
        f"<td>{html_escape(row.get('hit_count_delta'))}</td>"
        f"<td>{html_escape(row.get('rebalance_pair_full_hit'))}</td>"
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
