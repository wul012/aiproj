from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_patch_ready as resolve_exit_code


TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch.json"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch.csv"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSONL_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_examples.jsonl"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_CORPUS_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_corpus.txt"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch.txt"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch.md"
)
TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch.html"
)


def locate_completion_surface_stabilization_partial_hit_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_COMPLETION_SURFACE_STABILIZATION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("stabilized loss-suffix uptake patch input must be a JSON object")
    return dict(payload)


def build_stabilized_loss_suffix_uptake_patch(
    partial_hit_diagnostic: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    partial_hit_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory stabilized loss-suffix uptake patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(partial_hit_diagnostic.get("summary"))
    diagnostic = as_dict(partial_hit_diagnostic.get("diagnostic"))
    case_rows = list_of_dicts(partial_hit_diagnostic.get("case_diagnostics"))
    source_path = Path(source_corpus_path)
    source_text = source_path.read_text(encoding="utf-8")
    patch_examples = _patch_examples(case_rows)
    patched_corpus = _patched_corpus(source_text, patch_examples)
    checks = _checks(partial_hit_diagnostic, diagnostic_summary, diagnostic, patch_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, diagnostic_summary, diagnostic, patch_examples, patched_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_partial_hit_diagnostic": str(partial_hit_diagnostic_path or ""),
        "source_corpus": str(source_path),
        "partial_hit_diagnostic_summary": diagnostic_summary,
        "diagnostic": diagnostic,
        "patch_examples": patch_examples,
        "patched_corpus_text": patched_corpus,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _patch_examples(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in case_rows:
        case_id = str(row.get("case_id") or "case")
        continuation = str(row.get("continuation") or "")
        examples.extend([
            _example(f"{case_id}-fixed-l-to-loss-a", "fixed_l_to_loss_uptake", "fixed l\nfixed loss", case_id, continuation),
            _example(f"{case_id}-fixed-l-to-loss-b", "fixed_l_to_loss_uptake", "fixed l fixed loss", case_id, continuation),
            _example(f"{case_id}-fixed-lo-to-loss", "fixed_lo_to_loss_uptake", "fixed lo\nfixed loss", case_id, continuation),
            _example(f"{case_id}-surface-pair", "surface_pair_carry_forward", _surface_text(case_id), case_id, continuation),
        ])
    suffix_templates = [
        "loss\nfixed loss",
        "l\nloss\nfixed loss",
        "lo\nloss\nfixed loss",
        "fixed\nloss\nfixed loss",
        "fixed l\nloss\nfixed loss",
        "fixed lo\nloss\nfixed loss",
    ]
    for idx, text in enumerate(suffix_templates, start=1):
        examples.append(_example(f"global-suffix-uptake-{idx}", "global_suffix_uptake", text, "global", ""))
    for idx, text in enumerate([
        "Answer with exactly two tokens: fixed loss\nanswer:\nfixed loss",
        "Answer with exactly two words: fixed loss\nanswer:\nfixed loss",
        "Complete with exactly two tokens: fixed loss\ncompletion:\nfixed loss",
        "Complete with exactly two words: fixed loss\ncompletion:\nfixed loss",
        "answer: fixed loss",
        "completion: fixed loss",
    ], start=1):
        examples.append(_example(f"surface-carry-forward-{idx}", "surface_pair_carry_forward", text, "global", ""))
    return examples


def _surface_text(case_id: str) -> str:
    if "completion" in case_id:
        return "Complete with exactly two tokens: fixed loss\ncompletion:\nfixed loss"
    if "minimal" in case_id:
        return "Answer with exactly two words: fixed loss\nanswer:\nfixed loss"
    return "Answer with exactly two tokens: fixed loss\nanswer:\nfixed loss"


def _example(example_id: str, kind: str, text: str, case_id: str, continuation: str) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "text": text,
        "completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": case_id,
        "source_continuation": continuation,
        "purpose": _purpose(kind),
    }


def _purpose(kind: str) -> str:
    purposes = {
        "fixed_l_to_loss_uptake": "push the stabilized fixed l prefix to the complete fixed loss pair",
        "fixed_lo_to_loss_uptake": "teach the intermediate fixed lo fragment to finish loss",
        "surface_pair_carry_forward": "preserve stabilized answer and completion surfaces while increasing suffix uptake",
        "global_suffix_uptake": "strengthen loss as the suffix after fixed fragments",
    }
    return purposes.get(kind, "repair stabilized loss suffix uptake")


def _patched_corpus(source_text: str, patch_examples: list[dict[str, Any]]) -> str:
    parts = [source_text.rstrip(), "# v884 stabilized loss-suffix uptake patch"]
    parts.extend(str(row["text"]) for row in patch_examples)
    return "\n\n".join(part for part in parts if part) + "\n"


def _checks(
    partial_hit_diagnostic: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    diagnostic: dict[str, Any],
    patch_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    suffix_count = sum(1 for row in patch_examples if str(row.get("kind")).endswith("uptake"))
    carry_count = sum(1 for row in patch_examples if row.get("kind") == "surface_pair_carry_forward")
    return [
        _check("diagnostic_passed", partial_hit_diagnostic.get("status") == "pass", partial_hit_diagnostic.get("status"), "partial-hit diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_completion_surface_stabilization_partial_hit_diagnostic_ready"),
            "completion-surface stabilization partial-hit diagnostic must be ready",
        ),
        _check("surface_stabilized", diagnostic_summary.get("completion_surface_stabilized") is True, diagnostic_summary.get("completion_surface_stabilized"), "surface must already be stabilized"),
        _check("all_fixed_l_partial", diagnostic_summary.get("all_cases_fixed_l_partial") is True, diagnostic_summary.get("all_cases_fixed_l_partial"), "all cases must be fixed-l partial"),
        _check("loss_still_missing", int(diagnostic_summary.get("loss_hit_case_count") or 0) == 0, diagnostic_summary.get("loss_hit_case_count"), "loss suffix must still be missing"),
        _check("suffix_gap", diagnostic.get("suffix_gap_after_surface_stabilization") is True, diagnostic.get("suffix_gap_after_surface_stabilization"), "diagnostic must identify suffix gap"),
        _check("patch_examples_present", bool(patch_examples), len(patch_examples), "patch needs examples"),
        _check("suffix_examples_dominate", suffix_count >= carry_count, {"suffix": suffix_count, "carry": carry_count}, "suffix uptake examples should dominate carry-forward examples"),
        _check("decoder_anchor_free", not any(row.get("decoder_anchor") for row in patch_examples), False, "patch must stay no-anchor"),
    ]


def _summary(
    status: str,
    diagnostic_summary: dict[str, Any],
    diagnostic: dict[str, Any],
    patch_examples: list[dict[str, Any]],
    patched_corpus: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_ready": ready,
        "patch_example_count": len(patch_examples),
        "fixed_l_to_loss_uptake_count": sum(1 for row in patch_examples if row["kind"] == "fixed_l_to_loss_uptake"),
        "fixed_lo_to_loss_uptake_count": sum(1 for row in patch_examples if row["kind"] == "fixed_lo_to_loss_uptake"),
        "global_suffix_uptake_count": sum(1 for row in patch_examples if row["kind"] == "global_suffix_uptake"),
        "surface_pair_carry_forward_count": sum(1 for row in patch_examples if row["kind"] == "surface_pair_carry_forward"),
        "decoder_anchor_example_count": 0,
        "source_fixed_l_partial_case_count": diagnostic_summary.get("fixed_l_partial_case_count"),
        "source_loss_hit_case_count": diagnostic_summary.get("loss_hit_case_count"),
        "patched_corpus_char_count": len(patched_corpus),
        "model_quality_claim": "stabilized_loss_suffix_uptake_patch_only",
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch" if ready else "repair_stabilized_loss_suffix_uptake_patch_inputs",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_patch"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Stabilized loss-suffix uptake patch inputs failed.", "next_action": "repair_stabilized_loss_suffix_uptake_patch_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The patch targets loss suffix uptake after every contract surface stabilized at fixed l.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_CORPUS_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_JSONL_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_STABILIZED_LOSS_SUFFIX_UPTAKE_PATCH_TEXT_FILENAME",
    "build_stabilized_loss_suffix_uptake_patch",
    "locate_completion_surface_stabilization_partial_hit_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
