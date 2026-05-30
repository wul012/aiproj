from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_forced_choice_diagnostic import (
    REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME,
    REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
    REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME,
    REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_model_capability_required_term_pair_forced_choice_diagnostic_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("forced_choice_diagnostic_decision", summary.get("forced_choice_diagnostic_decision")),
        ("source_branch_retention_sweep_decision", summary.get("source_branch_retention_sweep_decision")),
        ("target_count", summary.get("target_count")),
        ("run_count", summary.get("run_count")),
        ("score_row_count", summary.get("score_row_count")),
        ("prompt_summary_count", summary.get("prompt_summary_count")),
        ("expected_best_count", summary.get("expected_best_count")),
        ("expected_best_rate", summary.get("expected_best_rate")),
        ("forced_choice_full_match_variant_count", summary.get("forced_choice_full_match_variant_count")),
        ("collapse_candidate_counts", summary.get("collapse_candidate_counts")),
        ("best_variant_id", summary.get("best_variant_id")),
        ("best_variant_expected_best_count", summary.get("best_variant_expected_best_count")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_model_capability_required_term_pair_forced_choice_diagnostic_csv(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    fieldnames = [
        "run_id",
        "variant_id",
        "prompt_term",
        "candidate_term",
        "is_expected_candidate",
        "avg_nll",
        "total_nll",
        "first_token_rank",
        "first_token_logprob",
        "token_count",
        "status",
    ]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("score_rows")):
            writer.writerow({field: _csv_clean(row.get(field)) for field in fieldnames})


def render_model_capability_required_term_pair_forced_choice_diagnostic_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    prompt_table = [
        "| Variant | Prompt term | Expected | Best candidate | Expected best | Margin |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in list_of_dicts(report.get("prompt_summaries")):
        prompt_table.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(row.get("variant_id")),
                    markdown_cell(row.get("prompt_term")),
                    markdown_cell(row.get("expected_term")),
                    markdown_cell(row.get("best_candidate_term")),
                    markdown_cell(row.get("expected_is_best")),
                    markdown_cell(row.get("expected_margin_vs_best")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Required-Term Pair Forced-Choice Diagnostic",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Diagnostic decision: `{summary.get('forced_choice_diagnostic_decision')}`",
            f"- Source sweep: `{summary.get('source_branch_retention_sweep_decision')}`",
            f"- Runs: `{summary.get('run_count')}`",
            f"- Expected-best count: `{summary.get('expected_best_count')}`",
            f"- Full-match variants: `{summary.get('forced_choice_full_match_variant_count')}`",
            "",
            "## Prompt Choices",
            "",
            *prompt_table,
            "",
            "## Boundary",
            "",
            f"- Model quality claim: `{interpretation.get('model_quality_claim')}`",
            f"- Reason: {interpretation.get('reason')}",
            f"- Next action: {interpretation.get('next_action')}",
            "",
        ]
    )


def render_model_capability_required_term_pair_forced_choice_diagnostic_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", summary.get("forced_choice_diagnostic_decision")),
        ("Runs", summary.get("run_count")),
        ("Scores", summary.get("score_row_count")),
        ("Expected best", summary.get("expected_best_count")),
        ("Full variants", summary.get("forced_choice_full_match_variant_count")),
        ("Best variant", summary.get("best_variant_id")),
    ]
    prompt_rows = "\n".join(_prompt_row_html(row) for row in list_of_dicts(report.get("prompt_summaries")))
    variant_rows = "\n".join(_variant_row_html(row) for row in list_of_dicts(report.get("variant_summaries")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT pair forced-choice diagnostic</title>
{_style()}
</head>
<body>
<main>
<header><h1>MiniGPT pair forced-choice diagnostic</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Next Action</h2><p>{html_escape(interpretation.get('next_action'))}</p></section>
<section class="panel">
<h2>Prompt Choices</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Prompt</th><th>Expected</th><th>Best</th><th>Expected best</th><th>Margin</th></tr></thead>
<tbody>{prompt_rows}</tbody>
</table></div>
</section>
<section class="panel">
<h2>Variant Summary</h2>
<div class="table-wrap"><table>
<thead><tr><th>Variant</th><th>Expected best</th><th>Prompt count</th><th>Full match</th><th>Collapse</th></tr></thead>
<tbody>{variant_rows}</tbody>
</table></div>
</section>
</main>
</body>
</html>
"""


def write_model_capability_required_term_pair_forced_choice_diagnostic_outputs(
    report: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME,
        "csv": root / "model_capability_required_term_pair_forced_choice_diagnostic.csv",
        "text": root / REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME,
        "markdown": root / REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME,
        "html": root / REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_model_capability_required_term_pair_forced_choice_diagnostic_csv(report, paths["csv"])
    paths["text"].write_text(render_model_capability_required_term_pair_forced_choice_diagnostic_text(report), encoding="utf-8")
    paths["markdown"].write_text(
        render_model_capability_required_term_pair_forced_choice_diagnostic_markdown(report),
        encoding="utf-8",
    )
    paths["html"].write_text(render_model_capability_required_term_pair_forced_choice_diagnostic_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _prompt_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('prompt_term'))}</td>"
        f"<td>{html_escape(row.get('expected_term'))}</td>"
        f"<td>{html_escape(row.get('best_candidate_term'))}</td>"
        f"<td>{html_escape(row.get('expected_is_best'))}</td>"
        f"<td>{html_escape(row.get('expected_margin_vs_best'))}</td>"
        "</tr>"
    )


def _variant_row_html(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('variant_id'))}</td>"
        f"<td>{html_escape(row.get('expected_best_count'))}</td>"
        f"<td>{html_escape(row.get('prompt_count'))}</td>"
        f"<td>{html_escape(row.get('forced_choice_full_match'))}</td>"
        f"<td>{html_escape(row.get('collapse_candidate'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#172026;--muted:#5d6975;--line:#d8dee4;--panel:#f7f9fb;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#eef2f5;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:18px;margin:0 0 12px}
p{color:var(--muted);line-height:1.55}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card{padding:14px}
.card span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
</style>"""


def _csv_clean(value: Any) -> Any:
    cell = csv_cell(value)
    return cell.rstrip() if isinstance(cell, str) else cell
