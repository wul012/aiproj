from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_structure_plan import (
    PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_contract.json"
PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_CSV_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_contract.csv"
PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_TEXT_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_contract.txt"
PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_contract.md"
PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_HTML_FILENAME = "model_capability_required_term_pair_readiness_objective_structure_contract.html"


OBJECTIVE_STRUCTURE_ROW_FAMILIES = [
    {
        "family": "task_id_direct_fixed",
        "role": "direct_term_completion",
        "target_term": "fixed",
        "rows": [
            "objective=direct_term | term=fixed | prompt_surface=fixed_equals | answer=fixed",
            "objective=direct_term | case=fixed_branch | target=fixed | response=fixed",
            "task_id=fixed_direct | input=fixed equals prompt | output=fixed token",
            "task_id=fixed_direct | branch=fixed | forbidden=loss | answer=fixed",
        ],
    },
    {
        "family": "task_id_direct_loss",
        "role": "direct_term_completion",
        "target_term": "loss",
        "rows": [
            "objective=direct_term | term=loss | prompt_surface=loss_equals | answer=loss",
            "objective=direct_term | case=loss_branch | target=loss | response=loss",
            "task_id=loss_direct | input=loss equals prompt | output=loss token",
            "task_id=loss_direct | branch=loss | forbidden=fixed | answer=loss",
        ],
    },
    {
        "family": "paired_block_forward",
        "role": "paired_branch_completion",
        "target_term": "fixed+loss",
        "rows": [
            "objective=paired_terms | first=fixed | second=loss | answer=fixed then loss",
            "paired_block order=fixed_loss | fixed branch answer fixed | loss branch answer loss",
            "task_id=pair_forward | fixed_result=fixed | loss_result=loss",
        ],
    },
    {
        "family": "paired_block_reverse",
        "role": "paired_branch_completion",
        "target_term": "loss+fixed",
        "rows": [
            "objective=paired_terms | first=loss | second=fixed | answer=loss then fixed",
            "paired_block order=loss_fixed | loss branch answer loss | fixed branch answer fixed",
            "task_id=pair_reverse | loss_result=loss | fixed_result=fixed",
        ],
    },
    {
        "family": "boundary_contrast",
        "role": "anti_contamination",
        "target_term": "fixed/loss",
        "rows": [
            "contrast fixed_branch keeps fixed and does not answer loss",
            "contrast loss_branch keeps loss and does not answer fixed",
            "boundary fixed answer remains fixed even when loss is nearby",
            "boundary loss answer remains loss even when fixed is nearby",
        ],
    },
]


def locate_objective_structure_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_STRUCTURE_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-structure contract input must be a JSON object")
    return dict(payload)


def build_objective_structure_contract(
    objective_plan: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan = as_dict(objective_plan.get("plan"))
    contract = _contract()
    checks = _checks(objective_plan, plan, contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-structure contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_plan_path": str(source_path or ""),
        "source_plan": {
            "status": objective_plan.get("status"),
            "decision": objective_plan.get("decision"),
            "summary": as_dict(objective_plan.get("summary")),
        },
        "contract": contract,
        "check_rows": checks,
        "summary": _summary(contract, checks),
        "interpretation": _interpretation(status),
    }


def _contract() -> dict[str, Any]:
    training_rows = [row for family in OBJECTIVE_STRUCTURE_ROW_FAMILIES for row in family["rows"]]
    evaluation_probes = [
        {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed", "split": "heldout-direct"},
        {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss", "split": "heldout-direct"},
        {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss", "split": "heldout-pair"},
    ]
    return {
        "contract_version": 5,
        "training_rows": training_rows,
        "row_families": OBJECTIVE_STRUCTURE_ROW_FAMILIES,
        "evaluation_probes": evaluation_probes,
        "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        "promotion_requirement": "fixed-direct and loss-direct heldout continuations must both hit before pair-probe promotion",
        "leakage_policy": "use task-id and paired-block descriptions, but never train on exact heldout direct or pair probes",
        "template_family": "objective_structure_task_id_and_paired_blocks",
        "source_route_boundary": "created after light capacity probe matched fixed-recovery without recovering loss",
    }


def _checks(objective_plan: dict[str, Any], plan: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    row_families = list_of_dicts(contract.get("row_families"))
    probes = list_of_dicts(contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    heldout = str(contract.get("heldout_pair_probe") or "")
    fixed_direct_count = _family_row_count(row_families, "task_id_direct_fixed")
    loss_direct_count = _family_row_count(row_families, "task_id_direct_loss")
    return [
        _check("plan_passed", objective_plan.get("status") == "pass", objective_plan.get("status"), "objective-structure plan must pass"),
        _check(
            "plan_decision",
            objective_plan.get("decision") == "pair_readiness_objective_structure_plan_ready",
            objective_plan.get("decision"),
            "contract follows only a ready objective-structure plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_objective_structure_contract",
            plan.get("proposed_next_artifact"),
            "plan must request this contract artifact",
        ),
        _check("training_rows_present", len(training_rows) >= 16, len(training_rows), "objective-structure rows must be substantial enough to materialize"),
        _check("direct_family_balance", fixed_direct_count == loss_direct_count, f"fixed={fixed_direct_count}, loss={loss_direct_count}", "fixed/loss direct row families must be balanced"),
        _check("paired_forward_present", _family_row_count(row_families, "paired_block_forward") >= 3, _family_row_count(row_families, "paired_block_forward"), "forward paired block rows must be present"),
        _check("paired_reverse_present", _family_row_count(row_families, "paired_block_reverse") >= 3, _family_row_count(row_families, "paired_block_reverse"), "reverse paired block rows must be present"),
        _check("evaluation_probes_present", len(probes) == 3, len(probes), "fixed, loss, and pair probes must be preserved"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair probe must stay out of training rows"),
    ]


def _family_row_count(row_families: list[dict[str, Any]], family_name: str) -> int:
    for family in row_families:
        if family.get("family") == family_name:
            return len(family.get("rows", []))
    return 0


def _summary(contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    row_families = list_of_dicts(contract.get("row_families"))
    return {
        "contract_ready": all(row.get("status") == "pass" for row in checks),
        "training_row_count": len(contract.get("training_rows", [])),
        "row_family_count": len(row_families),
        "evaluation_probe_count": len(contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "heldout_pair_probe": contract.get("heldout_pair_probe"),
        "template_family": contract.get("template_family"),
        "fixed_direct_row_count": _family_row_count(row_families, "task_id_direct_fixed"),
        "loss_direct_row_count": _family_row_count(row_families, "task_id_direct_loss"),
        "paired_block_row_count": _family_row_count(row_families, "paired_block_forward") + _family_row_count(row_families, "paired_block_reverse"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_structure_contract_ready"
    return "fix_pair_readiness_objective_structure_contract"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The objective-structure contract has source-plan, balance, or leakage issues.",
            "next_action": "repair contract before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_only",
        "reason": "The contract replaces single-sided row patching with task-id and paired-block objectives while preserving heldout probes.",
        "next_action": "materialize the objective-structure contract into a training corpus and heldout fixture",
    }


__all__ = [
    "OBJECTIVE_STRUCTURE_ROW_FAMILIES",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_TEXT_FILENAME",
    "build_objective_structure_contract",
    "locate_objective_structure_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
