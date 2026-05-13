from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import json
import os
from pathlib import Path
from typing import Any

from .dashboard import build_dashboard_payload


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
    }
    sections = [
        _style(),
        _script(page_data),
        f"<header><h1>{_e(title)}</h1><p>{_e(payload['run_dir'])}</p></header>",
        _stats(stats),
        _command_builder(defaults),
        _live_section(),
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
    return """<style>
:root {
  color-scheme: light;
  --ink: #172033;
  --muted: #536176;
  --line: #d9e2ec;
  --panel: #ffffff;
  --page: #f5f7f4;
  --blue: #1d4ed8;
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
  padding: 24px 32px 16px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}
h1 { margin: 0 0 6px; font-size: 27px; letter-spacing: 0; }
h2 { margin: 26px 32px 12px; font-size: 18px; letter-spacing: 0; }
h3 { margin: 10px 0 5px; font-size: 15px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); overflow-wrap: anywhere; }
button, input, output, select, textarea {
  font: inherit;
}
button {
  border: 1px solid #93a4b7;
  border-radius: 7px;
  background: #ffffff;
  color: var(--ink);
  padding: 8px 12px;
  cursor: pointer;
}
button:hover { border-color: var(--blue); color: var(--blue); }
textarea, input, select {
  width: 100%;
  border: 1px solid #b8c5d2;
  border-radius: 7px;
  padding: 9px 10px;
  background: #ffffff;
  color: var(--ink);
}
textarea { min-height: 96px; resize: vertical; }
output { color: var(--muted); }
.stats, .links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 12px;
  padding: 18px 32px 0;
}
.stat, .link, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.stat { padding: 13px; min-height: 82px; }
.label { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.value { margin-top: 6px; font-size: 20px; font-weight: 700; overflow-wrap: anywhere; }
.panel { margin: 0 32px 18px; padding: 16px; }
.builder {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(300px, 1.1fr);
  gap: 16px;
}
.controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.commands {
  display: grid;
  gap: 10px;
}
.command {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: start;
}
pre {
  margin: 0;
  min-height: 44px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #eef3f7;
  border-radius: 7px;
  padding: 10px;
}
.live-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}
.live-actions label { min-width: 220px; }
.selected-row { background: #eef6ff; }
.row-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.row-actions a { color: var(--blue); font-weight: 700; text-decoration: none; }
.pair-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(260px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.pair-card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  background: #ffffff;
}
.artifact-link { color: var(--blue); font-weight: 700; text-decoration: none; }
.output {
  margin-top: 12px;
  min-height: 92px;
}
.links { padding-top: 0; }
.link { padding: 12px; min-height: 105px; }
.link a { color: var(--blue); font-weight: 700; text-decoration: none; }
.link.missing { opacity: 0.55; }
.badge {
  display: inline-block;
  min-width: 44px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e6f0ff;
  color: #1746a2;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}
table { width: 100%; border-collapse: collapse; }
td, th { padding: 8px 6px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.bar { height: 12px; min-width: 80px; background: #e5e7eb; border-radius: 6px; overflow: hidden; }
.fill { height: 100%; background: var(--green); }
.warn { border-color: #f59e0b; background: #fffbeb; }
footer { padding: 22px 32px 34px; color: var(--muted); font-size: 13px; }
@media (max-width: 760px) {
  header, .stats, .links { padding-left: 16px; padding-right: 16px; }
  h2 { margin-left: 16px; margin-right: 16px; }
  .panel { margin-left: 16px; margin-right: 16px; }
  .builder { grid-template-columns: 1fr; }
  .command { grid-template-columns: 1fr; }
  .pair-grid { grid-template-columns: 1fr; }
}
</style>"""


def _script(page_data: dict[str, Any]) -> str:
    data = json.dumps(page_data, ensure_ascii=False)
    return f"""<script>
const MiniGPTPlayground = {data};
function quoteArg(value) {{
  const text = String(value).replaceAll("'", "''");
  return "'" + text + "'";
}}
function checkpointOptionById(id) {{
  if (!id) return null;
  return (MiniGPTPlayground.checkpoints || []).find((item) => item.id === id) || null;
}}
function selectedCheckpointOption(selectId = 'checkpointSelect') {{
  const select = document.getElementById(selectId);
  if (!select || !select.value) return null;
  return checkpointOptionById(select.value);
}}
function formatValue(value) {{
  if (value === null || value === undefined || value === '') return 'missing';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return String(value);
}}
function formatBytes(value) {{
  if (typeof value !== 'number') return 'missing';
  return value.toLocaleString() + ' B';
}}
function formatDelta(value) {{
  if (typeof value !== 'number') return 'missing';
  if (value === 0) return '0';
  return (value > 0 ? '+' : '') + value.toLocaleString();
}}
function appendCell(row, value) {{
  const cell = document.createElement('td');
  cell.textContent = formatValue(value);
  row.appendChild(cell);
  return cell;
}}
function setCheckpointSelect(selectId, id) {{
  const select = document.getElementById(selectId);
  if (select) select.value = id;
}}
function selectCheckpoint(id) {{
  setCheckpointSelect('checkpointSelect', id);
  setCheckpointSelect('pairLeftCheckpointSelect', id);
  buildCommands();
  renderCheckpointComparison();
}}
function buildCommands() {{
  const prompt = document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt;
  const maxTokens = document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens;
  const temperature = document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature;
  const topK = document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k;
  const seed = document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed;
  const option = selectedCheckpointOption();
  const checkpoint = option ? option.path : MiniGPTPlayground.runDir + '/checkpoint.pt';
  const generate = `python scripts/generate.py --checkpoint ${{quoteArg(checkpoint)}} --prompt ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --temperature ${{temperature}} --top-k ${{topK}}`;
  const chat = `python scripts/chat.py --checkpoint ${{quoteArg(checkpoint)}} --message ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --temperature ${{temperature}} --top-k ${{topK}}`;
  const sample = `python scripts/sample_lab.py --checkpoint ${{quoteArg(checkpoint)}} --prompt ${{quoteArg(prompt)}} --max-new-tokens ${{maxTokens}} --case conservative:0.6:10:${{seed}} --case balanced:${{temperature}}:${{topK}}:${{Number(seed) + 1}} --case creative:1.1:0:${{Number(seed) + 2}}`;
  document.getElementById('generateCommand').textContent = generate;
  document.getElementById('chatCommand').textContent = chat;
  document.getElementById('sampleCommand').textContent = sample;
}}
async function loadCheckpoints() {{
  const select = document.getElementById('checkpointSelect');
  const status = document.getElementById('checkpointStatus');
  if (!select || !status) return;
  try {{
    const response = await fetch('/api/checkpoints');
    if (!response.ok) throw new Error('checkpoint endpoint unavailable');
    const data = await response.json();
    MiniGPTPlayground.checkpoints = Array.isArray(data.checkpoints) ? data.checkpoints : [];
    populateCheckpointSelect(select, data.default_checkpoint_id, 0);
    populateCheckpointSelect(document.getElementById('pairLeftCheckpointSelect'), data.default_checkpoint_id, 0);
    populateCheckpointSelect(document.getElementById('pairRightCheckpointSelect'), data.default_checkpoint_id, 1);
    if (data.default_checkpoint_id) select.value = data.default_checkpoint_id;
    status.textContent = `${{MiniGPTPlayground.checkpoints.length}} checkpoint option(s)`;
    select.disabled = MiniGPTPlayground.checkpoints.length === 0;
    buildCommands();
    renderCheckpointComparison();
  }} catch (error) {{
    MiniGPTPlayground.checkpoints = [];
    status.textContent = 'Start scripts/serve_playground.py for checkpoint selection.';
    select.disabled = true;
  }}
}}
function populateCheckpointSelect(select, defaultId, preferredIndex) {{
  if (!select) return;
  const previous = select.value;
  const options = MiniGPTPlayground.checkpoints || [];
  select.innerHTML = '';
  for (const item of options) {{
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = `${{item.id}}${{item.is_default ? ' (default)' : ''}}`;
    option.disabled = !item.exists;
    select.appendChild(option);
  }}
  const fallback = options[Math.min(preferredIndex, Math.max(options.length - 1, 0))];
  select.value = previous && checkpointOptionById(previous) ? previous : (fallback ? fallback.id : defaultId || '');
  select.disabled = options.length === 0;
}}
function renderCheckpointComparison() {{
  const body = document.getElementById('checkpointCompareBody');
  const status = document.getElementById('checkpointCompareStatus');
  if (!body || !status) return;
  const rows = MiniGPTPlayground.checkpointComparison || [];
  body.innerHTML = '';
  if (!rows.length) {{
    status.textContent = 'Start scripts/serve_playground.py for checkpoint comparison.';
    return;
  }}
  const selected = selectedCheckpointOption();
  for (const item of rows) {{
    const row = document.createElement('tr');
    if (selected && item.id === selected.id) row.className = 'selected-row';
    appendCell(row, `${{item.id}}${{item.is_default ? ' (default)' : ''}}`);
    appendCell(row, item.status);
    appendCell(row, formatBytes(item.size_bytes));
    appendCell(row, item.parameter_count);
    appendCell(row, item.dataset_version);
    appendCell(row, formatDelta(item.parameter_delta));
    appendCell(row, formatDelta(item.size_delta_bytes));
    const actions = document.createElement('td');
    const actionWrap = document.createElement('div');
    actionWrap.className = 'row-actions';
    const useButton = document.createElement('button');
    useButton.type = 'button';
    useButton.textContent = 'Use';
    useButton.disabled = !item.exists;
    useButton.addEventListener('click', () => selectCheckpoint(item.id));
    const infoLink = document.createElement('a');
    infoLink.href = item.model_info_endpoint || `/api/model-info?checkpoint=${{encodeURIComponent(item.id)}}`;
    infoLink.textContent = 'Model info';
    actionWrap.appendChild(useButton);
    actionWrap.appendChild(infoLink);
    actions.appendChild(actionWrap);
    row.appendChild(actions);
    body.appendChild(row);
  }}
}}
async function loadCheckpointComparison() {{
  const status = document.getElementById('checkpointCompareStatus');
  try {{
    const response = await fetch('/api/checkpoint-compare');
    if (!response.ok) throw new Error('checkpoint comparison endpoint unavailable');
    const data = await response.json();
    MiniGPTPlayground.checkpointComparison = Array.isArray(data.checkpoints) ? data.checkpoints : [];
    const summary = data.summary || {{}};
    if (status) status.textContent = `${{formatValue(summary.ready_count)}} ready / ${{formatValue(data.checkpoint_count)}} checkpoint option(s)`;
    renderCheckpointComparison();
  }} catch (error) {{
    MiniGPTPlayground.checkpointComparison = [];
    if (status) status.textContent = 'Start scripts/serve_playground.py for checkpoint comparison.';
    renderCheckpointComparison();
  }}
}}
async function generateLive() {{
  const output = document.getElementById('liveOutput');
  const checkpoint = selectedCheckpointOption();
  const payload = {{
    prompt: document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt,
    max_new_tokens: Number(document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens),
    temperature: Number(document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature),
    top_k: Number(document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k),
    seed: Number(document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed),
  }};
  if (checkpoint) payload.checkpoint = checkpoint.id;
  output.textContent = 'Generating...';
  try {{
    const response = await fetch('/api/generate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
    }});
    const data = await response.json();
    if (!response.ok) {{
      output.textContent = data.error || 'Generation failed';
      return;
    }}
    output.textContent = data.generated || data.continuation || '';
  }} catch (error) {{
    output.textContent = 'Start scripts/serve_playground.py to use live generation.';
  }}
}}
function renderPairArtifact(artifact) {{
  const status = document.getElementById('pairArtifactStatus');
  if (!status) return;
  status.textContent = '';
  if (!artifact || !artifact.html_href) {{
    return;
  }}
  const link = document.createElement('a');
  link.href = artifact.html_href;
  link.textContent = 'Open saved pair HTML';
  link.className = 'artifact-link';
  status.appendChild(link);
  const detail = document.createElement('span');
  detail.textContent = ' (' + (artifact.json_href || artifact.json_path || 'json saved') + ')';
  status.appendChild(detail);
}}
async function generatePairLive(saveArtifact = false) {{
  const leftOutput = document.getElementById('pairLeftOutput');
  const rightOutput = document.getElementById('pairRightOutput');
  const status = document.getElementById('pairGenerateStatus');
  const artifactStatus = document.getElementById('pairArtifactStatus');
  const left = selectedCheckpointOption('pairLeftCheckpointSelect');
  const right = selectedCheckpointOption('pairRightCheckpointSelect');
  const payload = {{
    prompt: document.getElementById('promptInput').value || MiniGPTPlayground.defaults.prompt,
    max_new_tokens: Number(document.getElementById('maxTokensInput').value || MiniGPTPlayground.defaults.max_new_tokens),
    temperature: Number(document.getElementById('temperatureInput').value || MiniGPTPlayground.defaults.temperature),
    top_k: Number(document.getElementById('topKInput').value || MiniGPTPlayground.defaults.top_k),
    seed: Number(document.getElementById('seedInput').value || MiniGPTPlayground.defaults.seed),
    left_checkpoint: left ? left.id : undefined,
    right_checkpoint: right ? right.id : undefined,
  }};
  leftOutput.textContent = 'Generating...';
  rightOutput.textContent = 'Generating...';
  status.textContent = saveArtifact ? 'Generating and saving pair...' : 'Generating pair...';
  if (artifactStatus) artifactStatus.textContent = '';
  try {{
    const endpoint = saveArtifact ? '/api/generate-pair-artifact' : '/api/generate-pair';
    const response = await fetch(endpoint, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
    }});
    const data = await response.json();
    if (!response.ok) {{
      leftOutput.textContent = data.error || 'Pair generation failed';
      rightOutput.textContent = data.error || 'Pair generation failed';
      status.textContent = 'failed';
      return;
    }}
    leftOutput.textContent = data.left?.generated || data.left?.continuation || '';
    rightOutput.textContent = data.right?.generated || data.right?.continuation || '';
    const comparison = data.comparison || {{}};
    status.textContent = `same output: ${{formatValue(comparison.generated_equal)}}; char delta: ${{formatDelta(comparison.generated_char_delta)}}`;
    renderPairArtifact(data.artifact);
  }} catch (error) {{
    leftOutput.textContent = 'Start scripts/serve_playground.py to use pair generation.';
    rightOutput.textContent = 'Start scripts/serve_playground.py to use pair generation.';
    status.textContent = 'unavailable';
  }}
}}
function copyCommand(id) {{
  navigator.clipboard.writeText(document.getElementById(id).textContent);
}}
window.addEventListener('DOMContentLoaded', () => {{
  for (const id of ['promptInput', 'maxTokensInput', 'temperatureInput', 'topKInput', 'seedInput']) {{
    document.getElementById(id).addEventListener('input', buildCommands);
  }}
  document.getElementById('checkpointSelect').addEventListener('change', () => {{
    buildCommands();
    renderCheckpointComparison();
  }});
  document.getElementById('liveGenerateButton').addEventListener('click', generateLive);
  document.getElementById('pairGenerateButton').addEventListener('click', () => generatePairLive(false));
  document.getElementById('pairSaveButton').addEventListener('click', () => generatePairLive(true));
  document.getElementById('pairLeftCheckpointSelect').addEventListener('change', renderCheckpointComparison);
  document.getElementById('pairRightCheckpointSelect').addEventListener('change', renderCheckpointComparison);
  document.getElementById('refreshCheckpointCompareButton').addEventListener('click', loadCheckpointComparison);
  buildCommands();
  loadCheckpoints();
  loadCheckpointComparison();
}});
</script>"""


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
    <button id="liveGenerateButton" type="button">Generate</button>
    <output id="checkpointStatus">Checkpoint selector loads from /api/checkpoints.</output>
  </div>
  <pre id="liveOutput" class="output"></pre>
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
