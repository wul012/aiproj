from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.curriculum_patch_shape_diag import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME = "bounded_objective_curriculum_patch_profile_sweep.json"
CURRICULUM_PATCH_PROFILE_SWEEP_CSV_FILENAME = "bounded_objective_curriculum_patch_profile_sweep.csv"
CURRICULUM_PATCH_PROFILE_SWEEP_TEXT_FILENAME = "bounded_objective_curriculum_patch_profile_sweep.txt"
CURRICULUM_PATCH_PROFILE_SWEEP_MARKDOWN_FILENAME = "bounded_objective_curriculum_patch_profile_sweep.md"
CURRICULUM_PATCH_PROFILE_SWEEP_HTML_FILENAME = "bounded_objective_curriculum_patch_profile_sweep.html"

ProfileRunner = Callable[[dict[str, Any], dict[str, Any], str | Path, str | Path, str], dict[str, Any]]

DEFAULT_PROFILES: tuple[dict[str, Any], ...] = (
    {"profile_id": "v857-baseline", "max_new_tokens": 8, "temperature": 0.2, "top_k": 20, "seed": 1839},
    {"profile_id": "top1-low-temp", "max_new_tokens": 8, "temperature": 0.05, "top_k": 1, "seed": 1839},
    {"profile_id": "top3-low-temp", "max_new_tokens": 10, "temperature": 0.1, "top_k": 3, "seed": 1840},
    {"profile_id": "longer-top20", "max_new_tokens": 12, "temperature": 0.15, "top_k": 20, "seed": 1841},
    {"profile_id": "longer-open", "max_new_tokens": 12, "temperature": 0.2, "top_k": None, "seed": 1842},
)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def locate_objective_contract(path: str | Path) -> Path:
    return _locate(path, BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME)


def locate_curriculum_patch_training_run(path: str | Path) -> Path:
    return _locate(path, BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TRAINING_RUN_JSON_FILENAME)


def locate_shape_migration_diagnostic(path: str | Path) -> Path:
    return _locate(path, BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_SHAPE_MIGRATION_DIAGNOSTIC_JSON_FILENAME)


