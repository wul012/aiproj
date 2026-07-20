from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_rebalance_seed_stability import (
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_HTML_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_rebalance_seed_stability_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("pair_rebalance_seed_stability_decision", summary.get("pair_rebalance_seed_stability_decision")),
        ("source_pair_rebalance_decision", summary.get("source_pair_rebalance_decision")),
        ("source_pair_full_hit_count", summary.get("source_pair_full_hit_count")),
        ("source_pair_full_hit_delta", summary.get("source_pair_full_hit_delta")),
        ("selected_pair_count", summary.get("selected_pair_count")),
        ("seed_count", summary.get("seed_count")),
        ("pair_seed_run_count", summary.get("pair_seed_run_count")),
        ("probe_count", summary.get("probe_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("pair_seed_full_hit_count", summary.get("pair_seed_full_hit_count")),
        ("pair_seed_full_hit_rate", summary.get("pair_seed_full_hit_rate")),
        ("stable_pair_count", summary.get("stable_pair_count")),
        ("partial_stable_pair_count", summary.get("partial_stable_pair_count")),
        ("pair_rebalance_seed_stable", summary.get("pair_rebalance_seed_stable")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_rebalance_seed_stability_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "pair_seed_run_id",
        "pair_id",
        "seed",
        "term",
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
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_rebalance_seed_stability_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    table = [
        "| Pair | v495 hits | Full-hit seeds | Missed seeds | Full-hit rate | Stable |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("pair_seed_summaries")):
        table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(", ".join(str(term) for term in row.get("term_names") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("v495_hit_terms") or [])),
                    markdown_cell(", ".join(str(seed) for seed in row.get("full_hit_seeds") or [])),
                    markdown_cell(", ".join(str(seed) for seed in row.get("missed_full_hit_seeds") or [])),
                    markdown_cell(row.get("full_hit_rate")),
                    markdown_cell(row.get("stable_full_hit_across_seeds")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Pair Rebalance Seed Stability",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Seed-stability decision: `{summary.get('pair_rebalance_seed_stability_decision')}`",
            f"- Source rebalance decision: `{summary.get('source_pair_rebalance_decision')}`",
            f"- Selected pairs: `{summary.get('selected_pair_count')}`",
            f"- Seeds: `{summary.get('seed_count')}`",
            f"- Pair-seed runs: `{summary.get('pair_seed_run_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Pair-seed full hits: `{summary.get('pair_seed_full_hit_count')}`",
            f"- Stable pairs: `{summary.get('stable_pair_count')}`",
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


def render_model_capability_required_term_pair_rebalance_seed_stability_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("pair_rebalance_seed_stability_decision")),
        ("Pairs", summary.get("selected_pair_count")),
        ("Seeds", summary.get("seed_count")),
        ("Runs", summary.get("pair_seed_run_count")),
        ("Full seed hits", summary.get("pair_seed_full_hit_count")),
        ("Stable pairs", summary.get("stable_pair_count")),
        ("Stable signal", summary.get("pair_rebalance_seed_stable")),
    ]
    pair_rows = "\n".join(_pair_summary_html(row) for row in list_of_dicts(report.get("pair_seed_summaries")))
    seed_rows = "\n".join(_seed_pair_html(row) for row in list_of_dicts(report.get("seed_pair_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair rebalance seed stability</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term pair rebalance seed stability</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Stability Boundary</h2><p>This run repeats only v495 full-hit gain pairs across seeds. It tests whether the pair-level signal is stable before any three-term curriculum expansion.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Pair Stability</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>v495 hits</th><th>Full-hit seeds</th><th>Missed seeds</th><th>Rate</th><th>Stable</th></tr></thead>
<tbody>{pair_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Seed Pair Rows</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Seed</th><th>Hit terms</th><th>Missed terms</th><th>Full hit</th></tr></thead>
<tbody>{seed_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_rebalance_seed_stability_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_rebalance_seed_stability.csv",
        "text": root / REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_REBALANCE_SEED_STABILITY_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_rebalance_seed_stability_csv(report, paths["csv"])
    paths["text"].write_text(
        render_model_capability_required_term_pair_rebalance_seed_stability_text(report),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_rebalance_seed_stability_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_model_capability_required_term_pair_rebalance_seed_stability_html(report),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _pair_summary_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('term_names') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('v495_hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(seed) for seed in row.get('full_hit_seeds') or []))}</td>"
        f"<td>{html_escape(', '.join(str(seed) for seed in row.get('missed_full_hit_seeds') or []))}</td>"
        f"<td>{html_escape(row.get('full_hit_rate'))}</td>"
        f"<td>{html_escape(row.get('stable_full_hit_across_seeds'))}</td>"
        "</tr>"
    )


def _seed_pair_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('pair_id'))}</td>"
        f"<td>{html_escape(row.get('seed'))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('missed_terms') or []))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
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
table { width: 100%; border-collapse: collapse; min-width: 880px; }
th, td { text-align: left; border-bottom: 1px solid #e5eadf; padding: 10px; vertical-align: top; }
th { color: #52605a; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
