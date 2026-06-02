from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_level_contrast_plan import (
    PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.json"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.csv"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.txt"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.md"
)
PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.html"
)


OBJECTIVE_LEVEL_CONTRAST_ROW_FAMILIES = [
    {
        "family": "objective_header",
        "role": "objective_first_pair_answer",
        "target_term": "fixed+loss",
        "rows": [
            "objective pair_terms answer_target fixed loss response fixed loss",
            "task pair_terms required_terms fixed loss output fixed loss",
            "goal emit both required terms first fixed second loss answer fixed loss",
            "instruction provide required terms fixed and loss reply fixed loss",
            "objective required_pair fixed before loss answer fixed loss",
            "task paired_required_terms result tokens fixed loss",
        ],
    },
    {
        "family": "branch_role_contrast",
        "role": "balanced_branch_identity",
        "target_term": "fixed/loss",
        "rows": [
            "branch fixed_role asks fixed target answer fixed",
            "branch fixed_signal keeps fixed answer fixed",
            "branch fixed_objective excludes loss answer fixed",
            "branch fixed_named_output returns fixed",
            "branch loss_role asks loss target answer loss",
            "branch loss_signal keeps loss answer loss",
            "branch loss_objective excludes fixed answer loss",
            "branch loss_named_output returns loss",
        ],
    },
    {
        "family": "pair_answer_contrast",
        "role": "paired_objective_variants",
        "target_term": "fixed+loss",
        "rows": [
            "paired objective both branches fixed term and loss term answer fixed loss",
            "paired contrast fixed branch plus loss branch answer fixed loss",
            "required pair tokens are fixed then loss response fixed loss",
            "two term objective fixed term followed by loss term answer fixed loss",
            "pair task first branch fixed second branch loss output fixed loss",
            "joint required terms fixed loss answer exactly fixed loss",
            "contrast pair keeps fixed with loss response fixed loss",
            "objective pair answer includes fixed and loss response fixed loss",
        ],
    },
    {
        "family": "separator_neutral_answer",
        "role": "answer_separator_variants",
        "target_term": "fixed+loss",
        "rows": [
            "separator neutral pair answer fixed then loss",
            "separator neutral required terms fixed plus loss",
            "separator neutral combined answer fixed and loss",
            "separator neutral compact answer fixed loss",
        ],
    },
]


def locate_objective_level_contrast_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("objective-level contrast contract input must be a JSON object")
    return dict(payload)


