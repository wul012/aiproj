from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any

from minigpt.data_prep import build_dataset_report, build_prepared_dataset
from minigpt.data_quality import build_dataset_quality_report


SCALE_TIERS = [
    ("tiny", 2_000),
    ("small", 20_000),
    ("medium", 200_000),
    ("large", None),
]


def build_training_scale_plan(
    sources: list[str | Path],
    *,
    project_root: str | Path | None = None,
    out_root: str | Path = "runs/training-scale-plan",
    batch_out_root: str | Path | None = None,
    dataset_name: str = "portfolio-zh",
    dataset_version_prefix: str = "v70",
    dataset_description: str = "MiniGPT corpus planned for scale-aware training.",
    recursive: bool = True,
    max_variants: int = 3,
    python_executable: str = "python",
    sample_prompt: str = "MiniGPT",
    generated_at: str | None = None,
    title: str = "MiniGPT training scale plan",
) -> dict[str, Any]:
    if max_variants < 1:
        raise ValueError("max_variants must be at least 1")
    dataset = build_prepared_dataset(sources, recursive=recursive)
    dataset_report = build_dataset_report(dataset)
    quality = build_dataset_quality_report(dataset)
    tier = scale_tier(dataset.char_count)
    out = Path(out_root)
    root = Path(project_root) if project_root is not None else Path.cwd()
    batch_out = Path(batch_out_root) if batch_out_root is not None else out.parent / "training-portfolio-batch-from-scale-plan"
    variants = _recommended_variants(
        tier,
        char_count=dataset.char_count,
        dataset_name=dataset_name,
        dataset_version_prefix=dataset_version_prefix,
        dataset_description=dataset_description,
        sample_prompt=sample_prompt,
    )[:max_variants]
    matrix = [_variant_matrix_row(item, dataset.char_count, tier) for item in variants]
    variants_path = out / "training_scale_variants.json"
    command = [
        python_executable,
        str(root / "scripts" / "run_training_portfolio_batch.py"),
        *[str(Path(source)) for source in sources],
        "--variants",
        str(variants_path),
        "--out-root",
        str(batch_out),
        "--dataset-name",
        dataset_name,
        "--baseline",
        str(variants[0]["name"]),
    ]
    report = {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "project_root": str(root),
        "out_root": str(out),
        "sources": [str(Path(source)) for source in sources],
        "recursive": bool(recursive),
        "dataset": {
            "name": dataset_name,
            "version_prefix": dataset_version_prefix,
            "description": dataset_description,
            "source_count": dataset_report["source_count"],
            "char_count": dataset_report["char_count"],
            "line_count": dataset_report["line_count"],
            "unique_char_count": dataset_report["unique_char_count"],
            "unique_char_ratio": quality.get("unique_char_ratio"),
            "fingerprint": dataset_report["fingerprint"],
            "short_fingerprint": str(dataset_report["fingerprint"])[:12],
            "scale_tier": tier,
            "quality_status": quality.get("status"),
            "warning_count": quality.get("warning_count"),
            "issue_count": quality.get("issue_count"),
            "duplicate_line_count": quality.get("duplicate_line_count"),
        },
        "sources_detail": dataset_report["sources"],
        "quality_issues": quality.get("issues", []),
        "variants": variants,
        "variant_matrix": matrix,
        "batch": {
            "variants_path": str(variants_path),
            "out_root": str(batch_out),
            "baseline": variants[0]["name"],
            "command": command,
        },
        "recommendations": _recommendations(tier, quality, matrix),
    }
    return report


def scale_tier(char_count: int) -> str:
    if char_count < 0:
        raise ValueError("char_count cannot be negative")
    for name, limit in SCALE_TIERS:
        if limit is None or char_count < limit:
            return name
    return "large"


def write_training_scale_plan_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_scale_variants_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": report.get("generated_at"),
        "source": "training_scale_plan",
        "dataset": report.get("dataset", {}),
        "variants": list(report.get("variants", [])),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_training_scale_plan_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "name",
        "scale_tier",
        "dataset_version",
        "max_iters",
        "eval_interval",
        "batch_size",
        "block_size",
        "n_layer",
        "n_head",
        "n_embd",
        "seed",
        "token_budget",
        "corpus_pass_estimate",
        "description",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(report.get("variant_matrix")):
            writer.writerow({key: row.get(key) for key in fieldnames})


