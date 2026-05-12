from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import html
import json
import os
from pathlib import Path
from typing import Any


REGISTRY_ARTIFACT_PATHS = [
    "checkpoint.pt",
    "tokenizer.json",
    "train_config.json",
    "metrics.jsonl",
    "history_summary.json",
    "loss_curve.svg",
    "prepared_corpus.txt",
    "run_manifest.json",
    "run_manifest.svg",
    "dataset_report.json",
    "dataset_report.svg",
    "dataset_quality.json",
    "dataset_quality.svg",
    "eval_suite/eval_suite.json",
    "eval_suite/eval_suite.csv",
    "eval_suite/eval_suite.svg",
    "sample.txt",
    "eval_report.json",
    "dashboard.html",
    "playground.html",
]


@dataclass(frozen=True)
class RegisteredRun:
    name: str
    path: str
    git_commit: str | None
    git_dirty: bool | None
    tokenizer: str | None
    max_iters: int | None
    best_val_loss: float | None
    last_val_loss: float | None
    total_parameters: int | None
    data_source_kind: str | None
    dataset_fingerprint: str | None
    dataset_quality: str | None
    eval_suite_cases: int | None
    eval_suite_avg_unique: float | None
    artifact_count: int
    checkpoint_exists: bool
    dashboard_exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def discover_run_dirs(root: str | Path, recursive: bool = True) -> list[Path]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(base)
    if base.is_file():
        raise ValueError(f"run discovery root must be a directory: {base}")
    candidates = base.rglob("run_manifest.json") if recursive else base.glob("*/run_manifest.json")
    runs = sorted({path.parent.resolve(): path.parent for path in candidates}.values(), key=lambda item: str(item))
    return runs


def summarize_registered_run(run_dir: str | Path, name: str | None = None) -> RegisteredRun:
    root = Path(run_dir)
    manifest = _read_json(root / "run_manifest.json")
    train_config = _read_json(root / "train_config.json")
    history = _read_json(root / "history_summary.json")
    dataset_quality = _read_json(root / "dataset_quality.json")
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json")

    git = _pick_dict(manifest, "git")
    training = _pick_dict(manifest, "training")
    data = _pick_dict(manifest, "data")
    model = _pick_dict(manifest, "model")
    manifest_quality = _pick_dict(data, "dataset_quality")
    source = _pick_dict(data, "source")
    artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
    manifest_artifact_count = sum(1 for item in artifacts if isinstance(item, dict) and item.get("exists"))
    artifact_count = max(manifest_artifact_count, _actual_artifact_count(root))

    return RegisteredRun(
        name=name or root.name,
        path=str(root),
        git_commit=_as_str(_pick(git, "short_commit")),
        git_dirty=_as_bool(_pick(git, "dirty")),
        tokenizer=_as_str(_pick(training, "tokenizer") or _pick(train_config, "tokenizer")),
        max_iters=_as_int(_pick(train_config, "max_iters") or _nested_pick(training, "args", "max_iters")),
        best_val_loss=_as_float(_pick(history, "best_val_loss") or _nested_pick(_pick_dict(manifest, "results"), "history_summary", "best_val_loss")),
        last_val_loss=_as_float(_pick(history, "last_val_loss") or _nested_pick(_pick_dict(manifest, "results"), "history_summary", "last_val_loss")),
        total_parameters=_as_int(_pick(model, "parameter_count")),
        data_source_kind=_as_str(_pick(source, "kind")),
        dataset_fingerprint=_as_str(_pick(dataset_quality, "short_fingerprint") or _pick(manifest_quality, "short_fingerprint")),
        dataset_quality=_as_str(_pick(dataset_quality, "status") or _pick(manifest_quality, "status")),
        eval_suite_cases=_as_int(_pick(eval_suite, "case_count")),
        eval_suite_avg_unique=_as_float(_pick(eval_suite, "avg_unique_chars")),
        artifact_count=artifact_count,
        checkpoint_exists=(root / "checkpoint.pt").exists(),
        dashboard_exists=(root / "dashboard.html").exists(),
    )


def build_run_registry(run_dirs: list[str | Path], names: list[str] | None = None) -> dict[str, Any]:
    if not run_dirs:
        raise ValueError("at least one run directory is required")
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("names length must match run_dirs length")
    runs = [
        summarize_registered_run(run_dir, None if names is None else names[index])
        for index, run_dir in enumerate(run_dirs)
    ]
    return {
        "schema_version": 1,
        "run_count": len(runs),
        "runs": [run.to_dict() for run in runs],
        "best_by_best_val_loss": _best_by(runs, "best_val_loss"),
        "dataset_fingerprints": sorted({run.dataset_fingerprint for run in runs if run.dataset_fingerprint}),
        "quality_counts": _counts(run.dataset_quality or "missing" for run in runs),
    }


