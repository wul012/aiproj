from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_partial_hit_diagnostic import (
    LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch.json"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_CSV_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch.csv"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSONL_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch_examples.jsonl"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_CORPUS_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch_corpus.txt"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch.txt"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch.md"
LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_HTML_FILENAME = "bounded_objective_loss_signal_bridge_pair_binding_patch.html"


def locate_partial_hit_diagnostic(path: str | Path) -> Path:
    return _locate(path, LOSS_SIGNAL_BRIDGE_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME)


def locate_replay_comparison(path: str | Path) -> Path:
    return _locate(path, LOSS_SIGNAL_BRIDGE_REPLAY_COMPARISON_JSON_FILENAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective loss signal bridge pair-binding patch input must be a JSON object")
    return dict(payload)


def build_bounded_objective_loss_signal_bridge_pair_binding_patch(
    partial_hit_diagnostic: dict[str, Any],
    replay_comparison: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    partial_hit_diagnostic_path: str | Path | None = None,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge pair-binding patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(partial_hit_diagnostic.get("summary"))
    replay_summary = as_dict(replay_comparison.get("summary"))
    case_diagnostics = list_of_dicts(partial_hit_diagnostic.get("case_diagnostics"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    source_corpus = Path(source_corpus_path).read_text(encoding="utf-8")
    examples = _patch_examples(case_diagnostics, replay_rows)
    patched_corpus = _patched_corpus(source_corpus, examples)
    checks = _checks(partial_hit_diagnostic, diagnostic_summary, replay_comparison, replay_summary, examples)
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
        "source_partial_hit_diagnostic": str(partial_hit_diagnostic_path or ""),
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_corpus": str(source_corpus_path),
        "partial_hit_diagnostic_summary": diagnostic_summary,
        "replay_summary": replay_summary,
        "patch_examples": examples if status == "pass" else [],
        "patched_corpus_text": patched_corpus if status == "pass" else "",
        "check_rows": checks,
        "pair_binding_patch": patch,
        "summary": _summary(status, checks, examples, source_corpus, patched_corpus, patch),
        "interpretation": _interpretation(status, patch),
    }


def resolve_exit_code(report: dict[str, Any], *, require_patch_ready: bool) -> int:
    return 1 if require_patch_ready and report.get("status") != "pass" else 0


def _patch_examples(case_diagnostics: list[dict[str, Any]], replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_id = {str(row.get("case_id") or ""): row for row in replay_rows}
    examples: list[dict[str, Any]] = []
    for diagnostic in case_diagnostics:
        case_id = str(diagnostic.get("case_id") or "case")
        prompt = str(rows_by_id.get(case_id, {}).get("prompt") or "completion:")
        label = str(diagnostic.get("label") or "")
        examples.extend(_case_pair_examples(case_id, prompt, label))
    examples.extend(_global_pair_examples())
    return examples


def _case_pair_examples(case_id: str, prompt: str, label: str) -> list[dict[str, Any]]:
    clean_prompt = prompt.rstrip()
    examples = [
        _example(f"{case_id}-pair-repeat-a", "case_pair_repeat", clean_prompt, "fixed loss", case_id),
        _example(f"{case_id}-pair-repeat-b", "case_pair_repeat", clean_prompt, "fixed loss", case_id),
    ]
    if label == "fixed_only":
        examples.extend(
            [
                _example(f"{case_id}-fixed-needs-loss", "fixed_to_loss_binding", f"{clean_prompt}\nfixed", "loss", case_id),
                _example(f"{case_id}-fixed-restores-pair", "fixed_to_pair_binding", f"{clean_prompt}\nfixed", "fixed loss", case_id),
            ]
        )
    elif label == "loss_only":
        examples.extend(
            [
                _example(f"{case_id}-loss-needs-fixed", "loss_to_pair_binding", f"{clean_prompt}\nloss", "fixed loss", case_id),
                _example(f"{case_id}-loss-left-context", "loss_left_context_binding", "loss belongs with", "fixed loss", case_id),
            ]
        )
    elif label == "zero_hit":
        examples.extend(
            [
                _example(f"{case_id}-surface-repair-a", "completion_surface_pair_repair", clean_prompt, "fixed loss", case_id),
                _example(f"{case_id}-surface-repair-b", "completion_surface_pair_repair", "completion:", "fixed loss", case_id),
            ]
        )
    return examples


def _global_pair_examples() -> list[dict[str, Any]]:
    return [
        _example("global-fixed-to-loss-a", "global_pair_binding", "fixed", "loss", "global"),
        _example("global-fixed-to-loss-b", "global_pair_binding", "fixed", "loss", "global"),
        _example("global-target-pair-a", "global_pair_repeat", "target:", "fixed loss", "global"),
        _example("global-target-pair-b", "global_pair_repeat", "target:", "fixed loss", "global"),
        _example("global-answer-pair", "global_pair_repeat", "answer:", "fixed loss", "global"),
        _example("global-completion-pair", "global_pair_repeat", "completion:", "fixed loss", "global"),
    ]


def _example(example_id: str, kind: str, prompt: str, completion: str, source_case_id: str) -> dict[str, Any]:
    text = f"{prompt.rstrip()}\n{completion}".strip()
    return {
        "example_id": example_id,
        "kind": kind,
        "prompt": prompt,
        "completion": completion,
        "text": text,
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": source_case_id,
        "purpose": _purpose(kind),
    }


def _patched_corpus(source_corpus: str, examples: list[dict[str, Any]]) -> str:
    parts = [source_corpus.rstrip(), "# v864 loss signal bridge pair-binding patch"]
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
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "partial-hit diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_partial_hit_diagnostic_ready"),
            "partial-hit diagnostic must be ready",
        ),
        _check("pair_split_present", diagnostic_summary.get("paired_signal_split") is True, diagnostic_summary.get("paired_signal_split"), "pair-binding patch should follow a split fixed/loss signal"),
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "source replay comparison must pass"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_replay_comparison_ready"),
            "source replay comparison must be ready",
        ),
        _check("contract_not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "patch should not replace holdout after recovery"),
        _check("patch_examples_present", bool(examples), len(examples), "patch examples must be generated"),
        _check("decoder_anchor_free", all(example.get("decoder_anchor") is False for example in examples), False, "patch examples must stay no-anchor"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _patch(status: str, examples: list[dict[str, Any]], corpus: str) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "patch_example_count": len(examples) if ready else 0,
        "case_pair_repeat_count": sum(1 for example in examples if example.get("kind") == "case_pair_repeat") if ready else 0,
        "pair_binding_example_count": sum(1 for example in examples if "binding" in str(example.get("kind"))) if ready else 0,
        "completion_surface_example_count": sum(1 for example in examples if str(example.get("kind")).startswith("completion_surface")) if ready else 0,
        "decoder_anchor_example_count": 0,
        "patched_corpus_char_count": len(corpus) if ready else 0,
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_pair_binding_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_pair_binding_patch" if ready else "repair_bounded_objective_loss_signal_bridge_pair_binding_patch",
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
        "bounded_objective_loss_signal_bridge_pair_binding_patch_ready": status == "pass",
        "patch_example_count": patch.get("patch_example_count"),
        "case_pair_repeat_count": patch.get("case_pair_repeat_count"),
        "pair_binding_example_count": patch.get("pair_binding_example_count"),
        "completion_surface_example_count": patch.get("completion_surface_example_count"),
        "decoder_anchor_example_count": 0,
        "original_corpus_char_count": len(source_corpus),
        "patched_corpus_char_count": patch.get("patched_corpus_char_count"),
        "patch_kinds": sorted({str(example.get("kind")) for example in examples}) if status == "pass" else [],
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "model_quality_claim": "pair_binding_patch_only" if status == "pass" else "not_claimed",
        "proposed_next_artifact": patch.get("proposed_next_artifact"),
        "next_step": patch.get("next_step"),
    }


def _decision(status: str) -> str:
    return "bounded_objective_loss_signal_bridge_pair_binding_patch_ready" if status == "pass" else "bounded_objective_loss_signal_bridge_pair_binding_patch_blocked"


def _interpretation(status: str, patch: dict[str, Any]) -> dict[str, Any]:
    if status == "pass":
        return {
            "model_quality_claim": "pair_binding_patch_only",
            "reason": "The patch reinforces fixed loss as an ordered pair on the replay failure surfaces, but capability still requires training and replay.",
            "next_action": patch.get("next_step"),
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The pair-binding patch inputs were not sufficient.",
        "next_action": patch.get("next_step"),
    }


def _purpose(kind: str) -> str:
    return {
        "case_pair_repeat": "repeat fixed loss on the exact failed replay surface",
        "fixed_to_loss_binding": "teach that fixed should be completed with loss",
        "fixed_to_pair_binding": "keep fixed while restoring the full pair",
        "loss_to_pair_binding": "turn loss-only signal into the full ordered pair",
        "loss_left_context_binding": "bind loss back to fixed as its left context",
        "completion_surface_pair_repair": "repair the completion-label zero-hit surface",
        "global_pair_binding": "reinforce fixed-to-loss adjacency",
        "global_pair_repeat": "repeat fixed loss as a short target completion",
    }.get(kind, "reinforce fixed loss pair binding")


def _locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {source}")


__all__ = [
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_CORPUS_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_CSV_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_HTML_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSON_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_JSONL_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_MARKDOWN_FILENAME",
    "LOSS_SIGNAL_BRIDGE_PAIR_BINDING_PATCH_TEXT_FILENAME",
    "build_bounded_objective_loss_signal_bridge_pair_binding_patch",
    "locate_partial_hit_diagnostic",
    "locate_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
