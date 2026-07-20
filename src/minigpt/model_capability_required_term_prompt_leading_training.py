from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import (
    GenerateFunc,
    TrainFunc,
    _generation_row,
    _train_micro_checkpoint,
)
from minigpt.model_capability_required_term_prompt_leading_corpus import (
    REQUIRED_TERM_PROMPT_LEADING_CORPUS_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PROMPT_LEADING_TRAINING_JSON_FILENAME = "model_capability_required_term_prompt_leading_training.json"
REQUIRED_TERM_PROMPT_LEADING_TRAINING_TEXT_FILENAME = "model_capability_required_term_prompt_leading_training.txt"
REQUIRED_TERM_PROMPT_LEADING_TRAINING_MARKDOWN_FILENAME = "model_capability_required_term_prompt_leading_training.md"
REQUIRED_TERM_PROMPT_LEADING_TRAINING_HTML_FILENAME = "model_capability_required_term_prompt_leading_training.html"


def locate_model_capability_required_term_prompt_leading_training_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PROMPT_LEADING_CORPUS_JSON_FILENAME
    return source


def build_model_capability_required_term_prompt_leading_training(
    prompt_leading_corpus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    max_iters: int = 600,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 8,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 490,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    term_rows = _term_rows(prompt_leading_corpus_report)
    corpus_path = _resolve_corpus_path(prompt_leading_corpus_report, source_path)
    previous_training_report = _resolve_previous_training_report(prompt_leading_corpus_report, source_path)
    source_summary = as_dict(prompt_leading_corpus_report.get("summary"))
    previous_summary = as_dict(previous_training_report.get("summary"))
    issues = _input_issues(prompt_leading_corpus_report, term_rows, corpus_path, source_summary)

    train_dir = root / "prompt-leading-run"
    training: dict[str, Any] = {"status": "skipped", "reason": "input issues prevented training"}
    if not issues:
        training = _train_micro_checkpoint(
            {
                "corpus_path": str(corpus_path),
                "train_dir": str(train_dir),
                "max_iters": max_iters,
                "eval_iters": eval_iters,
                "batch_size": batch_size,
                "block_size": block_size,
                "n_layer": n_layer,
                "n_head": n_head,
                "n_embd": n_embd,
                "learning_rate": learning_rate,
                "seed": generation_seed,
                "device": device,
                "sample_prompt": _sample_prompt(term_rows),
            },
            train_func,
        )
        if training.get("status") != "pass":
            issues.append("prompt-leading corpus training command did not complete successfully")

    generation_rows: list[dict[str, Any]] = []
    if training.get("status") == "pass":
        generation_rows = [
            _generation_row(
                row,
                training,
                index=index,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                generation_seed=generation_seed,
                device=device,
                generate_func=generate_func,
            )
            for index, row in enumerate(term_rows)
        ]

    summary = summarize_required_term_prompt_leading_training(
        term_rows,
        generation_rows,
        training,
        source_summary=source_summary,
        previous_summary=previous_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term prompt-leading training",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_prompt_leading_corpus": str(source_path) if source_path else None,
        "source_required_term_balanced_training": str(previous_training_report.get("_source_path") or "")
        if previous_training_report
        else None,
        "out_dir": str(root),
        "settings": {
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "device": device,
            "comparison_boundary": "compare against v488 balanced training evidence when source_report is resolvable",
        },
        "source_corpus": {
            "path": str(corpus_path) if corpus_path else None,
            "line_count": as_dict(prompt_leading_corpus_report.get("corpus")).get("line_count"),
            "unique_line_rate": source_summary.get("unique_line_rate"),
            "term_line_spread": source_summary.get("term_line_spread"),
            "prompt_leading_line_count": source_summary.get("prompt_leading_line_count"),
            "prompt_aligned_term_count": source_summary.get("prompt_aligned_term_count"),
            "prompt_alignment_ready": source_summary.get("prompt_alignment_ready"),
        },
        "previous_baseline": _previous_baseline(previous_summary),
        "training": training,
        "summary": summary,
        "term_rows": term_rows,
        "generation_count": len(generation_rows),
        "generation_rows": generation_rows,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def summarize_required_term_prompt_leading_training(
    term_rows: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    training: dict[str, Any],
    *,
    source_summary: dict[str, Any] | None = None,
    previous_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    continuation_hits = sum(int(row.get("continuation_hit_count") or 0) for row in generation_rows)
    generated_hits = sum(int(row.get("generated_hit_count") or 0) for row in generation_rows)
    case_hits = sum(1 for row in generation_rows if int(row.get("continuation_hit_count") or 0) > 0)
    source = source_summary or {}
    previous = previous_summary or {}
    previous_continuation_hits = int(previous.get("continuation_hit_count") or 0)
    previous_generated_hits = int(previous.get("generated_hit_count") or 0)
    return {
        "prompt_leading_training_decision": _prompt_leading_training_decision(
            term_rows,
            generation_rows,
            continuation_hits,
            previous_continuation_hits,
            training,
        ),
        "term_count": len(term_rows),
        "generation_count": len(generation_rows),
        "continuation_hit_count": continuation_hits,
        "generated_hit_count": generated_hits,
        "prompt_hit_count": sum(int(row.get("prompt_hit_count") or 0) for row in generation_rows),
        "case_with_continuation_hit_count": case_hits,
        "continuation_hit_rate": round(case_hits / len(generation_rows), 4) if generation_rows else 0.0,
        "previous_continuation_hit_count": previous_continuation_hits,
        "previous_generated_hit_count": previous_generated_hits,
        "continuation_hit_delta": continuation_hits - previous_continuation_hits,
        "generated_hit_delta": generated_hits - previous_generated_hits,
        "improved_over_previous": continuation_hits > previous_continuation_hits,
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
        "prompt_leading_line_count": source.get("prompt_leading_line_count", 0),
        "prompt_aligned_term_count": source.get("prompt_aligned_term_count", 0),
        "prompt_alignment_ready": bool(source.get("prompt_alignment_ready")),
        "previous_prompt_alignment_ready": previous.get("prompt_alignment_ready"),
    }


def _term_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(report.get("term_rows")):
        term = str(row.get("term") or "").strip()
        prompt = str(row.get("scaffold_prompt") or "").strip()
        if not term:
            continue
        rows.append(
            {
                "case": row.get("case"),
                "term": term,
                "scaffold_prompt": prompt or f"{term}:",
                "prompt_leading_line_count": row.get("line_count"),
                "prompt_leading_pattern_count": row.get("pattern_count"),
                "prompt_leading_repeat": row.get("repeat"),
            }
        )
    return rows


def _resolve_corpus_path(report: dict[str, Any], source_path: str | Path | None) -> Path | None:
    raw = as_dict(report.get("corpus")).get("path")
    if not raw:
        return None
    candidate = Path(str(raw).replace("\\", "/"))
    candidates = [candidate, Path.cwd() / candidate]
    if source_path is not None:
        source_parent = Path(source_path).parent
        candidates.extend(anchor / candidate for anchor in (source_parent, *source_parent.parents))
    for item in candidates:
        if item.is_file():
            return item
    return candidate


def _resolve_previous_training_report(report: dict[str, Any], source_path: str | Path | None) -> dict[str, Any]:
    raw = report.get("source_report")
    if not raw:
        return {}
    candidate = Path(str(raw).replace("\\", "/"))
    candidates = [candidate, Path.cwd() / candidate]
    if source_path is not None:
        source_parent = Path(source_path).parent
        candidates.extend(anchor / candidate for anchor in (source_parent, *source_parent.parents))
    for item in candidates:
        if item.is_file():
            payload = read_json_report(item)
            payload["_source_path"] = str(item)
            return payload
        if item.is_dir():
            nested = item / "model_capability_required_term_balanced_training.json"
            if nested.is_file():
                payload = read_json_report(nested)
                payload["_source_path"] = str(nested)
                return payload
    return {}


def _input_issues(
    report: dict[str, Any],
    term_rows: list[dict[str, Any]],
    corpus_path: Path | None,
    source_summary: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source prompt-leading corpus report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source prompt-leading corpus report is not pass")
    if not term_rows:
        issues.append("source prompt-leading corpus report has no usable term rows")
    if corpus_path is None or not corpus_path.is_file():
        issues.append("source prompt-leading corpus file could not be resolved")
    if report and not bool(source_summary.get("prompt_alignment_ready")):
        issues.append("source prompt-leading corpus is not prompt-alignment ready")
    return issues


def _prompt_leading_training_decision(
    term_rows: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    continuation_hits: int,
    previous_continuation_hits: int,
    training: dict[str, Any],
) -> str:
    if training.get("status") != "pass":
        return "prompt_leading_training_run_failed"
    if not term_rows:
        return "no_required_term_rows"
    if not generation_rows:
        return "prompt_leading_training_generation_missing"
    if continuation_hits > previous_continuation_hits:
        return "prompt_leading_training_improved_over_previous"
    if continuation_hits > 0:
        return "prompt_leading_training_required_term_uptake_observed"
    return "prompt_leading_training_completed_without_uptake"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_prompt_leading_training"
    if summary.get("improved_over_previous"):
        return "required_term_prompt_leading_training_improved"
    if summary.get("continuation_hit_count"):
        return "required_term_prompt_leading_training_uptake_observed"
    return "required_term_prompt_leading_training_completed_without_uptake"


def _previous_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "balanced_training_decision": summary.get("balanced_training_decision"),
        "continuation_hit_count": int(summary.get("continuation_hit_count") or 0),
        "generated_hit_count": int(summary.get("generated_hit_count") or 0),
        "prompt_alignment_ready": summary.get("prompt_alignment_ready"),
        "prompt_leading_line_count": summary.get("prompt_leading_line_count"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("improved_over_previous"):
        return "prompt_leading_training_signal_only"
    if summary.get("continuation_hit_count"):
        return "required_term_training_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The prompt-leading training run did not complete cleanly."
    if summary.get("improved_over_previous"):
        return "A tiny checkpoint trained on the prompt-leading corpus improved required-term continuation hits over the v488 baseline."
    if summary.get("continuation_hit_count"):
        return "The prompt-leading corpus produced required-term continuation hits, but not above the previous baseline count."
    return "The prompt-leading training run completed, but short continuations still did not include required terms."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair prompt-leading training inputs before rerunning capability comparisons"
    if summary.get("improved_over_previous"):
        return "rerun the prompt-leading training across multiple seeds before making a stronger capability claim"
    if summary.get("prompt_alignment_ready"):
        return "increase training budget or reduce prompt variants before rerunning the prompt-leading training"
    return "repair prompt-leading corpus alignment before training again"


def _sample_prompt(term_rows: list[dict[str, Any]]) -> str:
    for row in term_rows:
        prompt = str(row.get("scaffold_prompt") or "")
        if prompt:
            return prompt
    return "data:"
