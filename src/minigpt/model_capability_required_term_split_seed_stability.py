from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_holdout import build_model_capability_required_term_holdout
from minigpt.model_capability_required_term_split_scan import (
    REQUIRED_TERM_SPLIT_SCAN_JSON_FILENAME,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_SPLIT_SEED_STABILITY_JSON_FILENAME = "model_capability_required_term_split_seed_stability.json"
REQUIRED_TERM_SPLIT_SEED_STABILITY_TEXT_FILENAME = "model_capability_required_term_split_seed_stability.txt"
REQUIRED_TERM_SPLIT_SEED_STABILITY_MARKDOWN_FILENAME = "model_capability_required_term_split_seed_stability.md"
REQUIRED_TERM_SPLIT_SEED_STABILITY_HTML_FILENAME = "model_capability_required_term_split_seed_stability.html"


def locate_model_capability_required_term_split_scan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_SPLIT_SCAN_JSON_FILENAME
    return source


def build_model_capability_required_term_split_seed_stability(
    split_scan_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: list[int] | None = None,
    max_iters: int | None = None,
    eval_iters: int | None = None,
    batch_size: int | None = None,
    block_size: int | None = None,
    n_layer: int | None = None,
    n_head: int | None = None,
    n_embd: int | None = None,
    learning_rate: float | None = None,
    term_repeat: int | None = None,
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    device: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    settings = _settings(split_scan_report)
    seed_values = seeds or [785, 1785, 2785]
    best = _best_split_row(split_scan_report)
    micro_path = _resolve_micro_report_path(split_scan_report, source_path)
    micro_report = read_json_report(micro_path) if micro_path else {}
    issues = _input_issues(split_scan_report, best, micro_report, seed_values)

    resolved = {
        "max_iters": _first_int(max_iters, settings.get("max_iters"), 800),
        "eval_iters": _first_int(eval_iters, settings.get("eval_iters"), 1),
        "batch_size": _first_int(batch_size, settings.get("batch_size"), 16),
        "block_size": _first_int(block_size, settings.get("block_size"), 8),
        "n_layer": _first_int(n_layer, settings.get("n_layer"), 1),
        "n_head": _first_int(n_head, settings.get("n_head"), 1),
        "n_embd": _first_int(n_embd, settings.get("n_embd"), 64),
        "learning_rate": _first_float(learning_rate, settings.get("learning_rate"), 0.02),
        "term_repeat": _first_int(term_repeat, settings.get("term_repeat"), 80),
        "max_new_tokens": _first_int(max_new_tokens, settings.get("max_new_tokens"), 16),
        "temperature": _first_float(temperature, settings.get("temperature"), 0.2),
        "top_k": _first_int(top_k, settings.get("top_k"), 1),
        "device": str(device or settings.get("device") or "cpu"),
    }

    rows: list[dict[str, Any]] = []
    if best and micro_report:
        holdout_terms = [str(term) for term in best.get("holdout_terms") or []]
        for seed in seed_values:
            seed_dir = root / "seeds" / f"seed-{seed}"
            report = build_model_capability_required_term_holdout(
                micro_report,
                out_dir=seed_dir,
                source_path=micro_path,
                max_iters=resolved["max_iters"],
                eval_iters=resolved["eval_iters"],
                batch_size=resolved["batch_size"],
                block_size=resolved["block_size"],
                n_layer=resolved["n_layer"],
                n_head=resolved["n_head"],
                n_embd=resolved["n_embd"],
                learning_rate=resolved["learning_rate"],
                term_repeat=resolved["term_repeat"],
                max_new_tokens=resolved["max_new_tokens"],
                temperature=resolved["temperature"],
                top_k=resolved["top_k"],
                generation_seed=int(seed),
                holdout_terms=holdout_terms,
                device=resolved["device"],
            )
            rows.append(_seed_row(seed, report, seed_dir))
            if report.get("status") != "pass":
                issues.append(f"seed {seed} did not complete successfully")

    summary = summarize_required_term_split_seed_stability(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term split seed stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_split_scan": str(source_path) if source_path else None,
        "source_required_term_micro_training": str(micro_path) if micro_path else None,
        "out_dir": str(root),
        "best_split": best,
        "settings": resolved | {"seeds": seed_values},
        "summary": summary,
        "seed_rows": rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def summarize_required_term_split_seed_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    complete_rows = [row for row in rows if row.get("status") == "pass"]
    train_repro_rows = [row for row in rows if int(row.get("train_continuation_hit_count") or 0) > 0]
    holdout_rows = [row for row in rows if int(row.get("holdout_continuation_hit_count") or 0) > 0]
    train_hits = [int(row.get("train_continuation_hit_count") or 0) for row in rows]
    holdout_hits = [int(row.get("holdout_continuation_hit_count") or 0) for row in rows]
    return {
        "seed_stability_decision": _seed_stability_decision(rows, train_repro_rows, holdout_rows),
        "seed_count": len(rows),
        "complete_seed_count": len(complete_rows),
        "train_repro_seed_count": len(train_repro_rows),
        "holdout_hit_seed_count": len(holdout_rows),
        "min_train_continuation_hit_count": min(train_hits) if train_hits else 0,
        "max_train_continuation_hit_count": max(train_hits) if train_hits else 0,
        "total_train_continuation_hit_count": sum(train_hits),
        "min_holdout_continuation_hit_count": min(holdout_hits) if holdout_hits else 0,
        "max_holdout_continuation_hit_count": max(holdout_hits) if holdout_hits else 0,
        "total_holdout_continuation_hit_count": sum(holdout_hits),
        "stable_train_repro": bool(rows) and len(train_repro_rows) == len(rows),
        "stable_holdout_zero": bool(rows) and not holdout_rows,
    }


def _settings(report: dict[str, Any]) -> dict[str, Any]:
    return as_dict(report.get("settings"))


def _best_split_row(report: dict[str, Any]) -> dict[str, Any]:
    rows = list_of_dicts(report.get("scan_rows"))
    best_id = str(as_dict(report.get("summary")).get("best_split_id") or "")
    if best_id:
        for row in rows:
            if str(row.get("id") or "") == best_id:
                return row
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            int(row.get("holdout_continuation_hit_count") or 0),
            int(row.get("train_continuation_hit_count") or 0),
            str(row.get("id") or ""),
        ),
    )


def _resolve_micro_report_path(report: dict[str, Any], source_path: str | Path | None) -> Path | None:
    raw = report.get("source_required_term_micro_training")
    if not raw:
        return None
    candidate = Path(str(raw).replace("\\", "/"))
    candidates = [candidate, Path.cwd() / candidate]
    if source_path is not None:
        source_parent = Path(source_path).parent
        candidates.extend(anchor / candidate for anchor in (source_parent, *source_parent.parents))
    for item in candidates:
        if item.is_file():
            return item
        if item.is_dir():
            nested = item / "model_capability_required_term_micro_training.json"
            if nested.is_file():
                return nested
    return candidate


def _input_issues(
    split_scan_report: dict[str, Any],
    best: dict[str, Any],
    micro_report: dict[str, Any],
    seeds: list[int],
) -> list[str]:
    issues: list[str] = []
    if not split_scan_report:
        issues.append("source required-term split scan report is missing or invalid")
    if split_scan_report and split_scan_report.get("status") != "pass":
        issues.append("source required-term split scan report is not pass")
    if not best:
        issues.append("source required-term split scan has no best split")
    if not micro_report:
        issues.append("source required-term micro-training report could not be resolved")
    if not seeds:
        issues.append("no seeds configured")
    return issues


def _seed_row(seed: int, report: dict[str, Any], seed_dir: Path) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "seed": seed,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "holdout_decision": summary.get("holdout_decision"),
        "train_example_count": summary.get("train_example_count"),
        "holdout_example_count": summary.get("holdout_example_count"),
        "train_continuation_hit_count": summary.get("train_continuation_hit_count"),
        "holdout_continuation_hit_count": summary.get("holdout_continuation_hit_count"),
        "train_hit_rate": summary.get("train_hit_rate"),
        "holdout_hit_rate": summary.get("holdout_hit_rate"),
        "report_dir": str(seed_dir),
        "report_json": str(seed_dir / "model_capability_required_term_holdout.json"),
    }


