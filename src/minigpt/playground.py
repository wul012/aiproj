from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import json
import os
from pathlib import Path
from typing import Any

from .dashboard import build_dashboard_payload
from .playground_assets import playground_script, playground_style


@dataclass(frozen=True)
class PlaygroundLink:
    key: str
    title: str
    path: Path
    kind: str
    exists: bool
    size_bytes: int | None
    href: str | None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["path"] = str(self.path)
        return payload


def build_playground_payload(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT playground",
) -> dict[str, Any]:
    root = Path(run_dir)
    out_path = Path(output_path) if output_path is not None else root / "playground.html"
    base_dir = out_path.parent
    warnings: list[str] = []

    dashboard = build_dashboard_payload(root, output_path=out_path, title="MiniGPT dashboard source")
    sampling_report = _read_json(root / "sample_lab" / "sample_lab.json", warnings)
    if sampling_report is not None and not isinstance(sampling_report, dict):
        warnings.append("sample_lab.json must contain an object")
        sampling_report = None

    commands = build_playground_commands(root)
    links = _collect_links(root, out_path, base_dir)
    available_links = [link for link in links if link.exists]
    sampling_cases = []
    if isinstance(sampling_report, dict):
        sampling_cases = list(sampling_report.get("results", []))

    return {
        "title": title,
        "run_dir": str(root),
        "output_path": str(out_path),
        "summary": {
            **dashboard["summary"],
            "playground_links": len(available_links),
            "sampling_cases": len(sampling_cases),
        },
        "commands": commands,
        "links": [link.to_dict() for link in links],
        "dashboard": dashboard,
        "sampling_report": sampling_report if isinstance(sampling_report, dict) else None,
        "warnings": dashboard.get("warnings", []) + warnings,
        "defaults": {
            "prompt": "人工智能",
            "max_new_tokens": 80,
            "temperature": 0.8,
            "top_k": 30,
            "seed": 42,
        },
    }


def build_playground_commands(run_dir: str | Path, prompt: str = "人工智能") -> dict[str, str]:
    root = Path(run_dir)
    checkpoint = root / "checkpoint.pt"
    return {
        "train": f"python scripts/train.py --out-dir {_quote_arg(str(root))}",
        "generate": (
            f"python scripts/generate.py --checkpoint {_quote_arg(str(checkpoint))} "
            f"--prompt {_quote_arg(prompt)} --max-new-tokens 80"
        ),
        "chat": (
            f"python scripts/chat.py --checkpoint {_quote_arg(str(checkpoint))} "
            f"--message {_quote_arg(prompt)} --max-new-tokens 80"
        ),
        "sample_lab": (
            f"python scripts/sample_lab.py --checkpoint {_quote_arg(str(checkpoint))} "
            f"--prompt {_quote_arg(prompt)} --max-new-tokens 80"
        ),
        "pair_batch": (
            f"python scripts/pair_batch.py --left-checkpoint {_quote_arg(str(checkpoint))} "
            f"--right-checkpoint {_quote_arg(str(root / 'wide' / 'checkpoint.pt'))} --left-id base --right-id wide "
            f"--suite {_quote_arg('data/eval_prompts.json')} --out-dir {_quote_arg(str(root / 'pair_batch'))}"
        ),
        "pair_trend": (
            f"python scripts/compare_pair_batches.py {_quote_arg(str(root / 'pair_batch' / 'pair_generation_batch.json'))} "
            f"{_quote_arg(str(root / 'pair_batch_candidate' / 'pair_generation_batch.json'))} --name current --name candidate "
            f"--out-dir {_quote_arg(str(root / 'pair_batch_trend'))}"
        ),
        "inspect_model": f"python scripts/inspect_model.py --checkpoint {_quote_arg(str(checkpoint))}",
        "dashboard": f"python scripts/build_dashboard.py --run-dir {_quote_arg(str(root))}",
        "playground": f"python scripts/build_playground.py --run-dir {_quote_arg(str(root))}",
        "experiment_card": f"python scripts/build_experiment_card.py --run-dir {_quote_arg(str(root))}",
    }


