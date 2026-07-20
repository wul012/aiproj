from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc
from minigpt.model_capability_required_term_pair_loss_alias_focus import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME,
    build_model_capability_required_term_pair_loss_alias_focus,
    locate_model_capability_required_term_pair_loss_alias_focus_source,
    read_json_report as read_json_report,
)
from minigpt.model_capability_required_term_pair_loss_alias_newline_suppression_probe import (
    build_model_capability_required_term_pair_loss_alias_newline_suppression_probe,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_BLOCKED_TOKEN_FRESH_COMPARE_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare.html"
)


def locate_loss_alias_blocked_token_fresh_compare_source(path: str | Path) -> Path:
    return locate_model_capability_required_term_pair_loss_alias_focus_source(path)


def build_model_capability_required_term_pair_loss_alias_blocked_token_fresh_compare(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = (527,),
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
    focus_report_dir = root / "fresh-focus-report"
    focus_run_dir = root / "fresh-focus-run"
    probe_report_dir = root / "blocked-token-probe-report"
    focus_report = build_model_capability_required_term_pair_loss_alias_focus(
        stability_report,
        out_dir=focus_run_dir,
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
        generate_func=focus_generate_func,
    )
    issues = _focus_issues(focus_report)
    probe_report: dict[str, Any] = {}
    if not issues:
        probe_report = build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
            focus_report,
            out_dir=probe_report_dir,
            source_path=focus_report_dir / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME,
            generated_at=timestamp,
            generate_func=probe_generate_func,
        )
        issues.extend(_probe_issues(probe_report))
    summary = _summary(focus_report, probe_report)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias blocked-token fresh compare",
        "generated_at": timestamp,
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_alias_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "sidecar_dirs": {
            "fresh_focus_run": str(focus_run_dir),
            "fresh_focus_report": str(focus_report_dir),
            "blocked_token_probe_report": str(probe_report_dir),
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
            "blocked_token_profile": ["\\n", "\\r"],
        },
        "fresh_focus_report": focus_report,
        "blocked_token_probe_report": probe_report,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def _focus_issues(focus_report: dict[str, Any]) -> list[str]:
    if focus_report.get("status") == "pass":
        return []
    return ["fresh focus report did not pass structurally"]


def _probe_issues(probe_report: dict[str, Any]) -> list[str]:
    if probe_report.get("status") == "pass":
        return []
    return ["blocked-token probe report did not pass structurally"]


def _summary(focus_report: dict[str, Any], probe_report: dict[str, Any]) -> dict[str, Any]:
    focus_summary = as_dict(focus_report.get("summary"))
    probe_summary = as_dict(probe_report.get("summary"))
    return {
        "fresh_focus_status": focus_report.get("status"),
        "fresh_focus_decision": focus_report.get("decision"),
        "fresh_focus_surface_decision": focus_summary.get("loss_alias_focus_surface_decision"),
        "fresh_focus_metric_decision": focus_summary.get("loss_alias_focus_metric_decision"),
        "fresh_focus_seed_count": focus_summary.get("seed_count"),
        "fresh_focus_checkpoint_seed_count": focus_summary.get("checkpoint_seed_count"),
        "fresh_focus_strict_full_coverage": focus_summary.get("stable_support_full_coverage"),
        "fresh_focus_newline_cleanup_full_coverage": focus_summary.get("stable_support_newline_cleanup_full_coverage"),
        "blocked_token_probe_status": probe_report.get("status"),
        "blocked_token_probe_decision": probe_report.get("decision"),
        "blocked_token_surface_decision": probe_summary.get("newline_suppression_decision"),
        "case_count": probe_summary.get("case_count", 0),
        "baseline_strict_hit_count": probe_summary.get("baseline_strict_hit_count", 0),
        "baseline_strict_full_coverage": probe_summary.get("baseline_strict_full_coverage", False),
        "blocked_token_strict_hit_count": probe_summary.get("suppressed_strict_hit_count", 0),
        "blocked_token_strict_full_coverage": probe_summary.get("suppressed_strict_full_coverage", False),
        "blocked_token_focus_strict_full_coverage": probe_summary.get("suppressed_focus_strict_full_coverage", False),
        "blocked_token_strict_gain_count": probe_summary.get("suppressed_strict_gain_count", 0),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_blocked_token_fresh_compare"
    if summary.get("blocked_token_strict_full_coverage") and not summary.get("baseline_strict_full_coverage"):
        return "required_term_pair_loss_alias_blocked_token_fresh_strict_recovery"
    if summary.get("baseline_strict_full_coverage"):
        return "required_term_pair_loss_alias_blocked_token_fresh_baseline_already_strict"
    if int(summary.get("blocked_token_strict_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_blocked_token_fresh_partial_recovery"
    return "required_term_pair_loss_alias_blocked_token_fresh_no_recovery"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("blocked_token_strict_full_coverage") and not summary.get("baseline_strict_full_coverage"):
        return "fresh_tiny_loss_alias_blocked_token_decoding_recovers_strict_surface"
    if summary.get("baseline_strict_full_coverage"):
        return "fresh_tiny_loss_alias_baseline_decode_already_strict"
    if int(summary.get("blocked_token_strict_gain_count") or 0) > 0:
        return "fresh_tiny_loss_alias_blocked_token_partial_decode_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The fresh focus training or blocked-token probe did not complete structurally."
    if summary.get("blocked_token_strict_full_coverage") and not summary.get("baseline_strict_full_coverage"):
        return "A fresh focused checkpoint still misses strict loss hits with default decoding, while newline-token blocking recovers every probed row."
    if summary.get("baseline_strict_full_coverage"):
        return "The fresh focused checkpoint already emits strict loss hits without blocked-token decoding."
    if int(summary.get("blocked_token_strict_gain_count") or 0) > 0:
        return "Blocked-token decoding recovered some strict loss rows on the fresh focused checkpoint."
    return "The fresh focused checkpoint did not gain strict loss hits from blocked-token decoding."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair fresh focus or probe evidence before changing decoding defaults"
    if summary.get("blocked_token_strict_full_coverage") and not summary.get("baseline_strict_full_coverage"):
        return "add an explicit generation profile comparison before making blocked tokens a default playground option"
    if summary.get("baseline_strict_full_coverage"):
        return "compare this stronger fresh seed against earlier checkpoints before claiming a general training improvement"
    if int(summary.get("blocked_token_strict_gain_count") or 0) > 0:
        return "inspect the unrecovered rows before broadening the blocked-token profile"
    return "return to corpus or objective tuning because blocked-token decoding did not help the fresh run"
