from __future__ import annotations

import html
from pathlib import Path
from typing import Any


def style() -> str:
    return """<style>
:root {
  color-scheme: light;
  --ink: #111827;
  --muted: #4b5563;
  --line: #d8dee9;
  --panel: #ffffff;
  --page: #f7f7f2;
  --blue: #2563eb;
  --green: #047857;
  --amber: #b45309;
  --red: #b91c1c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--page);
  color: var(--ink);
  font-family: Arial, "Microsoft YaHei", sans-serif;
  line-height: 1.5;
}
header {
  padding: 28px 32px 18px;
  border-bottom: 1px solid var(--line);
  background: #ffffff;
}
h1 { margin: 0 0 8px; font-size: 28px; font-weight: 700; letter-spacing: 0; }
h2 { margin: 28px 32px 12px; font-size: 18px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  padding: 18px 32px 4px;
}
.cell, .artifact, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.cell { padding: 14px; min-height: 84px; }
.label { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.value { margin-top: 6px; font-size: 21px; font-weight: 700; overflow-wrap: anywhere; }
.artifact { padding: 12px; min-height: 118px; }
.artifact a { color: var(--blue); text-decoration: none; font-weight: 700; }
.artifact.missing { opacity: 0.56; }
.badge {
  display: inline-block;
  min-width: 42px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e0f2fe;
  color: #075985;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}
.panel {
  margin: 0 32px 18px;
  padding: 16px;
}
.split {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
table { width: 100%; border-collapse: collapse; }
td, th { padding: 8px 6px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.bar { height: 12px; background: #e5e7eb; border-radius: 6px; overflow: hidden; }
.fill { height: 100%; background: var(--green); }
img.figure { display: block; max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
pre {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #f3f4f6;
  padding: 12px;
  border-radius: 8px;
  color: #111827;
}
.warn { border-color: #f59e0b; background: #fffbeb; }
footer { padding: 22px 32px 34px; color: var(--muted); font-size: 13px; }
@media (max-width: 680px) {
  header, .grid { padding-left: 16px; padding-right: 16px; }
  h2 { margin-left: 16px; margin-right: 16px; }
  .panel { margin-left: 16px; margin-right: 16px; }
}
</style>"""


def stats_grid(stats: list[tuple[str, Any]]) -> str:
    cells = []
    for label, value in stats:
        cells.append(
            f'<div class="cell"><div class="label">{escape(label)}</div>'
            f'<div class="value">{escape(fmt_missing(value))}</div></div>'
        )
    return '<section class="grid">' + "".join(cells) + "</section>"


def artifact_grid(artifacts: list[dict[str, Any]]) -> str:
    rows = []
    for artifact in artifacts:
        href = artifact.get("href")
        title = escape(artifact["title"])
        class_name = "artifact" if artifact.get("exists") else "artifact missing"
        heading = f'<a href="{escape(href)}">{title}</a>' if href else f"<strong>{title}</strong>"
        size = fmt_int(artifact.get("size_bytes")) if artifact.get("size_bytes") is not None else "missing"
        rows.append(
            f'<article class="{class_name}"><span class="badge">{escape(artifact["kind"])}</span>'
            f"<h3>{heading}</h3><p>{escape(artifact['description'])}</p><p>{escape(size)}</p></article>"
        )
    return "<h2>Artifacts</h2><section class=\"grid\">" + "".join(rows) + "</section>"


def model_section(payload: dict[str, Any]) -> str:
    report = payload.get("model_report")
    if not isinstance(report, dict):
        return ""
    config = report.get("config", {})
    groups = report.get("owned_parameter_groups", [])
    max_params = max((int(group.get("parameters", 0)) for group in groups), default=1)
    config_rows = "".join(f"<tr><th>{escape(key)}</th><td>{escape(value)}</td></tr>" for key, value in config.items())
    group_rows = []
    for group in groups:
        params = int(group.get("parameters", 0))
        percent = group.get("percent", 0)
        width = 0 if max_params == 0 else int(params * 100 / max_params)
        group_rows.append(
            f"<tr><td>{escape(group.get('label'))}</td><td>{fmt_int(params)}</td><td>{escape(percent)}%</td>"
            f'<td><div class="bar"><div class="fill" style="width:{width}%"></div></div></td></tr>'
        )
    figure = image(payload, "model_svg", "Model architecture")
    return (
        "<h2>Model</h2><section class=\"panel\"><div class=\"split\">"
        f"<div><table>{config_rows}</table></div>"
        f"<div><table><tr><th>Group</th><th>Params</th><th>Share</th><th></th></tr>{''.join(group_rows)}</table></div>"
        f"</div>{figure}</section>"
    )


