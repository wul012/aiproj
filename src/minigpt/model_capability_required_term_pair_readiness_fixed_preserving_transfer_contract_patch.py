from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_direct_completion_surface_contract import (
    PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_fixed_preserving_transfer_plan import (
    PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.json"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.csv"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.txt"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.md"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.html"
)


FIXED_PRESERVING_TRANSFER_ROWS = [
    "fixed_preserving_transfer guard fixed before loss => fixed loss",
    "fixed_preserving_transfer compact fixed/loss keeps fixed => fixed loss",
    "fixed_preserving_transfer reverse loss then fixed keeps fixed => loss fixed",
    "fixed_preserving_transfer boundary fixed retained with loss",
]


def locate_fixed_preserving_transfer_contract_patch_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PLAN_JSON_FILENAME
    return source


def locate_fixed_preserving_transfer_contract_patch_base(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("fixed-preserving transfer contract patch input must be a JSON object")
    return dict(payload)


def build_fixed_preserving_transfer_contract_patch(
    *,
    transfer_plan: dict[str, Any],
    base_contract_report: dict[str, Any],
    transfer_plan_path: str | Path | None = None,
    base_contract_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_contract = as_dict(base_contract_report.get("contract"))
    patched_contract = _patched_contract(base_contract)
    checks = _checks(transfer_plan, base_contract_report, patched_contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness fixed-preserving transfer contract patch",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_transfer_plan_path": str(transfer_plan_path or ""),
        "source_base_contract_path": str(base_contract_path or ""),
        "source_transfer_plan": {
            "status": transfer_plan.get("status"),
            "decision": transfer_plan.get("decision"),
            "summary": as_dict(transfer_plan.get("summary")),
        },
        "source_base_contract": {
            "status": base_contract_report.get("status"),
            "decision": base_contract_report.get("decision"),
            "summary": as_dict(base_contract_report.get("summary")),
        },
        "contract": patched_contract,
        "patch": {
            "added_rows": FIXED_PRESERVING_TRANSFER_ROWS,
            "added_row_count": len(FIXED_PRESERVING_TRANSFER_ROWS),
            "patch_focus": "light fixed-preserving transfer rows with exact direct-completion rows retained",
        },
        "check_rows": checks,
        "summary": _summary(base_contract, patched_contract, checks),
        "interpretation": _interpretation(status),
    }


def _patched_contract(base_contract: dict[str, Any]) -> dict[str, Any]:
    training_rows = [str(row) for row in base_contract.get("training_rows", [])]
    return {
        **base_contract,
        "contract_version": 9,
        "training_rows": training_rows + FIXED_PRESERVING_TRANSFER_ROWS,
        "patch_kind": "fixed_preserving_transfer",
        "patch_note": "adds a four-row fixed-preserving transfer bridge while preserving exact heldout pair prompt isolation",
    }


def _checks(transfer_plan: dict[str, Any], base_contract_report: dict[str, Any], patched_contract: dict[str, Any]) -> list[dict[str, Any]]:
    plan = as_dict(transfer_plan.get("plan"))
    training_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    probes = list_of_dicts(patched_contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    heldout = str(patched_contract.get("heldout_pair_probe") or "")
    row_budget = int(plan.get("transfer_row_budget") or 0)
    return [
        _check("transfer_plan_passed", transfer_plan.get("status") == "pass", transfer_plan.get("status"), "fixed-preserving transfer plan must pass"),
        _check(
            "transfer_plan_decision",
            transfer_plan.get("decision") == "pair_readiness_fixed_preserving_transfer_plan_ready",
            transfer_plan.get("decision"),
            "patch follows only a ready fixed-preserving transfer plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_fixed_preserving_transfer_contract_patch",
            plan.get("proposed_next_artifact"),
            "plan must request this patch artifact",
        ),
        _check("base_contract_passed", base_contract_report.get("status") == "pass", base_contract_report.get("status"), "base direct-completion contract must pass"),
        _check(
            "base_contract_decision",
            base_contract_report.get("decision") == "pair_readiness_direct_completion_surface_contract_ready",
            base_contract_report.get("decision"),
            "base must be the direct-completion surface contract",
        ),
        _check("fixed_preserving_rows_added", all(row in training_rows for row in FIXED_PRESERVING_TRANSFER_ROWS), "all fixed-preserving rows", "all fixed-preserving transfer rows must be present"),
        _check("transfer_row_budget_respected", 0 < len(FIXED_PRESERVING_TRANSFER_ROWS) <= row_budget, len(FIXED_PRESERVING_TRANSFER_ROWS), "patch must respect plan transfer row budget"),
        _check("broad_pair_transfer_rows_not_reused", not any(row.startswith("pair_transfer ") for row in FIXED_PRESERVING_TRANSFER_ROWS), FIXED_PRESERVING_TRANSFER_ROWS, "patch must not reuse broad pair_transfer rows from the closed route"),
        _check("exact_direct_rows_preserved", {"fixed=fixed", "loss=loss"}.issubset(set(training_rows)), sorted({"fixed=fixed", "loss=loss"} & set(training_rows)), "direct completion rows must be preserved"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair prompt must stay out of training rows"),
        _check("heldout_pair_absent_from_patch", HELDOUT_PAIR_PROBE not in FIXED_PRESERVING_TRANSFER_ROWS, HELDOUT_PAIR_PROBE in FIXED_PRESERVING_TRANSFER_ROWS, "patch rows must not train on exact heldout pair prompt"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
    ]


def _summary(base_contract: dict[str, Any], patched_contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    base_rows = [str(row) for row in base_contract.get("training_rows", [])]
    patched_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    return {
        "patch_ready": all(row.get("status") == "pass" for row in checks),
        "base_training_row_count": len(base_rows),
        "patched_training_row_count": len(patched_rows),
        "added_training_row_count": len(patched_rows) - len(base_rows),
        "fixed_preserving_transfer_row_count": len(FIXED_PRESERVING_TRANSFER_ROWS),
        "evaluation_probe_count": len(patched_contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_fixed_preserving_transfer_contract_patch_ready"
    return "fix_pair_readiness_fixed_preserving_transfer_contract_patch"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fixed-preserving transfer patch failed plan, base-contract, budget, or leakage checks.",
            "next_action": "repair fixed-preserving transfer patch before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_patch_only",
        "reason": "The patched contract keeps direct-completion rows and adds only four non-heldout fixed-preserving transfer rows.",
        "next_action": "materialize the fixed-preserving patched contract and rerun pair-readiness training",
    }


__all__ = [
    "FIXED_PRESERVING_TRANSFER_ROWS",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_CSV_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_HTML_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_JSON_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_CONTRACT_PATCH_TEXT_FILENAME",
    "build_fixed_preserving_transfer_contract_patch",
    "locate_fixed_preserving_transfer_contract_patch_base",
    "locate_fixed_preserving_transfer_contract_patch_plan",
    "read_json_report",
    "resolve_exit_code",
]
