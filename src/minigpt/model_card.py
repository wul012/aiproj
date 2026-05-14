from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    utc_now,
    write_json_payload,
)


def build_model_card(
    registry_path: str | Path,
    *,
    card_paths: list[str | Path] | None = None,
    title: str = "MiniGPT model card",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    cards = _load_experiment_cards(registry, card_paths, warnings)
    runs = _build_run_summaries(registry, cards)
    summary = _build_summary(registry, runs, cards)
    coverage = _build_coverage(registry, runs, cards)
    recommendations = _build_recommendations(summary, coverage, runs, warnings)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "registry_path": str(registry_file),
        "summary": summary,
        "intended_use": [
            "Educational MiniGPT-from-scratch experiments.",
            "Local comparison of tiny language-model runs, data quality, evaluation, and artifacts.",
            "Portfolio or review summary for a learning project.",
        ],
        "limitations": [
            "This is a small educational model, not a production assistant.",
            "Best validation loss is useful for comparison but does not guarantee generation quality.",
            "Fixed prompt evaluation is lightweight and should be expanded for serious model assessment.",
            "Training data coverage and safety review are intentionally minimal in this project.",
        ],
        "coverage": coverage,
        "quality_counts": registry.get("quality_counts", {}),
        "generation_quality_counts": registry.get("generation_quality_counts", {}),
        "tag_counts": registry.get("tag_counts", {}),
        "dataset_fingerprints": registry.get("dataset_fingerprints", []),
        "top_runs": _top_runs(registry, runs),
        "runs": runs,
        "recommendations": recommendations,
        "warnings": warnings,
    }


def write_model_card_json(card: dict[str, Any], path: str | Path) -> None:
    write_json_payload(card, path)


def render_model_card_markdown(card: dict[str, Any]) -> str:
    summary = _dict(card.get("summary"))
    coverage = _dict(card.get("coverage"))
    lines = [
        f"# {card.get('title', 'MiniGPT model card')}",
        "",
        f"- Generated: `{card.get('generated_at')}`",
        f"- Registry: `{card.get('registry_path')}`",
        "",
        "## Summary",
        "",
        *_markdown_table(
            [
                ("Run count", summary.get("run_count")),
                ("Best run", summary.get("best_run_name")),
                ("Best val loss", _fmt(summary.get("best_val_loss"))),
                ("Ready runs", summary.get("ready_runs")),
                ("Review runs", summary.get("review_runs")),
                ("Experiment cards", coverage.get("experiment_cards_found")),
                ("Quality checked", coverage.get("quality_checked_runs")),
                ("Eval suite runs", coverage.get("eval_suite_runs")),
                ("Generation quality", coverage.get("generation_quality_runs")),
            ]
        ),
        "",
        "## Intended Use",
        "",
        *[f"- {item}" for item in _string_list(card.get("intended_use"))],
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in _string_list(card.get("limitations"))],
        "",
        "## Top Runs",
        "",
        *_run_table(_list_of_dicts(card.get("top_runs"))),
        "",
        "## Coverage",
        "",
        *_markdown_table([(key, value) for key, value in coverage.items()]),
        "",
        "## Recommendations",
        "",
        *[f"- {item}" for item in _string_list(card.get("recommendations"))],
        "",
        "## Runs",
        "",
        *_run_table(_list_of_dicts(card.get("runs"))),
    ]
    warnings = _string_list(card.get("warnings"))
    if warnings:
        lines.extend(["", "## Warnings", "", *[f"- {item}" for item in warnings]])
    return "\n".join(lines).rstrip() + "\n"


def write_model_card_markdown(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_model_card_markdown(card), encoding="utf-8")


