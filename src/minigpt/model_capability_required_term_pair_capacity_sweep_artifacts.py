from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_capacity_sweep import (
    REQUIRED_TERM_PAIR_CAPACITY_SWEEP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_CAPACITY_SWEEP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_CAPACITY_SWEEP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_CAPACITY_SWEEP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_capacity_sweep_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("pair_capacity_sweep_decision", summary.get("pair_capacity_sweep_decision")),
        ("source_pair_rebalance_seed_stability_decision", summary.get("source_pair_rebalance_seed_stability_decision")),
        ("selected_pair_count", summary.get("selected_pair_count")),
        ("variant_count", summary.get("variant_count")),
        ("variant_run_count", summary.get("variant_run_count")),
        ("probe_count", summary.get("probe_count")),
        ("training_pass_count", summary.get("training_pass_count")),
        ("checkpoint_exists_count", summary.get("checkpoint_exists_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("variant_pair_full_hit_count", summary.get("variant_pair_full_hit_count")),
        ("variant_pair_partial_hit_count", summary.get("variant_pair_partial_hit_count")),
        ("variant_pair_full_hit_rate", summary.get("variant_pair_full_hit_rate")),
        ("capacity_full_hit_pair_count", summary.get("capacity_full_hit_pair_count")),
        ("capacity_full_hit_observed", summary.get("capacity_full_hit_observed")),
        ("best_variant_id", summary.get("best_variant_id")),
        ("best_variant_hit_count", summary.get("best_variant_hit_count")),
        ("best_variant_pair_full_hit", summary.get("best_variant_pair_full_hit")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_capacity_sweep_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "capacity_run_id",
        "pair_id",
        "variant_id",
        "variant_label",
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


def render_model_capability_required_term_pair_capacity_sweep_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    variant_table = [
        "| Pair | Variant | Hits | Missed | Hit rate | Full hit |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("variant_pair_summaries")):
        variant_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("pair_id")),
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(", ".join(str(term) for term in row.get("hit_terms") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("missed_terms") or [])),
                    markdown_cell(row.get("hit_rate")),
                    markdown_cell(row.get("pair_full_hit")),
                ]
            )
            + " |"
        )
    pair_table = [
        "| Pair | Full-hit variants | Partial variants | Best variant | Best hit count |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("pair_capacity_summaries")):
        pair_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("pair_id")),
                    markdown_cell(", ".join(str(item) for item in row.get("full_hit_variants") or [])),
                    markdown_cell(", ".join(str(item) for item in row.get("partial_hit_variants") or [])),
                    markdown_cell(row.get("best_variant_id")),
                    markdown_cell(row.get("best_variant_hit_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Pair Capacity Sweep",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Sweep decision: `{summary.get('pair_capacity_sweep_decision')}`",
            f"- Source seed-stability decision: `{summary.get('source_pair_rebalance_seed_stability_decision')}`",
            f"- Selected pairs: `{summary.get('selected_pair_count')}`",
            f"- Capacity variants: `{summary.get('variant_count')}`",
            f"- Variant runs: `{summary.get('variant_run_count')}`",
            f"- Training pass count: `{summary.get('training_pass_count')}`",
            f"- Full-hit variant pairs: `{summary.get('variant_pair_full_hit_count')}`",
            f"- Capacity full-hit observed: `{summary.get('capacity_full_hit_observed')}`",
            "",
            "## Variant Results",
            "",
            *variant_table,
            "",
            "## Pair Summary",
            "",
            *pair_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_capacity_sweep_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("pair_capacity_sweep_decision")),
        ("Variants", summary.get("variant_count")),
        ("Runs", summary.get("variant_run_count")),
        ("Probe hits", summary.get("probe_hit_count")),
        ("Full variant pairs", summary.get("variant_pair_full_hit_count")),
        ("Recovered", summary.get("capacity_full_hit_observed")),
        ("Best variant", summary.get("best_variant_id")),
    ]
    variant_rows = "\n".join(_variant_summary_html(row) for row in list_of_dicts(report.get("variant_pair_summaries")))
    pair_rows = "\n".join(_pair_capacity_html(row) for row in list_of_dicts(report.get("pair_capacity_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair capacity sweep</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term pair capacity sweep</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Experiment Boundary</h2><p>This run keeps the fragile v496 pair fixed and varies only training budget, embedding width, or corpus density. A recovered full hit is still a tiny-model signal, not a production quality claim.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Variant Results</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Variant</th><th>Hit terms</th><th>Missed terms</th><th>Rate</th><th>Full hit</th></tr></thead>
<tbody>{variant_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Pair Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Pair</th><th>Full-hit variants</th><th>Partial variants</th><th>Best variant</th><th>Best hits</th></tr></thead>
<tbody>{pair_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_capacity_sweep_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_CAPACITY_SWEEP_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_capacity_sweep.csv",
        "text": root / REQUIRED_TERM_PAIR_CAPACITY_SWEEP_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_CAPACITY_SWEEP_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_CAPACITY_SWEEP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_capacity_sweep_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_capacity_sweep_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_capacity_sweep_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_capacity_sweep_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _variant_summary_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('pair_id'))}</td>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('missed_terms') or []))}</td>"
        f"<td>{html_escape(row.get('hit_rate'))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        "</tr>"
    )


def _pair_capacity_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('pair_id'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('full_hit_variants') or []))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('partial_hit_variants') or []))}</td>"
        f"<td>{html_escape(row.get('best_variant_id'))}</td>"
        f"<td>{html_escape(row.get('best_variant_hit_count'))}</td>"
        "</tr>"
    )


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f4f6f7; color: #142126; }
body { margin: 0; padding: 28px; }
main { max-width: 1220px; margin: 0 auto; }
header { border-bottom: 1px solid #d8e0e3; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #53646b; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #d8e0e3; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(20, 33, 38, 0.05); }
.card span { display: block; color: #64757c; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 880px; }
th, td { text-align: left; border-bottom: 1px solid #e2e9eb; padding: 10px; vertical-align: top; }
th { color: #52656c; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
