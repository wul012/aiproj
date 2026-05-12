from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import html
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunComparison:
    name: str
    path: str
    tokenizer: str | None
    max_iters: int | None
    metrics_records: int
    best_val_loss: float | None
    last_val_loss: float | None
    eval_loss: float | None
    perplexity: float | None
    total_parameters: int | None
    n_layer: int | None
    n_head: int | None
    n_embd: int | None
    block_size: int | None
    vocab_size: int | None
    dashboard_exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_run(run_dir: str | Path, name: str | None = None) -> RunComparison:
    root = Path(run_dir)
    train_config = _read_json(root / "train_config.json")
    history_summary = _read_json(root / "history_summary.json")
    eval_report = _read_json(root / "eval_report.json")
    model_report = _read_json(root / "model_report" / "model_report.json")
    config = model_report.get("config", {}) if isinstance(model_report, dict) else {}

    return RunComparison(
        name=name or root.name,
        path=str(root),
        tokenizer=_as_str(_pick(train_config, "tokenizer") or _pick(eval_report, "tokenizer") or _pick(model_report, "tokenizer")),
        max_iters=_as_int(_pick(train_config, "max_iters")),
        metrics_records=_line_count(root / "metrics.jsonl"),
        best_val_loss=_as_float(_pick(history_summary, "best_val_loss")),
        last_val_loss=_as_float(_pick(history_summary, "last_val_loss")),
        eval_loss=_as_float(_pick(eval_report, "loss")),
        perplexity=_as_float(_pick(eval_report, "perplexity")),
        total_parameters=_as_int(_pick(model_report, "total_parameters")),
        n_layer=_as_int(_pick(config, "n_layer")),
        n_head=_as_int(_pick(config, "n_head")),
        n_embd=_as_int(_pick(config, "n_embd")),
        block_size=_as_int(_pick(config, "block_size")),
        vocab_size=_as_int(_pick(config, "vocab_size")),
        dashboard_exists=(root / "dashboard.html").exists(),
    )


def build_comparison_report(run_dirs: list[str | Path], names: list[str] | None = None) -> dict[str, Any]:
    if not run_dirs:
        raise ValueError("At least one run directory is required")
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("names length must match run_dirs length")

    runs = [
        summarize_run(run_dir, name=None if names is None else names[index])
        for index, run_dir in enumerate(run_dirs)
    ]
    report = {
        "run_count": len(runs),
        "runs": [run.to_dict() for run in runs],
        "best_by_best_val_loss": _best_run(runs, "best_val_loss"),
        "best_by_eval_loss": _best_run(runs, "eval_loss"),
        "best_by_perplexity": _best_run(runs, "perplexity"),
    }
    return report


def write_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report["runs"])
    fieldnames = [
        "name",
        "path",
        "tokenizer",
        "max_iters",
        "metrics_records",
        "best_val_loss",
        "last_val_loss",
        "eval_loss",
        "perplexity",
        "total_parameters",
        "n_layer",
        "n_head",
        "n_embd",
        "block_size",
        "vocab_size",
        "dashboard_exists",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def write_comparison_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    runs = list(report["runs"])
    width = 980
    row_h = 42
    top = 86
    height = top + max(1, len(runs)) * row_h + 92
    label_x = 28
    val_x = 230
    params_x = 590
    bar_w = 280
    values = [run.get("best_val_loss") for run in runs if run.get("best_val_loss") is not None]
    params = [run.get("total_parameters") for run in runs if run.get("total_parameters") is not None]
    max_loss = max(values) if values else 1.0
    max_params = max(params) if params else 1

    rows: list[str] = []
    for i, run in enumerate(runs):
        y = top + i * row_h
        name = html.escape(str(run.get("name")))
        loss = run.get("best_val_loss")
        param_count = run.get("total_parameters")
        loss_bar = 0 if loss is None else max(2, int(bar_w * float(loss) / max_loss))
        param_bar = 0 if param_count is None else max(2, int(bar_w * int(param_count) / max_params))
        rows.append(f'<text x="{label_x}" y="{y + 24}" font-family="Arial" font-size="14" fill="#111827">{name}</text>')
        rows.append(f'<rect x="{val_x}" y="{y + 8}" width="{loss_bar}" height="14" rx="3" fill="#dc2626"/>')
        rows.append(f'<text x="{val_x + bar_w + 10}" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{_fmt(loss)}</text>')
        rows.append(f'<rect x="{params_x}" y="{y + 24}" width="{param_bar}" height="14" rx="3" fill="#2563eb"/>')
        rows.append(f'<text x="{params_x + bar_w + 10}" y="{y + 37}" font-family="Arial" font-size="12" fill="#374151">{_fmt_int(param_count)}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT run comparison</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Red bars compare best validation loss; blue bars compare parameter count.</text>
  <text x="{val_x}" y="{top - 16}" font-family="Arial" font-size="13" fill="#374151">best val loss</text>
  <text x="{params_x}" y="{top - 16}" font-family="Arial" font-size="13" fill="#374151">parameters</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def write_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "comparison.json",
        "csv": root / "comparison.csv",
        "svg": root / "comparison.svg",
    }
    write_comparison_json(report, paths["json"])
    write_comparison_csv(report, paths["csv"])
    write_comparison_svg(report, paths["svg"])
    return {key: str(value) for key, value in paths.items()}


def _best_run(runs: list[RunComparison], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if getattr(run, field) is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda run: getattr(run, field))
    return {"name": best.name, "path": best.path, field: getattr(best, field)}


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


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