def render_model_card_html(card: dict[str, Any], *, base_dir: str | Path | None = None) -> str:
    summary = _dict(card.get("summary"))
    coverage = _dict(card.get("coverage"))
    stats = [
        ("Runs", summary.get("run_count")),
        ("Best run", summary.get("best_run_name")),
        ("Best val", _fmt(summary.get("best_val_loss"))),
        ("Ready", summary.get("ready_runs")),
        ("Review", summary.get("review_runs")),
        ("Cards", coverage.get("experiment_cards_found")),
        ("Eval suite", coverage.get("eval_suite_runs")),
        ("Gen quality", coverage.get("generation_quality_runs")),
        ("Quality", coverage.get("quality_checked_runs")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(card.get('title', 'MiniGPT model card'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(card.get('title', 'MiniGPT model card'))}</h1><p>{_e(card.get('registry_path'))}</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _list_section("Intended Use", card.get("intended_use")),
            _list_section("Limitations", card.get("limitations")),
            _run_section("Top Runs", _list_of_dicts(card.get("top_runs")), base_dir),
            _key_value_section("Coverage", coverage),
            _key_value_section("Quality Counts", _dict(card.get("quality_counts"))),
            _key_value_section("Generation Quality Counts", _dict(card.get("generation_quality_counts"))),
            _key_value_section("Tag Counts", _dict(card.get("tag_counts"))),
            _list_section("Recommendations", card.get("recommendations")),
            _run_section("All Runs", _list_of_dicts(card.get("runs")), base_dir),
            _list_section("Warnings", card.get("warnings"), hide_empty=True),
            "<footer>Generated by MiniGPT model card exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_model_card_html(card: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_model_card_html(card, base_dir=out_path.parent), encoding="utf-8")


def write_model_card_outputs(card: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "model_card.json",
        "markdown": root / "model_card.md",
        "html": root / "model_card.html",
    }
    write_model_card_json(card, paths["json"])
    write_model_card_markdown(card, paths["markdown"])
    write_model_card_html(card, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"model card input must be a JSON object: {path}")
    return payload


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _load_experiment_cards(
    registry: dict[str, Any],
    card_paths: list[str | Path] | None,
    warnings: list[str],
) -> dict[str, dict[str, Any]]:
    paths = [Path(path) for path in card_paths or []]
    if not paths:
        for run in registry.get("runs", []):
            if isinstance(run, dict) and run.get("path"):
                paths.append(Path(str(run["path"])) / "experiment_card.json")
    cards: dict[str, dict[str, Any]] = {}
    for path in paths:
        card = _read_json(path, warnings)
        if card is None:
            continue
        run_key = _path_key(card.get("run_dir") or path.parent)
        card["card_path"] = str(path)
        card["card_html_path"] = str(path.with_suffix(".html"))
        cards[run_key] = card
    return cards


def _build_run_summaries(registry: dict[str, Any], cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    runs = []
    for run in registry.get("runs", []):
        if not isinstance(run, dict):
            continue
        path = run.get("path")
        card = cards.get(_path_key(path)) if path is not None else None
        card_summary = _dict(card.get("summary")) if card else {}
        notes = _dict(card.get("notes")) if card else {}
        status = card_summary.get("status") or _derive_status(run)
        runs.append(
            {
                "name": run.get("name"),
                "path": path,
                "status": status,
                "best_val_loss_rank": run.get("best_val_loss_rank"),
                "best_val_loss": run.get("best_val_loss"),
                "best_val_loss_delta": run.get("best_val_loss_delta"),
                "dataset_quality": run.get("dataset_quality"),
                "eval_suite_cases": run.get("eval_suite_cases"),
                "generation_quality_status": run.get("generation_quality_status"),
                "generation_quality_cases": run.get("generation_quality_cases"),
                "generation_quality_pass_count": run.get("generation_quality_pass_count"),
                "generation_quality_warn_count": run.get("generation_quality_warn_count"),
                "generation_quality_fail_count": run.get("generation_quality_fail_count"),
                "artifact_count": run.get("artifact_count"),
                "checkpoint_exists": run.get("checkpoint_exists"),
                "dashboard_exists": run.get("dashboard_exists"),
                "experiment_card_exists": card is not None,
                "experiment_card_path": None if card is None else card.get("card_path"),
                "experiment_card_html": None if card is None else card.get("card_html_path"),
                "note": notes.get("note") or run.get("note"),
                "tags": notes.get("tags") or run.get("tags") or [],
                "recommendations": [] if card is None else list(card.get("recommendations", [])),
            }
        )
    runs.sort(key=lambda item: (_sort_rank(item.get("best_val_loss_rank")), str(item.get("name") or "")))
    return runs


def _build_summary(registry: dict[str, Any], runs: list[dict[str, Any]], cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    best = registry.get("best_by_best_val_loss") if isinstance(registry.get("best_by_best_val_loss"), dict) else {}
    ready = sum(1 for run in runs if run.get("status") == "ready")
    review = sum(1 for run in runs if run.get("status") == "review")
    return {
        "run_count": registry.get("run_count", len(runs)),
        "best_run_name": best.get("name"),
        "best_run_path": best.get("path"),
        "best_val_loss": best.get("best_val_loss"),
        "ready_runs": ready,
        "review_runs": review,
        "experiment_cards": len(cards),
        "comparable_runs": sum(1 for run in runs if run.get("best_val_loss") is not None),
    }


def _build_coverage(registry: dict[str, Any], runs: list[dict[str, Any]], cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    total = len(runs)
    return {
        "run_count": total,
        "experiment_cards_found": len(cards),
        "experiment_card_coverage": _ratio(len(cards), total),
        "quality_checked_runs": sum(1 for run in runs if run.get("dataset_quality") not in {None, "missing"}),
        "eval_suite_runs": sum(1 for run in runs if run.get("eval_suite_cases") not in {None, 0}),
        "generation_quality_runs": sum(1 for run in runs if run.get("generation_quality_status") not in {None, "missing"}),
        "generation_quality_pass_runs": sum(1 for run in runs if run.get("generation_quality_status") == "pass"),
        "checkpoint_runs": sum(1 for run in runs if run.get("checkpoint_exists")),
        "dashboard_runs": sum(1 for run in runs if run.get("dashboard_exists")),
        "dataset_fingerprint_count": len(registry.get("dataset_fingerprints", [])),
    }


def _top_runs(registry: dict[str, Any], runs: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    by_name = {str(run.get("name")): run for run in runs}
    top = []
    for item in registry.get("loss_leaderboard", []):
        if not isinstance(item, dict):
            continue
        run = by_name.get(str(item.get("name")))
        if run is None:
            run = item
        top.append(run)
        if len(top) >= limit:
            break
    return top or runs[:limit]


def _build_recommendations(
    summary: dict[str, Any],
    coverage: dict[str, Any],
    runs: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    items = []
    if coverage.get("experiment_cards_found", 0) < coverage.get("run_count", 0):
        items.append("Generate missing experiment cards so every registered run has a single-run review page.")
    if summary.get("ready_runs", 0) == 0:
        items.append("Promote at least one run to ready status by adding checkpoint, dataset quality, and eval suite artifacts.")
    else:
        items.append("Use the best ready run as the current project reference and compare new runs against it.")
    if any(run.get("dataset_quality") not in {"pass", None, "missing"} for run in runs):
        items.append("Review non-pass dataset quality runs before using them as baselines.")
    if coverage.get("eval_suite_runs", 0) < coverage.get("run_count", 0):
        items.append("Run the fixed prompt eval suite for every registered run.")
    if coverage.get("generation_quality_runs", 0) < coverage.get("run_count", 0):
        items.append("Analyze generation quality for every registered run after eval suite or sampling output exists.")
    if any(run.get("generation_quality_status") not in {"pass", None, "missing"} for run in runs):
        items.append("Review non-pass generation quality runs before treating them as release candidates.")
    if warnings:
        items.append("Fix invalid or unreadable experiment card JSON files listed in warnings.")
    return items


def _derive_status(run: dict[str, Any]) -> str:
    if not run.get("checkpoint_exists") or run.get("best_val_loss") is None:
        return "incomplete"
    if run.get("dataset_quality") in {None, "missing"}:
        return "needs-data-quality"
    if run.get("dataset_quality") != "pass":
        return "review"
    if run.get("eval_suite_cases") in {None, 0}:
        return "needs-eval"
    if run.get("generation_quality_status") in {None, "missing"}:
        return "needs-generation-quality"
    if run.get("generation_quality_status") != "pass":
        return "review"
    return "ready"


def _run_table(runs: list[dict[str, Any]]) -> list[str]:
    lines = ["| Rank | Run | Status | Best Val | Delta | Quality | Eval | Gen Quality | Card |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for run in runs:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(_rank_label(run.get("best_val_loss_rank"))),
                    _md(run.get("name")),
                    _md(run.get("status")),
                    _md(_fmt(run.get("best_val_loss"))),
                    _md(_fmt_delta(run.get("best_val_loss_delta"))),
                    _md(run.get("dataset_quality")),
                    _md(run.get("eval_suite_cases")),
                    _md(_generation_quality_label(run)),
                    _md("yes" if run.get("experiment_card_exists") else "no"),
                ]
            )
            + " |"
        )
    return lines


def _run_section(title: str, runs: list[dict[str, Any]], base_dir: str | Path | None) -> str:
    rows = []
    for run in runs:
        card = run.get("experiment_card_html") or run.get("experiment_card_path")
        card_link = _path_link(card, base_dir, "card") if card else '<span class="muted">missing</span>'
        rows.append(
            "<tr>"
            f"<td>{_e(_rank_label(run.get('best_val_loss_rank')))}</td>"
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(run.get('status'))}</td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}<br><span>{_e(_fmt_delta(run.get('best_val_loss_delta')))}</span></td>"
            f"<td>{_e(run.get('dataset_quality'))}</td>"
            f"<td>{_e(run.get('eval_suite_cases'))}</td>"
            f"<td>{_e(_generation_quality_label(run))}</td>"
            f"<td>{_tag_chips(run.get('tags'))}<br><span>{_e(run.get('note'))}</span></td>"
            f"<td>{card_link}</td>"
            "</tr>"
        )
    return (
        f'<section class="panel"><h2>{_e(title)}</h2>'
        '<table><thead><tr><th>Rank</th><th>Run</th><th>Status</th><th>Best Val</th><th>Quality</th><th>Eval</th><th>Gen Quality</th><th>Notes</th><th>Card</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def _key_value_section(title: str, payload: dict[str, Any]) -> str:
    rows = "".join(f"<tr><th>{_e(key)}</th><td>{_e(_fmt_any(value))}</td></tr>" for key, value in payload.items())
    return f'<section class="panel"><h2>{_e(title)}</h2><table>{rows}</table></section>'


def _list_section(title: str, values: Any, hide_empty: bool = False) -> str:
    items = _string_list(values)
    if hide_empty and not items:
        return ""
    if not items:
        items = ["missing"]
    return f'<section class="panel"><h2>{_e(title)}</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return '<div class="card">' + f'<div class="label">{_e(label)}</div><div class="value">{_e(_fmt_any(value))}</div>' + "</div>"


def _path_link(path: Any, base_dir: str | Path | None, label: str) -> str:
    if path is None:
        return '<span class="muted">missing</span>'
    href = str(path)
    if base_dir is not None:
        try:
            href = Path(os.path.relpath(Path(str(path)), Path(base_dir))).as_posix()
        except ValueError:
            href = Path(str(path)).as_posix()
    return f'<a href="{_e(href)}">{_e(label)}</a>'


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
span, .muted { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:82px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:920px; }
th, td { padding:8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
a { color:var(--blue); font-weight:700; text-decoration:none; }
.tag { display:inline-block; margin:0 4px 4px 0; padding:2px 6px; border-radius:999px; background:#e0f2fe; color:#075985; font-size:12px; font-weight:700; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _markdown_table(rows: list[tuple[str, Any]]) -> list[str]:
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in rows:
        lines.append(f"| {_md(key)} | {_md(value)} |")
    return lines


def _tag_chips(value: Any) -> str:
    tags = _as_str_list(value)
    if not tags:
        return '<span class="muted">missing</span>'
    return "".join(f'<span class="tag">{_e(tag)}</span>' for tag in tags)


def _generation_quality_label(run: dict[str, Any]) -> str:
    status = run.get("generation_quality_status") or "missing"
    cases = run.get("generation_quality_cases")
    if cases in {None, ""}:
        return str(status)
    return f"{status} ({cases} cases)"


def _path_key(value: Any) -> str:
    try:
        return str(Path(str(value)).resolve()).lower()
    except OSError:
        return str(value).lower()


def _sort_rank(value: Any) -> int:
    if value is None or value == "":
        return 1_000_000
    return int(value)


def _ratio(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 4)


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


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
    if value is None or value == "":
        return "missing"
    return f"{float(value):+.5g}"


def _fmt_any(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{key}:{val}" for key, val in value.items()) or "missing"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "missing"
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _md(value: Any) -> str:
    return _fmt_any(value).replace("|", "\\|").replace("\n", " ")
