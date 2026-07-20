from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_structure_contract import (
    PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_surface_mismatch_diagnostic import (
    PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME = "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.json"
PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_CSV_FILENAME = "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.csv"
PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_TEXT_FILENAME = "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.txt"
PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.md"
PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_HTML_FILENAME = "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.html"


DIRECT_PROMPT_BRIDGE_ROWS = [
    "bridge=direct_prompt | prompt=fixed= | answer=fixed",
    "bridge fixed raw surface fixed= produces fixed",
    "direct prompt fixed= should continue with fixed",
    "fixed= -> fixed token",
    "bridge=direct_prompt | prompt=loss= | answer=loss",
    "bridge loss raw surface loss= produces loss",
    "direct prompt loss= should continue with loss",
    "loss= -> loss token",
]


def locate_direct_prompt_bridge_contract_patch_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_direct_prompt_bridge_contract_patch_base(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("direct-prompt bridge contract patch input must be a JSON object")
    return dict(payload)


def build_direct_prompt_bridge_contract_patch(
    *,
    diagnostic_report: dict[str, Any],
    base_contract_report: dict[str, Any],
    diagnostic_path: str | Path | None = None,
    base_contract_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    base_contract = as_dict(base_contract_report.get("contract"))
    patched_contract = _patched_contract(base_contract)
    checks = _checks(diagnostic_report, base_contract_report, patched_contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness direct-prompt bridge contract patch",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_diagnostic_path": str(diagnostic_path or ""),
        "source_base_contract_path": str(base_contract_path or ""),
        "source_diagnostic": {
            "status": diagnostic_report.get("status"),
            "decision": diagnostic_report.get("decision"),
            "summary": as_dict(diagnostic_report.get("summary")),
        },
        "source_base_contract": {
            "status": base_contract_report.get("status"),
            "decision": base_contract_report.get("decision"),
            "summary": as_dict(base_contract_report.get("summary")),
        },
        "contract": patched_contract,
        "patch": {
            "added_rows": DIRECT_PROMPT_BRIDGE_ROWS,
            "added_row_count": len(DIRECT_PROMPT_BRIDGE_ROWS),
            "patch_focus": "raw fixed= and loss= direct prompt bridge without adding the heldout pair probe",
        },
        "check_rows": checks,
        "summary": _summary(base_contract, patched_contract, checks),
        "interpretation": _interpretation(status),
    }


def _patched_contract(base_contract: dict[str, Any]) -> dict[str, Any]:
    training_rows = [str(row) for row in base_contract.get("training_rows", [])]
    return {
        **base_contract,
        "contract_version": 6,
        "training_rows": training_rows + DIRECT_PROMPT_BRIDGE_ROWS,
        "patch_kind": "direct_prompt_bridge",
        "patch_note": "bridge rows expose raw fixed= and loss= surfaces while preserving heldout pair probe isolation",
    }


def _checks(diagnostic_report: dict[str, Any], base_contract_report: dict[str, Any], patched_contract: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostic_summary = as_dict(diagnostic_report.get("summary"))
    training_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    probes = list_of_dicts(patched_contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    heldout = str(patched_contract.get("heldout_pair_probe") or "")
    return [
        _check("diagnostic_passed", diagnostic_report.get("status") == "pass", diagnostic_report.get("status"), "surface mismatch diagnostic must pass"),
        _check(
            "diagnostic_decision",
            diagnostic_report.get("decision") == "pair_readiness_direct_surface_mismatch_detected",
            diagnostic_report.get("decision"),
            "bridge patch follows only a detected direct surface mismatch",
        ),
        _check("diagnostic_recommends_bridge", diagnostic_summary.get("recommended_next_artifact") == "pair_readiness_direct_prompt_bridge_contract_patch", diagnostic_summary.get("recommended_next_artifact"), "diagnostic must request this patch"),
        _check("base_contract_passed", base_contract_report.get("status") == "pass", base_contract_report.get("status"), "base objective-structure contract must pass"),
        _check(
            "base_contract_decision",
            base_contract_report.get("decision") == "pair_readiness_objective_structure_contract_ready",
            base_contract_report.get("decision"),
            "base must be the objective-structure contract",
        ),
        _check("bridge_rows_added", all(row in training_rows for row in DIRECT_PROMPT_BRIDGE_ROWS), "all bridge rows", "all direct prompt bridge rows must be present"),
        _check("fixed_bridge_balance", _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "fixed=") == 4, _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "fixed="), "fixed bridge rows must be balanced"),
        _check("loss_bridge_balance", _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "loss=") == 4, _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "loss="), "loss bridge rows must be balanced"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair probe must stay out of training rows"),
    ]


def _contains_count(rows: list[str], needle: str) -> int:
    return sum(1 for row in rows if needle in row)


def _summary(base_contract: dict[str, Any], patched_contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    base_rows = [str(row) for row in base_contract.get("training_rows", [])]
    patched_rows = [str(row) for row in patched_contract.get("training_rows", [])]
    return {
        "base_training_row_count": len(base_rows),
        "patched_training_row_count": len(patched_rows),
        "added_training_row_count": len(patched_rows) - len(base_rows),
        "bridge_row_count": len(DIRECT_PROMPT_BRIDGE_ROWS),
        "fixed_bridge_row_count": _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "fixed="),
        "loss_bridge_row_count": _contains_count(DIRECT_PROMPT_BRIDGE_ROWS, "loss="),
        "evaluation_probe_count": len(patched_contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "patch_ready": all(row.get("status") == "pass" for row in checks),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_direct_prompt_bridge_contract_patch_ready"
    return "fix_pair_readiness_direct_prompt_bridge_contract_patch"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The direct-prompt bridge patch failed diagnostic, base-contract, balance, or leakage checks.",
            "next_action": "repair bridge patch before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_patch_only",
        "reason": "The patched contract now includes raw fixed= and loss= bridge rows while keeping the pair heldout probe isolated.",
        "next_action": "materialize the direct-prompt bridge contract and rerun pair-readiness training",
    }


__all__ = [
    "DIRECT_PROMPT_BRIDGE_ROWS",
    "PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_CSV_FILENAME",
    "PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_HTML_FILENAME",
    "PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_JSON_FILENAME",
    "PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_MARKDOWN_FILENAME",
    "PAIR_READINESS_DIRECT_PROMPT_BRIDGE_CONTRACT_PATCH_TEXT_FILENAME",
    "build_direct_prompt_bridge_contract_patch",
    "locate_direct_prompt_bridge_contract_patch_base",
    "locate_direct_prompt_bridge_contract_patch_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
