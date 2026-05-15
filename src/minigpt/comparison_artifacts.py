from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def write_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(report["runs"])
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "path",
        "tokenizer",
        "dataset_version",
        "dataset_fingerprint",
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
        "token_count",
        "train_token_count",
        "val_token_count",
        "model_signature",
        "dashboard_exists",
        "baseline_name",
        "is_baseline",
        "best_val_loss_delta",
        "best_val_loss_delta_pct",
        "eval_loss_delta",
        "perplexity_delta",
        "total_parameters_delta",
        "total_parameters_ratio",
        "max_iters_delta",
        "tokenizer_changed",
        "model_signature_changed",
        "dataset_version_changed",
        "best_val_loss_relation",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for run in rows:
            row = dict(run)
            row.update(deltas.get(run.get("path"), {}))
            writer.writerow({field: row.get(field) for field in fieldnames})


def write_comparison_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    runs = list(report["runs"])
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    width = 1060
    row_h = 50
    top = 94
    height = top + max(1, len(runs)) * row_h + 104
    label_x = 28
    val_x = 250
    params_x = 640
    bar_w = 260
    values = [run.get("best_val_loss") for run in runs if run.get("best_val_loss") is not None]
    params = [run.get("total_parameters") for run in runs if run.get("total_parameters") is not None]
    max_loss = max(values) if values else 1.0
    max_params = max(params) if params else 1
    baseline = report.get("baseline", {})

    rows: list[str] = []
    for i, run in enumerate(runs):
        y = top + i * row_h
        name = html.escape(str(run.get("name")))
        loss = run.get("best_val_loss")
        param_count = run.get("total_parameters")
        delta = deltas.get(run.get("path"), {})
        relation = str(delta.get("best_val_loss_relation") or "missing")
        relation_color = "#047857" if relation == "improved" else "#b91c1c" if relation == "regressed" else "#6b7280"
        loss_bar = 0 if loss is None else max(2, int(bar_w * float(loss) / max_loss))
        param_bar = 0 if param_count is None else max(2, int(bar_w * int(param_count) / max_params))
        rows.append(f'<text x="{label_x}" y="{y + 18}" font-family="Arial" font-size="14" fill="#111827">{name}</text>')
        rows.append(f'<text x="{label_x}" y="{y + 38}" font-family="Arial" font-size="12" fill="#4b5563">{_e(run.get("model_signature"))}</text>')
        rows.append(f'<rect x="{val_x}" y="{y + 8}" width="{loss_bar}" height="14" rx="3" fill="#dc2626"/>')
        rows.append(f'<text x="{val_x + bar_w + 10}" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{_fmt(loss)} ({_fmt_signed(delta.get("best_val_loss_delta"))})</text>')
        rows.append(f'<rect x="{params_x}" y="{y + 24}" width="{param_bar}" height="14" rx="3" fill="#2563eb"/>')
        rows.append(f'<text x="{params_x + bar_w + 10}" y="{y + 37}" font-family="Arial" font-size="12" fill="#374151">{_fmt_int(param_count)} ({_fmt_ratio(delta.get("total_parameters_ratio"))})</text>')
        rows.append(f'<circle cx="{val_x - 18}" cy="{y + 15}" r="5" fill="{relation_color}"/>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT baseline model comparison</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#374151">Baseline: {_e(_pick(baseline, "name"))}. Red bars compare best validation loss; blue bars compare parameter count.</text>
  <text x="{val_x}" y="{top - 16}" font-family="Arial" font-size="13" fill="#374151">best val loss and delta</text>
  <text x="{params_x}" y="{top - 16}" font-family="Arial" font-size="13" fill="#374151">parameters and ratio</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def render_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _pick_dict(report, "summary")
    baseline = _pick_dict(report, "baseline")
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    rows = [
        "| Run | Model | Dataset | Best Val | Delta | Params | Param Ratio | Relation |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("path"), {})
        rows.append(
            "| "
            + " | ".join(
                [
                    _md(run.get("name")),
                    _md(run.get("model_signature")),
                    _md(run.get("dataset_version") or run.get("dataset_fingerprint")),
                    _md(_fmt(run.get("best_val_loss"))),
                    _md(_fmt_signed(delta.get("best_val_loss_delta"))),
                    _md(_fmt_int(run.get("total_parameters"))),
                    _md(_fmt_ratio(delta.get("total_parameters_ratio"))),
                    _md(delta.get("best_val_loss_relation")),
                ]
            )
            + " |"
        )
    recommendations = "\n".join(f"- {item}" for item in _as_str_list(report.get("recommendations")))
    return "\n".join(
        [
            "# MiniGPT baseline model comparison",
            "",
            f"- Generated at: `{report.get('generated_at')}`",
            f"- Baseline: `{baseline.get('name')}`",
            f"- Runs: `{report.get('run_count')}`",
            f"- Improved vs baseline: `{summary.get('improved_best_val_loss_count')}`",
            f"- Regressed vs baseline: `{summary.get('regressed_best_val_loss_count')}`",
            f"- Model signatures: `{summary.get('model_signature_count')}`",
            f"- Dataset versions: `{summary.get('dataset_version_count')}`",
            "",
            *rows,
            "",
            "## Recommendations",
            "",
            recommendations or "- No recommendations.",
            "",
        ]
    )


def write_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_comparison_markdown(report), encoding="utf-8")


def render_comparison_html(report: dict[str, Any]) -> str:
    summary = _pick_dict(report, "summary")
    baseline = _pick_dict(report, "baseline")
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    stats = [
        ("Baseline", baseline.get("name")),
        ("Runs", report.get("run_count")),
        ("Improved", summary.get("improved_best_val_loss_count")),
        ("Regressed", summary.get("regressed_best_val_loss_count")),
        ("Models", summary.get("model_signature_count")),
        ("Datasets", summary.get("dataset_version_count")),
    ]
    rows = []
    for run in _list_of_dicts(report.get("runs")):
        delta = deltas.get(run.get("path"), {})
        relation = str(delta.get("best_val_loss_relation") or "missing")
        relation_class = "pass" if relation == "improved" else "fail" if relation == "regressed" else "missing"
        baseline_label = " baseline" if delta.get("is_baseline") else ""
        rows.append(
            "<tr>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(run.get('model_signature'))}<br><span>{_e(run.get('tokenizer'))}</span></td>"
            f"<td>{_e(run.get('dataset_version'))}<br><span>{_e(run.get('dataset_fingerprint'))}</span></td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}<br><span>{_e(_fmt_signed(delta.get('best_val_loss_delta')))}</span></td>"
            f"<td>{_e(_fmt(run.get('eval_loss')))}<br><span>{_e(_fmt_signed(delta.get('eval_loss_delta')))}</span></td>"
            f"<td>{_e(_fmt(run.get('perplexity')))}<br><span>{_e(_fmt_signed(delta.get('perplexity_delta')))}</span></td>"
            f"<td>{_e(_fmt_int(run.get('total_parameters')))}<br><span>{_e(_fmt_ratio(delta.get('total_parameters_ratio')))}</span></td>"
            f'<td><span class="pill {relation_class}">{_e(relation + baseline_label)}</span></td>'
            "</tr>"
        )
    recommendations = "".join(f"<li>{_e(item)}</li>" for item in _as_str_list(report.get("recommendations")))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            "<title>MiniGPT baseline model comparison</title>",
            _comparison_style(),
            "</head>",
            "<body>",
            f"<header><h1>MiniGPT baseline model comparison</h1><p>Baseline: {_e(baseline.get('name'))}; generated at {_e(report.get('generated_at'))}.</p></header>",
            '<section class="stats">' + "".join(_stat_card(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Runs</h2><table><thead><tr><th>Run</th><th>Model</th><th>Dataset</th><th>Best Val</th><th>Eval</th><th>Perplexity</th><th>Params</th><th>Relation</th></tr></thead><tbody>',
            "".join(rows),
            "</tbody></table></section>",
            '<section class="panel"><h2>Recommendations</h2><ul>' + recommendations + "</ul></section>",
            "<footer>Generated by MiniGPT run comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_comparison_html(report), encoding="utf-8")


def write_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "comparison.json",
        "csv": root / "comparison.csv",
        "svg": root / "comparison.svg",
        "markdown": root / "comparison.md",
        "html": root / "comparison.html",
    }
    write_comparison_json(report, paths["json"])
    write_comparison_csv(report, paths["csv"])
    write_comparison_svg(report, paths["svg"])
    write_comparison_markdown(report, paths["markdown"])
    write_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    value = _pick(payload, key)
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = float(value)
    return f"{number:+.5g}"


def _fmt_ratio(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{float(value):.2f}x"


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _md(value: Any) -> str:
    return str(value if value is not None else "missing").replace("|", "\\|")


def _stat_card(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'


def _comparison_style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee8; --page:#f7f7f2; --panel:#ffffff; --blue:#2563eb; --green:#047857; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:30px 36px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; padding:18px 36px 0; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px 16px; min-height:78px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 36px; padding:18px; overflow:auto; }
table { width:100%; border-collapse:collapse; min-width:1080px; font-size:13px; }
th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#1f2937; background:#eef2f7; font-weight:700; }
.pill { display:inline-block; padding:4px 8px; border-radius:999px; color:#fff; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.fail { background:var(--red); }
.pill.missing { background:#6b7280; }
li { margin:6px 0; }
footer { padding:12px 36px 28px; color:var(--muted); font-size:12px; }
</style>"""
