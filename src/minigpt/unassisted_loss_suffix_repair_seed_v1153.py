from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload
from minigpt.unassisted_holdout_repair_partial_signal_diagnostic_v1152 import (
    UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM,
)
from minigpt.unassisted_holdout_repair_plan_v1148 import EXPLAIN_DIR_NAME
from minigpt.unassisted_holdout_repair_seed_corpus_v1149 import (
    UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
)


UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM = "unassisted_loss_suffix_repair_seed_v1153"
LOSS_SUFFIX_REPAIR_CORPUS_NAME = "unassisted_loss_suffix_repair_seed_corpus_v1153.txt"
LOSS_SUFFIX_REPAIR_JSONL_NAME = "unassisted_loss_suffix_repair_seed_corpus_v1153.jsonl"
LOSS_SUFFIX_REPAIR_HOLDOUT_NAME = "unassisted_loss_suffix_repair_holdout_prompts_v1153.json"
LOSS_SUFFIX_REPAIR_TRAIN_HINT_NAME = "unassisted_loss_suffix_repair_train_command_hint_v1153.json"


def default_v1152_diagnostic_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1152"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-partial-signal-diagnostic-v1152"
        / f"{UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM}.json"
    )


def default_v1149_seed_corpus_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1149"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-seed-corpus-v1149"
        / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
    )


def locate_v1152_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_HOLDOUT_REPAIR_PARTIAL_SIGNAL_DIAGNOSTIC_V1152_STEM}.json"
    return source


def locate_v1149_seed_corpus(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM}.json"
    return source


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def build_unassisted_loss_suffix_repair_seed_v1153(
    diagnostic_report: dict[str, Any],
    seed_report: dict[str, Any],
    *,
    diagnostic_path: str | Path | None = None,
    seed_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(diagnostic_report.get("summary"))
    seed_summary = as_dict(seed_report.get("summary"))
    base_rows = _base_seed_rows(seed_report)
    holdout_prompts = _holdout_prompts(seed_report)
    repair_rows = _repair_rows(diagnostic_report, holdout_prompts)
    revised_rows = base_rows + repair_rows
    corpus_text = _corpus_text(revised_rows)
    materialization = _materialization(revised_rows, repair_rows, holdout_prompts, corpus_text)
    checks = _checks(diagnostic_report, diagnostic_summary, seed_report, seed_summary, base_rows, repair_rows, holdout_prompts, corpus_text)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted loss suffix repair seed v1153",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_partial_signal_diagnostic": str(diagnostic_path or ""),
        "source_seed_corpus": str(seed_path or ""),
        "rows": revised_rows if status == "pass" else [],
        "repair_rows": repair_rows,
        "holdout_prompt_rows": holdout_prompts if status == "pass" else [],
        "corpus_text": corpus_text if status == "pass" else "",
        "train_command_hint": _train_command_hint(),
        "check_rows": checks,
        "materialization": materialization if status == "pass" else {},
        "summary": _summary(status, checks, materialization),
        "interpretation": _interpretation(status, materialization),
        "csv_fieldnames": [
            "example_id",
            "kind",
            "prompt",
            "completion",
            "repair_source_case_id",
            "training_only_context",
            "prompt_contains_target_terms",
        ],
        "recommendations": [
            "Run bounded CPU training from the v1153 corpus before replaying holdout prompts.",
            "Keep v1153 holdout prompts target-free; do not evaluate on loss-suffix training-only prompts.",
        ],
    }


def write_unassisted_loss_suffix_repair_seed_v1153_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    outputs = write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM,
        row_title="Revised Seed Rows",
    )
    root = Path(out_dir)
    corpus_path = root / LOSS_SUFFIX_REPAIR_CORPUS_NAME
    jsonl_path = root / LOSS_SUFFIX_REPAIR_JSONL_NAME
    holdout_path = root / LOSS_SUFFIX_REPAIR_HOLDOUT_NAME
    train_hint_path = root / LOSS_SUFFIX_REPAIR_TRAIN_HINT_NAME
    corpus_path.write_text(str(report.get("corpus_text") or ""), encoding="utf-8")
    jsonl_path.write_text(_jsonl(list_of_dicts(report.get("rows"))), encoding="utf-8")
    write_json_payload(report.get("holdout_prompt_rows", []), holdout_path)
    write_json_payload(report.get("train_command_hint", {}), train_hint_path)
    outputs["corpus"] = str(corpus_path)
    outputs["jsonl"] = str(jsonl_path)
    outputs["holdout_prompts"] = str(holdout_path)
    outputs["train_command_hint"] = str(train_hint_path)
    return outputs


