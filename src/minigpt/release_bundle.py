from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
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
    ci_workflow_hygiene_path: str | Path | None = None,
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
    ci_workflow_hygiene_file = _resolve_ci_workflow_hygiene_path(registry_file, audit_file, ci_workflow_hygiene_path)
    model_card = _read_json(model_file, warnings, "model card") if model_file is not None else None
    audit = _read_json(audit_file, warnings, "project audit") if audit_file is not None else None
    request_history_summary = (
        _read_json(request_history_summary_file, warnings, "request history summary")
        if request_history_summary_file is not None
        else None
    )
    ci_workflow_hygiene = (
        _read_json(ci_workflow_hygiene_file, warnings, "CI workflow hygiene")
        if ci_workflow_hygiene_file is not None
        else None
    )
    artifacts = _collect_release_artifacts(registry_file, model_file, audit_file, request_history_summary_file, ci_workflow_hygiene_file)
    top_runs = _top_runs(registry, model_card if isinstance(model_card, dict) else None)
    summary = _build_summary(
        registry,
        model_card if isinstance(model_card, dict) else None,
        audit if isinstance(audit, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
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
            "ci_workflow_hygiene_path": None if ci_workflow_hygiene_file is None else str(ci_workflow_hygiene_file),
        },
        "artifacts": artifacts,
        "top_runs": top_runs,
        "audit_checks": _audit_checks(audit if isinstance(audit, dict) else None),
        "request_history_context": _request_history_context(request_history_summary if isinstance(request_history_summary, dict) else None),
        "ci_workflow_context": _ci_workflow_context(ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None, audit if isinstance(audit, dict) else None),
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


def _default_release_name(registry_path: Path) -> str:
    return f"{registry_path.parent.name or 'registry'} release"


def _build_summary(
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    audit: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    ci_workflow_hygiene: dict[str, Any] | None,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    best = _dict(registry.get("best_by_best_val_loss"))
    audit_summary = _dict(audit.get("summary")) if audit else {}
    model_summary = _dict(model_card.get("summary")) if model_card else {}
    request_summary = _dict(request_history_summary.get("summary")) if isinstance(request_history_summary, dict) else {}
    ci_summary = _dict(ci_workflow_hygiene.get("summary")) if isinstance(ci_workflow_hygiene, dict) else {}
    audit_status = audit_summary.get("overall_status")
    release_status = _release_status(audit_status, audit_summary.get("fail_count"), audit_summary.get("warn_count"))
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
        "ci_workflow_status": audit_summary.get("ci_workflow_status") or ci_summary.get("status"),
        "ci_workflow_failed_checks": audit_summary.get("ci_workflow_failed_checks") if audit_summary.get("ci_workflow_failed_checks") is not None else ci_summary.get("failed_check_count"),
        "ci_workflow_node24_actions": audit_summary.get("ci_workflow_node24_actions") if audit_summary.get("ci_workflow_node24_actions") is not None else ci_summary.get("node24_native_action_count"),
        "available_artifacts": sum(1 for artifact in artifacts if artifact.get("exists")),
        "missing_artifacts": sum(1 for artifact in artifacts if not artifact.get("exists")),
    }


def _release_status(audit_status: Any, fail_count: Any, warn_count: Any) -> str:
    if audit_status == "pass":
        return "release-ready"
    if audit_status == "warn":
        return "review-needed"
    if audit_status == "fail" or fail_count:
        return "blocked"
    if warn_count:
        return "review-needed"
    return "needs-audit"


def _collect_release_artifacts(
    registry_path: Path,
    model_card_path: Path | None,
    audit_path: Path | None,
    request_history_summary_path: Path | None,
    ci_workflow_hygiene_path: Path | None,
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
            "python_version": summary.get("python_version"),
        }
    if audit_context:
        return dict(audit_context)
    return {"available": False, "status": None, "failed_check_count": None}


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
