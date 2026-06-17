from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import (
    as_dict,
    list_of_dicts,
    locate_upstream_report,
    number_or_default,
    number_or_none,
    read_json_object,
    utc_now,
)

GROK_TRAJECTORY_PHASE_STEM = "grok_trajectory_phases_v1181"
GROK_SOURCE_DEFAULT_NAME = "grok_v1179.json"


def locate_grok_report(path: str | Path) -> Path:
    return locate_upstream_report(path, GROK_SOURCE_DEFAULT_NAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="grokking source report")


def build_grok_trajectory_phase_report(
    grok_report_or_path: dict[str, Any] | str | Path,
    *,
    source_grok_report: str | Path | None = None,
    min_gap_steps: int = 1000,
    low_val_threshold: float = 0.5,
    min_wd_on_low_plateau_rate: float = 0.70,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_path: Path | None = None
    if isinstance(grok_report_or_path, (str, Path)):
        source_path = locate_grok_report(grok_report_or_path)
        grok_report = read_json_report(source_path)
    else:
        grok_report = dict(grok_report_or_path)
        if source_grok_report is not None:
            source_path = locate_grok_report(source_grok_report)

    summary = as_dict(grok_report.get("summary"))
    rows = list_of_dicts(grok_report.get("rows"))
    seed_count = int(number_or_default(summary.get("seeds"), 0, int))
    wd_on = float(number_or_default(summary.get("weight_decay_on"), 1.0))
    wd_off = float(number_or_default(summary.get("weight_decay_off"), 0.0))
    curves_by_wd = _curves_by_weight_decay(grok_report.get("curves"))
    phase_rows = _phase_rows(
        rows,
        curves_by_wd=curves_by_wd,
        wd_on=wd_on,
        wd_off=wd_off,
        min_gap_steps=min_gap_steps,
        low_val_threshold=low_val_threshold,
    )
    phase_summary = _phase_summary(phase_rows, seed_count=seed_count, wd_on=wd_on, wd_off=wd_off)
    checks = _checks(
        grok_report=grok_report,
        summary=summary,
        rows=rows,
        curves_by_wd=curves_by_wd,
        phase_rows=phase_rows,
        phase_summary=phase_summary,
        seed_count=seed_count,
        wd_on=wd_on,
        wd_off=wd_off,
        min_wd_on_low_plateau_rate=min_wd_on_low_plateau_rate,
    )
    failures = [check for check in checks if check["status"] != "pass"]
    ready = not failures

    return {
        "schema_version": 1,
        "title": "MiniGPT grokking trajectory phases v1181",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if ready else "fail",
        "decision": "grokking_phase_profile_consistent" if ready else "repair_grokking_phase_profile",
        "failed_count": len(failures),
        "issues": failures,
        "summary": {
            "phase_report_ready": ready,
            "source_status": grok_report.get("status"),
            "source_decision": grok_report.get("decision"),
            "source_verdict": summary.get("verdict"),
            "source_grok_report": str(source_path) if source_path is not None else "",
            "seed_count": seed_count,
            "row_count": len(rows),
            "curve_count": sum(len(curves) for curves in curves_by_wd.values()),
            "weight_decay_on": wd_on,
            "weight_decay_off": wd_off,
            "wd_on_delayed_grok_count": phase_summary["wd_on_delayed_grok_count"],
            "wd_off_memorized_censored_count": phase_summary["wd_off_memorized_censored_count"],
            "paired_phase_separation_count": phase_summary["paired_phase_separation_count"],
            "wd_on_low_plateau_rate_mean": phase_summary["wd_on_low_plateau_rate_mean"],
            "wd_on_min_gap": phase_summary["wd_on_min_gap"],
            "wd_on_max_gap": phase_summary["wd_on_max_gap"],
            "longest_delay_seed": phase_summary["longest_delay_seed"],
            "min_gap_steps": min_gap_steps,
            "low_val_threshold": low_val_threshold,
            "min_wd_on_low_plateau_rate": min_wd_on_low_plateau_rate,
            "boundary": "curve_phase_compression_only_no_training_rerun",
            "next_step": "use_phase_rows_to_explain_which_part_of_the_curve_makes_v1179_grokking",
        },
        "rows": phase_rows,
        "phase_rows": phase_rows,
        "check_rows": checks,
        "recommendations": _recommendations(ready, phase_summary),
        "csv_fieldnames": [
            "seed",
            "arm",
            "weight_decay",
            "phase",
            "t_mem",
            "t_gen",
            "grok_gap",
            "plateau_eval_count",
            "low_val_plateau_rate",
            "val_at_mem",
            "final_val_acc",
            "max_val_jump",
            "max_val_jump_step",
            "curve_endpoint_matches_row",
        ],
    }


def write_grok_trajectory_phase_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=GROK_TRAJECTORY_PHASE_STEM, row_title="Grokking Phase Rows")


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _curves_by_weight_decay(value: Any) -> dict[float, list[list[dict[str, float | int]]]]:
    if not isinstance(value, dict):
        return {}
    curves_by_wd: dict[float, list[list[dict[str, float | int]]]] = {}
    for raw_wd, raw_curves in value.items():
        wd = number_or_none(raw_wd)
        if wd is None or not isinstance(raw_curves, list):
            continue
        parsed = [_curve_points(curve) for curve in raw_curves if isinstance(curve, list)]
        curves_by_wd[float(wd)] = parsed
    return curves_by_wd


