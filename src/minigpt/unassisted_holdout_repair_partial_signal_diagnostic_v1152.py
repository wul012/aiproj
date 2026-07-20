from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now
from minigpt.unassisted_holdout_repair_plan_v1148 import EXPLAIN_DIR_NAME
from minigpt.unassisted_holdout_repair_replay_comparison_v1151 import (
    UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM,
)
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (
    UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
)
from minigpt.report_check_common import check_entry as _check


UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM = (
    "unassisted_holdout_repair_partial_signal_diagnostic_v1152"
)


def default_v1151_replay_comparison_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1151"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-replay-comparison-v1151"
        / f"{UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM}.json"
    )


def default_v1149_seed_corpus_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1149"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-seed-corpus-v1149"
        / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
    )


def locate_v1151_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM}.json"
    return source


def locate_v1149_seed_corpus(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
    return source


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def build_unassisted_holdout_repair_partial_signal_diagnostic_v1152(
    replay_report: dict[str, Any],
    seed_report: dict[str, Any],
    *,
    replay_path: str | Path | None = None,
    seed_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_report.get("summary"))
    seed_summary = as_dict(seed_report.get("summary"))
    replay_rows = list_of_dicts(replay_report.get("rows"))
    seed_rows = list_of_dicts(seed_report.get("rows"))
    profile = _seed_profile(seed_rows)
    replay_profile = _replay_profile(replay_rows, replay_summary)
    checks = _checks(replay_report, replay_summary, seed_report, seed_summary, replay_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    findings = _findings(status, replay_profile, profile, replay_rows)
    diagnosis = _diagnosis(status, replay_profile, profile, findings)
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted holdout repair partial signal diagnostic v1152",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, replay_profile),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_path or ""),
        "source_seed_corpus": str(seed_path or ""),
        "rows": findings,
        "check_rows": checks,
        "replay_profile": replay_profile,
        "seed_profile": profile,
        "diagnosis": diagnosis,
        "summary": _summary(status, checks, replay_profile, profile, diagnosis),
        "interpretation": _interpretation(status, diagnosis),
        "csv_fieldnames": [
            "finding_id",
            "severity",
            "status",
            "actual",
            "inference",
            "recommended_action",
        ],
    }


def write_unassisted_holdout_repair_partial_signal_diagnostic_v1152_outputs(
    report: dict[str, Any], out_dir: str | Path
) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM,
        row_title="Diagnostic Findings",
    )


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool = False) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _checks(
    replay_report: dict[str, Any],
    replay_summary: dict[str, Any],
    seed_report: dict[str, Any],
    seed_summary: dict[str, Any],
    replay_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("v1151_replay_passed", replay_report.get("status") == "pass", replay_report.get("status"), "v1151 replay comparison must be structurally valid"),
        _check("v1151_replay_ready", replay_summary.get("unassisted_holdout_repair_replay_ready") is True, replay_summary.get("unassisted_holdout_repair_replay_ready"), "v1151 must have completed replay generation"),
        _check("v1151_next_step_matches_diagnostic", replay_summary.get("next_step") == "diagnose_unassisted_holdout_repair_partial_signal", replay_summary.get("next_step"), "v1151 partial signal should point to this diagnostic"),
        _check("v1149_seed_corpus_passed", seed_report.get("status") == "pass", seed_report.get("status"), "v1149 seed corpus must be structurally valid"),
        _check("v1149_seed_corpus_ready", seed_summary.get("unassisted_holdout_repair_seed_corpus_ready") is True, seed_summary.get("unassisted_holdout_repair_seed_corpus_ready"), "v1149 seed corpus ready flag must be true"),
        _check("replay_rows_present", len(replay_rows) > 0, len(replay_rows), "diagnostic needs replay generation rows"),
        _check("promotion_boundary_kept", replay_summary.get("promotion_ready") is False and seed_summary.get("promotion_ready") is False, {"replay": replay_summary.get("promotion_ready"), "seed": seed_summary.get("promotion_ready")}, "diagnostic is evidence, not automatic promotion"),
    ]