def render_playground_html(payload: dict[str, Any]) -> str:
    title = str(payload["title"])
    summary = payload["summary"]
    defaults = payload["defaults"]
    stats = [
        ("Artifacts", summary.get("available_artifacts")),
        ("Links", summary.get("playground_links")),
        ("Metrics", summary.get("metrics_records")),
        ("Tokenizer", summary.get("tokenizer")),
        ("Best val", _fmt(summary.get("best_val_loss"))),
        ("Sampling", summary.get("sampling_cases")),
    ]
    page_data = {
        "runDir": payload["run_dir"],
        "defaults": defaults,
        "commands": payload["commands"],
        "checkpoints": [],
        "checkpointComparison": [],
        "requestHistory": [],
        "requestHistoryDetail": None,
        "requestHistoryFilters": {"status": "", "endpoint": "", "checkpoint": "", "limit": 12},
        "streamController": None,
    }
    sections = [
        _style(),
        _script(page_data),
        f"<header><h1>{_e(title)}</h1><p>{_e(payload['run_dir'])}</p></header>",
        _stats(stats),
        _command_builder(defaults),
        _live_section(),
        _request_history_section(),
        _checkpoint_comparison_section(),
        _pair_generation_section(),
        _sampling_section(payload.get("sampling_report")),
        _link_section(payload["links"]),
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
            "<footer>Generated by MiniGPT playground exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_playground(
    run_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "MiniGPT playground",
) -> dict[str, Any]:
    out_path = Path(output_path) if output_path is not None else Path(run_dir) / "playground.html"
    payload = build_playground_payload(run_dir, output_path=out_path, title=title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_playground_html(payload), encoding="utf-8")
    return payload


def _collect_links(root: Path, out_path: Path, base_dir: Path) -> list[PlaygroundLink]:
    specs = [
        ("playground", "Playground UI", out_path, "HTML"),
        ("dashboard", "Dashboard", root / "dashboard.html", "HTML"),
        ("checkpoint", "Checkpoint", root / "checkpoint.pt", "PT"),
        ("train_config", "Train config", root / "train_config.json", "JSON"),
        ("metrics", "Metrics", root / "metrics.jsonl", "JSONL"),
        ("history_summary", "History summary", root / "history_summary.json", "JSON"),
        ("loss_curve", "Loss curve", root / "loss_curve.svg", "SVG"),
        ("run_manifest", "Run manifest", root / "run_manifest.json", "JSON"),
        ("manifest_svg", "Manifest chart", root / "run_manifest.svg", "SVG"),
        ("prepared_corpus", "Prepared corpus", root / "prepared_corpus.txt", "TXT"),
        ("dataset_report", "Dataset report", root / "dataset_report.json", "JSON"),
        ("dataset_svg", "Dataset chart", root / "dataset_report.svg", "SVG"),
        ("dataset_quality", "Dataset quality", root / "dataset_quality.json", "JSON"),
        ("dataset_quality_svg", "Dataset quality chart", root / "dataset_quality.svg", "SVG"),
        ("dataset_version", "Dataset version", root / "dataset_version.json", "JSON"),
        ("dataset_version_html", "Dataset version report", root / "dataset_version.html", "HTML"),
        ("sample", "Sample text", root / "sample.txt", "TXT"),
        ("eval_suite", "Eval suite", root / "eval_suite" / "eval_suite.json", "JSON"),
        ("eval_suite_csv", "Eval suite CSV", root / "eval_suite" / "eval_suite.csv", "CSV"),
        ("eval_suite_svg", "Eval suite chart", root / "eval_suite" / "eval_suite.svg", "SVG"),
        ("eval_suite_html", "Eval suite report", root / "eval_suite" / "eval_suite.html", "HTML"),
        ("pair_batch_json", "Pair batch JSON", root / "pair_batch" / "pair_generation_batch.json", "JSON"),
        ("pair_batch_csv", "Pair batch CSV", root / "pair_batch" / "pair_generation_batch.csv", "CSV"),
        ("pair_batch_md", "Pair batch Markdown", root / "pair_batch" / "pair_generation_batch.md", "MD"),
        ("pair_batch_html", "Pair batch HTML", root / "pair_batch" / "pair_generation_batch.html", "HTML"),
        ("pair_trend_json", "Pair trend JSON", root / "pair_batch_trend" / "pair_batch_trend.json", "JSON"),
        ("pair_trend_csv", "Pair trend CSV", root / "pair_batch_trend" / "pair_batch_trend.csv", "CSV"),
        ("pair_trend_md", "Pair trend Markdown", root / "pair_batch_trend" / "pair_batch_trend.md", "MD"),
        ("pair_trend_html", "Pair trend HTML", root / "pair_batch_trend" / "pair_batch_trend.html", "HTML"),
        ("sample_lab_json", "Sampling JSON", root / "sample_lab" / "sample_lab.json", "JSON"),
        ("sample_lab_csv", "Sampling CSV", root / "sample_lab" / "sample_lab.csv", "CSV"),
        ("sample_lab_svg", "Sampling SVG", root / "sample_lab" / "sample_lab.svg", "SVG"),
        ("model_report", "Model report", root / "model_report" / "model_report.json", "JSON"),
        ("prediction_report", "Prediction report", root / "predictions" / "predictions.json", "JSON"),
        ("attention_report", "Attention report", root / "attention" / "attention.json", "JSON"),
        ("experiment_card_json", "Experiment card JSON", root / "experiment_card.json", "JSON"),
        ("experiment_card_md", "Experiment card Markdown", root / "experiment_card.md", "MD"),
        ("experiment_card_html", "Experiment card HTML", root / "experiment_card.html", "HTML"),
    ]
    return [
        _link(key, title, path, kind, base_dir, assume_exists=(key == "playground"))
        for key, title, path, kind in specs
    ]


