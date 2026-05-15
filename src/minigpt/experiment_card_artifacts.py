from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    write_json_payload,
)


def write_experiment_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)


def render_experiment_card_markdown(card: dict[str, Any]) -> str:
    summary = _dict(card.get("summary"))
    notes = _dict(card.get("notes"))
    data = _dict(card.get("data"))
    training = _dict(card.get("training"))
    evaluation = _dict(card.get("evaluation"))
    registry = _dict(card.get("registry"))
    artifacts = [item for item in card.get("artifacts", []) if isinstance(item, dict)]
    recommendations = [str(item) for item in card.get("recommendations", [])]
    warnings = [str(item) for item in card.get("warnings", [])]

    rows = [
        ("Run", summary.get("run_name")),
        ("Status", summary.get("status")),
        ("Best val loss", _fmt(summary.get("best_val_loss"))),
        ("Loss rank", _rank_label(summary.get("best_val_loss_rank"))),
        ("Loss delta", _fmt_delta(summary.get("best_val_loss_delta"))),
        ("Dataset quality", summary.get("dataset_quality")),
        ("Eval suite cases", summary.get("eval_suite_cases")),
        ("Git", summary.get("git_commit")),
        ("Parameters", _fmt_int(summary.get("total_parameters"))),
    ]
    lines = [
        f"# {card.get('title', 'MiniGPT experiment card')}",
        "",
        f"- Generated: `{card.get('generated_at')}`",
        f"- Run dir: `{card.get('run_dir')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(rows),
        "",
        "## Notes",
        "",
        f"- Note: {notes.get('note') or 'missing'}",
        f"- Tags: {_fmt_tags(notes.get('tags')) or 'missing'}",
        "",
        "## Data",
        "",
        *_markdown_table(
            [
                ("Source kind", data.get("source_kind")),
                ("Sources", data.get("source_count")),
                ("Characters", _fmt_int(data.get("char_count"))),
                ("Fingerprint", data.get("short_fingerprint")),
                ("Warnings", data.get("warning_count")),
            ]
        ),
        "",
        "## Training",
        "",
        *_markdown_table(
            [
                ("Tokenizer", training.get("tokenizer")),
                ("Max iters", training.get("max_iters")),
                ("Device", training.get("device_used")),
                ("Start step", training.get("start_step")),
                ("End step", training.get("end_step")),
                ("Last val loss", _fmt(training.get("last_val_loss"))),
            ]
        ),
        "",
        "## Evaluation",
        "",
        *_markdown_table(
            [
                ("Eval loss", _fmt(evaluation.get("eval_loss"))),
                ("Perplexity", _fmt(evaluation.get("perplexity"))),
                ("Eval suite cases", evaluation.get("eval_suite_cases")),
                ("Average unique chars", _fmt(evaluation.get("avg_unique_chars"))),
                ("Registry best", evaluation.get("is_best_val_loss")),
            ]
        ),
        "",
        "## Registry",
        "",
        *_markdown_table(
            [
                ("Registry path", registry.get("registry_path")),
                ("Run count", registry.get("run_count")),
                ("Quality counts", _fmt_mapping(registry.get("quality_counts"))),
                ("Tag counts", _fmt_mapping(registry.get("tag_counts"))),
            ]
        ),
        "",
        "## Recommendations",
        "",
        *[f"- {item}" for item in recommendations],
        "",
        "## Artifacts",
        "",
        *_artifact_lines(artifacts),
    ]
    if warnings:
        lines.extend(["", "## Warnings", "", *[f"- {item}" for item in warnings]])
    return "\n".join(lines).rstrip() + "\n"


def write_experiment_card_markdown(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_experiment_card_markdown(card), encoding="utf-8")


def render_experiment_card_html(card: dict[str, Any], *, base_dir: str | Path | None = None) -> str:
    summary = _dict(card.get("summary"))
    notes = _dict(card.get("notes"))
    artifacts = [item for item in card.get("artifacts", []) if isinstance(item, dict)]
    stats = [
        ("Status", summary.get("status")),
        ("Best val", _fmt(summary.get("best_val_loss"))),
        ("Rank", _rank_label(summary.get("best_val_loss_rank"))),
        ("Delta", _fmt_delta(summary.get("best_val_loss_delta"))),
        ("Quality", summary.get("dataset_quality")),
        ("Eval cases", summary.get("eval_suite_cases")),
        ("Git", summary.get("git_commit")),
        ("Params", _fmt_int(summary.get("total_parameters"))),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(card.get('title', 'MiniGPT experiment card'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(card.get('title', 'MiniGPT experiment card'))}</h1><p>{_e(card.get('run_dir'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Notes</h2>'
            f"<p>{_e(notes.get('note') or 'missing')}</p><p>{_tag_chips(notes.get('tags'))}</p></section>",
            _key_value_section("Data", _dict(card.get("data"))),
            _key_value_section("Training", _dict(card.get("training"))),
            _key_value_section("Evaluation", _dict(card.get("evaluation"))),
            _key_value_section("Registry", _dict(card.get("registry"))),
            _recommendation_section(card.get("recommendations", [])),
            _artifact_section(artifacts, base_dir),
            _warning_section(card.get("warnings", [])),
            "<footer>Generated by MiniGPT experiment card exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_experiment_card_html(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_experiment_card_html(card, base_dir=out_path.parent), encoding="utf-8")


def write_experiment_card_outputs(card: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "experiment_card.json",
        "markdown": root / "experiment_card.md",
        "html": root / "experiment_card.html",
    }
    _mark_output_artifacts(card, paths)
    write_experiment_card_json(card, paths["json"])
    write_experiment_card_markdown(card, paths["markdown"])
    write_experiment_card_html(card, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _mark_output_artifacts(card: dict[str, Any], paths: dict[str, Path]) -> None:
    key_map = {
        "json": "experiment_card_json",
        "markdown": "experiment_card_md",
        "html": "experiment_card_html",
    }
    artifacts = card.get("artifacts")
    if not isinstance(artifacts, list):
        return
    for output_key, artifact_key in key_map.items():
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("key") == artifact_key:
                artifact["exists"] = True
                artifact["size_bytes"] = paths[output_key].stat().st_size if paths[output_key].exists() else None
                break


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {_md(value)} |")
    return lines


def _artifact_lines(artifacts: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in artifacts:
        state = "yes" if item.get("exists") else "no"
        size = _fmt_int(item.get("size_bytes")) if item.get("size_bytes") is not None else "missing"
        lines.append(f"- `{item.get('path')}`: {state}, {size} bytes")
    return lines


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = []
    for key, value in payload.items():
        rows.append(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>")
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{"".join(rows)}</table></section>'


def _recommendation_section(items: Any) -> str:
    values = [str(item) for item in items] or ["No recommendations."]
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _artifact_section(artifacts: list[dict[str, Any]], base_dir: str | Path | None) -> str:
    rows = []
    for item in artifacts:
        path = str(item.get("path") or "")
        href = _artifact_href(path, base_dir)
        label = f'<a href="{_e(href)}">{_e(path)}</a>' if item.get("exists") and href else _e(path)
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('key'))}</td>"
            f"<td>{label}</td>"
            f"<td>{_e('yes' if item.get('exists') else 'no')}</td>"
            f"<td>{_e(_fmt_int(item.get('size_bytes')) if item.get('size_bytes') is not None else 'missing')}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Artifacts</h2><table><thead><tr><th>Key</th><th>Path</th><th>Exists</th><th>Size</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _warning_section(items: Any) -> str:
    warnings = [str(item) for item in items]
    if not warnings:
        return ""
    return '<section class="panel warn"><h2>Warnings</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in warnings) + "</ul></section>"


def _artifact_href(relative: str, base_dir: str | Path | None) -> str | None:
    if base_dir is None:
        return relative
    return Path(os.path.relpath(Path(base_dir) / relative, Path(base_dir))).as_posix()


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e(_fmt_any(value))}</div>'
        "</div>"
    )


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --amber:#b45309; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
.warn { border-color:#f59e0b; }
table { width:100%; border-collapse:collapse; min-width:760px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; }
.tag { display:inline-block; margin:0 4px 4px 0; padding:2px 6px; border-radius:999px; background:#e0f2fe; color:#075985; font-size:12px; font-weight:700; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _tag_chips(value: Any) -> str:
    tags = _as_str_list(value)
    if not tags:
        return '<span class="muted">missing</span>'
    return "".join(f'<span class="tag">{_e(tag)}</span>' for tag in tags)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_delta(value: Any) -> str:
    number = _as_optional_float(value)
    if number is None:
        return "missing"
    return f"{number:+.5g}"


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _fmt_tags(value: Any) -> str:
    return ", ".join(_as_str_list(value))


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict):
        return "missing"
    return ", ".join(f"{key}:{val}" for key, val in value.items()) or "missing"


def _fmt_any(value: Any) -> str:
    if isinstance(value, dict):
        return _fmt_mapping(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "missing"
    return _fmt(value)


def _md(value: Any) -> str:
    text = _fmt_any(value)
    return text.replace("|", "\\|").replace("\n", " ")
