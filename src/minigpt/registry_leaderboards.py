from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

from minigpt.registry_data import _as_optional_float, _as_str_list


def loss_leaderboard_html(leaderboard: Any) -> str:
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


def benchmark_rubric_leaderboard_html(leaderboard: Any) -> str:
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


def pair_delta_leaderboard_html(leaderboard: Any, base_dir: str | Path | None) -> str:
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


def release_readiness_delta_leaderboard_html(leaderboard: Any, base_dir: str | Path | None) -> str:
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


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _href(path: Path, base_dir: str | Path | None) -> str:
    if base_dir is None:
        return path.as_posix()
    try:
        return Path(os.path.relpath(path, Path(base_dir))).as_posix()
    except ValueError:
        return path.as_posix()


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


__all__ = [
    "benchmark_rubric_leaderboard_html",
    "loss_leaderboard_html",
    "pair_delta_leaderboard_html",
    "release_readiness_delta_leaderboard_html",
]
