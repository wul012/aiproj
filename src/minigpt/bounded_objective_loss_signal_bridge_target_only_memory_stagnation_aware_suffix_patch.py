from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_patch_ready as resolve_exit_code


TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.json"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.csv"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSONL_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_examples.jsonl"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_CORPUS_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_corpus.txt"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.txt"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.md"
)
TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch.html"
)


CONTRACT_SURFACES = [
    ("canonical_direct_completion", "Answer with exactly two tokens: fixed loss\nanswer:"),
    ("minimal_direct_completion", "Answer with exactly two words: fixed loss\nanswer:"),
    ("completion_label_surface", "Complete with exactly two tokens: fixed loss\ncompletion:"),
]


def locate_stagnation_aware_suffix_repair_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPAIR_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("stagnation-aware suffix patch input must be a JSON object")
    return dict(payload)


def build_stagnation_aware_suffix_patch(
    repair_plan: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    repair_plan_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory stagnation-aware suffix patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan_summary = as_dict(repair_plan.get("summary"))
    plan_actions = list_of_dicts(repair_plan.get("plan_actions"))
    source_path = Path(source_corpus_path)
    source_text = source_path.read_text(encoding="utf-8")
    patch_examples = _patch_examples(plan_actions)
    patched_corpus = _patched_corpus(source_text, patch_examples)
    checks = _checks(repair_plan, plan_summary, plan_actions, patch_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, plan_summary, patch_examples, patched_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_repair_plan": str(repair_plan_path or ""),
        "source_corpus": str(source_path),
        "repair_plan_summary": plan_summary,
        "repair_plan_actions": plan_actions,
        "contract_surfaces": [{"case_id": case_id, "prompt": prompt} for case_id, prompt in CONTRACT_SURFACES],
        "patch_examples": patch_examples,
        "patched_corpus_text": patched_corpus,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _patch_examples(plan_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    action_ids = {str(row.get("action_id")) for row in plan_actions}
    for case_id, prompt in CONTRACT_SURFACES:
        examples.extend([
            _example(f"{case_id}-space-exact", "replay_prompt_boundary", f"{prompt} fixed loss", case_id, "space exact contract completion"),
            _example(f"{case_id}-newline-exact", "replay_prompt_boundary", f"{prompt}\nfixed loss", case_id, "newline exact contract completion"),
            _example(f"{case_id}-fixed-l-loss-space", "suffix_position", f"{prompt} fixed l\nloss\nfixed loss", case_id, "force loss after fixed-l fragment"),
            _example(f"{case_id}-fixed-l-loss-newline", "suffix_position", f"{prompt}\nfixed l\nloss\nfixed loss", case_id, "force loss after newline fixed-l fragment"),
            _example(f"{case_id}-fixed-lo-loss-space", "suffix_position", f"{prompt} fixed lo\nloss\nfixed loss", case_id, "force loss after fixed-lo fragment"),
            _example(f"{case_id}-fixed-lo-loss-newline", "suffix_position", f"{prompt}\nfixed lo\nloss\nfixed loss", case_id, "force loss after newline fixed-lo fragment"),
        ])
    examples.extend([
        _example("surface-answer-space", "surface_format", "answer: fixed loss", "global", "preserve space answer surface"),
        _example("surface-answer-newline", "surface_format", "answer:\nfixed loss", "global", "preserve newline answer surface"),
        _example("surface-completion-space", "surface_format", "completion: fixed loss", "global", "preserve space completion surface"),
        _example("surface-completion-newline", "surface_format", "completion:\nfixed loss", "global", "preserve newline completion surface"),
        _example("suffix-ratio-fixed-l-a", "training_corpus_ratio", "fixed l\nloss\nfixed loss", "global", "increase suffix uptake density"),
        _example("suffix-ratio-fixed-l-b", "training_corpus_ratio", "fixed l fixed loss", "global", "increase suffix uptake density"),
        _example("suffix-ratio-fixed-lo-a", "training_corpus_ratio", "fixed lo\nloss\nfixed loss", "global", "increase suffix uptake density"),
        _example("suffix-ratio-fixed-lo-b", "training_corpus_ratio", "fixed lo fixed loss", "global", "increase suffix uptake density"),
    ])
    for action_id in sorted(action_ids):
        if action_id == "contract-gated-training-stop":
            examples.append(_example("verification-gate-note", "verification_gate", "sample success is not contract recovery\nreplay fixed loss before promotion", "global", "keep replay gate explicit"))
            break
    return examples


def _example(example_id: str, kind: str, text: str, case_id: str, purpose: str) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "text": text,
        "completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": case_id,
        "purpose": purpose,
    }


def _patched_corpus(source_text: str, patch_examples: list[dict[str, Any]]) -> str:
    parts = [source_text.rstrip(), "# v889 stagnation-aware suffix patch"]
    parts.extend(str(row["text"]) for row in patch_examples)
    return "\n\n".join(part for part in parts if part) + "\n"


def _checks(
    repair_plan: dict[str, Any],
    plan_summary: dict[str, Any],
    plan_actions: list[dict[str, Any]],
    patch_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    category_counts = _category_counts(patch_examples)
    suffix_count = category_counts["suffix_position"] + category_counts["training_corpus_ratio"]
    surface_count = category_counts["surface_format"]
    return [
        _check("plan_passed", repair_plan.get("status") == "pass", repair_plan.get("status"), "repair plan must pass"),
        _check("plan_ready", plan_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready") is True, plan_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_ready"), "repair plan must be ready"),
        _check("plan_actions_present", len(plan_actions) >= 5, len(plan_actions), "repair plan actions must be present"),
        _check("contract_surfaces_covered", _surface_coverage(patch_examples) == len(CONTRACT_SURFACES), _surface_coverage(patch_examples), "all contract surfaces must be represented"),
        _check("suffix_examples_dominate", suffix_count >= surface_count * 2, {"suffix": suffix_count, "surface": surface_count}, "suffix examples should dominate surface examples"),
        _check("format_pairs_present", surface_count >= 4, surface_count, "space and newline surface pairs must be present"),
        _check("decoder_anchor_free", not any(row.get("decoder_anchor") for row in patch_examples), False, "patch must stay no-anchor"),
        _check("verification_gate_present", category_counts["verification_gate"] >= 1, category_counts["verification_gate"], "patch must carry the replay verification gate"),
    ]


def _category_counts(examples: list[dict[str, Any]]) -> dict[str, int]:
    categories = ["replay_prompt_boundary", "suffix_position", "surface_format", "training_corpus_ratio", "verification_gate"]
    return {category: sum(1 for row in examples if row["kind"] == category) for category in categories}


def _surface_coverage(examples: list[dict[str, Any]]) -> int:
    return len({row["source_case_id"] for row in examples if row["source_case_id"] != "global"})


def _summary(status: str, plan_summary: dict[str, Any], patch_examples: list[dict[str, Any]], patched_corpus: str) -> dict[str, Any]:
    counts = _category_counts(patch_examples)
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_ready": status == "pass",
        "patch_example_count": len(patch_examples),
        "replay_prompt_boundary_example_count": counts["replay_prompt_boundary"],
        "suffix_position_example_count": counts["suffix_position"],
        "surface_format_example_count": counts["surface_format"],
        "training_corpus_ratio_example_count": counts["training_corpus_ratio"],
        "verification_gate_example_count": counts["verification_gate"],
        "decoder_anchor_example_count": 0,
        "source_plan_action_count": plan_summary.get("action_count"),
        "source_no_contract_gain_confirmed": plan_summary.get("source_no_contract_gain_confirmed"),
        "patched_corpus_char_count": len(patched_corpus),
        "model_quality_claim": "stagnation_aware_suffix_patch_only",
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run" if status == "pass" else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch" if status == "pass" else "repair_stagnation_aware_suffix_patch_inputs",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Stagnation-aware suffix patch inputs failed.", "next_action": "repair_stagnation_aware_suffix_patch_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The patch materializes the no-contract-gain repair plan into exact contract prompts, suffix-position bridges, format pairs, and a replay gate.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "CONTRACT_SURFACES",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_CORPUS_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_JSONL_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_PATCH_TEXT_FILENAME",
    "build_stagnation_aware_suffix_patch",
    "locate_stagnation_aware_suffix_repair_plan",
    "read_json_report",
    "resolve_exit_code",
]
