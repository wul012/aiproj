from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_check_common import check_row as _check, collect_failures, resolve_exit_code
from minigpt.report_utils import as_dict, list_of_dicts, locate_upstream_report, number_or_default, read_json_object, utc_now

GROK_WD_LAW_CHECK_STEM = "grok_wd_law_check_v1184"
WD_LAW_SOURCE_DEFAULT_NAME = "grok_wd_law_v1183.json"


def locate_wd_law_report(path: str | Path) -> Path:
    return locate_upstream_report(path, WD_LAW_SOURCE_DEFAULT_NAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="grokking weight-decay law source report")


def build_grok_wd_law_check(
    wd_law_report_or_path: dict[str, Any] | str | Path,
    *,
    source_wd_law_report: str | Path | None = None,
    grok_rate_threshold: float = 0.6,
    min_fastest_gap_steps: int = 1000,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_path: Path | None = None
    if isinstance(wd_law_report_or_path, (str, Path)):
        source_path = locate_wd_law_report(wd_law_report_or_path)
        wd_law_report = read_json_report(source_path)
    else:
        wd_law_report = dict(wd_law_report_or_path)
        if source_wd_law_report is not None:
            source_path = locate_wd_law_report(source_wd_law_report)

    summary = as_dict(wd_law_report.get("summary"))
    rows = sorted(list_of_dicts(wd_law_report.get("rows")), key=lambda row: float(number_or_default(row.get("weight_decay"), -1.0)))
    seed_rows = list_of_dicts(wd_law_report.get("seed_rows"))
    row_metrics = _row_metrics(rows, grok_rate_threshold=grok_rate_threshold)
    seed_metrics = _seed_metrics(seed_rows, summary=summary)
    checks = _checks(
        wd_law_report=wd_law_report,
        summary=summary,
        rows=rows,
        seed_rows=seed_rows,
        row_metrics=row_metrics,
        seed_metrics=seed_metrics,
        grok_rate_threshold=grok_rate_threshold,
        min_fastest_gap_steps=min_fastest_gap_steps,
    )
    failures = collect_failures(checks)
    ready = not failures

    return {
        "schema_version": 1,
        "title": "MiniGPT grokking weight-decay law check v1184",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if ready else "fail",
        "decision": "wd_law_interior_optimum_reconstructed" if ready else "repair_wd_law_interior_optimum_claim",
        "failed_count": len(failures),
        "issues": failures,
        "summary": {
            "wd_law_check_ready": ready,
            "source_status": wd_law_report.get("status"),
            "source_decision": wd_law_report.get("decision"),
            "source_verdict": summary.get("verdict"),
            "source_wd_law_report": str(source_path) if source_path is not None else "",
            "seed_count": int(number_or_default(summary.get("seeds"), 0, int)),
            "wd_count": len(rows),
            "seed_row_count": len(seed_rows),
            "grokking_wds": row_metrics["grokking_wds"],
            "computed_threshold_wd": row_metrics["threshold_wd"],
            "computed_fastest_wd": row_metrics["fastest_wd"],
            "computed_fastest_t_gen": row_metrics["fastest_t_gen"],
            "computed_second_fastest_t_gen": row_metrics["second_fastest_t_gen"],
            "fastest_gap_steps": row_metrics["fastest_gap_steps"],
            "low_end_censored": row_metrics["low_end_censored"],
            "high_end_censored": row_metrics["high_end_censored"],
            "strongest_mem_rate": row_metrics["strongest_mem_rate"],
            "strongest_grok_rate": row_metrics["strongest_grok_rate"],
            "strongest_seed_mem_count": seed_metrics["strongest_seed_mem_count"],
            "strongest_seed_grok_count": seed_metrics["strongest_seed_grok_count"],
            "grok_rate_threshold": grok_rate_threshold,
            "min_fastest_gap_steps": min_fastest_gap_steps,
            "boundary": "artifact_reconstruction_only_no_training_rerun",
            "next_step": "use_v1183_as_weight_decay_dose_response_anchor_if_check_passes",
        },
        "rows": checks,
        "check_rows": checks,
        "recommendations": _recommendations(ready, row_metrics),
        "csv_fieldnames": ["id", "status", "expected", "actual", "detail"],
    }


def write_grok_wd_law_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=GROK_WD_LAW_CHECK_STEM, row_title="Weight-Decay Law Checks")


