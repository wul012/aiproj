from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_pair_binding_replay_comparison import (
    LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic import (
    PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_patch_ready as resolve_exit_code


SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch.json"
SINGLE_LINE_SURFACE_PATCH_CSV_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch.csv"
SINGLE_LINE_SURFACE_PATCH_JSONL_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch_examples.jsonl"
SINGLE_LINE_SURFACE_PATCH_CORPUS_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch_corpus.txt"
SINGLE_LINE_SURFACE_PATCH_TEXT_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch.txt"
SINGLE_LINE_SURFACE_PATCH_MARKDOWN_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch.md"
SINGLE_LINE_SURFACE_PATCH_HTML_FILENAME = "bounded_objective_loss_signal_bridge_single_line_surface_patch.html"


def locate_zero_hit_diagnostic(path: str | Path) -> Path:
    return _locate(path, PAIR_BINDING_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME)


def locate_replay_comparison(path: str | Path) -> Path:
    return _locate(path, LOSS_SIGNAL_BRIDGE_PAIR_BINDING_REPLAY_COMPARISON_JSON_FILENAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("single-line surface patch input must be a JSON object")
    return dict(payload)


def build_single_line_surface_patch(
    zero_hit_diagnostic: dict[str, Any],
    replay_comparison: dict[str, Any],
    *,
    source_corpus_path: str | Path,
    zero_hit_diagnostic_path: str | Path | None = None,
    replay_comparison_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge single-line surface patch",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(zero_hit_diagnostic.get("summary"))
    replay_summary = as_dict(replay_comparison.get("summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    source_corpus = Path(source_corpus_path).read_text(encoding="utf-8")
    examples = _patch_examples(replay_rows)
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
        "loss_signal_bridge_single_line_surface_patch": patch,
        "summary": _summary(status, checks, examples, source_corpus, patched_corpus, patch),
        "interpretation": _interpretation(status, patch),
    }


def _patch_examples(replay_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for row in replay_rows:
        case_id = str(row.get("case_id") or "case")
        prompt = str(row.get("prompt") or "")
        examples.append(_example(f"{case_id}-single-line-case-a", "single_line_case_surface", _single_line(prompt), case_id))
        examples.append(_example(f"{case_id}-single-line-case-b", "single_line_case_surface", _single_line(prompt), case_id))
    examples.extend(
        [
            _example("answer-label-direct-a", "direct_label_surface", "answer: fixed loss", "global"),
            _example("answer-label-direct-b", "direct_label_surface", "answer: fixed loss", "global"),
            _example("completion-label-direct-a", "direct_label_surface", "completion: fixed loss", "global"),
            _example("completion-label-direct-b", "direct_label_surface", "completion: fixed loss", "global"),
            _example("target-label-direct-a", "direct_label_surface", "target: fixed loss", "global"),
            _example("target-label-direct-b", "direct_label_surface", "target: fixed loss", "global"),
            _example("fixed-loss-plain-a", "completion_surface_single_line", "fixed loss", "global"),
            _example("fixed-loss-plain-b", "completion_surface_single_line", "fixed loss", "global"),
        ]
    )
    return examples


def _single_line(prompt: str) -> str:
    clean = " ".join(prompt.strip().split())
    if clean.endswith(":"):
        return f"{clean} fixed loss"
    return f"{clean} fixed loss".strip()


def _example(example_id: str, kind: str, text: str, source_case_id: str) -> dict[str, Any]:
    return {
        "example_id": example_id,
        "kind": kind,
        "prompt": text,
        "completion": "fixed loss",
        "text": text,
        "required_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "source_case_id": source_case_id,
        "purpose": _purpose(kind),
    }


def _patched_corpus(source_corpus: str, examples: list[dict[str, Any]]) -> str:
    parts = [source_corpus.rstrip(), "# v868 single-line completion surface patch"]
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
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "zero-hit diagnostic must pass"),
        _check(
            "diagnostic_ready",
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_ready") is True,
            diagnostic_summary.get("bounded_objective_loss_signal_bridge_pair_binding_zero_hit_diagnostic_ready"),
            "zero-hit diagnostic must be ready",
        ),
        _check("label_echo_confirmed", diagnostic_summary.get("all_cases_label_echo") is True, diagnostic_summary.get("all_cases_label_echo"), "single-line patch should follow label echo"),
        _check("zero_hit_replay", int(replay_summary.get("any_hit_case_count") or 0) == 0, replay_summary.get("any_hit_case_count"), "source replay should still be zero-hit"),
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "source replay comparison must pass"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready"),
            "source replay comparison must be ready",
        ),
        _check("patch_examples_present", bool(examples), len(examples), "patch examples must be generated"),
        _check("decoder_anchor_free", all(example.get("decoder_anchor") is False for example in examples), 0, "patch examples must stay no-anchor"),
    ]


def _patch(status: str, examples: list[dict[str, Any]], corpus: str) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "patch_example_count": len(examples) if ready else 0,
        "single_line_case_example_count": sum(1 for example in examples if example.get("kind") == "single_line_case_surface") if ready else 0,
        "direct_label_example_count": sum(1 for example in examples if example.get("kind") == "direct_label_surface") if ready else 0,
        "completion_surface_example_count": sum(1 for example in examples if example.get("kind") == "completion_surface_single_line") if ready else 0,
        "decoder_anchor_example_count": 0,
        "patched_corpus_char_count": len(corpus) if ready else 0,
        "proposed_next_artifact": "bounded_objective_loss_signal_bridge_single_line_surface_training_run" if ready else "",
        "next_step": "train_bounded_objective_loss_signal_bridge_single_line_surface_patch" if ready else "repair_bounded_objective_loss_signal_bridge_single_line_surface_patch",
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
        "bounded_objective_loss_signal_bridge_single_line_surface_patch_ready": status == "pass",
        "patch_example_count": patch.get("patch_example_count"),
        "single_line_case_example_count": patch.get("single_line_case_example_count"),
        "direct_label_example_count": patch.get("direct_label_example_count"),
        "completion_surface_example_count": patch.get("completion_surface_example_count"),
        "decoder_anchor_example_count": 0,
        "original_corpus_char_count": len(source_corpus),
        "patched_corpus_char_count": patch.get("patched_corpus_char_count"),
        "patch_kinds": sorted({str(example.get("kind")) for example in examples}) if status == "pass" else [],
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
        "model_quality_claim": "single_line_surface_patch_only" if status == "pass" else "not_claimed",
        "proposed_next_artifact": patch.get("proposed_next_artifact"),
        "next_step": patch.get("next_step"),
    }


def _decision(status: str) -> str:
    return "bounded_objective_loss_signal_bridge_single_line_surface_patch_ready" if status == "pass" else "bounded_objective_loss_signal_bridge_single_line_surface_patch_blocked"


def _interpretation(status: str, patch: dict[str, Any]) -> dict[str, Any]:
    if status == "pass":
        return {
            "model_quality_claim": "single_line_surface_patch_only",
            "reason": "The patch rewrites failed surfaces into single-line target completions, but capability still requires training and replay.",
            "next_action": patch.get("next_step"),
        }
    return {"model_quality_claim": "not_claimed", "reason": "Single-line patch inputs were not sufficient.", "next_action": patch.get("next_step")}


def _purpose(kind: str) -> str:
    return {
        "single_line_case_surface": "put the target answer on the same surface as the failed prompt label",
        "direct_label_surface": "teach answer/completion labels to terminate directly in fixed loss",
        "completion_surface_single_line": "keep the target pair available without a trailing label to echo",
    }.get(kind, "repair single-line completion surface")


def _locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f"cannot locate {filename} under {source}")


__all__ = [
    "SINGLE_LINE_SURFACE_PATCH_CORPUS_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_CSV_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_HTML_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_JSON_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_JSONL_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_MARKDOWN_FILENAME",
    "SINGLE_LINE_SURFACE_PATCH_TEXT_FILENAME",
    "build_single_line_surface_patch",
    "locate_replay_comparison",
    "locate_zero_hit_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
