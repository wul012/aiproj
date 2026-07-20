from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_plan import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_seed_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSONL_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.jsonl"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CORPUS_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_corpus.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed.html"


def locate_unassisted_repair_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_PLAN_JSON_FILENAME
    return source


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed(
    unassisted_repair_plan: dict[str, Any],
    objective_contract_report: dict[str, Any],
    *,
    repair_plan_path: str | Path | None = None,
    objective_contract_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed",
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan_summary = as_dict(unassisted_repair_plan.get("summary"))
    contract_summary = as_dict(objective_contract_report.get("summary"))
    contract = as_dict(objective_contract_report.get("objective_contract"))
    contract_cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    seed_examples = _seed_examples(contract_cases)
    corpus_text = _corpus_text(seed_examples)
    checks = _checks(unassisted_repair_plan, objective_contract_report, plan_summary, contract_summary, contract, contract_cases, seed_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    seed = _seed(status, contract, seed_examples, corpus_text)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_repair_plan": str(repair_plan_path or ""),
        "source_objective_contract": str(objective_contract_path or ""),
        "source_plan_summary": plan_summary,
        "source_contract_summary": contract_summary,
        "seed_examples": seed_examples if status == "pass" else [],
        "corpus_text": corpus_text if status == "pass" else "",
        "check_rows": checks,
        "seed": seed,
        "summary": _summary(status, issues, contract, seed_examples, corpus_text),
        "interpretation": _interpretation(status, seed),
    }


def _seed_examples(contract_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for case in contract_cases:
        for repeat in range(4):
            examples.append(_contract_prompt_example(case, repeat))
            examples.append(_neutral_prompt_example(case, repeat))
    return examples


def _contract_prompt_example(case: dict[str, Any], repeat: int) -> dict[str, Any]:
    prompt = str(case.get("prompt") or "")
    completion = str(case.get("expected_completion") or "fixed loss")
    return _example(
        case,
        mode="contract_prompt_unassisted_completion",
        prompt=prompt,
        completion=completion,
        repeat=repeat,
    )


def _neutral_prompt_example(case: dict[str, Any], repeat: int) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "case")
    neutral_surfaces = [
        "Return the bounded objective answer.\nanswer:",
        "Write the required two-token output.\nanswer:",
        "Emit the canonical repair target.\nanswer:",
        "Complete the objective response.\nanswer:",
    ]
    completion = str(case.get("expected_completion") or "fixed loss")
    return _example(
        case,
        mode="neutral_prompt_unassisted_completion",
        prompt=f"{neutral_surfaces[repeat % len(neutral_surfaces)]} # {case_id}",
        completion=completion,
        repeat=repeat,
    )


def _example(case: dict[str, Any], *, mode: str, prompt: str, completion: str, repeat: int) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "case")
    required_terms = [str(term).lower() for term in case.get("required_terms", ["fixed", "loss"])]
    prompt_lower = prompt.lower()
    return {
        "example_id": f"{case_id}-{mode}-{repeat + 1:02d}",
        "case_id": case_id,
        "example_mode": mode,
        "prompt": prompt,
        "completion": completion,
        "text": _training_text(prompt, completion),
        "required_terms": required_terms,
        "prompt_contains_target_terms": any(term in prompt_lower for term in required_terms),
        "decoder_anchor_used": False,
        "direct_completion": True,
        "guardrail": "bounded_objective_unassisted_repair_seed",
    }


def _training_text(prompt: str, completion: str) -> str:
    return f"{prompt.rstrip()} {completion.strip()}".strip()


def _corpus_text(seed_examples: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(row.get("text") or "") for row in seed_examples if row.get("text")) + ("\n" if seed_examples else "")


