from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_objective_structure_contract import (
    PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_readiness_training_run import (
    PAIR_READINESS_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_JSON_FILENAME = "model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.json"
PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_CSV_FILENAME = "model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.csv"
PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_TEXT_FILENAME = "model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.txt"
PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.md"
PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_HTML_FILENAME = "model_capability_required_term_pair_readiness_surface_mismatch_diagnostic.html"


def locate_surface_mismatch_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_OBJECTIVE_STRUCTURE_CONTRACT_JSON_FILENAME
    return source


def locate_surface_mismatch_training_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface mismatch diagnostic input must be a JSON object")
    return dict(payload)


def build_surface_mismatch_diagnostic(
    *,
    contract_report: dict[str, Any],
    training_report: dict[str, Any],
    contract_path: str | Path | None = None,
    training_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract = as_dict(contract_report.get("contract"))
    replay_rows = list_of_dicts(as_dict(training_report.get("replay_report")).get("case_rows"))
    analysis_rows = _analysis_rows(contract, replay_rows)
    summary = _summary(contract, training_report, analysis_rows)
    checks = _checks(contract_report, training_report, summary)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT pair-readiness surface mismatch diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_contract_path": str(contract_path or ""),
        "source_training_path": str(training_path or ""),
        "source_contract": {
            "status": contract_report.get("status"),
            "decision": contract_report.get("decision"),
            "summary": as_dict(contract_report.get("summary")),
        },
        "source_training": {
            "status": training_report.get("status"),
            "decision": training_report.get("decision"),
            "summary": as_dict(training_report.get("summary")),
        },
        "analysis_rows": analysis_rows,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _analysis_rows(contract: dict[str, Any], replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        if replay.get("profile_id") != "default":
            continue
        prompt = str(replay.get("prompt") or "")
        term = str(replay.get("term") or "")
        continuation = str(replay.get("continuation") or "").rstrip()
        rows.append(
            {
                "term": term,
                "prompt": prompt,
                "continuation": continuation,
                "continuation_hit": bool(replay.get("continuation_hit")),
                "exact_prompt_training_row": prompt in training_rows,
                "raw_surface_reference_count": _raw_surface_reference_count(training_rows, prompt),
                "surface_class": _surface_class(prompt, continuation),
            }
        )
    return rows


def _raw_surface_reference_count(training_rows: list[str], prompt: str) -> int:
    return sum(1 for row in training_rows if prompt in row)


def _surface_class(prompt: str, continuation: str) -> str:
    if "fixed" in continuation or "loss" in continuation:
        return "term_surface_present"
    if prompt and continuation:
        return "non_term_surface"
    return "empty_surface"


def _summary(contract: dict[str, Any], training_report: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    default_terms = [str(row.get("term")) for row in rows]
    hit_terms = [str(row.get("term")) for row in rows if row.get("continuation_hit")]
    missed_terms = [str(row.get("term")) for row in rows if not row.get("continuation_hit")]
    direct_terms = ["fixed", "loss"]
    both_direct_missed = all(term in missed_terms for term in direct_terms)
    exact_prompt_overlap_count = sum(1 for row in rows if row.get("exact_prompt_training_row"))
    raw_surface_reference_count = sum(int(row.get("raw_surface_reference_count") or 0) for row in rows)
    surface_mismatch = bool(
        as_dict(training_report.get("summary")).get("training_status") == "pass"
        and both_direct_missed
        and exact_prompt_overlap_count == 0
        and raw_surface_reference_count == 0
    )
    return {
        "training_row_count": len(training_rows),
        "template_family": contract.get("template_family"),
        "default_replay_term_count": len(default_terms),
        "default_hit_terms": hit_terms,
        "default_missed_terms": missed_terms,
        "both_direct_terms_missed": both_direct_missed,
        "exact_prompt_overlap_count": exact_prompt_overlap_count,
        "raw_surface_reference_count": raw_surface_reference_count,
        "surface_mismatch_detected": surface_mismatch,
        "recommended_next_artifact": "pair_readiness_direct_prompt_bridge_contract_patch",
        "bridge_needed_terms": missed_terms,
    }


def _checks(contract_report: dict[str, Any], training_report: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("contract_passed", contract_report.get("status") == "pass", contract_report.get("status"), "source objective contract must pass"),
        _check(
            "contract_decision",
            contract_report.get("decision") == "pair_readiness_objective_structure_contract_ready",
            contract_report.get("decision"),
            "diagnostic follows only the objective-structure contract",
        ),
        _check("training_report_passed", training_report.get("status") == "pass", training_report.get("status"), "source training report must pass"),
        _check(
            "training_no_pair_full",
            training_report.get("decision") == "pair_readiness_training_no_pair_full",
            training_report.get("decision"),
            "surface mismatch diagnostic is only for no-pair-full training runs",
        ),
        _check("default_replay_terms_present", int(summary.get("default_replay_term_count") or 0) >= 2, summary.get("default_replay_term_count"), "need default fixed/loss replay rows"),
        _check("both_direct_terms_missed", summary.get("both_direct_terms_missed") is True, summary.get("both_direct_terms_missed"), "both direct terms must miss before planning a bridge"),
    ]


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_surface_mismatch_diagnostic_input"
    if summary.get("surface_mismatch_detected") is True:
        return "pair_readiness_direct_surface_mismatch_detected"
    return "pair_readiness_surface_mismatch_not_detected"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The diagnostic could not trust the source contract or training replay.",
            "next_action": "repair source evidence before patching objective rows",
        }
    if summary.get("surface_mismatch_detected") is True:
        return {
            "model_quality_claim": "diagnostic_only",
            "reason": "The objective-structure rows avoid exact direct prompts, and both heldout direct prompts miss with non-term continuations.",
            "next_action": "build pair_readiness_direct_prompt_bridge_contract_patch without adding the heldout pair probe",
        }
    return {
        "model_quality_claim": "diagnostic_only",
        "reason": "The direct replay misses are not explained by raw prompt surface mismatch alone.",
        "next_action": "inspect replay continuations before changing the contract",
    }


__all__ = [
    "PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_READINESS_SURFACE_MISMATCH_DIAGNOSTIC_TEXT_FILENAME",
    "build_surface_mismatch_diagnostic",
    "locate_surface_mismatch_contract_source",
    "locate_surface_mismatch_training_source",
    "read_json_report",
    "resolve_exit_code",
]