def write_registry_json(registry: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def write_registry_csv(registry: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "path",
        "git_commit",
        "git_dirty",
        "tokenizer",
        "max_iters",
        "best_val_loss",
        "last_val_loss",
        "total_parameters",
        "data_source_kind",
        "dataset_fingerprint",
        "dataset_quality",
        "eval_suite_cases",
        "eval_suite_avg_unique",
        "artifact_count",
        "checkpoint_exists",
        "dashboard_exists",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in registry["runs"]:
            writer.writerow({field: run.get(field) for field in fieldnames})


def write_registry_svg(registry: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    runs = list(registry["runs"])
    width = 1040
    row_h = 54
    top = 94
    height = top + max(1, len(runs)) * row_h + 68
    loss_values = [run.get("best_val_loss") for run in runs if run.get("best_val_loss") is not None]
    artifact_values = [run.get("artifact_count") for run in runs if run.get("artifact_count") is not None]
    max_loss = max(loss_values) if loss_values else 1.0
    max_artifacts = max(artifact_values) if artifact_values else 1
    rows = []
    for index, run in enumerate(runs):
        y = top + index * row_h
        loss = run.get("best_val_loss")
        artifacts = int(run.get("artifact_count") or 0)
        loss_bar = 0 if loss is None else max(2, int(260 * float(loss) / max_loss))
        artifact_bar = 0 if max_artifacts == 0 else max(2, int(220 * artifacts / max_artifacts))
        quality = str(run.get("dataset_quality") or "missing")
        quality_color = "#047857" if quality == "pass" else "#b45309" if quality == "warn" else "#6b7280"
        rows.append(f'<text x="28" y="{y + 20}" font-family="Arial" font-size="14" fill="#111827">{_e(run.get("name"))}</text>')
        rows.append(f'<text x="28" y="{y + 40}" font-family="Arial" font-size="12" fill="#4b5563">{_e(_clip(run.get("path"), 38))}</text>')
        rows.append(f'<rect x="300" y="{y + 9}" width="{loss_bar}" height="14" rx="3" fill="#dc2626"/>')
        rows.append(f'<text x="568" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{_fmt(loss)}</text>')
        rows.append(f'<rect x="650" y="{y + 9}" width="{artifact_bar}" height="14" rx="3" fill="#2563eb"/>')
        rows.append(f'<text x="880" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{artifacts} files</text>')
        rows.append(f'<circle cx="656" cy="{y + 38}" r="5" fill="{quality_color}"/>')
        rows.append(f'<text x="670" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">{_e(quality)} | eval={_e(run.get("eval_suite_cases"))} | data={_e(run.get("dataset_fingerprint"))}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="28" y="34" font-family="Arial" font-size="22" fill="#111827">MiniGPT run registry</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#4b5563">Runs: {registry.get('run_count')} | Dataset fingerprints: {len(registry.get('dataset_fingerprints', []))}</text>
  <text x="300" y="78" font-family="Arial" font-size="12" fill="#374151">best val loss</text>
  <text x="650" y="78" font-family="Arial" font-size="12" fill="#374151">artifact count / quality / eval suite</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_registry_html(
    registry: dict[str, Any],
    *,
    title: str = "MiniGPT run registry",
    base_dir: str | Path | None = None,
) -> str:
    runs = list(registry.get("runs", []))
    best = registry.get("best_by_best_val_loss") if isinstance(registry.get("best_by_best_val_loss"), dict) else {}
    quality_counts = registry.get("quality_counts", {})
    stats = [
        ("Runs", registry.get("run_count")),
        ("Best run", _pick(best, "name")),
        ("Best val", _fmt(_pick(best, "best_val_loss"))),
        ("Fingerprints", len(registry.get("dataset_fingerprints", []))),
        ("Quality", ", ".join(f"{key}:{value}" for key, value in quality_counts.items()) if isinstance(quality_counts, dict) else None),
    ]
    rows = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        quality = str(run.get("dataset_quality") or "missing")
        quality_class = "pass" if quality == "pass" else "warn" if quality == "warn" else "missing"
        links = _registry_links(run, base_dir)
        rows.append(
            '<tr data-run-row'
            f' data-search="{_e(_row_search_text(run))}"'
            f' data-quality="{_e(quality)}"'
            f' data-name="{_e(run.get("name"))}"'
            f' data-best-val="{_e(_sort_number(run.get("best_val_loss")))}"'
            f' data-params="{_e(_sort_number(run.get("total_parameters")))}"'
            f' data-artifacts="{_e(_sort_number(run.get("artifact_count")))}"'
            f' data-eval="{_e(_sort_number(run.get("eval_suite_cases")))}">'
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}</td>"
            f"<td>{_e(_fmt_int(run.get('total_parameters')))}</td>"
            f"<td>{_e(run.get('git_commit'))}<br><span>dirty={_e(run.get('git_dirty'))}</span></td>"
            f"<td>{_e(run.get('data_source_kind'))}<br><span>{_e(run.get('dataset_fingerprint'))}</span></td>"
            f'<td><span class="pill {quality_class}">{_e(quality)}</span></td>'
            f"<td>{_e(run.get('eval_suite_cases'))}<br><span>avg unique={_e(run.get('eval_suite_avg_unique'))}</span></td>"
            f"<td>{_e(run.get('artifact_count'))}</td>"
            f"<td>{links}</td>"
            "</tr>"
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(title)}</title>",
            _registry_style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(title)}</h1><p>Experiment index generated from MiniGPT run directories.</p></header>",
            '<section class="stats">' + "".join(_stat_card(label, value) for label, value in stats) + "</section>",
            _registry_controls(runs),
            '<section class="panel">',
            "<h2>Runs</h2>",
            '<table id="registry-table">',
            "<thead><tr><th>Run</th><th>Best Val</th><th>Params</th><th>Git</th><th>Data</th><th>Quality</th><th>Eval</th><th>Artifacts</th><th>Links</th></tr></thead>",
            '<tbody id="registry-rows">',
            "".join(rows),
            "</tbody>",
            "</table>",
            "</section>",
            '<section class="panel">',
            "<h2>Dataset Fingerprints</h2>",
            "<pre>" + _e(json.dumps(registry.get("dataset_fingerprints", []), ensure_ascii=False, indent=2)) + "</pre>",
            "</section>",
            "<footer>Generated by MiniGPT registry exporter.</footer>",
            _registry_script(),
            "</body>",
            "</html>",
        ]
    )


