from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from minigpt.registry_rankings import (
    annotate_loss_leaderboard,
    annotate_rubric_leaderboard,
    benchmark_rubric_summary,
    best_registered_run,
    collect_pair_delta_rows,
    collect_release_readiness_delta_rows,
    counts,
    pair_delta_leaderboard,
    pair_delta_summary,
    release_readiness_delta_leaderboard,
    release_readiness_delta_summary,
)


REGISTRY_ARTIFACT_PATHS = [
    "checkpoint.pt",
    "tokenizer.json",
    "train_config.json",
    "metrics.jsonl",
    "history_summary.json",
    "loss_curve.svg",
    "prepared_corpus.txt",
    "run_manifest.json",
    "run_manifest.svg",
    "dataset_report.json",
    "dataset_report.svg",
    "dataset_quality.json",
    "dataset_quality.svg",
    "dataset_version.json",
    "dataset_version.html",
    "eval_suite/eval_suite.json",
    "eval_suite/eval_suite.csv",
    "eval_suite/eval_suite.svg",
    "eval_suite/eval_suite.html",
    "pair_batch/pair_generation_batch.json",
    "pair_batch/pair_generation_batch.csv",
    "pair_batch/pair_generation_batch.md",
    "pair_batch/pair_generation_batch.html",
    "pair_batch_trend/pair_batch_trend.json",
    "pair_batch_trend/pair_batch_trend.csv",
    "pair_batch_trend/pair_batch_trend.md",
    "pair_batch_trend/pair_batch_trend.html",
    "release-readiness-comparison/release_readiness_comparison.json",
    "release-readiness-comparison/release_readiness_comparison.csv",
    "release-readiness-comparison/release_readiness_deltas.csv",
    "release-readiness-comparison/release_readiness_comparison.md",
    "release-readiness-comparison/release_readiness_comparison.html",
    "benchmark-scorecard/benchmark_scorecard.json",
    "benchmark-scorecard/benchmark_scorecard.csv",
    "benchmark-scorecard/benchmark_scorecard_drilldowns.csv",
    "benchmark-scorecard/benchmark_scorecard_rubric.csv",
    "benchmark-scorecard/benchmark_scorecard.md",
    "benchmark-scorecard/benchmark_scorecard.html",
    "generation-quality/generation_quality.json",
    "generation-quality/generation_quality.csv",
    "generation-quality/generation_quality.md",
    "generation-quality/generation_quality.svg",
    "generation-quality/generation_quality.html",
    "eval_suite/generation-quality/generation_quality.json",
    "eval_suite/generation-quality/generation_quality.csv",
    "eval_suite/generation-quality/generation_quality.md",
    "eval_suite/generation-quality/generation_quality.svg",
    "eval_suite/generation-quality/generation_quality.html",
    "sample.txt",
    "eval_report.json",
    "dashboard.html",
    "playground.html",
    "run_notes.json",
    "experiment_card.json",
    "experiment_card.md",
    "experiment_card.html",
]


