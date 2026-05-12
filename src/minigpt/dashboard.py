from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DashboardArtifact:
    key: str
    title: str
    path: Path
    kind: str
    description: str
    exists: bool
    size_bytes: int | None
    href: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} is not valid JSON: {exc}")
        return None


def _read_text(path: Path, limit: int = 1200) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit].rstrip() + "\n..."
    return text


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _href(path: Path, base_dir: Path) -> str | None:
    if not path.exists():
        return None
    return Path(os.path.relpath(path, base_dir)).as_posix()


def _artifact(
    key: str,
    title: str,
    path: Path,
    kind: str,
    description: str,
    base_dir: Path,
) -> DashboardArtifact:
    exists = path.exists()
    return DashboardArtifact(
        key=key,
        title=title,
        path=path,
        kind=kind,
        description=description,
        exists=exists,
        size_bytes=path.stat().st_size if exists and path.is_file() else None,
        href=_href(path, base_dir),
    )


def collect_artifacts(run_dir: str | Path, base_dir: str | Path) -> list[DashboardArtifact]:
    root = Path(run_dir)
    base = Path(base_dir)
    specs = [
        ("checkpoint", "Checkpoint", "checkpoint.pt", "PT", "saved model and optimizer state"),
        ("tokenizer", "Tokenizer", "tokenizer.json", "JSON", "token vocabulary and tokenizer metadata"),
        ("train_config", "Train config", "train_config.json", "JSON", "training command configuration"),
        ("metrics", "Metrics history", "metrics.jsonl", "JSONL", "step-by-step train/validation losses"),
        ("history_summary", "History summary", "history_summary.json", "JSON", "best and latest loss summary"),
        ("loss_curve", "Loss curve", "loss_curve.svg", "SVG", "training and validation loss chart"),
        ("sample", "Sample text", "sample.txt", "TXT", "generated sample saved after training"),
        ("eval_report", "Evaluation report", "eval_report.json", "JSON", "loss and perplexity report"),
        ("model_report", "Model report", "model_report/model_report.json", "JSON", "architecture and parameter report"),
        ("model_svg", "Model architecture", "model_report/model_architecture.svg", "SVG", "model structure diagram"),
        ("predictions", "Prediction report", "predictions/predictions.json", "JSON", "next-token top-k probabilities"),
        ("predictions_svg", "Prediction chart", "predictions/predictions.svg", "SVG", "next-token probability chart"),
        ("attention", "Attention report", "attention/attention.json", "JSON", "attention matrix and top links"),
        ("attention_svg", "Attention chart", "attention/attention.svg", "SVG", "attention heatmap"),
        ("transcript", "Chat transcript", "transcript.json", "JSON", "one-shot or interactive chat transcript"),
        ("generated", "Generated text", "generated.txt", "TXT", "standalone generation output"),
    ]
    return [
        _artifact(key, title, root / relative, kind, description, base)
        for key, title, relative, kind, description in specs
    ]


