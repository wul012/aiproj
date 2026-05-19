from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any, Literal, TypedDict

from minigpt.promoted_training_scale_seed_handoff_artifacts import (
    render_promoted_training_scale_seed_handoff_html,
    render_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_csv,
    write_promoted_training_scale_seed_handoff_html,
    write_promoted_training_scale_seed_handoff_json,
    write_promoted_training_scale_seed_handoff_markdown,
    write_promoted_training_scale_seed_handoff_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    count_available_artifacts,
    display_command as _display_command,
    list_of_dicts as _list_of_dicts,
    list_of_strs as _list_of_strs,
    make_artifact_rows,
    string_list as _string_list,
    utc_now,
)


SeedHandoffCleanEvidenceStatus = Literal["ready", "pending-plan", "review", "incomplete"]
SeedHandoffCleanEvidenceRequirementStatus = Literal["not-required", "pass", "fail"]


class SeedHandoffCleanEvidenceReadiness(TypedDict):
    ready: bool
    status: SeedHandoffCleanEvidenceStatus
    detail: str
    status_domain: list[SeedHandoffCleanEvidenceStatus]


class SeedHandoffCleanEvidenceRequirement(TypedDict):
    required: bool
    status: SeedHandoffCleanEvidenceRequirementStatus
    ready: bool
    readiness_status: SeedHandoffCleanEvidenceStatus | None
    detail: str | None
    status_domain: list[SeedHandoffCleanEvidenceRequirementStatus]


SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES: tuple[SeedHandoffCleanEvidenceStatus, ...] = (
    "ready",
    "pending-plan",
    "review",
    "incomplete",
)

SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES: tuple[SeedHandoffCleanEvidenceRequirementStatus, ...] = (
    "not-required",
    "pass",
    "fail",
)


