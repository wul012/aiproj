from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc
from minigpt.model_capability_required_term_pair_continuation_span_objective import (
    PrefixSweepFunc,
    build_model_capability_required_term_pair_continuation_span_objective,
)
from minigpt.model_capability_required_term_pair_diagnostic_rollup import (
    REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_JSON_FILENAME = "model_capability_required_term_pair_continuation_span_stability.json"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_TEXT_FILENAME = "model_capability_required_term_pair_continuation_span_stability.txt"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_MARKDOWN_FILENAME = "model_capability_required_term_pair_continuation_span_stability.md"
REQUIRED_TERM_PAIR_CONTINUATION_SPAN_STABILITY_HTML_FILENAME = "model_capability_required_term_pair_continuation_span_stability.html"
DEFAULT_CONTINUATION_SPAN_STABILITY_SEEDS = (510, 511)


def locate_model_capability_required_term_pair_continuation_span_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_continuation_span_stability(
    rollup_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = DEFAULT_CONTINUATION_SPAN_STABILITY_SEEDS,
    repeat: int = 160,
    bridge_repeat: int = 4,
    max_iters: int = 800,
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
    generate_func: GenerateFunc | None = None,
    prefix_sweep_func: PrefixSweepFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    clean_seeds = _clean_seeds(seeds)
    issues = _input_issues(rollup_report, clean_seeds)
    seed_reports: list[dict[str, Any]] = []
    if not issues:
        for index, seed in enumerate(clean_seeds):
            seed_reports.append(
                build_model_capability_required_term_pair_continuation_span_objective(
                    rollup_report,
                    out_dir=root / "seed-runs" / f"seed-{seed}",
                    source_path=source_path,
                    repeat=repeat,
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
                    generation_seed=seed,
                    device=device,
                    generated_at=generated_at,
                    train_func=train_func,
                    generate_func=generate_func,
                    prefix_sweep_func=prefix_sweep_func,
                )
            )
            if seed_reports[index].get("status") != "pass":
                issues.append(f"seed {seed} continuation-span objective did not pass")

    seed_rows = summarize_continuation_span_seed_rows(clean_seeds, seed_reports)
    summary = summarize_continuation_span_stability(seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair continuation-span stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_diagnostic_rollup": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": clean_seeds,
            "seed_count": len(clean_seeds),
            "repeat": max(1, int(repeat)),
            "bridge_repeat": max(0, int(bridge_repeat)),
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
            "experiment_boundary": "repeat the v510 continuation-span objective across seeds before treating prefix gain as stable",
        },
        "seed_rows": seed_rows,
        "seed_reports": seed_reports,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def summarize_continuation_span_seed_rows(seeds: list[int], reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, report in zip(seeds, reports):
        summary = as_dict(report.get("summary"))
        rows.append(
            {
                "seed": seed,
                "status": report.get("status"),
                "decision": report.get("decision"),
                "continuation_span_decision": summary.get("continuation_span_decision"),
                "checkpoint_exists": summary.get("checkpoint_exists"),
                "generation_hit_count": summary.get("generation_hit_count"),
                "candidate_pair_full_generation_hit": summary.get("candidate_pair_full_generation_hit"),
                "candidate_one_token_prefix_hit_count": summary.get("candidate_one_token_prefix_hit_count"),
                "prefix_minimum_improved_count": summary.get("prefix_minimum_improved_count"),
                "source_one_token_retained_count": summary.get("source_one_token_retained_count"),
                "out_dir": report.get("out_dir"),
            }
        )
    return rows


def summarize_continuation_span_stability(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    pass_count = sum(1 for row in seed_rows if row.get("status") == "pass")
    checkpoint_count = sum(1 for row in seed_rows if row.get("checkpoint_exists"))
    prefix_gain_count = sum(1 for row in seed_rows if int(row.get("prefix_minimum_improved_count") or 0) > 0)
    full_pair_count = sum(1 for row in seed_rows if row.get("candidate_pair_full_generation_hit"))
    one_token_both_count = sum(1 for row in seed_rows if int(row.get("candidate_one_token_prefix_hit_count") or 0) >= 2)
    return {
        "continuation_span_stability_decision": _stability_decision(seed_count, pass_count, prefix_gain_count, full_pair_count),
        "seed_count": seed_count,
        "pass_count": pass_count,
        "checkpoint_exists_count": checkpoint_count,
        "prefix_gain_seed_count": prefix_gain_count,
        "full_pair_generation_seed_count": full_pair_count,
        "both_terms_one_token_seed_count": one_token_both_count,
        "stable_prefix_gain": bool(seed_count) and prefix_gain_count == seed_count,
        "stable_full_pair_generation": bool(seed_count) and full_pair_count == seed_count,
    }


def _clean_seeds(seeds: tuple[int, ...] | list[int]) -> list[int]:
    clean: list[int] = []
    for seed in seeds:
        value = int(seed)
        if value not in clean:
            clean.append(value)
    return clean


def _input_issues(rollup_report: dict[str, Any], seeds: list[int]) -> list[str]:
    issues: list[str] = []
    if not rollup_report:
        issues.append("source diagnostic rollup report is missing or invalid")
    if rollup_report and rollup_report.get("status") != "pass":
        issues.append("source diagnostic rollup report is not pass")
    if as_dict(rollup_report.get("next_experiment_plan")).get("plan_id") != "continuation_span_objective_fixed_loss":
        issues.append("source rollup does not recommend continuation_span_objective_fixed_loss")
    if not seeds:
        issues.append("at least one seed is required")
    return issues


def _stability_decision(seed_count: int, pass_count: int, prefix_gain_count: int, full_pair_count: int) -> str:
    if pass_count != seed_count:
        return "continuation_span_seed_run_failed"
    if seed_count and full_pair_count == seed_count:
        return "continuation_span_full_pair_generation_stable"
    if seed_count and prefix_gain_count == seed_count:
        return "continuation_span_prefix_gain_stable"
    if prefix_gain_count > 0:
        return "continuation_span_prefix_gain_mixed"
    return "continuation_span_no_stable_gain"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_continuation_span_stability"
    decision = str(summary.get("continuation_span_stability_decision") or "")
    if decision == "continuation_span_full_pair_generation_stable":
        return "required_term_pair_continuation_span_full_generation_stable"
    if decision == "continuation_span_prefix_gain_stable":
        return "required_term_pair_continuation_span_prefix_gain_stable"
    if decision == "continuation_span_prefix_gain_mixed":
        return "required_term_pair_continuation_span_prefix_gain_mixed"
    return "required_term_pair_continuation_span_stability_no_gain"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("stable_full_pair_generation"):
        return "tiny_continuation_span_generation_stability_signal"
    if summary.get("stable_prefix_gain"):
        return "tiny_continuation_span_prefix_stability_signal"
    if int(summary.get("prefix_gain_seed_count") or 0) > 0:
        return "tiny_continuation_span_mixed_prefix_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "At least one continuation-span seed run failed."
    if summary.get("stable_full_pair_generation"):
        return "Every seed emitted both required terms in free continuation probes."
    if summary.get("stable_prefix_gain"):
        return "Every seed improved the source prefix-completion minimum for at least one target."
    if int(summary.get("prefix_gain_seed_count") or 0) > 0:
        return "Only part of the seed set reproduced the v510 prefix gain."
    return "The seed set did not reproduce a prefix or generation improvement."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair failed seed runs before changing the objective"
    if summary.get("stable_full_pair_generation"):
        return "add held-out prompts before treating continuation-span training as a stable capability gain"
    if summary.get("stable_prefix_gain"):
        return "add held-out prompt variants to test whether the stable prefix gain generalizes beyond copied scaffolds"
    return "revise the corpus objective before adding more seeds"
