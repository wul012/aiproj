from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import utc_now
from minigpt.maturity_capabilities import (
    CAPABILITY_SPECS,  # noqa: F401
    CapabilitySpec,  # noqa: F401
    capability_rows,
    discover_archive_versions,
    discover_explanation_versions,
    discover_published_versions,
    phase_timeline,
)
from minigpt.maturity_artifacts import (
    render_maturity_summary_html,  # noqa: F401
    render_maturity_summary_markdown,  # noqa: F401
    write_maturity_summary_csv,  # noqa: F401
    write_maturity_summary_html,  # noqa: F401
    write_maturity_summary_json,  # noqa: F401
    write_maturity_summary_markdown,  # noqa: F401
    write_maturity_summary_outputs,  # noqa: F401
)
from minigpt.maturity_release_context import build_release_readiness_context as _release_readiness_context


def build_maturity_summary(
    project_root: str | Path,
    *,
    title: str = "MiniGPT project maturity summary",
    generated_at: str | None = None,
    registry_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    published_versions = discover_published_versions(root)
    archive_versions = discover_archive_versions(root)
    explanation_versions = discover_explanation_versions(root)
    registry = _read_json(Path(registry_path)) if registry_path is not None else _read_json(root / "runs" / "registry" / "registry.json")
    request_history_summary = (
        _read_json(Path(request_history_summary_path))
        if request_history_summary_path is not None
        else _read_json(root / "runs" / "request-history-summary" / "request_history_summary.json")
    )
    capabilities = capability_rows(published_versions)
    registry_context = _registry_context(registry)
    release_readiness_context = _release_readiness_context(registry)
    request_history_context = _request_history_context(request_history_summary)
    summary = _summary(
        published_versions,
        archive_versions,
        explanation_versions,
        capabilities,
        registry,
        request_history_summary,
        release_readiness_context,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "project_root": str(root),
        "summary": summary,
        "capabilities": capabilities,
        "phase_timeline": phase_timeline(published_versions),
        "registry_context": registry_context,
        "release_readiness_context": release_readiness_context,
        "request_history_context": request_history_context,
        "recommendations": _recommendations(capabilities, registry, request_history_summary, release_readiness_context),
    }


def _summary(
    published_versions: list[int],
    archive_versions: list[int],
    explanation_versions: list[int],
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    release_readiness_context: dict[str, Any],
) -> dict[str, Any]:
    average = 0.0
    if capabilities:
        average = round(sum(float(item.get("maturity_level") or 0) for item in capabilities) / len(capabilities), 2)
    statuses = [str(item.get("status")) for item in capabilities]
    overall = "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"
    if overall == "pass" and release_readiness_context.get("trend_status") in {
        "regressed",
        "ci-regressed",
        "coverage-regressed",
        "benchmark-regressed",
    }:
        overall = "warn"
    return {
        "current_version": max(published_versions) if published_versions else None,
        "published_version_count": len(published_versions),
        "archive_version_count": len(archive_versions),
        "explanation_version_count": len(explanation_versions),
        "average_maturity_level": average,
        "overall_status": overall,
        "registry_runs": _pick(registry, "run_count"),
        "release_readiness_trend_status": release_readiness_context.get("trend_status"),
        "release_readiness_delta_count": release_readiness_context.get("delta_count"),
        "release_readiness_regressed_count": release_readiness_context.get("regressed_count"),
        "release_readiness_improved_count": release_readiness_context.get("improved_count"),
        "release_readiness_ci_workflow_regression_count": release_readiness_context.get("ci_workflow_regression_count"),
        "release_readiness_ci_workflow_order_regression_count": release_readiness_context.get("ci_workflow_order_regression_count"),
        "release_readiness_ci_workflow_status_changed_count": release_readiness_context.get("ci_workflow_status_changed_count"),
        "release_readiness_ci_workflow_regression_reasons": release_readiness_context.get("ci_workflow_regression_reasons"),
        "release_readiness_ci_workflow_regression_reason_counts": release_readiness_context.get("ci_workflow_regression_reason_counts"),
        "release_readiness_ci_tiny_plan_digest_gate_ready_regression_count": release_readiness_context.get(
            "ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count"
        ),
        "release_readiness_ci_boundary_gate_check_ready_regression_count": release_readiness_context.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count"
        ),
        "release_readiness_ci_boundary_plan_check_ready_regression_count": release_readiness_context.get(
            "ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count"
        ),
        "release_readiness_ci_archived_path_portability_check_ready_regression_count": release_readiness_context.get(
            "ci_workflow_archived_path_portability_check_ready_regression_count"
        ),
        "release_readiness_ci_drift_smoke_ready_regression_count": release_readiness_context.get(
            "ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count"
        ),
        "release_readiness_max_ci_workflow_failed_check_delta": release_readiness_context.get("max_abs_ci_workflow_failed_check_delta"),
        "release_readiness_max_ci_workflow_order_violation_delta": release_readiness_context.get("max_abs_ci_workflow_order_violation_delta"),
        "release_readiness_test_coverage_regression_count": release_readiness_context.get("test_coverage_regression_count"),
        "release_readiness_test_coverage_status_changed_count": release_readiness_context.get("test_coverage_status_changed_count"),
        "release_readiness_max_test_coverage_percent_delta": release_readiness_context.get("max_abs_test_coverage_percent_delta"),
        "release_readiness_max_test_coverage_gap_delta": release_readiness_context.get("max_abs_test_coverage_gap_delta"),
        "release_readiness_benchmark_history_regression_count": release_readiness_context.get("benchmark_history_regression_count"),
        "release_readiness_benchmark_history_status_changed_count": release_readiness_context.get("benchmark_history_status_changed_count"),
        "release_readiness_benchmark_history_boundary_changed_count": release_readiness_context.get("benchmark_history_boundary_changed_count"),
        "release_readiness_benchmark_suite_design_delta_count": release_readiness_context.get(
            "benchmark_history_suite_design_non_comparison_ready_delta_count"
        ),
        "release_readiness_benchmark_suite_design_regression_count": release_readiness_context.get(
            "benchmark_history_suite_design_non_comparison_ready_regression_count"
        ),
        "release_readiness_benchmark_design_change_delta_count": release_readiness_context.get(
            "benchmark_history_design_comparison_changed_delta_count"
        ),
        "release_readiness_benchmark_requirement_status_changed_count": release_readiness_context.get(
            "benchmark_history_readiness_requirement_status_changed_count"
        ),
        "release_readiness_max_benchmark_requirement_exit_code_delta": release_readiness_context.get(
            "max_abs_benchmark_history_readiness_requirement_exit_code_delta"
        ),
        "release_readiness_benchmark_requirement_failed_reason_added_count": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_added_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_removed_count": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_removed_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_added": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_added"
        ),
        "release_readiness_benchmark_requirement_failed_reason_removed": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_removed"
        ),
        "release_readiness_benchmark_requirement_failed_reason_recovery_delta_count": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_recovery_delta_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_mixed_delta_count": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_mixed_delta_count"
        ),
        "release_readiness_benchmark_requirement_failed_reason_drift_status_counts": release_readiness_context.get(
            "benchmark_history_readiness_requirement_failed_reason_drift_status_counts"
        ),
        "release_readiness_max_benchmark_history_case_regression_delta": release_readiness_context.get(
            "max_abs_benchmark_history_case_regression_delta"
        ),
        "release_readiness_max_benchmark_history_generation_flag_regression_delta": release_readiness_context.get(
            "max_abs_benchmark_history_generation_flag_regression_delta"
        ),
        "release_readiness_max_benchmark_suite_design_delta": release_readiness_context.get(
            "max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta"
        ),
        "release_readiness_max_benchmark_design_change_delta": release_readiness_context.get(
            "max_abs_benchmark_history_design_comparison_changed_entries_delta"
        ),
        "request_history_status": _nested_pick(request_history_summary, "summary", "status"),
        "request_history_records": _nested_pick(request_history_summary, "summary", "total_log_records"),
        "request_history_timeout_rate": _nested_pick(request_history_summary, "summary", "timeout_rate"),
        "request_history_error_rate": _nested_pick(request_history_summary, "summary", "error_rate"),
    }


