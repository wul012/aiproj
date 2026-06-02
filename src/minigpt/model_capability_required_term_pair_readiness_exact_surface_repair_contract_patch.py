from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_exact_surface_repair_plan import (
    PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch import (
    FIXED_PRESERVING_TRANSFER_ROWS,
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_JSON_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.json"
PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_CSV_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.csv"
PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_TEXT_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.txt"
PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.md"
PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_HTML_FILENAME = "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.html"


EXACT_SURFACE_REPAIR_ROWS = [
    "exact_surface_bridge pipe equals tokens map fixed and loss => fixed loss",
    "exact_surface_bridge fixed equals pipe loss equals expects fixed loss",
    "exact_surface_bridge compact pipe structure keeps fixed before loss",
    "exact_surface_bridge no space pipe joins fixed token and loss token",
]


def locate_exact_surface_repair_contract_patch_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_EXACT_SURFACE_REPAIR_PLAN_JSON_FILENAME
    return source


def locate_exact_surface_repair_contract_patch_base(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("exact-surface repair contract patch input must be a JSON object")
    return dict(payload)


def build_exact_surface_repair_contract_patch(
    *,
    repair_plan: dict[str, Any],
    base_contract_report: dict[str, Any],
    repair_plan_path: str | Path | None = None,
    base_contract_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_contract = as_dict(base_contract_report.get("contract"))
    patched_contract = _patched_contract(base_contract)
    checks = _checks(repair_plan, base_contract_report, patched_contract)
    failed = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness exact-surface repair contract patch",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_repair_plan_path": str(repair_plan_path or ""),
        "source_base_contract_path": str(base_contract_path or ""),
        "source_repair_plan": {
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
            "added_rows": EXACT_SURFACE_REPAIR_ROWS,
            "added_row_count": len(EXACT_SURFACE_REPAIR_ROWS),
            "patch_focus": "near-exact pipe/equals surface bridge without training on the heldout exact prompt",
        },
        "check_rows": checks,
        "summary": _summary(base_contract, patched_contract, checks),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _patched_contract(base_contract: dict[str, Any]) -> dict[str, Any]:
    training_rows = [str(row) for row in base_contract.get("training_rows", [])]
    return {
        **base_contract,
        "contract_version": 10,
        "training_rows": training_rows + EXACT_SURFACE_REPAIR_ROWS,
        "patch_kind": "exact_surface_repair",
        "patch_note": "adds four near-exact pipe/equals surface bridge rows while keeping the exact heldout prompt absent",
    }


def _checks(repair_plan: dict[str, Any], base_contract_report: dict[str, Any], patched_contract: dict[str, Any]) -> list[dict[str, Any]]:
    plan = as_dict(repair_plan.get("plan"))
    training_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    probe_prompts = [str(row.get("prompt")) for row in list_of_dicts(patched_contract.get("evaluation_probes"))]
    row_budget = int(plan.get("repair_row_budget") or 0)
    return [
        _check("repair_plan_passed", repair_plan.get("status") == "pass", repair_plan.get("status"), "exact-surface repair plan must pass"),
        _check(
            "repair_plan_decision",
            repair_plan.get("decision") == "pair_readiness_exact_surface_repair_plan_ready",
            repair_plan.get("decision"),
            "patch follows only a ready exact-surface repair plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_exact_surface_repair_contract_patch",
            plan.get("proposed_next_artifact"),
            "plan must request this patch artifact",
        ),
        _check("base_contract_passed", base_contract_report.get("status") == "pass", base_contract_report.get("status"), "base fixed-preserving contract must pass"),
        _check(
            "base_contract_decision",
            base_contract_report.get("decision") == "pair_readiness_fixed_preserving_transfer_contract_patch_ready",
            base_contract_report.get("decision"),
            "base must be the fixed-preserving transfer contract patch",
        ),
        _check("exact_surface_rows_added", all(row in training_rows for row in EXACT_SURFACE_REPAIR_ROWS), "all exact-surface rows", "all exact-surface repair rows must be present"),
        _check("repair_row_budget_respected", 0 < len(EXACT_SURFACE_REPAIR_ROWS) <= row_budget, len(EXACT_SURFACE_REPAIR_ROWS), "patch must respect plan row budget"),
        _check("fixed_preserving_rows_preserved", all(row in training_rows for row in FIXED_PRESERVING_TRANSFER_ROWS), "all fixed-preserving rows", "patch must preserve fixed-preserving transfer rows"),
        _check("exact_direct_rows_preserved", {"fixed=fixed", "loss=loss"}.issubset(set(training_rows)), sorted({"fixed=fixed", "loss=loss"} & set(training_rows)), "direct completion rows must be preserved"),
        _check("heldout_pair_absent", HELDOUT_PAIR_PROBE not in training_rows, HELDOUT_PAIR_PROBE in training_rows, "heldout pair prompt must stay out of all training rows"),
        _check("heldout_pair_absent_from_patch", HELDOUT_PAIR_PROBE not in EXACT_SURFACE_REPAIR_ROWS, HELDOUT_PAIR_PROBE in EXACT_SURFACE_REPAIR_ROWS, "patch rows must not train on exact heldout pair prompt"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(base_contract: dict[str, Any], patched_contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    base_rows = [str(row) for row in base_contract.get("training_rows", [])]
    patched_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    return {
        "patch_ready": all(row["status"] == "pass" for row in checks),
        "base_training_row_count": len(base_rows),
        "patched_training_row_count": len(patched_rows),
        "added_training_row_count": len(patched_rows) - len(base_rows),
        "exact_surface_repair_row_count": len(EXACT_SURFACE_REPAIR_ROWS),
        "fixed_preserving_transfer_row_count": len(FIXED_PRESERVING_TRANSFER_ROWS),
        "evaluation_probe_count": len(patched_contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_exact_surface_repair_contract_patch_ready"
    return "fix_pair_readiness_exact_surface_repair_contract_patch"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The exact-surface repair patch failed plan, base-contract, budget, or leakage checks.",
            "next_action": "repair exact-surface contract patch before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_patch_only",
        "reason": "The patched contract adds near-exact pipe/equals bridge rows while keeping the exact heldout prompt absent.",
        "next_action": "materialize the exact-surface repair contract and rerun training plus independent replay",
    }


__all__ = [
    "EXACT_SURFACE_REPAIR_ROWS",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_CSV_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_HTML_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_JSON_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_MARKDOWN_FILENAME",
    "PAIR_READINESS_EXACT_SURFACE_REPAIR_CONTRACT_PATCH_TEXT_FILENAME",
    "build_exact_surface_repair_contract_patch",
    "locate_exact_surface_repair_contract_patch_base",
    "locate_exact_surface_repair_contract_patch_plan",
    "read_json_report",
    "resolve_exit_code",
]
