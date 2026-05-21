from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.release_bundle_artifacts import (
    render_release_bundle_html,
    render_release_bundle_markdown,
    write_release_bundle_html,
    write_release_bundle_json,
    write_release_bundle_markdown,
    write_release_bundle_outputs,
)


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
    request_history_summary_file = _resolve_request_history_summary_path(registry_file, audit_file, request_history_summary_path)
    benchmark_history_file = _resolve_benchmark_history_path(registry_file, audit_file, benchmark_history_path)
    ci_workflow_hygiene_file = _resolve_ci_workflow_hygiene_path(registry_file, audit_file, ci_workflow_hygiene_path)
    test_coverage_report_file = _resolve_test_coverage_report_path(registry_file, audit_file, test_coverage_report_path)
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
            "request_history_summary_path": None if request_history_summary_file is None else str(request_history_summary_file),
            "benchmark_history_path": None if benchmark_history_file is None else str(benchmark_history_file),
            "ci_workflow_hygiene_path": None if ci_workflow_hygiene_file is None else str(ci_workflow_hygiene_file),
            "test_coverage_report_path": None if test_coverage_report_file is None else str(test_coverage_report_file),
        },
        "artifacts": artifacts,
        "top_runs": top_runs,
        "audit_checks": _audit_checks(audit if isinstance(audit, dict) else None),
        "request_history_context": _request_history_context(request_history_summary if isinstance(request_history_summary, dict) else None),
        "benchmark_history_context": _benchmark_history_context(benchmark_history if isinstance(benchmark_history, dict) else None, audit if isinstance(audit, dict) else None),
        "ci_workflow_context": _ci_workflow_context(ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None, audit if isinstance(audit, dict) else None),
        "test_coverage_context": _test_coverage_context(test_coverage_report if isinstance(test_coverage_report, dict) else None, audit if isinstance(audit, dict) else None),
        "recommendations": _recommendations(model_card if isinstance(model_card, dict) else None, audit if isinstance(audit, dict) else None, summary),
        "warnings": warnings,
    }


def _read_required_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"release bundle input must be a JSON object: {path}")
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


def _resolve_model_card_path(registry_path: Path, model_card_path: str | Path | None) -> Path | None:
    if model_card_path is not None:
        return Path(model_card_path)
    candidates = [
        registry_path.parent / "model_card.json",
        registry_path.parent / "model-card" / "model_card.json",
        registry_path.parent.parent / "model-card" / "model_card.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _resolve_audit_path(registry_path: Path, audit_path: str | Path | None) -> Path | None:
    if audit_path is not None:
        return Path(audit_path)
    candidates = [
        registry_path.parent / "project_audit.json",
        registry_path.parent / "audit" / "project_audit.json",
        registry_path.parent.parent / "audit" / "project_audit.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _resolve_request_history_summary_path(
    registry_path: Path,
    audit_path: Path | None,
    request_history_summary_path: str | Path | None,
) -> Path | None:
    if request_history_summary_path is not None:
        return Path(request_history_summary_path)
    candidates: list[Path] = []
    if audit_path is not None:
        try:
            audit = _read_required_json(audit_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            audit = {}
        path = audit.get("request_history_summary_path") if isinstance(audit, dict) else None
        if path:
            candidates.append(Path(str(path)))
    candidates.extend(
        [
            registry_path.parent / "request_history_summary.json",
            registry_path.parent / "request-history-summary" / "request_history_summary.json",
            registry_path.parent.parent / "request-history-summary" / "request_history_summary.json",
        ]
    )
    return next((path for path in candidates if path.exists()), None)


def _resolve_benchmark_history_path(
    registry_path: Path,
    audit_path: Path | None,
    benchmark_history_path: str | Path | None,
) -> Path | None:
    if benchmark_history_path is not None:
        return Path(benchmark_history_path)
    candidates: list[Path] = []
    if audit_path is not None:
        try:
            audit = _read_required_json(audit_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            audit = {}
        path = audit.get("benchmark_history_path") if isinstance(audit, dict) else None
        if path:
            candidates.append(Path(str(path)))
    candidates.extend(
        [
            registry_path.parent / "benchmark_history.json",
            registry_path.parent / "benchmark-history" / "benchmark_history.json",
            registry_path.parent.parent / "benchmark-history" / "benchmark_history.json",
        ]
    )
    return next((path for path in candidates if path.exists()), None)


def _resolve_ci_workflow_hygiene_path(
    registry_path: Path,
    audit_path: Path | None,
    ci_workflow_hygiene_path: str | Path | None,
) -> Path | None:
    if ci_workflow_hygiene_path is not None:
        return Path(ci_workflow_hygiene_path)
    candidates: list[Path] = []
    if audit_path is not None:
        try:
            audit = _read_required_json(audit_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            audit = {}
        path = audit.get("ci_workflow_hygiene_path") if isinstance(audit, dict) else None
        if path:
            candidates.append(Path(str(path)))
    candidates.extend(
        [
            registry_path.parent / "ci_workflow_hygiene.json",
            registry_path.parent / "ci-workflow-hygiene" / "ci_workflow_hygiene.json",
            registry_path.parent.parent / "ci-workflow-hygiene" / "ci_workflow_hygiene.json",
        ]
    )
    return next((path for path in candidates if path.exists()), None)


def _resolve_test_coverage_report_path(
    registry_path: Path,
    audit_path: Path | None,
    test_coverage_report_path: str | Path | None,
) -> Path | None:
    if test_coverage_report_path is not None:
        return Path(test_coverage_report_path)
    candidates: list[Path] = []
    if audit_path is not None:
        try:
            audit = _read_required_json(audit_path)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            audit = {}
        path = audit.get("test_coverage_report_path") if isinstance(audit, dict) else None
        if path:
            candidates.append(Path(str(path)))
    candidates.extend(
        [
            registry_path.parent / "test_coverage_report.json",
            registry_path.parent / "test-coverage" / "test_coverage_report.json",
            registry_path.parent.parent / "test-coverage" / "test_coverage_report.json",
        ]
    )
    return next((path for path in candidates if path.exists()), None)


def _default_release_name(registry_path: Path) -> str:
    return f"{registry_path.parent.name or 'registry'} release"


def _build_summary(
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    benchmark_history: dict[str, Any] | None,
    ci_workflow_hygiene: dict[str, Any] | None,
    test_coverage_report: dict[str, Any] | None,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    best = _dict(registry.get("best_by_best_val_loss"))
    audit_summary = _dict(audit.get("summary")) if audit else {}
    model_summary = _dict(model_card.get("summary")) if model_card else {}
    request_summary = _dict(request_history_summary.get("summary")) if isinstance(request_history_summary, dict) else {}
    benchmark_context = _benchmark_history_context(benchmark_history, audit if isinstance(audit, dict) else None)
    ci_summary = _dict(ci_workflow_hygiene.get("summary")) if isinstance(ci_workflow_hygiene, dict) else {}
    audit_ci_context = _dict(audit.get("ci_workflow_context")) if isinstance(audit, dict) else {}
    coverage_summary = _dict(test_coverage_report.get("summary")) if isinstance(test_coverage_report, dict) else {}
    audit_status = audit_summary.get("overall_status")
    benchmark_history_status = _benchmark_history_summary_status(audit_summary.get("benchmark_history_status"), benchmark_context)
    release_status = _release_status(
        audit_status,
        audit_summary.get("fail_count"),
        audit_summary.get("warn_count"),
        benchmark_history_status,
    )
    return {
        "release_status": release_status,
        "audit_status": audit_status or "missing",
        "audit_score_percent": audit_summary.get("score_percent"),
        "run_count": registry.get("run_count") or model_summary.get("run_count"),
        "best_run_name": best.get("name") or model_summary.get("best_run_name"),
        "best_val_loss": best.get("best_val_loss") or model_summary.get("best_val_loss"),
        "ready_runs": audit_summary.get("ready_runs") or model_summary.get("ready_runs"),
        "request_history_status": audit_summary.get("request_history_status") or request_summary.get("status"),
        "request_history_records": audit_summary.get("request_history_records") or request_summary.get("total_log_records"),
        "benchmark_history_status": benchmark_history_status,
        "benchmark_history_entries": first_present(audit_summary.get("benchmark_history_entries"), benchmark_context.get("entry_count")),
        "benchmark_history_ready": first_present(audit_summary.get("benchmark_history_ready"), benchmark_context.get("ready_count")),
        "benchmark_history_review": first_present(audit_summary.get("benchmark_history_review"), benchmark_context.get("review_count")),
        "benchmark_history_blocked": first_present(audit_summary.get("benchmark_history_blocked"), benchmark_context.get("blocked_count")),
        "benchmark_history_case_regressions": first_present(
            audit_summary.get("benchmark_history_case_regressions"),
            benchmark_context.get("case_regression_entry_count"),
        ),
        "benchmark_history_generation_flag_regressions": first_present(
            audit_summary.get("benchmark_history_generation_flag_regressions"),
            benchmark_context.get("generation_quality_flag_regression_entry_count"),
        ),
        "benchmark_history_readiness_requirement_status": first_present(
            benchmark_context.get("readiness_requirement_status"),
            audit_summary.get("benchmark_history_readiness_requirement_status"),
        ),
        "benchmark_history_readiness_requirement_exit_code": first_present(
            benchmark_context.get("readiness_requirement_exit_code"),
            audit_summary.get("benchmark_history_readiness_requirement_exit_code"),
        ),
        "benchmark_history_readiness_requirement_failed_reasons": first_present(
            benchmark_context.get("readiness_requirement_failed_reasons"),
            audit_summary.get("benchmark_history_readiness_requirement_failed_reasons"),
        ),
        "benchmark_history_model_quality_claim": first_present(
            audit_summary.get("benchmark_history_model_quality_claim"),
            benchmark_context.get("model_quality_claim"),
        ),
        "benchmark_history_latest_boundary": first_present(
            audit_summary.get("benchmark_history_latest_boundary"),
            benchmark_context.get("latest_boundary"),
        ),
        "ci_workflow_status": audit_summary.get("ci_workflow_status") or ci_summary.get("status"),
        "ci_workflow_failed_checks": audit_summary.get("ci_workflow_failed_checks") if audit_summary.get("ci_workflow_failed_checks") is not None else ci_summary.get("failed_check_count"),
        "ci_workflow_node24_actions": audit_summary.get("ci_workflow_node24_actions") if audit_summary.get("ci_workflow_node24_actions") is not None else ci_summary.get("node24_native_action_count"),
        "ci_workflow_required_order_count": first_present(ci_summary.get("required_order_count"), audit_ci_context.get("required_order_count")),
        "ci_workflow_order_violation_count": first_present(ci_summary.get("order_violation_count"), audit_ci_context.get("order_violation_count")),
        "test_coverage_status": audit_summary.get("test_coverage_status") or coverage_summary.get("status"),
        "test_coverage_decision": audit_summary.get("test_coverage_decision") or coverage_summary.get("decision"),
        "test_coverage_percent": audit_summary.get("test_coverage_percent") if audit_summary.get("test_coverage_percent") is not None else coverage_summary.get("line_coverage_percent"),
        "test_coverage_fail_under": audit_summary.get("test_coverage_fail_under") if audit_summary.get("test_coverage_fail_under") is not None else coverage_summary.get("fail_under"),
        "test_coverage_gap": audit_summary.get("test_coverage_gap") if audit_summary.get("test_coverage_gap") is not None else coverage_summary.get("coverage_gap"),
        "available_artifacts": sum(1 for artifact in artifacts if artifact.get("exists")),
        "missing_artifacts": sum(1 for artifact in artifacts if not artifact.get("exists")),
    }


def _release_status(audit_status: Any, fail_count: Any, warn_count: Any, benchmark_history_status: Any = None) -> str:
    if audit_status == "pass":
        if benchmark_history_status == "warn":
            return "review-needed"
        return "release-ready"
    if audit_status == "warn":
        return "review-needed"
    if audit_status == "fail" or fail_count:
        return "blocked"
    if warn_count:
        return "review-needed"
    if benchmark_history_status == "warn":
        return "review-needed"
    return "needs-audit"


def _collect_release_artifacts(
    registry_path: Path,
    model_card_path: Path | None,
    audit_path: Path | None,
    request_history_summary_path: Path | None,
    benchmark_history_path: Path | None,
    ci_workflow_hygiene_path: Path | None,
    test_coverage_report_path: Path | None,
) -> list[dict[str, Any]]:
    registry_dir = registry_path.parent
    specs = [
        ("registry_json", "Registry JSON", registry_path, "JSON", "machine-readable run registry"),
        ("registry_csv", "Registry CSV", registry_dir / "registry.csv", "CSV", "tabular run registry"),
        ("registry_svg", "Registry SVG", registry_dir / "registry.svg", "SVG", "static run registry chart"),
        ("registry_html", "Registry HTML", registry_dir / "registry.html", "HTML", "interactive run registry"),
    ]
    if model_card_path is not None:
        model_dir = model_card_path.parent
        specs.extend(
            [
                ("model_card_json", "Model card JSON", model_card_path, "JSON", "project model card"),
                ("model_card_md", "Model card Markdown", model_dir / "model_card.md", "MD", "markdown model card"),
                ("model_card_html", "Model card HTML", model_dir / "model_card.html", "HTML", "browser model card"),
            ]
        )
    if audit_path is not None:
        audit_dir = audit_path.parent
        specs.extend(
            [
                ("project_audit_json", "Project audit JSON", audit_path, "JSON", "machine-readable project audit"),
                ("project_audit_md", "Project audit Markdown", audit_dir / "project_audit.md", "MD", "markdown project audit"),
                ("project_audit_html", "Project audit HTML", audit_dir / "project_audit.html", "HTML", "browser project audit"),
            ]
        )
    if request_history_summary_path is not None:
        request_dir = request_history_summary_path.parent
        specs.extend(
            [
                (
                    "request_history_summary_json",
                    "Request history summary JSON",
                    request_history_summary_path,
                    "JSON",
                    "machine-readable local inference request stability summary",
                ),
                (
                    "request_history_summary_md",
                    "Request history summary Markdown",
                    request_dir / "request_history_summary.md",
                    "MD",
                    "markdown local inference request stability summary",
                ),
                (
                    "request_history_summary_html",
                    "Request history summary HTML",
                    request_dir / "request_history_summary.html",
                    "HTML",
                    "browser local inference request stability summary",
                ),
            ]
        )
    if benchmark_history_path is not None:
        history_dir = benchmark_history_path.parent
        specs.extend(
            [
                (
                    "benchmark_history_json",
                    "Benchmark history JSON",
                    benchmark_history_path,
                    "JSON",
                    "machine-readable repeated benchmark comparison and decision history",
                ),
                (
                    "benchmark_history_md",
                    "Benchmark history Markdown",
                    history_dir / "benchmark_history.md",
                    "MD",
                    "markdown repeated benchmark comparison and decision history",
                ),
                (
                    "benchmark_history_html",
                    "Benchmark history HTML",
                    history_dir / "benchmark_history.html",
                    "HTML",
                    "browser repeated benchmark comparison and decision history",
                ),
            ]
        )
    if ci_workflow_hygiene_path is not None:
        ci_dir = ci_workflow_hygiene_path.parent
        specs.extend(
            [
                (
                    "ci_workflow_hygiene_json",
                    "CI workflow hygiene JSON",
                    ci_workflow_hygiene_path,
                    "JSON",
                    "machine-readable CI workflow action/runtime policy hygiene report",
                ),
                (
                    "ci_workflow_hygiene_md",
                    "CI workflow hygiene Markdown",
                    ci_dir / "ci_workflow_hygiene.md",
                    "MD",
                    "markdown CI workflow action/runtime policy hygiene report",
                ),
                (
                    "ci_workflow_hygiene_html",
                    "CI workflow hygiene HTML",
                    ci_dir / "ci_workflow_hygiene.html",
                    "HTML",
                    "browser CI workflow action/runtime policy hygiene report",
                ),
            ]
        )
    if test_coverage_report_path is not None:
        coverage_dir = test_coverage_report_path.parent
        specs.extend(
            [
                (
                    "test_coverage_report_json",
                    "Test coverage report JSON",
                    test_coverage_report_path,
                    "JSON",
                    "machine-readable coverage gate report",
                ),
                (
                    "test_coverage_report_md",
                    "Test coverage report Markdown",
                    coverage_dir / "test_coverage_report.md",
                    "MD",
                    "markdown coverage gate report",
                ),
                (
                    "test_coverage_report_html",
                    "Test coverage report HTML",
                    coverage_dir / "test_coverage_report.html",
                    "HTML",
                    "browser coverage gate report",
                ),
            ]
        )
    return [_artifact(key, title, path, kind, description) for key, title, path, kind, description in specs]


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {"available": False, "status": None, "total_log_records": None}
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _benchmark_history_context(benchmark_history: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("benchmark_history_context")) if isinstance(audit, dict) else {}
    if isinstance(benchmark_history, dict):
        summary = _dict(benchmark_history.get("summary"))
        readiness = _dict(benchmark_history.get("readiness_requirement"))
        entries = _list_of_dicts(benchmark_history.get("entries"))
        latest = entries[-1] if entries else {}
        return {
            "available": True,
            "evidence_kind": benchmark_history.get("evidence_kind") or audit_context.get("evidence_kind"),
            "entry_count": summary.get("entry_count") if summary else len(entries),
            "promote_count": summary.get("promote_count"),
            "ready_count": summary.get("ready_count"),
            "review_count": summary.get("review_count"),
            "blocked_count": summary.get("blocked_count"),
            "case_regression_entry_count": summary.get("case_regression_entry_count"),
            "generation_quality_flag_regression_entry_count": summary.get("generation_quality_flag_regression_entry_count"),
            "best_candidate_name": summary.get("best_candidate_name"),
            "best_entry_name": summary.get("best_entry_name"),
            "model_quality_claim": summary.get("model_quality_claim"),
            "readiness_requirement_status": first_present(readiness.get("status"), audit_context.get("readiness_requirement_status")),
            "readiness_requirement_decision": first_present(readiness.get("decision"), audit_context.get("readiness_requirement_decision")),
            "readiness_requirement_exit_code": first_present(readiness.get("exit_code"), audit_context.get("readiness_requirement_exit_code")),
            "readiness_requirement_failed_reasons": _string_list(readiness.get("failed_reasons"))
            or _string_list(audit_context.get("readiness_requirement_failed_reasons")),
            "latest_boundary": latest.get("boundary") or audit_context.get("latest_boundary"),
            "latest_decision_status": latest.get("decision_status") or audit_context.get("latest_decision_status"),
            "latest_promotion_readiness": latest.get("promotion_readiness") or audit_context.get("latest_promotion_readiness"),
        }
    if audit_context:
        return dict(audit_context)
    return {
        "available": False,
        "entry_count": None,
        "ready_count": None,
        "readiness_requirement_status": None,
        "readiness_requirement_exit_code": None,
        "readiness_requirement_failed_reasons": [],
        "model_quality_claim": None,
        "latest_boundary": None,
    }


def _status_from_benchmark_context(context: dict[str, Any]) -> str | None:
    if not context.get("available"):
        return None
    regression_keys = (
        "review_count",
        "blocked_count",
        "case_regression_entry_count",
        "generation_quality_flag_regression_entry_count",
    )
    if any(_int(context.get(key)) > 0 for key in regression_keys):
        return "warn"
    if context.get("readiness_requirement_status") == "fail" or _int(context.get("readiness_requirement_exit_code")) > 0:
        return "warn"
    if _int(context.get("entry_count")) == 0 or _int(context.get("ready_count")) == 0:
        return "warn"
    if context.get("model_quality_claim") == "not_claimed":
        return "warn"
    return "pass"


def _benchmark_history_summary_status(audit_status: Any, context: dict[str, Any]) -> str | None:
    context_status = _status_from_benchmark_context(context)
    if audit_status == "warn" or context_status == "warn":
        return "warn"
    return audit_status or context_status


def _ci_workflow_context(ci_workflow_hygiene: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("ci_workflow_context")) if isinstance(audit, dict) else {}
    if isinstance(ci_workflow_hygiene, dict):
        summary = _dict(ci_workflow_hygiene.get("summary"))
        return {
            "available": True,
            "workflow_path": ci_workflow_hygiene.get("workflow_path") or audit_context.get("workflow_path"),
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "check_count": summary.get("check_count"),
            "failed_check_count": summary.get("failed_check_count"),
            "action_count": summary.get("action_count"),
            "node24_native_action_count": summary.get("node24_native_action_count"),
            "forbidden_env_count": summary.get("forbidden_env_count"),
            "missing_step_count": summary.get("missing_step_count"),
            "required_order_count": summary.get("required_order_count"),
            "order_violation_count": summary.get("order_violation_count"),
            "python_version": summary.get("python_version"),
        }
    if audit_context:
        return dict(audit_context)
    return {"available": False, "status": None, "failed_check_count": None, "required_order_count": None, "order_violation_count": None}


def _test_coverage_context(test_coverage_report: dict[str, Any] | None, audit: dict[str, Any] | None) -> dict[str, Any]:
    audit_context = _dict(audit.get("test_coverage_context")) if isinstance(audit, dict) else {}
    if isinstance(test_coverage_report, dict):
        summary = _dict(test_coverage_report.get("summary"))
        return {
            "available": True,
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "line_coverage_percent": summary.get("line_coverage_percent"),
            "covered_lines": summary.get("covered_lines"),
            "num_statements": summary.get("num_statements"),
            "missing_lines": summary.get("missing_lines"),
            "file_count": summary.get("file_count"),
            "threshold_enabled": summary.get("threshold_enabled"),
            "fail_under": summary.get("fail_under"),
            "coverage_gap": summary.get("coverage_gap"),
        }
    if audit_context:
        return dict(audit_context)
    return {"available": False, "status": None, "line_coverage_percent": None, "coverage_gap": None}


def _artifact(key: str, title: str, path: Path, kind: str, description: str) -> dict[str, Any]:
    exists = path.exists()
    return {
        "key": key,
        "title": title,
        "path": str(path),
        "kind": kind,
        "description": description,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
    }


def _top_runs(registry: dict[str, Any], model_card: dict[str, Any] | None) -> list[dict[str, Any]]:
    if model_card and isinstance(model_card.get("top_runs"), list):
        return _list_of_dicts(model_card.get("top_runs"))[:5]
    by_name = {str(run.get("name")): run for run in _list_of_dicts(registry.get("runs"))}
    rows = []
    for item in _list_of_dicts(registry.get("loss_leaderboard")):
        run = by_name.get(str(item.get("name")), item)
        rows.append(run)
    return rows[:5] or _list_of_dicts(registry.get("runs"))[:5]


def _audit_checks(audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not audit:
        return []
    return _list_of_dicts(audit.get("checks"))


def _recommendations(model_card: dict[str, Any] | None, audit: dict[str, Any] | None, summary: dict[str, Any]) -> list[str]:
    items: list[str] = []
    if audit:
        items.extend(_string_list(audit.get("recommendations")))
    if model_card:
        for item in _string_list(model_card.get("recommendations")):
            if item not in items:
                items.append(item)
    if summary.get("release_status") == "release-ready":
        items.insert(0, "Release evidence is complete; keep this bundle with the tagged version.")
    elif summary.get("release_status") == "blocked":
        items.insert(0, "Do not present this release as complete until failed audit checks are fixed.")
    elif summary.get("release_status") == "needs-audit":
        items.insert(0, "Generate project_audit.json before treating this as a release bundle.")
    return items or ["Review release evidence before sharing the project externally."]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
