from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic import (
    SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_patch_ready as resolve_exit_code


TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch.json"
TARGET_ONLY_MEMORY_PATCH_CSV_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch.csv"
TARGET_ONLY_MEMORY_PATCH_JSONL_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch_examples.jsonl"
TARGET_ONLY_MEMORY_PATCH_CORPUS_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch_corpus.txt"
TARGET_ONLY_MEMORY_PATCH_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch.txt"
TARGET_ONLY_MEMORY_PATCH_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch.md"
TARGET_ONLY_MEMORY_PATCH_HTML_FILENAME = "bounded_objective_loss_signal_bridge_target_only_memory_patch.html"


def locate_zero_hit_diagnostic(path: str | Path) -> Path:
    return _locate(path, SINGLE_LINE_SURFACE_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME)


def locate_replay_comparison(path: str | Path) -> Path:
    return _locate(path, LOSS_SIGNAL_BRIDGE_SINGLE_LINE_SURFACE_REPLAY_COMPARISON_JSON_FILENAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("target-only memory patch input must be a JSON object")
    return dict(payload)


def build_target_only_memory_patch(
    zero_hit_diagnostic: dict[str, Any],
    replay_comparison: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    zero_hit_diagnostic_path: str | Path | None = None,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(zero_hit_diagnostic.get("summary"))
    replay_summary = as_dict(replay_comparison.get("summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    case_diagnostics = list_of_dicts(zero_hit_diagnostic.get("case_diagnostics"))
    source_corpus = Path(source_corpus_path).read_text(encoding="utf-8")
    examples = _patch_examples(replay_rows, case_diagnostics)
    patched_corpus = _patched_corpus(source_corpus, examples)
    checks = _checks(zero_hit_diagnostic, diagnostic_summary, replay_comparison, replay_summary, examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    patch = _patch(status, examples, patched_corpus)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_zero_hit_diagnostic": str(zero_hit_diagnostic_path or ""),
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_corpus": str(source_corpus_path),
        "zero_hit_diagnostic_summary": diagnostic_summary,
        "replay_summary": replay_summary,
        "patch_examples": examples if status == "pass" else [],
        "patched_corpus_text": patched_corpus if status == "pass" else "",
        "check_rows": checks,
        "target_only_memory_patch": patch,
        "summary": _summary(status, checks, examples, source_corpus, patched_corpus, patch),
        "interpretation": _interpretation(status, patch),
    }


def _patch_examples(replay_rows: list[dict[str, Any]], case_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostic_by_case = {str(row.get("case_id") or ""): row for row in case_diagnostics}
    examples: list[dict[str, Any]] = []
    for row in replay_rows:
        case_id = str(row.get("case_id") or "case")
        prompt = str(row.get("prompt") or "")
        diagnostic = diagnostic_by_case.get(case_id, {})
        examples.extend(_case_memory_examples(case_id, prompt, diagnostic))
    examples.extend(_global_target_examples())
    return examples


def _case_memory_examples(case_id: str, prompt: str, diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    label = _last_label(prompt)
    instruction = _label_free_instruction(prompt)
    continuation_class = str(diagnostic.get("continuation_class") or "zero_hit")
    return [
        _example(f"{case_id}-target-only-a", "target_only_completion_memory", "fixed loss", case_id, continuation_class),
        _example(f"{case_id}-target-only-b", "target_only_completion_memory", "fixed loss", case_id, continuation_class),
        _example(
            f"{case_id}-prompt-target-memory",
            "prompt_target_memory",
            f"{instruction} fixed loss".strip(),
            case_id,
            continuation_class,
        ),
        _example(
            f"{case_id}-label-target-memory",
            "label_target_memory",
            f"{label}\nfixed loss" if label else "fixed loss",
            case_id,
            continuation_class,
        ),
    ]


def _global_target_examples() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(8):
        rows.append(_example(f"global-fixed-loss-memory-{idx + 1}", "target_only_completion_memory", "fixed loss", "global", "target_memory"))
    rows.extend(
        [
            _example("global-two-token-answer", "plain_target_statement", "two token answer fixed loss", "global", "target_memory"),
            _example("global-canonical-completion", "plain_target_statement", "canonical completion fixed loss", "global", "target_memory"),
            _example("global-no-label-repeat-a", "target_pair_repeat", "fixed loss\nfixed loss", "global", "target_memory"),
            _example("global-no-label-repeat-b", "target_pair_repeat", "fixed loss fixed loss", "global", "target_memory"),
        ]
    )
    return rows


def _example(example_id: str, kind: str, text: str, source_case_id: str, continuation_class: str) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "text": text,
        "completion": "fixed loss",
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": source_case_id,
        "source_continuation_class": continuation_class,
        "purpose": _purpose(kind),
    }


def _label_free_instruction(prompt: str) -> str:
    parts = [part.strip() for part in prompt.splitlines() if part.strip()]
    if parts and parts[-1].lower().rstrip() in {"answer:", "completion:"}:
        parts = parts[:-1]
    return " ".join(parts)


def _last_label(prompt: str) -> str:
    for part in reversed([line.strip() for line in prompt.splitlines() if line.strip()]):
        if part.lower() in {"answer:", "completion:"}:
            return part
    return ""


def _patched_corpus(source_corpus: str, examples: list[dict[str, Any]]) -> str:
    parts = [source_corpus.rstrip(), "# v872 target-only completion memory patch"]
    parts.extend(str(example["text"]) for example in examples)
    return "\n\n".join(parts).strip() + "\n"


def _checks(
    diagnostic: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    replay: dict[str, Any],
    replay_summary: dict[str, Any],
    examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "single-line zero-hit diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_single_line_surface_zero_hit_diagnostic_ready"),
            "single-line zero-hit diagnostic must be ready",
        ),
        _check(
            "label_or_fragment_confirmed",
            diagnostic_summary.get("all_cases_label_or_fragment") is True,
            diagnostic_summary.get("all_cases_label_or_fragment"),
            "target-only patch should follow persisted label echo or fragments",
        ),
        _check(
            "loss_improved_without_uptake",
            diagnostic_summary.get("loss_improved_without_required_term_uptake") is True,
            diagnostic_summary.get("loss_improved_without_required_term_uptake"),
            "target-only patch is intended for low-loss zero-hit replay",
        ),
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "source replay comparison must pass"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready"),
            "source replay comparison must be ready",
        ),
        _check("zero_hit_replay", int(replay_summary.get("any_hit_case_count") or 0) == 0, replay_summary.get("any_hit_case_count"), "source replay must still be zero-hit"),
        _check("patch_examples_present", bool(examples), len(examples), "patch examples must be generated"),
        _check("decoder_anchor_free", all(example.get("decoder_anchor") is False for example in examples), 0, "patch examples must stay no-anchor"),
    ]


def _patch(status: str, examples: list[dict[str, Any]], corpus: str) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "patch_example_count": len(examples) if ready else 0,
        "target_only_example_count": sum(1 for example in examples if example.get("kind") == "target_only_completion_memory") if ready else 0,
        "prompt_target_memory_count": sum(1 for example in examples if example.get("kind") == "prompt_target_memory") if ready else 0,
        "label_target_memory_count": sum(1 for example in examples if example.get("kind") == "label_target_memory") if ready else 0,
        "decoder_anchor_example_count": 0,
        "patched_corpus_char_count": len(corpus) if ready else 0,
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_target_only_memory_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_target_only_memory_patch" if ready else "repair_bounded_objective_loss_signal_bridge_target_only_memory_patch",
    }


def _summary(
    status: str,
    checks: list[dict[str, Any]],
    examples: list[dict[str, Any]],
    source_corpus: str,
    patched_corpus: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_patch_ready": status == "pass",
        "patch_example_count": patch.get("patch_example_count"),
        "target_only_example_count": patch.get("target_only_example_count"),
        "prompt_target_memory_count": patch.get("prompt_target_memory_count"),
        "label_target_memory_count": patch.get("label_target_memory_count"),
        "decoder_anchor_example_count": 0,
        "original_corpus_char_count": len(source_corpus),
        "patched_corpus_char_count": patch.get("patched_corpus_char_count"),
        "patch_kinds": sorted({str(example.get("kind")) for example in examples}) if status == "pass" else [],
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "model_quality_claim": "target_only_memory_patch_only" if status == "pass" else "not_claimed",
        "proposed_next_artifact": patch.get("proposed_next_artifact"),
        "next_step": patch.get("next_step"),
    }


def _decision(status: str) -> str:
    return "bounded_objective_loss_signal_bridge_target_only_memory_patch_ready" if status == "pass" else "bounded_objective_loss_signal_bridge_target_only_memory_patch_blocked"


def _interpretation(status: str, patch: dict[str, Any]) -> dict[str, Any]:
    if status == "pass":
        return {
            "model_quality_claim": "target_only_memory_patch_only",
            "reason": "The patch shifts repair examples toward fixed loss memory with fewer label surfaces; capability still requires training and replay.",
            "next_action": patch.get("next_step"),
        }
    return {"model_quality_claim": "not_claimed", "reason": "Target-only memory patch inputs were not sufficient.", "next_action": patch.get("next_step")}


def _purpose(kind: str) -> str:
    return {
        "target_only_completion_memory": "reinforce fixed loss without answer/completion labels",
        "prompt_target_memory": "bind the objective instruction directly to fixed loss without a trailing label",
        "label_target_memory": "keep a minimal label-to-target bridge while avoiding repeated labels",
        "plain_target_statement": "state the target pair as plain memory",
        "target_pair_repeat": "increase short target-pair recurrence without label noise",
    }.get(kind, "repair target-only completion memory")


def _locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {source}")


__all__ = [
    "TARGET_ONLY_MEMORY_PATCH_CORPUS_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_JSONL_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_PATCH_TEXT_FILENAME",
    "build_target_only_memory_patch",
    "locate_replay_comparison",
    "locate_zero_hit_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
