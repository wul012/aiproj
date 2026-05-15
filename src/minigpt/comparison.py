from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from minigpt.comparison_artifacts import (
    render_comparison_html,
    render_comparison_markdown,
    write_comparison_csv,
    write_comparison_html,
    write_comparison_json,
    write_comparison_markdown,
    write_comparison_outputs,
    write_comparison_svg,
)


@dataclass(frozen=True)
class RunComparison:
    name: str
    path: str
    tokenizer: str | None
    dataset_version: str | None
    dataset_fingerprint: str | None
    max_iters: int | None
    metrics_records: int
    best_val_loss: float | None
    last_val_loss: float | None
    eval_loss: float | None
    perplexity: float | None
    total_parameters: int | None
    n_layer: int | None
    n_head: int | None
    n_embd: int | None
    block_size: int | None
    vocab_size: int | None
    token_count: int | None
    train_token_count: int | None
    val_token_count: int | None
    model_signature: str
    dashboard_exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_run(run_dir: str | Path, name: str | None = None) -> RunComparison:
    root = Path(run_dir)
    train_config = _read_json(root / "train_config.json")
    history_summary = _read_json(root / "history_summary.json")
    eval_report = _read_json(root / "eval_report.json")
    model_report = _read_json(root / "model_report" / "model_report.json")
    run_manifest = _read_json(root / "run_manifest.json")
    dataset_quality = _read_json(root / "dataset_quality.json")
    dataset_version_report = _read_json(root / "dataset_version.json")

    manifest_data = _pick_dict(run_manifest, "data")
    manifest_training = _pick_dict(run_manifest, "training")
    manifest_model = _pick_dict(run_manifest, "model")
    manifest_args = _pick_dict(manifest_training, "args")
    manifest_dataset_version = _pick_dict(manifest_data, "dataset_version")
    manifest_dataset_quality = _pick_dict(manifest_data, "dataset_quality")

    report_config = _pick_dict(model_report, "config")
    manifest_config = _pick_dict(manifest_model, "config")
    config = manifest_config or report_config

    tokenizer = _as_str(
        _pick(manifest_training, "tokenizer")
        or _pick(train_config, "tokenizer")
        or _pick(eval_report, "tokenizer")
        or _pick(model_report, "tokenizer")
    )
    max_iters = _as_int(
        _pick(train_config, "max_iters")
        or _pick(manifest_args, "max_iters")
        or _pick(manifest_training, "end_step")
    )
    total_parameters = _as_int(_pick(manifest_model, "parameter_count") or _pick(model_report, "total_parameters"))
    n_layer = _as_int(_pick(config, "n_layer"))
    n_head = _as_int(_pick(config, "n_head"))
    n_embd = _as_int(_pick(config, "n_embd"))
    block_size = _as_int(_pick(config, "block_size"))
    vocab_size = _as_int(_pick(config, "vocab_size"))
    dataset_version = _as_str(
        _pick(manifest_dataset_version, "id")
        or _nested_pick(dataset_version_report, "dataset", "id")
    )
    dataset_fingerprint = _as_str(
        _pick(manifest_dataset_version, "short_fingerprint")
        or _nested_pick(dataset_version_report, "stats", "short_fingerprint")
        or _pick(manifest_dataset_quality, "short_fingerprint")
        or _pick(dataset_quality, "short_fingerprint")
    )

    return RunComparison(
        name=name or root.name,
        path=str(root),
        tokenizer=tokenizer,
        dataset_version=dataset_version,
        dataset_fingerprint=dataset_fingerprint,
        max_iters=max_iters,
        metrics_records=_line_count(root / "metrics.jsonl"),
        best_val_loss=_as_float(_pick(history_summary, "best_val_loss") or _nested_pick(run_manifest, "results", "history_summary", "best_val_loss")),
        last_val_loss=_as_float(_pick(history_summary, "last_val_loss") or _nested_pick(run_manifest, "results", "history_summary", "last_val_loss")),
        eval_loss=_as_float(_pick(eval_report, "loss")),
        perplexity=_as_float(_pick(eval_report, "perplexity")),
        total_parameters=total_parameters,
        n_layer=n_layer,
        n_head=n_head,
        n_embd=n_embd,
        block_size=block_size,
        vocab_size=vocab_size,
        token_count=_as_int(_pick(manifest_data, "token_count")),
        train_token_count=_as_int(_pick(manifest_data, "train_token_count")),
        val_token_count=_as_int(_pick(manifest_data, "val_token_count")),
        model_signature=_model_signature(
            tokenizer=tokenizer,
            n_layer=n_layer,
            n_head=n_head,
            n_embd=n_embd,
            block_size=block_size,
            vocab_size=vocab_size,
            total_parameters=total_parameters,
            max_iters=max_iters,
        ),
        dashboard_exists=(root / "dashboard.html").exists(),
    )


