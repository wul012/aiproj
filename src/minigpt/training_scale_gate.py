from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    display_command as _display_command,
    list_of_dicts as _list_of_dicts,
    utc_now,
)
from minigpt.training_scale_gate_artifacts import (
    render_training_scale_gate_html,
    render_training_scale_gate_markdown,
    write_training_scale_gate_csv,
    write_training_scale_gate_html,
    write_training_scale_gate_json,
    write_training_scale_gate_markdown,
    write_training_scale_gate_outputs,
)


POLICY_PROFILES: dict[str, dict[str, Any]] = {
    "review": {
        "min_char_count": 200,
        "small_corpus_status": "warn",
        "tiny_status": "warn",
        "max_warning_count": 5,
        "quality_warning_status": "warn",
        "min_variant_count": 1,
        "max_variant_count": 4,
        "max_token_budget": 2_000_000,
        "max_corpus_pass_estimate": 500.0,
        "budget_status": "warn",
        "corpus_pass_status": "warn",
    },
    "standard": {
        "min_char_count": 2_000,
        "small_corpus_status": "fail",
        "tiny_status": "fail",
        "max_warning_count": 0,
        "quality_warning_status": "fail",
        "min_variant_count": 1,
        "max_variant_count": 4,
        "max_token_budget": 2_000_000,
        "max_corpus_pass_estimate": 150.0,
        "budget_status": "fail",
        "corpus_pass_status": "warn",
    },
    "strict": {
        "min_char_count": 20_000,
        "small_corpus_status": "fail",
        "tiny_status": "fail",
        "max_warning_count": 0,
        "quality_warning_status": "fail",
        "min_variant_count": 2,
        "max_variant_count": 3,
        "max_token_budget": 5_000_000,
        "max_corpus_pass_estimate": 50.0,
        "budget_status": "fail",
        "corpus_pass_status": "fail",
    },
}


def load_training_scale_plan(path: str | Path) -> dict[str, Any]:
    return _dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def build_training_scale_gate(
    plan: dict[str, Any],
    *,
    plan_path: str | Path | None = None,
    profile: str = "review",
    policy_overrides: dict[str, Any] | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT training scale gate",
) -> dict[str, Any]:
    policy = _policy(profile, policy_overrides)
    checks = _build_checks(plan, policy)
    summary = _status_summary(checks)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "profile": profile,
        "policy": policy,
        "plan_path": None if plan_path is None else str(plan_path),
        "plan_summary": _plan_summary(plan),
        "overall_status": summary["overall_status"],
        "pass_count": summary["pass_count"],
        "warn_count": summary["warn_count"],
        "fail_count": summary["fail_count"],
        "checks": checks,
        "batch": _dict(plan.get("batch")),
        "recommendations": _recommendations(summary["overall_status"], checks, plan),
    }


def _policy(profile: str, overrides: dict[str, Any] | None) -> dict[str, Any]:
    if profile not in POLICY_PROFILES:
        choices = ", ".join(sorted(POLICY_PROFILES))
        raise ValueError(f"unknown profile {profile!r}; choose one of: {choices}")
    policy = dict(POLICY_PROFILES[profile])
    policy.update(dict(overrides or {}))
    policy["profile"] = profile
    return policy


def _build_checks(plan: dict[str, Any], policy: dict[str, Any]) -> list[dict[str, Any]]:
    dataset = _dict(plan.get("dataset"))
    batch = _dict(plan.get("batch"))
    variants = _list_of_dicts(plan.get("variants"))
    matrix = _list_of_dicts(plan.get("variant_matrix"))
    char_count = _int(dataset.get("char_count"))
    warning_count = _int(dataset.get("warning_count"))
    scale_tier = str(dataset.get("scale_tier") or "unknown")
    baseline = str(batch.get("baseline") or "")
    variant_names = {str(item.get("name") or "") for item in variants}
    checks = [
        _check(
            "plan_schema",
            "pass" if int(plan.get("schema_version") or 0) >= 1 and dataset else "fail",
            "Plan has a supported schema and dataset block.",
            "Regenerate the v70 training scale plan before running the batch.",
            {"schema_version": plan.get("schema_version"), "has_dataset": bool(dataset)},
        ),
        _check(
            "source_count",
            "pass" if _int(dataset.get("source_count")) > 0 else "fail",
            f"Plan references {_int(dataset.get('source_count'))} source files.",
            "Provide at least one .txt source file or directory.",
            {"source_count": dataset.get("source_count")},
        ),
        _check(
            "dataset_fingerprint",
            "pass" if dataset.get("fingerprint") else "warn",
            "Dataset fingerprint is present.",
            "Regenerate the scale plan with dataset preparation metadata.",
            {"fingerprint": dataset.get("fingerprint")},
        ),
        _check(
            "min_char_count",
            "pass" if char_count >= int(policy["min_char_count"]) else str(policy["small_corpus_status"]),
            f"Corpus has {char_count} characters; policy minimum is {policy['min_char_count']}.",
            "Collect more training text before treating results as model capability evidence.",
            {"char_count": char_count, "min_char_count": policy["min_char_count"]},
        ),
        _check(
            "tiny_corpus",
            str(policy["tiny_status"]) if scale_tier == "tiny" else "pass",
            f"Scale tier is {scale_tier}.",
            "Use tiny-corpus runs only as pipeline smoke evidence.",
            {"scale_tier": scale_tier},
        ),
        _check(
            "quality_warnings",
            "pass" if warning_count <= int(policy["max_warning_count"]) else str(policy["quality_warning_status"]),
            f"Dataset has {warning_count} quality warnings; policy maximum is {policy['max_warning_count']}.",
            "Review data quality issues before executing longer variants.",
            {"warning_count": warning_count, "max_warning_count": policy["max_warning_count"]},
        ),
        _check(
            "variant_count",
            _variant_count_status(len(variants), policy),
            f"Plan has {len(variants)} variants; policy range is {policy['min_variant_count']}..{policy['max_variant_count']}.",
            "Keep the matrix small enough to review and large enough to compare.",
            {"variant_count": len(variants), "min": policy["min_variant_count"], "max": policy["max_variant_count"]},
        ),
        _check(
            "baseline_variant",
            "pass" if baseline and baseline in variant_names else "fail",
            f"Baseline variant is {baseline or '<missing>'}.",
            "Set batch.baseline to one of the planned variant names.",
            {"baseline": baseline, "variant_names": sorted(variant_names)},
        ),
        _check(
            "batch_handoff",
            "pass" if batch.get("variants_path") and batch.get("command") else "fail",
            "Batch handoff path and command are present.",
            "Regenerate the scale plan so it includes variants_path and batch command.",
            {"variants_path": batch.get("variants_path"), "has_command": bool(batch.get("command"))},
        ),
        _check(
            "variant_dataset_versions",
            "pass" if variants and all(item.get("dataset_version") for item in variants) else "fail",
            "Every variant has a dataset_version.",
            "Give each variant a stable dataset_version before executing the batch.",
            {"missing": [item.get("name") for item in variants if not item.get("dataset_version")]},
        ),
        _budget_check(matrix, policy),
        _corpus_pass_check(matrix, policy),
    ]
    return checks


