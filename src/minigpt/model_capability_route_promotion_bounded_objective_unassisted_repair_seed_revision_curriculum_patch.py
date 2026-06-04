from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSONL_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_examples.jsonl"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_corpus.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch.html"


def locate_partial_hit_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME
    return source


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed revision curriculum patch input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch(
    partial_hit_diagnostic: dict[str, Any],
    seed_revision: dict[str, Any],
    objective_contract: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    partial_hit_diagnostic_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    objective_contract_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision curriculum patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(partial_hit_diagnostic.get("summary"))
    seed_summary = as_dict(seed_revision.get("summary"))
    contract_summary = as_dict(objective_contract.get("summary"))
    contract = as_dict(objective_contract.get("objective_contract"))
    contract_cases = list_of_dicts(objective_contract.get("contract_cases"))
    original_corpus = Path(source_corpus_path).read_text(encoding="utf-8")
    examples = _patch_examples(contract, contract_cases)
    patch_corpus = _patch_corpus(original_corpus, examples)
    checks = _checks(partial_hit_diagnostic, diagnostic_summary, seed_revision, seed_summary, objective_contract, contract_summary, examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    patch = _patch(status, examples, patch_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_partial_hit_diagnostic": str(partial_hit_diagnostic_path or ""),
        "source_seed_revision": str(seed_revision_path or ""),
        "source_objective_contract": str(objective_contract_path or ""),
        "source_corpus": str(source_corpus_path),
        "partial_hit_diagnostic_summary": diagnostic_summary,
        "seed_revision_summary": seed_summary,
        "objective_contract_summary": contract_summary,
        "patch_examples": examples if status == "pass" else [],
        "patched_corpus_text": patch_corpus if status == "pass" else "",
        "check_rows": checks,
        "curriculum_patch": patch,
        "summary": _summary(status, checks, examples, original_corpus, patch_corpus, patch),
        "interpretation": _interpretation(status, patch),
    }


def resolve_exit_code(report: dict[str, Any], *, require_patch_ready: bool) -> int:
    return 1 if require_patch_ready and report.get("status") != "pass" else 0


def _patch_examples(contract: dict[str, Any], contract_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    target = str(contract.get("required_exact_completion") or "fixed loss")
    examples: list[dict[str, Any]] = []
    for case in contract_cases:
        case_id = str(case.get("case_id") or "case")
        prompt = str(case.get("prompt") or "answer:")
        examples.extend(_case_patch_examples(case_id, prompt, target))
    examples.extend(_loss_bridge_examples(target))
    return examples


def _case_patch_examples(case_id: str, prompt: str, target: str) -> list[dict[str, Any]]:
    clean_prompt = prompt.rstrip()
    return [
        _example(f"{case_id}-second-term-repeat-1", "loss_second_term_repeat", clean_prompt, target),
        _example(f"{case_id}-second-term-repeat-2", "loss_second_term_repeat", clean_prompt, target),
        _example(f"{case_id}-fixed-to-loss-bridge", "fixed_to_loss_bridge", f"{clean_prompt}\nfixed", "loss"),
        _example(f"{case_id}-full-completion-contrast", "full_completion_contrast", clean_prompt, f"{target}\nnot: fixed t"),
    ]


def _loss_bridge_examples(target: str) -> list[dict[str, Any]]:
    return [
        _example("loss-after-fixed-short", "loss_after_fixed_short", "fixed", "loss"),
        _example("loss-after-fixed-label", "loss_after_fixed_label", "Continue after fixed:", "loss"),
        _example("two-token-target-repeat-a", "two_token_target_repeat", "target:", target),
        _example("two-token-target-repeat-b", "two_token_target_repeat", "target:", target),
        _example("completion-surface-short-a", "completion_surface_short", "completion:", target),
        _example("completion-surface-short-b", "completion_surface_short", "completion:", target),
    ]


def _example(example_id: str, kind: str, prompt: str, completion: str) -> dict[str, Any]:
    text = f"{prompt}\n{completion}".strip()
    return {
        "example_id": example_id,
        "kind": kind,
        "prompt": prompt,
        "completion": completion,
        "text": text,
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "purpose": _purpose(kind),
    }


def _patch_corpus(original_corpus: str, examples: list[dict[str, Any]]) -> str:
    parts = [original_corpus.rstrip(), "# v855 curriculum patch"]
    parts.extend(str(example["text"]) for example in examples)
    return "\n\n".join(parts).strip() + "\n"


def _checks(
    diagnostic: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    seed: dict[str, Any],
    seed_summary: dict[str, Any],
    contract: dict[str, Any],
    contract_summary: dict[str, Any],
    examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "partial-hit diagnostic must pass"),
        _check("diagnostic_ready", diagnostic_summary.get("bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready") is True, diagnostic_summary.get("bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready"), "partial-hit diagnostic must be ready"),
        _check("partial_hit_present", int(diagnostic_summary.get("partial_hit_case_count") or 0) > 0, diagnostic_summary.get("partial_hit_case_count"), "patch should only follow a partial-hit diagnostic"),
        _check("seed_revision_ready", seed.get("status") == "pass" and seed_summary.get("bounded_objective_unassisted_repair_seed_revision_ready") is True, seed_summary.get("bounded_objective_unassisted_repair_seed_revision_ready"), "seed revision must be ready"),
        _check("contract_ready", contract.get("status") == "pass" and contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "objective contract must be ready"),
        _check("patch_examples_present", bool(examples), len(examples), "patch examples must be generated"),
        _check("decoder_anchor_free", all(example.get("decoder_anchor") is False for example in examples), False, "patch examples must stay no-anchor"),
    ]


def _patch(status: str, examples: list[dict[str, Any]], patch_corpus: str) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "patch_example_count": len(examples) if ready else 0,
        "loss_focus_example_count": sum(1 for example in examples if "loss" in str(example.get("completion")).lower()) if ready else 0,
        "completion_surface_example_count": sum(1 for example in examples if str(example.get("kind")) == "completion_surface_short") if ready else 0,
        "decoder_anchor_example_count": 0,
        "patched_corpus_char_count": len(patch_corpus) if ready else 0,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_run" if ready else "",
        "next_step": "train_bounded_objective_unassisted_repair_seed_revision_curriculum_patch" if ready else "repair_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_inputs",
    }


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    examples: list[dict[str, Any]],
    original_corpus: str,
    patch_corpus: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready": status == "pass",
        "patch_example_count": patch.get("patch_example_count"),
        "loss_focus_example_count": patch.get("loss_focus_example_count"),
        "completion_surface_example_count": patch.get("completion_surface_example_count"),
        "decoder_anchor_example_count": 0,
        "original_corpus_char_count": len(original_corpus),
        "patched_corpus_char_count": patch.get("patched_corpus_char_count"),
        "patch_kinds": sorted({str(example.get("kind")) for example in examples}) if status == "pass" else [],
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "model_quality_claim": "curriculum_patch_only" if status == "pass" else "not_claimed",
        "proposed_next_artifact": patch.get("proposed_next_artifact"),
        "next_step": patch.get("next_step"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_ready"
    return "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch"


def _interpretation(status: str, patch: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Curriculum patch inputs failed structural checks.", "next_action": patch.get("next_step")}
    return {
        "model_quality_claim": "curriculum_patch_only",
        "reason": "The patch targets loss second-term stabilization and completion-surface zero-hit cases; capability still requires training and replay.",
        "next_action": patch.get("next_step"),
    }


def _purpose(kind: str) -> str:
    purposes = {
        "loss_second_term_repeat": "repeat the full two-token target after the original contract prompt",
        "fixed_to_loss_bridge": "teach loss as the immediate continuation after fixed",
        "full_completion_contrast": "separate full fixed loss completion from fixed t near misses",
        "loss_after_fixed_short": "short bridge for the second required term",
        "loss_after_fixed_label": "labelled bridge for the second required term",
        "two_token_target_repeat": "repeat the exact target in a compact surface",
        "completion_surface_short": "repair completion-label prompt surface",
    }
    return purposes.get(kind, kind)


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CORPUS_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_JSONL_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_CURRICULUM_PATCH_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch",
    "locate_objective_contract",
    "locate_partial_hit_diagnostic",
    "locate_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
