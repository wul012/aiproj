from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic import (
    TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch.json"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch.csv"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSONL_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_examples.jsonl"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_CORPUS_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_corpus.txt"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch.txt"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch.md"
)
TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch.html"
)


def locate_loss_suffix_replay_regression_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_LOSS_SUFFIX_REPLAY_REGRESSION_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective completion-surface stabilization patch input must be a JSON object")
    return dict(payload)


def build_completion_surface_stabilization_patch(
    regression_diagnostic: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    regression_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory completion-surface stabilization patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(regression_diagnostic.get("summary"))
    regression = as_dict(regression_diagnostic.get("regression"))
    current_cases = list_of_dicts(regression_diagnostic.get("current_case_diagnostics"))
    baseline_cases = list_of_dicts(regression_diagnostic.get("baseline_case_diagnostics"))
    source_path = Path(source_corpus_path)
    source_text = source_path.read_text(encoding="utf-8")
    patch_examples = _patch_examples(current_cases, baseline_cases)
    patched_corpus = _patched_corpus(source_text, patch_examples)
    checks = _checks(regression_diagnostic, diagnostic_summary, regression, patch_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, diagnostic_summary, regression, patch_examples, patched_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_regression_diagnostic": str(regression_diagnostic_path or ""),
        "source_corpus": str(source_path),
        "regression_diagnostic_summary": diagnostic_summary,
        "regression": regression,
        "patch_examples": patch_examples,
        "patched_corpus_text": patched_corpus,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_patch_ready: bool) -> int:
    return 1 if require_patch_ready and report.get("status") != "pass" else 0


def _patch_examples(current_cases: list[dict[str, Any]], baseline_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completion_case = _case_by_id(current_cases, "completion_label_surface")
    baseline_completion = _case_by_id(baseline_cases, "completion_label_surface")
    examples: list[dict[str, Any]] = []
    completion_templates = [
        "Complete with exactly two tokens: fixed loss\ncompletion:\nfixed loss",
        "Complete with exactly two tokens: fixed loss\ncompletion: fixed loss",
        "Complete with exactly two words: fixed loss\ncompletion:\nfixed loss",
        "Complete with exactly two words: fixed loss\ncompletion: fixed loss",
        "completion:\nfixed loss",
        "completion: fixed loss",
        "Complete the target pair.\ncompletion:\nfixed loss",
        "Required output: fixed loss\ncompletion:\nfixed loss",
        "Complete with the exact answer.\ncompletion: fixed loss",
        "Complete with no label echo.\ncompletion:\nfixed loss",
        "Complete the phrase fixed loss.\ncompletion:\nfixed loss",
        "Complete the phrase fixed loss.\ncompletion: fixed loss",
    ]
    for idx, text in enumerate(completion_templates, start=1):
        examples.append(_example(f"completion-surface-stabilization-{idx}", "completion_surface_stabilization", text, "completion_label_surface", completion_case))

    answer_templates = [
        "Answer with exactly two tokens: fixed loss\nanswer:\nfixed loss",
        "Answer with exactly two tokens: fixed loss\nanswer: fixed loss",
        "Answer with exactly two words: fixed loss\nanswer:\nfixed loss",
        "Answer with exactly two words: fixed loss\nanswer: fixed loss",
        "answer:\nfixed loss",
        "answer: fixed loss",
    ]
    for idx, text in enumerate(answer_templates, start=1):
        source_case = "canonical_direct_completion" if idx <= 2 else "minimal_direct_completion"
        examples.append(_example(f"answer-surface-carry-forward-{idx}", "answer_surface_carry_forward", text, source_case, _case_by_id(current_cases, source_case)))

    bridge_templates = [
        "fixed l\nfixed loss",
        "fixed lo\nfixed loss",
        "fixed\nloss\nfixed loss",
        "completion:\nfixed l\nfixed loss",
        "completion:\nfixed lo\nfixed loss",
        "answer:\nfixed l\nfixed loss",
    ]
    for idx, text in enumerate(bridge_templates, start=1):
        source_case = "completion_label_surface" if idx <= 5 else "canonical_direct_completion"
        examples.append(_example(f"prefix-fragment-bridge-{idx}", "prefix_fragment_bridge", text, source_case, completion_case))

    anti_fragment_templates = [
        "Complete with exactly two tokens: fixed loss\ncompletion:\nfixed loss\nfixed loss",
        "Complete with exactly two tokens: fixed loss\ncompletion: fixed loss\nfixed loss",
        "Complete with exactly two words: fixed loss\ncompletion:\nfixed loss\nfixed loss",
        "Complete with exactly two words: fixed loss\ncompletion: fixed loss\nfixed loss",
    ]
    for idx, text in enumerate(anti_fragment_templates, start=1):
        examples.append(_example(f"completion-fragment-resistance-{idx}", "completion_fragment_resistance", text, "completion_label_surface", baseline_completion))
    return examples


def _example(example_id: str, kind: str, text: str, case_id: str, source_case: dict[str, Any]) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "text": text,
        "completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": case_id,
        "source_case_label": source_case.get("label", ""),
        "source_continuation": source_case.get("continuation", ""),
        "purpose": _purpose(kind),
    }


def _purpose(kind: str) -> str:
    purposes = {
        "completion_surface_stabilization": "teach completion-label prompts to emit the exact fixed loss pair without answer-label drift",
        "answer_surface_carry_forward": "preserve canonical and minimal answer surfaces while repairing completion prompts",
        "prefix_fragment_bridge": "bridge fixed l and fixed lo fragments to the complete fixed loss pair",
        "completion_fragment_resistance": "repeat the correct completion surface to resist the observed an: fix fragment",
    }
    return purposes.get(kind, "repair completion surface regression")


def _case_by_id(rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("case_id") == case_id:
            return row
    return {}


def _patched_corpus(source_text: str, patch_examples: list[dict[str, Any]]) -> str:
    parts = [source_text.rstrip(), "# v880 target-only memory completion-surface stabilization patch"]
    parts.extend(str(row["text"]) for row in patch_examples)
    return "\n\n".join(part for part in parts if part) + "\n"


def _checks(
    regression_diagnostic: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    regression: dict[str, Any],
    patch_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    completion_count = sum(1 for row in patch_examples if row.get("kind") == "completion_surface_stabilization")
    answer_count = sum(1 for row in patch_examples if row.get("kind") == "answer_surface_carry_forward")
    return [
        _check("diagnostic_passed", regression_diagnostic.get("status") == "pass", regression_diagnostic.get("status"), "regression diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_regression_diagnostic_ready"),
            "loss-suffix replay regression diagnostic must be ready",
        ),
        _check("sample_contract_gap", diagnostic_summary.get("sample_contract_gap") is True, diagnostic_summary.get("sample_contract_gap"), "patch only applies when sample success and contract failure coexist"),
        _check("completion_regressed_to_zero", regression.get("completion_surface_regressed_to_zero") is True, regression.get("completion_surface_regressed_to_zero"), "completion surface must be the regressed surface"),
        _check("zero_hit_delta_positive", int(regression.get("zero_hit_delta") or 0) > 0, regression.get("zero_hit_delta"), "patch expects a zero-hit regression against baseline"),
        _check("patch_examples_present", bool(patch_examples), len(patch_examples), "completion surface patch needs examples"),
        _check("completion_surface_dominates", completion_count >= answer_count, {"completion": completion_count, "answer": answer_count}, "completion stabilization should dominate carry-forward examples"),
        _check("decoder_anchor_free", not any(row.get("decoder_anchor") for row in patch_examples), False, "patch must stay no-anchor"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    diagnostic_summary: dict[str, Any],
    regression: dict[str, Any],
    patch_examples: list[dict[str, Any]],
    patched_corpus: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_ready": ready,
        "patch_example_count": len(patch_examples),
        "completion_surface_example_count": sum(1 for row in patch_examples if row["kind"] == "completion_surface_stabilization"),
        "answer_surface_carry_forward_count": sum(1 for row in patch_examples if row["kind"] == "answer_surface_carry_forward"),
        "prefix_fragment_bridge_count": sum(1 for row in patch_examples if row["kind"] == "prefix_fragment_bridge"),
        "completion_fragment_resistance_count": sum(1 for row in patch_examples if row["kind"] == "completion_fragment_resistance"),
        "decoder_anchor_example_count": 0,
        "source_sample_contract_gap": diagnostic_summary.get("sample_contract_gap"),
        "source_zero_hit_delta": regression.get("zero_hit_delta"),
        "source_any_hit_delta": regression.get("any_hit_delta"),
        "patched_corpus_char_count": len(patched_corpus),
        "model_quality_claim": "completion_surface_stabilization_patch_only",
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch" if ready else "repair_completion_surface_stabilization_patch_inputs",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_patch"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Completion-surface stabilization patch inputs failed.", "next_action": "repair_completion_surface_stabilization_patch_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The patch targets the completion-label zero-hit regression while carrying forward answer surfaces.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_CORPUS_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_JSONL_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PATCH_TEXT_FILENAME",
    "build_completion_surface_stabilization_patch",
    "locate_loss_suffix_replay_regression_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
