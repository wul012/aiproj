from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc
from minigpt.model_capability_required_term_pair_loss_alias_objective import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_JSON_FILENAME,
    build_model_capability_required_term_pair_loss_alias_objective,
    locate_model_capability_required_term_pair_loss_alias_objective_source,
    read_json_report,
)
from minigpt.report_utils import as_dict, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME = "model_capability_required_term_pair_loss_alias_stability.json"
REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_TEXT_FILENAME = "model_capability_required_term_pair_loss_alias_stability.txt"
REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_alias_stability.md"
REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_HTML_FILENAME = "model_capability_required_term_pair_loss_alias_stability.html"
DEFAULT_LOSS_ALIAS_STABILITY_SEEDS = (514, 515)


def locate_model_capability_required_term_pair_loss_alias_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_JSON_FILENAME
        if source.is_file():
            return source
        return locate_model_capability_required_term_pair_loss_alias_objective_source(path)
    return source


def build_model_capability_required_term_pair_loss_alias_stability(
    heldout_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = DEFAULT_LOSS_ALIAS_STABILITY_SEEDS,
    repeat: int = 220,
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
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    clean_seeds = _clean_seeds(seeds)
    issues = _input_issues(heldout_report, clean_seeds)
    seed_reports: list[dict[str, Any]] = []
    if not issues:
        for index, seed in enumerate(clean_seeds):
            seed_report = build_model_capability_required_term_pair_loss_alias_objective(
                heldout_report,
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
            )
            seed_reports.append(seed_report)
            if seed_reports[index].get("status") != "pass":
                issues.append(f"seed {seed} loss-alias objective did not pass structurally")

    seed_rows = summarize_loss_alias_seed_rows(clean_seeds, seed_reports)
    summary = summarize_loss_alias_stability(seed_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias stability",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_continuation_span_heldout": str(source_path) if source_path else None,
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
            "experiment_boundary": "repeat the v514 loss-alias objective across seeds before promoting recovery as stable",
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


def summarize_loss_alias_seed_rows(seeds: list[int], reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, report in zip(seeds, reports):
        summary = as_dict(report.get("summary"))
        training = as_dict(report.get("training"))
        rows.append(
            {
                "seed": seed,
                "status": report.get("status"),
                "decision": report.get("decision"),
                "loss_alias_decision": summary.get("loss_alias_decision"),
                "checkpoint_exists": summary.get("checkpoint_exists"),
                "generation_hit_case_count": summary.get("generation_hit_case_count"),
                "source_loss_hit": summary.get("source_loss_hit"),
                "heldout_loss_alias_hit_case_count": summary.get("heldout_loss_alias_hit_case_count"),
                "heldout_loss_alias_full_coverage": summary.get("heldout_loss_alias_full_coverage"),
                "training_status": summary.get("training_status"),
                "checkpoint_path": training.get("checkpoint_path"),
                "out_dir": report.get("out_dir"),
            }
        )
    return rows


def summarize_loss_alias_stability(seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seed_count = len(seed_rows)
    pass_count = sum(1 for row in seed_rows if row.get("status") == "pass")
    checkpoint_count = sum(1 for row in seed_rows if row.get("checkpoint_exists"))
    full_coverage_count = sum(1 for row in seed_rows if row.get("heldout_loss_alias_full_coverage"))
    partial_hit_count = sum(1 for row in seed_rows if int(row.get("heldout_loss_alias_hit_case_count") or 0) > 0)
    source_hit_count = sum(1 for row in seed_rows if row.get("source_loss_hit"))
    return {
        "loss_alias_stability_decision": _stability_decision(seed_count, pass_count, full_coverage_count, partial_hit_count),
        "seed_count": seed_count,
        "pass_count": pass_count,
        "checkpoint_seed_count": checkpoint_count,
        "source_loss_hit_seed_count": source_hit_count,
        "heldout_loss_alias_partial_seed_count": partial_hit_count,
        "heldout_loss_alias_full_seed_count": full_coverage_count,
        "stable_loss_alias_full_coverage": seed_count > 0 and full_coverage_count == seed_count,
        "stable_loss_alias_partial_coverage": seed_count > 0 and partial_hit_count == seed_count,
        "all_seed_generation_hit_case_count": sum(int(row.get("generation_hit_case_count") or 0) for row in seed_rows),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _clean_seeds(seeds: tuple[int, ...] | list[int]) -> list[int]:
    clean: list[int] = []
    for seed in seeds:
        value = int(seed)
        if value not in clean:
            clean.append(value)
    return clean


def _input_issues(heldout_report: dict[str, Any], seeds: list[int]) -> list[str]:
    issues: list[str] = []
    if not heldout_report:
        issues.append("source continuation-span heldout report is missing or invalid")
    if heldout_report and heldout_report.get("status") != "pass":
        issues.append("source continuation-span heldout report is not pass")
    if not seeds:
        issues.append("loss-alias stability seed list is empty")
    return issues


def _stability_decision(seed_count: int, pass_count: int, full_coverage_count: int, partial_hit_count: int) -> str:
    if seed_count == 0:
        return "loss_alias_stability_no_seeds"
    if pass_count < seed_count:
        return "loss_alias_stability_structural_failures"
    if full_coverage_count == seed_count:
        return "loss_alias_stable_full_hit"
    if partial_hit_count == seed_count:
        return "loss_alias_stable_partial_hit"
    if full_coverage_count > 0 or partial_hit_count > 0:
        return "loss_alias_seed_dependent_hit"
    return "loss_alias_no_stable_generation_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_stability"
    if summary.get("stable_loss_alias_full_coverage"):
        return "required_term_pair_loss_alias_stable_full_hit"
    if summary.get("stable_loss_alias_partial_coverage"):
        return "required_term_pair_loss_alias_stable_partial_hit"
    if int(summary.get("heldout_loss_alias_full_seed_count") or 0) > 0:
        return "required_term_pair_loss_alias_seed_dependent"
    return "required_term_pair_loss_alias_not_stable"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("stable_loss_alias_full_coverage"):
        return "tiny_loss_alias_seed_stable_full_signal"
    if summary.get("stable_loss_alias_partial_coverage"):
        return "tiny_loss_alias_seed_stable_partial_signal"
    if int(summary.get("heldout_loss_alias_full_seed_count") or 0) > 0:
        return "tiny_loss_alias_seed_dependent_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The loss-alias stability run had structural failures."
    if summary.get("stable_loss_alias_full_coverage"):
        return "Every tested seed recovered all held-out loss alias prompts."
    if summary.get("stable_loss_alias_partial_coverage"):
        return "Every tested seed recovered at least one held-out loss alias prompt."
    if int(summary.get("heldout_loss_alias_full_seed_count") or 0) > 0:
        return "At least one seed recovered the loss aliases, but the signal is seed-dependent."
    return "No tested seed recovered a stable held-out loss alias signal."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair stability inputs or failed seed runs before promoting the loss-alias objective"
    if summary.get("stable_loss_alias_full_coverage"):
        return "recombine fixed and loss alias objectives and check whether both branches survive together"
    if summary.get("stable_loss_alias_partial_coverage"):
        return "inspect missed loss alias rows before adding fixed branch back"
    return "change corpus shape before adding more seeds"
