from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_fixed_recovery_repair_plan import (
    PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_structured_template_contract import (
    PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_JSON_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.json"
PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_CSV_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.csv"
PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_TEXT_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.txt"
PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.md"
PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_HTML_FILENAME = "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.html"

FIXED_RECOVERY_ROWS = [
    "task: complete required term | prompt: fixed= | answer: fixed | recovery: fixed",
    "case=fixed-recovery | prompt=fixed= | expected=fixed | answer=fixed",
    "fixed direct answer confirmation -> fixed",
    "fixed prompt should complete fixed before loss",
    "fixed branch keeps fixed and rejects loss completion",
    "fixed recovery row preserves fixed token sequence",
    "when prompt begins fixed= the answer remains fixed",
    "required term fixed stays fixed while loss rows stay present",
]


def locate_fixed_recovery_contract_patch_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_RECOVERY_REPAIR_PLAN_JSON_FILENAME
    return source


def locate_fixed_recovery_contract_patch_base(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-recovery contract patch input must be a JSON object")
    return dict(payload)


def build_fixed_recovery_contract_patch(
    *,
    repair_plan: dict[str, Any],
    base_contract_report: dict[str, Any],
    plan_path: str | Path | None = None,
    base_contract_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_contract = as_dict(base_contract_report.get("contract"))
    patched_contract = _patched_contract(base_contract)
    checks = _checks(repair_plan, base_contract_report, patched_contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness fixed-recovery contract patch",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_plan_path": str(plan_path or ""),
        "source_base_contract_path": str(base_contract_path or ""),
        "source_plan": {
            "status": repair_plan.get("status"),
            "decision": repair_plan.get("decision"),
            "summary": as_dict(repair_plan.get("summary")),
        },
        "source_base_contract": {
            "status": base_contract_report.get("status"),
            "decision": base_contract_report.get("decision"),
            "summary": as_dict(base_contract_report.get("summary")),
        },
        "contract": patched_contract,
        "patch": {
            "added_rows": FIXED_RECOVERY_ROWS,
            "added_row_count": len(FIXED_RECOVERY_ROWS),
            "patch_focus": "fixed direct recovery without removing structured loss rows",
        },
        "check_rows": checks,
        "summary": _summary(base_contract, patched_contract, checks),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _patched_contract(base_contract: dict[str, Any]) -> dict[str, Any]:
    training_rows = [str(row) for row in base_contract.get("training_rows", [])]
    return {
        **base_contract,
        "contract_version": 4,
        "training_rows": training_rows + FIXED_RECOVERY_ROWS,
        "patch_kind": "fixed_recovery",
        "patch_note": "fixed-recovery rows are added after structured-template rows while preserving loss rows and heldout probes",
    }


def _checks(repair_plan: dict[str, Any], base_contract_report: dict[str, Any], patched_contract: dict[str, Any]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    heldout = str(patched_contract.get("heldout_pair_probe") or "")
    probes = list_of_dicts(patched_contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    return [
        _check("repair_plan_passed", repair_plan.get("status") == "pass", repair_plan.get("status"), "repair plan must pass"),
        _check(
            "repair_plan_decision",
            repair_plan.get("decision") == "pair_readiness_fixed_recovery_repair_plan_ready",
            repair_plan.get("decision"),
            "patch follows only a ready fixed-recovery repair plan",
        ),
        _check("base_contract_passed", base_contract_report.get("status") == "pass", base_contract_report.get("status"), "base structured-template contract must pass"),
        _check(
            "base_contract_decision",
            base_contract_report.get("decision") == "pair_readiness_structured_template_contract_ready",
            base_contract_report.get("decision"),
            "base must be the structured-template contract",
        ),
        _check("fixed_rows_added", all(row in training_rows for row in FIXED_RECOVERY_ROWS), "all fixed rows", "all fixed-recovery rows must be present"),
        _check("loss_rows_preserved", _contains_count(training_rows, "loss") >= 6, _contains_count(training_rows, "loss"), "loss structured rows must remain present"),
        _check("evaluation_probes_preserved", len(probes) == 3, len(probes), "fixed, loss, and pair probes must be preserved"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair probe must not be a training row"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _contains_count(rows: list[str], needle: str) -> int:
    return sum(1 for row in rows if needle in row)


def _summary(base_contract: dict[str, Any], patched_contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    base_rows = [str(row) for row in base_contract.get("training_rows", [])]
    patched_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    return {
        "base_training_row_count": len(base_rows),
        "patched_training_row_count": len(patched_rows),
        "added_training_row_count": len(patched_rows) - len(base_rows),
        "loss_row_count": _contains_count(patched_rows, "loss"),
        "evaluation_probe_count": len(patched_contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "patch_ready": all(row.get("status") == "pass" for row in checks),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_fixed_recovery_contract_patch_ready"
    return "fix_pair_readiness_fixed_recovery_contract_patch"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fixed-recovery contract patch failed checks.",
            "next_action": "repair patch before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_patch_only",
        "reason": "The structured-template contract now includes fixed-recovery rows while preserving loss rows and heldout probes.",
        "next_action": "materialize the fixed-recovery contract and rerun pair-readiness training",
    }


__all__ = [
    "FIXED_RECOVERY_ROWS",
    "PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_CSV_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_HTML_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_JSON_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_RECOVERY_CONTRACT_PATCH_TEXT_FILENAME",
    "build_fixed_recovery_contract_patch",
    "locate_fixed_recovery_contract_patch_base",
    "locate_fixed_recovery_contract_patch_plan",
    "read_json_report",
    "resolve_exit_code",
]