def manifest_section(payload: dict[str, Any]) -> str:
    manifest = payload.get("run_manifest")
    if not isinstance(manifest, dict):
        return ""
    git = manifest.get("git", {}) if isinstance(manifest.get("git"), dict) else {}
    data = manifest.get("data", {}) if isinstance(manifest.get("data"), dict) else {}
    model = manifest.get("model", {}) if isinstance(manifest.get("model"), dict) else {}
    training = manifest.get("training", {}) if isinstance(manifest.get("training"), dict) else {}
    results = manifest.get("results", {}) if isinstance(manifest.get("results"), dict) else {}
    history = results.get("history_summary", {}) if isinstance(results.get("history_summary"), dict) else {}
    rows = [
        ("Commit", git.get("short_commit")),
        ("Branch", git.get("branch")),
        ("Dirty", git.get("dirty")),
        ("Tokens", data.get("token_count")),
        ("Train/val", f"{data.get('train_token_count')} / {data.get('val_token_count')}"),
        ("Parameters", fmt_int(model.get("parameter_count"))),
        ("Tokenizer", training.get("tokenizer")),
        ("Best val", fmt(history.get("best_val_loss"))),
        ("Started", manifest.get("started_at")),
        ("Duration", f"{manifest.get('duration_seconds')}s"),
    ]
    table = "".join(f"<tr><th>{escape(label)}</th><td>{escape(fmt_missing(value))}</td></tr>" for label, value in rows)
    figure = image(payload, "manifest_svg", "Run manifest")
    return f"<h2>Run Manifest</h2><section class=\"panel\"><table>{table}</table>{figure}</section>"


def dataset_section(payload: dict[str, Any]) -> str:
    report = payload.get("dataset_report")
    quality = payload.get("dataset_quality")
    version = payload.get("dataset_version")
    if not isinstance(report, dict) and not isinstance(quality, dict) and not isinstance(version, dict):
        return ""
    dataset_id = nested_pick(version, "dataset", "id")
    version_stats = pick(version, "stats")
    rows = []
    if isinstance(report, dict):
        for source in report.get("sources", [])[:8]:
            if isinstance(source, dict):
                rows.append(
                    f"<tr><td>{escape(Path(str(source.get('path'))).name)}</td>"
                    f"<td>{escape(source.get('char_count'))}</td>"
                    f"<td>{escape(source.get('line_count'))}</td>"
                    f"<td>{escape(source.get('unique_char_count'))}</td></tr>"
                )
    quality_rows = ""
    if isinstance(quality, dict):
        quality_rows = (
            f"<p>Quality: {escape(quality.get('status'))} | Fingerprint: {escape(quality.get('short_fingerprint'))} | "
            f"Warnings: {escape(quality.get('warning_count'))} | Issues: {escape(quality.get('issue_count'))}</p>"
        )
    version_rows = ""
    if isinstance(version, dict):
        version_rows = (
            f"<p>Dataset version: {escape(dataset_id)} | Version fingerprint: {escape(pick(version_stats, 'short_fingerprint'))}</p>"
        )
    figure = image(payload, "dataset_svg", "Dataset chart")
    quality_figure = image(payload, "dataset_quality_svg", "Dataset quality chart")
    return (
        "<h2>Dataset</h2><section class=\"panel\">"
        f"<p>Sources: {escape(pick(report, 'source_count'))} | Characters: {escape(pick(report, 'char_count'))} | Unique chars: {escape(pick(report, 'unique_char_count'))}</p>"
        f"{version_rows}"
        f"{quality_rows}"
        f"<table><tr><th>Source</th><th>Chars</th><th>Lines</th><th>Unique</th></tr>{''.join(rows)}</table>"
        f"{figure}{quality_figure}</section>"
    )


def training_section(payload: dict[str, Any]) -> str:
    history = payload.get("history_summary")
    if not isinstance(history, dict):
        return ""
    rows = "".join(f"<tr><th>{escape(key)}</th><td>{escape(fmt(value))}</td></tr>" for key, value in history.items())
    figure = image(payload, "loss_curve", "Loss curve")
    eval_report = payload.get("eval_report")
    eval_rows = ""
    if isinstance(eval_report, dict):
        eval_rows = "".join(f"<tr><th>{escape(key)}</th><td>{escape(fmt(value))}</td></tr>" for key, value in eval_report.items() if key in {"split", "loss", "perplexity", "eval_iters", "batch_size"})
    return f"<h2>Training</h2><section class=\"panel\"><div class=\"split\"><table>{rows}</table><table>{eval_rows}</table></div>{figure}</section>"


