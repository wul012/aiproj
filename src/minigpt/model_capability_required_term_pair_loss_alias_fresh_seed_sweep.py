from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc
from minigpt.model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare import (
    build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare,
    locate_loss_alias_blocked_token_fresh_compare_source,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_FRESH_SEED_SWEEP_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_fresh_seed_sweep.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_FRESH_SEED_SWEEP_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_fresh_seed_sweep.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_FRESH_SEED_SWEEP_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_fresh_seed_sweep.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_FRESH_SEED_SWEEP_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_fresh_seed_sweep.html"
)


def locate_loss_alias_fresh_seed_sweep_source(path: str | Path) -> Path:
    return locate_loss_alias_blocked_token_fresh_compare_source(path)


def build_model_capability_required_term_pair_loss_alias_fresh_seed_sweep(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = (527, 528, 529),
    base_repeat: int = 180,
    focus_repeat: int = 180,
    bridge_repeat: int = 4,
    max_iters: int = 900,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    focus_generate_func: GenerateFunc | None = None,
    probe_generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    timestamp = generated_at or utc_now()
    compare_report_dir = root / "fresh-compare-report"
    compare_run_dir = root / "fresh-compare-run"
    compare_report = build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
        stability_report,
        out_dir=compare_run_dir,
        source_path=source_path,
        seeds=seeds,
        base_repeat=base_repeat,
        focus_repeat=focus_repeat,
        bridge_repeat=bridge_repeat,
        max_iters=max_iters,
        eval_iters=eval_iters,
        batch_size=batch_size,
        block_size=block_size,
        n_layer=n_layer,
        n_head=n_head,
        n_embd=n_embd,
        learning_rate=learning_rate,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        device=device,
        generated_at=timestamp,
        train_func=train_func,
        focus_generate_func=focus_generate_func,
        probe_generate_func=probe_generate_func,
    )
    issues = [] if compare_report.get("status") == "pass" else ["fresh seed compare report did not pass structurally"]
    seed_rows = _seed_rows(compare_report)
    summary = _summary(seed_rows, compare_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias fresh seed sweep",
        "generated_at": timestamp,
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_alias_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "sidecar_dirs": {
            "fresh_compare_report": str(compare_report_dir),
            "fresh_compare_run": str(compare_run_dir),
        },
        "settings": {
            "seeds": [int(seed) for seed in seeds],
            "base_repeat": base_repeat,
            "focus_repeat": focus_repeat,
            "bridge_repeat": bridge_repeat,
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
        },
        "seed_rows": seed_rows,
        "fresh_compare_report": compare_report,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _seed_rows(compare_report: dict[str, Any]) -> list[dict[str, Any]]:
    focus = as_dict(compare_report.get("fresh_focus_report"))
    probe = as_dict(compare_report.get("blocked_token_probe_report"))
    probe_rows = list_of_dicts(probe.get("case_rows"))
    rows: list[dict[str, Any]] = []
    for seed_report in list_of_dicts(focus.get("seed_reports")):
        seed = int(as_dict(seed_report.get("settings")).get("generation_seed") or 0)
        seed_probe_rows = [row for row in probe_rows if int(row.get("seed") or 0) == seed]
        baseline_rows = [row for row in seed_probe_rows if row.get("profile_id") == "baseline_rerun"]
        blocked_rows = [row for row in seed_probe_rows if row.get("profile_id") == "suppress_newline_tokens"]
        seed_summary = as_dict(seed_report.get("summary"))
        baseline_hits = sum(1 for row in baseline_rows if row.get("strict_hit"))
        blocked_hits = sum(1 for row in blocked_rows if row.get("strict_hit"))
        rows.append(
            {
                "seed": seed,
                "status": seed_report.get("status"),
                "checkpoint_exists": bool(seed_summary.get("checkpoint_exists")),
                "case_count": len(baseline_rows),
                "baseline_strict_hit_count": baseline_hits,
                "baseline_strict_full_coverage": bool(baseline_rows) and baseline_hits == len(baseline_rows),
                "blocked_token_strict_hit_count": blocked_hits,
                "blocked_token_strict_full_coverage": bool(blocked_rows) and blocked_hits == len(blocked_rows),
                "blocked_token_strict_gain_count": sum(1 for row in blocked_rows if row.get("strict_gain")),
                "fresh_focus_strict_full_coverage": bool(seed_summary.get("support_full_coverage")),
                "fresh_focus_newline_cleanup_full_coverage": bool(seed_summary.get("support_newline_cleanup_full_coverage")),
                "out_dir": seed_report.get("out_dir"),
            }
        )
    return rows


def _summary(seed_rows: list[dict[str, Any]], compare_report: dict[str, Any]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    baseline_full_seed_count = sum(1 for row in seed_rows if row.get("baseline_strict_full_coverage"))
    blocked_full_seed_count = sum(1 for row in seed_rows if row.get("blocked_token_strict_full_coverage"))
    return {
        "fresh_compare_status": compare_report.get("status"),
        "fresh_compare_decision": compare_report.get("decision"),
        "seed_count": seed_count,
        "pass_seed_count": sum(1 for row in seed_rows if row.get("status") == "pass"),
        "checkpoint_seed_count": sum(1 for row in seed_rows if row.get("checkpoint_exists")),
        "baseline_strict_full_seed_count": baseline_full_seed_count,
        "blocked_token_strict_full_seed_count": blocked_full_seed_count,
        "stable_baseline_strict_full_coverage": seed_count > 0 and baseline_full_seed_count == seed_count,
        "stable_blocked_token_strict_full_coverage": seed_count > 0 and blocked_full_seed_count == seed_count,
        "blocked_token_gain_seed_count": sum(1 for row in seed_rows if int(row.get("blocked_token_strict_gain_count") or 0) > 0),
        "total_blocked_token_strict_gain_count": sum(int(row.get("blocked_token_strict_gain_count") or 0) for row in seed_rows),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_fresh_seed_sweep"
    if summary.get("stable_baseline_strict_full_coverage"):
        return "required_term_pair_loss_alias_fresh_seed_sweep_baseline_stably_strict"
    if summary.get("stable_blocked_token_strict_full_coverage"):
        return "required_term_pair_loss_alias_fresh_seed_sweep_blocked_token_stably_recovers"
    if int(summary.get("total_blocked_token_strict_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_fresh_seed_sweep_blocked_token_partial_recovery"
    return "required_term_pair_loss_alias_fresh_seed_sweep_unstable"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("stable_baseline_strict_full_coverage"):
        return "fresh_tiny_loss_alias_baseline_decode_stably_strict"
    if summary.get("stable_blocked_token_strict_full_coverage"):
        return "fresh_tiny_loss_alias_blocked_token_decode_stably_recovers"
    if int(summary.get("total_blocked_token_strict_gain_count") or 0) > 0:
        return "fresh_tiny_loss_alias_blocked_token_decode_partial_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The multi-seed fresh compare did not complete structurally."
    if summary.get("stable_baseline_strict_full_coverage"):
        return "Every fresh seed reached strict loss-alias coverage with default decoding."
    if summary.get("stable_blocked_token_strict_full_coverage"):
        return "Default decoding was not stably strict, but blocked-token decoding recovered every seed."
    if int(summary.get("total_blocked_token_strict_gain_count") or 0) > 0:
        return "Blocked-token decoding helped at least one fresh seed but did not produce stable coverage."
    return "Fresh seeds did not establish stable strict coverage or blocked-token recovery."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair fresh seed sweep evidence before changing generation defaults"
    if summary.get("stable_baseline_strict_full_coverage"):
        return "compare the stable fresh baseline against pair coexistence prompts before changing decoding"
    if summary.get("stable_blocked_token_strict_full_coverage"):
        return "keep blocked-token as an explicit profile and test it in the playground/API surface"
    if int(summary.get("total_blocked_token_strict_gain_count") or 0) > 0:
        return "inspect seed-level failures before broadening the blocked-token profile"
    return "return to corpus or objective tuning because fresh seeds are still unstable"
