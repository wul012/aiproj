from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_CSV_FILENAME,
    BOUNDED_OBJECTIVE_CONTRACT_HTML_FILENAME,
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
    BOUNDED_OBJECTIVE_CONTRACT_MARKDOWN_FILENAME,
    BOUNDED_OBJECTIVE_CONTRACT_TEXT_FILENAME,
)
from minigpt.report_utils import as_dict, csv_cell, html_escape, list_of_dicts, markdown_cell, write_json_payload


def render_bounded_objective_contract_text(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    interpretation = as_dict(report.get("interpretation"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("bounded_objective_contract_ready", summary.get("bounded_objective_contract_ready")),
        ("contract_id", summary.get("contract_id")),
        ("target_terms", ",".join(str(item) for item in summary.get("target_terms", []))),
        ("contract_case_count", summary.get("contract_case_count")),
        ("planned_seed_example_count", summary.get("planned_seed_example_count")),
        ("unchanged_suite_check_required", summary.get("unchanged_suite_check_required")),
        ("promotion_claim_allowed", summary.get("promotion_claim_allowed")),
        ("proposed_next_artifact", summary.get("proposed_next_artifact")),
        ("model_quality_claim", interpretation.get("model_quality_claim")),
        ("next_action", interpretation.get("next_action")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def write_bounded_objective_contract_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = ["case_id", "prompt", "expected_completion", "required_terms", "surface", "canonical", "exact_completion_required"]
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in list_of_dicts(report.get("contract_cases")):
            writer.writerow({field: csv_cell(_csv_value(row.get(field))) for field in fieldnames})


def render_bounded_objective_contract_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("objective_contract"))
    seed_blueprint = as_dict(report.get("seed_blueprint"))
    lines = [
        f"# {markdown_cell(report.get('title', 'MiniGPT bounded objective contract'))}",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Contract: `{summary.get('contract_id')}`",
        f"- Next artifact: `{summary.get('proposed_next_artifact')}`",
        "",
        "## Contract",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Target terms | {markdown_cell(','.join(str(item) for item in contract.get('target_terms', [])))} |",
        f"| Canonical prompt | {markdown_cell(contract.get('canonical_prompt'))} |",
        f"| Required completion | {markdown_cell(contract.get('required_exact_completion'))} |",
        f"| Unchanged suite required | {markdown_cell(contract.get('unchanged_suite_check_required'))} |",
        "",
        "## Contract Cases",
        "",
        "| Case | Prompt | Completion | Canonical |",
        "| --- | --- | --- | --- |",
    ]
    for row in list_of_dicts(report.get("contract_cases")):
        lines.append("| " + " | ".join([markdown_cell(row.get("case_id")), markdown_cell(row.get("prompt")), markdown_cell(row.get("expected_completion")), markdown_cell(row.get("canonical"))]) + " |")
    lines.extend(
        [
            "",
            "## Seed Blueprint",
            "",
            f"- Blueprint: `{markdown_cell(seed_blueprint.get('blueprint_id'))}`",
            f"- Planned examples: `{seed_blueprint.get('planned_example_count')}`",
            f"- Next artifact: `{markdown_cell(seed_blueprint.get('next_artifact'))}`",
            "",
            "## Holdout Rule",
            "",
            f"- `{markdown_cell(as_dict(report.get('holdout_rule')).get('holdout_id'))}`: {markdown_cell(as_dict(report.get('holdout_rule')).get('purpose'))}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_bounded_objective_contract_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    contract = as_dict(report.get("objective_contract"))
    seed_blueprint = as_dict(report.get("seed_blueprint"))
    holdout_rule = as_dict(report.get("holdout_rule"))
    interpretation = as_dict(report.get("interpretation"))
    stats = [
        ("Status", report.get("status")),
        ("Decision", report.get("decision")),
        ("Contract", summary.get("contract_id")),
        ("Cases", summary.get("contract_case_count")),
        ("Seed rows", summary.get("planned_seed_example_count")),
        ("Holdout", summary.get("unchanged_suite_check_required")),
        ("Claim", interpretation.get("model_quality_claim")),
        ("Next", summary.get("proposed_next_artifact")),
    ]
    case_rows = "".join(_case_row(row) for row in list_of_dicts(report.get("contract_cases")))
    blocked = "".join(f"<li>{html_escape(item)}</li>" for item in contract.get("blocked_surfaces", []))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>{html_escape(report.get('title', 'MiniGPT bounded objective contract'))}</title>
{_style()}
</head>
<body>
<main>
<header><h1>{html_escape(report.get('title', 'MiniGPT bounded objective contract'))}</h1><p>{html_escape(interpretation.get('reason'))}</p></header>
<section class="stats">{''.join(_card(label, value) for label, value in stats)}</section>
<section class="panel"><h2>Objective Contract</h2><div class="contract">
<div><span>Prompt</span><strong>{html_escape(contract.get('canonical_prompt'))}</strong></div>
<div><span>Completion</span><strong>{html_escape(contract.get('required_exact_completion'))}</strong></div>
<div><span>Target Terms</span><strong>{html_escape(','.join(str(item) for item in contract.get('target_terms', [])))}</strong></div>
</div></section>
<section class="panel"><h2>Contract Cases</h2><div class="table-wrap"><table>
<thead><tr><th>Case</th><th>Prompt</th><th>Completion</th><th>Canonical</th></tr></thead>
<tbody>{case_rows}</tbody>
</table></div></section>
<section class="columns"><div class="panel"><h2>Seed Blueprint</h2><p>{html_escape(seed_blueprint.get('blueprint_id'))}</p><strong>{html_escape(seed_blueprint.get('planned_example_count'))} planned rows</strong></div><div class="panel"><h2>Holdout Rule</h2><p>{html_escape(holdout_rule.get('purpose'))}</p></div><div class="panel"><h2>Blocked Surfaces</h2><ul>{blocked}</ul></div></section>
</main>
</body>
</html>
"""


def write_bounded_objective_contract_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
        "csv": root / BOUNDED_OBJECTIVE_CONTRACT_CSV_FILENAME,
        "text": root / BOUNDED_OBJECTIVE_CONTRACT_TEXT_FILENAME,
        "markdown": root / BOUNDED_OBJECTIVE_CONTRACT_MARKDOWN_FILENAME,
        "html": root / BOUNDED_OBJECTIVE_CONTRACT_HTML_FILENAME,
    }
    write_json_payload(report, paths["json"])
    write_bounded_objective_contract_csv(report, paths["csv"])
    paths["text"].write_text(render_bounded_objective_contract_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_bounded_objective_contract_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_bounded_objective_contract_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return value


def _case_row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{html_escape(row.get('case_id'))}</td>"
        f"<td>{html_escape(row.get('prompt'))}</td>"
        f"<td>{html_escape(row.get('expected_completion'))}</td>"
        f"<td>{html_escape(row.get('canonical'))}</td>"
        "</tr>"
    )


def _card(label: str, value: Any) -> str:
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17212b;--muted:#64717d;--line:#d8dee5;--panel:#f8fafc;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;background:#f1f3f7;color:var(--ink);font-family:Arial,"Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px}
h1{font-size:30px;margin:0 0 8px;letter-spacing:0}
h2{font-size:18px;margin:0 0 12px;letter-spacing:0}
p{color:var(--muted);line-height:1.55;overflow-wrap:anywhere}
.stats,.contract,.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:18px 0}
.card,.panel{background:white;border:1px solid var(--line);border-radius:8px}
.card,.contract div{padding:14px}
.card span,.contract span{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}
.card strong,.contract strong{display:block;margin-top:6px;font-size:18px;line-height:1.2;color:var(--accent);overflow-wrap:anywhere}
.panel{padding:16px;margin:14px 0}
.table-wrap{overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:#334155}
td,li{overflow-wrap:anywhere}
</style>"""


__all__ = [
    "render_bounded_objective_contract_html",
    "render_bounded_objective_contract_markdown",
    "render_bounded_objective_contract_text",
    "write_bounded_objective_contract_outputs",
]