def build_objective_level_contrast_contract(
    plan_report: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan = as_dict(plan_report.get("plan"))
    contract = _contract(plan)
    checks = _checks(plan_report, plan, contract)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness objective-level contrast contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_plan_path": str(source_path or ""),
        "source_plan": {
            "status": plan_report.get("status"),
            "decision": plan_report.get("decision"),
            "summary": as_dict(plan_report.get("summary")),
        },
        "contract": contract,
        "check_rows": checks,
        "summary": _summary(contract, checks),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 1 if require_pass and report.get("status") != "pass" else 0


def _contract(plan: dict[str, Any]) -> dict[str, Any]:
    training_rows = [row for family in OBJECTIVE_LEVEL_CONTRAST_ROW_FAMILIES for row in family["rows"]]
    return {
        "contract_version": 11,
        "training_rows": training_rows,
        "row_families": OBJECTIVE_LEVEL_CONTRAST_ROW_FAMILIES,
        "evaluation_probes": [
            {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed", "split": "heldout-direct"},
            {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss", "split": "heldout-direct"},
            {"id": "exact-heldout-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss", "split": "heldout-pair"},
        ],
        "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        "promotion_requirement": "direct fixed/loss hits must transfer to the heldout pair replay before promotion",
        "leakage_policy": "train objective descriptions and answer terms, never the exact heldout prompt surfaces",
        "template_family": "objective_level_contrast",
        "source_selected_route": plan.get("selected_route"),
        "source_objective": as_dict(plan.get("objective")),
    }


def _checks(plan_report: dict[str, Any], plan: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    row_families = list_of_dicts(contract.get("row_families"))
    probes = list_of_dicts(contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    planned_count = int(as_dict(plan_report.get("summary")).get("planned_training_row_count") or 0)
    return [
        _check("plan_passed", plan_report.get("status") == "pass", plan_report.get("status"), "objective-level contrast plan must pass"),
        _check(
            "plan_decision",
            plan_report.get("decision") == "pair_readiness_objective_level_contrast_plan_ready",
            plan_report.get("decision"),
            "contract follows only a ready objective-level contrast plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_objective_level_contrast_contract",
            plan.get("proposed_next_artifact"),
            "plan must request this contract artifact",
        ),
        _check("training_row_count_matches_plan", len(training_rows) == planned_count, f"actual={len(training_rows)}, planned={planned_count}", "contract rows must match planned row count"),
        _check("row_families_present", len(row_families) == 4, len(row_families), "all four planned row families must be present"),
        _check("branch_role_balance", _branch_family_count(row_families, "answer fixed") == _branch_family_count(row_families, "answer loss"), _branch_count_text(row_families), "fixed and loss branch answer rows must be balanced"),
        _check("evaluation_probes_present", len(probes) == 3, len(probes), "fixed, loss, and exact pair probes must be preserved"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", HELDOUT_PAIR_PROBE not in training_rows, HELDOUT_PAIR_PROBE in training_rows, "heldout pair probe must stay out of training rows"),
        _check("no_near_exact_pipe_prompt", not any("|" in row or "=" in row for row in training_rows), "pipe_or_equals_absent", "objective-level rows must avoid near-exact pipe/equals prompt surfaces"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _branch_family_count(row_families: list[dict[str, Any]], needle: str) -> int:
    return sum(1 for row in _family_rows(row_families, "branch_role_contrast") if needle in row)


def _branch_count_text(row_families: list[dict[str, Any]]) -> str:
    return f"fixed={_branch_family_count(row_families, 'answer fixed')}, loss={_branch_family_count(row_families, 'answer loss')}"


def _family_rows(row_families: list[dict[str, Any]], family_name: str) -> list[str]:
    for family in row_families:
        if family.get("family") == family_name:
            return [str(row) for row in family.get("rows", [])]
    return []


def _summary(contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [str(row) for row in contract.get("training_rows", [])]
    row_families = list_of_dicts(contract.get("row_families"))
    return {
        "contract_ready": all(row["status"] == "pass" for row in checks),
        "training_row_count": len(rows),
        "row_family_count": len(row_families),
        "evaluation_probe_count": len(contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "heldout_pair_probe": contract.get("heldout_pair_probe"),
        "template_family": contract.get("template_family"),
        "objective_header_row_count": _family_row_count(row_families, "objective_header"),
        "branch_role_row_count": _family_row_count(row_families, "branch_role_contrast"),
        "pair_answer_row_count": _family_row_count(row_families, "pair_answer_contrast"),
        "separator_neutral_row_count": _family_row_count(row_families, "separator_neutral_answer"),
    }


def _family_row_count(row_families: list[dict[str, Any]], family_name: str) -> int:
    for family in row_families:
        if family.get("family") == family_name:
            return len(family.get("rows", []))
    return 0


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_objective_level_contrast_contract_ready"
    return "fix_pair_readiness_objective_level_contrast_contract"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The objective-level contrast contract failed plan, balance, count, or leakage checks.",
            "next_action": "repair contract before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_only",
        "reason": "The contract teaches objective-level paired answers while avoiding heldout prompt surfaces.",
        "next_action": "materialize the objective-level contrast contract and train a fresh tiny checkpoint",
    }


__all__ = [
    "OBJECTIVE_LEVEL_CONTRAST_ROW_FAMILIES",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_CSV_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_HTML_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_JSON_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_READINESS_OBJECTIVE_LEVEL_CONTRAST_CONTRACT_TEXT_FILENAME",
    "build_objective_level_contrast_contract",
    "locate_objective_level_contrast_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
