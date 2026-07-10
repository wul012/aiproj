from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.project_audit_artifacts import (
    render_project_audit_html,  # noqa: F401
    render_project_audit_markdown,  # noqa: F401
    write_project_audit_html,  # noqa: F401
    write_project_audit_json,  # noqa: F401
    write_project_audit_markdown,  # noqa: F401
    write_project_audit_outputs,  # noqa: F401
)
from minigpt.project_audit_builder import (
    build_project_audit_checks,
    build_project_audit_recommendations,
    build_project_audit_run_rows,
    summarize_project_audit_checks,
)
from minigpt.project_audit_contexts import (
    build_benchmark_history_context,
    build_ci_workflow_context,
    build_request_history_context,
    build_test_coverage_context,
)
from minigpt.report_utils import utc_now


def build_project_audit(
    registry_path: str | Path,
    *,
    model_card_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    benchmark_history_path: str | Path | None = None,
    ci_workflow_hygiene_path: str | Path | None = None,
    test_coverage_report_path: str | Path | None = None,
    title: str = "MiniGPT project audit",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    model_card_file = _resolve_model_card_path(registry_file, model_card_path)
    request_history_summary_file = _resolve_request_history_summary_path(registry_file, request_history_summary_path)
    benchmark_history_file = _resolve_benchmark_history_path(registry_file, benchmark_history_path)
    ci_workflow_hygiene_file = _resolve_ci_workflow_hygiene_path(registry_file, ci_workflow_hygiene_path)
    test_coverage_report_file = _resolve_test_coverage_report_path(registry_file, test_coverage_report_path)
    model_card = _read_json(model_card_file, warnings, "model card") if model_card_file is not None else None
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
    runs = build_project_audit_run_rows(registry, model_card if isinstance(model_card, dict) else None)
    checks = build_project_audit_checks(
        registry,
        model_card if isinstance(model_card, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        request_history_summary_file,
        benchmark_history if isinstance(benchmark_history, dict) else None,
        benchmark_history_file,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
        ci_workflow_hygiene_file,
        test_coverage_report if isinstance(test_coverage_report, dict) else None,
        test_coverage_report_file,
        runs,
    )
    summary = summarize_project_audit_checks(
        checks,
        registry,
        model_card if isinstance(model_card, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        benchmark_history if isinstance(benchmark_history, dict) else None,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
        test_coverage_report if isinstance(test_coverage_report, dict) else None,
        runs,
    )

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "registry_path": str(registry_file),
        "model_card_path": None if model_card_file is None else str(model_card_file),
        "request_history_summary_path": None if request_history_summary_file is None else str(request_history_summary_file),
        "benchmark_history_path": None if benchmark_history_file is None else str(benchmark_history_file),
        "ci_workflow_hygiene_path": None if ci_workflow_hygiene_file is None else str(ci_workflow_hygiene_file),
        "test_coverage_report_path": None if test_coverage_report_file is None else str(test_coverage_report_file),
        "summary": summary,
        "checks": checks,
        "request_history_context": build_request_history_context(request_history_summary if isinstance(request_history_summary, dict) else None),
        "benchmark_history_context": build_benchmark_history_context(benchmark_history if isinstance(benchmark_history, dict) else None),
        "ci_workflow_context": build_ci_workflow_context(ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None),
        "test_coverage_context": build_test_coverage_context(test_coverage_report if isinstance(test_coverage_report, dict) else None),
        "runs": runs,
        "recommendations": build_project_audit_recommendations(checks, summary),
        "warnings": warnings,
    }


def _resolve_model_card_path(registry_path: Path, model_card_path: str | Path | None) -> Path | None:
    if model_card_path is not None:
        return Path(model_card_path)
    candidates = [
        registry_path.parent / "model_card.json",
        registry_path.parent / "model-card" / "model_card.json",
        registry_path.parent.parent / "model-card" / "model_card.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_request_history_summary_path(registry_path: Path, request_history_summary_path: str | Path | None) -> Path | None:
    if request_history_summary_path is not None:
        return Path(request_history_summary_path)
    candidates = [
        registry_path.parent / "request_history_summary.json",
        registry_path.parent / "request-history-summary" / "request_history_summary.json",
        registry_path.parent.parent / "request-history-summary" / "request_history_summary.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_benchmark_history_path(registry_path: Path, benchmark_history_path: str | Path | None) -> Path | None:
    if benchmark_history_path is not None:
        return Path(benchmark_history_path)
    candidates = [
        registry_path.parent / "benchmark_history.json",
        registry_path.parent / "benchmark-history" / "benchmark_history.json",
        registry_path.parent.parent / "benchmark-history" / "benchmark_history.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_ci_workflow_hygiene_path(registry_path: Path, ci_workflow_hygiene_path: str | Path | None) -> Path | None:
    if ci_workflow_hygiene_path is not None:
        return Path(ci_workflow_hygiene_path)
    candidates = [
        registry_path.parent / "ci_workflow_hygiene.json",
        registry_path.parent / "ci-workflow-hygiene" / "ci_workflow_hygiene.json",
        registry_path.parent.parent / "ci-workflow-hygiene" / "ci_workflow_hygiene.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resolve_test_coverage_report_path(registry_path: Path, test_coverage_report_path: str | Path | None) -> Path | None:
    if test_coverage_report_path is not None:
        return Path(test_coverage_report_path)
    candidates = [
        registry_path.parent / "test_coverage_report.json",
        registry_path.parent / "test-coverage" / "test_coverage_report.json",
        registry_path.parent.parent / "test-coverage" / "test_coverage_report.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"project audit input must be a JSON object: {path}")
    return payload


def _read_json(path: Path, warnings: list[str], label: str) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"{label} not found: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload
