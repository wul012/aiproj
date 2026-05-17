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


def write_training_run_evidence_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_training_run_evidence_csv(report: dict[str, Any], path: str | Path) -> None:
    summary = _dict(report.get("summary"))
    training = _dict(report.get("training"))
    evaluation = _dict(report.get("evaluation"))
    fieldnames = [
        "status",
        "readiness_score",
        "critical_missing_count",
        "warning_count",
        "available_artifact_count",
        "artifact_count",
        "checkpoint_exists",
        "run_manifest_exists",
        "tokenizer",
        "target_step",
        "actual_last_step",
        "best_val_loss",
        "last_val_loss",
        "sample_exists",
        "eval_suite_exists",
        "eval_suite_case_count",
        "avg_continuation_chars",
        "avg_unique_chars",
        "eval_task_type_count",
        "eval_difficulty_count",
    ]
    write_csv_row(
        {
            "status": summary.get("status"),
            "readiness_score": summary.get("readiness_score"),
            "critical_missing_count": summary.get("critical_missing_count"),
            "warning_count": summary.get("warning_count"),
            "available_artifact_count": summary.get("available_artifact_count"),
            "artifact_count": summary.get("artifact_count"),
            "checkpoint_exists": summary.get("checkpoint_exists"),
            "run_manifest_exists": summary.get("run_manifest_exists"),
            "tokenizer": training.get("tokenizer"),
            "target_step": training.get("target_step"),
            "actual_last_step": training.get("actual_last_step"),
            "best_val_loss": training.get("best_val_loss"),
            "last_val_loss": training.get("last_val_loss"),
            "sample_exists": summary.get("sample_exists"),
            "eval_suite_exists": summary.get("eval_suite_exists"),
            "eval_suite_case_count": summary.get("eval_suite_case_count"),
            "avg_continuation_chars": evaluation.get("avg_continuation_chars"),
            "avg_unique_chars": evaluation.get("avg_unique_chars"),
            "eval_task_type_count": evaluation.get("task_type_count"),
            "eval_difficulty_count": evaluation.get("difficulty_count"),
        },
        path,
        fieldnames,
    )


def render_training_run_evidence_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    training = _dict(report.get("training"))
    data = _dict(report.get("data"))
    evaluation = _dict(report.get("evaluation"))
    sample = _dict(report.get("sample"))
    lines = [
        f"# {report.get('title', 'MiniGPT training run evidence')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Run dir: `{report.get('run_dir')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Readiness score: `{summary.get('readiness_score')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Status", summary.get("status")),
                ("Readiness score", summary.get("readiness_score")),
                ("Core artifacts", f"{summary.get('core_available_count')}/{summary.get('core_artifact_count')}"),
                ("All artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
                ("Critical missing", summary.get("critical_missing_count")),
                ("Warnings", summary.get("warning_count")),
                ("Eval cases", summary.get("eval_suite_case_count")),
            ]
        ),
        "",
        "## Training",
        "",
        *_markdown_table(
            [
                ("Tokenizer", training.get("tokenizer")),
                ("Device", training.get("device_used")),
                ("Target step", training.get("target_step")),
                ("Actual last step", training.get("actual_last_step")),
                ("Best val loss", _fmt(training.get("best_val_loss"))),
                ("Last val loss", _fmt(training.get("last_val_loss"))),
                ("Parameters", _fmt_int(training.get("parameter_count"))),
            ]
        ),
        "",
        "## Data",
        "",
        *_markdown_table(
            [
                ("Source kind", data.get("source_kind")),
                ("Source path", data.get("source_path")),
                ("Token count", _fmt_int(data.get("token_count"))),
                ("Train tokens", _fmt_int(data.get("train_token_count"))),
                ("Val tokens", _fmt_int(data.get("val_token_count"))),
                ("Dataset quality", data.get("dataset_quality_status")),
                ("Dataset fingerprint", data.get("dataset_fingerprint")),
            ]
        ),
        "",
        "## Evaluation",
        "",
        *_markdown_table(
            [
                ("Exists", evaluation.get("exists")),
                ("Suite", evaluation.get("suite_name")),
                ("Version", evaluation.get("suite_version")),
                ("Language", evaluation.get("language")),
                ("Cases", evaluation.get("case_count")),
                ("Results", evaluation.get("result_count")),
                ("Avg continuation chars", _fmt(evaluation.get("avg_continuation_chars"))),
                ("Avg unique chars", _fmt(evaluation.get("avg_unique_chars"))),
                ("Task types", evaluation.get("task_types")),
                ("Difficulties", evaluation.get("difficulties")),
            ]
        ),
        "",
        "## Sample",
        "",
        *_markdown_table(
            [
                ("Exists", sample.get("exists")),
                ("Prompt", sample.get("prompt")),
                ("Characters", sample.get("char_count")),
            ]
        ),
        "",
        "## Checks",
        "",
        "| Status | Code | Message | Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for check in _list_of_dicts(report.get("checks")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(check.get("status")),
                    _md(check.get("code")),
                    _md(check.get("message")),
                    _md(check.get("recommendation")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Artifacts", "", "| Key | Required | Exists | Size | Path |", "| --- | --- | --- | --- | --- |"])
    for artifact in _list_of_dicts(report.get("artifacts")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(artifact.get("key")),
                    _md(artifact.get("required_level")),
                    _md(artifact.get("exists")),
                    _md(_fmt_int(artifact.get("size_bytes")) if artifact.get("size_bytes") is not None else "missing"),
                    _md(artifact.get("path")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_training_run_evidence_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_run_evidence_markdown(report), encoding="utf-8")


def render_training_run_evidence_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    training = _dict(report.get("training"))
    evaluation = _dict(report.get("evaluation"))
    stats = [
        ("Status", summary.get("status")),
        ("Score", summary.get("readiness_score")),
        ("Core", f"{summary.get('core_available_count')}/{summary.get('core_artifact_count')}"),
        ("Artifacts", f"{summary.get('available_artifact_count')}/{summary.get('artifact_count')}"),
        ("Step", f"{training.get('actual_last_step')}/{training.get('target_step')}"),
        ("Best val", _fmt(training.get("best_val_loss"))),
        ("Eval cases", evaluation.get("case_count")),
        ("Task types", evaluation.get("task_type_count")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training run evidence'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training run evidence'))}</h1><p>{_e(report.get('run_dir'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _key_value_section("Training", _dict(report.get("training"))),
            _key_value_section("Data", _dict(report.get("data"))),
            _key_value_section("Evaluation", _dict(report.get("evaluation"))),
            _key_value_section("Sample", _dict(report.get("sample"))),
            _checks_section(_list_of_dicts(report.get("checks"))),
            _artifacts_section(_list_of_dicts(report.get("artifacts"))),
            _list_section("Recommendations", report.get("recommendations")),
            _list_section("Warnings", report.get("warnings"), css_class="warn"),
            "<footer>Generated by MiniGPT training run evidence.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_run_evidence_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_run_evidence_html(report), encoding="utf-8")


def write_training_run_evidence_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_run_evidence.json",
        "csv": root / "training_run_evidence.csv",
        "markdown": root / "training_run_evidence.md",
        "html": root / "training_run_evidence.html",
    }
    write_training_run_evidence_json(report, paths["json"])
    write_training_run_evidence_csv(report, paths["csv"])
    write_training_run_evidence_markdown(report, paths["markdown"])
    write_training_run_evidence_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    output = ["| Field | Value |", "| --- | --- |"]
    for label, value in rows:
        output.append(f"| {_md(label)} | {_md(value)} |")
    return output


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>"
        for key, value in payload.items()
    )
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _checks_section(checks: list[dict[str, Any]]) -> str:
    rows = "".join(
        f'<tr class="{_e(check.get("status"))}">'
        f"<td>{_e(check.get('status'))}</td>"
        f"<td>{_e(check.get('code'))}</td>"
        f"<td>{_e(check.get('message'))}</td>"
        f"<td>{_e(check.get('recommendation'))}</td>"
        "</tr>"
        for check in checks
    )
    return (
        '<section class="panel"><h2>Checks</h2><table>'
        "<thead><tr><th>Status</th><th>Code</th><th>Message</th><th>Recommendation</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>"
    )


def _artifacts_section(artifacts: list[dict[str, Any]]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{_e(item.get('key'))}</td>"
        f"<td>{_e(item.get('required_level'))}</td>"
        f"<td>{_e(item.get('exists'))}</td>"
        f"<td>{_e(_fmt_int(item.get('size_bytes')) if item.get('size_bytes') is not None else 'missing')}</td>"
        f"<td>{_e(item.get('path'))}</td>"
        "</tr>"
        for item in artifacts
    )
    return (
        '<section class="panel"><h2>Artifacts</h2><table>'
        "<thead><tr><th>Key</th><th>Required</th><th>Exists</th><th>Size</th><th>Path</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>"
    )


def _list_section(title: str, items: Any, *, css_class: str = "") -> str:
    values = _string_list(items)
    if not values:
        return ""
    class_attr = f" {css_class}" if css_class else ""
    return (
        f'<section class="panel{class_attr}"><h2>{_e(title)}</h2><ul>'
        + "".join(f"<li>{_e(item)}</li>" for item in values)
        + "</ul></section>"
    )


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(_fmt_any(value))}</strong></div>'


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, "Microsoft YaHei", sans-serif; background:#f6f7f2; color:#172026; }
* { box-sizing:border-box; }
body { margin:0; padding:28px; }
header, section, footer { max-width:1180px; margin:0 auto 18px; }
header { border-bottom:1px solid #d7dccf; padding-bottom:18px; }
h1 { font-size:30px; margin:0 0 8px; letter-spacing:0; }
h2 { font-size:18px; margin:0 0 12px; letter-spacing:0; }
p { color:#4f5d52; overflow-wrap:anywhere; }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px; }
.card, .panel { background:#fff; border:1px solid #d9ded7; border-radius:8px; padding:14px; box-shadow:0 1px 2px rgba(23,32,38,0.05); }
.card span { display:block; color:#667366; font-size:12px; text-transform:uppercase; }
.card strong { display:block; margin-top:6px; font-size:17px; overflow-wrap:anywhere; }
.panel { overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:820px; }
th, td { text-align:left; border-bottom:1px solid #e3e7df; padding:9px; vertical-align:top; }
th { color:#435047; font-size:12px; text-transform:uppercase; }
tr.pass td:first-child { color:#047857; font-weight:700; }
tr.warn td:first-child { color:#b45309; font-weight:700; }
tr.fail td:first-child { color:#b91c1c; font-weight:700; }
.warn { border-color:#f59e0b; }
li { margin:7px 0; }
footer { color:#69756a; font-size:12px; }
</style>"""


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_any(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{key}:{item}" for key, item in value.items()) or "missing"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "missing"
    return _fmt(value)


__all__ = [
    "render_training_run_evidence_html",
    "render_training_run_evidence_markdown",
    "write_training_run_evidence_csv",
    "write_training_run_evidence_html",
    "write_training_run_evidence_json",
    "write_training_run_evidence_markdown",
    "write_training_run_evidence_outputs",
]
