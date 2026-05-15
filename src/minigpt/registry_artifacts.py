from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

from minigpt.registry_data import _as_optional_float, _as_str_list


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
        "best_val_loss_rank",
        "best_val_loss",
        "best_val_loss_delta",
        "is_best_val_loss",
        "last_val_loss",
        "total_parameters",
        "data_source_kind",
        "dataset_fingerprint",
        "dataset_quality",
        "eval_suite_cases",
        "eval_suite_avg_unique",
        "generation_quality_status",
        "generation_quality_cases",
        "generation_quality_pass_count",
        "generation_quality_warn_count",
        "generation_quality_fail_count",
        "generation_quality_avg_unique_ratio",
        "benchmark_scorecard_status",
        "benchmark_scorecard_score",
        "benchmark_rubric_rank",
        "benchmark_rubric_delta_from_best",
        "is_best_benchmark_rubric",
        "benchmark_rubric_status",
        "benchmark_rubric_avg_score",
        "benchmark_rubric_pass_count",
        "benchmark_rubric_warn_count",
        "benchmark_rubric_fail_count",
        "benchmark_weakest_rubric_case",
        "benchmark_weakest_rubric_score",
        "benchmark_scorecard_html_exists",
        "pair_batch_cases",
        "pair_batch_generated_differences",
        "pair_batch_html_exists",
        "pair_trend_reports",
        "pair_trend_changed_cases",
        "pair_trend_html_exists",
        "release_readiness_comparison_status",
        "release_readiness_report_count",
        "release_readiness_baseline_status",
        "release_readiness_ready_count",
        "release_readiness_blocked_count",
        "release_readiness_improved_count",
        "release_readiness_regressed_count",
        "release_readiness_changed_panel_delta_count",
        "release_readiness_html_exists",
        "artifact_count",
        "checkpoint_exists",
        "dashboard_exists",
        "note",
        "tags",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in registry["runs"]:
            writer.writerow({field: _csv_value(run.get(field)) for field in fieldnames})


def write_registry_svg(registry: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    runs = list(registry["runs"])
    width = 1040
    row_h = 70
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
        rank = run.get("best_val_loss_rank")
        delta = run.get("best_val_loss_delta")
        artifacts = int(run.get("artifact_count") or 0)
        loss_bar = 0 if loss is None else max(2, int(260 * float(loss) / max_loss))
        artifact_bar = 0 if max_artifacts == 0 else max(2, int(220 * artifacts / max_artifacts))
        quality = str(run.get("dataset_quality") or "missing")
        quality_color = "#047857" if quality == "pass" else "#b45309" if quality == "warn" else "#6b7280"
        generation_quality = str(run.get("generation_quality_status") or "missing")
        note_line = _clip(_note_summary(run), 56)
        rows.append(f'<text x="28" y="{y + 20}" font-family="Arial" font-size="14" fill="#111827">{_e(run.get("name"))}</text>')
        rows.append(f'<text x="28" y="{y + 40}" font-family="Arial" font-size="12" fill="#4b5563">{_e(_clip(run.get("path"), 38))}</text>')
        rows.append(f'<text x="242" y="{y + 21}" font-family="Arial" font-size="13" fill="#111827">{_e(_rank_label(rank))}</text>')
        rows.append(f'<rect x="300" y="{y + 9}" width="{loss_bar}" height="14" rx="3" fill="#dc2626"/>')
        rows.append(f'<text x="568" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{_e(_fmt(loss))} ({_e(_fmt_delta(delta))})</text>')
        rows.append(f'<rect x="650" y="{y + 9}" width="{artifact_bar}" height="14" rx="3" fill="#2563eb"/>')
        rows.append(f'<text x="880" y="{y + 21}" font-family="Arial" font-size="12" fill="#374151">{artifacts} files</text>')
        rows.append(f'<circle cx="656" cy="{y + 38}" r="5" fill="{quality_color}"/>')
        rows.append(f'<text x="670" y="{y + 42}" font-family="Arial" font-size="12" fill="#374151">{_e(quality)} | eval={_e(run.get("eval_suite_cases"))} | gen={_e(generation_quality)} | data={_e(run.get("dataset_fingerprint"))}</text>')
        rows.append(f'<text x="670" y="{y + 60}" font-family="Arial" font-size="12" fill="#4b5563">{_e(note_line)}</text>')
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


def write_registry_html(registry: dict[str, Any], path: str | Path, title: str = "MiniGPT run registry") -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from minigpt.registry_render import render_registry_html

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


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_delta(value: Any) -> str:
    number = _as_optional_float(value)
    if number is None:
        return "delta missing"
    return f"{number:+.5g}"


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _note_summary(run: dict[str, Any]) -> str:
    tags = _fmt_tags(run.get("tags"))
    note = str(run.get("note") or "")
    if tags and note:
        return f"{tags}: {note}"
    return tags or note or "no notes"


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _fmt_tags(value: Any) -> str:
    tags = value if isinstance(value, list) else _as_str_list(value)
    return ", ".join(str(tag) for tag in tags)


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "write_registry_csv",
    "write_registry_html",
    "write_registry_json",
    "write_registry_outputs",
    "write_registry_svg",
]
