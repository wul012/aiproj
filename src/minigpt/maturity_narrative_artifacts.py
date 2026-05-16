from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_maturity_narrative_json(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(narrative, ensure_ascii=False, indent=2), encoding="utf-8")


def render_maturity_narrative_markdown(narrative: dict[str, Any]) -> str:
    summary = _dict(narrative.get("summary"))
    lines = [
        f"# {narrative.get('title', 'MiniGPT release-quality maturity narrative')}",
        "",
        f"- Generated: `{narrative.get('generated_at')}`",
        f"- Project root: `{narrative.get('project_root')}`",
        "",
        "## Portfolio Summary",
        "",
        *_markdown_table(
            [
                ("Portfolio status", summary.get("portfolio_status")),
                ("Current version", summary.get("current_version")),
                ("Maturity status", summary.get("maturity_status")),
                ("Release readiness trend", summary.get("release_readiness_trend_status")),
                ("Request history status", summary.get("request_history_status")),
                ("Benchmark scorecards", summary.get("benchmark_scorecard_count")),
                ("Benchmark average", summary.get("benchmark_avg_score")),
                ("Benchmark decisions", summary.get("benchmark_decision_count")),
                ("Scorecard decision run", summary.get("benchmark_decision_selected_run")),
                ("Scorecard decision flag delta", summary.get("benchmark_decision_selected_flag_delta")),
                ("Dataset cards", summary.get("dataset_card_count")),
                ("Dataset warnings", summary.get("dataset_warning_count")),
            ]
        ),
        "",
        "## Narrative",
        "",
    ]
    for section in _list_of_dicts(narrative.get("sections")):
        lines.extend(
            [
                f"### {section.get('title')}",
                "",
                f"- Status: `{section.get('status')}`",
                f"- Claim: {section.get('claim')}",
                f"- Evidence: {section.get('evidence')}",
                f"- Boundary: {section.get('boundary')}",
                f"- Next step: {section.get('next_step')}",
                "",
            ]
        )
    lines.extend(["## Evidence Matrix", "", "| Area | Status | Evidence | Signal | Note |", "| --- | --- | --- | --- | --- |"])
    for item in _list_of_dicts(narrative.get("evidence_matrix")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(item.get("area")),
                    _md(item.get("status")),
                    _md(item.get("path")),
                    _md(item.get("signal")),
                    _md(item.get("note")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(narrative.get("recommendations")))
    warnings = _string_list(narrative.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_maturity_narrative_markdown(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_narrative_markdown(narrative), encoding="utf-8")


def render_maturity_narrative_html(narrative: dict[str, Any]) -> str:
    summary = _dict(narrative.get("summary"))
    stats = [
        ("Portfolio", summary.get("portfolio_status")),
        ("Version", summary.get("current_version")),
        ("Maturity", summary.get("maturity_status")),
        ("Release trend", summary.get("release_readiness_trend_status")),
        ("Requests", summary.get("request_history_status")),
        ("Benchmarks", summary.get("benchmark_scorecard_count")),
        ("Benchmark avg", summary.get("benchmark_avg_score")),
        ("Decisions", summary.get("benchmark_decision_count")),
        ("Decision run", summary.get("benchmark_decision_selected_run")),
        ("Dataset cards", summary.get("dataset_card_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(narrative.get('title', 'MiniGPT release-quality maturity narrative'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(narrative.get('title', 'MiniGPT release-quality maturity narrative'))}</h1><p>{_e(narrative.get('project_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _section_cards(_list_of_dicts(narrative.get("sections"))),
            _evidence_table(_list_of_dicts(narrative.get("evidence_matrix"))),
            _list_section("Recommendations", narrative.get("recommendations")),
            _list_section("Warnings", narrative.get("warnings")),
            "<footer>Generated by MiniGPT maturity narrative exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maturity_narrative_html(narrative: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_narrative_html(narrative), encoding="utf-8")


def write_maturity_narrative_outputs(narrative: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maturity_narrative.json",
        "markdown": root / "maturity_narrative.md",
        "html": root / "maturity_narrative.html",
    }
    write_maturity_narrative_json(narrative, paths["json"])
    write_maturity_narrative_markdown(narrative, paths["markdown"])
    write_maturity_narrative_html(narrative, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _section_cards(sections: list[dict[str, Any]]) -> str:
    cards = []
    for section in sections:
        cards.append(
            '<article class="panel narrative">'
            f"<h2>{_e(section.get('title'))}</h2>"
            f'<span class="pill {_e(section.get("status"))}">{_e(section.get("status"))}</span>'
            f"<p><strong>Claim.</strong> {_e(section.get('claim'))}</p>"
            f"<p><strong>Evidence.</strong> {_e(section.get('evidence'))}</p>"
            f"<p><strong>Boundary.</strong> {_e(section.get('boundary'))}</p>"
            f"<p><strong>Next.</strong> {_e(section.get('next_step'))}</p>"
            "</article>"
        )
    return "".join(cards)


def _evidence_table(rows: list[dict[str, Any]]) -> str:
    body = "".join(
        "<tr>"
        f"<td>{_e(row.get('area'))}</td>"
        f"<td>{_e(row.get('status'))}</td>"
        f"<td>{_e(row.get('signal'))}</td>"
        f"<td>{_e(row.get('path'))}<br><span>exists={_e(row.get('exists'))}</span></td>"
        f"<td>{_e(row.get('note'))}</td>"
        "</tr>"
        for row in rows
    )
    return (
        '<section class="panel"><h2>Evidence Matrix</h2>'
        '<table><thead><tr><th>Area</th><th>Status</th><th>Signal</th><th>Path</th><th>Note</th></tr></thead><tbody>'
        + body
        + "</tbody></table></section>"
    )


def _list_section(title: str, values: Any) -> str:
    items = _string_list(values)
    if not items:
        return ""
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _style() -> str:
    return """<style>
:root { --ink:#151f2c; --muted:#566170; --line:#d8dee9; --page:#f7f8f3; --panel:#fff; --green:#047857; --amber:#b45309; --red:#b91c1c; --blue:#1f5f74; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.46; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
.narrative p { max-width:980px; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:62px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; background:var(--blue); }
.pill.ready, .pill.pass, .pill.improved, .pill.stable { background:var(--green); }
.pill.review, .pill.warn, .pill.panel-changed, .pill.incomplete { background:var(--amber); }
.pill.fail, .pill.regressed { background:var(--red); }
.pill.missing { background:#6b7280; }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