def eval_suite_section(payload: dict[str, Any]) -> str:
    report = payload.get("eval_suite")
    if not isinstance(report, dict):
        return ""
    benchmark = report.get("benchmark") if isinstance(report.get("benchmark"), dict) else {}
    task_counts = benchmark.get("task_type_counts") or report.get("task_type_counts") or {}
    difficulty_counts = benchmark.get("difficulty_counts") or report.get("difficulty_counts") or {}
    rows = []
    for item in report.get("results", [])[:8]:
        if isinstance(item, dict):
            rows.append(
                f"<tr><td>{escape(item.get('name'))}</td><td>{escape(item.get('task_type'))}</td><td>{escape(item.get('difficulty'))}</td><td>{escape(item.get('prompt'))}</td>"
                f"<td>{escape(item.get('seed'))}</td><td>{escape(item.get('unique_char_count'))}</td>"
                f"<td>{escape(clip(str(item.get('continuation', '')), 60))}</td></tr>"
            )
    figure = image(payload, "eval_suite_svg", "Eval suite chart")
    return (
        "<h2>Eval Suite</h2><section class=\"panel\">"
        f"<p>Suite: {escape(benchmark.get('suite_name') or report.get('suite'))} | Cases: {escape(report.get('case_count'))} | Tasks: {escape(join_counts(task_counts))} | Difficulty: {escape(join_counts(difficulty_counts))}</p>"
        f"<p>Avg continuation chars: {escape(report.get('avg_continuation_chars'))} | Avg unique chars: {escape(report.get('avg_unique_chars'))}</p>"
        f"<table><tr><th>Name</th><th>Task</th><th>Difficulty</th><th>Prompt</th><th>Seed</th><th>Unique</th><th>Continuation</th></tr>{''.join(rows)}</table>"
        f"{figure}</section>"
    )


def pair_batch_section(payload: dict[str, Any]) -> str:
    batch = payload.get("pair_batch")
    trend = payload.get("pair_trend")
    if not isinstance(batch, dict) and not isinstance(trend, dict):
        return ""
    batch_links = [
        artifact_anchor(payload, "pair_batch_html", "Open pair batch HTML"),
        artifact_anchor(payload, "pair_batch_json", "JSON"),
        artifact_anchor(payload, "pair_batch_csv", "CSV"),
        artifact_anchor(payload, "pair_batch_md", "Markdown"),
    ]
    trend_links = [
        artifact_anchor(payload, "pair_trend_html", "Open pair trend HTML"),
        artifact_anchor(payload, "pair_trend_json", "JSON"),
        artifact_anchor(payload, "pair_trend_csv", "CSV"),
        artifact_anchor(payload, "pair_trend_md", "Markdown"),
    ]
    batch_rows = ""
    if isinstance(batch, dict):
        suite = batch.get("suite") if isinstance(batch.get("suite"), dict) else {}
        left = batch.get("left") if isinstance(batch.get("left"), dict) else {}
        right = batch.get("right") if isinstance(batch.get("right"), dict) else {}
        batch_rows = "".join(
            f"<tr><th>{escape(label)}</th><td>{escape(fmt_missing(value))}</td></tr>"
            for label, value in [
                ("Suite", f"{suite.get('name')} v{suite.get('version')}"),
                ("Pair", f"{left.get('checkpoint_id')} -> {right.get('checkpoint_id')}"),
                ("Cases", batch.get("case_count")),
                ("Generated diff", batch.get("generated_difference_count")),
                ("Avg gen delta", batch.get("avg_abs_generated_char_delta")),
            ]
        )
    trend_rows = ""
    if isinstance(trend, dict):
        trend_rows = "".join(
            f"<tr><th>{escape(label)}</th><td>{escape(fmt_missing(value))}</td></tr>"
            for label, value in [
                ("Reports", trend.get("report_count")),
                ("Cases", trend.get("case_count")),
                ("Changed cases", trend.get("changed_generated_equal_cases")),
                ("Max gen delta", trend.get("max_abs_generated_char_delta")),
                ("Max cont delta", trend.get("max_abs_continuation_char_delta")),
            ]
        )
    return (
        "<h2>Pair Batch Reports</h2><section class=\"panel\"><div class=\"split\">"
        f"<div><h3>Batch</h3><table>{batch_rows}</table><p>{' | '.join(link for link in batch_links if link)}</p></div>"
        f"<div><h3>Trend</h3><table>{trend_rows}</table><p>{' | '.join(link for link in trend_links if link)}</p></div>"
        "</div></section>"
    )


