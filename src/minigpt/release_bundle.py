from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.release_bundle_artifacts import (
    render_release_bundle_html,  # noqa: F401
    render_release_bundle_markdown,  # noqa: F401
    write_release_bundle_html,  # noqa: F401
    write_release_bundle_json,  # noqa: F401
    write_release_bundle_markdown,  # noqa: F401
    write_release_bundle_outputs,  # noqa: F401
)
from minigpt.release_bundle_contexts import (
    _audit_checks,
    _benchmark_history_context,
    _ci_workflow_context,
    _recommendations,
    _request_history_context,
    _test_coverage_context,
    _top_runs,
)
from minigpt.release_bundle_support import (
    _build_summary,
    _collect_release_artifacts,
    _default_release_name,
    _read_json,
    _read_required_json,
    _resolve_audit_path,
    _resolve_benchmark_history_path,
    _resolve_ci_workflow_hygiene_path,
    _resolve_model_card_path,
    _resolve_request_history_summary_path,
    _resolve_test_coverage_report_path,
)
from minigpt.report_utils import utc_now


def build_release_bundle(
    registry_path: str | Path,
    *,
    model_card_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    benchmark_history_path: str | Path | None = None,
    ci_workflow_hygiene_path: str | Path | None = None,
    test_coverage_report_path: str | Path | None = None,
    release_name: str | None = None,
    title: str = "MiniGPT release bundle",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    model_file = _resolve_model_card_path(registry_file, model_card_path)
    audit_file = _resolve_audit_path(registry_file, audit_path)
    request_history_summary_file = _resolve_request_history_summary_path(
        registry_file, audit_file, request_history_summary_path
    )
    benchmark_history_file = _resolve_benchmark_history_path(registry_file, audit_file, benchmark_history_path)
    ci_workflow_hygiene_file = _resolve_ci_workflow_hygiene_path(registry_file, audit_file, ci_workflow_hygiene_path)
    test_coverage_report_file = _resolve_test_coverage_report_path(
        registry_file, audit_file, test_coverage_report_path
    )
    model_card = _read_json(model_file, warnings, "model card") if model_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history_summary = (
        _read_json(request_history_summary_file, warnings, "request history summary")
        if request_history_summary_file is not None
        else None
    )
    benchmark_history = (
        _read_json(benchmark_history_file, warnings, "benchmark history")
        if benchmark_history_file is not None
        else None
    )
    ci_workflow_hygiene = (
        _read_json(ci_workflow_hygiene_file, warnings, "CI workflow hygiene")
        if ci_workflow_hygiene_file is not None
        else None
    )
    test_coverage_report = (
        _read_json(test_coverage_report_file, warnings, "test coverage report")
        if test_coverage_report_file is not None
        else None
    )
    artifacts = _collect_release_artifacts(
        registry_file,
        model_file,
        audit_file,
        request_history_summary_file,
        benchmark_history_file,
        ci_workflow_hygiene_file,
        test_coverage_report_file,
    )
    top_runs = _top_runs(registry, model_card if isinstance(model_card, dict) else None)
    summary = _build_summary(
        registry,
        model_card if isinstance(model_card, dict) else None,
        audit if isinstance(audit, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        benchmark_history if isinstance(benchmark_history, dict) else None,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
        test_coverage_report if isinstance(test_coverage_report, dict) else None,
        artifacts,
    )

    return {
        "schema_version": 1,
        "title": title,
        "release_name": release_name or _default_release_name(registry_file),
        "generated_at": generated_at or utc_now(),
        "summary": summary,
        "inputs": {
            "registry_path": str(registry_file),
            "model_card_path": None if model_file is None else str(model_file),
            "project_audit_path": None if audit_file is None else str(audit_file),
            "request_history_summary_path": None
            if request_history_summary_file is None
            else str(request_history_summary_file),
            "benchmark_history_path": None if benchmark_history_file is None else str(benchmark_history_file),
            "ci_workflow_hygiene_path": None
            if ci_workflow_hygiene_file is None
            else str(ci_workflow_hygiene_file),
            "test_coverage_report_path": None
            if test_coverage_report_file is None
            else str(test_coverage_report_file),
        },
        "artifacts": artifacts,
        "top_runs": top_runs,
        "audit_checks": _audit_checks(audit if isinstance(audit, dict) else None),
        "request_history_context": _request_history_context(
            request_history_summary if isinstance(request_history_summary, dict) else None
        ),
        "benchmark_history_context": _benchmark_history_context(
            benchmark_history if isinstance(benchmark_history, dict) else None,
            audit if isinstance(audit, dict) else None,
        ),
        "ci_workflow_context": _ci_workflow_context(
            ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
            audit if isinstance(audit, dict) else None,
        ),
        "test_coverage_context": _test_coverage_context(
            test_coverage_report if isinstance(test_coverage_report, dict) else None,
            audit if isinstance(audit, dict) else None,
        ),
        "recommendations": _recommendations(
            model_card if isinstance(model_card, dict) else None,
            audit if isinstance(audit, dict) else None,
            summary,
        ),
        "warnings": warnings,
    }