@dataclass(frozen=True)
class RegisteredRun:
    name: str
    path: str
    git_commit: str | None
    git_dirty: bool | None
    tokenizer: str | None
    max_iters: int | None
    best_val_loss: float | None
    last_val_loss: float | None
    total_parameters: int | None
    data_source_kind: str | None
    dataset_version: str | None
    dataset_fingerprint: str | None
    dataset_dedupe_policy: str | None
    dataset_source_order_digest: str | None
    dataset_included_source_count: int | None
    dataset_skipped_source_count: int | None
    dataset_char_count: int | None
    dataset_quality: str | None
    eval_suite_cases: int | None
    eval_suite_avg_unique: float | None
    generation_quality_status: str | None
    generation_quality_cases: int | None
    generation_quality_pass_count: int | None
    generation_quality_warn_count: int | None
    generation_quality_fail_count: int | None
    generation_quality_avg_unique_ratio: float | None
    benchmark_scorecard_status: str | None
    benchmark_scorecard_score: float | None
    benchmark_rubric_status: str | None
    benchmark_rubric_avg_score: float | None
    benchmark_rubric_pass_count: int | None
    benchmark_rubric_warn_count: int | None
    benchmark_rubric_fail_count: int | None
    benchmark_weakest_rubric_case: str | None
    benchmark_weakest_rubric_score: float | None
    benchmark_scorecard_html_exists: bool
    pair_batch_cases: int | None
    pair_batch_generated_differences: int | None
    pair_batch_html_exists: bool
    pair_trend_reports: int | None
    pair_trend_changed_cases: int | None
    pair_trend_html_exists: bool
    release_readiness_comparison_status: str | None
    release_readiness_report_count: int | None
    release_readiness_baseline_status: str | None
    release_readiness_ready_count: int | None
    release_readiness_blocked_count: int | None
    release_readiness_improved_count: int | None
    release_readiness_regressed_count: int | None
    release_readiness_changed_panel_delta_count: int | None
    release_readiness_ci_workflow_regression_count: int | None
    release_readiness_ci_workflow_order_regression_count: int | None
    release_readiness_test_coverage_regression_count: int | None
    release_readiness_benchmark_history_delta_count: int | None
    release_readiness_benchmark_history_regression_count: int | None
    release_readiness_benchmark_requirement_status_change_count: int | None
    release_readiness_benchmark_requirement_exit_code_delta_max: int | float | None
    release_readiness_benchmark_requirement_failed_reason_added_count: int | None
    release_readiness_benchmark_requirement_failed_reason_removed_count: int | None
    release_readiness_html_exists: bool
    artifact_count: int
    checkpoint_exists: bool
    dashboard_exists: bool
    note: str | None
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def discover_run_dirs(root: str | Path, recursive: bool = True) -> list[Path]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(base)
    if base.is_file():
        raise ValueError(f"run discovery root must be a directory: {base}")
    candidates = base.rglob("run_manifest.json") if recursive else base.glob("*/run_manifest.json")
    runs = sorted({path.parent.resolve(): path.parent for path in candidates}.values(), key=lambda item: str(item))
    return runs


