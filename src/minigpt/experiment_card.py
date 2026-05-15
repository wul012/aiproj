from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    utc_now,
    write_json_payload,
)


CARD_ARTIFACT_PATHS = [
    ("checkpoint", "checkpoint.pt", "model checkpoint"),
    ("tokenizer", "tokenizer.json", "tokenizer metadata"),
    ("train_config", "train_config.json", "training configuration"),
    ("history_summary", "history_summary.json", "training loss summary"),
    ("dataset_report", "dataset_report.json", "dataset source report"),
    ("dataset_quality", "dataset_quality.json", "dataset quality report"),
    ("eval_suite", "eval_suite/eval_suite.json", "fixed prompt evaluation suite"),
    ("run_manifest", "run_manifest.json", "reproducibility manifest"),
    ("dashboard", "dashboard.html", "static dashboard"),
    ("playground", "playground.html", "static playground"),
    ("experiment_card_json", "experiment_card.json", "machine-readable experiment card"),
    ("experiment_card_md", "experiment_card.md", "markdown experiment card"),
    ("experiment_card_html", "experiment_card.html", "browser experiment card"),
]

def build_experiment_card(
    run_dir: str | Path,
    *,
    registry_path: str | Path | None = None,
    title: str = "MiniGPT experiment card",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    warnings: list[str] = []
    train_config = _read_json(root / "train_config.json", warnings)
    history = _read_json(root / "history_summary.json", warnings)
    dataset_report = _read_json(root / "dataset_report.json", warnings)
    dataset_quality = _read_json(root / "dataset_quality.json", warnings)
    eval_report = _read_json(root / "eval_report.json", warnings)
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json", warnings)
    manifest = _read_json(root / "run_manifest.json", warnings)
    model_report = _read_json(root / "model_report" / "model_report.json", warnings)
    run_notes = _read_json(root / "run_notes.json", warnings)
    registry = _read_json(Path(registry_path), warnings) if registry_path is not None else None
    registry_run = _find_registry_run(root, registry if isinstance(registry, dict) else None)

    notes = _build_notes(run_notes, registry_run)
    summary = _build_summary(root, train_config, history, dataset_quality, eval_report, eval_suite, manifest, model_report, registry_run, notes)
    data = _build_data_section(dataset_report, dataset_quality, manifest)
    training = _build_training_section(train_config, history, manifest)
    evaluation = _build_evaluation_section(eval_report, eval_suite, registry_run)
    registry_context = _build_registry_context(registry, registry_run, registry_path)
    artifacts = _collect_card_artifacts(root)
    recommendations = _build_recommendations(summary, data, evaluation, artifacts, warnings)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_dir": str(root),
        "summary": summary,
        "notes": notes,
        "data": data,
        "training": training,
        "evaluation": evaluation,
        "registry": registry_context,
        "artifacts": artifacts,
        "recommendations": recommendations,
        "warnings": warnings,
    }


def write_experiment_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)