def _checks(
    plan: dict[str, Any],
    contract_report: dict[str, Any],
    plan_summary: dict[str, Any],
    contract_summary: dict[str, Any],
    contract: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    seed_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    neutral_count = sum(1 for row in seed_examples if row.get("prompt_contains_target_terms") is False)
    return [
        _check("repair_plan_passed", plan.get("status") == "pass", plan.get("status"), "source repair plan must pass"),
        _check("repair_plan_ready", plan_summary.get("bounded_objective_unassisted_repair_plan_ready") is True, plan_summary.get("bounded_objective_unassisted_repair_plan_ready"), "source repair plan must be ready"),
        _check("next_artifact_matches", plan_summary.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_objective_unassisted_repair_seed", plan_summary.get("proposed_next_artifact"), "plan must request unassisted repair seed"),
        _check("contract_passed", contract_report.get("status") == "pass", contract_report.get("status"), "source objective contract must pass"),
        _check("contract_ready", contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "source objective contract must be ready"),
        _check("target_terms_exact", contract.get("target_terms") == ["fixed", "loss"], contract.get("target_terms"), "seed must preserve fixed/loss target terms"),
        _check("contract_cases_present", bool(contract_cases), len(contract_cases), "seed needs objective contract cases"),
        _check("example_count_matches", len(seed_examples) == len(contract_cases) * 8, len(seed_examples), "seed must create 8 examples per case"),
        _check("neutral_prompts_present", neutral_count == len(contract_cases) * 4, neutral_count, "half of examples must avoid target terms in the prompt"),
        _check("no_decoder_anchors", not any(row.get("decoder_anchor_used") for row in seed_examples), len(seed_examples), "unassisted repair seed must not use decoder anchors"),
        _check("all_examples_have_required_terms", all(_contains_terms(row) for row in seed_examples), len(seed_examples), "every seed example text must contain fixed/loss"),
    ]


def _contains_terms(row: dict[str, Any]) -> bool:
    text = str(row.get("text") or "").lower()
    return "fixed" in text and "loss" in text


def _seed(status: str, contract: dict[str, Any], examples: list[dict[str, Any]], corpus_text: str) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "contract_id": contract.get("contract_id") if status == "pass" else "",
        "example_count": len(examples) if status == "pass" else 0,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_training_run" if status == "pass" else "",
        "next_step": "train_bounded_objective_unassisted_repair_seed" if status == "pass" else "repair_unassisted_repair_seed_inputs",
    }


def _summary(status: str, issues: list[dict[str, Any]], contract: dict[str, Any], examples: list[dict[str, Any]], corpus_text: str) -> dict[str, Any]:
    neutral_count = sum(1 for row in examples if row.get("prompt_contains_target_terms") is False) if status == "pass" else 0
    return {
        "bounded_objective_unassisted_repair_seed_ready": status == "pass",
        "contract_id": contract.get("contract_id") if status == "pass" else "",
        "target_terms": contract.get("target_terms") if status == "pass" else [],
        "example_count": len(examples) if status == "pass" else 0,
        "neutral_prompt_example_count": neutral_count,
        "target_term_prompt_example_count": len(examples) - neutral_count if status == "pass" else 0,
        "decoder_anchor_example_count": 0,
        "direct_example_count": sum(1 for row in examples if row.get("direct_completion") is True) if status == "pass" else 0,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "promotion_claim_allowed": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_training_run" if status == "pass" else "",
        "next_step": "train_bounded_objective_unassisted_repair_seed" if status == "pass" else "repair_unassisted_repair_seed_inputs",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_ready"
    return "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed"


def _interpretation(status: str, seed: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Unassisted repair seed inputs are incomplete.", "next_action": "repair unassisted repair seed inputs"}
    return {
        "model_quality_claim": "seed_only",
        "reason": "The corpus removes decoder anchors and adds neutral prompts, but capability still requires training and unassisted replay.",
        "next_action": seed.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CORPUS_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_JSONL_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed",
    "locate_objective_contract",
    "locate_unassisted_repair_plan",
    "read_json_report",
    "resolve_exit_code",
]