def load_promoted_training_scale_seed(path: str | Path) -> dict[str, Any]:
    seed_path = _resolve_seed_path(Path(path))
    payload = json.loads(seed_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("promoted training scale seed must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(seed_path)
    return payload


def build_promoted_training_scale_seed_handoff(
    seed_path: str | Path,
    *,
    execute: bool = False,
    allow_review: bool = True,
    require_clean_evidence: bool = False,
    timeout_seconds: int = 900,
    generated_at: str | None = None,
    title: str = "MiniGPT promoted training scale seed handoff",
) -> dict[str, Any]:
    seed = load_promoted_training_scale_seed(seed_path)
    seed_file = Path(str(seed.get("_source_path")))
    seed_dir = seed_file.parent
    seed_status = str(seed.get("seed_status") or "")
    next_plan = _dict(seed.get("next_plan"))
    project_root = _resolve_path(next_plan.get("project_root"), seed_dir)
    command = _list_of_strs(next_plan.get("command"))
    allowed, blocked_reason = _handoff_allowed(seed_status, command, allow_review=allow_review)
    execution = _execution_result(
        command,
        project_root=project_root,
        execute=execute,
        allowed=allowed,
        blocked_reason=blocked_reason,
        timeout_seconds=timeout_seconds,
    )
    plan_report = _load_plan_report(project_root, next_plan)
    artifact_rows = _artifact_rows(project_root, next_plan)
    next_batch_command = _list_of_strs(_dict(plan_report.get("batch")).get("command"))
    summary = _summary(seed, next_plan, plan_report, execution, artifact_rows, next_batch_command)
    clean_evidence_requirement = build_seed_handoff_clean_evidence_requirement(
        summary,
        required=require_clean_evidence,
    )
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "seed_path": str(seed_file),
        "seed_status": seed_status,
        "allow_review": bool(allow_review),
        "execute": bool(execute),
        "timeout_seconds": int(timeout_seconds),
        "handoff_allowed": allowed,
        "blocked_reason": blocked_reason,
        "command": command,
        "command_text": _display_command(command),
        "execution": execution,
        "plan_report_path": str(_plan_report_path(project_root, next_plan)),
        "plan_report": plan_report,
        "next_batch_command": next_batch_command,
        "next_batch_command_text": _display_command(next_batch_command),
        "artifact_rows": artifact_rows,
        "summary": summary,
        "clean_evidence_requirement": clean_evidence_requirement,
        "recommendations": _recommendations(
            summary,
            plan_report,
            execution,
            artifact_rows,
            next_batch_command,
            clean_evidence_requirement,
        ),
    }


def build_seed_handoff_clean_evidence_requirement(
    summary: dict[str, Any],
    *,
    required: bool = False,
) -> SeedHandoffCleanEvidenceRequirement:
    ready = bool(summary.get("seed_handoff_clean_evidence_ready"))
    status: SeedHandoffCleanEvidenceRequirementStatus = "not-required"
    if required:
        status = "pass" if ready else "fail"
    readiness_status = summary.get("seed_handoff_clean_evidence_status")
    if readiness_status not in SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES:
        readiness_status = None
    detail = summary.get("seed_handoff_clean_evidence_detail")
    return {
        "required": bool(required),
        "status": status,
        "ready": ready,
        "readiness_status": readiness_status,
        "detail": str(detail) if detail is not None else None,
        "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES),
    }


def _resolve_path(value: Any, base_dir: Path) -> Path:
    if value is None:
        return base_dir
    path = Path(str(value))
    if path.is_absolute():
        return path
    return base_dir / path


def _resolve_seed_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.extend(
            [
                path / "promoted_training_scale_seed.json",
                path / "promoted-seed" / "promoted_training_scale_seed.json",
                path / "seed" / "promoted_training_scale_seed.json",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _load_plan_report(project_root: Path, next_plan: dict[str, Any]) -> dict[str, Any]:
    plan_path = _plan_report_path(project_root, next_plan)
    if not plan_path.is_file():
        return {}
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _plan_report_path(project_root: Path, next_plan: dict[str, Any]) -> Path:
    plan_out_dir = _resolve_path(next_plan.get("plan_out_dir"), project_root)
    return plan_out_dir / "training_scale_plan.json"


def _artifact_rows(project_root: Path, next_plan: dict[str, Any]) -> list[dict[str, Any]]:
    plan_out_dir = _resolve_path(next_plan.get("plan_out_dir"), project_root)
    return make_artifact_rows(
        [
            ("training_scale_plan_json", plan_out_dir / "training_scale_plan.json"),
            ("training_scale_variants_json", plan_out_dir / "training_scale_variants.json"),
            ("training_scale_plan_csv", plan_out_dir / "training_scale_plan.csv"),
            ("training_scale_plan_markdown", plan_out_dir / "training_scale_plan.md"),
            ("training_scale_plan_html", plan_out_dir / "training_scale_plan.html"),
        ]
    )


def _summary(
    seed: dict[str, Any],
    next_plan: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
) -> dict[str, Any]:
    baseline = _dict(seed.get("baseline_seed"))
    plan_summary = _dict(plan_report.get("summary"))
    plan_suite = _dict(plan_report.get("suite"))
    plan_dataset = _dict(plan_report.get("dataset"))
    handoff_guard = _dict(baseline.get("handoff_suite_guard"))
    batch_review = _dict(baseline.get("handoff_batch_review"))
    seed_suite_path = _dict(next_plan.get("suite")).get("path")
    selected_handoff_suite_path = handoff_guard.get("selected_handoff_selected_suite_path")
    plan_suite_path = plan_suite.get("path") or plan_summary.get("suite_path")
    suite_alignment = _suite_alignment(selected_handoff_suite_path, seed_suite_path, plan_suite_path)
    clean_evidence_readiness = _clean_evidence_readiness(execution.get("status"), suite_alignment)
    return {
        "handoff_status": execution.get("status"),
        "seed_status": seed.get("seed_status"),
        "decision_status": baseline.get("decision_status"),
        "selected_name": baseline.get("selected_name"),
        "selected_gate_status": baseline.get("gate_status"),
        "selected_batch_status": baseline.get("batch_status"),
        "selected_readiness_score": baseline.get("readiness_score"),
        "source_count": len(_list_of_dicts(next_plan.get("sources"))),
        "missing_source_count": sum(1 for row in _list_of_dicts(next_plan.get("sources")) if not row.get("exists")),
        "artifact_count": len(artifact_rows),
        "available_artifact_count": count_available_artifacts(artifact_rows),
        "plan_status": "available" if plan_report else "missing",
        "seed_suite_path": seed_suite_path,
        "seed_suite_source": next_plan.get("suite_source"),
        "selected_handoff_require_suite_consistency": handoff_guard.get("selected_handoff_require_suite_consistency"),
        "selected_handoff_suite_consistency": handoff_guard.get("selected_handoff_suite_consistency"),
        "selected_handoff_suite_mismatch_count": handoff_guard.get("selected_handoff_suite_mismatch_count"),
        "selected_handoff_selected_suite_path": selected_handoff_suite_path,
        "handoff_suite_consistent_count": handoff_guard.get("handoff_suite_consistent_count"),
        "handoff_suite_mismatch_total": handoff_guard.get("handoff_suite_mismatch_total"),
        "comparison_ready_handoff_suite_mismatch_total": handoff_guard.get("comparison_ready_handoff_suite_mismatch_total"),
        "selected_handoff_selected_batch_review_status": batch_review.get(
            "selected_handoff_selected_batch_review_status"
        ),
        "selected_handoff_selected_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_review_action_count"
        ),
        "selected_handoff_selected_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_selected_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_selected_batch_maturity_coverage_regression_count": batch_review.get(
            "selected_handoff_selected_batch_maturity_coverage_regression_count"
        ),
        "selected_handoff_batch_comparison_review_action_count": batch_review.get(
            "selected_handoff_batch_comparison_review_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_action_count": batch_review.get(
            "selected_handoff_batch_comparison_blocker_action_count"
        ),
        "selected_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("selected_handoff_batch_comparison_blocker_reasons")
        ),
        "comparison_ready_handoff_selected_batch_review_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_review_count"
        ),
        "comparison_ready_handoff_selected_batch_blocker_count": batch_review.get(
            "comparison_ready_handoff_selected_batch_blocker_count"
        ),
        "comparison_ready_handoff_selected_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_selected_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_selected_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_review_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_review_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_action_total": batch_review.get(
            "comparison_ready_handoff_batch_comparison_blocker_action_total"
        ),
        "comparison_ready_handoff_batch_comparison_blocker_reasons": _string_list(
            batch_review.get("comparison_ready_handoff_batch_comparison_blocker_reasons")
        ),
        "plan_suite_mode": plan_suite.get("mode") or plan_summary.get("suite_mode"),
        "plan_suite_name": plan_suite.get("name") or plan_summary.get("suite_name"),
        "plan_suite_path": plan_suite_path,
        "seed_handoff_suite_alignment_status": suite_alignment["status"],
        "seed_handoff_suite_alignment_detail": suite_alignment["detail"],
        "seed_handoff_suite_alignment_mismatch_count": suite_alignment["mismatch_count"],
        "seed_handoff_suite_alignment_missing_count": suite_alignment["missing_count"],
        "seed_handoff_clean_evidence_ready": clean_evidence_readiness["ready"],
        "seed_handoff_clean_evidence_status": clean_evidence_readiness["status"],
        "seed_handoff_clean_evidence_detail": clean_evidence_readiness["detail"],
        "seed_handoff_clean_evidence_status_domain": clean_evidence_readiness["status_domain"],
        "plan_scale_tier": plan_dataset.get("scale_tier"),
        "plan_variant_count": len(_list_of_dicts(plan_report.get("variants"))),
        "plan_source_count": plan_dataset.get("source_count"),
        "plan_quality_status": plan_dataset.get("quality_status"),
        "next_batch_command_available": bool(next_batch_command),
        "execution_returncode": execution.get("returncode"),
        "execution_elapsed_seconds": execution.get("elapsed_seconds"),
    }


def _clean_evidence_readiness(handoff_status: Any, suite_alignment: dict[str, Any]) -> SeedHandoffCleanEvidenceReadiness:
    alignment_status = str(suite_alignment.get("status") or "")
    detail = str(suite_alignment.get("detail") or "")
    if alignment_status == "consistent" and handoff_status == "completed":
        return _clean_evidence_payload(
            ready=True,
            status="ready",
            detail="completed handoff has consistent suite alignment and can be used as clean comparison evidence",
        )
    if alignment_status == "pending-plan":
        return _clean_evidence_payload(
            ready=False,
            status="pending-plan",
            detail="execute the seed handoff before treating clean comparison evidence as ready",
        )
    if alignment_status == "missing":
        return _clean_evidence_payload(
            ready=False,
            status="incomplete",
            detail=f"missing suite alignment evidence: {detail}",
        )
    if alignment_status == "mismatch":
        return _clean_evidence_payload(
            ready=False,
            status="review",
            detail=f"review suite alignment mismatch before using this as clean comparison evidence: {detail}",
        )
    return _clean_evidence_payload(
        ready=False,
        status="review",
        detail="review seed handoff suite alignment before treating this as clean comparison evidence",
    )


def _clean_evidence_payload(
    *,
    ready: bool,
    status: SeedHandoffCleanEvidenceStatus,
    detail: str,
) -> SeedHandoffCleanEvidenceReadiness:
    return {
        "ready": ready,
        "status": status,
        "detail": detail,
        "status_domain": list(SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES),
    }


def _suite_alignment(selected_handoff_path: Any, seed_path: Any, plan_path: Any) -> dict[str, Any]:
    selected = None if selected_handoff_path is None else str(selected_handoff_path)
    seed = None if seed_path is None else str(seed_path)
    plan = None if plan_path is None else str(plan_path)
    missing = [name for name, value in (("selected_handoff", selected), ("seed", seed)) if not value]
    mismatches = []
    if selected and seed and selected != seed:
        mismatches.append(f"selected_handoff={selected} differs from seed={seed}")
    if plan:
        if seed and plan != seed:
            mismatches.append(f"plan={plan} differs from seed={seed}")
        if selected and plan != selected:
            mismatches.append(f"plan={plan} differs from selected_handoff={selected}")
    if missing:
        status = "missing"
        detail = "missing required suite path(s): " + ", ".join(missing)
    elif mismatches:
        status = "mismatch"
        detail = "; ".join(mismatches)
    elif plan:
        status = "consistent"
        detail = f"selected_handoff, seed, and plan suite paths align at {plan}"
    else:
        status = "pending-plan"
        detail = f"selected_handoff and seed suite paths align at {seed}; plan suite is not available yet"
    return {
        "status": status,
        "detail": detail,
        "mismatch_count": len(mismatches),
        "missing_count": len(missing),
    }


def _recommendations(
    summary: dict[str, Any],
    plan_report: dict[str, Any],
    execution: dict[str, Any],
    artifact_rows: list[dict[str, Any]],
    next_batch_command: list[str],
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None = None,
) -> list[str]:
    status = str(summary.get("handoff_status") or "")
    alignment_recommendations = _suite_alignment_recommendations(summary)
    clean_evidence_recommendations = _clean_evidence_requirement_recommendations(clean_evidence_requirement)
    batch_review_recommendations = _handoff_batch_review_recommendations(summary)
    if status == "planned":
        return (
            alignment_recommendations
            + clean_evidence_recommendations
            + batch_review_recommendations
            + ["Review the generated seed command, then rerun with --execute to materialize the next training scale plan."]
        )
    if status == "blocked":
        return (
            alignment_recommendations
            + clean_evidence_recommendations
            + batch_review_recommendations
            + ["Fix the seed or plan blockers before trying to produce the next training scale plan."]
        )
    if status == "timeout":
        return (
            alignment_recommendations
            + clean_evidence_recommendations
            + batch_review_recommendations
            + ["Inspect the partial plan output tree and rerun with a larger timeout if the plan command is still valid."]
        )
    if status == "failed":
        return (
            alignment_recommendations
            + clean_evidence_recommendations
            + batch_review_recommendations
            + ["Inspect stdout/stderr tails and the seed command before retrying the next plan handoff."]
        )
    recommendations = alignment_recommendations + clean_evidence_recommendations + batch_review_recommendations + [
        "Use the generated plan report and batch command as the next input to the training-scale workflow.",
    ]
    if plan_report:
        recommendations.append("Keep the generated plan JSON and variants JSON as the evidence for the next cycle.")
    if artifact_rows and summary.get("available_artifact_count") != summary.get("artifact_count"):
        recommendations.append("Some expected plan artifacts are missing; inspect the plan output directory before moving on.")
    if next_batch_command:
        recommendations.append("The next batch command is ready, but it should be reviewed before executing training.")
    if execution.get("returncode") not in {None, 0}:
        recommendations.append("The plan command returned a non-zero exit code, so treat the seed handoff as failed.")
    return recommendations


def _handoff_batch_review_recommendations(summary: dict[str, Any]) -> list[str]:
    selected_status = str(summary.get("selected_handoff_selected_batch_review_status") or "")
    if selected_status == "blocker":
        return [
            "Resolve selected handoff batch blocker actions before treating this seed handoff as clean model-quality evidence."
        ]
    if selected_status == "review":
        return [
            "Review selected handoff batch actions before treating this seed handoff as clean model-quality evidence."
        ]
    if summary.get("comparison_ready_handoff_selected_batch_blocker_count"):
        return [
            "Other comparison-ready promoted inputs carried handoff batch blockers; keep them with this handoff review context."
        ]
    return []


def _clean_evidence_requirement_recommendations(
    clean_evidence_requirement: SeedHandoffCleanEvidenceRequirement | None,
) -> list[str]:
    requirement = _dict(clean_evidence_requirement)
    if not requirement.get("required"):
        return []
    status = str(requirement.get("status") or "")
    detail = str(requirement.get("detail") or "")
    if status == "pass":
        return ["Clean-evidence requirement passed; this seed handoff can be used as clean comparison evidence."]
    if status == "fail":
        suffix = f": {detail}" if detail else "."
        return [f"Clean-evidence requirement failed; resolve readiness before using this handoff as clean comparison evidence{suffix}"]
    return ["Review clean-evidence requirement status before using this handoff as clean comparison evidence."]


def _suite_alignment_recommendations(summary: dict[str, Any]) -> list[str]:
    status = str(summary.get("seed_handoff_suite_alignment_status") or "")
    detail = str(summary.get("seed_handoff_suite_alignment_detail") or "")
    if status == "pending-plan":
        return ["Suite alignment is pending plan generation; execute the seed handoff before treating the plan suite as confirmed."]
    if status == "consistent":
        return ["Suite alignment is consistent across selected handoff, seed, and generated plan paths."]
    if status == "mismatch":
        return [f"Review suite alignment mismatch before using this handoff as clean model-quality evidence: {detail}"]
    if status == "missing":
        return [f"Record missing suite alignment evidence before treating this handoff as a clean comparison: {detail}"]
    return ["Review suite alignment evidence before continuing the next training-scale cycle."]


def _handoff_allowed(seed_status: str, command: list[str], *, allow_review: bool) -> tuple[bool, str | None]:
    if not command:
        return False, "seed did not provide a plan command"
    if seed_status == "ready":
        return True, None
    if seed_status == "review" and allow_review:
        return True, None
    if seed_status == "review":
        return False, "seed status is review and allow_review is false"
    return False, f"seed status is {seed_status or 'missing'}"


def _execution_result(
    command: list[str],
    *,
    project_root: Path,
    execute: bool,
    allowed: bool,
    blocked_reason: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not execute:
        return {
            "status": "planned" if allowed else "blocked",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
            "blocked_reason": blocked_reason,
        }
    if not allowed:
        return {
            "status": "blocked",
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "",
            "blocked_reason": blocked_reason,
        }
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_seconds)),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.perf_counter() - started, 3)
        return {
            "status": "timeout",
            "returncode": None,
            "elapsed_seconds": elapsed,
            "stdout_tail": _tail(_decode_timeout_text(exc.stdout)),
            "stderr_tail": _tail(_decode_timeout_text(exc.stderr)),
            "blocked_reason": f"command exceeded timeout_seconds={timeout_seconds}",
        }
    elapsed = round(time.perf_counter() - started, 3)
    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
        "blocked_reason": None if completed.returncode == 0 else "plan command returned non-zero",
    }


def _decode_timeout_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _tail(text: str, max_chars: int = 700) -> str:
    text = text.strip()
    return text[-max_chars:] if len(text) > max_chars else text

__all__ = [
    "SEED_HANDOFF_CLEAN_EVIDENCE_REQUIREMENT_STATUSES",
    "SEED_HANDOFF_CLEAN_EVIDENCE_STATUSES",
    "SeedHandoffCleanEvidenceRequirement",
    "SeedHandoffCleanEvidenceRequirementStatus",
    "SeedHandoffCleanEvidenceReadiness",
    "SeedHandoffCleanEvidenceStatus",
    "build_promoted_training_scale_seed_handoff",
    "build_seed_handoff_clean_evidence_requirement",
    "load_promoted_training_scale_seed",
    "render_promoted_training_scale_seed_handoff_html",
    "render_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_csv",
    "write_promoted_training_scale_seed_handoff_html",
    "write_promoted_training_scale_seed_handoff_json",
    "write_promoted_training_scale_seed_handoff_markdown",
    "write_promoted_training_scale_seed_handoff_outputs",
]
