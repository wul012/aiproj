from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, locate_upstream_report, number_or_default, read_json_object, utc_now

GROK_EVIDENCE_CHECK_STEM = "grok_evidence_check_v1180"
GROK_SOURCE_DEFAULT_NAME = "grok_v1179.json"


def locate_grok_report(path: str | Path) -> Path:
    return locate_upstream_report(path, GROK_SOURCE_DEFAULT_NAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="grokking source report")


def build_grok_evidence_check(
    grok_report_or_path: dict[str, Any] | str | Path,
    *,
    source_grok_report: str | Path | None = None,
    min_delay_steps: int = 1000,
    max_val_at_mem: float = 0.5,
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
    grouped = _group_rows(rows, wd_on=wd_on, wd_off=wd_off)
    metrics = _metrics(grouped, wd_on=wd_on, wd_off=wd_off)
    checks = _checks(
        grok_report=grok_report,
        summary=summary,
        rows=rows,
        grouped=grouped,
        metrics=metrics,
        seed_count=seed_count,
        wd_on=wd_on,
        wd_off=wd_off,
        min_delay_steps=min_delay_steps,
        max_val_at_mem=max_val_at_mem,
    )
    failures = [check for check in checks if check["status"] != "pass"]
    ready = not failures

    return {
        "schema_version": 1,
        "title": "MiniGPT grokking evidence check v1180",
        "generated_at": generated_at or utc_now(),
        "status": "pass" if ready else "fail",
        "decision": "grokking_evidence_claim_reconstructed" if ready else "repair_grokking_evidence_claim",
        "failed_count": len(failures),
        "issues": failures,
        "summary": {
            "evidence_check_ready": ready,
            "source_status": grok_report.get("status"),
            "source_decision": grok_report.get("decision"),
            "source_verdict": summary.get("verdict"),
            "source_grok_report": str(source_path) if source_path is not None else "",
            "seed_count": seed_count,
            "row_count": len(rows),
            "weight_decay_on": wd_on,
            "weight_decay_off": wd_off,
            "wd_on_mem_count": metrics["wd_on_mem_count"],
            "wd_on_grok_count": metrics["wd_on_grok_count"],
            "wd_off_mem_count": metrics["wd_off_mem_count"],
            "wd_off_grok_count": metrics["wd_off_grok_count"],
            "wd_on_mean_gap": metrics["wd_on_mean_gap"],
            "wd_on_mean_val_at_mem": metrics["wd_on_mean_val_at_mem"],
            "summary_wd_on_grok_rate": summary.get("wd_on_grok_rate"),
            "summary_wd_off_grok_rate": summary.get("wd_off_grok_rate"),
            "min_delay_steps": min_delay_steps,
            "max_val_at_mem": max_val_at_mem,
            "boundary": "artifact_reconstruction_only_no_training_rerun",
            "next_step": "use_v1179_as_positive_training_dynamics_anchor_if_check_passes",
        },
        "rows": checks,
        "check_rows": checks,
        "recommendations": _recommendations(ready, summary),
        "csv_fieldnames": ["id", "status", "expected", "actual", "detail"],
    }


def write_grok_evidence_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=GROK_EVIDENCE_CHECK_STEM, row_title="Grok Evidence Checks")


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _group_rows(rows: list[dict[str, Any]], *, wd_on: float, wd_off: float) -> dict[str, list[dict[str, Any]]]:
    return {
        "wd_on": [row for row in rows if float(number_or_default(row.get("weight_decay"), -1.0)) == wd_on],
        "wd_off": [row for row in rows if float(number_or_default(row.get("weight_decay"), -1.0)) == wd_off],
    }


def _metrics(grouped: dict[str, list[dict[str, Any]]], *, wd_on: float, wd_off: float) -> dict[str, Any]:
    del wd_on, wd_off
    on = grouped["wd_on"]
    off = grouped["wd_off"]
    gaps = [float(row["grok_gap"]) for row in on if row.get("grok_gap") is not None]
    val_at_mem = [float(row["val_at_mem"]) for row in on if row.get("val_at_mem") is not None]
    return {
        "wd_on_mem_count": sum(1 for row in on if bool(row.get("memorized"))),
        "wd_on_grok_count": sum(1 for row in on if bool(row.get("grokked"))),
        "wd_off_mem_count": sum(1 for row in off if bool(row.get("memorized"))),
        "wd_off_grok_count": sum(1 for row in off if bool(row.get("grokked"))),
        "wd_on_mean_gap": _mean(gaps),
        "wd_on_mean_val_at_mem": _mean(val_at_mem),
    }


