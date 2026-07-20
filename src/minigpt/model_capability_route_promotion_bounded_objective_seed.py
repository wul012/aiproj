from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_SEED_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_seed.json"
BOUNDED_OBJECTIVE_SEED_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_seed.csv"
BOUNDED_OBJECTIVE_SEED_JSONL_FILENAME = "model_capability_route_promotion_bounded_objective_seed.jsonl"
BOUNDED_OBJECTIVE_SEED_CORPUS_FILENAME = "model_capability_route_promotion_bounded_objective_seed_corpus.txt"
BOUNDED_OBJECTIVE_SEED_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_seed.txt"
BOUNDED_OBJECTIVE_SEED_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_seed.md"
BOUNDED_OBJECTIVE_SEED_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_seed.html"


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective seed input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_seed(
    objective_contract_report: dict[str, Any],
    *,
    objective_contract_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective seed",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(objective_contract_report.get("summary"))
    contract = as_dict(objective_contract_report.get("objective_contract"))
    contract_cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    seed_blueprint = as_dict(objective_contract_report.get("seed_blueprint"))
    seed_examples = _seed_examples(contract_cases, seed_blueprint)
    corpus_text = _corpus_text(seed_examples)
    checks = _checks(objective_contract_report, summary, contract, contract_cases, seed_blueprint, seed_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_objective_contract": str(objective_contract_path or ""),
        "source_contract_summary": summary,
        "seed_examples": seed_examples if status == "pass" else [],
        "corpus_text": corpus_text if status == "pass" else "",
        "check_rows": checks,
        "seed": _seed(status, contract, seed_examples, corpus_text),
        "summary": _summary(status, issues, contract, seed_examples, corpus_text),
        "interpretation": _interpretation(status),
    }


def resolve_exit_code(report: dict[str, Any], *, require_seed_ready: bool) -> int:
    if require_seed_ready and report.get("status") != "pass":
        return 1
    return 0


def _seed_examples(contract_cases: list[dict[str, Any]], seed_blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    examples_per_case = int(seed_blueprint.get("examples_per_case") or 0)
    examples = []
    for case_index, case in enumerate(contract_cases):
        mode = _mode_for_case(case_index)
        for repeat in range(examples_per_case):
            examples.append(_example(case, mode, repeat))
    return examples


def _mode_for_case(case_index: int) -> str:
    modes = ["direct_prompt_completion", "minimal_surface_repeat", "label_surface_repeat"]
    return modes[case_index % len(modes)]


def _example(case: dict[str, Any], mode: str, repeat: int) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "case")
    prompt = str(case.get("prompt") or "")
    completion = str(case.get("expected_completion") or "")
    return {
        "example_id": f"{case_id}-{mode}-{repeat + 1:02d}",
        "case_id": case_id,
        "example_mode": mode,
        "prompt": prompt,
        "completion": completion,
        "text": _training_text(prompt, completion),
        "required_terms": list(case.get("required_terms") or ["fixed", "loss"]),
        "surface": case.get("surface"),
        "direct_completion": True,
        "guardrail": "bounded_objective_contract_direct_seed",
    }


def _training_text(prompt: str, completion: str) -> str:
    return f"{prompt.rstrip()} {completion.strip()}".strip()


def _corpus_text(seed_examples: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(row.get("text") or "") for row in seed_examples if row.get("text")) + ("\n" if seed_examples else "")


def _checks(
    source: dict[str, Any],
    summary: dict[str, Any],
    contract: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    seed_blueprint: dict[str, Any],
    seed_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    planned_count = seed_blueprint.get("planned_example_count")
    return [
        _check("contract_passed", source.get("status") == "pass", source.get("status"), "source objective contract must pass"),
        _check("contract_ready", summary.get("bounded_objective_contract_ready") is True, summary.get("bounded_objective_contract_ready"), "source objective contract must be ready"),
        _check("next_artifact_matches", summary.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_objective_seed", summary.get("proposed_next_artifact"), "source contract must request objective seed"),
        _check("target_terms_exact", contract.get("target_terms") == ["fixed", "loss"], contract.get("target_terms"), "seed must preserve fixed/loss target terms"),
        _check("contract_cases_match_summary", len(contract_cases) == summary.get("contract_case_count"), {"cases": len(contract_cases), "summary": summary.get("contract_case_count")}, "contract case count must match summary"),
        _check("planned_count_matches", len(seed_examples) == planned_count == 18, {"examples": len(seed_examples), "planned": planned_count}, "seed examples must match deterministic blueprint"),
        _check("all_examples_direct", all(row.get("direct_completion") is True for row in seed_examples), len(seed_examples), "all seed examples must be direct-completion rows"),
        _check("no_carry_forward_examples", not any("carry" in str(row.get("example_mode")) for row in seed_examples), [row.get("example_mode") for row in seed_examples], "objective seed must not contain carry-forward rows"),
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
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_training_run" if status == "pass" else "",
        "next_step": "train_bounded_objective_seed" if status == "pass" else "repair_bounded_objective_seed_inputs",
    }


def _summary(
    status: str,
    issues: list[dict[str, Any]],
    contract: dict[str, Any],
    examples: list[dict[str, Any]],
    corpus_text: str,
) -> dict[str, Any]:
    modes = sorted({str(row.get("example_mode")) for row in examples}) if status == "pass" else []
    return {
        "bounded_objective_seed_ready": status == "pass",
        "contract_id": contract.get("contract_id") if status == "pass" else "",
        "target_terms": contract.get("target_terms") if status == "pass" else [],
        "example_count": len(examples) if status == "pass" else 0,
        "direct_example_count": sum(1 for row in examples if row.get("direct_completion") is True) if status == "pass" else 0,
        "carry_forward_example_count": 0,
        "example_modes": modes,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "promotion_claim_allowed": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_training_run" if status == "pass" else "",
        "failed_check_count": len(issues),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_seed_ready"
    return "fix_model_capability_route_promotion_bounded_objective_seed"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Objective seed inputs are incomplete.", "next_action": "repair objective seed inputs"}
    return {
        "model_quality_claim": "seed_only",
        "reason": "The corpus is direct and bounded; capability still requires controlled training and replay.",
        "next_action": "model_capability_route_promotion_bounded_objective_training_run",
    }


__all__ = [
    "BOUNDED_OBJECTIVE_SEED_CORPUS_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_JSONL_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_SEED_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_seed",
    "locate_objective_contract",
    "read_json_report",
    "resolve_exit_code",
]