def _curve_points(curve: list[Any]) -> list[dict[str, float | int]]:
    points: list[dict[str, float | int]] = []
    for raw in curve:
        point = as_dict(raw)
        step = number_or_none(point.get("step"), int)
        train_acc = number_or_none(point.get("train_acc"))
        val_acc = number_or_none(point.get("val_acc"))
        if step is None or train_acc is None or val_acc is None:
            continue
        points.append({"step": int(step), "train_acc": float(train_acc), "val_acc": float(val_acc)})
    return sorted(points, key=lambda item: int(item["step"]))


def _phase_rows(
    rows: list[dict[str, Any]],
    *,
    curves_by_wd: dict[float, list[list[dict[str, float | int]]]],
    wd_on: float,
    wd_off: float,
    min_gap_steps: int,
    low_val_threshold: float,
) -> list[dict[str, Any]]:
    indexes: dict[float, int] = {}
    phase_rows: list[dict[str, Any]] = []
    for row in rows:
        wd = float(number_or_default(row.get("weight_decay"), -1.0))
        index = indexes.get(wd, 0)
        indexes[wd] = index + 1
        curve = curves_by_wd.get(wd, [])
        points = curve[index] if index < len(curve) else []
        phase_rows.append(
            _one_phase_row(
                row,
                points=points,
                arm=_arm_name(wd, wd_on=wd_on, wd_off=wd_off),
                min_gap_steps=min_gap_steps,
                low_val_threshold=low_val_threshold,
            )
        )
    return phase_rows


def _one_phase_row(
    row: dict[str, Any],
    *,
    points: list[dict[str, float | int]],
    arm: str,
    min_gap_steps: int,
    low_val_threshold: float,
) -> dict[str, Any]:
    t_mem = number_or_none(row.get("t_mem"), int)
    t_gen = number_or_none(row.get("t_gen"), int)
    grok_gap = number_or_none(row.get("grok_gap"), int)
    val_at_mem = number_or_none(row.get("val_at_mem"))
    final_val = number_or_none(row.get("final_val_acc"))
    memorized = bool(row.get("memorized"))
    grokked = bool(row.get("grokked"))
    plateau = _plateau_points(points, t_mem=t_mem, t_gen=t_gen, grokked=grokked)
    low_count = sum(1 for point in plateau if float(point["val_acc"]) < low_val_threshold)
    max_jump, max_jump_step = _max_val_jump(points, after_step=t_mem)
    phase = _classify_phase(
        memorized=memorized,
        grokked=grokked,
        t_mem=t_mem,
        t_gen=t_gen,
        grok_gap=grok_gap,
        val_at_mem=val_at_mem,
        min_gap_steps=min_gap_steps,
        low_val_threshold=low_val_threshold,
    )
    return {
        "seed": int(number_or_default(row.get("seed"), -1, int)),
        "arm": arm,
        "weight_decay": float(number_or_default(row.get("weight_decay"), -1.0)),
        "phase": phase,
        "memorized": memorized,
        "grokked": grokked,
        "t_mem": t_mem,
        "t_gen": t_gen,
        "grok_gap": grok_gap,
        "steps_run": number_or_none(row.get("steps_run"), int),
        "curve_points": len(points),
        "curve_first_step": int(points[0]["step"]) if points else None,
        "curve_last_step": int(points[-1]["step"]) if points else None,
        "plateau_eval_count": len(plateau),
        "low_val_plateau_count": low_count,
        "low_val_plateau_rate": _rate(low_count, len(plateau)),
        "val_at_mem": val_at_mem,
        "final_val_acc": final_val,
        "max_val_jump": max_jump,
        "max_val_jump_step": max_jump_step,
        "curve_endpoint_matches_row": _endpoint_matches_row(points, final_val),
        "curve_mempoint_matches_row": _mempoint_matches_row(points, t_mem=t_mem, val_at_mem=val_at_mem),
    }


