from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    first_present,
    list_of_dicts as _list_of_dicts,
    positive_int_mapping as _int_mapping,
    string_list as _string_list,
    utc_now,
)
from minigpt.training_scale_promotion_artifacts import (
    render_training_scale_promotion_html,
    render_training_scale_promotion_markdown,
    write_training_scale_promotion_csv,
    write_training_scale_promotion_html,
    write_training_scale_promotion_json,
    write_training_scale_promotion_markdown,
    write_training_scale_promotion_outputs,
)


REQUIRED_VARIANT_ARTIFACTS = [
    "checkpoint",
    "run_manifest",
    "eval_suite",
    "generation_quality",
    "benchmark_scorecard",
    "dataset_card",
    "registry",
    "maturity_summary",
    "maturity_narrative",
]


def load_training_scale_handoff(path: str | Path) -> dict[str, Any]:
    handoff_path = _resolve_handoff_path(Path(path))
    payload = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("training scale handoff must be a JSON object")
    payload = dict(payload)
    payload["_source_path"] = str(handoff_path)
    return payload


def build_training_scale_promotion(
    handoff_path: str | Path,
    *,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale promotion",
) -> dict[str, Any]:
    handoff = load_training_scale_handoff(handoff_path)
    handoff_file = Path(str(handoff.get("_source_path")))
    handoff_dir = handoff_file.parent
    command = _string_list(handoff.get("command"))
    project_root = _project_root(command, handoff_dir)
    out_root = _out_root(command, handoff, project_root, handoff_dir)

    scale_run_path = _handoff_artifact_path(handoff, "training_scale_run_json", out_root / "training_scale_run.json", project_root, handoff_dir)
    batch_path = _handoff_artifact_path(handoff, "batch_json", out_root / "batch" / "training_portfolio_batch.json", project_root, handoff_dir)
    scale_run = _read_json(scale_run_path)
    batch = _read_json(batch_path)
    variants = _variant_rows(batch, project_root, handoff_dir)
    evidence_rows = _evidence_rows(handoff_file, handoff, scale_run_path, batch_path, variants, project_root, handoff_dir)
    suite_guard = _suite_guard(handoff)
    clean_batch_review_guard = _clean_batch_review_guard(handoff)
    blockers, review_items = _issues(handoff, scale_run, batch, variants, evidence_rows, clean_batch_review_guard)
    summary = _summary(handoff, scale_run, batch, variants, evidence_rows, blockers, review_items, suite_guard, clean_batch_review_guard)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "handoff_path": str(handoff_file),
        "project_root": str(project_root),
        "out_root": str(out_root),
        "suite_guard": suite_guard,
        "clean_batch_review_guard": clean_batch_review_guard,
        "handoff_summary": _dict(handoff.get("summary")),
        "training_scale_run_path": str(scale_run_path),
        "training_scale_run": _scale_run_digest(scale_run),
        "batch_path": str(batch_path),
        "batch": _batch_digest(batch),
        "variants": variants,
        "evidence_rows": evidence_rows,
        "summary": summary,
        "blockers": blockers,
        "review_items": review_items,
        "recommendations": _recommendations(summary, blockers, review_items),
    }


def _resolve_handoff_path(path: Path) -> Path:
    candidates = [path]
    if path.is_dir():
        candidates.append(path / "training_scale_handoff.json")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(path)


def _project_root(command: list[str], handoff_dir: Path) -> Path:
    value = _option_value(command, "--project-root")
    if value:
        return Path(value)
    return Path.cwd()


def _out_root(command: list[str], handoff: dict[str, Any], project_root: Path, handoff_dir: Path) -> Path:
    value = _option_value(command, "--out-root")
    if value:
        return _resolve_path(value, project_root, handoff_dir)
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        if row.get("key") == "training_scale_run_json":
            return _resolve_path(row.get("path"), project_root, handoff_dir).parent
    return project_root


def _handoff_artifact_path(
    handoff: dict[str, Any],
    key: str,
    fallback: Path,
    project_root: Path,
    handoff_dir: Path,
) -> Path:
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        if row.get("key") == key and row.get("path"):
            return _resolve_path(row.get("path"), project_root, handoff_dir)
    return fallback