def _link(
    key: str,
    title: str,
    path: Path,
    kind: str,
    base_dir: Path,
    assume_exists: bool = False,
) -> PlaygroundLink:
    exists = assume_exists or path.exists()
    return PlaygroundLink(
        key=key,
        title=title,
        path=path,
        kind=kind,
        exists=exists,
        size_bytes=path.stat().st_size if path.exists() and path.is_file() else None,
        href=Path(os.path.relpath(path, base_dir)).as_posix() if exists else None,
    )


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} is not valid JSON: {exc}")
        return None


def _style() -> str:
    return playground_style()


def _script(page_data: dict[str, Any]) -> str:
    return playground_script(page_data)


def _stats(stats: list[tuple[str, Any]]) -> str:
    cells = []
    for label, value in stats:
        cells.append(
            f'<div class="stat"><div class="label">{_e(label)}</div>'
            f'<div class="value">{_e(_fmt_missing(value))}</div></div>'
        )
    return '<section class="stats">' + "".join(cells) + "</section>"


def _command_builder(defaults: dict[str, Any]) -> str:
    return f"""<h2>Playground</h2>
<section class="panel builder">
  <div>
    <label class="label" for="promptInput">Prompt</label>
    <textarea id="promptInput">{_e(defaults["prompt"])}</textarea>
    <div class="controls">
      <label><span class="label">Max tokens</span><input id="maxTokensInput" type="number" min="1" max="512" value="{_e(defaults["max_new_tokens"])}"></label>
      <label><span class="label">Temperature</span><input id="temperatureInput" type="number" min="0.1" max="2" step="0.1" value="{_e(defaults["temperature"])}"></label>
      <label><span class="label">Top-k</span><input id="topKInput" type="number" min="0" max="200" value="{_e(defaults["top_k"])}"></label>
      <label><span class="label">Seed</span><input id="seedInput" type="number" value="{_e(defaults["seed"])}"></label>
    </div>
  </div>
  <div class="commands">
    <div class="command"><pre id="generateCommand"></pre><button type="button" onclick="copyCommand('generateCommand')">Copy</button></div>
    <div class="command"><pre id="chatCommand"></pre><button type="button" onclick="copyCommand('chatCommand')">Copy</button></div>
    <div class="command"><pre id="sampleCommand"></pre><button type="button" onclick="copyCommand('sampleCommand')">Copy</button></div>
  </div>
</section>"""


def _live_section() -> str:
    return """<h2>Live Generate</h2>
<section class="panel">
  <div class="live-actions">
    <label><span class="label">Checkpoint</span><select id="checkpointSelect"><option value="">default</option></select></label>
    <button id="liveGenerateButton" type="button">Stream Generate</button>
    <button id="liveStopButton" type="button" disabled>Stop</button>
    <output id="checkpointStatus">Checkpoint selector loads from /api/checkpoints.</output>
  </div>
  <pre id="liveOutput" class="output"></pre>
</section>"""


def _request_history_section() -> str:
    return """<h2>Request History</h2>
<section class="panel">
  <div class="live-actions">
    <label><span class="label">Status</span><select id="requestHistoryStatusFilter"><option value="">all</option><option value="ok">ok</option><option value="timeout">timeout</option><option value="cancelled">cancelled</option><option value="bad_request">bad_request</option><option value="error">error</option></select></label>
    <label><span class="label">Endpoint</span><select id="requestHistoryEndpointFilter"><option value="">all</option><option value="/api/generate">/api/generate</option><option value="/api/generate-stream">/api/generate-stream</option><option value="/api/generate-pair">/api/generate-pair</option><option value="/api/generate-pair-artifact">/api/generate-pair-artifact</option></select></label>
    <label><span class="label">Checkpoint</span><input id="requestHistoryCheckpointFilter" type="text" placeholder="default"></label>
    <label><span class="label">Limit</span><input id="requestHistoryLimitInput" type="number" min="1" max="200" value="12"></label>
    <button id="refreshRequestHistoryButton" type="button">Refresh</button>
    <a id="requestHistoryExportLink" class="artifact-link" href="/api/request-history?format=csv">Export CSV</a>
    <output id="requestHistoryStatus">Request history loads from /api/request-history.</output>
  </div>
  <table id="requestHistoryTable">
    <thead>
      <tr><th>Log</th><th>Time</th><th>Endpoint</th><th>Status</th><th>Checkpoint</th><th>Prompt</th><th>Output</th><th>Stream</th><th>Elapsed</th><th>Actions</th></tr>
    </thead>
    <tbody id="requestHistoryBody"></tbody>
  </table>
  <div id="requestHistoryDetailPanel" class="detail-panel">
    <output id="requestHistoryDetailStatus">Select a request row to inspect normalized and raw JSON.</output>
    <pre id="requestHistoryDetailOutput"></pre>
  </div>
</section>"""


