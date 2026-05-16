from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any

from minigpt.registry_assets import registry_script, registry_style
from minigpt.registry_data import _as_optional_float, _as_str_list, _pick


def render_registry_html(
    registry: dict[str, Any],
    *,
    title: str = "MiniGPT run registry",
    base_dir: str | Path | None = None,
) -> str:
    runs = list(registry.get("runs", []))
    best = registry.get("best_by_best_val_loss") if isinstance(registry.get("best_by_best_val_loss"), dict) else {}
    quality_counts = registry.get("quality_counts", {})
    tag_counts = registry.get("tag_counts", {})
    generation_quality_counts = registry.get("generation_quality_counts", {})
    benchmark_rubric_counts = registry.get("benchmark_rubric_counts", {})
    benchmark_rubric_summary = registry.get("benchmark_rubric_summary", {})
    pair_report_counts = registry.get("pair_report_counts", {})
    pair_delta_summary = registry.get("pair_delta_summary", {})
    release_readiness_counts = registry.get("release_readiness_comparison_counts", {})
    release_readiness_delta_summary = registry.get("release_readiness_delta_summary", {})
    loss_leaderboard = registry.get("loss_leaderboard", [])
    stats = [
        ("Runs", registry.get("run_count")),
        ("Best run", _pick(best, "name")),
        ("Best val", _fmt(_pick(best, "best_val_loss"))),
        ("Comparable", len(loss_leaderboard) if isinstance(loss_leaderboard, list) else 0),
        ("Fingerprints", len(registry.get("dataset_fingerprints", []))),
        ("Quality", ", ".join(f"{key}:{value}" for key, value in quality_counts.items()) if isinstance(quality_counts, dict) else None),
        ("Gen quality", ", ".join(f"{key}:{value}" for key, value in generation_quality_counts.items()) if isinstance(generation_quality_counts, dict) else None),
        ("Rubric", _benchmark_rubric_summary_label(benchmark_rubric_summary, benchmark_rubric_counts)),
        ("Pair reports", _pair_report_count_label(pair_report_counts)),
        ("Pair deltas", _pair_delta_summary_label(pair_delta_summary)),
        ("Release readiness", _release_readiness_counts_label(release_readiness_counts)),
        ("Readiness deltas", _release_readiness_delta_summary_label(release_readiness_delta_summary)),
        ("Tags", len(tag_counts) if isinstance(tag_counts, dict) else 0),
    ]
    rows = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        quality = str(run.get("dataset_quality") or "missing")
        quality_class = "pass" if quality == "pass" else "warn" if quality == "warn" else "missing"
        generation_quality = str(run.get("generation_quality_status") or "missing")
        generation_quality_class = (
            "pass" if generation_quality == "pass" else "warn" if generation_quality == "warn" else "fail" if generation_quality == "fail" else "missing"
        )
        links = _registry_links(run, base_dir)
        rows.append(
            '<tr data-run-row'
            f' data-search="{_e(_row_search_text(run))}"'
            f' data-quality="{_e(quality)}"'
            f' data-name="{_e(run.get("name"))}"'
            f' data-rank="{_e(_sort_number(run.get("best_val_loss_rank")))}"'
            f' data-best-val="{_e(_sort_number(run.get("best_val_loss")))}"'
            f' data-delta="{_e(_sort_number(run.get("best_val_loss_delta")))}"'
            f' data-params="{_e(_sort_number(run.get("total_parameters")))}"'
            f' data-artifacts="{_e(_sort_number(run.get("artifact_count")))}"'
            f' data-rubric="{_e(_sort_number(run.get("benchmark_rubric_avg_score")))}"'
            f' data-pair="{_e(_sort_number(_pair_report_score(run)))}"'
            f' data-readiness="{_e(_sort_number(_release_readiness_sort_score(run)))}"'
            f' data-eval="{_e(_sort_number(run.get("eval_suite_cases")))}">'
            f"<td><strong>{_e(run.get('name'))}</strong><br><span>{_e(run.get('path'))}</span></td>"
            f"<td>{_e(_rank_label(run.get('best_val_loss_rank')))}</td>"
            f"<td>{_e(_fmt(run.get('best_val_loss')))}<br><span>{_e(_fmt_delta(run.get('best_val_loss_delta')))}</span></td>"
            f"<td>{_e(_fmt_int(run.get('total_parameters')))}</td>"
            f"<td>{_e(run.get('git_commit'))}<br><span>dirty={_e(run.get('git_dirty'))}</span></td>"
            f"<td>{_e(run.get('data_source_kind'))}<br><span>{_e(run.get('dataset_fingerprint'))}</span></td>"
            f'<td><span class="pill {quality_class}">{_e(quality)}</span></td>'
            f"<td>{_e(run.get('eval_suite_cases'))}<br><span>avg unique={_e(run.get('eval_suite_avg_unique'))}</span></td>"
            f'<td><span class="pill {generation_quality_class}">{_e(generation_quality)}</span><br><span>cases={_e(run.get("generation_quality_cases"))}</span></td>'
            f"<td>{_benchmark_rubric_cell(run)}</td>"
            f"<td>{_pair_report_cell(run)}</td>"
            f"<td>{_release_readiness_cell(run)}</td>"
            f"<td>{_e(run.get('artifact_count'))}</td>"
            f"<td>{_tag_chips(run.get('tags'))}<br><span>{_e(run.get('note'))}</span></td>"
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
            "<thead><tr><th>Run</th><th>Rank</th><th>Best Val</th><th>Params</th><th>Git</th><th>Data</th><th>Quality</th><th>Eval</th><th>Gen Quality</th><th>Rubric</th><th>Pair Reports</th><th>Release Readiness</th><th>Artifacts</th><th>Notes</th><th>Links</th></tr></thead>",
            '<tbody id="registry-rows">',
            "".join(rows),
            "</tbody>",
            "</table>",
            "</section>",
            _loss_leaderboard_html(loss_leaderboard),
            _benchmark_rubric_leaderboard_html(registry.get("benchmark_rubric_leaderboard", [])),
            _pair_delta_leaderboard_html(registry.get("pair_delta_leaderboard", []), base_dir),
            _release_readiness_delta_leaderboard_html(registry.get("release_readiness_delta_leaderboard", []), base_dir),
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


def write_registry_json(registry: dict[str, Any], path: str | Path) -> None:
    from minigpt.registry_artifacts import write_registry_json as _write_registry_json

    _write_registry_json(registry, path)


def write_registry_csv(registry: dict[str, Any], path: str | Path) -> None:
    from minigpt.registry_artifacts import write_registry_csv as _write_registry_csv

    _write_registry_csv(registry, path)


def write_registry_svg(registry: dict[str, Any], path: str | Path) -> None:
    from minigpt.registry_artifacts import write_registry_svg as _write_registry_svg

    _write_registry_svg(registry, path)


def write_registry_html(registry: dict[str, Any], path: str | Path, title: str = "MiniGPT run registry") -> None:
    from minigpt.registry_artifacts import write_registry_html as _write_registry_html

    _write_registry_html(registry, path, title=title)


def write_registry_outputs(registry: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    from minigpt.registry_artifacts import write_registry_outputs as _write_registry_outputs

    return _write_registry_outputs(registry, out_dir)


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


def _sort_number(value: Any) -> str:
    if value is None:
        return ""
    return str(float(value))


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


def _row_search_text(run: dict[str, Any]) -> str:
    keys = [
        "name",
        "path",
        "git_commit",
        "tokenizer",
        "data_source_kind",
        "dataset_fingerprint",
        "dataset_quality",
        "generation_quality_status",
        "benchmark_scorecard_status",
        "benchmark_rubric_status",
        "benchmark_weakest_rubric_case",
        "pair_batch_cases",
        "pair_trend_reports",
        "release_readiness_comparison_status",
        "release_readiness_baseline_status",
        "release_readiness_improved_count",
        "release_readiness_regressed_count",
        "release_readiness_ci_workflow_regression_count",
        "note",
        "tags",
    ]
    return " ".join(str(_csv_value(run.get(key)) or "") for key in keys).lower()


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
        '<option value="rank">Rank</option>'
        '<option value="bestVal">Best Val</option>'
        '<option value="delta">Loss Delta</option>'
        '<option value="name">Name</option>'
        '<option value="artifacts">Artifacts</option>'
        '<option value="rubric">Rubric</option>'
        '<option value="pair">Pair Reports</option>'
        '<option value="readiness">Release Readiness</option>'
        '<option value="eval">Eval Cases</option>'
        '<option value="params">Params</option>'
        "</select></label>"
        '<button id="sort-direction" type="button" aria-pressed="false">Asc</button>'
        '<output id="registry-count" for="registry-search quality-filter sort-key">0 / 0</output>'
        '<button id="share-view" type="button">Share</button>'
        '<button id="export-visible-csv" type="button">CSV</button>'
        '<output id="registry-status" for="share-view export-visible-csv"></output>'
        "</section>"
    )


def _registry_links(run: dict[str, Any], base_dir: str | Path | None) -> str:
    root = Path(str(run.get("path", "")))
    specs = [
        ("dashboard", root / "dashboard.html"),
        ("card", root / "experiment_card.html"),
        ("manifest", root / "run_manifest.json"),
        ("eval", root / "eval_suite" / "eval_suite.json"),
        ("scorecard", root / "benchmark-scorecard" / "benchmark_scorecard.html"),
        ("pair batch", root / "pair_batch" / "pair_generation_batch.html"),
        ("pair trend", root / "pair_batch_trend" / "pair_batch_trend.html"),
        ("readiness cmp", root / "release-readiness-comparison" / "release_readiness_comparison.html"),
        ("readiness cmp", root / "release_readiness_comparison.html"),
        ("gen quality", root / "generation-quality" / "generation_quality.html"),
        ("gen quality", root / "eval_suite" / "generation-quality" / "generation_quality.html"),
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


def _pair_report_count_label(value: Any) -> str:
    if not isinstance(value, dict):
        return "batch:0, trend:0"
    return f"batch:{value.get('pair_batch', 0)}, trend:{value.get('pair_trend', 0)}"


def _pair_delta_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("case_count"):
        return "cases:0"
    return (
        f"cases:{value.get('case_count')}, "
        f"max gen:{_fmt(value.get('max_abs_generated_char_delta'))}, "
        f"max cont:{_fmt(value.get('max_abs_continuation_char_delta'))}"
    )


def _release_readiness_counts_label(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _release_readiness_delta_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "deltas:0"
    return (
        f"deltas:{value.get('delta_count')}, "
        f"regressed:{value.get('regressed_count')}, "
        f"improved:{value.get('improved_count')}, "
        f"panels:{value.get('changed_panel_delta_count')}"
    )


def _benchmark_rubric_summary_label(summary: Any, counts: Any) -> str:
    if isinstance(summary, dict) and summary.get("available"):
        return (
            f"best:{_fmt(summary.get('best_score'))}, "
            f"weakest:{_fmt(summary.get('weakest_score'))}, "
            f"regressions:{summary.get('regression_count')}"
        )
    if isinstance(counts, dict) and counts:
        return ", ".join(f"{key}:{value}" for key, value in counts.items())
    return "missing"


def _pair_report_score(run: dict[str, Any]) -> int:
    score = 0
    if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists"):
        score += int(run.get("pair_batch_cases") or 1)
    if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists"):
        score += int(run.get("pair_trend_reports") or 1)
    return score


def _release_readiness_sort_score(run: dict[str, Any]) -> int:
    order = {
        "regressed": 0,
        "ci-regressed": 1,
        "blocked": 2,
        "panel-changed": 3,
        "stable": 4,
        "improved": 5,
        "missing": 6,
    }
    return order.get(str(run.get("release_readiness_comparison_status") or "missing"), 6)


def _benchmark_rubric_cell(run: dict[str, Any]) -> str:
    status = str(run.get("benchmark_rubric_status") or "missing")
    status_class = "pass" if status == "pass" else "warn" if status == "warn" else "fail" if status == "fail" else "missing"
    if run.get("benchmark_rubric_avg_score") is None and status == "missing":
        return '<span class="muted">missing</span>'
    return (
        f'<span class="pill {status_class}">{_e(status)}</span>'
        f"<br><span>score={_e(_fmt(run.get('benchmark_rubric_avg_score')))} rank={_e(_rank_label(run.get('benchmark_rubric_rank')))}</span>"
        f"<br><span>delta={_e(_fmt_delta(run.get('benchmark_rubric_delta_from_best')))}</span>"
        f"<br><span>weak={_e(run.get('benchmark_weakest_rubric_case'))}:{_e(_fmt(run.get('benchmark_weakest_rubric_score')))}</span>"
    )


def _pair_report_cell(run: dict[str, Any]) -> str:
    rows = []
    if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists"):
        rows.append(
            "batch cases="
            + _e(run.get("pair_batch_cases") if run.get("pair_batch_cases") is not None else "html")
            + " diff="
            + _e(_fmt(run.get("pair_batch_generated_differences")))
        )
    if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists"):
        rows.append(
            "trend reports="
            + _e(run.get("pair_trend_reports") if run.get("pair_trend_reports") is not None else "html")
            + " changed="
            + _e(_fmt(run.get("pair_trend_changed_cases")))
        )
    if not rows:
        return '<span class="muted">missing</span>'
    return "<br>".join(f"<span>{row}</span>" for row in rows)


def _release_readiness_cell(run: dict[str, Any]) -> str:
    status = str(run.get("release_readiness_comparison_status") or "missing")
    status_class = (
        "pass"
        if status in {"improved", "stable"}
        else "warn"
        if status in {"panel-changed", "ci-regressed"}
        else "fail"
        if status in {"regressed", "blocked"}
        else "missing"
    )
    if status == "missing" and not run.get("release_readiness_html_exists"):
        return '<span class="muted">missing</span>'
    return (
        f'<span class="pill {status_class}">{_e(status)}</span>'
        f"<br><span>reports={_e(_fmt(run.get('release_readiness_report_count')))} baseline={_e(_fmt(run.get('release_readiness_baseline_status')))}</span>"
        f"<br><span>ready={_e(_fmt(run.get('release_readiness_ready_count')))} blocked={_e(_fmt(run.get('release_readiness_blocked_count')))}</span>"
        f"<br><span>improved={_e(_fmt(run.get('release_readiness_improved_count')))} regressed={_e(_fmt(run.get('release_readiness_regressed_count')))}</span>"
        f"<br><span>panel deltas={_e(_fmt(run.get('release_readiness_changed_panel_delta_count')))} ci regressions={_e(_fmt(run.get('release_readiness_ci_workflow_regression_count')))}</span>"
    )


def _stat_card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _loss_leaderboard_html(leaderboard: Any) -> str:
    if not isinstance(leaderboard, list) or not leaderboard:
        return (
            '<section class="panel">'
            "<h2>Loss Leaderboard</h2>"
            '<p class="muted">No comparable best validation loss values.</p>'
            "</section>"
        )
    items = []
    for item in leaderboard[:8]:
        if not isinstance(item, dict):
            continue
        items.append(
            "<li>"
            f"<strong>{_e(_rank_label(item.get('rank')))} {_e(item.get('name'))}</strong>"
            f"<span>{_e(_fmt(item.get('best_val_loss')))} / {_e(_fmt_delta(item.get('best_val_loss_delta')))}"
            f" / quality={_e(item.get('dataset_quality'))} / eval={_e(item.get('eval_suite_cases'))}</span>"
            "</li>"
        )
    return (
        '<section class="panel">'
        "<h2>Loss Leaderboard</h2>"
        '<ol class="leaderboard">'
        + "".join(items)
        + "</ol>"
        "</section>"
    )


def _benchmark_rubric_leaderboard_html(leaderboard: Any) -> str:
    if not isinstance(leaderboard, list) or not leaderboard:
        return (
            '<section class="panel">'
            "<h2>Rubric Leaderboard</h2>"
            '<p class="muted">No benchmark rubric scores were found.</p>'
            "</section>"
        )
    items = []
    for item in leaderboard[:8]:
        if not isinstance(item, dict):
            continue
        items.append(
            "<li>"
            f"<strong>{_e(_rank_label(item.get('rank')))} {_e(item.get('name'))}</strong>"
            f"<span>score={_e(_fmt(item.get('benchmark_rubric_avg_score')))} / {_e(_fmt_delta(item.get('benchmark_rubric_delta_from_best')))}"
            f" / status={_e(item.get('benchmark_rubric_status'))} / weak={_e(item.get('benchmark_weakest_rubric_case'))}:{_e(_fmt(item.get('benchmark_weakest_rubric_score')))}</span>"
            "</li>"
        )
    return (
        '<section class="panel">'
        "<h2>Rubric Leaderboard</h2>"
        '<ol class="leaderboard">'
        + "".join(items)
        + "</ol>"
        "</section>"
    )


def _pair_delta_leaderboard_html(leaderboard: Any, base_dir: str | Path | None) -> str:
    if not isinstance(leaderboard, list) or not leaderboard:
        return (
            '<section class="panel">'
            "<h2>Pair Delta Leaders</h2>"
            '<p class="muted">No pair batch case deltas were found.</p>'
            "</section>"
        )
    rows = []
    for item in leaderboard[:10]:
        if not isinstance(item, dict):
            continue
        report_link = ""
        report_path = item.get("report_path")
        if report_path and Path(str(report_path)).exists():
            report_link = f'<a href="{_e(_href(Path(str(report_path)), base_dir))}">pair batch</a>'
        rows.append(
            "<tr>"
            f"<td><strong>{_e(item.get('run_name'))}</strong><br><span>{_e(item.get('case'))}</span></td>"
            f"<td>{_e(_fmt(item.get('abs_generated_char_delta')))}</td>"
            f"<td>{_e(_fmt(item.get('generated_char_delta')))}<br><span>cont={_e(_fmt(item.get('continuation_char_delta')))}</span></td>"
            f"<td>{_e(item.get('generated_equal'))}<br><span>cont={_e(item.get('continuation_equal'))}</span></td>"
            f"<td>{_e(item.get('task_type'))}<br><span>{_e(item.get('difficulty'))}</span></td>"
            f"<td>{_e(item.get('left_checkpoint_id'))} -> {_e(item.get('right_checkpoint_id'))}<br><span>{_e(item.get('suite_name'))} v{_e(item.get('suite_version'))}</span></td>"
            f"<td>{report_link}</td>"
            "</tr>"
        )
    return (
        '<section class="panel">'
        "<h2>Pair Delta Leaders</h2>"
        '<table><thead><tr><th>Run / Case</th><th>Abs Gen Delta</th><th>Delta</th><th>Equal</th><th>Task</th><th>Pair</th><th>Report</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
        "</section>"
    )


def _release_readiness_delta_leaderboard_html(leaderboard: Any, base_dir: str | Path | None) -> str:
    if not isinstance(leaderboard, list) or not leaderboard:
        return (
            '<section class="panel">'
            "<h2>Release Readiness Deltas</h2>"
            '<p class="muted">No release readiness comparison deltas were found.</p>'
            "</section>"
        )
    rows = []
    for item in leaderboard[:10]:
        if not isinstance(item, dict):
            continue
        report_link = ""
        report_path = item.get("report_path")
        if report_path and Path(str(report_path)).exists():
            report_link = f'<a href="{_e(_href(Path(str(report_path)), base_dir))}">comparison</a>'
        rows.append(
            "<tr>"
            f"<td><strong>{_e(item.get('run_name'))}</strong><br><span>{_e(item.get('compared_release'))}</span></td>"
            f"<td>{_e(item.get('delta_status'))}<br><span>{_e(_fmt_delta(item.get('status_delta')))}</span></td>"
            f"<td>{_e(item.get('baseline_status'))} -> {_e(item.get('compared_status'))}</td>"
            f"<td>{_e(item.get('changed_panel_count'))}<br><span>{_e('; '.join(_as_str_list(item.get('changed_panels'))))}</span></td>"
            f"<td>{_e(_fmt_delta(item.get('audit_score_delta')))}<br><span>missing={_e(_fmt_delta(item.get('missing_artifact_delta')))}</span></td>"
            f"<td>{_e(item.get('baseline_ci_workflow_status'))} -> {_e(item.get('compared_ci_workflow_status'))}<br><span>failed={_e(_fmt_delta(item.get('ci_workflow_failed_check_delta')))}</span></td>"
            f"<td>{_e(item.get('explanation'))}</td>"
            f"<td>{report_link}</td>"
            "</tr>"
        )
    return (
        '<section class="panel">'
        "<h2>Release Readiness Deltas</h2>"
        '<table><thead><tr><th>Run / Compared</th><th>Trend</th><th>Status</th><th>Panels</th><th>Audit / Missing</th><th>CI workflow</th><th>Explanation</th><th>Report</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
        "</section>"
    )


def _registry_style() -> str:
    return registry_style()


def _registry_script() -> str:
    return registry_script()


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _fmt_tags(value: Any) -> str:
    tags = value if isinstance(value, list) else _as_str_list(value)
    return ", ".join(str(tag) for tag in tags)


def _tag_chips(value: Any) -> str:
    tags = value if isinstance(value, list) else _as_str_list(value)
    if not tags:
        return '<span class="muted">no tags</span>'
    return "".join(f'<span class="tag">{_e(tag)}</span>' for tag in tags)


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
