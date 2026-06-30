from __future__ import annotations

from typing import Any

from minigpt.registry_assets import registry_script as _asset_registry_script
from minigpt.registry_assets import registry_style as _asset_registry_style
from minigpt.registry_data import _pick
from minigpt.registry_render_format import escape_html as _e
from minigpt.registry_render_format import fmt as _fmt
from minigpt.registry_render_rows import registry_run_row


def registry_stats(registry: dict[str, Any]) -> list[tuple[str, Any]]:
    best = registry.get("best_by_best_val_loss") if isinstance(registry.get("best_by_best_val_loss"), dict) else {}
    quality_counts = registry.get("quality_counts", {})
    tag_counts = registry.get("tag_counts", {})
    generation_quality_counts = registry.get("generation_quality_counts", {})
    benchmark_rubric_counts = registry.get("benchmark_rubric_counts", {})
    benchmark_rubric_summary = registry.get("benchmark_rubric_summary", {})
    pair_report_counts = registry.get("pair_report_counts", {})
    pair_delta_summary = registry.get("pair_delta_summary", {})
    dataset_snapshot_summary = registry.get("dataset_snapshot_summary", {})
    dataset_dedupe_policy_counts = registry.get("dataset_dedupe_policy_counts", {})
    release_readiness_counts = registry.get("release_readiness_comparison_counts", {})
    release_readiness_delta_summary = registry.get("release_readiness_delta_summary", {})
    loss_leaderboard = registry.get("loss_leaderboard", [])
    return [
        ("Runs", registry.get("run_count")),
        ("Best run", _pick(best, "name")),
        ("Best val", _fmt(_pick(best, "best_val_loss"))),
        ("Comparable", len(loss_leaderboard) if isinstance(loss_leaderboard, list) else 0),
        ("Fingerprints", len(registry.get("dataset_fingerprints", []))),
        ("Dataset snapshots", _dataset_snapshot_summary_label(dataset_snapshot_summary)),
        ("Dedupe policies", _count_label(dataset_dedupe_policy_counts)),
        ("Quality", ", ".join(f"{key}:{value}" for key, value in quality_counts.items()) if isinstance(quality_counts, dict) else None),
        ("Gen quality", ", ".join(f"{key}:{value}" for key, value in generation_quality_counts.items()) if isinstance(generation_quality_counts, dict) else None),
        ("Rubric", _benchmark_rubric_summary_label(benchmark_rubric_summary, benchmark_rubric_counts)),
        ("Pair reports", _pair_report_count_label(pair_report_counts)),
        ("Pair deltas", _pair_delta_summary_label(pair_delta_summary)),
        ("Release readiness", _release_readiness_counts_label(release_readiness_counts)),
        ("Readiness deltas", _release_readiness_delta_summary_label(release_readiness_delta_summary)),
        ("CI regression reasons", _release_readiness_ci_reason_summary_label(release_readiness_delta_summary)),
        ("CI order regressions", _release_readiness_ci_order_summary_label(release_readiness_delta_summary)),
        ("Coverage regressions", _release_readiness_coverage_summary_label(release_readiness_delta_summary)),
        ("Benchmark regressions", _release_readiness_benchmark_summary_label(release_readiness_delta_summary)),
        ("Benchmark suite-design", _release_readiness_benchmark_suite_summary_label(release_readiness_delta_summary)),
        ("Tags", len(tag_counts) if isinstance(tag_counts, dict) else 0),
    ]


def registry_controls(runs: list[Any]) -> str:
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


def stat_card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def registry_style() -> str:
    return _asset_registry_style()


def registry_script() -> str:
    return _asset_registry_script()


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


def _count_label(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _dataset_snapshot_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return (
        f"snapshots:{value.get('snapshot_run_count', 0)}, "
        f"missing:{value.get('missing_snapshot_count', 0)}, "
        f"skipped-runs:{value.get('skipped_source_run_count', 0)}"
    )


def _release_readiness_delta_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "deltas:0"
    return (
        f"deltas:{value.get('delta_count')}, "
        f"regressed:{value.get('regressed_count')}, "
        f"improved:{value.get('improved_count')}, "
        f"panels:{value.get('changed_panel_delta_count')}, "
        f"coverage:{value.get('test_coverage_regression_count', 0)}"
        f", benchmark:{value.get('benchmark_history_regression_count', 0)}"
        f", suite:{value.get('benchmark_history_suite_design_non_comparison_ready_regression_count', 0)}"
        f", req:{value.get('benchmark_history_readiness_requirement_status_changed_count', 0)}"
    )


def _release_readiness_coverage_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "missing"
    return (
        f"regressions:{value.get('test_coverage_regression_count', 0)}, "
        f"gap:{_fmt(value.get('max_abs_test_coverage_gap_delta'))}, "
        f"percent:{_fmt(value.get('max_abs_test_coverage_percent_delta'))}"
    )


def _release_readiness_ci_order_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "missing"
    return (
        f"regressions:{value.get('ci_workflow_order_regression_count', 0)}, "
        f"max:{_fmt(value.get('max_abs_ci_workflow_order_violation_delta'))}"
    )


def _release_readiness_ci_reason_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "missing"
    counts = value.get("ci_workflow_regression_reason_counts")
    if not isinstance(counts, dict) or not counts:
        return "none"
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _release_readiness_benchmark_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "missing"
    return (
        f"regressions:{value.get('benchmark_history_regression_count', 0)}, "
        f"case:{_fmt(value.get('max_abs_benchmark_history_case_regression_delta'))}, "
        f"flags:{_fmt(value.get('max_abs_benchmark_history_generation_flag_regression_delta'))}, "
        f"suite:{_fmt(value.get('max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta'))}, "
        f"req:{value.get('benchmark_history_readiness_requirement_status_changed_count', 0)}, "
        f"exit:{_fmt(value.get('max_abs_benchmark_history_readiness_requirement_exit_code_delta'))}, "
        f"boundary:{value.get('benchmark_history_boundary_changed_count', 0)}"
    )


def _release_readiness_benchmark_suite_summary_label(value: Any) -> str:
    if not isinstance(value, dict) or not value.get("delta_count"):
        return "missing"
    return (
        f"deltas:{value.get('benchmark_history_suite_design_non_comparison_ready_delta_count', 0)}, "
        f"regressions:{value.get('benchmark_history_suite_design_non_comparison_ready_regression_count', 0)}, "
        f"design changes:{value.get('benchmark_history_design_comparison_changed_delta_count', 0)}"
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


__all__ = [
    "registry_controls",
    "registry_run_row",
    "registry_script",
    "registry_stats",
    "registry_style",
    "stat_card",
]
