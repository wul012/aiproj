from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


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
    dataset_fingerprint: str | None
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
    source = _pick_dict(data, "source")
    generation_summary = _pick_dict(generation_quality, "summary")
    benchmark_summary = _pick_dict(benchmark_scorecard, "summary")
    release_readiness_summary = _pick_dict(release_readiness_comparison, "summary")
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
        dataset_fingerprint=_as_str(_pick(dataset_quality, "short_fingerprint") or _pick(manifest_quality, "short_fingerprint")),
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
    loss_leaderboard = _annotate_loss_leaderboard(run_rows)
    rubric_leaderboard = _annotate_rubric_leaderboard(run_rows)
    pair_delta_rows = _collect_pair_delta_rows(run_dirs, names)
    pair_delta_leaderboard = _pair_delta_leaderboard(pair_delta_rows)
    release_readiness_delta_rows = _collect_release_readiness_delta_rows(run_dirs, names)
    release_readiness_delta_leaderboard = _release_readiness_delta_leaderboard(release_readiness_delta_rows)
    return {
        "schema_version": 1,
        "run_count": len(runs),
        "runs": run_rows,
        "best_by_best_val_loss": _best_by(runs, "best_val_loss"),
        "loss_leaderboard": loss_leaderboard,
        "benchmark_rubric_leaderboard": rubric_leaderboard,
        "benchmark_rubric_summary": _benchmark_rubric_summary(rubric_leaderboard),
        "pair_delta_summary": _pair_delta_summary(pair_delta_rows),
        "pair_delta_leaderboard": pair_delta_leaderboard,
        "release_readiness_delta_summary": _release_readiness_delta_summary(release_readiness_delta_rows),
        "release_readiness_delta_leaderboard": release_readiness_delta_leaderboard,
        "dataset_fingerprints": sorted({run.dataset_fingerprint for run in runs if run.dataset_fingerprint}),
        "quality_counts": _counts(run.dataset_quality or "missing" for run in runs),
        "generation_quality_counts": _counts(run.generation_quality_status or "missing" for run in runs),
        "benchmark_rubric_counts": _counts(run.benchmark_rubric_status or "missing" for run in runs),
        "release_readiness_comparison_counts": _counts(run.release_readiness_comparison_status or "missing" for run in runs),
        "pair_report_counts": {
            "pair_batch": sum(1 for run in run_rows if run.get("pair_batch_cases") is not None or run.get("pair_batch_html_exists")),
            "pair_trend": sum(1 for run in run_rows if run.get("pair_trend_reports") is not None or run.get("pair_trend_html_exists")),
        },
        "tag_counts": _counts(tag for run in runs for tag in run.tags),
    }

def _actual_artifact_count(root: Path) -> int:
    return sum(1 for relative in REGISTRY_ARTIFACT_PATHS if (root / relative).exists())


def _best_by(runs: list[RegisteredRun], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if getattr(run, field) is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda run: getattr(run, field))
    return {"name": best.name, "path": best.path, field: getattr(best, field)}


def _annotate_loss_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for run in runs:
        run["best_val_loss_rank"] = None
        run["best_val_loss_delta"] = None
        run["is_best_val_loss"] = False
    candidates = [
        run
        for run in runs
        if _as_optional_float(run.get("best_val_loss")) is not None
    ]
    candidates.sort(key=lambda run: (_as_optional_float(run.get("best_val_loss")) or float("inf"), str(run.get("name") or "")))
    if not candidates:
        return []
    best_loss = _as_optional_float(candidates[0].get("best_val_loss")) or 0.0
    leaderboard = []
    for rank, run in enumerate(candidates, start=1):
        loss = _as_optional_float(run.get("best_val_loss")) or 0.0
        delta = loss - best_loss
        run["best_val_loss_rank"] = rank
        run["best_val_loss_delta"] = delta
        run["is_best_val_loss"] = rank == 1
        leaderboard.append(
            {
                "rank": rank,
                "name": run.get("name"),
                "path": run.get("path"),
                "best_val_loss": loss,
                "best_val_loss_delta": delta,
                "dataset_quality": run.get("dataset_quality"),
                "eval_suite_cases": run.get("eval_suite_cases"),
                "generation_quality_status": run.get("generation_quality_status"),
                "benchmark_rubric_avg_score": run.get("benchmark_rubric_avg_score"),
                "benchmark_rubric_status": run.get("benchmark_rubric_status"),
                "tags": list(run.get("tags") or []),
                "note": run.get("note"),
            }
        )
    return leaderboard


