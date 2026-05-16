from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.project_audit_artifacts import (
    render_project_audit_html,
    render_project_audit_markdown,
    write_project_audit_html,
    write_project_audit_json,
    write_project_audit_markdown,
    write_project_audit_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    utc_now,
)


CHECK_WEIGHTS = {
    "pass": 1.0,
    "warn": 0.5,
    "fail": 0.0,
}


def build_project_audit(
    registry_path: str | Path,
    *,
    model_card_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
    ci_workflow_hygiene_path: str | Path | None = None,
    title: str = "MiniGPT project audit",
    generated_at: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    registry_file = Path(registry_path)
    registry = _read_required_json(registry_file)
    model_card_file = _resolve_model_card_path(registry_file, model_card_path)
    request_history_summary_file = _resolve_request_history_summary_path(registry_file, request_history_summary_path)
    ci_workflow_hygiene_file = _resolve_ci_workflow_hygiene_path(registry_file, ci_workflow_hygiene_path)
    model_card = _read_json(model_card_file, warnings, "model card") if model_card_file is not None else None
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
    runs = _build_run_rows(registry, model_card if isinstance(model_card, dict) else None)
    checks = _build_checks(
        registry,
        model_card if isinstance(model_card, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        request_history_summary_file,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
        ci_workflow_hygiene_file,
        runs,
    )
    summary = _summarize_checks(
        checks,
        registry,
        model_card if isinstance(model_card, dict) else None,
        request_history_summary if isinstance(request_history_summary, dict) else None,
        ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None,
        runs,
    )

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "registry_path": str(registry_file),
        "model_card_path": None if model_card_file is None else str(model_card_file),
        "request_history_summary_path": None if request_history_summary_file is None else str(request_history_summary_file),
        "ci_workflow_hygiene_path": None if ci_workflow_hygiene_file is None else str(ci_workflow_hygiene_file),
        "summary": summary,
        "checks": checks,
        "request_history_context": _request_history_context(request_history_summary if isinstance(request_history_summary, dict) else None),
        "ci_workflow_context": _ci_workflow_context(ci_workflow_hygiene if isinstance(ci_workflow_hygiene, dict) else None),
        "runs": runs,
        "recommendations": _build_recommendations(checks, summary),
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


def _build_run_rows(registry: dict[str, Any], model_card: dict[str, Any] | None) -> list[dict[str, Any]]:
    model_runs = {}
    if isinstance(model_card, dict):
        for run in model_card.get("runs", []):
            if isinstance(run, dict) and run.get("path"):
                model_runs[str(run["path"])] = run
    rows = []
    for run in registry.get("runs", []):
        if not isinstance(run, dict):
            continue
        model_run = model_runs.get(str(run.get("path")), {})
        status = model_run.get("status") or _derive_status(run)
        row = {
            "name": run.get("name"),
            "path": run.get("path"),
            "status": status,
            "best_val_loss_rank": run.get("best_val_loss_rank"),
            "best_val_loss": run.get("best_val_loss"),
            "best_val_loss_delta": run.get("best_val_loss_delta"),
            "dataset_quality": run.get("dataset_quality"),
            "eval_suite_cases": run.get("eval_suite_cases"),
            "generation_quality_status": run.get("generation_quality_status"),
            "generation_quality_cases": run.get("generation_quality_cases"),
            "generation_quality_pass_count": run.get("generation_quality_pass_count"),
            "generation_quality_warn_count": run.get("generation_quality_warn_count"),
            "generation_quality_fail_count": run.get("generation_quality_fail_count"),
            "artifact_count": run.get("artifact_count"),
            "checkpoint_exists": bool(run.get("checkpoint_exists")),
            "dashboard_exists": bool(run.get("dashboard_exists")),
            "experiment_card_exists": bool(model_run.get("experiment_card_exists")),
            "tags": model_run.get("tags") or run.get("tags") or [],
            "note": model_run.get("note") or run.get("note"),
        }
        rows.append(row)
    rows.sort(key=lambda item: (_rank_sort(item.get("best_val_loss_rank")), str(item.get("name") or "")))
    return rows


def _build_checks(
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    request_history_summary_path: Path | None,
    ci_workflow_hygiene: dict[str, Any] | None,
    ci_workflow_hygiene_path: Path | None,
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    total = len(runs)
    checks = [
        _check("registry_runs", "Registry has runs", "pass" if total > 0 else "fail", f"{total} registered run(s)."),
        _check(
            "best_run",
            "Best run is identified",
            "pass" if isinstance(registry.get("best_by_best_val_loss"), dict) else "fail",
            f"best={_pick(_dict(registry.get('best_by_best_val_loss')), 'name') or 'missing'}",
        ),
        _coverage_check("Comparable loss coverage", "comparable_loss", sum(1 for run in runs if run.get("best_val_loss") is not None), total),
        _coverage_check("Experiment card coverage", "experiment_cards", sum(1 for run in runs if run.get("experiment_card_exists")), total),
        _coverage_check("Dataset quality coverage", "dataset_quality", sum(1 for run in runs if run.get("dataset_quality") not in {None, "missing"}), total),
        _coverage_check("Eval suite coverage", "eval_suite", sum(1 for run in runs if run.get("eval_suite_cases") not in {None, 0}), total),
        _coverage_check("Generation quality coverage", "generation_quality", sum(1 for run in runs if run.get("generation_quality_status") not in {None, "missing"}), total),
        _coverage_check("Checkpoint coverage", "checkpoints", sum(1 for run in runs if run.get("checkpoint_exists")), total),
        _coverage_check("Dashboard coverage", "dashboards", sum(1 for run in runs if run.get("dashboard_exists")), total),
        _check(
            "model_card",
            "Model card is available",
            "pass" if isinstance(model_card, dict) else "warn",
            "model_card.json loaded" if isinstance(model_card, dict) else "model_card.json missing or unreadable",
        ),
        _check(
            "ready_run",
            "At least one ready run",
            "pass" if any(run.get("status") == "ready" for run in runs) else "warn",
            f"{sum(1 for run in runs if run.get('status') == 'ready')} ready run(s).",
        ),
        _request_history_summary_check(request_history_summary, request_history_summary_path),
        _ci_workflow_hygiene_check(ci_workflow_hygiene, ci_workflow_hygiene_path),
    ]
    non_pass_quality = [run.get("name") for run in runs if run.get("dataset_quality") not in {"pass", None, "missing"}]
    checks.append(
        _check(
            "non_pass_quality",
            "No non-pass dataset quality runs",
            "pass" if not non_pass_quality else "warn",
            "all checked runs pass" if not non_pass_quality else "review: " + ", ".join(str(name) for name in non_pass_quality),
        )
    )
    non_pass_generation = [
        run.get("name")
        for run in runs
        if run.get("generation_quality_status") not in {"pass", None, "missing"}
    ]
    checks.append(
        _check(
            "non_pass_generation_quality",
            "No non-pass generation quality runs",
            "pass" if not non_pass_generation else "warn",
            "all analyzed runs pass" if not non_pass_generation else "review: " + ", ".join(str(name) for name in non_pass_generation),
        )
    )
    return checks


def _coverage_check(title: str, check_id: str, count: int, total: int) -> dict[str, Any]:
    if total == 0:
        status = "fail"
    elif count == total:
        status = "pass"
    elif count > 0:
        status = "warn"
    else:
        status = "fail"
    return _check(check_id, title, status, f"{count}/{total} run(s).", {"count": count, "total": total, "ratio": _ratio(count, total)})


def _check(check_id: str, title: str, status: str, detail: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": check_id,
        "title": title,
        "status": status,
        "detail": detail,
        "evidence": evidence or {},
    }


def _request_history_summary_check(
    request_history_summary: dict[str, Any] | None,
    request_history_summary_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        detail = (
            f"request_history_summary.json missing at {request_history_summary_path}"
            if request_history_summary_path is not None
            else "request_history_summary.json missing; local inference stability was not summarized."
        )
        return _check("request_history_summary", "Request history summary is clean", "warn", detail)
    summary = _dict(request_history_summary.get("summary"))
    status = str(summary.get("status") or "missing")
    records = summary.get("total_log_records")
    invalid = summary.get("invalid_record_count")
    timeout_rate = summary.get("timeout_rate")
    error_rate = summary.get("error_rate")
    audit_status = "pass" if status == "pass" else "warn"
    detail = (
        f"status={status}; records={_fmt_any(records)}; invalid={_fmt_any(invalid)}; "
        f"timeout_rate={_fmt_any(timeout_rate)}; error_rate={_fmt_any(error_rate)}."
    )
    return _check(
        "request_history_summary",
        "Request history summary is clean",
        audit_status,
        detail,
        {
            "status": status,
            "total_log_records": records,
            "invalid_record_count": invalid,
            "timeout_rate": timeout_rate,
            "bad_request_rate": summary.get("bad_request_rate"),
            "error_rate": error_rate,
            "path": None if request_history_summary_path is None else str(request_history_summary_path),
        },
    )


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {
            "available": False,
            "status": None,
            "total_log_records": None,
            "timeout_rate": None,
            "error_rate": None,
        }
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "timeout_count": summary.get("timeout_count"),
        "bad_request_count": summary.get("bad_request_count"),
        "error_count": summary.get("error_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "unique_checkpoint_count": summary.get("unique_checkpoint_count"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _ci_workflow_hygiene_check(
    ci_workflow_hygiene: dict[str, Any] | None,
    ci_workflow_hygiene_path: Path | None,
) -> dict[str, Any]:
    if not isinstance(ci_workflow_hygiene, dict):
        detail = (
            f"ci_workflow_hygiene.json missing at {ci_workflow_hygiene_path}"
            if ci_workflow_hygiene_path is not None
            else "ci_workflow_hygiene.json missing; CI workflow policy was not summarized."
        )
        return _check("ci_workflow_hygiene", "CI workflow hygiene is clean", "warn", detail)
    summary = _dict(ci_workflow_hygiene.get("summary"))
    status = str(summary.get("status") or "missing")
    action_count = summary.get("action_count")
    node24_actions = summary.get("node24_native_action_count")
    failed_checks = summary.get("failed_check_count")
    missing_steps = summary.get("missing_step_count")
    forbidden_env = summary.get("forbidden_env_count")
    audit_status = "pass" if status == "pass" else "warn"
    detail = (
        f"status={status}; actions={_fmt_any(action_count)}; node24_native={_fmt_any(node24_actions)}; "
        f"failed_checks={_fmt_any(failed_checks)}; forbidden_env={_fmt_any(forbidden_env)}; "
        f"missing_steps={_fmt_any(missing_steps)}."
    )
    return _check(
        "ci_workflow_hygiene",
        "CI workflow hygiene is clean",
        audit_status,
        detail,
        {
            "status": status,
            "decision": summary.get("decision"),
            "action_count": action_count,
            "node24_native_action_count": node24_actions,
            "failed_check_count": failed_checks,
            "forbidden_env_count": forbidden_env,
            "missing_step_count": missing_steps,
            "python_version": summary.get("python_version"),
            "path": None if ci_workflow_hygiene_path is None else str(ci_workflow_hygiene_path),
        },
    )


def _ci_workflow_context(ci_workflow_hygiene: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(ci_workflow_hygiene, dict):
        return {
            "available": False,
            "status": None,
            "decision": None,
            "action_count": None,
            "node24_native_action_count": None,
            "failed_check_count": None,
        }
    summary = _dict(ci_workflow_hygiene.get("summary"))
    return {
        "available": True,
        "workflow_path": ci_workflow_hygiene.get("workflow_path"),
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


def _summarize_checks(
    checks: list[dict[str, Any]],
    registry: dict[str, Any],
    model_card: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
    ci_workflow_hygiene: dict[str, Any] | None,
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    pass_count = sum(1 for check in checks if check["status"] == "pass")
    warn_count = sum(1 for check in checks if check["status"] == "warn")
    fail_count = sum(1 for check in checks if check["status"] == "fail")
    score = round(100 * sum(CHECK_WEIGHTS[check["status"]] for check in checks) / max(1, len(checks)), 1)
    if fail_count:
        overall = "fail"
    elif warn_count:
        overall = "warn"
    else:
        overall = "pass"
    model_summary = _dict(model_card.get("summary")) if isinstance(model_card, dict) else {}
    request_summary = _dict(request_history_summary.get("summary")) if isinstance(request_history_summary, dict) else {}
    ci_summary = _dict(ci_workflow_hygiene.get("summary")) if isinstance(ci_workflow_hygiene, dict) else {}
    best = _dict(registry.get("best_by_best_val_loss"))
    return {
        "overall_status": overall,
        "score_percent": score,
        "check_count": len(checks),
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "run_count": len(runs),
        "best_run_name": best.get("name"),
        "best_val_loss": best.get("best_val_loss"),
        "ready_runs": model_summary.get("ready_runs") if model_summary else sum(1 for run in runs if run.get("status") == "ready"),
        "review_runs": model_summary.get("review_runs") if model_summary else sum(1 for run in runs if run.get("status") == "review"),
        "request_history_status": request_summary.get("status"),
        "request_history_records": request_summary.get("total_log_records"),
        "request_history_timeout_rate": request_summary.get("timeout_rate"),
        "request_history_error_rate": request_summary.get("error_rate"),
        "ci_workflow_status": ci_summary.get("status"),
        "ci_workflow_decision": ci_summary.get("decision"),
        "ci_workflow_failed_checks": ci_summary.get("failed_check_count"),
        "ci_workflow_node24_actions": ci_summary.get("node24_native_action_count"),
    }


def _build_recommendations(checks: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    items = []
    for check in checks:
        if check["status"] == "pass":
            continue
        if check["id"] == "experiment_cards":
            items.append("Generate experiment cards for every registered run before presenting the project.")
        elif check["id"] == "dataset_quality":
            items.append("Run dataset quality checks for all registered runs.")
        elif check["id"] == "eval_suite":
            items.append("Run the fixed prompt eval suite for all registered checkpoints.")
        elif check["id"] == "generation_quality":
            items.append("Run generation quality analysis for all registered eval suite or sampling outputs.")
        elif check["id"] == "model_card":
            items.append("Build model_card.json so the audit can include project-level context.")
        elif check["id"] == "non_pass_quality":
            items.append("Review runs with non-pass dataset quality before using them as baselines.")
        elif check["id"] == "non_pass_generation_quality":
            items.append("Review runs with non-pass generation quality before release-style handoff.")
        elif check["id"] == "ready_run":
            items.append("Promote at least one run to ready status by completing checkpoint, data quality, and eval artifacts.")
        elif check["id"] == "request_history_summary":
            items.append("Generate or review request_history_summary.json before using local playground activity as release evidence.")
        elif check["id"] == "ci_workflow_hygiene":
            items.append("Generate or review ci_workflow_hygiene.json before using CI workflow policy as release evidence.")
        elif check["id"] == "dashboards":
            items.append("Build dashboards for missing runs to improve reviewability.")
        elif check["id"] == "checkpoints":
            items.append("Restore or create missing checkpoints for registered runs.")
    if not items:
        items.append("All audit checks passed; keep the audit with the model card as release evidence.")
    elif summary.get("overall_status") == "fail":
        items.insert(0, "Fix failed audit checks before treating this MiniGPT state as release-ready.")
    return items


def _derive_status(run: dict[str, Any]) -> str:
    if not run.get("checkpoint_exists") or run.get("best_val_loss") is None:
        return "incomplete"
    if run.get("dataset_quality") in {None, "missing"}:
        return "needs-data-quality"
    if run.get("dataset_quality") != "pass":
        return "review"
    if run.get("eval_suite_cases") in {None, 0}:
        return "needs-eval"
    if run.get("generation_quality_status") in {None, "missing"}:
        return "needs-generation-quality"
    if run.get("generation_quality_status") != "pass":
        return "review"
    return "ready"


def _ratio(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 4)


def _rank_sort(value: Any) -> int:
    if value is None or value == "":
        return 1_000_000
    return int(value)


def _rank_label(value: Any) -> str:
    if value is None or value == "":
        return "unranked"
    return f"#{int(value)}"


def _fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.5g}"
    return "missing" if value is None else str(value)

def _pick(payload: dict[str, Any], key: str) -> Any:
    return payload.get(key) if isinstance(payload, dict) else None
