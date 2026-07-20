from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_seed_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSONL_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.jsonl"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CORPUS_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_corpus.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision.html"


def locate_curriculum_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME
    return source


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision(
    curriculum_revision: dict[str, Any],
    objective_contract_report: dict[str, Any],
    *,
    curriculum_revision_path: str | Path | None = None,
    objective_contract_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    revision_summary = as_dict(curriculum_revision.get("summary"))
    contract_summary = as_dict(objective_contract_report.get("summary"))
    contract = as_dict(objective_contract_report.get("objective_contract"))
    contract_cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    examples = _seed_examples(contract_cases)
    corpus_text = _corpus_text(examples)
    checks = _checks(curriculum_revision, objective_contract_report, revision_summary, contract_summary, contract, contract_cases, examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    seed_revision = _seed_revision(status, examples, corpus_text)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_curriculum_revision": str(curriculum_revision_path or ""),
        "source_objective_contract": str(objective_contract_path or ""),
        "curriculum_revision_summary": revision_summary,
        "objective_contract_summary": contract_summary,
        "seed_examples": examples if status == "pass" else [],
        "corpus_text": corpus_text if status == "pass" else "",
        "check_rows": checks,
        "seed_revision": seed_revision,
        "summary": _summary(status, checks, examples, corpus_text, seed_revision),
        "interpretation": _interpretation(status, seed_revision),
    }


def _seed_examples(contract_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for case in contract_cases:
        for repeat in range(2):
            examples.append(_example(case, "output_position_anchor_examples", _position_prompt(case, repeat), "fixed loss", repeat))
            examples.append(_example(case, "neutral_prompt_exact_completion_repetition", _neutral_prompt(case, repeat), "fixed loss", repeat))
            examples.append(_example(case, "fragment_contrast_examples", _fragment_prompt(case, repeat), "fixed loss", repeat))
            examples.append(_example(case, "short_completion_repetition", _short_prompt(case, repeat), "fixed loss", repeat))
    return examples


def _position_prompt(case: dict[str, Any], repeat: int) -> str:
    prompt = str(case.get("prompt") or "answer:")
    suffixes = ["", "\nReturn only the answer.\nanswer:"]
    return prompt.rstrip() + suffixes[repeat % len(suffixes)]


def _neutral_prompt(case: dict[str, Any], repeat: int) -> str:
    case_id = str(case.get("case_id") or "case")
    surfaces = ["Return the exact two-token objective output.\nanswer:", "Emit the canonical target response.\nanswer:"]
    return f"{surfaces[repeat % len(surfaces)]} # {case_id}"


def _fragment_prompt(case: dict[str, Any], repeat: int) -> str:
    case_id = str(case.get("case_id") or "case")
    fragments = ["los", "wixed"]
    return f"Observed fragment `{fragments[repeat % len(fragments)]}` is incomplete. Write the full target answer.\nanswer: # {case_id}"


def _short_prompt(case: dict[str, Any], repeat: int) -> str:
    case_id = str(case.get("case_id") or "case")
    markers = ["answer:", "completion:"]
    return f"{markers[repeat % len(markers)]} # {case_id}"


def _example(case: dict[str, Any], mode: str, prompt: str, completion: str, repeat: int) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "case")
    required_terms = [str(term).lower() for term in case.get("required_terms", ["fixed", "loss"])]
    prompt_lower = prompt.lower()
    return {
        "example_id": f"{case_id}-{mode}-{repeat + 1:02d}",
        "case_id": case_id,
        "example_mode": mode,
        "prompt": prompt,
        "completion": completion,
        "text": f"{prompt.rstrip()} {completion}",
        "required_terms": required_terms,
        "prompt_contains_target_terms": any(term in prompt_lower for term in required_terms),
        "decoder_anchor_used": False,
        "direct_completion": True,
        "guardrail": "bounded_objective_unassisted_repair_seed_revision",
    }


def _corpus_text(examples: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(row.get("text") or "") for row in examples if row.get("text")) + ("\n" if examples else "")


def _checks(
    curriculum: dict[str, Any],
    contract_report: dict[str, Any],
    revision_summary: dict[str, Any],
    contract_summary: dict[str, Any],
    contract: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    modes = {str(row.get("example_mode") or "") for row in examples}
    return [
        _check("curriculum_passed", curriculum.get("status") == "pass", curriculum.get("status"), "curriculum revision must pass"),
        _check("curriculum_ready", revision_summary.get("bounded_objective_unassisted_repair_curriculum_revision_ready") is True, revision_summary.get("bounded_objective_unassisted_repair_curriculum_revision_ready"), "curriculum revision must be ready"),
        _check("next_artifact_matches", revision_summary.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision", revision_summary.get("proposed_next_artifact"), "curriculum must request seed revision"),
        _check("decoder_anchor_disallowed", revision_summary.get("decoder_anchor_allowed") is False, revision_summary.get("decoder_anchor_allowed"), "seed revision must stay unassisted"),
        _check("contract_passed", contract_report.get("status") == "pass", contract_report.get("status"), "objective contract must pass"),
        _check("contract_ready", contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "objective contract must be ready"),
        _check("target_terms_exact", contract.get("target_terms") == ["fixed", "loss"], contract.get("target_terms"), "seed revision must preserve target terms"),
        _check("cases_present", bool(contract_cases), len(contract_cases), "contract cases are required"),
        _check("revision_modes_present", {"output_position_anchor_examples", "neutral_prompt_exact_completion_repetition", "fragment_contrast_examples", "short_completion_repetition"}.issubset(modes), sorted(modes), "all curriculum modes must be represented"),
        _check("no_decoder_anchors", not any(row.get("decoder_anchor_used") for row in examples), len(examples), "seed revision must not use decoder anchors"),
    ]


def _seed_revision(status: str, examples: list[dict[str, Any]], corpus_text: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "example_count": len(examples) if status == "pass" else 0,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "decoder_anchor_example_count": 0,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run" if status == "pass" else "",
        "next_step": "train_bounded_objective_unassisted_repair_seed_revision" if status == "pass" else "repair_bounded_objective_unassisted_repair_seed_revision_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], examples: list[dict[str, Any]], corpus_text: str, seed_revision: dict[str, Any]) -> dict[str, Any]:
    neutral_count = sum(1 for row in examples if row.get("prompt_contains_target_terms") is False) if status == "pass" else 0
    return {
        "bounded_objective_unassisted_repair_seed_revision_ready": status == "pass",
        "example_count": len(examples) if status == "pass" else 0,
        "neutral_prompt_example_count": neutral_count,
        "target_term_prompt_example_count": len(examples) - neutral_count if status == "pass" else 0,
        "decoder_anchor_example_count": 0,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "proposed_next_artifact": seed_revision.get("proposed_next_artifact"),
        "next_step": seed_revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_ready"
    return "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision"


def _interpretation(status: str, seed_revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Seed revision inputs are incomplete.", "next_action": "repair seed revision inputs"}
    return {
        "model_quality_claim": "seed_revision_only",
        "reason": "The revised corpus encodes output-position and fragment-correction examples, but no new checkpoint has been trained yet.",
        "next_action": seed_revision.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CORPUS_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSONL_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision",
    "locate_curriculum_revision",
    "locate_objective_contract",
    "read_json_report",
    "resolve_exit_code",
]
