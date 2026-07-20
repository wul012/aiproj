from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic import (
    TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison import (
    TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_patch_ready as resolve_exit_code


TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.json"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.csv"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSONL_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_examples.jsonl"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_CORPUS_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_corpus.txt"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.txt"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.md"
)
TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch.html"
)


def locate_partial_hit_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge target-only memory loss-suffix patch input must be a JSON object")
    return dict(payload)


def build_loss_suffix_patch(
    partial_hit_diagnostic: dict[str, Any],
    replay_comparison: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    partial_hit_diagnostic_path: str | Path | None = None,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory loss-suffix patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(partial_hit_diagnostic.get("summary"))
    replay_summary = as_dict(replay_comparison.get("summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    source_path = Path(source_corpus_path)
    source_text = source_path.read_text(encoding="utf-8")
    patch_examples = _patch_examples(replay_rows)
    patched_corpus = _patched_corpus(source_text, patch_examples)
    checks = _checks(partial_hit_diagnostic, replay_comparison, diagnostic_summary, replay_summary, patch_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, diagnostic_summary, replay_summary, patch_examples, patched_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_partial_hit_diagnostic": str(partial_hit_diagnostic_path or ""),
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_corpus": str(source_path),
        "partial_hit_diagnostic_summary": diagnostic_summary,
        "replay_summary": replay_summary,
        "patch_examples": patch_examples,
        "patched_corpus_text": patched_corpus,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _patch_examples(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in replay_rows:
        case_id = str(row.get("case_id") or "case")
        continuation = str(row.get("continuation") or "")
        label = "completion" if "completion" in case_id else "answer"
        examples.extend([
            _example(f"{case_id}-target-pair-a", "target_pair_memory", "fixed loss", case_id, continuation),
            _example(f"{case_id}-target-pair-b", "target_pair_memory", "fixed loss", case_id, continuation),
            _example(f"{case_id}-loss-suffix", "loss_suffix_memory", "loss", case_id, continuation),
            _example(f"{case_id}-prefix-bridge", "loss_prefix_bridge", "fixed l\nloss\nfixed loss", case_id, continuation),
            _example(f"{case_id}-label-pair", "minimal_label_pair", f"{label}:\nfixed loss", case_id, continuation),
        ])
    for idx in range(1, 7):
        examples.append(_example(f"global-loss-memory-{idx}", "loss_suffix_memory", "loss", "global", ""))
    for idx in range(1, 7):
        examples.append(_example(f"global-fixed-loss-pair-{idx}", "target_pair_memory", "fixed loss", "global", ""))
    return examples


def _example(example_id: str, kind: str, text: str, case_id: str, continuation: str) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "text": text,
        "completion": "fixed loss" if "pair" in kind or kind == "loss_prefix_bridge" else "loss",
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": case_id,
        "source_continuation": continuation,
        "purpose": _purpose(kind),
    }


def _purpose(kind: str) -> str:
    purposes = {
        "target_pair_memory": "reinforce the complete fixed loss pair after fixed-prefix recovery",
        "loss_suffix_memory": "strengthen the missing loss suffix token",
        "loss_prefix_bridge": "bridge the observed fixed l partial continuation to complete fixed loss",
        "minimal_label_pair": "keep a minimal replay-label to complete-pair bridge",
    }
    return purposes.get(kind, "repair target-only memory loss suffix gap")


def _patched_corpus(source_text: str, patch_examples: list[dict[str, Any]]) -> str:
    parts = [source_text.rstrip(), "# v876 target-only memory loss-suffix patch"]
    parts.extend(str(row["text"]) for row in patch_examples)
    return "\n\n".join(part for part in parts if part) + "\n"


def _checks(
    partial_hit_diagnostic: dict[str, Any],
    replay_comparison: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    replay_summary: dict[str, Any],
    patch_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", partial_hit_diagnostic.get("status") == "pass", partial_hit_diagnostic.get("status"), "partial-hit diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_partial_hit_diagnostic_ready"),
            "target-only memory partial-hit diagnostic must be ready",
        ),
        _check("all_cases_loss_prefix", diagnostic_summary.get("all_cases_loss_prefix") is True, diagnostic_summary.get("all_cases_loss_prefix"), "patch only applies when every case reaches the loss prefix"),
        _check("no_loss_hit_yet", int(diagnostic_summary.get("loss_hit_case_count") or 0) == 0, diagnostic_summary.get("loss_hit_case_count"), "loss suffix patch only applies before loss hits are present"),
        _check("replay_passed", replay_comparison.get("status") == "pass", replay_comparison.get("status"), "replay comparison must pass"),
        _check("replay_partial_hit", int(replay_summary.get("any_hit_case_count") or 0) > 0, replay_summary.get("any_hit_case_count"), "replay must contain partial hits"),
        _check("patch_examples_present", bool(patch_examples), len(patch_examples), "loss suffix patch needs examples"),
        _check("decoder_anchor_free", not any(row.get("decoder_anchor") for row in patch_examples), False, "patch must stay no-anchor"),
    ]


def _summary(
    status: str,
    diagnostic_summary: dict[str, Any],
    replay_summary: dict[str, Any],
    patch_examples: list[dict[str, Any]],
    patched_corpus: str,
) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready": ready,
        "patch_example_count": len(patch_examples),
        "target_pair_example_count": sum(1 for row in patch_examples if row["kind"] == "target_pair_memory"),
        "loss_suffix_example_count": sum(1 for row in patch_examples if row["kind"] == "loss_suffix_memory"),
        "loss_prefix_bridge_example_count": sum(1 for row in patch_examples if row["kind"] == "loss_prefix_bridge"),
        "minimal_label_pair_example_count": sum(1 for row in patch_examples if row["kind"] == "minimal_label_pair"),
        "decoder_anchor_example_count": 0,
        "source_loss_prefix_case_count": diagnostic_summary.get("loss_prefix_case_count"),
        "source_any_hit_case_count": replay_summary.get("any_hit_case_count"),
        "patched_corpus_char_count": len(patched_corpus),
        "model_quality_claim": "loss_suffix_patch_only",
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch" if ready else "repair_loss_suffix_patch_inputs",
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_ready"
    return "fix_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Loss-suffix patch inputs failed.", "next_action": "repair_loss_suffix_patch_inputs"}
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The patch targets the missing loss suffix after replay consistently reached fixed l.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_CORPUS_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_JSONL_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_SUFFIX_PATCH_TEXT_FILENAME",
    "build_loss_suffix_patch",
    "locate_partial_hit_diagnostic",
    "locate_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
