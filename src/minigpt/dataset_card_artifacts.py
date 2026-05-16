from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    write_json_payload,
)


def write_dataset_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)


def render_dataset_card_markdown(card: dict[str, Any]) -> str:
    dataset = _dict(card.get("dataset"))
    summary = _dict(card.get("summary"))
    provenance = _dict(card.get("provenance"))
    quality = _dict(card.get("quality"))
    lines = [
        f"# {card.get('title', 'MiniGPT dataset card')}",
        "",
        f"- Generated: `{card.get('generated_at')}`",
        f"- Dataset dir: `{card.get('dataset_dir')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Dataset", dataset.get("id")),
                ("Description", dataset.get("description")),
                ("Readiness", summary.get("readiness_status")),
                ("Quality", summary.get("quality_status")),
                ("Sources", summary.get("source_count")),
                ("Characters", summary.get("char_count")),
                ("Unique chars", summary.get("unique_char_count")),
                ("Fingerprint", summary.get("short_fingerprint")),
                ("Warnings", summary.get("warning_count")),
            ]
        ),
        "",
        "## Intended Use",
        "",
        *[f"- {item}" for item in _string_list(card.get("intended_use"))],
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in _string_list(card.get("limitations"))],
        "",
        "## Provenance",
        "",
        *_markdown_table(
            [
                ("Source roots", ", ".join(_string_list(provenance.get("source_roots")))),
                ("Recursive", provenance.get("recursive")),
                ("Output name", provenance.get("output_name")),
                ("Output text", provenance.get("output_text")),
            ]
        ),
        "",
        "| Source | Chars | Lines | SHA-256 |",
        "| --- | ---: | ---: | --- |",
    ]
    for source in _list_of_dicts(provenance.get("sources")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(source.get("path")),
                    _md(source.get("char_count")),
                    _md(source.get("line_count")),
                    _md(str(source.get("sha256") or "")[:12]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Quality",
            "",
            *_markdown_table(
                [
                    ("Status", quality.get("status")),
                    ("Warnings", quality.get("warning_count")),
                    ("Issues", quality.get("issue_count")),
                    ("Duplicate lines", quality.get("duplicate_line_count")),
                    ("Issue codes", ", ".join(_string_list(quality.get("issue_codes")))),
                ]
            ),
            "",
            "| Severity | Code | Message | Path |",
            "| --- | --- | --- | --- |",
        ]
    )
    for issue in _list_of_dicts(quality.get("issues")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(issue.get("severity")),
                    _md(issue.get("code")),
                    _md(issue.get("message")),
                    _md(issue.get("path")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "| Key | Exists | Path | Description |",
            "| --- | --- | --- | --- |",
        ]
    )
    for artifact in _list_of_dicts(card.get("artifacts")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(artifact.get("key")),
                    _md(artifact.get("exists")),
                    _md(artifact.get("path")),
                    _md(artifact.get("description")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(card.get("recommendations")))
    warnings = _string_list(card.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    return "\n".join(lines).rstrip() + "\n"


def write_dataset_card_markdown(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dataset_card_markdown(card), encoding="utf-8")


def render_dataset_card_html(card: dict[str, Any]) -> str:
    dataset = _dict(card.get("dataset"))
    summary = _dict(card.get("summary"))
    quality = _dict(card.get("quality"))
    stats = [
        ("Dataset", dataset.get("id")),
        ("Readiness", summary.get("readiness_status")),
        ("Quality", summary.get("quality_status")),
        ("Sources", summary.get("source_count")),
        ("Characters", summary.get("char_count")),
        ("Fingerprint", summary.get("short_fingerprint")),
        ("Warnings", summary.get("warning_count")),
        ("Generated", card.get("generated_at")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(card.get('title', 'MiniGPT dataset card'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(card.get('title', 'MiniGPT dataset card'))}</h1><p>{_e(dataset.get('description'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _list_section("Intended Use", card.get("intended_use")),
            _list_section("Limitations", card.get("limitations")),
            _key_value_section("Provenance", _dict(card.get("provenance"))),
            _quality_section_html(quality),
            _artifact_section_html(card.get("artifacts")),
            _list_section("Recommendations", card.get("recommendations")),
            _list_section("Warnings", card.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT dataset card exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_dataset_card_html(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dataset_card_html(card), encoding="utf-8")


def write_dataset_card_outputs(card: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "dataset_card.json",
        "markdown": root / "dataset_card.md",
        "html": root / "dataset_card.html",
    }
    _mark_output_artifacts(card, paths)
    write_dataset_card_json(card, paths["json"])
    write_dataset_card_markdown(card, paths["markdown"])
    write_dataset_card_html(card, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _mark_output_artifacts(card: dict[str, Any], paths: dict[str, Path]) -> None:
    key_map = {
        "json": "dataset_card_json",
        "markdown": "dataset_card_md",
        "html": "dataset_card_html",
    }
    artifacts = _list_of_dicts(card.get("artifacts"))
    for output_key, artifact_key in key_map.items():
        path = paths[output_key]
        found = False
        for artifact in artifacts:
            if artifact.get("key") == artifact_key:
                artifact["path"] = str(path)
                artifact["exists"] = True
                found = True
                break
        if not found:
            artifacts.append(
                {
                    "key": artifact_key,
                    "path": str(path),
                    "exists": True,
                    "description": f"{output_key} dataset card",
                }
            )
    card["artifacts"] = artifacts


def _key_value_section(title: str, mapping: dict[str, Any]) -> str:
    rows = []
    for key in sorted(mapping):
        value = mapping[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        rows.append(f"<tr><th>{_e(key)}</th><td>{_e(value)}</td></tr>")
    return f'<section class="panel"><h2>{_e(title)}</h2><table>' + "".join(rows) + "</table></section>"


def _quality_section_html(quality: dict[str, Any]) -> str:
    rows = []
    for issue in _list_of_dicts(quality.get("issues")):
        rows.append(
            "<tr>"
            f"<td>{_e(issue.get('severity'))}</td>"
            f"<td><strong>{_e(issue.get('code'))}</strong></td>"
            f"<td>{_e(issue.get('message'))}</td>"
            f"<td>{_e(issue.get('path'))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="4" class="muted">No quality issues recorded.</td></tr>')
    return (
        '<section class="panel"><h2>Quality Issues</h2>'
        '<table><thead><tr><th>Severity</th><th>Code</th><th>Message</th><th>Path</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _artifact_section_html(artifacts: Any) -> str:
    rows = []
    for item in _list_of_dicts(artifacts):
        status = "yes" if item.get("exists") else "no"
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('key'))}</td>"
            f"<td><span class=\"pill {status}\">{_e(status)}</span></td>"
            f"<td>{_e(item.get('path'))}</td>"
            f"<td>{_e(item.get('description'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Artifacts</h2>'
        '<table><thead><tr><th>Key</th><th>Exists</th><th>Path</th><th>Description</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _list_section(title: str, values: Any, *, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _md(value: Any) -> str:
    return ("missing" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e("missing" if value is None else value)}</div></div>'


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f7f7f2; --panel:#fff; --green:#047857; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:860px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:42px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.yes { background:var(--green); }
.pill.no { background:var(--red); }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


__all__ = [
    "render_dataset_card_html",
    "render_dataset_card_markdown",
    "write_dataset_card_html",
    "write_dataset_card_json",
    "write_dataset_card_markdown",
    "write_dataset_card_outputs",
]