def build_comparison_report(
    run_dirs: list[str | Path],
    names: list[str] | None = None,
    *,
    baseline: str | int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not run_dirs:
        raise ValueError("At least one run directory is required")
    if names is not None and len(names) != len(run_dirs):
        raise ValueError("names length must match run_dirs length")

    runs = [
        summarize_run(run_dir, name=None if names is None else names[index])
        for index, run_dir in enumerate(run_dirs)
    ]
    baseline_run = _select_baseline(runs, baseline)
    baseline_deltas = [_baseline_delta(run, baseline_run) for run in runs]
    summary = _comparison_summary(runs, baseline_run, baseline_deltas)
    report = {
        "schema_version": 2,
        "generated_at": generated_at or _utc_now(),
        "run_count": len(runs),
        "baseline": baseline_run.to_dict(),
        "runs": [run.to_dict() for run in runs],
        "baseline_deltas": baseline_deltas,
        "summary": summary,
        "best_by_best_val_loss": _best_run(runs, "best_val_loss"),
        "best_by_eval_loss": _best_run(runs, "eval_loss"),
        "best_by_perplexity": _best_run(runs, "perplexity"),
        "recommendations": _comparison_recommendations(runs, baseline_run, baseline_deltas, summary),
    }
    return report


def _select_baseline(runs: list[RunComparison], baseline: str | int | None) -> RunComparison:
    if baseline is None:
        return runs[0]
    if isinstance(baseline, int):
        if baseline < 0 or baseline >= len(runs):
            raise ValueError(f"baseline index out of range: {baseline}")
        return runs[baseline]
    wanted = baseline.strip()
    if not wanted:
        raise ValueError("baseline cannot be empty")
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(runs):
            return runs[index]
    for run in runs:
        if wanted in {run.name, run.path, Path(run.path).name}:
            return run
    raise ValueError(f"baseline did not match a run name, path, or 1-based index: {baseline}")


def _baseline_delta(run: RunComparison, baseline: RunComparison) -> dict[str, Any]:
    best_delta = _delta(run.best_val_loss, baseline.best_val_loss)
    params_ratio = _ratio(run.total_parameters, baseline.total_parameters)
    return {
        "name": run.name,
        "path": run.path,
        "baseline_name": baseline.name,
        "is_baseline": run.path == baseline.path,
        "best_val_loss_delta": best_delta,
        "best_val_loss_delta_pct": _pct_delta(run.best_val_loss, baseline.best_val_loss),
        "eval_loss_delta": _delta(run.eval_loss, baseline.eval_loss),
        "perplexity_delta": _delta(run.perplexity, baseline.perplexity),
        "total_parameters_delta": _int_delta(run.total_parameters, baseline.total_parameters),
        "total_parameters_ratio": params_ratio,
        "max_iters_delta": _int_delta(run.max_iters, baseline.max_iters),
        "tokenizer_changed": _changed(run.tokenizer, baseline.tokenizer),
        "model_signature_changed": _changed(run.model_signature, baseline.model_signature),
        "dataset_version_changed": _changed(run.dataset_version, baseline.dataset_version),
        "best_val_loss_relation": _loss_relation(best_delta, is_baseline=run.path == baseline.path),
    }


def _comparison_summary(
    runs: list[RunComparison],
    baseline: RunComparison,
    deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    dataset_versions = sorted({run.dataset_version for run in runs if run.dataset_version})
    model_signatures = sorted({run.model_signature for run in runs if run.model_signature})
    tokenizers = sorted({run.tokenizer for run in runs if run.tokenizer})
    return {
        "baseline_name": baseline.name,
        "baseline_path": baseline.path,
        "baseline_best_val_loss": baseline.best_val_loss,
        "comparable_best_val_loss_count": sum(1 for run in runs if run.best_val_loss is not None),
        "improved_best_val_loss_count": sum(1 for row in deltas if row.get("best_val_loss_relation") == "improved"),
        "regressed_best_val_loss_count": sum(1 for row in deltas if row.get("best_val_loss_relation") == "regressed"),
        "tied_best_val_loss_count": sum(1 for row in deltas if row.get("best_val_loss_relation") == "tied"),
        "missing_best_val_loss_count": sum(1 for row in deltas if row.get("best_val_loss_relation") == "missing"),
        "tokenizers": tokenizers,
        "tokenizer_count": len(tokenizers),
        "model_signatures": model_signatures,
        "model_signature_count": len(model_signatures),
        "dataset_versions": dataset_versions,
        "dataset_version_count": len(dataset_versions),
    }


def _comparison_recommendations(
    runs: list[RunComparison],
    baseline: RunComparison,
    deltas: list[dict[str, Any]],
    summary: dict[str, Any],
) -> list[str]:
    recommendations: list[str] = []
    best = _best_run(runs, "best_val_loss")
    if best is None or baseline.best_val_loss is None:
        recommendations.append("Record best_val_loss for all candidate runs before making a model decision.")
    elif best["name"] == baseline.name:
        recommendations.append("The baseline remains the best run by best_val_loss; keep it as the reference until a candidate beats it.")
    else:
        best_delta = next((row for row in deltas if row.get("name") == best["name"]), {})
        recommendations.append(
            f"{best['name']} beats the baseline by {_fmt_signed(best_delta.get('best_val_loss_delta'))} best_val_loss; inspect generation quality before promoting it."
        )
    if summary.get("dataset_version_count", 0) > 1:
        recommendations.append("Dataset versions differ across runs; compare model changes separately from data changes.")
    if summary.get("model_signature_count", 0) <= 1:
        recommendations.append("All runs share the same model signature; add at least one size/tokenizer/training-step variant for a stronger baseline comparison.")
    if any(run.eval_loss is None for run in runs):
        recommendations.append("Some runs are missing eval_report.json; run the evaluation script so eval_loss and perplexity deltas are comparable.")
    if any(run.dataset_version is None for run in runs):
        recommendations.append("Some runs are missing dataset_version.json; rerun training from a versioned prepared dataset when possible.")
    return recommendations


def _best_run(runs: list[RunComparison], field: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if getattr(run, field) is not None]
    if not candidates:
        return None
    best = min(candidates, key=lambda run: getattr(run, field))
    return {"name": best.name, "path": best.path, field: getattr(best, field)}


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    value = _pick(payload, key)
    return value if isinstance(value, dict) else {}


def _nested_pick(payload: Any, *keys: str) -> Any:
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _delta(value: Any, baseline: Any) -> float | None:
    if value is None or baseline is None:
        return None
    return float(value) - float(baseline)


def _int_delta(value: Any, baseline: Any) -> int | None:
    if value is None or baseline is None:
        return None
    return int(value) - int(baseline)


def _pct_delta(value: Any, baseline: Any) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return (float(value) - float(baseline)) / float(baseline) * 100


def _ratio(value: Any, baseline: Any) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return float(value) / float(baseline)


def _changed(value: Any, baseline: Any) -> bool | None:
    if value is None or baseline is None:
        return None
    return value != baseline


def _loss_relation(delta: float | None, *, is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    if delta is None:
        return "missing"
    if delta < 0:
        return "improved"
    if delta > 0:
        return "regressed"
    return "tied"


def _model_signature(
    *,
    tokenizer: str | None,
    n_layer: int | None,
    n_head: int | None,
    n_embd: int | None,
    block_size: int | None,
    vocab_size: int | None,
    total_parameters: int | None,
    max_iters: int | None,
) -> str:
    return "|".join(
        [
            f"tok={tokenizer or 'unknown'}",
            f"L={_missing(n_layer)}",
            f"H={_missing(n_head)}",
            f"E={_missing(n_embd)}",
            f"B={_missing(block_size)}",
            f"V={_missing(vocab_size)}",
            f"P={_missing(total_parameters)}",
            f"steps={_missing(max_iters)}",
        ]
    )


def _missing(value: Any) -> str:
    return "?" if value is None else str(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = float(value)
    return f"{number:+.5g}"