def build_dashboard_payload(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT experiment dashboard",
) -> dict[str, Any]:
    root = Path(run_dir)
    out_path = Path(output_path) if output_path is not None else root / "dashboard.html"
    base_dir = out_path.parent
    warnings: list[str] = []

    train_config = _read_json(root / "train_config.json", warnings)
    history_summary = _read_json(root / "history_summary.json", warnings)
    eval_report = _read_json(root / "eval_report.json", warnings)
    model_report = _read_json(root / "model_report" / "model_report.json", warnings)
    predictions = _read_json(root / "predictions" / "predictions.json", warnings)
    attention = _read_json(root / "attention" / "attention.json", warnings)
    transcript = _read_json(root / "transcript.json", warnings)
    sample_text = _read_text(root / "sample.txt")
    generated_text = _read_text(root / "generated.txt")

    artifacts = collect_artifacts(root, base_dir)
    available = [artifact for artifact in artifacts if artifact.exists]
    model_config = model_report.get("config") if isinstance(model_report, dict) else None
    top_prediction = None
    if isinstance(predictions, dict) and predictions.get("predictions"):
        top_prediction = predictions["predictions"][0]
    last_assistant = None
    if isinstance(transcript, dict):
        turns = transcript.get("turns", [])
        for turn in reversed(turns):
            if isinstance(turn, dict) and turn.get("role") == "assistant":
                last_assistant = turn.get("content")
                break

    summary = {
        "run_dir": str(root),
        "available_artifacts": len(available),
        "metrics_records": _line_count(root / "metrics.jsonl"),
        "tokenizer": _pick(train_config, "tokenizer") or _pick(eval_report, "tokenizer") or _pick(model_report, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters"),
        "best_val_loss": _pick(history_summary, "best_val_loss"),
        "last_val_loss": _pick(history_summary, "last_val_loss"),
        "eval_loss": _pick(eval_report, "loss"),
        "perplexity": _pick(eval_report, "perplexity"),
        "total_parameters": _pick(model_report, "total_parameters"),
        "top_prediction": top_prediction,
        "last_assistant": last_assistant,
    }

    return {
        "title": title,
        "run_dir": str(root),
        "output_path": str(out_path),
        "summary": summary,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "train_config": train_config if isinstance(train_config, dict) else None,
        "history_summary": history_summary if isinstance(history_summary, dict) else None,
        "eval_report": eval_report if isinstance(eval_report, dict) else None,
        "model_report": model_report if isinstance(model_report, dict) else None,
        "model_config": model_config if isinstance(model_config, dict) else None,
        "predictions": predictions if isinstance(predictions, dict) else None,
        "attention": attention if isinstance(attention, dict) else None,
        "transcript": transcript if isinstance(transcript, dict) else None,
        "sample_text": sample_text,
        "generated_text": generated_text,
        "warnings": warnings,
    }


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def render_dashboard_html(payload: dict[str, Any]) -> str:
    title = str(payload["title"])
    summary = payload["summary"]
    artifacts = payload["artifacts"]
    stats = [
        ("Artifacts", summary.get("available_artifacts")),
        ("Metrics", summary.get("metrics_records")),
        ("Tokenizer", summary.get("tokenizer")),
        ("Max iters", summary.get("max_iters")),
        ("Best val", _fmt(summary.get("best_val_loss"))),
        ("Eval loss", _fmt(summary.get("eval_loss"))),
        ("Perplexity", _fmt(summary.get("perplexity"))),
        ("Parameters", _fmt_int(summary.get("total_parameters"))),
    ]

    sections = [
        _style(),
        f"<header><h1>{_e(title)}</h1><p>{_e(str(payload['run_dir']))}</p></header>",
        _stats_grid(stats),
        _artifact_grid(artifacts),
        _model_section(payload),
        _training_section(payload),
        _prediction_section(payload),
        _attention_section(payload),
        _chat_section(payload),
        _text_section("Sample", payload.get("sample_text")),
        _text_section("Generated", payload.get("generated_text")),
        _warning_section(payload.get("warnings", [])),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(title)}</title>",
            "</head>",
            "<body>",
            *sections,
            "<footer>Generated by MiniGPT dashboard exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_dashboard(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT experiment dashboard",
) -> dict[str, Any]:
    out_path = Path(output_path) if output_path is not None else Path(run_dir) / "dashboard.html"
    payload = build_dashboard_payload(run_dir, output_path=out_path, title=title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dashboard_html(payload), encoding="utf-8")
    return payload


def _style() -> str:
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


def _stats_grid(stats: list[tuple[str, Any]]) -> str:
    cells = []
    for label, value in stats:
        cells.append(
            f'<div class="cell"><div class="label">{_e(label)}</div>'
            f'<div class="value">{_e(_fmt_missing(value))}</div></div>'
        )
    return '<section class="grid">' + "".join(cells) + "</section>"


def _artifact_grid(artifacts: list[dict[str, Any]]) -> str:
    rows = []
    for artifact in artifacts:
        href = artifact.get("href")
        title = _e(artifact["title"])
        class_name = "artifact" if artifact.get("exists") else "artifact missing"
        heading = f'<a href="{_e(href)}">{title}</a>' if href else f"<strong>{title}</strong>"
        size = _fmt_int(artifact.get("size_bytes")) if artifact.get("size_bytes") is not None else "missing"
        rows.append(
            f'<article class="{class_name}"><span class="badge">{_e(artifact["kind"])}</span>'
            f"<h3>{heading}</h3><p>{_e(artifact['description'])}</p><p>{_e(size)}</p></article>"
        )
    return "<h2>Artifacts</h2><section class=\"grid\">" + "".join(rows) + "</section>"