def _checks(
    *,
    grok_report: dict[str, Any],
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    metrics: dict[str, Any],
    seed_count: int,
    wd_on: float,
    wd_off: float,
    min_delay_steps: int,
    max_val_at_mem: float,
) -> list[dict[str, Any]]:
    del wd_on, wd_off
    return [
        _check("source_status_pass", grok_report.get("status") == "pass", "pass", grok_report.get("status"), "source report must be a valid measurement"),
        _check(
            "source_verdict_wd_driven",
            summary.get("verdict") == "grokking_reproduced_wd_driven",
            "grokking_reproduced_wd_driven",
            summary.get("verdict"),
            "v1179 headline claim is specifically weight-decay-driven grokking",
        ),
        _check(
            "seed_arm_grid_complete",
            seed_count > 0 and len(grouped["wd_on"]) == seed_count and len(grouped["wd_off"]) == seed_count and len(rows) == seed_count * 2,
            f"{seed_count} rows per arm; total {seed_count * 2}",
            {"wd_on": len(grouped["wd_on"]), "wd_off": len(grouped["wd_off"]), "total": len(rows)},
            "each seed must have paired weight_decay on/off rows",
        ),
        _check(
            "wd_on_memorized_all",
            metrics["wd_on_mem_count"] == seed_count,
            seed_count,
            metrics["wd_on_mem_count"],
            "with-decay arm must memorize all seeds before claiming delayed generalization",
        ),
        _check(
            "wd_on_grokked_all",
            metrics["wd_on_grok_count"] == seed_count,
            seed_count,
            metrics["wd_on_grok_count"],
            "with-decay arm must grok all seeds for the v1179 strong positive claim",
        ),
        _check(
            "wd_off_memorized_all",
            metrics["wd_off_mem_count"] == seed_count,
            seed_count,
            metrics["wd_off_mem_count"],
            "no-decay ablation should still memorize, separating optimization from generalization",
        ),
        _check(
            "wd_off_did_not_grok",
            metrics["wd_off_grok_count"] == 0,
            0,
            metrics["wd_off_grok_count"],
            "weight-decay-driven verdict requires the no-decay ablation not to grok within budget",
        ),
        _check(
            "delay_real",
            (metrics["wd_on_mean_gap"] or 0.0) >= min_delay_steps and (metrics["wd_on_mean_val_at_mem"] or 1.0) < max_val_at_mem,
            {"mean_gap_at_least": min_delay_steps, "mean_val_at_mem_below": max_val_at_mem},
            {"mean_gap": metrics["wd_on_mean_gap"], "mean_val_at_mem": metrics["wd_on_mean_val_at_mem"]},
            "validation must remain low at memorization and generalize much later",
        ),
        _check(
            "summary_rates_match_rows",
            _close(summary.get("wd_on_grok_rate"), _rate(metrics["wd_on_grok_count"], seed_count))
            and _close(summary.get("wd_off_grok_rate"), _rate(metrics["wd_off_grok_count"], seed_count)),
            {"wd_on_grok_rate": _rate(metrics["wd_on_grok_count"], seed_count), "wd_off_grok_rate": _rate(metrics["wd_off_grok_count"], seed_count)},
            {"wd_on_grok_rate": summary.get("wd_on_grok_rate"), "wd_off_grok_rate": summary.get("wd_off_grok_rate")},
            "summary grok rates must reconstruct from rows",
        ),
        _check(
            "boundary_present",
            summary.get("boundary") == "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
            "toy_scale_single_task_modular_addition_grokking_not_a_scaling_claim",
            summary.get("boundary"),
            "positive grokking result must keep its toy-scale boundary",
        ),
    ]


def _check(check_id: str, passed: bool, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual, "detail": detail}


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _close(actual: Any, expected: float, *, eps: float = 1e-9) -> bool:
    try:
        return abs(float(actual) - expected) <= eps
    except (TypeError, ValueError):
        return False


def _recommendations(ready: bool, summary: dict[str, Any]) -> list[str]:
    if ready:
        return [
            "The v1179 grokking claim reconstructs from the archived rows: memorization is early, generalization is delayed, and the no-decay ablation stays ungrokked.",
            "Use v1179 as a positive training-dynamics anchor, while keeping the toy-scale modular-addition boundary explicit.",
        ]
    return [
        f"Repair the v1179 evidence before using the grokking claim; current verdict is {summary.get('verdict')}.",
        "Do not cite the grokking result as a positive anchor until every check row passes.",
    ]


__all__ = [
    "GROK_EVIDENCE_CHECK_STEM",
    "GROK_SOURCE_DEFAULT_NAME",
    "build_grok_evidence_check",
    "locate_grok_report",
    "read_json_report",
    "resolve_exit_code",
    "write_grok_evidence_check_outputs",
]