def _registry_context(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "available": False,
            "run_count": None,
            "pair_delta_cases": None,
            "pair_report_counts": {},
        }
    pair_delta = _dict(registry.get("pair_delta_summary"))
    return {
        "available": True,
        "run_count": registry.get("run_count"),
        "quality_counts": registry.get("quality_counts") if isinstance(registry.get("quality_counts"), dict) else {},
        "generation_quality_counts": registry.get("generation_quality_counts") if isinstance(registry.get("generation_quality_counts"), dict) else {},
        "pair_report_counts": registry.get("pair_report_counts") if isinstance(registry.get("pair_report_counts"), dict) else {},
        "pair_delta_cases": pair_delta.get("case_count"),
        "pair_delta_max_generated": pair_delta.get("max_abs_generated_char_delta"),
    }


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {
            "available": False,
            "status": None,
            "total_log_records": None,
            "timeout_rate": None,
            "bad_request_rate": None,
            "error_rate": None,
        }
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "ok_count": summary.get("ok_count"),
        "timeout_count": summary.get("timeout_count"),
        "bad_request_count": summary.get("bad_request_count"),
        "error_count": summary.get("error_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "stream_request_count": summary.get("stream_request_count"),
        "pair_request_count": summary.get("pair_request_count"),
        "unique_checkpoint_count": summary.get("unique_checkpoint_count"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _recommendations(
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    release_readiness_context: dict[str, Any],
) -> list[str]:
    recs = [
        "Treat v48 as a phase summary: avoid continuing to split links/trends/dashboard unless the change improves evaluation quality.",
        "Next high-value step: consolidate eval suite, generation quality, pair batch, and pair delta leaders into one benchmark scoring suite.",
        "Use the maturity matrix to explain the project as a learning AI engineering artifact, not as a production-grade model service.",
    ]
    weak = [item for item in capabilities if item.get("status") != "pass"]
    if weak:
        recs.append("Revisit weaker areas first: " + ", ".join(str(item.get("title")) for item in weak[:3]) + ".")
    if not isinstance(registry, dict):
        recs.append("Generate a fresh registry before final portfolio review so the maturity summary can include live run counts.")
    if not release_readiness_context.get("available"):
        recs.append("Generate a registry with release readiness comparison outputs so maturity review can include release quality trend context.")
    elif int(release_readiness_context.get("test_coverage_regression_count") or 0) > 0:
        recs.append("Review test coverage regressions before presenting the project as release-stable; maturity status is downgraded to review.")
    elif int(release_readiness_context.get("benchmark_history_readiness_requirement_failed_reason_mixed_delta_count") or 0) > 0:
        recs.append(
            "Review mixed benchmark-history readiness failed-reason drift before presenting the project as release-stable; new reasons can hide behind removals."
        )
    elif int(release_readiness_context.get("benchmark_history_readiness_requirement_status_changed_count") or 0) > 0:
        recs.append(
            "Review benchmark-history readiness requirement changes before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("benchmark_history_readiness_requirement_failed_reason_added_count") or 0) > 0:
        recs.append(
            "Review newly added benchmark-history readiness failed reasons before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("benchmark_history_suite_design_non_comparison_ready_regression_count") or 0) > 0:
        recs.append(
            "Review benchmark-history suite-design readiness regressions before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("benchmark_history_regression_count") or 0) > 0:
        recs.append(
            "Review benchmark-history readiness regressions before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("regressed_count") or 0) > 0:
        recs.append("Review release readiness regressions before presenting the project as release-stable; maturity status is downgraded to review.")
    elif int(release_readiness_context.get("ci_workflow_regression_count") or 0) > 0:
        recs.append(
            "Review CI workflow hygiene regressions"
            + _reason_count_detail(release_readiness_context.get("ci_workflow_regression_reason_counts"))
            + " before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("ci_workflow_order_regression_count") or 0) > 0:
        recs.append(
            "Review CI workflow order regressions"
            + _reason_count_detail(release_readiness_context.get("ci_workflow_regression_reason_counts"))
            + " before presenting the project as release-stable; maturity status is downgraded to review."
        )
    elif int(release_readiness_context.get("improved_count") or 0) > 0:
        recs.append("Keep release readiness comparison evidence in the registry so improvement history remains visible during maturity review.")
    elif int(release_readiness_context.get("benchmark_history_readiness_requirement_failed_reason_recovery_delta_count") or 0) > 0:
        recs.append("Keep benchmark readiness failed-reason recovery evidence visible; it is a stability signal, not a model-quality proof.")
    if not isinstance(request_history_summary, dict):
        recs.append("Generate request_history_summary.json before local serving review so maturity context includes recent inference stability.")
    else:
        request_summary = _dict(request_history_summary.get("summary"))
        if request_summary.get("status") not in {"pass", "empty"}:
            recs.append("Review request history summary warnings before using the playground session as stable local inference evidence.")
    return recs


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _reason_count_detail(value: Any) -> str:
    counts = _dict(value)
    if not counts:
        return ""
    return " (" + ", ".join(f"{key}:{counts[key]}" for key in sorted(counts)) + ")"


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _nested_pick(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