def _row_metrics(rows: list[dict[str, Any]], *, grok_rate_threshold: float) -> dict[str, Any]:
    if not rows:
        return {
            "wds": [],
            "grokking_wds": [],
            "threshold_wd": None,
            "fastest_wd": None,
            "fastest_t_gen": None,
            "second_fastest_t_gen": None,
            "fastest_gap_steps": None,
            "low_end_censored": False,
            "high_end_censored": False,
            "strongest_mem_rate": None,
            "strongest_grok_rate": None,
        }
    wds = [float(number_or_default(row.get("weight_decay"), -1.0)) for row in rows]
    grok_rows = [
        row for row in rows
        if float(number_or_default(row.get("grok_rate"), 0.0)) >= grok_rate_threshold and row.get("t_gen_mean") is not None
    ]
    grokking_wds = [float(number_or_default(row.get("weight_decay"), -1.0)) for row in grok_rows]
    fastest = min(grok_rows, key=lambda row: float(number_or_default(row.get("t_gen_mean"), float("inf"))), default={})
    ordered_t = sorted(float(number_or_default(row.get("t_gen_mean"), float("inf"))) for row in grok_rows)
    strongest = rows[-1]
    threshold_wd = grokking_wds[0] if grokking_wds else None
    fastest_t = float(number_or_default(fastest.get("t_gen_mean"), 0.0)) if fastest else None
    second_t = ordered_t[1] if len(ordered_t) > 1 else None
    return {
        "wds": wds,
        "grokking_wds": grokking_wds,
        "threshold_wd": threshold_wd,
        "fastest_wd": float(number_or_default(fastest.get("weight_decay"), -1.0)) if fastest else None,
        "fastest_t_gen": fastest_t,
        "second_fastest_t_gen": second_t,
        "fastest_gap_steps": (second_t - fastest_t) if (fastest_t is not None and second_t is not None) else None,
        "low_end_censored": bool(threshold_wd is not None and threshold_wd > wds[0]),
        "high_end_censored": float(number_or_default(strongest.get("grok_rate"), 0.0)) < grok_rate_threshold
        and float(number_or_default(strongest.get("mem_rate"), 0.0)) >= 0.999,
        "strongest_mem_rate": float(number_or_default(strongest.get("mem_rate"), 0.0)),
        "strongest_grok_rate": float(number_or_default(strongest.get("grok_rate"), 0.0)),
    }


def _seed_metrics(seed_rows: list[dict[str, Any]], *, summary: dict[str, Any]) -> dict[str, int]:
    wds = [float(item) for item in summary.get("wds", [])] if isinstance(summary.get("wds"), list) else []
    strongest = max(wds) if wds else None
    strongest_rows = [row for row in seed_rows if strongest is not None and float(number_or_default(row.get("weight_decay"), -1.0)) == strongest]
    return {
        "strongest_seed_mem_count": sum(1 for row in strongest_rows if bool(row.get("memorized"))),
        "strongest_seed_grok_count": sum(1 for row in strongest_rows if bool(row.get("grokked"))),
    }


