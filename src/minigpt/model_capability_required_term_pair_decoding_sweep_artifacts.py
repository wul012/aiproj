from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_decoding_sweep import (
    REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload
from minigpt.report_utils import html_card as _card


def render_model_capability_required_term_pair_decoding_sweep_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("pair_decoding_sweep_decision", summary.get("pair_decoding_sweep_decision")),
        ("source_pair_capacity_sweep_decision", summary.get("source_pair_capacity_sweep_decision")),
        ("target_count", summary.get("target_count")),
        ("profile_count", summary.get("profile_count")),
        ("profile_target_count", summary.get("profile_target_count")),
        ("probe_count", summary.get("probe_count")),
        ("probe_hit_count", summary.get("probe_hit_count")),
        ("profile_target_full_hit_count", summary.get("profile_target_full_hit_count")),
        ("profile_target_partial_hit_count", summary.get("profile_target_partial_hit_count")),
        ("profile_target_full_hit_rate", summary.get("profile_target_full_hit_rate")),
        ("decoding_full_hit_target_count", summary.get("decoding_full_hit_target_count")),
        ("decoding_full_hit_observed", summary.get("decoding_full_hit_observed")),
        ("best_target_id", summary.get("best_target_id")),
        ("best_profile_id", summary.get("best_profile_id")),
        ("best_profile_hit_count", summary.get("best_profile_hit_count")),
        ("best_profile_pair_full_hit", summary.get("best_profile_pair_full_hit")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_decoding_sweep_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "target_id",
        "pair_id",
        "variant_id",
        "profile_id",
        "term",
        "generation_seed",
        "max_new_tokens",
        "temperature",
        "top_k",
        "checkpoint_exists",
        "tokenizer_exists",
        "prompt_hit_count",
        "generated_hit_count",
        "continuation_hit_count",
        "prompt_truncated",
        "generated_preview",
        "continuation_preview",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("probe_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_decoding_sweep_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    profile_table = [
        "| Target | Profile | Hits | Missed | Hit rate | Full hit |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in list_of_dicts(report.get("profile_target_summaries")):
        profile_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("target_id")),
                    markdown_cell(row.get("profile_id")),
                    markdown_cell(", ".join(str(term) for term in row.get("hit_terms") or [])),
                    markdown_cell(", ".join(str(term) for term in row.get("missed_terms") or [])),
                    markdown_cell(row.get("hit_rate")),
                    markdown_cell(row.get("pair_full_hit")),
                ]
            )
            + " |"
        )
    target_table = [
        "| Target | Variant | Full-hit profiles | Partial profiles | Best profile | Best hits |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("target_summaries")):
        target_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("target_id")),
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(", ".join(str(item) for item in row.get("full_hit_profiles") or [])),
                    markdown_cell(", ".join(str(item) for item in row.get("partial_hit_profiles") or [])),
                    markdown_cell(row.get("best_profile_id")),
                    markdown_cell(row.get("best_profile_hit_count")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Model Capability Required-Term Pair Decoding Sweep",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Sweep decision: `{summary.get('pair_decoding_sweep_decision')}`",
            f"- Source capacity decision: `{summary.get('source_pair_capacity_sweep_decision')}`",
            f"- Targets: `{summary.get('target_count')}`",
            f"- Profiles: `{summary.get('profile_count')}`",
            f"- Probe hits: `{summary.get('probe_hit_count')}`",
            f"- Full-hit profile targets: `{summary.get('profile_target_full_hit_count')}`",
            f"- Decoding full-hit observed: `{summary.get('decoding_full_hit_observed')}`",
            "",
            "## Profile Results",
            "",
            *profile_table,
            "",
            "## Target Summary",
            "",
            *target_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{as_dict(report.get('interpretation')).get('model_quality_claim')}`",
            f"- Reason: {as_dict(report.get('interpretation')).get('reason')}",
            f"- Next action: {as_dict(report.get('interpretation')).get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_decoding_sweep_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("pair_decoding_sweep_decision")),
        ("Targets", summary.get("target_count")),
        ("Profiles", summary.get("profile_count")),
        ("Probe hits", summary.get("probe_hit_count")),
        ("Full profile targets", summary.get("profile_target_full_hit_count")),
        ("Recovered", summary.get("decoding_full_hit_observed")),
        ("Best profile", summary.get("best_profile_id")),
    ]
    profile_rows = "\n".join(_profile_summary_html(row) for row in list_of_dicts(report.get("profile_target_summaries")))
    target_rows = "\n".join(_target_summary_html(row) for row in list_of_dicts(report.get("target_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair decoding sweep</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT required-term pair decoding sweep</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Experiment Boundary</h2><p>This report reuses existing v497 capacity checkpoints. It changes decoding length, temperature, and top-k only; it does not retrain the model.</p><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Profile Results</h2>
<div class="table-wrap"><table>
<thead><tr><th>Target</th><th>Profile</th><th>Hit terms</th><th>Missed terms</th><th>Rate</th><th>Full hit</th></tr></thead>
<tbody>{profile_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Target Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Target</th><th>Variant</th><th>Full-hit profiles</th><th>Partial profiles</th><th>Best profile</th><th>Best hits</th></tr></thead>
<tbody>{target_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_decoding_sweep_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_DECODING_SWEEP_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_decoding_sweep.csv",
        "text": root / REQUIRED_TERM_PAIR_DECODING_SWEEP_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_DECODING_SWEEP_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_DECODING_SWEEP_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_decoding_sweep_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_decoding_sweep_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_decoding_sweep_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_decoding_sweep_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _profile_summary_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('target_id'))}</td>"
        f"<td>{html_escape(row.get('profile_id'))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('hit_terms') or []))}</td>"
        f"<td>{html_escape(', '.join(str(term) for term in row.get('missed_terms') or []))}</td>"
        f"<td>{html_escape(row.get('hit_rate'))}</td>"
        f"<td>{html_escape(row.get('pair_full_hit'))}</td>"
        "</tr>"
    )


def _target_summary_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('target_id'))}</td>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('full_hit_profiles') or []))}</td>"
        f"<td>{html_escape(', '.join(str(item) for item in row.get('partial_hit_profiles') or []))}</td>"
        f"<td>{html_escape(row.get('best_profile_id'))}</td>"
        f"<td>{html_escape(row.get('best_profile_hit_count'))}</td>"
        "</tr>"
    )


def _csv_clean(value: Any) -> Any:
    cleaned = csv_cell(value)
    if isinstance(cleaned, str):
        return cleaned.rstrip()
    return cleaned


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f5f2; color: #1a211d; }
body { margin: 0; padding: 28px; }
main { max-width: 1220px; margin: 0 auto; }
header { border-bottom: 1px solid #dedbd2; padding-bottom: 16px; margin-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #605e55; line-height: 1.55; overflow-wrap: anywhere; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card, .panel { background: #fff; border: 1px solid #dedbd2; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(26, 33, 29, 0.05); }
.card span { display: block; color: #6f6c62; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.panel { margin-bottom: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 880px; }
th, td { text-align: left; border-bottom: 1px solid #e7e3da; padding: 10px; vertical-align: top; }
th { color: #5f5b52; font-size: 12px; text-transform: uppercase; }
td { overflow-wrap: anywhere; }
</style>"""