def summarize_registered_run(run_dir: str | Path, name: str | None = None) -> RegisteredRun:
    root = Path(run_dir)
    manifest = _read_json(root / "run_manifest.json")
    train_config = _read_json(root / "train_config.json")
    history = _read_json(root / "history_summary.json")
    dataset_quality = _read_json(root / "dataset_quality.json")
    dataset_version_report = _read_json(root / "dataset_version.json")
    eval_suite = _read_json(root / "eval_suite" / "eval_suite.json")
    generation_quality = _read_generation_quality(root)
    benchmark_scorecard = _read_benchmark_scorecard(root)
    pair_batch = _read_json(root / "pair_batch" / "pair_generation_batch.json")
    pair_trend = _read_json(root / "pair_batch_trend" / "pair_batch_trend.json")
    release_readiness_comparison = _read_release_readiness_comparison(root)
    run_notes = _read_run_notes(root)

    git = _pick_dict(manifest, "git")
    training = _pick_dict(manifest, "training")
    data = _pick_dict(manifest, "data")
    model = _pick_dict(manifest, "model")
    manifest_quality = _pick_dict(data, "dataset_quality")
    manifest_dataset_version = _pick_dict(data, "dataset_version")
    source = _pick_dict(data, "source")
    dataset_stats = _pick_dict(dataset_version_report, "stats")
    dataset_snapshot = _pick_dict(dataset_version_report, "snapshot")
    dataset_preparation = _pick_dict(dataset_version_report, "preparation")
    generation_summary = _pick_dict(generation_quality, "summary")
    benchmark_summary = _pick_dict(benchmark_scorecard, "summary")
    release_readiness_summary = _pick_dict(release_readiness_comparison, "summary")
    release_readiness_deltas = _release_readiness_deltas(release_readiness_comparison)
    artifacts = manifest.get("artifacts", []) if isinstance(manifest, dict) else []
    manifest_artifact_count = sum(1 for item in artifacts if isinstance(item, dict) and item.get("exists"))
    artifact_count = max(manifest_artifact_count, _actual_artifact_count(root))

    return RegisteredRun(
        name=name or root.name,
        path=str(root),
        git_commit=_as_str(_pick(git, "short_commit")),
        git_dirty=_as_bool(_pick(git, "dirty")),
        tokenizer=_as_str(_pick(training, "tokenizer") or _pick(train_config, "tokenizer")),
        max_iters=_as_int(_pick(train_config, "max_iters") or _nested_pick(training, "args", "max_iters")),
        best_val_loss=_as_float(_pick(history, "best_val_loss") or _nested_pick(_pick_dict(manifest, "results"), "history_summary", "best_val_loss")),
        last_val_loss=_as_float(_pick(history, "last_val_loss") or _nested_pick(_pick_dict(manifest, "results"), "history_summary", "last_val_loss")),
        total_parameters=_as_int(_pick(model, "parameter_count")),
        data_source_kind=_as_str(_pick(source, "kind")),
        dataset_version=_as_str(_pick(manifest_dataset_version, "id") or _nested_pick(dataset_version_report, "dataset", "id")),
        dataset_fingerprint=_as_str(
            _pick(manifest_dataset_version, "short_fingerprint")
            or _pick(dataset_stats, "short_fingerprint")
            or _pick(dataset_quality, "short_fingerprint")
            or _pick(manifest_quality, "short_fingerprint")
        ),
        dataset_dedupe_policy=_as_str(
            _pick(dataset_snapshot, "dedupe_policy")
            or ("exact-source-content" if _pick(dataset_preparation, "dedupe_exact_sources") else None)
        ),
        dataset_source_order_digest=_as_str(_pick(dataset_snapshot, "source_order_digest")),
        dataset_included_source_count=_as_int(_pick(dataset_stats, "included_source_count")),
        dataset_skipped_source_count=_as_int(_pick(dataset_stats, "skipped_source_count")),
        dataset_char_count=_as_int(_pick(dataset_stats, "char_count")),
        dataset_quality=_as_str(_pick(dataset_quality, "status") or _pick(manifest_quality, "status")),
        eval_suite_cases=_as_int(_pick(eval_suite, "case_count")),
        eval_suite_avg_unique=_as_float(_pick(eval_suite, "avg_unique_chars")),
        generation_quality_status=_as_str(_pick(generation_summary, "overall_status")),
        generation_quality_cases=_as_int(_pick(generation_summary, "case_count")),
        generation_quality_pass_count=_as_int(_pick(generation_summary, "pass_count")),
        generation_quality_warn_count=_as_int(_pick(generation_summary, "warn_count")),
        generation_quality_fail_count=_as_int(_pick(generation_summary, "fail_count")),
        generation_quality_avg_unique_ratio=_as_float(_pick(generation_summary, "avg_unique_ratio")),
        benchmark_scorecard_status=_as_str(_pick(benchmark_summary, "overall_status")),
        benchmark_scorecard_score=_as_float(_pick(benchmark_summary, "overall_score")),
        benchmark_rubric_status=_as_str(_pick(benchmark_summary, "rubric_status")),
        benchmark_rubric_avg_score=_as_float(_pick(benchmark_summary, "rubric_avg_score")),
        benchmark_rubric_pass_count=_as_int(_pick(benchmark_summary, "rubric_pass_count")),
        benchmark_rubric_warn_count=_as_int(_pick(benchmark_summary, "rubric_warn_count")),
        benchmark_rubric_fail_count=_as_int(_pick(benchmark_summary, "rubric_fail_count")),
        benchmark_weakest_rubric_case=_as_str(_pick(benchmark_summary, "weakest_rubric_case")),
        benchmark_weakest_rubric_score=_as_float(_pick(benchmark_summary, "weakest_rubric_score")),
        benchmark_scorecard_html_exists=(root / "benchmark-scorecard" / "benchmark_scorecard.html").exists(),
        pair_batch_cases=_as_int(_pick(pair_batch, "case_count")),
        pair_batch_generated_differences=_as_int(_pick(pair_batch, "generated_difference_count")),
        pair_batch_html_exists=(root / "pair_batch" / "pair_generation_batch.html").exists(),
        pair_trend_reports=_as_int(_pick(pair_trend, "report_count")),
        pair_trend_changed_cases=_as_int(_pick(pair_trend, "changed_generated_equal_cases")),
        pair_trend_html_exists=(root / "pair_batch_trend" / "pair_batch_trend.html").exists(),
        release_readiness_comparison_status=_release_readiness_comparison_status(release_readiness_summary),
        release_readiness_report_count=_as_int(_pick(release_readiness_summary, "readiness_count")),
        release_readiness_baseline_status=_as_str(_pick(release_readiness_summary, "baseline_status")),
        release_readiness_ready_count=_as_int(_pick(release_readiness_summary, "ready_count")),
        release_readiness_blocked_count=_as_int(_pick(release_readiness_summary, "blocked_count")),
        release_readiness_improved_count=_as_int(_pick(release_readiness_summary, "improved_count")),
        release_readiness_regressed_count=_as_int(_pick(release_readiness_summary, "regressed_count")),
        release_readiness_changed_panel_delta_count=_as_int(_pick(release_readiness_summary, "changed_panel_delta_count")),
        release_readiness_ci_workflow_regression_count=_as_int(_pick(release_readiness_summary, "ci_workflow_regression_count")),
        release_readiness_ci_workflow_order_regression_count=_as_int(_pick(release_readiness_summary, "ci_workflow_order_regression_count")),
        release_readiness_test_coverage_regression_count=_as_int(_pick(release_readiness_summary, "test_coverage_regression_count")),
        release_readiness_benchmark_history_delta_count=_as_int(_pick(release_readiness_summary, "benchmark_history_delta_count")),
        release_readiness_benchmark_history_regression_count=_as_int(_pick(release_readiness_summary, "benchmark_history_regression_count")),
        release_readiness_benchmark_requirement_status_change_count=_release_readiness_benchmark_requirement_status_change_count(
            release_readiness_deltas
        ),
        release_readiness_benchmark_requirement_exit_code_delta_max=_release_readiness_benchmark_requirement_exit_code_delta_max(
            release_readiness_deltas
        ),
        release_readiness_benchmark_requirement_failed_reason_added_count=_release_readiness_benchmark_requirement_failed_reason_added_count(
            release_readiness_deltas
        ),
        release_readiness_benchmark_requirement_failed_reason_removed_count=_release_readiness_benchmark_requirement_failed_reason_removed_count(
            release_readiness_deltas
        ),
        release_readiness_html_exists=_release_readiness_html_exists(root),
        artifact_count=artifact_count,
        checkpoint_exists=(root / "checkpoint.pt").exists(),
        dashboard_exists=(root / "dashboard.html").exists(),
        note=_as_str(_pick(run_notes, "note") or _pick(run_notes, "summary")),
        tags=_as_str_list(_pick(run_notes, "tags")),
    )