def _annotate_rubric_leaderboard(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for run in runs:
        run["benchmark_rubric_rank"] = None
        run["benchmark_rubric_delta_from_best"] = None
        run["is_best_benchmark_rubric"] = False
    candidates = [
        run
        for run in runs
        if _as_optional_float(run.get("benchmark_rubric_avg_score")) is not None
    ]
    candidates.sort(key=lambda run: (-(_as_optional_float(run.get("benchmark_rubric_avg_score")) or 0.0), str(run.get("name") or "")))
    if not candidates:
        return []
    best_score = _as_optional_float(candidates[0].get("benchmark_rubric_avg_score")) or 0.0
    leaderboard = []
    for rank, run in enumerate(candidates, start=1):
        score = _as_optional_float(run.get("benchmark_rubric_avg_score")) or 0.0
        delta = score - best_score
        run["benchmark_rubric_rank"] = rank
        run["benchmark_rubric_delta_from_best"] = delta
        run["is_best_benchmark_rubric"] = rank == 1
        leaderboard.append(
            {
                "rank": rank,
                "name": run.get("name"),
                "path": run.get("path"),
                "benchmark_rubric_avg_score": score,
                "benchmark_rubric_delta_from_best": delta,
                "benchmark_rubric_status": run.get("benchmark_rubric_status"),
                "benchmark_weakest_rubric_case": run.get("benchmark_weakest_rubric_case"),
                "benchmark_weakest_rubric_score": run.get("benchmark_weakest_rubric_score"),
                "best_val_loss": run.get("best_val_loss"),
                "generation_quality_status": run.get("generation_quality_status"),
                "tags": list(run.get("tags") or []),
                "note": run.get("note"),
            }
        )
    return leaderboard


def _benchmark_rubric_summary(leaderboard: list[dict[str, Any]]) -> dict[str, Any]:
    if not leaderboard:
        return {
            "available": False,
            "run_count": 0,
            "regression_count": 0,
        }
    regressions = [item for item in leaderboard if (_as_optional_float(item.get("benchmark_rubric_delta_from_best")) or 0.0) < 0]
    weakest = leaderboard[-1]
    largest_regression = min(
        regressions,
        key=lambda item: _as_optional_float(item.get("benchmark_rubric_delta_from_best")) or 0.0,
        default=None,
    )
    best = leaderboard[0]
    return {
        "available": True,
        "run_count": len(leaderboard),
        "best_run": best.get("name"),
        "best_score": best.get("benchmark_rubric_avg_score"),
        "weakest_run": weakest.get("name"),
        "weakest_score": weakest.get("benchmark_rubric_avg_score"),
        "regression_count": len(regressions),
        "largest_regression_run": _pick(largest_regression, "name"),
        "largest_regression_delta": _pick(largest_regression, "benchmark_rubric_delta_from_best"),
    }


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _collect_pair_delta_rows(run_dirs: list[str | Path], names: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, run_dir in enumerate(run_dirs):
        root = Path(run_dir)
        run_name = str(names[index]) if names is not None else root.name
        report_path = root / "pair_batch" / "pair_generation_batch.json"
        report = _read_json(report_path)
        if not isinstance(report, dict):
            continue
        suite = _pick_dict(report, "suite")
        left = _pick_dict(report, "left")
        right = _pick_dict(report, "right")
        for result in report.get("results", []):
            if not isinstance(result, dict):
                continue
            comparison = _pick_dict(result, "comparison")
            generated_delta = _as_optional_float(_pick(comparison, "generated_char_delta"))
            continuation_delta = _as_optional_float(_pick(comparison, "continuation_char_delta"))
            if generated_delta is None and continuation_delta is None:
                continue
            rows.append(
                {
                    "run_name": run_name,
                    "run_path": str(root),
                    "case": _as_str(_pick(result, "name")) or "unknown",
                    "task_type": _as_str(_pick(result, "task_type")),
                    "difficulty": _as_str(_pick(result, "difficulty")),
                    "generated_equal": _pick(comparison, "generated_equal"),
                    "continuation_equal": _pick(comparison, "continuation_equal"),
                    "generated_char_delta": _int_if_whole(generated_delta),
                    "continuation_char_delta": _int_if_whole(continuation_delta),
                    "abs_generated_char_delta": _int_if_whole(abs(generated_delta)) if generated_delta is not None else None,
                    "abs_continuation_char_delta": _int_if_whole(abs(continuation_delta)) if continuation_delta is not None else None,
                    "suite_name": _as_str(_pick(suite, "name")),
                    "suite_version": _as_str(_pick(suite, "version")),
                    "left_checkpoint_id": _as_str(_pick(left, "checkpoint_id")),
                    "right_checkpoint_id": _as_str(_pick(right, "checkpoint_id")),
                    "report_path": str(report_path),
                }
            )
    return rows


def _pair_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            _as_optional_float(item.get("abs_generated_char_delta")) or -1.0,
            _as_optional_float(item.get("abs_continuation_char_delta")) or -1.0,
            str(item.get("run_name") or ""),
            str(item.get("case") or ""),
        ),
        reverse=True,
    )
    return ordered[:limit]


