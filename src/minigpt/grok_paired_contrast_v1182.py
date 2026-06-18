from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_check_common import check_row as _check, collect_failures, resolve_exit_code
from minigpt.report_utils import as_dict, list_of_dicts, locate_upstream_report, number_or_default, number_or_none, read_json_object, utc_now

GROK_PAIRED_CONTRAST_STEM = "grok_paired_contrast_v1182"
PHASE_SOURCE_DEFAULT_NAME = "grok_trajectory_phases_v1181.json"


def locate_phase_report(path: str | Path) -> Path:
    return locate_upstream_report(path, PHASE_SOURCE_DEFAULT_NAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="grokking phase source report")


def build_grok_paired_contrast_report(
    phase_report_or_path: dict[str, Any] | str | Path,
    *,
    source_phase_report: str | Path | None = None,
    min_final_val_gain: float = 0.70,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_path: Path | None = None
    if isinstance(phase_report_or_path, (str, Path)):
        source_path = locate_phase_report(phase_report_or_path)
        phase_report = read_json_report(source_path)
    else:
        phase_report = dict(phase_report_or_path)
        if source_phase_report is not None:
            source_path = locate_phase_report(source_phase_report)

    summary = as_dict(phase_report.get("summary"))
    phase_rows = list_of_dicts(phase_report.get("phase_rows") or phase_report.get("rows"))
    seed_count = int(number_or_default(summary.get("seed_count"), 0, int))
    pair_rows = _pair_rows(phase_rows)
    paired_summary = _paired_summary(pair_rows, seed_count=seed_count)
    checks = _checks(
        phase_report=phase_report,
        summary=summary,
        phase_rows=phase_rows,
        pair_rows=pair_rows,
        paired_summary=paired_summary,
        seed_count=seed_count,
        min_final_val_gain=min_final_val_gain,
    )
    failures = collect_failures(checks)
    ready = not failures

    return {
        "schema_version": 1,
        "title": "MiniGPT grokking paired contrast v1182",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if ready else "fail",
        "decision": "grokking_weight_decay_pair_contrast_consistent" if ready else "repair_grokking_pair_contrast",
        "failed_count": len(failures),
        "issues": failures,
        "summary": {
            "paired_contrast_ready": ready,
            "source_status": phase_report.get("status"),
            "source_decision": phase_report.get("decision"),
            "source_phase_report": str(source_path) if source_path is not None else "",
            "seed_count": seed_count,
            "phase_row_count": len(phase_rows),
            "pair_count": len(pair_rows),
            "matched_memorization_count": paired_summary["matched_memorization_count"],
            "on_delayed_grok_count": paired_summary["on_delayed_grok_count"],
            "off_memorized_censored_count": paired_summary["off_memorized_censored_count"],
            "no_decay_censored_count": paired_summary["no_decay_censored_count"],
            "mean_final_val_gain": paired_summary["mean_final_val_gain"],
            "min_final_val_gain": paired_summary["min_final_val_gain"],
            "mean_steps_saved_by_grok_stop": paired_summary["mean_steps_saved_by_grok_stop"],
            "longest_delay_seed": paired_summary["longest_delay_seed"],
            "largest_final_val_gain_seed": paired_summary["largest_final_val_gain_seed"],
            "required_min_final_val_gain": min_final_val_gain,
            "boundary": "paired_phase_contrast_only_no_training_rerun",
            "next_step": "use_pair_rows_as_the_plainest_weight_decay_counterfactual_for_v1179_grokking",
        },
        "rows": pair_rows,
        "pair_rows": pair_rows,
        "check_rows": checks,
        "recommendations": _recommendations(ready, paired_summary),
        "csv_fieldnames": [
            "seed",
            "pair_status",
            "on_phase",
            "off_phase",
            "on_t_mem",
            "off_t_mem",
            "t_mem_delta",
            "on_t_gen",
            "off_t_gen",
            "on_grok_gap",
            "on_steps_run",
            "off_steps_run",
            "steps_saved_by_grok_stop",
            "on_final_val_acc",
            "off_final_val_acc",
            "final_val_gain",
            "on_low_val_plateau_rate",
            "off_low_val_plateau_rate",
        ],
    }


def write_grok_paired_contrast_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=GROK_PAIRED_CONTRAST_STEM, row_title="Grokking Paired Contrasts")


