from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_bridge_closeout_plan import (
    PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.json"
)
PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.csv"
)
PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.txt"
)
PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.md"
)
PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.html"
)


DIRECT_COMPLETION_SURFACE_ROW_FAMILIES = [
    {
        "family": "exact_direct_completion",
        "role": "direct_completion_surface",
        "target_term": "fixed/loss",
        "rows": ["fixed=fixed", "loss=loss"],
    },
    {
        "family": "fixed_prefix_ladder",
        "role": "direct_completion_prefix",
        "target_term": "fixed",
        "rows": ["fixed=f", "fixed=fi", "fixed=fix"],
    },
    {
        "family": "loss_prefix_ladder",
        "role": "direct_completion_prefix",
        "target_term": "loss",
        "rows": ["loss=l", "loss=lo", "loss=los"],
    },
    {
        "family": "paired_order_forward",
        "role": "paired_order_surface",
        "target_term": "fixed+loss",
        "rows": [
            "pair_surface order=fixed_then_loss | fixed=fixed | loss=loss",
            "pair_surface forward fixed token fixed and loss token loss",
        ],
    },
    {
        "family": "paired_order_reverse",
        "role": "paired_order_surface",
        "target_term": "loss+fixed",
        "rows": [
            "pair_surface order=loss_then_fixed | loss=loss | fixed=fixed",
            "pair_surface reverse loss token loss and fixed token fixed",
        ],
    },
    {
        "family": "direct_boundary_contrast",
        "role": "anti_contamination",
        "target_term": "fixed/loss",
        "rows": [
            "direct_completion fixed branch keeps fixed not loss",
            "direct_completion loss branch keeps loss not fixed",
            "direct_completion fixed surface cannot answer loss",
            "direct_completion loss surface cannot answer fixed",
        ],
    },
]


def locate_direct_completion_surface_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_BRIDGE_CLOSEOUT_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("direct-completion surface contract input must be a JSON object")
    return dict(payload)


def build_direct_completion_surface_contract(
    closeout_plan: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan = as_dict(closeout_plan.get("plan"))
    contract = _contract()
    checks = _checks(closeout_plan, plan, contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness direct-completion surface contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_closeout_plan_path": str(source_path or ""),
        "source_closeout_plan": {
            "status": closeout_plan.get("status"),
            "decision": closeout_plan.get("decision"),
            "summary": as_dict(closeout_plan.get("summary")),
        },
        "contract": contract,
        "check_rows": checks,
        "summary": _summary(contract, checks),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _contract() -> dict[str, Any]:
    training_rows = [row for family in DIRECT_COMPLETION_SURFACE_ROW_FAMILIES for row in family["rows"]]
    evaluation_probes = [
        {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed", "split": "heldout-direct"},
        {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss", "split": "heldout-direct"},
        {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss", "split": "heldout-pair"},
    ]
    return {
        "contract_version": 7,
        "training_rows": training_rows,
        "row_families": DIRECT_COMPLETION_SURFACE_ROW_FAMILIES,
        "evaluation_probes": evaluation_probes,
        "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        "promotion_requirement": "fixed-direct and loss-direct heldout continuations must both hit before pair-probe promotion",
        "leakage_policy": "train exact direct completions and balanced prefixes, but keep exact heldout prompts and pair probe out of training rows",
        "template_family": "direct_completion_surface_balanced_prefix_ladder",
        "source_route_boundary": "created after direct-prompt bridge patch had zero hit improvement and introduced fixed pollution",
    }


def _checks(closeout_plan: dict[str, Any], plan: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    row_families = list_of_dicts(contract.get("row_families"))
    probes = list_of_dicts(contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    heldout = str(contract.get("heldout_pair_probe") or "")
    exact_rows = _family_rows(row_families, "exact_direct_completion")
    return [
        _check("closeout_plan_passed", closeout_plan.get("status") == "pass", closeout_plan.get("status"), "bridge closeout plan must pass"),
        _check(
            "closeout_plan_decision",
            closeout_plan.get("decision") == "pair_readiness_bridge_closeout_plan_ready",
            closeout_plan.get("decision"),
            "contract follows only a ready bridge closeout plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_direct_completion_surface_contract",
            plan.get("proposed_next_artifact"),
            "closeout plan must request this contract artifact",
        ),
        _check("training_rows_present", len(training_rows) >= 16, len(training_rows), "direct-completion surface rows must be materializable"),
        _check("exact_fixed_completion_present", "fixed=fixed" in exact_rows, exact_rows, "exact fixed completion row must be present"),
        _check("exact_loss_completion_present", "loss=loss" in exact_rows, exact_rows, "exact loss completion row must be present"),
        _check(
            "prefix_ladder_balance",
            _family_row_count(row_families, "fixed_prefix_ladder") == _family_row_count(row_families, "loss_prefix_ladder"),
            f"fixed={_family_row_count(row_families, 'fixed_prefix_ladder')}, loss={_family_row_count(row_families, 'loss_prefix_ladder')}",
            "fixed and loss prefix ladders must contain the same number of rows",
        ),
        _check("paired_forward_present", _family_row_count(row_families, "paired_order_forward") >= 2, _family_row_count(row_families, "paired_order_forward"), "forward paired order rows must be present"),
        _check("paired_reverse_present", _family_row_count(row_families, "paired_order_reverse") >= 2, _family_row_count(row_families, "paired_order_reverse"), "reverse paired order rows must be present"),
        _check("evaluation_probes_present", len(probes) == 3, len(probes), "fixed, loss, and pair probes must be preserved"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair probe must stay out of training rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _family_rows(row_families: list[dict[str, Any]], family_name: str) -> list[str]:
    for family in row_families:
        if family.get("family") == family_name:
            return [str(row) for row in family.get("rows", [])]
    return []


def _family_row_count(row_families: list[dict[str, Any]], family_name: str) -> int:
    return len(_family_rows(row_families, family_name))


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
        "exact_completion_row_count": _family_row_count(row_families, "exact_direct_completion"),
        "fixed_prefix_row_count": _family_row_count(row_families, "fixed_prefix_ladder"),
        "loss_prefix_row_count": _family_row_count(row_families, "loss_prefix_ladder"),
        "paired_order_row_count": _family_row_count(row_families, "paired_order_forward") + _family_row_count(row_families, "paired_order_reverse"),
        "boundary_contrast_row_count": _family_row_count(row_families, "direct_boundary_contrast"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_direct_completion_surface_contract_ready"
    return "fix_pair_readiness_direct_completion_surface_contract"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The direct-completion surface contract has source-plan, balance, or leakage issues.",
            "next_action": "repair direct-completion contract before corpus materialization",
        }
    return {
        "model_quality_claim": "contract_only",
        "reason": "The contract replaces descriptive bridge rows with compact exact direct completions and balanced prefix surfaces.",
        "next_action": "materialize the direct-completion surface contract and rerun pair-readiness training",
    }


__all__ = [
    "DIRECT_COMPLETION_SURFACE_ROW_FAMILIES",
    "PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_CSV_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_HTML_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_JSON_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_READINESS_DIRECT_COMPLETION_SURFACE_CONTRACT_TEXT_FILENAME",
    "build_direct_completion_surface_contract",
    "locate_direct_completion_surface_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
