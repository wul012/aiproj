from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    csv_cell,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_json_payload,
)


def write_governance_stabilization_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_governance_stabilization_csv(report: dict[str, Any], path: str | Path) -> None:
    fieldnames = [
        "id",
        "name",
        "action",
        "necessary",
        "has_consumer",
        "has_evidence",
        "consumer",
        "evidence",
        "review_reason",
        "expansion_rule",
        "next_action",
    ]
    rows = []
    for item in _list_of_dicts(report.get("chains")):
        rows.append({field: csv_cell(item.get(field)) for field in fieldnames})
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_governance_stabilization_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    policy = _dict(report.get("policy"))
    routing = _dict(report.get("proposal_routing"))
    routing_requirement = _dict(report.get("routing_requirement"))
    keyword_hits = _string_list(routing.get("keyword_hits"))
    ambiguous_keyword_hits = _string_list(routing.get("ambiguous_keyword_hits"))
    lines = [
        f"# {report.get('title', 'MiniGPT governance stabilization review')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        f"- New chain pause: `{policy.get('new_chain_pause')}` for `{policy.get('pause_days')}` days",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "chain_count",
        "keep_count",
        "watch_count",
        "merge_count",
        "cut_count",
        "missing_consumer_count",
        "missing_evidence_count",
        "missing_review_reason_count",
        "missing_expansion_rule_count",
        "consolidation_candidate_count",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(
        [
            "",
            "## Governance Chains",
            "",
            "| Chain | Action | Consumer | Evidence | Review reason | Expansion rule | Next action |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in _list_of_dicts(report.get("chains")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("name")),
                    _md(item.get("action")),
                    _md(item.get("consumer")),
                    _md(item.get("evidence")),
                    _md(item.get("review_reason")),
                    _md(item.get("expansion_rule")),
                    _md(item.get("next_action")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Proposal Routing",
            "",
            f"- Decision: `{routing.get('decision')}`",
            f"- Items: `{routing.get('item_count')}`",
            f"- Merge existing: `{routing.get('merge_existing_count')}`",
            f"- Review: `{routing.get('review_count')}`",
            f"- New-chain candidates: `{routing.get('new_chain_candidate_count')}`",
            f"- Exact matches: `{routing.get('exact_match_count')}`",
            f"- Keyword matches: `{routing.get('keyword_match_count')}`",
            f"- Ambiguous keyword matches: `{routing.get('ambiguous_keyword_match_count')}`",
            f"- Keyword hits: `{', '.join(keyword_hits)}`" if keyword_hits else "- Keyword hits: ``",
            f"- Ambiguous keyword hits: `{', '.join(ambiguous_keyword_hits)}`" if ambiguous_keyword_hits else "- Ambiguous keyword hits: ``",
            f"- Requirement status: `{routing_requirement.get('status', 'not-required')}`",
            f"- Requirement decision: `{routing_requirement.get('decision', 'report-only')}`",
            f"- Requirement exit code: `{routing_requirement.get('exit_code', 0)}`",
            f"- Requirement failed reasons: `{', '.join(_string_list(routing_requirement.get('failed_reasons')))}`",
            "",
            "| Proposal | Target chain | Suggested chain | Match basis | Matched keyword | Matched keywords | Matched chains | Decision | Reason | Expansion rule |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    rows = _list_of_dicts(routing.get("items"))
    if rows:
        for item in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md(item.get("title")),
                        _md(item.get("target_chain")),
                        _md(item.get("suggested_chain")),
                        _md(item.get("match_basis")),
                        _md(item.get("matched_keyword")),
                        _md(", ".join(_string_list(item.get("matched_keywords")))),
                        _md(", ".join(_string_list(item.get("matched_chains")))),
                        _md(item.get("route_decision")),
                        _md(item.get("reason")),
                        _md(item.get("expansion_rule")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("|  |  |  |  |  |  |  | not_applicable | No governance expansion proposals were provided. |  |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_governance_stabilization_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_governance_stabilization_markdown(report), encoding="utf-8")


def render_governance_stabilization_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    policy = _dict(report.get("policy"))
    routing = _dict(report.get("proposal_routing"))
    routing_requirement = _dict(report.get("routing_requirement"))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Pause days", policy.get("pause_days")),
        ("Chains", summary.get("chain_count")),
        ("Keep", summary.get("keep_count")),
        ("Watch", summary.get("watch_count")),
        ("Merge/Cut", summary.get("consolidation_candidate_count")),
        ("Missing rules", summary.get("missing_expansion_rule_count")),
        ("Routing", routing.get("decision")),
        ("Exact match", routing.get("exact_match_count")),
        ("Keyword match", routing.get("keyword_match_count")),
        ("Ambiguous keyword", routing.get("ambiguous_keyword_match_count")),
        ("Routing requirement", routing_requirement.get("status", "not-required")),
        ("Routing exit", routing_requirement.get("exit_code", 0)),
    ]
    rows = "".join(_governance_chain_html_row(item) for item in _list_of_dicts(report.get("chains")))
    if not rows:
        rows = '<tr><td colspan="7" class="muted">No governance chains were provided.</td></tr>'
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT governance stabilization review'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT governance stabilization review'))}</h1><p>Stabilize existing governance chains before adding new report layers.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            "<section><h2>Governance Chains</h2><table><tr><th>Chain</th><th>Action</th><th>Consumer</th><th>Evidence</th><th>Review Reason</th><th>Expansion Rule</th><th>Next Action</th></tr>"
            + rows
            + "</table></section>",
            _proposal_routing_section(routing),
            _routing_requirement_section(routing_requirement),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT maintenance policy.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_governance_stabilization_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_governance_stabilization_html(report), encoding="utf-8")


def write_governance_stabilization_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "governance_stabilization.json",
        "csv": root / "governance_stabilization.csv",
        "markdown": root / "governance_stabilization.md",
        "html": root / "governance_stabilization.html",
    }
    write_governance_stabilization_json(report, paths["json"])
    write_governance_stabilization_csv(report, paths["csv"])
    write_governance_stabilization_markdown(report, paths["markdown"])
    write_governance_stabilization_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _governance_chain_html_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td><strong>{_e(item.get('name'))}</strong><br><span class=\"muted\">{_e(item.get('id'))}</span></td>"
        f"<td>{_e(item.get('action'))}</td>"
        f"<td>{_e(item.get('consumer'))}</td>"
        f"<td>{_e(item.get('evidence'))}</td>"
        f"<td>{_e(item.get('review_reason'))}</td>"
        f"<td>{_e(item.get('expansion_rule'))}</td>"
        f"<td>{_e(item.get('next_action'))}</td>"
        "</tr>"
    )