def _pair_rows(phase_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_seed: dict[int, dict[str, dict[str, Any]]] = {}
    for row in phase_rows:
        seed = int(number_or_default(row.get("seed"), -1, int))
        arm = str(row.get("arm") or "")
        if seed < 0 or arm not in {"weight_decay_on", "weight_decay_off"}:
            continue
        by_seed.setdefault(seed, {})[arm] = row
    rows: list[dict[str, Any]] = []
    for seed in sorted(by_seed):
        pair = by_seed[seed]
        on = pair.get("weight_decay_on")
        off = pair.get("weight_decay_off")
        rows.append(_one_pair_row(seed, on=on, off=off))
    return rows


def _one_pair_row(seed: int, *, on: dict[str, Any] | None, off: dict[str, Any] | None) -> dict[str, Any]:
    on = on or {}
    off = off or {}
    on_t_mem = number_or_none(on.get("t_mem"), int)
    off_t_mem = number_or_none(off.get("t_mem"), int)
    on_t_gen = number_or_none(on.get("t_gen"), int)
    off_t_gen = number_or_none(off.get("t_gen"), int)
    on_steps = number_or_none(on.get("steps_run"), int)
    off_steps = number_or_none(off.get("steps_run"), int)
    on_final = number_or_none(on.get("final_val_acc"))
    off_final = number_or_none(off.get("final_val_acc"))
    final_gain = _diff(on_final, off_final)
    steps_saved = _diff(off_steps, on_steps)
    matched_mem = bool(on.get("memorized")) and bool(off.get("memorized")) and on_t_mem == off_t_mem
    no_decay_censored = bool(off.get("memorized")) and not bool(off.get("grokked")) and off_t_gen is None
    pair_ok = (
        matched_mem
        and str(on.get("phase")) == "delayed_grok"
        and str(off.get("phase")) == "memorized_only_censored"
        and final_gain is not None
        and final_gain > 0.0
        and steps_saved is not None
        and steps_saved > 0.0
    )
    return {
        "seed": seed,
        "pair_status": "weight_decay_counterfactual" if pair_ok else "pair_needs_review",
        "on_phase": on.get("phase"),
        "off_phase": off.get("phase"),
        "on_t_mem": on_t_mem,
        "off_t_mem": off_t_mem,
        "t_mem_delta": _diff(off_t_mem, on_t_mem),
        "on_t_gen": on_t_gen,
        "off_t_gen": off_t_gen,
        "on_grok_gap": number_or_none(on.get("grok_gap"), int),
        "on_steps_run": on_steps,
        "off_steps_run": off_steps,
        "steps_saved_by_grok_stop": steps_saved,
        "on_final_val_acc": on_final,
        "off_final_val_acc": off_final,
        "final_val_gain": final_gain,
        "on_low_val_plateau_rate": number_or_none(on.get("low_val_plateau_rate")),
        "off_low_val_plateau_rate": number_or_none(off.get("low_val_plateau_rate")),
        "matched_memorization": matched_mem,
        "no_decay_censored": no_decay_censored,
    }


def _paired_summary(pair_rows: list[dict[str, Any]], *, seed_count: int) -> dict[str, Any]:
    del seed_count
    gains = [float(row["final_val_gain"]) for row in pair_rows if row.get("final_val_gain") is not None]
    step_savings = [float(row["steps_saved_by_grok_stop"]) for row in pair_rows if row.get("steps_saved_by_grok_stop") is not None]
    delayed = [row for row in pair_rows if row.get("on_phase") == "delayed_grok"]
    return {
        "matched_memorization_count": sum(1 for row in pair_rows if row.get("matched_memorization")),
        "on_delayed_grok_count": len(delayed),
        "off_memorized_censored_count": sum(1 for row in pair_rows if row.get("off_phase") == "memorized_only_censored"),
        "no_decay_censored_count": sum(1 for row in pair_rows if row.get("no_decay_censored")),
        "mean_final_val_gain": _mean(gains),
        "min_final_val_gain": min(gains) if gains else None,
        "mean_steps_saved_by_grok_stop": _mean(step_savings),
        "longest_delay_seed": _seed_with_max(pair_rows, "on_grok_gap"),
        "largest_final_val_gain_seed": _seed_with_max(pair_rows, "final_val_gain"),
    }


def _checks(
    *,
    phase_report: dict[str, Any],
    summary: dict[str, Any],
    phase_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    paired_summary: dict[str, Any],
    seed_count: int,
    min_final_val_gain: float,
) -> list[dict[str, Any]]:
    return [
        _check("source_phase_report_pass", phase_report.get("status") == "pass", "pass", phase_report.get("status"), "upstream phase report must pass before paired contrast is trusted"),
        _check(
            "source_phase_decision_consistent",
            phase_report.get("decision") == "grokking_phase_profile_consistent",
            "grokking_phase_profile_consistent",
            phase_report.get("decision"),
            "v1182 expects the v1181 phase profile contract",
        ),
        _check(
            "phase_rows_present",
            seed_count > 0 and len(phase_rows) == seed_count * 2,
            f"{seed_count * 2} phase rows",
            len(phase_rows),
            "each seed should have one on and one off phase row",
        ),
        _check("seed_pairs_complete", len(pair_rows) == seed_count, seed_count, len(pair_rows), "each seed should collapse into one paired contrast row"),
        _check(
            "matched_memorization_all_pairs",
            paired_summary["matched_memorization_count"] == seed_count,
            seed_count,
            paired_summary["matched_memorization_count"],
            "paired arms should memorize at the same step before comparing generalization",
        ),
        _check(
            "on_delayed_grok_all_pairs",
            paired_summary["on_delayed_grok_count"] == seed_count,
            seed_count,
            paired_summary["on_delayed_grok_count"],
            "weight-decay arm should be delayed_grok for every seed",
        ),
        _check(
            "off_memorized_censored_all_pairs",
            paired_summary["off_memorized_censored_count"] == seed_count and paired_summary["no_decay_censored_count"] == seed_count,
            seed_count,
            {"phase": paired_summary["off_memorized_censored_count"], "censored": paired_summary["no_decay_censored_count"]},
            "no-decay arm should memorize but never reach t_gen inside the budget",
        ),
        _check(
            "final_validation_gain_large",
            (paired_summary["min_final_val_gain"] or 0.0) >= min_final_val_gain,
            f">= {min_final_val_gain}",
            paired_summary["min_final_val_gain"],
            "the paired contrast should show a large validation gain from weight decay",
        ),
        _check(
            "grok_stop_saves_steps",
            bool(pair_rows) and all((row.get("steps_saved_by_grok_stop") or 0.0) > 0.0 for row in pair_rows),
            "off arm runs longer than on arm for every pair",
            sum(1 for row in pair_rows if (row.get("steps_saved_by_grok_stop") or 0.0) > 0.0),
            "with-decay arms stop after confirmed grok while no-decay arms consume the full budget",
        ),
        _check(
            "boundary_present",
            summary.get("boundary") == "curve_phase_compression_only_no_training_rerun",
            "curve_phase_compression_only_no_training_rerun",
            summary.get("boundary"),
            "paired contrast must stay tied to v1181's no-rerun boundary",
        ),
    ]


def _recommendations(ready: bool, paired_summary: dict[str, Any]) -> list[str]:
    if ready:
        return [
            "Use the paired rows as the shortest honest explanation of v1179: the same seed memorizes in both arms, but only the weight-decay arm generalizes.",
            f"Seed {paired_summary.get('largest_final_val_gain_seed')} is the clearest final-accuracy contrast; seed {paired_summary.get('longest_delay_seed')} is the clearest delayed-grokking story.",
        ]
    return [
        "Do not cite weight decay as the paired counterfactual until pair completeness, matched memorization, and final validation gain checks pass.",
        "Inspect any pair_needs_review row first; one broken seed can turn the causal story back into an ordinary correlation.",
    ]


def _diff(left: int | float | None, right: int | float | None) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _seed_with_max(rows: list[dict[str, Any]], field: str) -> int | None:
    candidates = [row for row in rows if row.get(field) is not None]
    if not candidates:
        return None
    return int(max(candidates, key=lambda row: float(row[field]))["seed"])


__all__ = [
    "GROK_PAIRED_CONTRAST_STEM",
    "PHASE_SOURCE_DEFAULT_NAME",
    "build_grok_paired_contrast_report",
    "locate_phase_report",
    "read_json_report",
    "resolve_exit_code",
    "write_grok_paired_contrast_outputs",
]