def _variant_rows(batch: dict[str, Any], project_root: Path, handoff_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for item in _list_of_dicts(batch.get("variant_results")):
        portfolio_json = _resolve_path(item.get("portfolio_json") or item.get("portfolio_path"), project_root, handoff_dir)
        portfolio = _read_json(portfolio_json)
        artifact_rows = _portfolio_artifact_rows(portfolio, project_root, handoff_dir)
        missing_required = [key for key in REQUIRED_VARIANT_ARTIFACTS if not _artifact_exists(artifact_rows, key)]
        blocked = item.get("status") != "completed" or _dict(portfolio.get("execution")).get("status") != "completed"
        status = "blocked" if blocked else "review" if missing_required else "ready"
        artifacts = _dict(portfolio.get("artifacts"))
        rows.append(
            {
                "name": item.get("name"),
                "description": item.get("description"),
                "promotion_status": status,
                "status": item.get("status"),
                "run_name": portfolio.get("run_name"),
                "dataset_name": portfolio.get("dataset_name"),
                "dataset_version": portfolio.get("dataset_version"),
                "portfolio_json": str(portfolio_json),
                "portfolio_html": str(_resolve_path(item.get("portfolio_html"), project_root, handoff_dir)) if item.get("portfolio_html") else None,
                "run_dir": artifacts.get("run_dir"),
                "step_count": _dict(portfolio.get("execution")).get("step_count") or item.get("step_count"),
                "completed_steps": _dict(portfolio.get("execution")).get("completed_steps") or item.get("completed_steps"),
                "failed_step": _dict(portfolio.get("execution")).get("failed_step") or item.get("failed_step"),
                "required_artifact_count": len(REQUIRED_VARIANT_ARTIFACTS),
                "available_required_artifact_count": len(REQUIRED_VARIANT_ARTIFACTS) - len(missing_required),
                "missing_required": missing_required,
                "checkpoint_exists": _artifact_exists(artifact_rows, "checkpoint"),
                "run_manifest_exists": _artifact_exists(artifact_rows, "run_manifest"),
                "registry_exists": _artifact_exists(artifact_rows, "registry"),
                "maturity_narrative_exists": _artifact_exists(artifact_rows, "maturity_narrative"),
                "artifact_rows": artifact_rows,
            }
        )
    return rows


def _portfolio_artifact_rows(portfolio: dict[str, Any], project_root: Path, handoff_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(_dict(portfolio.get("artifacts")).items()):
        path = _resolve_path(value, project_root, handoff_dir)
        rows.append({"key": key, "path": str(path), "exists": path.exists()})
    return rows


def _evidence_rows(
    handoff_file: Path,
    handoff: dict[str, Any],
    scale_run_path: Path,
    batch_path: Path,
    variants: list[dict[str, Any]],
    project_root: Path,
    handoff_dir: Path,
) -> list[dict[str, Any]]:
    rows = [
        {"key": "handoff_json", "path": str(handoff_file), "exists": handoff_file.exists()},
        {"key": "training_scale_run_json", "path": str(scale_run_path), "exists": scale_run_path.exists()},
        {"key": "batch_json", "path": str(batch_path), "exists": batch_path.exists()},
    ]
    for row in _list_of_dicts(handoff.get("artifact_rows")):
        path = _resolve_path(row.get("path"), project_root, handoff_dir)
        rows.append({"key": f"handoff:{row.get('key')}", "path": str(path), "exists": path.exists()})
    for variant in variants:
        for artifact in _list_of_dicts(variant.get("artifact_rows")):
            if artifact.get("key") in REQUIRED_VARIANT_ARTIFACTS:
                rows.append(
                    {
                        "key": f"variant:{variant.get('name')}:{artifact.get('key')}",
                        "path": artifact.get("path"),
                        "exists": artifact.get("exists"),
                    }
                )
    return rows


def _issues(
    handoff: dict[str, Any],
    scale_run: dict[str, Any],
    batch: dict[str, Any],
    variants: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    clean_batch_review_guard: dict[str, Any],
) -> tuple[list[str], list[str]]:
    blockers = []
    review_items = []
    handoff_summary = _dict(handoff.get("summary"))
    handoff_status = handoff_summary.get("handoff_status") or _dict(handoff.get("execution")).get("status")
    if handoff_status != "completed":
        blockers.append(f"handoff status is {handoff_status or 'missing'}")
    if _dict(handoff.get("execution")).get("returncode") not in (0, None):
        blockers.append("handoff execute command returned non-zero")
    if clean_batch_review_guard.get("handoff_require_clean_batch_review") and (
        clean_batch_review_guard.get("handoff_clean_batch_review_status") != "clean"
        or int(clean_batch_review_guard.get("handoff_batch_maturity_ci_regression_count") or 0)
    ):
        blockers.append("handoff requires clean batch-review evidence but status is not clean")
    if scale_run.get("status") != "completed":
        blockers.append(f"training scale run status is {scale_run.get('status') or 'missing'}")
    batch_status = _nested(batch, "execution", "status") or _nested(scale_run, "batch_summary", "status")
    if batch_status != "completed":
        blockers.append(f"training portfolio batch status is {batch_status or 'missing'}")
    if not variants:
        blockers.append("no variant portfolio results were found")
    blocked_variants = [str(row.get("name")) for row in variants if row.get("promotion_status") == "blocked"]
    if blocked_variants:
        blockers.append("variant portfolios failed: " + ", ".join(blocked_variants))
    missing_required = [
        f"{row.get('name')} missing {', '.join(_string_list(row.get('missing_required')))}"
        for row in variants
        if _string_list(row.get("missing_required"))
    ]
    review_items.extend(missing_required)
    missing_evidence = [str(row.get("key")) for row in evidence_rows if not row.get("exists")]
    if missing_evidence:
        review_items.append("missing evidence rows: " + ", ".join(missing_evidence[:8]))
    return blockers, review_items


def _summary(
    handoff: dict[str, Any],
    scale_run: dict[str, Any],
    batch: dict[str, Any],
    variants: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    blockers: list[str],
    review_items: list[str],
    suite_guard: dict[str, Any],
    clean_batch_review_guard: dict[str, Any],
) -> dict[str, Any]:
    ready_variants = [row for row in variants if row.get("promotion_status") == "ready"]
    required_total = sum(int(row.get("required_artifact_count") or 0) for row in variants)
    required_available = sum(int(row.get("available_required_artifact_count") or 0) for row in variants)
    promotion_status = "blocked" if blockers else "review" if review_items else "promoted"
    return {
        "promotion_status": promotion_status,
        "handoff_status": _dict(handoff.get("summary")).get("handoff_status") or _dict(handoff.get("execution")).get("status"),
        "handoff_require_suite_consistency": suite_guard.get("handoff_require_suite_consistency"),
        "handoff_suite_consistency": suite_guard.get("handoff_suite_consistency"),
        "handoff_suite_mismatch_count": suite_guard.get("handoff_suite_mismatch_count"),
        "handoff_selected_suite_path": suite_guard.get("handoff_selected_suite_path"),
        "handoff_require_clean_batch_review": clean_batch_review_guard.get("handoff_require_clean_batch_review"),
        "handoff_clean_batch_review_status": clean_batch_review_guard.get("handoff_clean_batch_review_status"),
        "handoff_selected_batch_review_status": suite_guard.get("handoff_selected_batch_review_status"),
        "handoff_selected_batch_comparison_review_action_count": suite_guard.get("handoff_selected_batch_comparison_review_action_count"),
        "handoff_selected_batch_comparison_blocker_action_count": suite_guard.get("handoff_selected_batch_comparison_blocker_action_count"),
        "handoff_selected_batch_maturity_coverage_regression_count": suite_guard.get("handoff_selected_batch_maturity_coverage_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_count": suite_guard.get("handoff_selected_batch_maturity_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": suite_guard.get(
            "handoff_selected_batch_maturity_ci_regression_reason_counts"
        )
        or clean_batch_review_guard.get("handoff_selected_batch_maturity_ci_regression_reason_counts"),
        "handoff_batch_comparison_review_action_count": suite_guard.get("handoff_batch_comparison_review_action_count"),
        "handoff_batch_comparison_blocker_action_count": suite_guard.get("handoff_batch_comparison_blocker_action_count"),
        "handoff_batch_maturity_coverage_regression_count": suite_guard.get("handoff_batch_maturity_coverage_regression_count"),
        "handoff_batch_maturity_ci_regression_count": suite_guard.get("handoff_batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": suite_guard.get("handoff_batch_maturity_ci_regression_reason_counts")
        or clean_batch_review_guard.get("handoff_batch_maturity_ci_regression_reason_counts"),
        "handoff_batch_maturity_ci_regression_names": suite_guard.get("handoff_batch_maturity_ci_regression_names"),
        "handoff_batch_comparison_blocker_reasons": suite_guard.get("handoff_batch_comparison_blocker_reasons"),
        "scale_run_status": scale_run.get("status"),
        "batch_status": _nested(batch, "execution", "status") or _nested(scale_run, "batch_summary", "status"),
        "variant_count": len(variants),
        "ready_variant_count": len(ready_variants),
        "checkpoint_count": sum(1 for row in variants if row.get("checkpoint_exists")),
        "registry_count": sum(1 for row in variants if row.get("registry_exists")),
        "maturity_narrative_count": sum(1 for row in variants if row.get("maturity_narrative_exists")),
        "required_artifact_count": required_total,
        "available_required_artifact_count": required_available,
        "evidence_count": len(evidence_rows),
        "available_evidence_count": sum(1 for row in evidence_rows if row.get("exists")),
        "blocker_count": len(blockers),
        "review_item_count": len(review_items),
    }


def _scale_run_digest(scale_run: dict[str, Any]) -> dict[str, Any]:
    gate = _dict(scale_run.get("gate"))
    batch = _dict(scale_run.get("batch_summary"))
    return {
        "status": scale_run.get("status"),
        "allowed": scale_run.get("allowed"),
        "gate_profile": scale_run.get("gate_profile"),
        "gate_status": gate.get("overall_status"),
        "batch_status": batch.get("status"),
        "completed_variant_count": batch.get("completed_variant_count"),
        "variant_count": batch.get("variant_count"),
    }


def _batch_digest(batch: dict[str, Any]) -> dict[str, Any]:
    execution = _dict(batch.get("execution"))
    return {
        "status": execution.get("status"),
        "variant_count": execution.get("variant_count") or batch.get("variant_count"),
        "completed_variant_count": execution.get("completed_variant_count"),
        "comparison_status": execution.get("comparison_status"),
        "failed_variant": execution.get("failed_variant"),
    }


def _recommendations(summary: dict[str, Any], blockers: list[str], review_items: list[str]) -> list[str]:
    status = str(summary.get("promotion_status") or "")
    if summary.get("handoff_require_clean_batch_review") and (
        summary.get("handoff_clean_batch_review_status") != "clean"
        or int(summary.get("handoff_batch_maturity_ci_regression_count") or 0)
    ):
        detail = _reason_detail(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail else ""
        return ["Resolve handoff clean batch-review requirement before accepting this run as promotion-ready evidence." + suffix]
    if summary.get("handoff_selected_batch_review_status") == "blocker":
        return ["Resolve selected batch comparison blocker actions before treating this handoff as promotion-ready evidence."]
    if int(summary.get("handoff_batch_maturity_ci_regression_count") or 0):
        detail = _reason_detail(summary.get("handoff_batch_maturity_ci_regression_reason_counts"))
        suffix = f" Observed reasons: {detail}." if detail else ""
        return ["Resolve CI-regressed handoff batch evidence before treating this handoff as promotion-ready evidence." + suffix]
    if summary.get("handoff_selected_batch_review_status") == "review":
        return ["Review selected batch comparison actions before treating this handoff as promotion-ready evidence."]
    if status == "promoted":
        return [
            "Use the promoted variant as a stable local baseline for the next training-scale comparison.",
            "Keep the handoff and promotion JSON together when sharing this run as project evidence.",
        ]
    if blockers:
        return ["Stop promotion and inspect the blocking execution or batch status before continuing."]
    if review_items:
        return ["Review missing optional evidence before treating this handoff as a mature baseline."]
    return ["Inspect the promotion summary before selecting the next larger training profile."]


def _suite_guard(handoff: dict[str, Any]) -> dict[str, Any]:
    handoff_summary = _dict(handoff.get("summary"))
    guard = _dict(handoff.get("suite_guard"))
    required = first_present(
        guard.get("decision_require_suite_consistency"),
        guard.get("require_suite_consistency"),
        handoff_summary.get("decision_require_suite_consistency"),
        handoff_summary.get("require_suite_consistency"),
    )
    return {
        "handoff_require_suite_consistency": bool(required),
        "handoff_suite_consistency": first_present(guard.get("suite_consistency"), handoff_summary.get("suite_consistency")),
        "handoff_suite_mismatch_count": first_present(guard.get("suite_mismatch_count"), handoff_summary.get("suite_mismatch_count")),
        "handoff_selected_suite_path": first_present(guard.get("selected_suite_path"), handoff_summary.get("selected_suite_path")),
        "handoff_selected_batch_review_status": _handoff_value(handoff, "selected_batch_review_status"),
        "handoff_selected_batch_comparison_review_action_count": _handoff_value(handoff, "selected_batch_comparison_review_action_count"),
        "handoff_selected_batch_comparison_blocker_action_count": _handoff_value(handoff, "selected_batch_comparison_blocker_action_count"),
        "handoff_selected_batch_maturity_coverage_regression_count": _handoff_value(handoff, "selected_batch_maturity_coverage_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_count": _handoff_value(handoff, "selected_batch_maturity_ci_regression_count"),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            _handoff_value(handoff, "selected_batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_comparison_review_action_count": _handoff_value(handoff, "batch_comparison_review_action_count"),
        "handoff_batch_comparison_blocker_action_count": _handoff_value(handoff, "batch_comparison_blocker_action_count"),
        "handoff_batch_maturity_coverage_regression_count": _handoff_value(handoff, "batch_maturity_coverage_regression_count"),
        "handoff_batch_maturity_ci_regression_count": _handoff_value(handoff, "batch_maturity_ci_regression_count"),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            _handoff_value(handoff, "batch_maturity_ci_regression_reason_counts")
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(_handoff_value(handoff, "batch_maturity_ci_regression_names")),
        "handoff_batch_comparison_blocker_reasons": _string_list(_handoff_value(handoff, "batch_comparison_blocker_reasons")),
        "workflow_suite_path": guard.get("workflow_suite_path") or handoff_summary.get("workflow_suite_path"),
        "workflow_suite_name": guard.get("workflow_suite_name") or handoff_summary.get("workflow_suite_name"),
    }


def _clean_batch_review_guard(handoff: dict[str, Any]) -> dict[str, Any]:
    handoff_summary = _dict(handoff.get("summary"))
    guard = _dict(handoff.get("clean_batch_review_guard"))
    required = first_present(
        guard.get("decision_require_clean_batch_review"),
        guard.get("require_clean_batch_review"),
        handoff_summary.get("decision_require_clean_batch_review"),
        handoff_summary.get("require_clean_batch_review"),
    )
    return {
        "handoff_require_clean_batch_review": bool(required),
        "handoff_clean_batch_review_status": first_present(
            guard.get("clean_batch_review_status"),
            handoff_summary.get("clean_batch_review_status"),
            handoff_summary.get("selected_batch_review_status"),
        ),
        "handoff_batch_comparison_review_action_count": first_present(
            guard.get("batch_comparison_review_action_count"),
            handoff_summary.get("batch_comparison_review_action_count"),
        ),
        "handoff_batch_comparison_blocker_action_count": first_present(
            guard.get("batch_comparison_blocker_action_count"),
            handoff_summary.get("batch_comparison_blocker_action_count"),
        ),
        "handoff_batch_maturity_coverage_regression_count": first_present(
            guard.get("batch_maturity_coverage_regression_count"),
            handoff_summary.get("batch_maturity_coverage_regression_count"),
        ),
        "handoff_batch_maturity_ci_regression_count": first_present(
            guard.get("batch_maturity_ci_regression_count"),
            handoff_summary.get("batch_maturity_ci_regression_count"),
        ),
        "handoff_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                guard.get("batch_maturity_ci_regression_reason_counts"),
                handoff_summary.get("batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_selected_batch_maturity_ci_regression_reason_counts": _int_mapping(
            first_present(
                guard.get("selected_batch_maturity_ci_regression_reason_counts"),
                handoff_summary.get("selected_batch_maturity_ci_regression_reason_counts"),
            )
        ),
        "handoff_batch_maturity_ci_regression_names": _string_list(
            first_present(
                guard.get("batch_maturity_ci_regression_names"),
                handoff_summary.get("batch_maturity_ci_regression_names"),
            )
        ),
        "handoff_batch_comparison_blocker_reasons": _string_list(
            first_present(
                guard.get("batch_comparison_blocker_reasons"),
                handoff_summary.get("batch_comparison_blocker_reasons"),
            )
        ),
    }


def _handoff_value(handoff: dict[str, Any], key: str) -> Any:
    handoff_summary = _dict(handoff.get("summary"))
    decision_summary = _dict(handoff.get("decision_summary"))
    return first_present(handoff_summary.get(key), decision_summary.get(key))


def _reason_detail(value: Any) -> str:
    counts = _int_mapping(value)
    return ", ".join(f"{reason}:{count}" for reason, count in counts.items())


def _artifact_exists(rows: list[dict[str, Any]], key: str) -> bool:
    return any(row.get("key") == key and bool(row.get("exists")) for row in rows)


def _resolve_path(value: Any, project_root: Path, handoff_dir: Path) -> Path:
    if value is None:
        return project_root
    path = Path(str(value))
    if path.is_absolute():
        return path
    candidates = [project_root / path, handoff_dir / path, Path.cwd() / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def _option_value(command: list[str], option: str) -> str | None:
    for index, part in enumerate(command):
        if part == option and index + 1 < len(command):
            return command[index + 1]
    return None


def _nested(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
