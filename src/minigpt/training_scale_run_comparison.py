from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.training_scale_run_comparison_artifacts import (
    render_training_scale_run_comparison_html,
    render_training_scale_run_comparison_markdown,
    write_training_scale_run_comparison_csv,
    write_training_scale_run_comparison_html,
    write_training_scale_run_comparison_json,
    write_training_scale_run_comparison_markdown,
    write_training_scale_run_comparison_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    number_or_default,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
    utc_now,
)


GATE_ORDER = {"fail": 0, "warn": 1, "pass": 2}


def load_training_scale_run(path: str | Path) -> dict[str, Any]:
    run_path = _resolve_run_path(Path(path))
    payload = json.loads(run_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale run must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(run_path)
    return payload


def build_training_scale_run_comparison(
    run_paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    title: str = "MiniGPT training scale run comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    if not run_paths:
        raise ValueError("at least one training scale run is required")
    if names is not None and len(names) != len(run_paths):
        raise ValueError("names length must match run_paths length")
    reports = [load_training_scale_run(path) for path in run_paths]
    resolved_names = _resolve_names(reports, names)
    runs = [_run_summary(report, resolved_names[index], index) for index, report in enumerate(reports)]
    baseline_run = _select_baseline(runs, baseline)
    deltas = [_run_delta(row, baseline_run) for row in runs]
    summary = _comparison_summary(runs, baseline_run, deltas)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "run_count": len(runs),
        "baseline": baseline_run,
        "runs": runs,
        "baseline_deltas": deltas,
        "summary": summary,
        "best_by_readiness": _best_by_readiness(runs),
        "recommendations": _recommendations(summary, deltas),
    }


def _resolve_run_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_run.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _resolve_names(reports: list[dict[str, Any]], names: list[str] | None) -> list[str]:
    if names is not None:
        resolved = [str(name).strip() for name in names]
    else:
        resolved = [
            str(report.get("name") or Path(str(report.get("_source_path") or f"run-{index + 1}")).parent.name or f"run-{index + 1}")
            for index, report in enumerate(reports)
        ]
    if any(not name for name in resolved):
        raise ValueError("run names cannot be empty")
    if len(set(resolved)) != len(resolved):
        raise ValueError("run names must be unique")
    return resolved


def _run_summary(report: dict[str, Any], name: str, index: int) -> dict[str, Any]:
    gate = _dict(report.get("gate"))
    plan = _dict(report.get("scale_plan_summary"))
    batch = _dict(report.get("batch_summary"))
    row = {
        "index": index + 1,
        "name": name,
        "source_path": report.get("_source_path"),
        "status": report.get("status"),
        "allowed": bool(report.get("allowed")),
        "execute": bool(report.get("execute")),
        "gate_status": gate.get("overall_status"),
        "gate_profile": report.get("gate_profile") or gate.get("profile"),
        "gate_pass_count": gate.get("pass_count"),
        "gate_warn_count": gate.get("warn_count"),
        "gate_fail_count": gate.get("fail_count"),
        "dataset_name": plan.get("dataset_name"),
        "version_prefix": plan.get("version_prefix"),
        "scale_tier": plan.get("scale_tier"),
        "char_count": plan.get("char_count"),
        "warning_count": plan.get("warning_count"),
        "variant_count": plan.get("variant_count"),
        "baseline": plan.get("baseline"),
        "suite_mode": plan.get("suite_mode") or batch.get("suite_mode"),
        "suite_name": plan.get("suite_name") or batch.get("suite_name"),
        "suite_path": plan.get("suite_path") or batch.get("suite_path"),
        "batch_status": batch.get("status"),
        "comparison_status": batch.get("comparison_status"),
        "batch_comparison_review_action_count": _int(batch.get("comparison_review_action_count")),
        "batch_comparison_blocker_action_count": _int(batch.get("comparison_blocker_action_count")),
        "batch_maturity_review_count": _int(batch.get("maturity_review_count")),
        "batch_maturity_coverage_regression_count": _int(batch.get("maturity_coverage_regression_count")),
        "batch_maturity_ci_regression_count": _int(batch.get("maturity_ci_regression_count")),
        "batch_maturity_review_names": _string_list(batch.get("maturity_review_names")),
        "batch_maturity_coverage_regression_names": _string_list(batch.get("maturity_coverage_regression_names")),
        "batch_maturity_ci_regression_names": _string_list(batch.get("maturity_ci_regression_names")),
        "batch_maturity_ci_regression_reason_counts": _int_mapping(batch.get("maturity_ci_regression_reason_counts")),
        "batch_comparison_blocker_reasons": _string_list(batch.get("comparison_blocker_reasons")),
        "batch_comparison_blocker_portfolios": _string_list(batch.get("comparison_blocker_portfolios")),
        "completed_variant_count": batch.get("completed_variant_count"),
        "blocked_reason": report.get("blocked_reason"),
        "gate_outputs": _dict(report.get("gate_outputs")),
        "batch_outputs": _dict(report.get("batch_outputs")),
    }
    row["readiness_score"] = _readiness_score(row)
    return row


def _readiness_score(row: dict[str, Any]) -> int:
    score = 0
    if row.get("allowed"):
        score += 35
    score += {"pass": 35, "warn": 18, "fail": 0}.get(str(row.get("gate_status")), 0)
    score += {"completed": 25, "planned": 18, "skipped": 0, "failed": -10}.get(str(row.get("batch_status")), 0)
    if row.get("comparison_status") == "written":
        score += 7
    score -= 8 * _int(row.get("batch_comparison_blocker_action_count"))
    if row.get("execute"):
        score += 5
    return max(0, score)


def _select_baseline(runs: list[dict[str, Any]], baseline: str | int | None) -> dict[str, Any]:
    if baseline is None:
        return runs[0]
    if isinstance(baseline, int) or (isinstance(baseline, str) and str(baseline).isdigit()):
        index = int(baseline)
        if index < 0 or index >= len(runs):
            raise ValueError("baseline index out of range")
        return runs[index]
    for run in runs:
        if run.get("name") == baseline:
            return run
    raise ValueError(f"baseline not found: {baseline}")


def _run_delta(run: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    readiness_delta = _int(run.get("readiness_score")) - _int(baseline.get("readiness_score"))
    gate_delta = GATE_ORDER.get(str(run.get("gate_status")), -1) - GATE_ORDER.get(str(baseline.get("gate_status")), -1)
    allowed_delta = int(bool(run.get("allowed"))) - int(bool(baseline.get("allowed")))
    return {
        "name": run.get("name"),
        "baseline_name": baseline.get("name"),
        "is_baseline": run.get("name") == baseline.get("name"),
        "allowed_delta": allowed_delta,
        "readiness_delta": readiness_delta,
        "suite_relation": _suite_relation(run, baseline),
        "gate_relation": _relation(gate_delta),
        "batch_relation": _batch_relation(run, baseline),
        "explanation": _delta_explanation(run, baseline, readiness_delta, gate_delta, allowed_delta),
    }


def _comparison_summary(runs: list[dict[str, Any]], baseline: dict[str, Any], deltas: list[dict[str, Any]]) -> dict[str, Any]:
    suite_paths = sorted({str(row.get("suite_path")) for row in runs if row.get("suite_path")})
    return {
        "baseline_name": baseline.get("name"),
        "baseline_suite_path": baseline.get("suite_path"),
        "run_count": len(runs),
        "allowed_count": sum(1 for row in runs if row.get("allowed")),
        "blocked_count": sum(1 for row in runs if row.get("status") == "blocked" or not row.get("allowed")),
        "batch_started_count": sum(1 for row in runs if row.get("batch_status") not in {None, "skipped"}),
        "batch_skipped_count": sum(1 for row in runs if row.get("batch_status") in {None, "skipped"}),
        "gate_pass_count": sum(1 for row in runs if row.get("gate_status") == "pass"),
        "gate_warn_count": sum(1 for row in runs if row.get("gate_status") == "warn"),
        "gate_fail_count": sum(1 for row in runs if row.get("gate_status") == "fail"),
        "suite_consistency": _suite_consistency(runs, suite_paths),
        "suite_path_count": len(suite_paths),
        "suite_paths": suite_paths,
        "suite_mismatch_count": sum(1 for row in deltas if row.get("suite_relation") == "changed"),
        "batch_comparison_review_action_count": sum(_int(row.get("batch_comparison_review_action_count")) for row in runs),
        "batch_comparison_blocker_action_count": sum(_int(row.get("batch_comparison_blocker_action_count")) for row in runs),
        "batch_maturity_review_count": sum(_int(row.get("batch_maturity_review_count")) for row in runs),
        "batch_maturity_coverage_regression_count": sum(_int(row.get("batch_maturity_coverage_regression_count")) for row in runs),
        "batch_maturity_ci_regression_count": sum(_int(row.get("batch_maturity_ci_regression_count")) for row in runs),
        "batch_maturity_ci_regression_reason_counts": _merge_reason_counts(runs),
        "batch_maturity_coverage_regression_names": sorted(
            {
                name
                for row in runs
                for name in _string_list(row.get("batch_maturity_coverage_regression_names"))
            }
        ),
        "batch_maturity_ci_regression_names": sorted(
            {
                name
                for row in runs
                for name in _string_list(row.get("batch_maturity_ci_regression_names"))
            }
        ),
        "batch_comparison_blocker_reasons": sorted(
            {
                reason
                for row in runs
                for reason in _string_list(row.get("batch_comparison_blocker_reasons"))
            }
        ),
        "readiness_improvement_count": sum(1 for row in deltas if _int(row.get("readiness_delta")) > 0),
        "readiness_regression_count": sum(1 for row in deltas if _int(row.get("readiness_delta")) < 0),
    }


def _best_by_readiness(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        return {}
    return dict(max(runs, key=lambda row: _int(row.get("readiness_score"))))


def _recommendations(summary: dict[str, Any], deltas: list[dict[str, Any]]) -> list[str]:
    recommendations = []
    if _int(summary.get("blocked_count")):
        recommendations.append("Review blocked gated runs before executing larger-corpus batches.")
    if _int(summary.get("gate_fail_count")):
        recommendations.append("Gate failures should be fixed or explicitly justified before using --allow-fail.")
    if _int(summary.get("gate_warn_count")):
        recommendations.append("Gate warnings can support smoke evidence, but should not be treated as model capability proof.")
    if summary.get("suite_consistency") == "mixed":
        recommendations.append("Compared runs use different benchmark suites; treat readiness deltas as governance evidence, not clean model-quality deltas.")
    elif summary.get("suite_consistency") == "missing":
        recommendations.append("Some compared runs do not report a benchmark suite; review their plan summaries before selecting a promoted baseline.")
    if _int(summary.get("batch_started_count")) and not _int(summary.get("blocked_count")):
        recommendations.append("All compared runs reached the batch layer; review batch comparisons before moving to --execute.")
    if _int(summary.get("batch_comparison_blocker_action_count")):
        recommendations.append("Resolve batch comparison blocker actions before promoting any scale run from this comparison.")
    elif _int(summary.get("batch_comparison_review_action_count")):
        recommendations.append("Review batch comparison actions before treating readiness ranking as clean baseline evidence.")
    if _int(summary.get("batch_maturity_ci_regression_count")):
        recommendations.append("Review CI-regressed batch portfolios before treating scale-run readiness as clean automation evidence.")
    if any(_int(row.get("readiness_delta")) < 0 for row in deltas):
        recommendations.append("At least one run regressed against the baseline readiness score.")
    if not recommendations:
        recommendations.append("No blocked or regressed scale runs were found.")
    return recommendations


def _relation(delta: int) -> str:
    if delta > 0:
        return "improved"
    if delta < 0:
        return "regressed"
    return "unchanged"


def _batch_relation(run: dict[str, Any], baseline: dict[str, Any]) -> str:
    if run.get("batch_status") == baseline.get("batch_status"):
        return "unchanged"
    if run.get("batch_status") != "skipped" and baseline.get("batch_status") == "skipped":
        return "improved"
    if run.get("batch_status") == "skipped" and baseline.get("batch_status") != "skipped":
        return "regressed"
    return "changed"


def _suite_relation(run: dict[str, Any], baseline: dict[str, Any]) -> str:
    if run.get("suite_path") == baseline.get("suite_path"):
        return "unchanged"
    if run.get("suite_path") and baseline.get("suite_path"):
        return "changed"
    return "unknown"


def _suite_consistency(runs: list[dict[str, Any]], suite_paths: list[str]) -> str:
    if any(not row.get("suite_path") for row in runs):
        return "missing"
    if len(suite_paths) > 1:
        return "mixed"
    return "consistent"


def _delta_explanation(run: dict[str, Any], baseline: dict[str, Any], readiness_delta: int, gate_delta: int, allowed_delta: int) -> str:
    if run.get("name") == baseline.get("name"):
        return "baseline"
    parts = []
    if readiness_delta:
        parts.append(f"readiness {_signed(readiness_delta)}")
    if gate_delta:
        parts.append(f"gate {_relation(gate_delta)}")
    if allowed_delta:
        parts.append("allowed changed")
    if run.get("batch_status") != baseline.get("batch_status"):
        parts.append(f"batch {baseline.get('batch_status')} -> {run.get('batch_status')}")
    if run.get("suite_path") != baseline.get("suite_path"):
        parts.append(f"suite {baseline.get('suite_path') or 'missing'} -> {run.get('suite_path') or 'missing'}")
    return "; ".join(parts) or "unchanged"


def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _merge_reason_counts(runs: list[dict[str, Any]]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for run in runs:
        for reason, count in _int_mapping(run.get("batch_maturity_ci_regression_reason_counts")).items():
            merged[reason] = merged.get(reason, 0) + count
    return dict(sorted(merged.items()))


def _signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)