def _checkpoint_comparison_section() -> str:
    return """<h2>Checkpoint Compare</h2>
<section class="panel">
  <div class="live-actions">
    <button id="refreshCheckpointCompareButton" type="button">Refresh</button>
    <output id="checkpointCompareStatus">Checkpoint comparison loads from /api/checkpoint-compare.</output>
  </div>
  <table id="checkpointCompareTable">
    <thead>
      <tr><th>ID</th><th>Status</th><th>Size</th><th>Params</th><th>Dataset</th><th>Param delta</th><th>Size delta</th><th>Actions</th></tr>
    </thead>
    <tbody id="checkpointCompareBody"></tbody>
  </table>
</section>"""


def _pair_generation_section() -> str:
    return """<h2>Side-by-Side Generate</h2>
<section class="panel">
  <div class="live-actions">
    <label><span class="label">Left checkpoint</span><select id="pairLeftCheckpointSelect"><option value="">default</option></select></label>
    <label><span class="label">Right checkpoint</span><select id="pairRightCheckpointSelect"><option value="">default</option></select></label>
    <button id="pairGenerateButton" type="button">Generate Pair</button>
    <button id="pairSaveButton" type="button">Generate & Save Pair</button>
    <output id="pairGenerateStatus">Pair generation uses /api/generate-pair.</output>
    <output id="pairArtifactStatus"></output>
  </div>
  <div class="pair-grid">
    <article class="pair-card">
      <h3>Left</h3>
      <pre id="pairLeftOutput" class="output"></pre>
    </article>
    <article class="pair-card">
      <h3>Right</h3>
      <pre id="pairRightOutput" class="output"></pre>
    </article>
  </div>
</section>"""


def _sampling_section(report: Any) -> str:
    if not isinstance(report, dict):
        return ""
    results = list(report.get("results", []))
    if not results:
        return ""
    max_unique = max((int(item.get("unique_char_count", 0)) for item in results), default=1)
    rows = []
    for item in results:
        unique = int(item.get("unique_char_count", 0))
        width = 0 if max_unique == 0 else int(unique * 100 / max_unique)
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('name'))}</td>"
            f"<td>{_e(item.get('temperature'))}</td>"
            f"<td>{_e(item.get('top_k') if item.get('top_k') is not None else 'none')}</td>"
            f"<td>{_e(item.get('seed'))}</td>"
            f"<td><div class=\"bar\"><div class=\"fill\" style=\"width:{width}%\"></div></div></td>"
            f"<td>{_e(_clip(item.get('continuation', ''), 52))}</td>"
            "</tr>"
        )
    return (
        "<h2>Sampling Lab</h2><section class=\"panel\">"
        f"<p>Prompt: {_e(report.get('prompt'))}</p>"
        "<table><tr><th>Name</th><th>Temp</th><th>Top-k</th><th>Seed</th><th>Unique</th><th>Continuation</th></tr>"
        f"{''.join(rows)}</table></section>"
    )


def _link_section(links: list[dict[str, Any]]) -> str:
    rows = []
    for link in links:
        class_name = "link" if link.get("exists") else "link missing"
        title = _e(link["title"])
        heading = f'<a href="{_e(link.get("href"))}">{title}</a>' if link.get("href") else f"<strong>{title}</strong>"
        size = _fmt_int(link.get("size_bytes")) if link.get("size_bytes") is not None else "missing"
        rows.append(
            f'<article class="{class_name}"><span class="badge">{_e(link["kind"])}</span>'
            f"<h3>{heading}</h3><p>{_e(size)}</p></article>"
        )
    return "<h2>Run Files</h2><section class=\"links\">" + "".join(rows) + "</section>"


def _warning_section(warnings: list[str]) -> str:
    if not warnings:
        return ""
    rows = "".join(f"<li>{_e(warning)}</li>" for warning in warnings)
    return f'<section class="panel warn"><strong>Warnings</strong><ul>{rows}</ul></section>'


def _quote_arg(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def _clip(value: Any, limit: int) -> str:
    text = str(value).replace("\n", "\\n").replace("\t", "\\t")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


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