def render_experiment_card_markdown(card: dict[str, Any]) -> str:
    summary = _dict(card.get("summary"))
    notes = _dict(card.get("notes"))
    data = _dict(card.get("data"))
    training = _dict(card.get("training"))
    evaluation = _dict(card.get("evaluation"))
    registry = _dict(card.get("registry"))
    artifacts = [item for item in card.get("artifacts", []) if isinstance(item, dict)]
    recommendations = [str(item) for item in card.get("recommendations", [])]
    warnings = [str(item) for item in card.get("warnings", [])]

    rows = [
        ("Run", summary.get("run_name")),
        ("Status", summary.get("status")),
        ("Best val loss", _fmt(summary.get("best_val_loss"))),
        ("Loss rank", _rank_label(summary.get("best_val_loss_rank"))),
        ("Loss delta", _fmt_delta(summary.get("best_val_loss_delta"))),
        ("Dataset quality", summary.get("dataset_quality")),
        ("Eval suite cases", summary.get("eval_suite_cases")),
        ("Git", summary.get("git_commit")),
        ("Parameters", _fmt_int(summary.get("total_parameters"))),
    ]
    lines = [
        f"# {card.get('title', 'MiniGPT experiment card')}",
        "",
        f"- Generated: `{card.get('generated_at')}`",
        f"- Run dir: `{card.get('run_dir')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(rows),
        "",
        "## Notes",
        "",
        f"- Note: {notes.get('note') or 'missing'}",
        f"- Tags: {_fmt_tags(notes.get('tags')) or 'missing'}",
        "",
        "## Data",
        "",
        *_markdown_table(
            [
                ("Source kind", data.get("source_kind")),
                ("Sources", data.get("source_count")),
                ("Characters", _fmt_int(data.get("char_count"))),
                ("Fingerprint", data.get("short_fingerprint")),
                ("Warnings", data.get("warning_count")),
            ]
        ),
        "",
        "## Training",
        "",
        *_markdown_table(
            [
                ("Tokenizer", training.get("tokenizer")),
                ("Max iters", training.get("max_iters")),
                ("Device", training.get("device_used")),
                ("Start step", training.get("start_step")),
                ("End step", training.get("end_step")),
                ("Last val loss", _fmt(training.get("last_val_loss"))),
            ]
        ),
        "",
        "## Evaluation",
        "",
        *_markdown_table(
            [
                ("Eval loss", _fmt(evaluation.get("eval_loss"))),
                ("Perplexity", _fmt(evaluation.get("perplexity"))),
                ("Eval suite cases", evaluation.get("eval_suite_cases")),
                ("Average unique chars", _fmt(evaluation.get("avg_unique_chars"))),
                ("Registry best", evaluation.get("is_best_val_loss")),
            ]
        ),
        "",
        "## Registry",
        "",
        *_markdown_table(
            [
                ("Registry path", registry.get("registry_path")),
                ("Run count", registry.get("run_count")),
                ("Quality counts", _fmt_mapping(registry.get("quality_counts"))),
                ("Tag counts", _fmt_mapping(registry.get("tag_counts"))),
            ]
        ),
        "",
        "## Recommendations",
        "",
        *[f"- {item}" for item in recommendations],
        "",
        "## Artifacts",
        "",
        *_artifact_lines(artifacts),
    ]
    if warnings:
        lines.extend(["", "## Warnings", "", *[f"- {item}" for item in warnings]])
    return "\n".join(lines).rstrip() + "\n"


def write_experiment_card_markdown(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_experiment_card_markdown(card), encoding="utf-8")


