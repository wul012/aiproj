from __future__ import annotations

import json
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract_check_rows import (
    check_rows,
    json_text,
)
from minigpt.report_utils import html_escape


def check_family_text_rows(check: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        (
            "receipt_contract_summary_check_check_family_summary",
            json.dumps(check.get("check_family_summary"), ensure_ascii=False),
        ),
        (
            "receipt_contract_summary_check_failed_check_target_count",
            check.get("failed_check_target_count"),
        ),
        (
            "receipt_contract_summary_check_failed_check_targets",
            json.dumps(check.get("failed_check_targets"), ensure_ascii=False),
        ),
    ]


def check_family_markdown_lines(check: dict[str, Any]) -> list[str]:
    lines = [
        "",
        "## Check Family Summary",
        "",
        "| Family | Status | Checks | Failed | Required failed | Failed targets |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in check_rows(check.get("check_family_summary")):
        lines.append(
            f"| {row.get('family')} | {row.get('status')} | {row.get('check_count')} | "
            f"{row.get('failed_count')} | {row.get('required_failed_count')} | "
            f"{json_text(row.get('failed_targets'))} |"
        )
    lines.extend(
        [
            "",
            "## Failed Check Targets",
            "",
            "| Family | Type | Target | Required | Detail |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    failed_targets = check_rows(check.get("failed_check_targets"))
    if failed_targets:
        for row in failed_targets:
            lines.append(
                f"| {row.get('family')} | {row.get('check_type')} | {row.get('target')} | "
                f"{row.get('required')} | {row.get('detail')} |"
            )
    else:
        lines.append("| none | none | none | none | none |")
    return lines


def check_family_html_sections(check: dict[str, Any]) -> str:
    family_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('family'))}</td>"
        f"<td>{html_escape(row.get('status'))}</td>"
        f"<td>{html_escape(row.get('check_count'))}</td>"
        f"<td>{html_escape(row.get('failed_count'))}</td>"
        f"<td>{html_escape(row.get('required_failed_count'))}</td>"
        f"<td>{html_escape(json_text(row.get('failed_targets')))}</td>"
        "</tr>"
        for row in check_rows(check.get("check_family_summary"))
    )
    failed_rows = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('family'))}</td>"
        f"<td>{html_escape(row.get('check_type'))}</td>"
        f"<td>{html_escape(row.get('target'))}</td>"
        f"<td>{html_escape(row.get('required'))}</td>"
        f"<td>{html_escape(row.get('detail'))}</td>"
        "</tr>"
        for row in check_rows(check.get("failed_check_targets"))
    ) or "<tr><td>none</td><td>none</td><td>none</td><td>none</td><td>none</td></tr>"
    return f"""<section>
<h2>Check Family Summary</h2>
<table>
<thead>
<tr><th>Family</th><th>Status</th><th>Checks</th><th>Failed</th><th>Required failed</th><th>Failed targets</th></tr>
</thead>
<tbody>
{family_rows}
</tbody>
</table>
</section>
<section>
<h2>Failed Check Targets</h2>
<table>
<thead>
<tr><th>Family</th><th>Type</th><th>Target</th><th>Required</th><th>Detail</th></tr>
</thead>
<tbody>
{failed_rows}
</tbody>
</table>
</section>"""


__all__ = [
    "check_family_html_sections",
    "check_family_markdown_lines",
    "check_family_text_rows",
]