def _classify_phase(
    *,
    memorized: bool,
    grokked: bool,
    t_mem: int | float | None,
    t_gen: int | float | None,
    grok_gap: int | float | None,
    val_at_mem: int | float | None,
    min_gap_steps: int,
    low_val_threshold: float,
) -> str:
    if not memorized:
        return "not_memorized"
    if grokked and t_mem is not None and t_gen is not None and grok_gap is not None:
        if grok_gap >= min_gap_steps and (val_at_mem is not None and val_at_mem < low_val_threshold):
            return "delayed_grok"
        return "immediate_or_ordinary_learning"
    if memorized and not grokked:
        return "memorized_only_censored"
    return "incomplete_phase"


def _plateau_points(
    points: list[dict[str, float | int]],
    *,
    t_mem: int | float | None,
    t_gen: int | float | None,
    grokked: bool,
) -> list[dict[str, float | int]]:
    if t_mem is None:
        return []
    if grokked and t_gen is not None:
        return [point for point in points if int(point["step"]) >= t_mem and int(point["step"]) < t_gen]
    return [point for point in points if int(point["step"]) >= t_mem]


def _max_val_jump(points: list[dict[str, float | int]], *, after_step: int | float | None) -> tuple[float | None, int | None]:
    jumps: list[tuple[float, int]] = []
    for before, after in zip(points, points[1:]):
        if after_step is not None and int(after["step"]) < after_step:
            continue
        jumps.append((float(after["val_acc"]) - float(before["val_acc"]), int(after["step"])))
    if not jumps:
        return None, None
    jump, step = max(jumps, key=lambda item: item[0])
    return jump, step


def _endpoint_matches_row(points: list[dict[str, float | int]], final_val: int | float | None) -> bool:
    if not points or final_val is None:
        return False
    return _close(points[-1]["val_acc"], final_val, eps=1e-6)


def _mempoint_matches_row(
    points: list[dict[str, float | int]], *, t_mem: int | float | None, val_at_mem: int | float | None
) -> bool:
    if t_mem is None or val_at_mem is None:
        return False
    for point in points:
        if int(point["step"]) == int(t_mem):
            return _close(point["val_acc"], val_at_mem, eps=1e-3)
    return False


def _phase_summary(phase_rows: list[dict[str, Any]], *, seed_count: int, wd_on: float, wd_off: float) -> dict[str, Any]:
    del wd_on, wd_off
    on = [row for row in phase_rows if row["arm"] == "weight_decay_on"]
    off = [row for row in phase_rows if row["arm"] == "weight_decay_off"]
    delayed = [row for row in on if row["phase"] == "delayed_grok"]
    censored = [row for row in off if row["phase"] == "memorized_only_censored"]
    paired = _paired_phase_count(phase_rows)
    gaps = [float(row["grok_gap"]) for row in delayed if row.get("grok_gap") is not None]
    plateau_rates = [float(row["low_val_plateau_rate"]) for row in delayed if row.get("low_val_plateau_rate") is not None]
    longest = max(delayed, key=lambda row: float(row.get("grok_gap") or 0.0), default={})
    return {
        "seed_count": seed_count,
        "wd_on_delayed_grok_count": len(delayed),
        "wd_off_memorized_censored_count": len(censored),
        "paired_phase_separation_count": paired,
        "wd_on_low_plateau_rate_mean": _mean(plateau_rates),
        "wd_on_low_plateau_rate_min": min(plateau_rates) if plateau_rates else None,
        "wd_on_min_gap": min(gaps) if gaps else None,
        "wd_on_max_gap": max(gaps) if gaps else None,
        "longest_delay_seed": longest.get("seed"),
    }


def _paired_phase_count(phase_rows: list[dict[str, Any]]) -> int:
    by_seed: dict[int, dict[str, str]] = {}
    for row in phase_rows:
        seed = int(number_or_default(row.get("seed"), -1, int))
        by_seed.setdefault(seed, {})[str(row.get("arm"))] = str(row.get("phase"))
    return sum(
        1
        for phases in by_seed.values()
        if phases.get("weight_decay_on") == "delayed_grok"
        and phases.get("weight_decay_off") == "memorized_only_censored"
    )