def build_run_registry(run_dirs: list[str | Path], names: list[str] | None = None) -> dict[str, Any]:
    if not run_dirs:
        raise ValueError("at least one run directory is required")
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("names length must match run_dirs length")
    runs = [
        summarize_registered_run(run_dir, None if names is None else names[index])
        for index, run_dir in enumerate(run_dirs)
    ]
    run_rows = [run.to_dict() for run in runs]
    loss_leaderboard = annotate_loss_leaderboard(run_rows)
    rubric_leaderboard = annotate_rubric_leaderboard(run_rows)
    pair_delta_rows = collect_pair_delta_rows(run_dirs, names)
    pair_delta_leaders = pair_delta_leaderboard(pair_delta_rows)
    release_readiness_delta_rows = collect_release_readiness_delta_rows(run_dirs, names)
    release_readiness_delta_leaders = release_readiness_delta_leaderboard(release_readiness_delta_rows)
    return {
        "schema_version": 1,
        "run_count": len(runs),
        "runs": run_rows,
        "best_by_best_val_loss": best_registered_run(runs, "best_val_loss"),
        "loss_leaderboard": loss_leaderboard,
        "benchmark_rubric_leaderboard": rubric_leaderboard,
        "benchmark_rubric_summary": benchmark_rubric_summary(rubric_leaderboard),
        "pair_delta_summary": pair_delta_summary(pair_delta_rows),
        "pair_delta_leaderboard": pair_delta_leaders,
        "release_readiness_delta_summary": release_readiness_delta_summary(release_readiness_delta_rows),
        "release_readiness_delta_leaderboard": release_readiness_delta_leaders,
        "dataset_versions": sorted({run.dataset_version for run in runs if run.dataset_version}),
        "dataset_fingerprints": sorted({run.dataset_fingerprint for run in runs if run.dataset_fingerprint}),
        "dataset_dedupe_policy_counts": counts(run.dataset_dedupe_policy or "missing" for run in runs),
        "dataset_snapshot_summary": _dataset_snapshot_summary(run_rows),
        "quality_counts": counts(run.dataset_quality or "missing" for run in runs),
        "generation_quality_counts": counts(run.generation_quality_status or "missing" for run in runs),
        "benchmark_rubric_counts": counts(run.benchmark_rubric_status or "missing" for run in runs),
        "release_readiness_comparison_counts": counts(run.release_readiness_comparison_status or "missing" for run in runs),
        "pair_report_counts": {
            "pair_batch": sum(1 for run in run_rows if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists")),
            "pair_trend": sum(1 for run in run_rows if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists")),
        },
        "tag_counts": counts(tag for run in runs for tag in run.tags),
    }


def _dataset_snapshot_summary(runs: list[dict[str, Any]]) -> dict[str, Any]:
    included = [_as_int(run.get("dataset_included_source_count")) for run in runs]
    skipped = [_as_int(run.get("dataset_skipped_source_count")) for run in runs]
    chars = [_as_int(run.get("dataset_char_count")) for run in runs]
    included_values = [value for value in included if value is not None]
    skipped_values = [value for value in skipped if value is not None]
    char_values = [value for value in chars if value is not None]
    return {
        "run_count": len(runs),
        "snapshot_run_count": sum(
            1
            for run in runs
            if run.get("dataset_dedupe_policy") is not None
            or run.get("dataset_source_order_digest") is not None
            or run.get("dataset_included_source_count") is not None
            or run.get("dataset_skipped_source_count") is not None
            or run.get("dataset_char_count") is not None
        ),
        "missing_snapshot_count": sum(
            1
            for run in runs
            if run.get("dataset_dedupe_policy") is None
            and run.get("dataset_source_order_digest") is None
            and run.get("dataset_included_source_count") is None
            and run.get("dataset_skipped_source_count") is None
            and run.get("dataset_char_count") is None
        ),
        "dataset_version_count": len({run.get("dataset_version") for run in runs if run.get("dataset_version")}),
        "dataset_fingerprint_count": len({run.get("dataset_fingerprint") for run in runs if run.get("dataset_fingerprint")}),
        "dedupe_policy_count": len({run.get("dataset_dedupe_policy") for run in runs if run.get("dataset_dedupe_policy")}),
        "source_order_digest_count": len({run.get("dataset_source_order_digest") for run in runs if run.get("dataset_source_order_digest")}),
        "skipped_source_run_count": sum(1 for value in skipped_values if value > 0),
        "total_included_source_count": sum(included_values) if included_values else None,
        "total_skipped_source_count": sum(skipped_values) if skipped_values else None,
        "total_char_count": sum(char_values) if char_values else None,
    }

def _actual_artifact_count(root: Path) -> int:
    return sum(1 for relative in REGISTRY_ARTIFACT_PATHS if (root / relative).exists())


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_run_notes(root: Path) -> dict[str, Any]:
    payload = _read_json(root / "run_notes.json")
    return payload if isinstance(payload, dict) else {}


def _read_generation_quality(root: Path) -> dict[str, Any]:
    candidates = [
        root / "generation-quality" / "generation_quality.json",
        root / "eval_suite" / "generation-quality" / "generation_quality.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["generation_quality_path"] = str(path)
            return payload
    return {}


def _read_benchmark_scorecard(root: Path) -> dict[str, Any]:
    candidates = [
        root / "benchmark-scorecard" / "benchmark_scorecard.json",
        root / "benchmark_scorecard.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["benchmark_scorecard_path"] = str(path)
            return payload
    return {}


def _read_release_readiness_comparison(root: Path) -> dict[str, Any]:
    candidates = [
        root / "release-readiness-comparison" / "release_readiness_comparison.json",
        root / "release_readiness_comparison.json",
    ]
    for path in candidates:
        payload = _read_json(path)
        if isinstance(payload, dict):
            payload["release_readiness_comparison_path"] = str(path)
            return payload
    return {}


def _release_readiness_html_exists(root: Path) -> bool:
    return any(
        path.exists()
        for path in [
            root / "release-readiness-comparison" / "release_readiness_comparison.html",
            root / "release_readiness_comparison.html",
        ]
    )


def _release_readiness_comparison_status(summary: dict[str, Any]) -> str | None:
    if not summary:
        return None
    if int(summary.get("test_coverage_regression_count") or 0) > 0:
        return "coverage-regressed"
    if int(summary.get("benchmark_history_regression_count") or 0) > 0:
        return "benchmark-regressed"
    if int(summary.get("ci_workflow_regression_count") or 0) > 0:
        return "ci-regressed"
    if int(summary.get("regressed_count") or 0) > 0:
        return "regressed"
    if int(summary.get("improved_count") or 0) > 0:
        return "improved"
    if int(summary.get("changed_panel_delta_count") or 0) > 0:
        return "panel-changed"
    if int(summary.get("blocked_count") or 0) > 0:
        return "blocked"
    return "stable"


def _release_readiness_deltas(report: dict[str, Any]) -> list[dict[str, Any]]:
    deltas = report.get("deltas") if isinstance(report, dict) else None
    return [delta for delta in deltas if isinstance(delta, dict)] if isinstance(deltas, list) else []


def _release_readiness_benchmark_requirement_status_change_count(deltas: list[dict[str, Any]]) -> int | None:
    if not deltas:
        return None
    return sum(1 for delta in deltas if bool(delta.get("benchmark_history_readiness_requirement_status_changed")))


def _release_readiness_benchmark_requirement_exit_code_delta_max(deltas: list[dict[str, Any]]) -> int | float | None:
    values = [
        abs(value)
        for value in (_as_optional_float(delta.get("benchmark_history_readiness_requirement_exit_code_delta")) for delta in deltas)
        if value is not None
    ]
    return _int_if_whole(max(values)) if values else None


def _release_readiness_benchmark_requirement_failed_reason_added_count(deltas: list[dict[str, Any]]) -> int | None:
    if not deltas:
        return None
    return sum(_release_readiness_benchmark_requirement_reason_count(delta, "added") for delta in deltas)


def _release_readiness_benchmark_requirement_failed_reason_removed_count(deltas: list[dict[str, Any]]) -> int | None:
    if not deltas:
        return None
    return sum(_release_readiness_benchmark_requirement_reason_count(delta, "removed") for delta in deltas)


def _release_readiness_benchmark_requirement_reason_count(delta: dict[str, Any], kind: str) -> int:
    key = f"benchmark_history_readiness_requirement_failed_reason_{kind}_count"
    direct = _as_int(delta.get(key))
    if direct is not None:
        return direct
    baseline = delta.get("baseline_benchmark_history_readiness_requirement_failed_reasons")
    compared = delta.get("compared_benchmark_history_readiness_requirement_failed_reasons")
    if kind == "added":
        return len(_reason_additions(baseline, compared))
    return len(_reason_removals(baseline, compared))


def _reason_additions(baseline: Any, compared: Any) -> list[str]:
    baseline_reasons = set(_as_str_list(baseline))
    return [reason for reason in _as_str_list(compared) if reason not in baseline_reasons]


def _reason_removals(baseline: Any, compared: Any) -> list[str]:
    compared_reasons = set(_as_str_list(compared))
    return [reason for reason in _as_str_list(baseline) if reason not in compared_reasons]


def _pick(payload: Any, key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    nested = _pick(payload, key)
    return nested if isinstance(nested, dict) else {}


def _nested_pick(payload: Any, section: str, key: str) -> Any:
    nested = _pick(payload, section)
    return _pick(nested, key)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_if_whole(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _as_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


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