def _seed_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_free_pair = []
    loss_after_fixed = []
    fixed_first = []
    prompt_counts: dict[str, int] = {}
    for row in rows:
        prompt = str(row.get("prompt") or "")
        prompt_counts[prompt] = prompt_counts.get(prompt, 0) + 1
        target_terms = [str(term).lower() for term in row.get("target_terms", [])]
        completion = str(row.get("completion") or "").lower()
        training_only = row.get("training_only_context") is True
        if "fixed" in target_terms and "loss" in target_terms and not training_only:
            target_free_pair.append(row)
        if "loss" in completion and (training_only or str(row.get("kind") or "") == "loss_after_model_fixed"):
            loss_after_fixed.append(row)
        if target_terms == ["fixed"] or (target_terms == ["fixed"] and "loss" not in completion):
            fixed_first.append(row)
    return {
        "example_count": len(rows),
        "target_free_pair_example_count": len(target_free_pair),
        "loss_after_fixed_training_context_count": len(loss_after_fixed),
        "fixed_first_example_count": len(fixed_first),
        "unique_prompt_count": len(prompt_counts),
        "repeated_prompt_count": sum(1 for count in prompt_counts.values() if count > 1),
        "loss_suffix_context_tied": len(loss_after_fixed) > 0,
    }


def _replay_profile(rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    case_count = int(summary.get("case_count") or len(rows) or 0)
    fixed_count = int(summary.get("fixed_hit_case_count") or sum(1 for row in rows if row.get("fixed_hit")))
    loss_count = int(summary.get("loss_hit_case_count") or sum(1 for row in rows if row.get("loss_hit")))
    full_pair_count = int(summary.get("full_pair_case_count") or sum(1 for row in rows if row.get("full_pair_hit")))
    zero_hit_rows = [row for row in rows if not row.get("fixed_hit") and not row.get("loss_hit")]
    fixed_only_rows = [row for row in rows if row.get("fixed_hit") and not row.get("loss_hit")]
    truncated_like_rows = [row for row in rows if not str(row.get("generated") or "").startswith(str(row.get("prompt") or ""))]
    return {
        "case_count": case_count,
        "fixed_hit_case_count": fixed_count,
        "loss_hit_case_count": loss_count,
        "full_pair_case_count": full_pair_count,
        "zero_hit_case_count": len(zero_hit_rows),
        "fixed_only_case_count": len(fixed_only_rows),
        "partial_signal_visible": fixed_count > 0 and full_pair_count < case_count,
        "loss_missing": case_count > 0 and loss_count == 0,
        "full_pair_missing": case_count > 0 and full_pair_count == 0,
        "zero_hit_case_ids": [str(row.get("case_id") or "") for row in zero_hit_rows],
        "fixed_only_case_ids": [str(row.get("case_id") or "") for row in fixed_only_rows],
        "context_window_drift_case_ids": [str(row.get("case_id") or "") for row in truncated_like_rows],
    }


def _findings(
    status: str,
    replay_profile: dict[str, Any],
    seed_profile: dict[str, Any],
    replay_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if status != "pass":
        return [
            _finding(
                "diagnostic_inputs_incomplete",
                "blocker",
                "blocked",
                "source checks failed",
                "cannot diagnose model behavior until replay and seed reports are structurally valid",
                "repair source reports, then rerun v1152 diagnostic",
            )
        ]
    rows = [
        _finding("fixed_signal_visible", "info", "observed", replay_profile.get("fixed_hit_case_count"), "v1151 generated `fixed` in target-free holdout continuations", "preserve fixed-oriented examples while repairing loss suffix"),
        _finding("loss_absent_in_all_replay_cases", "blocker", "requires_repair", replay_profile.get("loss_hit_case_count"), "v1151 did not generate `loss` in any holdout continuation", "add target-free loss-suffix reinforcement before another replay"),
        _finding("full_pair_absent", "blocker", "requires_repair", replay_profile.get("full_pair_case_count"), "`fixed loss` full-pair recovery is still zero", "do not promote; run a repair seed revision focused on loss after fixed"),
        _finding("zero_hit_prompt_cluster", "warn", "observed", replay_profile.get("zero_hit_case_ids"), "some prompts produce neither fixed nor loss", "keep prompt-level diagnostics in the next replay"),
        _finding("loss_suffix_context_tied", "warn", "observed", seed_profile.get("loss_after_fixed_training_context_count"), "loss-after-fixed evidence exists mainly as a training-only context where prompt already contains fixed", "create target-free prompts that require the model to continue from fixed to loss without prompt contamination"),
        _finding("fixed_first_bias", "warn", "observed", seed_profile.get("fixed_first_example_count"), "fixed-only examples likely help the first token but can leave loss undertrained", "rebalance corpus so fixed-first support does not stop at fixed"),
    ]
    if replay_profile.get("context_window_drift_case_ids"):
        rows.append(
            _finding(
                "context_window_drift_visible",
                "warn",
                "observed",
                replay_profile.get("context_window_drift_case_ids"),
                "at least one generated string no longer starts with the full prompt, suggesting tiny block-size truncation",
                "keep short and long prompts separate in the next replay report",
            )
        )
    rows.append(
        _finding(
            "next_repair_action",
            "action",
            "ready",
            "build_unassisted_loss_suffix_repair_seed",
            "the next version should alter evidence inputs, not reinterpret v1151 as success",
            "materialize a loss-suffix repair seed and rerun bounded CPU training/replay",
        )
    )
    return rows


def _diagnosis(
    status: str,
    replay_profile: dict[str, Any],
    seed_profile: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    if status != "pass":
        return {"ready": False, "root_cause_hypothesis": "source evidence invalid", "next_step": "repair_partial_signal_diagnostic_inputs"}
    loss_context_tied = seed_profile.get("loss_after_fixed_training_context_count", 0) > 0
    root_cause = "loss_suffix_underlearned_after_fixed"
    if loss_context_tied:
        root_cause = "loss_suffix_context_tied_and_underlearned_after_fixed"
    return {
        "ready": True,
        "root_cause_hypothesis": root_cause,
        "evidence_basis": [
            f"fixed hits {replay_profile.get('fixed_hit_case_count')}/{replay_profile.get('case_count')}",
            f"loss hits {replay_profile.get('loss_hit_case_count')}/{replay_profile.get('case_count')}",
            f"target-free pair examples {seed_profile.get('target_free_pair_example_count')}",
            f"loss-after-fixed training-only examples {seed_profile.get('loss_after_fixed_training_context_count')}",
        ],
        "blocking_findings": [row["finding_id"] for row in findings if row.get("severity") == "blocker"],
        "model_quality_claim": "partial_signal_diagnostic_only",
        "promotion_ready": False,
        "next_step": "build_unassisted_loss_suffix_repair_seed",
    }


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    replay_profile: dict[str, Any],
    seed_profile: dict[str, Any],
    diagnosis: dict[str, Any],
) -> dict[str, Any]:
    return {
        "unassisted_holdout_repair_partial_signal_diagnostic_ready": status == "pass" and diagnosis.get("ready") is True,
        "case_count": replay_profile.get("case_count"),
        "fixed_hit_case_count": replay_profile.get("fixed_hit_case_count"),
        "loss_hit_case_count": replay_profile.get("loss_hit_case_count"),
        "full_pair_case_count": replay_profile.get("full_pair_case_count"),
        "fixed_only_case_count": replay_profile.get("fixed_only_case_count"),
        "zero_hit_case_count": replay_profile.get("zero_hit_case_count"),
        "target_free_pair_example_count": seed_profile.get("target_free_pair_example_count"),
        "loss_after_fixed_training_context_count": seed_profile.get("loss_after_fixed_training_context_count"),
        "fixed_first_example_count": seed_profile.get("fixed_first_example_count"),
        "root_cause_hypothesis": diagnosis.get("root_cause_hypothesis"),
        "model_quality_claim": diagnosis.get("model_quality_claim", "not_claimed") if status == "pass" else "not_claimed",
        "promotion_ready": False,
        "next_step": diagnosis.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, replay_profile: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_unassisted_holdout_repair_partial_signal_diagnostic_inputs"
    if replay_profile.get("partial_signal_visible") and replay_profile.get("loss_missing"):
        return "unassisted_holdout_repair_partial_signal_diagnostic_ready"
    return "unassisted_holdout_repair_replay_not_partial_signal"


def _interpretation(status: str, diagnosis: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Source reports are incomplete.", "next_action": "repair diagnostic inputs"}
    return {
        "model_quality_claim": "partial_signal_diagnostic_only",
        "reason": "The real v1151 replay shows fixed-only partial signal, but loss and full-pair recovery are absent.",
        "next_action": diagnosis.get("next_step"),
    }


def _finding(
    finding_id: str,
    severity: str,
    status: str,
    actual: Any,
    inference: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "severity": severity,
        "status": status,
        "actual": actual,
        "inference": inference,
        "recommended_action": recommended_action,
    }


__all__ = [
    "UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM",
    "build_unassisted_holdout_repair_partial_signal_diagnostic_v1152",
    "default_v1149_seed_corpus_path",
    "default_v1151_replay_comparison_path",
    "locate_v1149_seed_corpus",
    "locate_v1151_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
    "write_unassisted_holdout_repair_partial_signal_diagnostic_v1152_outputs",
]
