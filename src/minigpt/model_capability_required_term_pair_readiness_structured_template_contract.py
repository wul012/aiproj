from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_repair_comparison import (
    PAIR_READINESS_REPAIR_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_split_contract import HELDOUT_PAIR_PROBE
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_structured_template_contract.json"
)
PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_structured_template_contract.csv"
)
PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_structured_template_contract.txt"
)
PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_structured_template_contract.md"
)
PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_structured_template_contract.html"
)

STRUCTURED_TEMPLATE_ROWS = [
    "task: complete required term | prompt: fixed= | answer: fixed",
    "task: complete required term | prompt: loss= | answer: loss",
    "case=fixed | prompt=fixed= | expected=fixed | answer=fixed",
    "case=loss | prompt=loss= | expected=loss | answer=loss",
    "fixed direct template -> fixed",
    "loss direct template -> loss",
    "fixed route target term is fixed",
    "loss route target term is loss",
    "when prompt begins fixed= complete fixed",
    "when prompt begins loss= complete loss",
    "required term fixed stays on fixed branch",
    "required term loss stays on loss branch",
    "fixed branch answer uses fixed and avoids loss",
    "loss branch answer uses loss and avoids fixed",
]


def locate_structured_template_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_REPAIR_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("structured-template contract input must be a JSON object")
    return dict(payload)


def build_structured_template_contract(
    repair_comparison: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract = _contract()
    checks = _checks(repair_comparison, contract)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness structured-template contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_comparison_path": str(source_path or ""),
        "source_comparison": {
            "status": repair_comparison.get("status"),
            "decision": repair_comparison.get("decision"),
            "summary": as_dict(repair_comparison.get("summary")),
        },
        "contract": contract,
        "check_rows": checks,
        "summary": _summary(repair_comparison, contract, checks),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _contract() -> dict[str, Any]:
    evaluation_probes = [
        {"id": "fixed-direct", "prompt": "fixed=", "expected_term": "fixed", "split": "heldout-direct"},
        {"id": "loss-direct", "prompt": "loss=", "expected_term": "loss", "split": "heldout-direct"},
        {"id": "fixed-loss-pair", "prompt": HELDOUT_PAIR_PROBE, "expected_term": "fixed+loss", "split": "heldout-pair"},
    ]
    return {
        "contract_version": 3,
        "training_rows": STRUCTURED_TEMPLATE_ROWS,
        "evaluation_probes": evaluation_probes,
        "heldout_pair_probe": HELDOUT_PAIR_PROBE,
        "promotion_requirement": "fixed-direct and loss-direct must both hit before pair probe or baseline promotion is claimed",
        "leakage_policy": "structured rows may describe direct prompts, but exact heldout probe strings must not be training rows",
        "template_family": "prompt_answer_structured_direct_terms",
        "source_route_boundary": "created after the loss-retention prefix repair regressed, so this avoids more single-sided prefix weighting",
    }


def _checks(repair_comparison: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    summary = as_dict(repair_comparison.get("summary"))
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    probes = list_of_dicts(contract.get("evaluation_probes"))
    probe_prompts = [str(row.get("prompt")) for row in probes]
    heldout = str(contract.get("heldout_pair_probe") or "")
    return [
        _check("source_comparison_passed", repair_comparison.get("status") == "pass", repair_comparison.get("status"), "source comparison must pass"),
        _check(
            "source_comparison_decision",
            repair_comparison.get("decision") == "pair_readiness_loss_retention_patch_regressed",
            repair_comparison.get("decision"),
            "structured template route follows only the closed loss-retention regression branch",
        ),
        _check("prior_route_regressed", summary.get("candidate_regressed") is True, summary.get("candidate_regressed"), "source must confirm the prior repair regressed"),
        _check("prior_default_delta_negative", int(summary.get("default_hit_delta") or 0) < 0, summary.get("default_hit_delta"), "source default-hit delta must be negative"),
        _check("training_rows_present", len(training_rows) >= 12, len(training_rows), "structured template rows must be substantial enough to materialize"),
        _check("fixed_rows_present", _contains_count(training_rows, "fixed") >= 6, _contains_count(training_rows, "fixed"), "fixed route must have repeated structured anchors"),
        _check("loss_rows_present", _contains_count(training_rows, "loss") >= 6, _contains_count(training_rows, "loss"), "loss route must have repeated structured anchors"),
        _check("evaluation_probes_present", len(probes) == 3, len(probes), "fixed, loss, and pair probes must be preserved"),
        _check("no_exact_eval_row_overlap", not (set(training_rows) & set(probe_prompts)), sorted(set(training_rows) & set(probe_prompts)), "exact eval prompts must not be training rows"),
        _check("heldout_pair_absent", heldout not in training_rows, heldout in training_rows, "heldout pair probe must stay out of training rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _contains_count(rows: list[str], needle: str) -> int:
    return sum(1 for row in rows if needle in row)


def _summary(repair_comparison: dict[str, Any], contract: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    comparison_summary = as_dict(repair_comparison.get("summary"))
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    return {
        "contract_ready": all(row.get("status") == "pass" for row in checks),
        "structured_training_row_count": len(training_rows),
        "evaluation_probe_count": len(contract.get("evaluation_probes", [])),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "source_default_hit_delta": comparison_summary.get("default_hit_delta"),
        "source_candidate_regressed": comparison_summary.get("candidate_regressed"),
        "heldout_pair_probe": contract.get("heldout_pair_probe"),
        "template_family": contract.get("template_family"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_structured_template_contract_ready"
    return "fix_pair_readiness_structured_template_contract"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The structured-template contract could not prove source-route closure or leakage safety.",
            "next_action": "repair the contract or re-check the v713 comparison before materialization",
        }
    return {
        "model_quality_claim": "contract_only",
        "reason": "The previous prefix-weighting repair regressed, so this contract switches to structured prompt-answer rows while preserving heldout direct and pair probes.",
        "next_action": "materialize the structured-template contract and run a real tiny training comparison",
    }


__all__ = [
    "PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_CSV_FILENAME",
    "PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_HTML_FILENAME",
    "PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_JSON_FILENAME",
    "PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_READINESS_STRUCTURED_TEMPLATE_CONTRACT_TEXT_FILENAME",
    "STRUCTURED_TEMPLATE_ROWS",
    "build_structured_template_contract",
    "locate_structured_template_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