def _proposal_routing_section(routing: dict[str, Any]) -> str:
    rows = "".join(_proposal_routing_html_row(item) for item in _list_of_dicts(routing.get("items")))
    if not rows:
        rows = '<tr><td colspan="10" class="muted">No governance expansion proposals were provided.</td></tr>'
    summary = (
        f"<p><strong>{_e(routing.get('decision'))}</strong> "
        f"items={_e(routing.get('item_count'))}, merge={_e(routing.get('merge_existing_count'))}, "
        f"review={_e(routing.get('review_count'))}, new-chain={_e(routing.get('new_chain_candidate_count'))}, "
        f"keywords={_e(routing.get('keyword_match_count'))}, ambiguous={_e(routing.get('ambiguous_keyword_match_count'))}, "
        f"ambiguous-hits={_e(', '.join(_string_list(routing.get('ambiguous_keyword_hits'))))}</p>"
    )
    return (
        "<section><h2>Proposal Routing</h2>"
        + summary
        + "<table><tr><th>Proposal</th><th>Target Chain</th><th>Suggested Chain</th><th>Match Basis</th><th>Matched Keyword</th><th>Matched Keywords</th><th>Matched Chains</th><th>Decision</th><th>Reason</th><th>Expansion Rule</th></tr>"
        + rows
        + "</table></section>"
    )


def _proposal_routing_html_row(item: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{_e(item.get('title'))}</td>"
        f"<td>{_e(item.get('target_chain'))}</td>"
        f"<td>{_e(item.get('suggested_chain'))}</td>"
        f"<td>{_e(item.get('match_basis'))}</td>"
        f"<td>{_e(item.get('matched_keyword'))}</td>"
        f"<td>{_e(', '.join(_string_list(item.get('matched_keywords'))))}</td>"
        f"<td>{_e(', '.join(_string_list(item.get('matched_chains'))))}</td>"
        f"<td>{_e(item.get('route_decision'))}</td>"
        f"<td>{_e(item.get('reason'))}</td>"
        f"<td>{_e(item.get('expansion_rule'))}</td>"
        "</tr>"
    )


def _routing_requirement_section(requirement: dict[str, Any]) -> str:
    if not requirement:
        requirement = {
            "required": False,
            "status": "not-required",
            "decision": "report-only",
            "exit_code": 0,
            "blocking_count": 0,
            "failed_reasons": [],
        }
    rows = [
        ("Required", requirement.get("required")),
        ("Status", requirement.get("status")),
        ("Decision", requirement.get("decision")),
        ("Exit code", requirement.get("exit_code")),
        ("Blocking count", requirement.get("blocking_count")),
        ("Failed reasons", ", ".join(_string_list(requirement.get("failed_reasons")))),
    ]
    return (
        "<section><h2>Routing Requirement</h2><table>"
        + "".join(f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows)
        + "</table></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return f"<section><h2>{_e(title)}</h2><p class=\"muted\">None.</p></section>"
    return f"<section><h2>{_e(title)}</h2><ul>" + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1040px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #1f7a5c; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; }
th { background: #eef3f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.muted { color: #687782; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()


__all__ = [
    "render_governance_stabilization_html",
    "render_governance_stabilization_markdown",
    "write_governance_stabilization_csv",
    "write_governance_stabilization_html",
    "write_governance_stabilization_json",
    "write_governance_stabilization_markdown",
    "write_governance_stabilization_outputs",
]