def _model_section(payload: dict[str, Any]) -> str:
    report = payload.get("model_report")
    if not isinstance(report, dict):
        return ""
    config = report.get("config", {})
    groups = report.get("owned_parameter_groups", [])
    max_params = max((int(group.get("parameters", 0)) for group in groups), default=1)
    config_rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(value)}</td></tr>" for key, value in config.items())
    group_rows = []
    for group in groups:
        params = int(group.get("parameters", 0))
        percent = group.get("percent", 0)
        width = 0 if max_params == 0 else int(params * 100 / max_params)
        group_rows.append(
            f"<tr><td>{_e(group.get('label'))}</td><td>{_fmt_int(params)}</td><td>{_e(percent)}%</td>"
            f'<td><div class="bar"><div class="fill" style="width:{width}%"></div></div></td></tr>'
        )
    figure = _image(payload, "model_svg", "Model architecture")
    return (
        "<h2>Model</h2><section class=\"panel\"><div class=\"split\">"
        f"<div><table>{config_rows}</table></div>"
        f"<div><table><tr><th>Group</th><th>Params</th><th>Share</th><th></th></tr>{''.join(group_rows)}</table></div>"
        f"</div>{figure}</section>"
    )


def _training_section(payload: dict[str, Any]) -> str:
    history = payload.get("history_summary")
    if not isinstance(history, dict):
        return ""
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt(value))}</td></tr>" for key, value in history.items())
    figure = _image(payload, "loss_curve", "Loss curve")
    eval_report = payload.get("eval_report")
    eval_rows = ""
    if isinstance(eval_report, dict):
        eval_rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt(value))}</td></tr>" for key, value in eval_report.items() if key in {"split", "loss", "perplexity", "eval_iters", "batch_size"})
    return f"<h2>Training</h2><section class=\"panel\"><div class=\"split\"><table>{rows}</table><table>{eval_rows}</table></div>{figure}</section>"


def _prediction_section(payload: dict[str, Any]) -> str:
    predictions = payload.get("predictions")
    if not isinstance(predictions, dict):
        return ""
    rows = []
    for item in predictions.get("predictions", [])[:8]:
        rows.append(
            f"<tr><td>{_e(item.get('rank'))}</td><td>{_e(item.get('token'))}</td>"
            f"<td>{_e(item.get('probability'))}</td><td>{_e(item.get('logit'))}</td></tr>"
        )
    figure = _image(payload, "predictions_svg", "Prediction chart")
    return (
        "<h2>Prediction</h2><section class=\"panel\">"
        f"<p>Prompt: {_e(predictions.get('prompt'))}</p>"
        f"<table><tr><th>Rank</th><th>Token</th><th>Probability</th><th>Logit</th></tr>{''.join(rows)}</table>"
        f"{figure}</section>"
    )


def _attention_section(payload: dict[str, Any]) -> str:
    attention = payload.get("attention")
    if not isinstance(attention, dict):
        return ""
    rows = []
    for item in attention.get("last_token_top_links", [])[:6]:
        rows.append(
            f"<tr><td>{_e(item.get('from_token'))}</td><td>{_e(item.get('to_token'))}</td>"
            f"<td>{_e(item.get('weight'))}</td></tr>"
        )
    figure = _image(payload, "attention_svg", "Attention chart")
    return (
        "<h2>Attention</h2><section class=\"panel\">"
        f"<p>Prompt: {_e(attention.get('prompt'))}</p>"
        f"<table><tr><th>From</th><th>To</th><th>Weight</th></tr>{''.join(rows)}</table>"
        f"{figure}</section>"
    )


def _chat_section(payload: dict[str, Any]) -> str:
    transcript = payload.get("transcript")
    if not isinstance(transcript, dict):
        return ""
    rows = []
    for turn in transcript.get("turns", []):
        if isinstance(turn, dict):
            rows.append(f"<tr><th>{_e(turn.get('role'))}</th><td>{_e(turn.get('content'))}</td></tr>")
    return f"<h2>Chat</h2><section class=\"panel\"><table>{''.join(rows)}</table></section>"


def _text_section(title: str, text: Any) -> str:
    if not text:
        return ""
    return f"<h2>{_e(title)}</h2><section class=\"panel\"><pre>{_e(text)}</pre></section>"


def _warning_section(warnings: list[str]) -> str:
    if not warnings:
        return ""
    rows = "".join(f"<li>{_e(warning)}</li>" for warning in warnings)
    return f'<section class="panel warn"><strong>Warnings</strong><ul>{rows}</ul></section>'


def _image(payload: dict[str, Any], key: str, alt: str) -> str:
    artifact = next((item for item in payload["artifacts"] if item["key"] == key and item.get("href")), None)
    if artifact is None:
        return ""
    return f'<p><img class="figure" src="{_e(artifact["href"])}" alt="{_e(alt)}"></p>'


def _fmt(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


def _fmt_int(value: Any) -> str:
    if isinstance(value, int):
        return f"{value:,}"
    return _fmt_missing(value)


def _fmt_missing(value: Any) -> str:
    if value is None:
        return "missing"
    return str(_fmt(value))


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