def prediction_section(payload: dict[str, Any]) -> str:
    predictions = payload.get("predictions")
    if not isinstance(predictions, dict):
        return ""
    rows = []
    for item in predictions.get("predictions", [])[:8]:
        rows.append(
            f"<tr><td>{escape(item.get('rank'))}</td><td>{escape(item.get('token'))}</td>"
            f"<td>{escape(item.get('probability'))}</td><td>{escape(item.get('logit'))}</td></tr>"
        )
    figure = image(payload, "predictions_svg", "Prediction chart")
    return (
        "<h2>Prediction</h2><section class=\"panel\">"
        f"<p>Prompt: {escape(predictions.get('prompt'))}</p>"
        f"<table><tr><th>Rank</th><th>Token</th><th>Probability</th><th>Logit</th></tr>{''.join(rows)}</table>"
        f"{figure}</section>"
    )


def attention_section(payload: dict[str, Any]) -> str:
    attention = payload.get("attention")
    if not isinstance(attention, dict):
        return ""
    rows = []
    for item in attention.get("last_token_top_links", [])[:6]:
        rows.append(
            f"<tr><td>{escape(item.get('from_token'))}</td><td>{escape(item.get('to_token'))}</td>"
            f"<td>{escape(item.get('weight'))}</td></tr>"
        )
    figure = image(payload, "attention_svg", "Attention chart")
    return (
        "<h2>Attention</h2><section class=\"panel\">"
        f"<p>Prompt: {escape(attention.get('prompt'))}</p>"
        f"<table><tr><th>From</th><th>To</th><th>Weight</th></tr>{''.join(rows)}</table>"
        f"{figure}</section>"
    )


def chat_section(payload: dict[str, Any]) -> str:
    transcript = payload.get("transcript")
    if not isinstance(transcript, dict):
        return ""
    rows = []
    for turn in transcript.get("turns", []):
        if isinstance(turn, dict):
            rows.append(f"<tr><th>{escape(turn.get('role'))}</th><td>{escape(turn.get('content'))}</td></tr>")
    return f"<h2>Chat</h2><section class=\"panel\"><table>{''.join(rows)}</table></section>"


def text_section(title: str, text: Any) -> str:
    if not text:
        return ""
    return f"<h2>{escape(title)}</h2><section class=\"panel\"><pre>{escape(text)}</pre></section>"


def warning_section(warnings: list[str]) -> str:
    if not warnings:
        return ""
    rows = "".join(f"<li>{escape(warning)}</li>" for warning in warnings)
    return f'<section class="panel warn"><strong>Warnings</strong><ul>{rows}</ul></section>'


def image(payload: dict[str, Any], key: str, alt: str) -> str:
    artifact = next((item for item in payload["artifacts"] if item["key"] == key and item.get("href")), None)
    if artifact is None:
        return ""
    return f'<p><img class="figure" src="{escape(artifact["href"])}" alt="{escape(alt)}"></p>'


def artifact_anchor(payload: dict[str, Any], key: str, label: str) -> str:
    artifact = next((item for item in payload["artifacts"] if item["key"] == key and item.get("href")), None)
    if artifact is None:
        return ""
    return f'<a href="{escape(artifact["href"])}">{escape(label)}</a>'


def pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def nested_pick(payload: Any, section: str, key: str) -> Any:
    if not isinstance(payload, dict):
        return None
    nested = payload.get(section)
    if isinstance(nested, dict):
        return nested.get(key)
    return None


def fmt(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


def fmt_int(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return fmt_missing(value)


def fmt_missing(value: Any) -> str:
    if value is None:
        return "missing"
    return str(fmt(value))


def clip(text: str, limit: int) -> str:
    flat = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "..."


def join_counts(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return ""
    return ", ".join(f"{key}={count}" for key, count in value.items())


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "artifact_grid",
    "artifact_anchor",
    "attention_section",
    "chat_section",
    "clip",
    "dataset_section",
    "escape",
    "eval_suite_section",
    "fmt",
    "fmt_int",
    "fmt_missing",
    "image",
    "join_counts",
    "manifest_section",
    "model_section",
    "nested_pick",
    "pair_batch_section",
    "pick",
    "prediction_section",
    "stats_grid",
    "style",
    "text_section",
    "training_section",
    "warning_section",
]