def render_experiment_card_html(card: dict[str, Any], *, base_dir: str | Path | None = None) -> str:
    summary = _dict(card.get("summary"))
    notes = _dict(card.get("notes"))
    artifacts = [item for item in card.get("artifacts", []) if isinstance(item, dict)]
    stats = [
        ("Status", summary.get("status")),
        ("Best val", _fmt(summary.get("best_val_loss"))),
        ("Rank", _rank_label(summary.get("best_val_loss_rank"))),
        ("Delta", _fmt_delta(summary.get("best_val_loss_delta"))),
        ("Quality", summary.get("dataset_quality")),
        ("Eval cases", summary.get("eval_suite_cases")),
        ("Git", summary.get("git_commit")),
        ("Params", _fmt_int(summary.get("total_parameters"))),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(card.get('title', 'MiniGPT experiment card'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(card.get('title', 'MiniGPT experiment card'))}</h1><p>{_e(card.get('run_dir'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            '<section class="panel"><h2>Notes</h2>'
            f"<p>{_e(notes.get('note') or 'missing')}</p><p>{_tag_chips(notes.get('tags'))}</p></section>",
            _key_value_section("Data", _dict(card.get("data"))),
            _key_value_section("Training", _dict(card.get("training"))),
            _key_value_section("Evaluation", _dict(card.get("evaluation"))),
            _key_value_section("Registry", _dict(card.get("registry"))),
            _recommendation_section(card.get("recommendations", [])),
            _artifact_section(artifacts, base_dir),
            _warning_section(card.get("warnings", [])),
            "<footer>Generated by MiniGPT experiment card exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_experiment_card_html(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_experiment_card_html(card, base_dir=out_path.parent), encoding="utf-8")


def write_experiment_card_outputs(card: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "experiment_card.json",
        "markdown": root / "experiment_card.md",
        "html": root / "experiment_card.html",
    }
    _mark_output_artifacts(card, paths)
    write_experiment_card_json(card, paths["json"])
    write_experiment_card_markdown(card, paths["markdown"])
    write_experiment_card_html(card, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} is not valid JSON: {exc}")
        return None


def _find_registry_run(root: Path, registry: dict[str, Any] | None) -> dict[str, Any] | None:
    if registry is None:
        return None
    try:
        resolved = root.resolve()
    except OSError:
        resolved = root.absolute()
    for run in registry.get("runs", []):
        if not isinstance(run, dict):
            continue
        path = run.get("path")
        if path is None:
            continue
        try:
            candidate = Path(str(path)).resolve()
        except OSError:
            candidate = Path(str(path)).absolute()
        if candidate == resolved or str(path) == str(root):
            return run
    return None


def _build_notes(run_notes: Any, registry_run: dict[str, Any] | None) -> dict[str, Any]:
    notes = run_notes if isinstance(run_notes, dict) else {}
    note = _pick(notes, "note") or _pick(notes, "summary") or _pick(registry_run, "note")
    tags = _as_str_list(_pick(notes, "tags") or _pick(registry_run, "tags"))
    return {"note": _as_str(note), "tags": tags}


def _build_summary(
    root: Path,
    train_config: Any,
    history: Any,
    dataset_quality: Any,
    eval_report: Any,
    eval_suite: Any,
    manifest: Any,
    model_report: Any,
    registry_run: dict[str, Any] | None,
    notes: dict[str, Any],
) -> dict[str, Any]:
    manifest_data = _pick_dict(manifest, "data")
    manifest_training = _pick_dict(manifest, "training")
    manifest_model = _pick_dict(manifest, "model")
    manifest_results = _pick_dict(manifest, "results")
    manifest_history = _pick_dict(manifest_results, "history_summary")
    git = _pick_dict(manifest, "git")
    best_val_loss = (
        _pick(registry_run, "best_val_loss")
        or _pick(history, "best_val_loss")
        or _pick(manifest_history, "best_val_loss")
    )
    dataset_status = (
        _pick(registry_run, "dataset_quality")
        or _pick(dataset_quality, "status")
        or _pick(_pick_dict(manifest_data, "dataset_quality"), "status")
    )
    checkpoint_exists = (root / "checkpoint.pt").exists()
    eval_cases = _pick(registry_run, "eval_suite_cases") or _pick(eval_suite, "case_count")
    status = _overall_status(dataset_status, checkpoint_exists, best_val_loss, eval_cases)
    return {
        "run_name": _pick(registry_run, "name") or root.name,
        "status": status,
        "checkpoint_exists": checkpoint_exists,
        "tokenizer": _pick(train_config, "tokenizer") or _pick(manifest_training, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters") or _nested_pick(manifest_training, "args", "max_iters"),
        "best_val_loss": _as_optional_float(best_val_loss),
        "best_val_loss_rank": _pick(registry_run, "best_val_loss_rank"),
        "best_val_loss_delta": _pick(registry_run, "best_val_loss_delta"),
        "is_best_val_loss": bool(_pick(registry_run, "is_best_val_loss")),
        "last_val_loss": _as_optional_float(_pick(history, "last_val_loss") or _pick(manifest_history, "last_val_loss")),
        "eval_loss": _as_optional_float(_pick(eval_report, "loss")),
        "perplexity": _as_optional_float(_pick(eval_report, "perplexity")),
        "dataset_quality": _as_str(dataset_status),
        "dataset_fingerprint": _as_str(_pick(registry_run, "dataset_fingerprint") or _pick(dataset_quality, "short_fingerprint")),
        "eval_suite_cases": _as_int(eval_cases),
        "git_commit": _as_str(_pick(registry_run, "git_commit") or _pick(git, "short_commit")),
        "git_dirty": _pick(registry_run, "git_dirty") if _pick(registry_run, "git_dirty") is not None else _pick(git, "dirty"),
        "total_parameters": _as_int(_pick(registry_run, "total_parameters") or _pick(model_report, "total_parameters") or _pick(manifest_model, "parameter_count")),
        "note": notes.get("note"),
        "tags": notes.get("tags", []),
    }


def _build_data_section(dataset_report: Any, dataset_quality: Any, manifest: Any) -> dict[str, Any]:
    manifest_data = _pick_dict(manifest, "data")
    source = _pick_dict(manifest_data, "source")
    manifest_quality = _pick_dict(manifest_data, "dataset_quality")
    return {
        "source_kind": _pick(source, "kind"),
        "source_count": _pick(dataset_report, "source_count"),
        "char_count": _pick(dataset_report, "char_count"),
        "line_count": _pick(dataset_report, "line_count"),
        "unique_char_count": _pick(dataset_report, "unique_char_count"),
        "token_count": _pick(manifest_data, "token_count"),
        "train_token_count": _pick(manifest_data, "train_token_count"),
        "val_token_count": _pick(manifest_data, "val_token_count"),
        "status": _pick(dataset_quality, "status") or _pick(manifest_quality, "status"),
        "short_fingerprint": _pick(dataset_quality, "short_fingerprint") or _pick(manifest_quality, "short_fingerprint"),
        "warning_count": _pick(dataset_quality, "warning_count"),
        "issue_count": _pick(dataset_quality, "issue_count"),
    }


def _build_training_section(train_config: Any, history: Any, manifest: Any) -> dict[str, Any]:
    manifest_training = _pick_dict(manifest, "training")
    args = _pick_dict(manifest_training, "args")
    return {
        "tokenizer": _pick(train_config, "tokenizer") or _pick(manifest_training, "tokenizer"),
        "max_iters": _pick(train_config, "max_iters") or _pick(args, "max_iters"),
        "batch_size": _pick(train_config, "batch_size") or _pick(args, "batch_size"),
        "block_size": _pick(train_config, "block_size") or _pick(args, "block_size"),
        "learning_rate": _pick(train_config, "learning_rate") or _pick(args, "learning_rate"),
        "device_used": _pick(manifest_training, "device_used"),
        "start_step": _pick(manifest_training, "start_step"),
        "end_step": _pick(manifest_training, "end_step"),
        "best_val_loss": _pick(history, "best_val_loss"),
        "last_val_loss": _pick(history, "last_val_loss"),
    }


def _build_evaluation_section(eval_report: Any, eval_suite: Any, registry_run: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "eval_loss": _pick(eval_report, "loss"),
        "perplexity": _pick(eval_report, "perplexity"),
        "eval_suite_cases": _pick(eval_suite, "case_count") or _pick(registry_run, "eval_suite_cases"),
        "avg_unique_chars": _pick(eval_suite, "avg_unique_chars") or _pick(registry_run, "eval_suite_avg_unique"),
        "best_val_loss_rank": _pick(registry_run, "best_val_loss_rank"),
        "best_val_loss_delta": _pick(registry_run, "best_val_loss_delta"),
        "is_best_val_loss": bool(_pick(registry_run, "is_best_val_loss")),
    }


def _build_registry_context(registry: Any, registry_run: dict[str, Any] | None, registry_path: str | Path | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "registry_path": None if registry_path is None else str(registry_path),
            "run_count": None,
            "quality_counts": None,
            "tag_counts": None,
            "matched_run": registry_run is not None,
        }
    return {
        "registry_path": None if registry_path is None else str(registry_path),
        "run_count": registry.get("run_count"),
        "quality_counts": registry.get("quality_counts"),
        "tag_counts": registry.get("tag_counts"),
        "matched_run": registry_run is not None,
    }


def _collect_card_artifacts(root: Path) -> list[dict[str, Any]]:
    artifacts = []
    for key, relative, description in CARD_ARTIFACT_PATHS:
        path = root / relative
        exists = path.exists()
        artifacts.append(
            {
                "key": key,
                "path": relative,
                "description": description,
                "exists": exists,
                "size_bytes": path.stat().st_size if exists and path.is_file() else None,
            }
        )
    return artifacts


def _build_recommendations(
    summary: dict[str, Any],
    data: dict[str, Any],
    evaluation: dict[str, Any],
    artifacts: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    items: list[str] = []
    if summary.get("is_best_val_loss"):
        items.append("Keep this run as the current best-val reference until a lower-loss run is registered.")
    if summary.get("dataset_quality") in {None, "missing"}:
        items.append("Generate dataset_quality.json before comparing this run seriously.")
    elif summary.get("dataset_quality") != "pass":
        items.append("Review dataset quality warnings before promoting this run.")
    if evaluation.get("eval_suite_cases") in {None, 0}:
        items.append("Run the fixed prompt eval suite so generations can be compared across checkpoints.")
    if not summary.get("checkpoint_exists"):
        items.append("Create or restore checkpoint.pt before using this run for generation.")
    if data.get("short_fingerprint") is None:
        items.append("Record a dataset fingerprint to make data provenance reproducible.")
    if warnings:
        items.append("Fix invalid JSON inputs listed in the warnings section.")
    if not any(item.get("key") == "dashboard" and item.get("exists") for item in artifacts):
        items.append("Build dashboard.html to make all run artifacts easier to inspect.")
    return items or ["This run has the core metadata needed for a first-pass experiment review."]


def _mark_output_artifacts(card: dict[str, Any], paths: dict[str, Path]) -> None:
    key_map = {
        "json": "experiment_card_json",
        "markdown": "experiment_card_md",
        "html": "experiment_card_html",
    }
    artifacts = card.get("artifacts")
    if not isinstance(artifacts, list):
        return
    for output_key, artifact_key in key_map.items():
        for artifact in artifacts:
            if isinstance(artifact, dict) and artifact.get("key") == artifact_key:
                artifact["exists"] = True
                artifact["size_bytes"] = paths[output_key].stat().st_size if paths[output_key].exists() else None
                break


def _overall_status(dataset_status: Any, checkpoint_exists: bool, best_val_loss: Any, eval_cases: Any) -> str:
    if not checkpoint_exists or best_val_loss is None:
        return "incomplete"
    if dataset_status in {None, "missing"}:
        return "needs-data-quality"
    if dataset_status not in {"pass", None}:
        return "review"
    if eval_cases in {None, 0}:
        return "needs-eval"
    return "ready"


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {key} | {_md(value)} |")
    return lines


def _artifact_lines(artifacts: list[dict[str, Any]]) -> list[str]:
    lines = []
    for item in artifacts:
        state = "yes" if item.get("exists") else "no"
        size = _fmt_int(item.get("size_bytes")) if item.get("size_bytes") is not None else "missing"
        lines.append(f"- `{item.get('path')}`: {state}, {size} bytes")
    return lines


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = []
    for key, value in payload.items():
        rows.append(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>")
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{"".join(rows)}</table></section>'


def _recommendation_section(items: Any) -> str:
    values = [str(item) for item in items] or ["No recommendations."]
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _artifact_section(artifacts: list[dict[str, Any]], base_dir: str | Path | None) -> str:
    rows = []
    for item in artifacts:
        path = str(item.get("path") or "")
        href = _artifact_href(path, base_dir)
        label = f'<a href="{_e(href)}">{_e(path)}</a>' if item.get("exists") and href else _e(path)
        rows.append(
            "<tr>"
            f"<td>{_e(item.get('key'))}</td>"
            f"<td>{label}</td>"
            f"<td>{_e('yes' if item.get('exists') else 'no')}</td>"
            f"<td>{_e(_fmt_int(item.get('size_bytes')) if item.get('size_bytes') is not None else 'missing')}</td>"
            "</tr>"
        )
    return '<section class="panel"><h2>Artifacts</h2><table><thead><tr><th>Key</th><th>Path</th><th>Exists</th><th>Size</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></section>"


def _warning_section(items: Any) -> str:
    warnings = [str(item) for item in items]
    if not warnings:
        return ""
    return '<section class="panel warn"><h2>Warnings</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in warnings) + "</ul></section>"


def _artifact_href(relative: str, base_dir: str | Path | None) -> str | None:
    if base_dir is None:
        return relative
    return Path(os.path.relpath(Path(base_dir) / relative, Path(base_dir))).as_posix()


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e(_fmt_any(value))}</div>'
        "</div>"
    )


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --amber:#b45309; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
.warn { border-color:#f59e0b; }
table { width:100%; border-collapse:collapse; min-width:760px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; }
.tag { display:inline-block; margin:0 4px 4px 0; padding:2px 6px; border-radius:999px; background:#e0f2fe; color:#075985; font-size:12px; font-weight:700; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _tag_chips(value: Any) -> str:
    tags = _as_str_list(value)
    if not tags:
        return '<span class="muted">missing</span>'
    return "".join(f'<span class="tag">{_e(tag)}</span>' for tag in tags)


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    nested = _pick(payload, key)
    return nested if isinstance(nested, dict) else {}


def _nested_pick(payload: Any, section: str, key: str) -> Any:
    return _pick(_pick_dict(payload, section), key)


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _fmt(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return str(value)


def _fmt_delta(value: Any) -> str:
    number = _as_optional_float(value)
    if number is None:
        return "missing"
    return f"{number:+.5g}"


def _fmt_int(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{int(value):,}"


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _fmt_tags(value: Any) -> str:
    return ", ".join(_as_str_list(value))


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict):
        return "missing"
    return ", ".join(f"{key}:{val}" for key, val in value.items()) or "missing"


def _fmt_any(value: Any) -> str:
    if isinstance(value, dict):
        return _fmt_mapping(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "missing"
    return _fmt(value)


def _md(value: Any) -> str:
    text = _fmt_any(value)
    return text.replace("|", "\\|").replace("\n", " ")