def _budget_check(matrix: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    max_row = _max_row(matrix, "token_budget")
    value = _float(max_row.get("token_budget")) if max_row else 0.0
    status = "pass" if max_row and value <= float(policy["max_token_budget"]) else str(policy["budget_status"])
    return _check(
        "token_budget",
        status,
        f"Largest token budget is {int(value)}; policy maximum is {policy['max_token_budget']}.",
        "Reduce max_iters, batch_size, or block_size before executing expensive variants.",
        {"variant": max_row.get("name") if max_row else None, "token_budget": value, "max_token_budget": policy["max_token_budget"]},
    )


def _corpus_pass_check(matrix: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    max_row = _max_row(matrix, "corpus_pass_estimate")
    value = _float(max_row.get("corpus_pass_estimate")) if max_row else 0.0
    status = "pass" if max_row and value <= float(policy["max_corpus_pass_estimate"]) else str(policy["corpus_pass_status"])
    return _check(
        "corpus_pass_estimate",
        status,
        f"Largest estimated corpus passes is {value}; policy maximum is {policy['max_corpus_pass_estimate']}.",
        "For tiny corpora, lower iterations or gather more data before trusting loss improvements.",
        {
            "variant": max_row.get("name") if max_row else None,
            "corpus_pass_estimate": value,
            "max_corpus_pass_estimate": policy["max_corpus_pass_estimate"],
        },
    )


def _check(code: str, status: str, message: str, recommendation: str, details: dict[str, Any]) -> dict[str, Any]:
    if status not in {"pass", "warn", "fail"}:
        raise ValueError(f"invalid check status: {status}")
    return {
        "code": code,
        "status": status,
        "message": message,
        "recommendation": recommendation,
        "details": details,
    }


def _status_summary(checks: list[dict[str, Any]]) -> dict[str, Any]:
    fail_count = sum(1 for check in checks if check.get("status") == "fail")
    warn_count = sum(1 for check in checks if check.get("status") == "warn")
    pass_count = sum(1 for check in checks if check.get("status") == "pass")
    if fail_count:
        overall = "fail"
    elif warn_count:
        overall = "warn"
    else:
        overall = "pass"
    return {
        "overall_status": overall,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "pass_count": pass_count,
    }


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    dataset = _dict(plan.get("dataset"))
    return {
        "dataset_name": dataset.get("name"),
        "version_prefix": dataset.get("version_prefix"),
        "scale_tier": dataset.get("scale_tier"),
        "char_count": dataset.get("char_count"),
        "source_count": dataset.get("source_count"),
        "warning_count": dataset.get("warning_count"),
        "quality_status": dataset.get("quality_status"),
        "variant_count": len(_list_of_dicts(plan.get("variants"))),
        "baseline": _dict(plan.get("batch")).get("baseline"),
    }


def _recommendations(status: str, checks: list[dict[str, Any]], plan: dict[str, Any]) -> list[str]:
    if status == "pass":
        recommendations = ["The scale plan is ready to hand to the training portfolio batch runner."]
    elif status == "warn":
        recommendations = ["The scale plan can be used for smoke or review runs, but warnings should be read first."]
    else:
        recommendations = ["Do not execute the planned batch until failed checks are fixed or a looser profile is selected."]
    for check in checks:
        if check.get("status") in {"warn", "fail"}:
            recommendations.append(f"{check.get('code')}: {check.get('recommendation')}")
    command = _dict(plan.get("batch")).get("command")
    if command:
        recommendations.append(f"Batch command: {_display_command(command)}")
    return recommendations


def _variant_count_status(count: int, policy: dict[str, Any]) -> str:
    if count < int(policy["min_variant_count"]):
        return "fail"
    if count > int(policy["max_variant_count"]):
        return "warn"
    return "pass"


def _max_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    if not rows:
        return {}
    return max(rows, key=lambda row: _float(row.get(key)))


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