def _pair_delta_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_names = {str(row.get("run_name")) for row in rows if row.get("run_name")}
    generated_values = [_as_optional_float(row.get("abs_generated_char_delta")) for row in rows]
    continuation_values = [_as_optional_float(row.get("abs_continuation_char_delta")) for row in rows]
    generated_values = [value for value in generated_values if value is not None]
    continuation_values = [value for value in continuation_values if value is not None]
    return {
        "case_count": len(rows),
        "run_count": len(run_names),
        "max_abs_generated_char_delta": _int_if_whole(max(generated_values)) if generated_values else None,
        "max_abs_continuation_char_delta": _int_if_whole(max(continuation_values)) if continuation_values else None,
    }


def _collect_release_readiness_delta_rows(run_dirs: list[str | Path], names: list[str] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, run_dir in enumerate(run_dirs):
        root = Path(run_dir)
        run_name = str(names[index]) if names is not None else root.name
        report = _read_release_readiness_comparison(root)
        if not isinstance(report, dict):
            continue
        report_path = _as_str(report.get("release_readiness_comparison_path"))
        for delta in report.get("deltas", []):
            if not isinstance(delta, dict):
                continue
            changed_panels = _as_str_list(delta.get("changed_panels"))
            rows.append(
                {
                    "run_name": run_name,
                    "run_path": str(root),
                    "baseline_release": _as_str(delta.get("baseline_release")),
                    "compared_release": _as_str(delta.get("compared_release")),
                    "baseline_status": _as_str(delta.get("baseline_status")),
                    "compared_status": _as_str(delta.get("compared_status")),
                    "status_delta": _int_if_whole(_as_optional_float(delta.get("status_delta"))),
                    "delta_status": _as_str(delta.get("delta_status")) or "same",
                    "audit_score_delta": _int_if_whole(_as_optional_float(delta.get("audit_score_delta"))),
                    "missing_artifact_delta": _int_if_whole(_as_optional_float(delta.get("missing_artifact_delta"))),
                    "fail_panel_delta": _int_if_whole(_as_optional_float(delta.get("fail_panel_delta"))),
                    "warn_panel_delta": _int_if_whole(_as_optional_float(delta.get("warn_panel_delta"))),
                    "changed_panel_count": len(changed_panels),
                    "changed_panels": changed_panels,
                    "explanation": _as_str(delta.get("explanation")),
                    "report_path": report_path,
                }
            )
    return rows


def _release_readiness_delta_leaderboard(rows: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    status_priority = {"regressed": 0, "improved": 1, "panel-changed": 2, "same": 3}
    ordered = sorted(
        rows,
        key=lambda item: (
            status_priority.get(str(item.get("delta_status") or ""), 4),
            -abs(_as_optional_float(item.get("status_delta")) or 0.0),
            -int(item.get("changed_panel_count") or 0),
            str(item.get("run_name") or ""),
            str(item.get("compared_release") or ""),
        ),
    )
    return ordered[:limit]


def _release_readiness_delta_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    run_names = {str(row.get("run_name")) for row in rows if row.get("run_name")}
    counts = _counts(row.get("delta_status") or "missing" for row in rows)
    status_deltas = [abs(value) for value in (_as_optional_float(row.get("status_delta")) for row in rows) if value is not None]
    return {
        "delta_count": len(rows),
        "run_count": len(run_names),
        "regressed_count": counts.get("regressed", 0),
        "improved_count": counts.get("improved", 0),
        "panel_changed_count": counts.get("panel-changed", 0),
        "same_count": counts.get("same", 0),
        "changed_panel_delta_count": sum(1 for row in rows if int(row.get("changed_panel_count") or 0) > 0),
        "max_abs_status_delta": _int_if_whole(max(status_deltas)) if status_deltas else None,
    }


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
    if int(summary.get("regressed_count") or 0) > 0:
        return "regressed"
    if int(summary.get("improved_count") or 0) > 0:
        return "improved"
    if int(summary.get("changed_panel_delta_count") or 0) > 0:
        return "panel-changed"
    if int(summary.get("blocked_count") or 0) > 0:
        return "blocked"
    return "stable"


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