def write_registry_html(registry: dict[str, Any], path: str | Path, title: str = "MiniGPT run registry") -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_registry_html(registry, title=title, base_dir=out_path.parent), encoding="utf-8")


def write_registry_outputs(registry: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "registry.json",
        "csv": root / "registry.csv",
        "svg": root / "registry.svg",
        "html": root / "registry.html",
    }
    write_registry_json(registry, paths["json"])
    write_registry_csv(registry, paths["csv"])
    write_registry_svg(registry, paths["svg"])
    write_registry_html(registry, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _actual_artifact_count(root: Path) -> int:
    return sum(1 for relative in REGISTRY_ARTIFACT_PATHS if (root / relative).exists())


def _best_by(runs: list[RegisteredRun], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if getattr(run, field) is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda run: getattr(run, field))
    return {"name": best.name, "path": best.path, field: getattr(best, field)}


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    nested = _pick(payload, key)
    return nested if isinstance(nested, dict) else {}


def _nested_pick(payload: Any, section: str, key: str) -> Any:
    nested = _pick(payload, section)
    return _pick(nested, key)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def _sort_number(value: Any) -> str:
    if value is None:
        return ""
    return str(float(value))


def _row_search_text(run: dict[str, Any]) -> str:
    keys = [
        "name",
        "path",
        "git_commit",
        "tokenizer",
        "data_source_kind",
        "dataset_fingerprint",
        "dataset_quality",
    ]
    return " ".join(str(run.get(key) or "") for key in keys).lower()


def _registry_controls(runs: list[Any]) -> str:
    qualities = sorted({str(run.get("dataset_quality") or "missing") for run in runs if isinstance(run, dict)})
    quality_options = ['<option value="">All</option>'] + [
        f'<option value="{_e(quality)}">{_e(quality)}</option>' for quality in qualities
    ]
    return (
        '<section class="toolbar" aria-label="Registry controls">'
        '<label><span>Search</span><input id="registry-search" type="search" placeholder="run, commit, data, path"></label>'
        '<label><span>Quality</span><select id="quality-filter">'
        + "".join(quality_options)
        + "</select></label>"
        '<label><span>Sort</span><select id="sort-key">'
        '<option value="bestVal">Best Val</option>'
        '<option value="name">Name</option>'
        '<option value="artifacts">Artifacts</option>'
        '<option value="eval">Eval Cases</option>'
        '<option value="params">Params</option>'
        "</select></label>"
        '<button id="sort-direction" type="button" aria-pressed="false">Asc</button>'
        '<output id="registry-count" for="registry-search quality-filter sort-key">0 / 0</output>'
        "</section>"
    )


def _registry_links(run: dict[str, Any], base_dir: str | Path | None) -> str:
    root = Path(str(run.get("path", "")))
    specs = [
        ("dashboard", root / "dashboard.html"),
        ("manifest", root / "run_manifest.json"),
        ("eval", root / "eval_suite" / "eval_suite.json"),
    ]
    links = []
    for label, path in specs:
        if path.exists():
            href = _href(path, base_dir)
            links.append(f'<a href="{_e(href)}">{_e(label)}</a>')
    return " ".join(links) if links else '<span class="muted">missing</span>'


def _href(path: Path, base_dir: str | Path | None) -> str:
    if base_dir is None:
        return path.as_posix()
    try:
        return Path(os.path.relpath(path, Path(base_dir))).as_posix()
    except ValueError:
        return path.as_posix()


def _stat_card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _registry_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.toolbar { display:grid; grid-template-columns:minmax(220px, 1fr) 160px 160px 74px 90px; gap:10px; align-items:end; padding:14px 32px 0; }
.toolbar label { display:flex; flex-direction:column; gap:5px; color:var(--muted); font-size:12px; text-transform:uppercase; }
.toolbar input, .toolbar select, .toolbar button, .toolbar output { width:100%; min-height:38px; border:1px solid var(--line); border-radius:8px; background:#fff; color:var(--ink); font:inherit; }
.toolbar input, .toolbar select { padding:7px 9px; }
.toolbar button { cursor:pointer; font-weight:700; }
.toolbar output { display:flex; align-items:center; justify-content:center; color:var(--muted); }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:900px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; margin-right:8px; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.missing { background:#6b7280; }
pre { margin:0; white-space:pre-wrap; background:#f3f4f6; padding:12px; border-radius:8px; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats, .toolbar { padding-left:16px; padding-right:16px; } .toolbar { grid-template-columns:1fr 1fr; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _registry_script() -> str:
    return """<script>
(() => {
  const rows = Array.from(document.querySelectorAll("[data-run-row]"));
  const search = document.getElementById("registry-search");
  const quality = document.getElementById("quality-filter");
  const sortKey = document.getElementById("sort-key");
  const direction = document.getElementById("sort-direction");
  const count = document.getElementById("registry-count");
  const numericKeys = new Set(["bestVal", "params", "artifacts", "eval"]);
  let ascending = true;

  const numberCompare = (a, b, key) => {
    const av = a.dataset[key] || "";
    const bv = b.dataset[key] || "";
    if (!av && !bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    const delta = Number(av) - Number(bv);
    return ascending ? delta : -delta;
  };

  const textCompare = (a, b, key) => {
    const delta = (a.dataset[key] || "").localeCompare(b.dataset[key] || "", undefined, { numeric: true });
    return ascending ? delta : -delta;
  };

  const apply = () => {
    const query = (search.value || "").trim().toLowerCase();
    const wantedQuality = quality.value;
    const visible = [];
    rows.forEach((row) => {
      const matchesQuery = !query || (row.dataset.search || "").includes(query);
      const matchesQuality = !wantedQuality || row.dataset.quality === wantedQuality;
      const shown = matchesQuery && matchesQuality;
      row.hidden = !shown;
      if (shown) visible.push(row);
    });
    const key = sortKey.value;
    visible
      .sort((a, b) => numericKeys.has(key) ? numberCompare(a, b, key) : textCompare(a, b, key))
      .forEach((row) => row.parentElement.appendChild(row));
    count.value = `${visible.length} / ${rows.length}`;
  };

  search.addEventListener("input", apply);
  quality.addEventListener("change", apply);
  sortKey.addEventListener("change", apply);
  direction.addEventListener("click", () => {
    ascending = !ascending;
    direction.textContent = ascending ? "Asc" : "Desc";
    direction.setAttribute("aria-pressed", String(!ascending));
    apply();
  });
  apply();
})();
</script>"""


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
