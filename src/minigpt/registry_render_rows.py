from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from minigpt.registry_data import _as_str_list
from minigpt.registry_render_format import csv_value as _csv_value
from minigpt.registry_render_format import escape_html as _e
from minigpt.registry_render_format import fmt as _fmt
from minigpt.registry_render_format import fmt_delta as _fmt_delta
from minigpt.registry_render_format import fmt_int as _fmt_int
from minigpt.registry_render_format import rank_label as _rank_label
from minigpt.registry_render_format import sort_number as _sort_number


def registry_run_row(run: dict[str, Any], base_dir: str | Path | None) -> str:
    quality = str(run.get("dataset_quality") or "missing")
    quality_class = "pass" if quality == "pass" else "warn" if quality == "warn" else "missing"
    generation_quality = str(run.get("generation_quality_status") or "missing")
    generation_quality_class = (
        "pass"
        if generation_quality == "pass"
        else "warn"
        if generation_quality == "warn"
        else "fail"
        if generation_quality == "fail"
        else "missing"
    )
    links = _registry_links(run, base_dir)
    return (
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
        f"<td>{_e(run.get('data_source_kind'))}<br><span>{_e(run.get('dataset_version'))}</span><br><span>{_e(run.get('dataset_fingerprint'))}</span><br><span>{_e(_dataset_snapshot_label(run))}</span></td>"
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


def _row_search_text(run: dict[str, Any]) -> str:
    keys = [
        "name",
        "path",
        "git_commit",
        "tokenizer",
        "data_source_kind",
        "dataset_version",
        "dataset_fingerprint",
        "dataset_dedupe_policy",
        "dataset_source_order_digest",
        "dataset_quality",
        "dataset_included_source_count",
        "dataset_skipped_source_count",
        "dataset_char_count",
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
        "release_readiness_ci_workflow_regression_reasons",
        "release_readiness_test_coverage_regression_count",
        "release_readiness_benchmark_history_regression_count",
        "release_readiness_benchmark_suite_design_delta_count",
        "release_readiness_benchmark_suite_design_regression_count",
        "release_readiness_benchmark_design_change_delta_count",
        "release_readiness_benchmark_requirement_status_change_count",
        "release_readiness_benchmark_requirement_exit_code_delta_max",
        "release_readiness_benchmark_requirement_failed_reason_added_count",
        "release_readiness_benchmark_requirement_failed_reason_removed_count",
        "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count",
        "note",
        "tags",
    ]
    return " ".join(str(_csv_value(run.get(key)) or "") for key in keys).lower()


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


def _pair_report_score(run: dict[str, Any]) -> int:
    score = 0
    if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists"):
        score += int(run.get("pair_batch_cases") or 1)
    if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists"):
        score += int(run.get("pair_trend_reports") or 1)
    return score


def _dataset_snapshot_label(run: dict[str, Any]) -> str:
    parts = []
    policy = run.get("dataset_dedupe_policy")
    if policy:
        parts.append(f"dedupe={policy}")
    included = run.get("dataset_included_source_count")
    skipped = run.get("dataset_skipped_source_count")
    if included is not None or skipped is not None:
        parts.append(f"included={_fmt_int(included)}")
        parts.append(f"skipped={_fmt_int(skipped)}")
    char_count = run.get("dataset_char_count")
    if char_count is not None:
        parts.append(f"chars={_fmt_int(char_count)}")
    digest = run.get("dataset_source_order_digest")
    if digest:
        parts.append(f"order={_clip(digest, 18)}")
    return "; ".join(parts) if parts else "snapshot missing"


def _release_readiness_sort_score(run: dict[str, Any]) -> int:
    order = {
        "coverage-regressed": 0,
        "benchmark-regressed": 1,
        "ci-regressed": 2,
        "regressed": 3,
        "blocked": 4,
        "panel-changed": 5,
        "stable": 6,
        "improved": 7,
        "missing": 8,
    }
    return order.get(str(run.get("release_readiness_comparison_status") or "missing"), 8)


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
        if status in {"panel-changed", "ci-regressed", "coverage-regressed", "benchmark-regressed"}
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
        f"<br><span>ci reasons={_e(_fmt_tags(run.get('release_readiness_ci_workflow_regression_reasons')))}</span>"
        f"<br><span>ci order regressions={_e(_fmt(run.get('release_readiness_ci_workflow_order_regression_count')))}</span>"
        f"<br><span>coverage regressions={_e(_fmt(run.get('release_readiness_test_coverage_regression_count')))}</span>"
        f"<br><span>benchmark regressions={_e(_fmt(run.get('release_readiness_benchmark_history_regression_count')))} deltas={_e(_fmt(run.get('release_readiness_benchmark_history_delta_count')))}</span>"
        f"<br><span>suite design deltas={_e(_fmt(run.get('release_readiness_benchmark_suite_design_delta_count')))} regressions={_e(_fmt(run.get('release_readiness_benchmark_suite_design_regression_count')))} changes={_e(_fmt(run.get('release_readiness_benchmark_design_change_delta_count')))}</span>"
        f"<br><span>benchmark req changes={_e(_fmt(run.get('release_readiness_benchmark_requirement_status_change_count')))} exit max={_e(_fmt(run.get('release_readiness_benchmark_requirement_exit_code_delta_max')))}</span>"
        f"<br><span>benchmark reasons +={_e(_fmt(run.get('release_readiness_benchmark_requirement_failed_reason_added_count')))} -={_e(_fmt(run.get('release_readiness_benchmark_requirement_failed_reason_removed_count')))} mixed={_e(_fmt(run.get('release_readiness_benchmark_requirement_failed_reason_mixed_delta_count')))}</span>"
    )


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


__all__ = ["registry_run_row"]