def resolve_exit_code(report: dict[str, Any], *, require_seed_ready: bool = False) -> int:
    return 1 if require_seed_ready and report.get("status") != "pass" else 0


def _base_seed_rows(seed_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(list_of_dicts(seed_report.get("rows")), start=1):
        item = dict(row)
        item.setdefault("variant_index", index)
        item.setdefault("repair_source_case_id", "")
        item.setdefault("repair_added_in_version", "")
        item.setdefault("text", _join_prompt_completion(str(item.get("prompt") or ""), str(item.get("completion") or "")))
        rows.append(item)
    return rows


def _holdout_prompts(seed_report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(seed_report.get("holdout_prompt_rows"))


def _repair_rows(diagnostic_report: dict[str, Any], holdout_prompts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    replay_profile = as_dict(diagnostic_report.get("replay_profile"))
    fixed_only_ids = [str(case_id) for case_id in replay_profile.get("fixed_only_case_ids", []) if str(case_id)]
    zero_hit_ids = [str(case_id) for case_id in replay_profile.get("zero_hit_case_ids", []) if str(case_id)]
    prompt_by_case = {str(row.get("case_id") or ""): str(row.get("prompt") or "") for row in holdout_prompts}
    rows = []
    for case_id in fixed_only_ids:
        prompt = prompt_by_case.get(case_id, "").rstrip()
        if prompt:
            rows.append(_loss_suffix_row(len(rows) + 1, case_id, prompt))
    for case_id in zero_hit_ids:
        prompt = prompt_by_case.get(case_id, "").rstrip()
        if prompt:
            rows.append(_zero_hit_full_pair_row(len(rows) + 1, case_id, prompt))
            rows.append(_loss_suffix_row(len(rows) + 1, case_id, prompt))
    return rows


def _loss_suffix_row(index: int, case_id: str, prompt: str) -> dict[str, Any]:
    repair_prompt = f"{prompt} fixed"
    completion = " loss"
    return {
        "example_id": f"loss-suffix-repair-{index:02d}",
        "kind": "loss_suffix_after_fixed",
        "prompt": repair_prompt,
        "completion": completion,
        "text": _join_prompt_completion(repair_prompt, completion),
        "target_terms": ["loss"],
        "decoder_anchor": False,
        "decoder_anchor_boundary": "training_only_context_not_eval",
        "training_only_context": True,
        "prompt_contains_target_terms": True,
        "source": "v1152_partial_signal_diagnostic",
        "repair_source_case_id": case_id,
        "repair_added_in_version": "v1153",
    }


def _zero_hit_full_pair_row(index: int, case_id: str, prompt: str) -> dict[str, Any]:
    completion = " fixed loss"
    return {
        "example_id": f"zero-hit-full-pair-repair-{index:02d}",
        "kind": "zero_hit_full_pair_reinforcement",
        "prompt": prompt,
        "completion": completion,
        "text": _join_prompt_completion(prompt, completion),
        "target_terms": ["fixed", "loss"],
        "decoder_anchor": False,
        "decoder_anchor_boundary": "none",
        "training_only_context": False,
        "prompt_contains_target_terms": False,
        "source": "v1152_partial_signal_diagnostic",
        "repair_source_case_id": case_id,
        "repair_added_in_version": "v1153",
    }


def _checks(
    diagnostic_report: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    seed_report: dict[str, Any],
    seed_summary: dict[str, Any],
    base_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    holdout_prompts: list[dict[str, Any]],
    corpus_text: str,
) -> list[dict[str, Any]]:
    loss_suffix_count = sum(1 for row in repair_rows if row.get("kind") == "loss_suffix_after_fixed")
    fixed_only_count = _int_value(diagnostic_summary.get("fixed_only_case_count"))
    zero_hit_count = _int_value(diagnostic_summary.get("zero_hit_case_count"))
    loss_hit_count = _int_value(diagnostic_summary.get("loss_hit_case_count"), default=-1)
    return [
        _check("v1152_diagnostic_passed", diagnostic_report.get("status") == "pass", diagnostic_report.get("status"), "v1152 diagnostic must pass before revising seed data"),
        _check("v1152_diagnostic_ready", diagnostic_summary.get("unassisted_holdout_repair_partial_signal_diagnostic_ready") is True, diagnostic_summary.get("unassisted_holdout_repair_partial_signal_diagnostic_ready"), "v1152 diagnostic ready flag must be true"),
        _check("v1152_next_step_matches_seed_revision", diagnostic_summary.get("next_step") == "build_unassisted_loss_suffix_repair_seed", diagnostic_summary.get("next_step"), "v1152 should point to loss-suffix seed construction"),
        _check("v1149_seed_corpus_passed", seed_report.get("status") == "pass", seed_report.get("status"), "v1149 seed corpus must pass"),
        _check("v1149_seed_corpus_ready", seed_summary.get("unassisted_holdout_repair_seed_corpus_ready") is True, seed_summary.get("unassisted_holdout_repair_seed_corpus_ready"), "v1149 seed corpus ready flag must be true"),
        _check("loss_missing_confirmed", loss_hit_count == 0, diagnostic_summary.get("loss_hit_case_count"), "seed revision should only run for the missing-loss condition"),
        _check("fixed_only_cases_have_suffix_repairs", loss_suffix_count >= fixed_only_count, {"loss_suffix": loss_suffix_count, "fixed_only": fixed_only_count}, "each fixed-only case should receive a loss-suffix training-only repair"),
        _check("zero_hit_case_reinforced", zero_hit_count == 0 or any(row.get("kind") == "zero_hit_full_pair_reinforcement" for row in repair_rows), zero_hit_count, "zero-hit prompt should receive at least one target-free full-pair reinforcement"),
        _check("repair_rows_added", len(repair_rows) >= max(1, fixed_only_count + zero_hit_count), len(repair_rows), "revised corpus must add targeted repair rows"),
        _check("holdout_prompts_target_free", _target_free(holdout_prompts), _target_prompt_hits(holdout_prompts), "holdout prompts must remain target-free"),
        _check("base_rows_preserved", len(base_rows) >= 6, len(base_rows), "v1153 should extend, not replace, v1149 seed rows"),
        _check("corpus_non_empty", len(corpus_text) > 250, len(corpus_text), "revised corpus should be trainable and larger than v1149"),
        _check("promotion_boundary_kept", diagnostic_summary.get("promotion_ready") is False and seed_summary.get("promotion_ready") is False, {"diagnostic": diagnostic_summary.get("promotion_ready"), "seed": seed_summary.get("promotion_ready")}, "seed revision is not promotion evidence"),
    ]


def _materialization(
    rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    holdout_prompts: list[dict[str, Any]],
    corpus_text: str,
) -> dict[str, Any]:
    return {
        "ready": True,
        "base_example_count": len(rows) - len(repair_rows),
        "repair_example_count": len(repair_rows),
        "revised_example_count": len(rows),
        "loss_suffix_repair_example_count": sum(1 for row in repair_rows if row.get("kind") == "loss_suffix_after_fixed"),
        "zero_hit_full_pair_repair_example_count": sum(1 for row in repair_rows if row.get("kind") == "zero_hit_full_pair_reinforcement"),
        "target_free_holdout_prompt_count": len(holdout_prompts),
        "training_only_context_count": sum(1 for row in rows if row.get("training_only_context")),
        "corpus_char_count": len(corpus_text),
        "promotion_ready": False,
        "proposed_next_artifact": "unassisted_loss_suffix_repair_training_run_v1154",
        "next_step": "run_unassisted_loss_suffix_repair_training",
    }


def _summary(status: str, checks: list[dict[str, Any]], materialization: dict[str, Any]) -> dict[str, Any]:
    return {
        "unassisted_loss_suffix_repair_seed_ready": status == "pass" and materialization.get("ready") is True,
        "base_example_count": materialization.get("base_example_count"),
        "repair_example_count": materialization.get("repair_example_count"),
        "revised_example_count": materialization.get("revised_example_count"),
        "loss_suffix_repair_example_count": materialization.get("loss_suffix_repair_example_count"),
        "zero_hit_full_pair_repair_example_count": materialization.get("zero_hit_full_pair_repair_example_count"),
        "target_free_holdout_prompt_count": materialization.get("target_free_holdout_prompt_count"),
        "training_only_context_count": materialization.get("training_only_context_count"),
        "corpus_char_count": materialization.get("corpus_char_count"),
        "model_quality_claim": "seed_revision_only" if status == "pass" else "not_claimed",
        "promotion_ready": False,
        "proposed_next_artifact": materialization.get("proposed_next_artifact"),
        "next_step": materialization.get("next_step") if status == "pass" else "repair_unassisted_loss_suffix_seed_inputs",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    return "unassisted_loss_suffix_repair_seed_ready" if status == "pass" else "fix_unassisted_loss_suffix_repair_seed_inputs"


def _interpretation(status: str, materialization: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Seed revision inputs are incomplete.", "next_action": "repair seed revision inputs"}
    return {
        "model_quality_claim": "seed_revision_only",
        "reason": "The revised corpus adds loss-suffix training-only rows for fixed-only replay cases while preserving target-free holdout prompts.",
        "next_action": materialization.get("next_step"),
    }


def _train_command_hint() -> dict[str, Any]:
    return {
        "script": "scripts/train.py",
        "prepared_data": LOSS_SUFFIX_REPAIR_CORPUS_NAME,
        "suggested_args": {
            "tokenizer": "char",
            "batch_size": 8,
            "block_size": 24,
            "max_iters": 80,
            "eval_interval": 10,
            "eval_iters": 2,
            "learning_rate": 0.01,
            "train_ratio": 0.85,
            "n_layer": 1,
            "n_head": 1,
            "n_embd": 16,
            "dropout": 0.0,
            "seed": 1153,
            "device": "cpu",
        },
    }


def _corpus_text(rows: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(row.get("text") or _join_prompt_completion(str(row.get("prompt") or ""), str(row.get("completion") or ""))) for row in rows) + ("\n" if rows else "")


def _join_prompt_completion(prompt: str, completion: str) -> str:
    if not prompt:
        return completion.strip()
    if completion.startswith(" ") or prompt.endswith(" "):
        return f"{prompt}{completion}"
    return f"{prompt} {completion}"


def _jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def _target_free(prompts: list[dict[str, Any]]) -> bool:
    return not _target_prompt_hits(prompts)


def _target_prompt_hits(prompts: list[dict[str, Any]]) -> list[str]:
    hits = []
    for row in prompts:
        prompt = str(row.get("prompt") or "").lower()
        terms = [str(term).lower() for term in row.get("expected_terms", ["fixed", "loss"])]
        if any(term and term in prompt for term in terms):
            hits.append(str(row.get("case_id") or row.get("prompt") or "unknown"))
    return hits


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _int_value(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool) or value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "LOSS_SUFFIX_REPAIR_CORPUS_NAME",
    "LOSS_SUFFIX_REPAIR_HOLDOUT_NAME",
    "LOSS_SUFFIX_REPAIR_JSONL_NAME",
    "LOSS_SUFFIX_REPAIR_TRAIN_HINT_NAME",
    "UNASSISTED_LOSS_SUFFIX_REPAIR_SEED_V1153_STEM",
    "build_unassisted_loss_suffix_repair_seed_v1153",
    "default_v1149_seed_corpus_path",
    "default_v1152_diagnostic_path",
    "locate_v1149_seed_corpus",
    "locate_v1152_diagnostic",
    "read_json_report",
    "resolve_exit_code",
    "write_unassisted_loss_suffix_repair_seed_v1153_outputs",
]