def _checks(
    *,
    wd_law_report: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
    row_metrics: dict[str, Any],
    seed_metrics: dict[str, int],
    grok_rate_threshold: float,
    min_fastest_gap_steps: int,
) -> list[dict[str, Any]]:
    seed_count = int(number_or_default(summary.get("seeds"), 0, int))
    expected_wds = [float(item) for item in summary.get("wds", [])] if isinstance(summary.get("wds"), list) else []
    return [
        _check("source_status_pass", wd_law_report.get("status") == "pass", "pass", wd_law_report.get("status"), "source report must be a valid measurement"),
        _check(
            "source_verdict_interior_optimum",
            summary.get("verdict") == "wd_dose_response_interior_optimum"
            and wd_law_report.get("decision") == "wd_dose_response_interior_optimum",
            "wd_dose_response_interior_optimum",
            {"decision": wd_law_report.get("decision"), "verdict": summary.get("verdict")},
            "v1183 headline claim is an interior optimum, not a monotone acceleration claim",
        ),
        _check("grid_complete_rows", len(rows) == len(expected_wds) and len(seed_rows) == seed_count * len(expected_wds), {"dose_rows": len(expected_wds), "seed_rows": seed_count * len(expected_wds)}, {"dose_rows": len(rows), "seed_rows": len(seed_rows)}, "dose rows and seed rows must cover every configured weight decay"),
        _check("all_doses_memorize", bool(rows) and all(float(number_or_default(row.get("mem_rate"), 0.0)) >= 0.999 for row in rows), "mem_rate>=0.999 for every dose", [row.get("mem_rate") for row in rows], "dose-response should separate memorization from generalization, not training failure"),
        _check(
            "grok_threshold_matches_summary",
            _close(row_metrics["threshold_wd"], summary.get("grok_threshold_wd")),
            summary.get("grok_threshold_wd"),
            row_metrics["threshold_wd"],
            f"first dose with grok_rate>={grok_rate_threshold} must match the summary threshold",
        ),
        _check(
            "fastest_wd_matches_summary",
            _close(row_metrics["fastest_wd"], summary.get("fastest_grok_wd")),
            summary.get("fastest_grok_wd"),
            row_metrics["fastest_wd"],
            "fastest grokking dose must be re-derived from dose rows",
        ),
        _check(
            "fastest_is_interior",
            row_metrics["fastest_wd"] not in {min(expected_wds, default=None), max(expected_wds, default=None)},
            "fastest wd is not the minimum or maximum dose",
            row_metrics["fastest_wd"],
            "interior optimum requires the fastest dose to be inside the sweep range",
        ),
        _check(
            "fastest_gap_material",
            (row_metrics["fastest_gap_steps"] or 0.0) >= min_fastest_gap_steps,
            f">= {min_fastest_gap_steps}",
            row_metrics["fastest_gap_steps"],
            "fastest dose should be materially faster than the next grokking dose",
        ),
        _check("low_end_censored", row_metrics["low_end_censored"] and bool(summary.get("censored_below_threshold")), True, {"computed": row_metrics["low_end_censored"], "summary": summary.get("censored_below_threshold")}, "too-little weight decay should be censored below the grok threshold"),
        _check(
            "high_end_censored_not_broken",
            row_metrics["high_end_censored"]
            and bool(summary.get("high_end_grok_censored"))
            and not bool(summary.get("too_much_wd_breaks_memorization")),
            {"high_end_censored": True, "too_much_wd_breaks_memorization": False},
            {"computed_high_end_censored": row_metrics["high_end_censored"], "summary_high_end": summary.get("high_end_grok_censored"), "too_much_breaks_mem": summary.get("too_much_wd_breaks_memorization")},
            "strongest dose should memorize but fail to grok, proving the high-end side of the interior optimum",
        ),
        _check(
            "strongest_seed_rows_memorize_not_grok",
            seed_metrics["strongest_seed_mem_count"] == seed_count and seed_metrics["strongest_seed_grok_count"] == 0,
            {"memorized": seed_count, "grokked": 0},
            seed_metrics,
            "every strongest-dose seed should memorize but none should grok",
        ),
        _check(
            "not_monotone_acceleration_claim",
            wd_law_report.get("decision") != "wd_dose_response_monotone_acceleration" and bool(summary.get("interior_optimum")),
            "interior optimum overrides monotone acceleration",
            {"decision": wd_law_report.get("decision"), "interior_optimum": summary.get("interior_optimum"), "monotone_t_gen_decrease": summary.get("monotone_t_gen_decrease")},
            "the check must guard the exact over-claim v1183 fixed",
        ),
        _check(
            "boundary_present",
            summary.get("boundary") == "toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim",
            "toy_scale_single_task_modular_addition_grokking_dose_response_not_a_scaling_claim",
            summary.get("boundary"),
            "positive dose-response result must keep its toy-scale boundary",
        ),
    ]


def _close(actual: Any, expected: Any, *, eps: float = 1e-9) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= eps
    except (TypeError, ValueError):
        return False


def _recommendations(ready: bool, row_metrics: dict[str, Any]) -> list[str]:
    if ready:
        return [
            "The v1183 dose-response claim reconstructs from the dose rows: grokking appears only above a threshold, is fastest at an interior dose, and disappears again at the strongest dose.",
            f"Use weight_decay={row_metrics.get('fastest_wd')} as the fastest toy-scale grokking dose, while keeping the high-end censoring boundary explicit.",
        ]
    return [
        "Do not cite v1183 as an interior-optimum dose-response until every check row passes.",
        "Inspect high_end_censored and fastest_wd first; those two fields protect against the monotone-acceleration over-claim.",
    ]


__all__ = [
    "GROK_WD_LAW_CHECK_STEM",
    "WD_LAW_SOURCE_DEFAULT_NAME",
    "build_grok_wd_law_check",
    "locate_wd_law_report",
    "read_json_report",
    "resolve_exit_code",
    "write_grok_wd_law_check_outputs",
]