def build_bounded_objective_curriculum_patch_profile_sweep(
    objective_contract_report: dict[str, Any],
    training_run_report: dict[str, Any],
    shape_migration_diagnostic_report: dict[str, Any],
    *,
    profiles: list[dict[str, Any]] | None = None,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    objective_contract_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    shape_migration_diagnostic_path: str | Path | None = None,
    profile_runner: ProfileRunner | None = None,
    title: str = "MiniGPT bounded objective curriculum patch profile sweep",
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract_summary = as_dict(objective_contract_report.get("summary"))
    training_summary = as_dict(training_run_report.get("summary"))
    diagnostic_summary = as_dict(shape_migration_diagnostic_report.get("summary"))
    cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    selected_profiles = [dict(profile) for profile in (profiles or list(DEFAULT_PROFILES))]
    checkpoint = _resolve_checkpoint(training_run_report, checkpoint_path)
    tokenizer = _resolve_tokenizer(training_run_report, tokenizer_path, checkpoint)
    sweep_rows, sweep_errors = _run_profile_sweep(cases, selected_profiles, checkpoint, tokenizer, device, profile_runner or _generate_profile_case)
    profile_summaries = _profile_summaries(selected_profiles, sweep_rows)
    checks = _checks(objective_contract_report, contract_summary, training_run_report, training_summary, shape_migration_diagnostic_report, diagnostic_summary, cases, selected_profiles, checkpoint, tokenizer, sweep_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, cases, selected_profiles, sweep_rows, profile_summaries)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_objective_contract": str(objective_contract_path or ""),
        "source_training_run": str(training_run_path or ""),
        "source_shape_migration_diagnostic": str(shape_migration_diagnostic_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "profiles": selected_profiles,
        "contract_summary": contract_summary,
        "training_summary": training_summary,
        "shape_migration_summary": diagnostic_summary,
        "sweep_rows": sweep_rows,
        "sweep_errors": sweep_errors,
        "profile_summaries": profile_summaries,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_sweep_ready: bool, require_any_profile_recovered: bool = False) -> int:
    summary = as_dict(report.get("summary"))
    if require_sweep_ready and report.get("status") != "pass":
        return 1
    if require_any_profile_recovered and summary.get("any_profile_recovered") is not True:
        return 1
    return 0


def _run_profile_sweep(
    cases: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: ProfileRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for profile in profiles:
        for case in cases:
            try:
                generation = runner(case, profile, checkpoint, tokenizer, device)
                rows.append(_sweep_row(case, profile, generation))
            except Exception as exc:  # pragma: no cover - defensive report path
                errors.append({"profile_id": profile.get("profile_id"), "case_id": case.get("case_id"), "error": str(exc)})
    return rows, errors


def _generate_profile_case(case: dict[str, Any], profile: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(case.get("prompt") or ""),
        max_new_tokens=int(profile.get("max_new_tokens") or 8),
        temperature=float(profile.get("temperature") or 0.2),
        top_k=None if profile.get("top_k") in {None, "", 0, "0"} else int(profile.get("top_k")),
        seed=None if profile.get("seed") in {None, ""} else int(profile.get("seed")),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _sweep_row(case: dict[str, Any], profile: dict[str, Any], generation: dict[str, Any]) -> dict[str, Any]:
    required_terms = _terms(case.get("required_terms"))
    generated = str(generation.get("generated") or "")
    continuation = str(generation.get("continuation") or generated)
    lowered = continuation.lower()
    hit_terms = [term for term in required_terms if term in lowered]
    missed_terms = [term for term in required_terms if term not in hit_terms]
    return {
        "profile_id": str(profile.get("profile_id") or ""),
        "case_id": str(case.get("case_id") or ""),
        "prompt": str(case.get("prompt") or ""),
        "continuation": continuation,
        "generated": generated,
        "required_terms": required_terms,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "case_pass": not missed_terms,
        "any_hit": bool(hit_terms),
        "loss_hit": "loss" in hit_terms,
        "fixed_hit": "fixed" in hit_terms,
        "max_new_tokens": int(profile.get("max_new_tokens") or 8),
        "temperature": float(profile.get("temperature") or 0.2),
        "top_k": profile.get("top_k"),
        "seed": profile.get("seed"),
    }


def _profile_summaries(profiles: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile.get("profile_id") or "")
        profile_rows = [row for row in rows if row["profile_id"] == profile_id]
        passed = sum(1 for row in profile_rows if row["case_pass"])
        any_hit = sum(1 for row in profile_rows if row["any_hit"])
        zero_hit = sum(1 for row in profile_rows if not row["any_hit"])
        loss_hit = sum(1 for row in profile_rows if row["loss_hit"])
        summaries.append(
            {
                "profile_id": profile_id,
                "case_count": len(profile_rows),
                "passed_case_count": passed,
                "any_hit_case_count": any_hit,
                "zero_hit_case_count": zero_hit,
                "loss_hit_case_count": loss_hit,
                "fixed_hit_case_count": sum(1 for row in profile_rows if row["fixed_hit"]),
                "pass_rate": round(passed / len(profile_rows), 6) if profile_rows else 0.0,
                "objective_contract_recovered": bool(profile_rows) and passed == len(profile_rows),
            }
        )
    return summaries


def _checks(
    contract: dict[str, Any],
    contract_summary: dict[str, Any],
    training: dict[str, Any],
    training_summary: dict[str, Any],
    diagnostic: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    cases: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("contract_passed", contract.get("status") == "pass", contract.get("status"), "objective contract must pass"),
        _check("contract_ready", contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "objective contract must be ready"),
        _check("training_passed", training.get("status") == "pass", training.get("status"), "curriculum patch training run must pass"),
        _check(
            "training_ready",
            training_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready") is True,
            training_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready"),
            "curriculum patch training run must be ready",
        ),
        _check("shape_diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "shape migration diagnostic must pass"),
        _check(
            "shape_diagnostic_ready",
            diagnostic_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_unassisted_repair_seed_revision_curriculum_patch_shape_migration_diagnostic_ready"),
            "shape migration diagnostic must be ready",
        ),
        _check("cases_present", bool(cases), len(cases), "objective contract must provide replay cases"),
        _check("profiles_present", bool(profiles), len(profiles), "profile sweep must include at least one profile"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("no_sweep_errors", not errors, len(errors), "all profile/case generations should complete"),
    ]


def _summary(status: str, cases: list[dict[str, Any]], profiles: list[dict[str, Any]], rows: list[dict[str, Any]], profile_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    best = _best_profile(profile_summaries)
    any_recovered = any(row.get("objective_contract_recovered") for row in profile_summaries)
    return {
        "bounded_objective_curriculum_patch_profile_sweep_ready": status == "pass",
        "case_count": len(cases),
        "profile_count": len(profiles),
        "sweep_row_count": len(rows),
        "any_profile_recovered": any_recovered,
        "profile_with_loss_hit_count": sum(1 for row in profile_summaries if int(row.get("loss_hit_case_count") or 0) > 0),
        "max_passed_case_count": max([int(row.get("passed_case_count") or 0) for row in profile_summaries] or [0]),
        "max_any_hit_case_count": max([int(row.get("any_hit_case_count") or 0) for row in profile_summaries] or [0]),
        "max_loss_hit_case_count": max([int(row.get("loss_hit_case_count") or 0) for row in profile_summaries] or [0]),
        "best_profile_id": best.get("profile_id"),
        "best_profile_loss_hit_case_count": best.get("loss_hit_case_count"),
        "best_profile_any_hit_case_count": best.get("any_hit_case_count"),
        "model_quality_claim": "decode_profile_sweep_only",
        "next_action": _next_action(any_recovered, int(best.get("loss_hit_case_count") or 0), int(best.get("any_hit_case_count") or 0)),
    }


def _best_profile(profile_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not profile_summaries:
        return {}
    return max(
        profile_summaries,
        key=lambda row: (
            int(row.get("passed_case_count") or 0),
            int(row.get("loss_hit_case_count") or 0),
            int(row.get("any_hit_case_count") or 0),
            -int(row.get("zero_hit_case_count") or 0),
            str(row.get("profile_id") or ""),
        ),
    )


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "bounded_objective_curriculum_patch_profile_sweep_blocked"
    if summary.get("any_profile_recovered") is True:
        return "bounded_objective_curriculum_patch_profile_sweep_contract_recovered_holdout_required"
    if int(summary.get("max_loss_hit_case_count") or 0) > 0:
        return "bounded_objective_curriculum_patch_profile_sweep_found_loss_signal_bridge_required"
    if int(summary.get("max_any_hit_case_count") or 0) > 0:
        return "bounded_objective_curriculum_patch_profile_sweep_confirms_fixed_only_boundary"
    return "bounded_objective_curriculum_patch_profile_sweep_zero_hit"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The profile sweep could not run structurally."
    elif summary.get("any_profile_recovered") is True:
        reason = "At least one decoding profile recovered all bounded objective cases; holdout replay is required before any promotion."
    elif int(summary.get("max_loss_hit_case_count") or 0) > 0:
        reason = "At least one profile produced `loss`, but no profile recovered the full bounded objective contract."
    elif int(summary.get("max_any_hit_case_count") or 0) > 0:
        reason = "Profiles still find only partial required-term signal; `loss` remains outside stable decoding."
    else:
        reason = "No profile produced a required-term hit."
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": reason,
        "next_action": summary.get("next_action"),
    }


def _next_action(recovered: bool, loss_hits: int, any_hits: int) -> str:
    if recovered:
        return "run_bounded_objective_curriculum_patch_holdout_replay"
    if loss_hits > 0:
        return "build_loss_signal_bridge_without_promotion"
    if any_hits > 0:
        return "revise_curriculum_patch_for_loss_uptake_or_return_to_seed_design"
    return "diagnose_curriculum_patch_zero_hit_profiles"


def _resolve_checkpoint(report: dict[str, Any], explicit: str | Path | None) -> Path:
    if explicit is not None:
        return Path(explicit)
    run_dir = Path(str(report.get("run_dir") or ""))
    return run_dir / "checkpoint.pt"


def _resolve_tokenizer(report: dict[str, Any], explicit: str | Path | None, checkpoint: Path) -> Path:
    if explicit is not None:
        return Path(explicit)
    run_dir = Path(str(report.get("run_dir") or ""))
    if run_dir:
        return run_dir / "tokenizer.json"
    return checkpoint.with_name("tokenizer.json")


def _locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {source}")


def _terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(term).lower() for term in value]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


__all__ = [
    "CURRICULUM_PATCH_PROFILE_SWEEP_CSV_FILENAME",
    "CURRICULUM_PATCH_PROFILE_SWEEP_HTML_FILENAME",
    "CURRICULUM_PATCH_PROFILE_SWEEP_JSON_FILENAME",
    "CURRICULUM_PATCH_PROFILE_SWEEP_MARKDOWN_FILENAME",
    "CURRICULUM_PATCH_PROFILE_SWEEP_TEXT_FILENAME",
    "DEFAULT_PROFILES",
    "build_bounded_objective_curriculum_patch_profile_sweep",
    "locate_curriculum_patch_training_run",
    "locate_objective_contract",
    "locate_shape_migration_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
