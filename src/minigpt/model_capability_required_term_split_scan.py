from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_holdout import (
    REQUIRED_TERM_HOLDOUT_JSON_FILENAME,
    build_model_capability_required_term_holdout,
    locate_model_capability_required_term_micro_training,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_SPLIT_SCAN_JSON_FILENAME = "model_capability_required_term_split_scan.json"
REQUIRED_TERM_SPLIT_SCAN_TEXT_FILENAME = "model_capability_required_term_split_scan.txt"
REQUIRED_TERM_SPLIT_SCAN_MARKDOWN_FILENAME = "model_capability_required_term_split_scan.md"
REQUIRED_TERM_SPLIT_SCAN_HTML_FILENAME = "model_capability_required_term_split_scan.html"


def build_model_capability_required_term_split_scan(
    micro_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    split_specs: list[dict[str, Any]] | None = None,
    max_iters: int = 800,
    eval_iters: int = 1,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    term_repeat: int = 80,
    max_new_tokens: int = 16,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 485,
    device: str = "cpu",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    specs = split_specs or default_split_specs(micro_report)
    issues = _input_issues(micro_report, specs)
    rows: list[dict[str, Any]] = []
    child_reports: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        split_dir = root / "splits" / str(spec["id"])
        report = build_model_capability_required_term_holdout(
            micro_report,
            out_dir=split_dir,
            source_path=source_path,
            max_iters=max_iters,
            eval_iters=eval_iters,
            batch_size=batch_size,
            block_size=block_size,
            n_layer=n_layer,
            n_head=n_head,
            n_embd=n_embd,
            learning_rate=learning_rate,
            term_repeat=term_repeat,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=generation_seed + (index * 100),
            holdout_terms=[str(term) for term in spec.get("holdout_terms") or []],
            device=device,
        )
        rows.append(_scan_row(spec, report, split_dir))
        child_reports.append(report)
        if report.get("status") != "pass":
            issues.append(f"split {spec['id']} did not complete successfully")

    summary = summarize_required_term_split_scan(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term split scan",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_micro_training": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "term_repeat": term_repeat,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "device": device,
        },
        "split_spec_count": len(specs),
        "split_specs": specs,
        "summary": summary,
        "scan_rows": rows,
        "child_report_count": len(child_reports),
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def default_split_specs(micro_report: dict[str, Any]) -> list[dict[str, Any]]:
    terms = sorted({str(row.get("term") or "") for row in list_of_dicts(micro_report.get("examples")) if row.get("term")})
    if not terms:
        return []
    grouped = [
        terms[::3],
        terms[1::3],
        terms[2::3],
        [term for term in terms if term in {"four", "while"}],
    ]
    specs: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for index, holdouts in enumerate(grouped, start=1):
        selected = tuple(sorted(term for term in holdouts if term))
        if not selected or selected in seen:
            continue
        seen.add(selected)
        specs.append({"id": f"split-{index}", "holdout_terms": list(selected)})
    return specs


def summarize_required_term_split_scan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    train_repro_rows = [row for row in rows if int(row.get("train_continuation_hit_count") or 0) > 0]
    holdout_hit_rows = [row for row in rows if int(row.get("holdout_continuation_hit_count") or 0) > 0]
    complete_rows = [row for row in rows if row.get("status") == "pass"]
    best_train = max((int(row.get("train_continuation_hit_count") or 0) for row in rows), default=0)
    best_holdout = max((int(row.get("holdout_continuation_hit_count") or 0) for row in rows), default=0)
    return {
        "split_scan_decision": _split_scan_decision(rows, train_repro_rows, holdout_hit_rows),
        "split_count": len(rows),
        "complete_split_count": len(complete_rows),
        "train_repro_split_count": len(train_repro_rows),
        "holdout_hit_split_count": len(holdout_hit_rows),
        "best_train_continuation_hit_count": best_train,
        "best_holdout_continuation_hit_count": best_holdout,
        "total_train_continuation_hit_count": sum(int(row.get("train_continuation_hit_count") or 0) for row in rows),
        "total_holdout_continuation_hit_count": sum(int(row.get("holdout_continuation_hit_count") or 0) for row in rows),
        "best_split_id": _best_split_id(rows),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _scan_row(spec: dict[str, Any], report: dict[str, Any], split_dir: Path) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    return {
        "id": spec.get("id"),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "holdout_decision": summary.get("holdout_decision"),
        "holdout_terms": [str(term) for term in spec.get("holdout_terms") or []],
        "train_example_count": summary.get("train_example_count"),
        "holdout_example_count": summary.get("holdout_example_count"),
        "train_continuation_hit_count": summary.get("train_continuation_hit_count"),
        "holdout_continuation_hit_count": summary.get("holdout_continuation_hit_count"),
        "train_hit_rate": summary.get("train_hit_rate"),
        "holdout_hit_rate": summary.get("holdout_hit_rate"),
        "report_json": str(split_dir / REQUIRED_TERM_HOLDOUT_JSON_FILENAME),
        "report_dir": str(split_dir),
    }


def _input_issues(micro_report: dict[str, Any], specs: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not micro_report:
        issues.append("source required-term micro-training report is missing or invalid")
    if micro_report and micro_report.get("status") != "pass":
        issues.append("source required-term micro-training report is not pass")
    if not list_of_dicts(micro_report.get("examples")):
        issues.append("source required-term micro-training report has no examples")
    if not specs:
        issues.append("no split specs available")
    return issues


def _split_scan_decision(
    rows: list[dict[str, Any]],
    train_repro_rows: list[dict[str, Any]],
    holdout_hit_rows: list[dict[str, Any]],
) -> str:
    if not rows:
        return "no_split_scan_rows"
    if holdout_hit_rows:
        return "heldout_required_term_uptake_found"
    if train_repro_rows:
        return "train_slice_uptake_reproduced_without_holdout"
    return "train_slice_uptake_not_reproduced"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_split_scan"
    if int(summary.get("holdout_hit_split_count") or 0) > 0:
        return "required_term_split_scan_holdout_uptake_observed"
    if int(summary.get("train_repro_split_count") or 0) > 0:
        return "required_term_split_scan_train_slice_only"
    return "required_term_split_scan_no_uptake"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("holdout_hit_split_count") or 0) > 0:
        return "heldout_split_scan_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The required-term split scan did not complete cleanly."
    if int(summary.get("holdout_hit_split_count") or 0) > 0:
        return "At least one split produced held-out required-term continuation uptake."
    if int(summary.get("train_repro_split_count") or 0) > 0:
        return "At least one split reproduced train-slice uptake, but no split produced held-out required-term uptake."
    return "No scanned split reproduced required-term continuation uptake."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed split scan rows before changing training scope"
    if int(summary.get("holdout_hit_split_count") or 0) > 0:
        return "repeat the best split with multiple seeds before making a benchmark-level claim"
    if int(summary.get("train_repro_split_count") or 0) > 0:
        return "stabilize the best train-slice split across seeds, then reintroduce a stricter holdout"
    return "change corpus construction before further split scans"


def _best_split_id(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    best = max(
        rows,
        key=lambda row: (
            int(row.get("holdout_continuation_hit_count") or 0),
            int(row.get("train_continuation_hit_count") or 0),
            str(row.get("id") or ""),
        ),
    )
    return str(best.get("id") or "")
