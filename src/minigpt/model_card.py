from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_card_artifacts import (
    render_model_card_html,
    render_model_card_markdown,
    write_model_card_html,
    write_model_card_json,
    write_model_card_markdown,
    write_model_card_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    list_of_dicts as _list_of_dicts,
    utc_now,
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