def _seed_stability_decision(
    rows: list[dict[str, Any]],
    train_repro_rows: list[dict[str, Any]],
    holdout_rows: list[dict[str, Any]],
) -> str:
    if not rows:
        return "no_seed_stability_rows"
    if holdout_rows:
        return "heldout_uptake_seen_during_seed_stability"
    if len(train_repro_rows) == len(rows):
        return "train_slice_uptake_stable_without_holdout"
    if train_repro_rows:
        return "train_slice_uptake_partial_without_holdout"
    return "train_slice_uptake_not_stable"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_split_seed_stability"
    if int(summary.get("holdout_hit_seed_count") or 0) > 0:
        return "required_term_seed_stability_holdout_uptake_seen"
    if summary.get("stable_train_repro"):
        return "required_term_seed_stability_train_slice_stable"
    if int(summary.get("train_repro_seed_count") or 0) > 0:
        return "required_term_seed_stability_train_slice_partial"
    return "required_term_seed_stability_no_uptake"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("holdout_hit_seed_count") or 0) > 0:
        return "heldout_seed_stability_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The best-split seed stability check did not complete cleanly."
    if int(summary.get("holdout_hit_seed_count") or 0) > 0:
        return "At least one seed produced held-out required-term continuation uptake."
    if summary.get("stable_train_repro"):
        return "Every repeated seed reproduced train-slice required-term uptake, but held-out uptake stayed at zero."
    if int(summary.get("train_repro_seed_count") or 0) > 0:
        return "Only some repeated seeds reproduced train-slice uptake, and held-out uptake stayed at zero."
    return "No repeated seed reproduced train-slice required-term uptake."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair seed stability inputs before changing model or corpus scale"
    if int(summary.get("holdout_hit_seed_count") or 0) > 0:
        return "run a stricter held-out prompt set before making benchmark-level claims"
    if summary.get("stable_train_repro"):
        return "use this stable train-slice setup to redesign the held-out corpus boundary"
    return "improve corpus construction before further held-out checks"


def _first_int(*values: Any) -> int:
    for value in values:
        if value is not None:
            return int(value)
    return 0


def _first_float(*values: Any) -> float:
    for value in values:
        if value is not None:
            return float(value)
    return 0.0