def _checks(
    *,
    grok_report: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    curves_by_wd: dict[float, list[list[dict[str, float | int]]]],
    phase_rows: list[dict[str, Any]],
    phase_summary: dict[str, Any],
    seed_count: int,
    wd_on: float,
    wd_off: float,
    min_wd_on_low_plateau_rate: float,
) -> list[dict[str, Any]]:
    return [
        _check("source_status_pass", grok_report.get("status") == "pass", "pass", grok_report.get("status"), "source report must be a valid measurement"),
        _check(
            "source_verdict_wd_driven",
            summary.get("verdict") == "grokking_reproduced_wd_driven",
            "grokking_reproduced_wd_driven",
            summary.get("verdict"),
            "phase profile is meaningful only for the v1179 positive grokking claim",
        ),
        _check(
            "curve_grid_complete",
            seed_count > 0 and len(curves_by_wd.get(wd_on, [])) == seed_count and len(curves_by_wd.get(wd_off, [])) == seed_count,
            {"wd_on_curves": seed_count, "wd_off_curves": seed_count},
            {"wd_on_curves": len(curves_by_wd.get(wd_on, [])), "wd_off_curves": len(curves_by_wd.get(wd_off, []))},
            "each arm needs one archived curve per seed",
        ),
        _check(
            "rows_have_matching_curves",
            bool(rows) and all(row.get("curve_points", 0) > 0 for row in phase_rows),
            "every row has a curve",
            sum(1 for row in phase_rows if row.get("curve_points", 0) > 0),
            "row-level phase labels must be backed by curve points",
        ),
        _check(
            "curve_endpoints_match_rows",
            bool(phase_rows) and all(row.get("curve_endpoint_matches_row") for row in phase_rows),
            "all endpoints match final_val_acc",
            sum(1 for row in phase_rows if row.get("curve_endpoint_matches_row")),
            "archived curve endpoints must agree with the row summary",
        ),
        _check(
            "curve_mempoints_match_rows",
            bool(phase_rows) and all(row.get("curve_mempoint_matches_row") for row in phase_rows),
            "all t_mem points match val_at_mem",
            sum(1 for row in phase_rows if row.get("curve_mempoint_matches_row")),
            "archived curve memorization points must agree with row val_at_mem",
        ),
        _check(
            "wd_on_delayed_grok_all_seeds",
            phase_summary["wd_on_delayed_grok_count"] == seed_count,
            seed_count,
            phase_summary["wd_on_delayed_grok_count"],
            "with-decay rows must classify as delayed grokking, not immediate learning",
        ),
        _check(
            "wd_on_low_plateau_rate",
            (phase_summary["wd_on_low_plateau_rate_min"] or 0.0) >= min_wd_on_low_plateau_rate,
            f">= {min_wd_on_low_plateau_rate} for every with-decay seed",
            phase_summary["wd_on_low_plateau_rate_min"],
            "validation should stay low across most of the memorized plateau before generalization",
        ),
        _check(
            "wd_off_memorized_censored_all_seeds",
            phase_summary["wd_off_memorized_censored_count"] == seed_count,
            seed_count,
            phase_summary["wd_off_memorized_censored_count"],
            "no-decay rows should memorize but remain censored before generalization",
        ),
        _check(
            "paired_phase_separation",
            phase_summary["paired_phase_separation_count"] == seed_count,
            seed_count,
            phase_summary["paired_phase_separation_count"],
            "each seed should show delayed grokking only in the weight-decay arm",
        ),
        _check(
            "boundary_present",
            summary.get("boundary") == "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
            "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
            summary.get("boundary"),
            "phase profile must keep the toy-scale boundary explicit",
        ),
    ]


def _check(check_id: str, passed: bool, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual, "detail": detail}


def _recommendations(ready: bool, phase_summary: dict[str, Any]) -> list[str]:
    if ready:
        return [
            "The v1179 curves compress into the expected phases: early train memorization, a long low-validation plateau, then late generalization only with weight decay.",
            f"The longest delayed seed is {phase_summary.get('longest_delay_seed')}, useful as the clearest example when explaining grokking to readers.",
        ]
    return [
        "Do not use the v1179 curves as a phase explanation until curve counts, endpoints, and paired phase separation are repaired.",
        "If this fails after a new grokking run, inspect whether the change turned delayed grokking into immediate ordinary learning or no-grok censoring.",
    ]


def _arm_name(wd: float, *, wd_on: float, wd_off: float) -> str:
    if _close(wd, wd_on):
        return "weight_decay_on"
    if _close(wd, wd_off):
        return "weight_decay_off"
    return f"weight_decay_{wd:g}"


def _rate(count: int, total: int) -> float | None:
    if total <= 0:
        return None
    return count / total


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _close(actual: Any, expected: Any, *, eps: float = 1e-9) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= eps
    except (TypeError, ValueError):
        return False


__all__ = [
    "GROK_SOURCE_DEFAULT_NAME",
    "GROK_TRAJECTORY_PHASE_STEM",
    "build_grok_trajectory_phase_report",
    "locate_grok_report",
    "read_json_report",
    "resolve_exit_code",
    "write_grok_trajectory_phase_outputs",
]