def render_training_scale_plan_markdown(report: dict[str, Any]) -> str:
    dataset = _dict(report.get("dataset"))
    batch = _dict(report.get("batch"))
    lines = [
        f"# {report.get('title', 'MiniGPT training scale plan')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Scale tier: `{dataset.get('scale_tier')}`",
        f"- Dataset: `{dataset.get('name')}` / `{dataset.get('version_prefix')}`",
        f"- Sources: `{dataset.get('source_count')}`",
        f"- Characters: `{dataset.get('char_count')}`",
        f"- Quality: `{dataset.get('quality_status')}` with `{dataset.get('warning_count')}` warnings",
        f"- Variants file: `{batch.get('variants_path')}`",
        "",
        "## Variant Matrix",
        "",
        "| Variant | Config | Token budget | Corpus passes | Purpose |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in _list_of_dicts(report.get("variant_matrix")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("name")),
                    _md(_config_label(row)),
                    _md(row.get("token_budget")),
                    _md(row.get("corpus_pass_estimate")),
                    _md(row.get("description")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Batch Command",
            "",
            f"`{_display_command(batch.get('command'))}`",
            "",
            "## Recommendations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    issues = _list_of_dicts(report.get("quality_issues"))
    if issues:
        lines.extend(["", "## Quality Issues", ""])
        for issue in issues[:8]:
            lines.append(f"- `{issue.get('code')}`: {issue.get('message')}")
    return "\n".join(lines).rstrip() + "\n"


def write_training_scale_plan_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_plan_markdown(report), encoding="utf-8")


def render_training_scale_plan_html(report: dict[str, Any]) -> str:
    dataset = _dict(report.get("dataset"))
    batch = _dict(report.get("batch"))
    stats = [
        ("Scale", dataset.get("scale_tier")),
        ("Sources", dataset.get("source_count")),
        ("Chars", dataset.get("char_count")),
        ("Lines", dataset.get("line_count")),
        ("Unique ratio", dataset.get("unique_char_ratio")),
        ("Quality", dataset.get("quality_status")),
        ("Warnings", dataset.get("warning_count")),
        ("Variants", len(_list_of_dicts(report.get("variants")))),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT training scale plan'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT training scale plan'))}</h1><p>{_e(dataset.get('name'))} / {_e(dataset.get('version_prefix'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _variant_table(report),
            _batch_panel(batch),
            _list_section("Recommendations", report.get("recommendations")),
            _quality_section(report),
            "<footer>Generated by MiniGPT training scale planner.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_training_scale_plan_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_training_scale_plan_html(report), encoding="utf-8")


def write_training_scale_plan_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "training_scale_plan.json",
        "variants": root / "training_scale_variants.json",
        "csv": root / "training_scale_plan.csv",
        "markdown": root / "training_scale_plan.md",
        "html": root / "training_scale_plan.html",
    }
    write_training_scale_plan_json(report, paths["json"])
    write_training_scale_variants_json(report, paths["variants"])
    write_training_scale_plan_csv(report, paths["csv"])
    write_training_scale_plan_markdown(report, paths["markdown"])
    write_training_scale_plan_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _recommended_variants(
    tier: str,
    *,
    char_count: int,
    dataset_name: str,
    dataset_version_prefix: str,
    dataset_description: str,
    sample_prompt: str,
) -> list[dict[str, Any]]:
    rows = [
        _variant(
            "scale-smoke",
            "Fast smoke run for checking the corpus and pipeline before spending time on training.",
            dataset_name,
            f"{dataset_version_prefix}-smoke",
            dataset_description,
            max_iters=50,
            eval_interval=25,
            eval_iters=5,
            batch_size=8,
            block_size=64,
            n_layer=2,
            n_head=2,
            n_embd=64,
            seed=1337,
            sample_prompt=sample_prompt,
            sample_tokens=40,
        ),
        _variant(
            "scale-baseline",
            "Baseline capacity run for comparing whether the corpus supports real improvement.",
            dataset_name,
            f"{dataset_version_prefix}-baseline",
            dataset_description,
            max_iters=150 if tier in {"tiny", "small"} else 220,
            eval_interval=50,
            eval_iters=10,
            batch_size=16,
            block_size=96,
            n_layer=2,
            n_head=2,
            n_embd=96,
            seed=2026,
            sample_prompt=sample_prompt,
            sample_tokens=50,
        ),
    ]
    if tier in {"medium", "large"}:
        rows.append(
            _variant(
                "scale-extended",
                "Larger context and embedding run for medium or larger corpora after the smoke pass is healthy.",
                dataset_name,
                f"{dataset_version_prefix}-extended",
                dataset_description,
                max_iters=360 if tier == "medium" else 500,
                eval_interval=60,
                eval_iters=15,
                batch_size=24,
                block_size=128,
                n_layer=3,
                n_head=4,
                n_embd=128,
                seed=4096,
                sample_prompt=sample_prompt,
                sample_tokens=64,
            )
        )
    return _fit_variant_contexts(rows, char_count)


def _variant(
    name: str,
    description: str,
    dataset_name: str,
    dataset_version: str,
    dataset_description: str,
    **config: Any,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "run_name": name,
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "dataset_description": dataset_description,
        "device": "cpu",
        "title": f"MiniGPT training portfolio pipeline ({name})",
        "learning_rate": 3e-4,
        **config,
    }


def _fit_variant_contexts(variants: list[dict[str, Any]], char_count: int) -> list[dict[str, Any]]:
    fitted = []
    for variant in variants:
        item = dict(variant)
        requested = int(item.get("block_size") or 1)
        adjusted = safe_block_size_for_char_count(char_count, requested)
        if adjusted < requested:
            item["block_size"] = adjusted
            item["context_adjustment"] = (
                f"block_size reduced from {requested} to {adjusted} "
                "so the default 90/10 train/val split can produce batches."
            )
        fitted.append(item)
    return fitted


def safe_block_size_for_char_count(char_count: int, requested: int, train_ratio: float = 0.9) -> int:
    if char_count < 0:
        raise ValueError("char_count cannot be negative")
    if requested < 1:
        raise ValueError("requested block_size must be at least 1")
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0 and 1")

    split_idx = max(1, int(char_count * train_ratio))
    val_count = char_count - split_idx
    effective_eval_count = val_count if val_count >= 2 else split_idx
    max_block_size = max(1, effective_eval_count - 2)
    if max_block_size >= 16:
        max_block_size = max(16, (max_block_size // 8) * 8)
    return min(requested, max_block_size)


def _variant_matrix_row(variant: dict[str, Any], char_count: int, tier: str) -> dict[str, Any]:
    token_budget = int(variant["batch_size"]) * int(variant["block_size"]) * int(variant["max_iters"])
    passes = round(token_budget / max(1, char_count), 3)
    return {
        "name": variant.get("name"),
        "description": variant.get("description"),
        "scale_tier": tier,
        "dataset_version": variant.get("dataset_version"),
        "max_iters": variant.get("max_iters"),
        "eval_interval": variant.get("eval_interval"),
        "batch_size": variant.get("batch_size"),
        "block_size": variant.get("block_size"),
        "context_adjustment": variant.get("context_adjustment"),
        "n_layer": variant.get("n_layer"),
        "n_head": variant.get("n_head"),
        "n_embd": variant.get("n_embd"),
        "seed": variant.get("seed"),
        "token_budget": token_budget,
        "corpus_pass_estimate": passes,
    }


def _recommendations(tier: str, quality: dict[str, Any], matrix: list[dict[str, Any]]) -> list[str]:
    recommendations = [
        "Run the smoke variant first, then hand the generated training_scale_variants.json to the v69 batch runner.",
    ]
    if tier == "tiny":
        recommendations.append("The corpus is tiny; treat loss curves and samples as pipeline evidence, not model capability evidence.")
    elif tier == "small":
        recommendations.append("The corpus is small; compare baseline runs, but collect more Chinese text before trusting capability changes.")
    elif tier == "medium":
        recommendations.append("The corpus is medium-sized; run smoke and baseline before the extended variant.")
    else:
        recommendations.append("The corpus is large enough for staged runs; keep the smoke pass as a release gate before expensive variants.")
    if int(quality.get("warning_count") or 0) > 0:
        recommendations.append("Inspect dataset quality warnings before executing the extended training variant.")
    if any(row.get("context_adjustment") for row in matrix):
        recommendations.append("At least one block_size was reduced so tiny corpora can pass the training split.")
    if matrix:
        best = max(matrix, key=lambda row: int(row.get("token_budget") or 0))
        recommendations.append(
            f"The largest planned token budget is {best.get('token_budget')} tokens in `{best.get('name')}`."
        )
    return recommendations


def _variant_table(report: dict[str, Any]) -> str:
    rows = []
    for row in _list_of_dicts(report.get("variant_matrix")):
        rows.append(
            "<tr>"
            f"<td>{_e(row.get('name'))}</td>"
            f"<td>{_e(_config_label(row))}</td>"
            f"<td>{_e(row.get('token_budget'))}</td>"
            f"<td>{_e(row.get('corpus_pass_estimate'))}</td>"
            f"<td>{_e(row.get('description'))}</td>"
            "</tr>"
        )
    return (
        '<section><h2>Variant Matrix</h2><div class="table-wrap"><table>'
        "<thead><tr><th>Variant</th><th>Config</th><th>Token budget</th><th>Corpus passes</th><th>Purpose</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div></section>"
    )


def _batch_panel(batch: dict[str, Any]) -> str:
    return (
        "<section><h2>Batch Handoff</h2>"
        f"<p><strong>Variants:</strong> {_e(batch.get('variants_path'))}</p>"
        f"<p><strong>Out root:</strong> {_e(batch.get('out_root'))}</p>"
        f"<pre>{_e(_display_command(batch.get('command')))}</pre>"
        "</section>"
    )


def _quality_section(report: dict[str, Any]) -> str:
    issues = _list_of_dicts(report.get("quality_issues"))
    if not issues:
        return "<section><h2>Quality Issues</h2><p>No quality issues found.</p></section>"
    rows = []
    for issue in issues[:8]:
        rows.append(
            "<li>"
            f"<strong>{_e(issue.get('code'))}</strong>: {_e(issue.get('message'))}"
            "</li>"
        )
    return f"<section><h2>Quality Issues</h2><ul>{''.join(rows)}</ul></section>"


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return ""
    return f"<section><h2>{_e(title)}</h2><ul>{''.join(f'<li>{_e(item)}</li>' for item in values)}</ul></section>"


def _style() -> str:
    return """<style>
:root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; background: #f6f7f2; color: #172026; }
body { margin: 0; padding: 28px; }
header, section, footer { max-width: 1120px; margin: 0 auto 18px; }
header { border-bottom: 1px solid #d7dccf; padding-bottom: 18px; }
h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: 0; }
h2 { font-size: 18px; margin: 0 0 12px; letter-spacing: 0; }
p { color: #4f5d52; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.card, section { background: #ffffff; border: 1px solid #d9ded7; border-radius: 8px; padding: 14px; box-shadow: 0 1px 2px rgba(23, 32, 38, 0.05); }
.card span { display: block; color: #667366; font-size: 12px; }
.card strong { display: block; margin-top: 6px; font-size: 16px; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 760px; }
th, td { text-align: left; border-bottom: 1px solid #e3e7df; padding: 9px; vertical-align: top; }
th { color: #435047; font-size: 12px; text-transform: uppercase; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; background: #172026; color: #f7faf2; border-radius: 8px; padding: 12px; }
li { margin: 7px 0; }
footer { color: #69756a; font-size: 12px; }
</style>"""


def _card(label: str, value: Any) -> str:
    return f'<div class="card"><span>{_e(label)}</span><strong>{_e(value)}</strong></div>'


def _config_label(row: dict[str, Any]) -> str:
    return (
        f"iters={row.get('max_iters')}, batch={row.get('batch_size')}, block={row.get('block_size')}, "
        f"layers={row.get('n_layer')}, heads={row.get('n_head')}, embd={row.get('n_embd')}, seed={row.get('seed')}"
    )


def _display_command(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(part) for part in value)
    return "" if value is None else str(value)


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
