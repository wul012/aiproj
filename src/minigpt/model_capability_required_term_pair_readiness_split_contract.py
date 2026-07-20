from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_split_plan import (
    PAIR_READINESS_SPLIT_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_SPLIT_CONTRACT_JSON_FILENAME = "model_capability_required_term_pair_readiness_split_contract.json"
PAIR_READINESS_SPLIT_CONTRACT_CSV_FILENAME = "model_capability_required_term_pair_readiness_split_contract.csv"
PAIR_READINESS_SPLIT_CONTRACT_TEXT_FILENAME = "model_capability_required_term_pair_readiness_split_contract.txt"
PAIR_READINESS_SPLIT_CONTRACT_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_split_contract.md"
PAIR_READINESS_SPLIT_CONTRACT_HTML_FILENAME = "model_capability_required_term_pair_readiness_split_contract.html"

HELDOUT_PAIR_PROBE = "fixed=|loss="


def locate_pair_readiness_split_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_SPLIT_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness split contract input must be a JSON object")
    return dict(payload)


def build_pair_readiness_split_contract(
    split_plan: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan = as_dict(split_plan.get("plan"))
    contract = _contract()
    checks = _checks(split_plan, plan, contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair-readiness split contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_plan_path": str(source_path or ""),
        "source_plan": {
            "status": split_plan.get("status"),
            "decision": split_plan.get("decision"),
            "summary": as_dict(split_plan.get("summary")),
        },
        "contract": contract,
        "check_rows": checks,
        "summary": _summary(contract, checks),
        "interpretation": _interpretation(status),
    }


def _contract() -> dict[str, Any]:
    training_rows = [
        "fixed=f",
        "fixed=fi",
        "fixed=fix",
        "fixed=fixed",
        "loss=l",
        "loss=lo",
        "loss=los",
        "loss=loss",
        "fixed branch starts with f",
        "loss branch starts with l",
        "fixed branch does not start loss",
        "loss branch does not start fixed",
    ]
    evaluation_probes = [
        {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed", "split": "heldout-direct"},
        {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss", "split": "heldout-direct"},
        {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss", "split": "heldout-pair"},
    ]
    return {
        "contract_version": 1,
        "training_rows": training_rows,
        "evaluation_probes": evaluation_probes,
        "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        "promotion_requirement": "fixed-direct and loss-direct heldout continuations must both hit before pair capability is claimed",
        "leakage_policy": "evaluation prompts may be prefixes but exact heldout pair probes must not appear in training rows",
    }


def _checks(split_plan: dict[str, Any], plan: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    probes = [as_dict(row) for row in contract.get("evaluation_probes", [])]
    probe_prompts = [str(row.get("prompt")) for row in probes]
    return [
        _check("plan_passed", split_plan.get("status") == "pass", split_plan.get("status"), "split plan must pass"),
        _check(
            "plan_decision",
            split_plan.get("decision") == "pair_readiness_split_plan_ready",
            split_plan.get("decision"),
            "contract follows only a ready pair-readiness split plan",
        ),
        _check(
            "next_artifact_matches",
            plan.get("proposed_next_artifact") == "pair_readiness_split_contract",
            plan.get("proposed_next_artifact"),
            "plan must request this contract artifact",
        ),
        _check("training_rows_present", len(training_rows) >= 8, len(training_rows), "contract needs direct and anti-contamination rows"),
        _check("evaluation_probes_present", len(probes) == 3, len(probes), "contract needs fixed, loss, and pair heldout probes"),
        _check(
            "no_exact_eval_row_overlap",
            not (set(training_rows) & set(probe_prompts)),
            sorted(set(training_rows) & set(probe_prompts)),
            "evaluation prompt strings must not be exact training rows",
        ),
        _check(
            "heldout_pair_probe_absent",
            HELDOUT_PAIR_PROBE not in training_rows,
            HELDOUT_PAIR_PROBE in training_rows,
            "heldout pair probe must stay out of training rows",
        ),
    ]


def _summary(contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "training_row_count": len(contract.get("training_rows", [])),
        "evaluation_probe_count": len(contract.get("evaluation_probes", [])),
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "heldout_pair_probe": contract.get("heldout_pair_probe"),
        "contract_ready": all(row.get("status") == "pass" for row in checks),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_split_contract_ready"
    return "fix_pair_readiness_split_contract"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The pair-readiness split contract has leakage or source-plan issues.",
            "next_action": "repair contract before training",
        }
    return {
        "model_quality_claim": "contract_only",
        "reason": "Training rows and heldout probes are now separated enough to build a corpus without reusing the pair probe as a training row.",
        "next_action": "materialize the contract into a training corpus and heldout evaluation fixture",
    }


__all__ = [
    "HELDOUT_PAIR_PROBE",
    "PAIR_READINESS_SPLIT_CONTRACT_CSV_FILENAME",
    "PAIR_READINESS_SPLIT_CONTRACT_HTML_FILENAME",
    "PAIR_READINESS_SPLIT_CONTRACT_JSON_FILENAME",
    "PAIR_READINESS_SPLIT_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_READINESS_SPLIT_CONTRACT_TEXT_FILENAME",
    "build_pair_readiness_split_contract",
    "locate_pair_readiness_split_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
