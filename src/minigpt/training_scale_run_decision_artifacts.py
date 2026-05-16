from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    write_csv_row,
    write_json_payload,
)


def write_training_scale_run_decision_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_scale_run_decision_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    selected = _dict(report.get("selected_run"))
    summary = _dict(report.get("summary"))
    fieldnames = [
        "decision_status",
        "recommended_action",
        "selected_run",
        "selected_gate_status",
        "selected_batch_status",
        "selected_readiness_score",
        "candidate_count",
        "rejected_count",
        "execute_command",
    ]
    write_csv_row(
        {
            "decision_status": report.get("decision_status"),
            "recommended_action": report.get("recommended_action"),
            "selected_run": selected.get("name"),
            "selected_gate_status": selected.get("gate_status"),
            "selected_batch_status": selected.get("batch_status"),
            "selected_readiness_score": selected.get("readiness_score"),
            "candidate_count": summary.get("candidate_count"),
            "rejected_count": summary.get("rejected_count"),
            "execute_command": report.get("execute_command_text"),
        },
        out_path,
        fieldnames,
    )


def render_training_scale_run_decision_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale run decision')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('decision_status')}`",
        f"- Action: `{report.get('recommended_action')}`",
        f"- Selected run: `{selected.get('name')}`",
        f"- Gate: `{selected.get('gate_status')}`",
        f"- Batch: `{selected.get('batch_status')}`",
        f"- Readiness: `{selected.get('readiness_score')}`",
        f"- Candidates: `{summary.get('candidate_count')}`",
        f"- Rejected: `{summary.get('rejected_count')}`",
        "",
        "## Execute command",
        "",
        "```powershell",
        str(report.get("execute_command_text") or ""),
        "```",
        "",
        "## Rejected runs",
        "",
        "| Run | Gate | Batch | Score | Reasons |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for run in _list_of_dicts(report.get("rejected_runs")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("gate_status")),
                    _md(run.get("batch_status")),
                    _md(run.get("readiness_score")),
                    _md("; ".join(_string_list(run.get("reasons")))),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_run_decision_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_decision_markdown(report), encoding="utf-8")


def render_training_scale_run_decision_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    selected = _dict(report.get("selected_run"))
    stats = [
        ("Status", report.get("decision_status")),
        ("Action", report.get("recommended_action")),
        ("Selected", selected.get("name")),
        ("Gate", selected.get("gate_status")),
        ("Batch", selected.get("batch_status")),
        ("Readiness", selected.get("readiness_score")),
        ("Candidates", summary.get("candidate_count")),
        ("Rejected", summary.get("rejected_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale run decision'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale run decision'))}</h1><p>{_e(report.get('comparison_path'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _command_section(report),
            _rejected_table(report),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT training scale run decision.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_run_decision_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_run_decision_html(report), encoding="utf-8")


def write_training_scale_run_decision_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_run_decision.json",
        "csv": root / "training_scale_run_decision.csv",
        "markdown": root / "training_scale_run_decision.md",
        "html": root / "training_scale_run_decision.html",
    }
    write_training_scale_run_decision_json(report, paths["json"])
    write_training_scale_run_decision_csv(report, paths["csv"])
    write_training_scale_run_decision_markdown(report, paths["markdown"])
    write_training_scale_run_decision_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _command_section(report: dict[str, Any]) -> str:
    text = str(report.get("execute_command_text") or "")
    if not text:
        text = "No execute command because no eligible run was selected."
    return f"<section><h2>Execute Command</h2><pre>{_e(text)}</pre></section>"


def _rejected_table(report: dict[str, Any]) -> str:
    rows = []
    for run in _list_of_dicts(report.get("rejected_runs")):
        rows.append(
            "<tr>"
            f"<td>{_e(run.get('name'))}</td>"
            f"<td>{_e(run.get('gate_status'))}</td>"
            f"<td>{_e(run.get('batch_status'))}</td>"
            f"<td>{_e(run.get('readiness_score'))}</td>"
            f"<td>{_e('; '.join(_string_list(run.get('reasons'))))}</td>"
            "</tr>"
        )
    if not rows:
        return "<section><h2>Rejected Runs</h2><p>No rejected runs.</p></section>"
    return (
        '<section><h2>Rejected Runs</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Run</th><th>Gate</th><th>Batch</th><th>Score</th><th>Reasons</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f7f8f3; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1160px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


__all__ = [
    "render_training_scale_run_decision_html",
    "render_training_scale_run_decision_markdown",
    "write_training_scale_run_decision_csv",
    "write_training_scale_run_decision_html",
    "write_training_scale_run_decision_json",
    "write_training_scale_run_decision_markdown",
    "write_training_scale_run_decision_outputs",
]
