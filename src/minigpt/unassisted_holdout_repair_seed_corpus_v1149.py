from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload
from minigpt.unassisted_holdout_repair_plan_v1148 import EXPLAIN_DIR_NAME, UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM

UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM = "unassisted_holdout_repair_seed_corpus_v1149"
SEED_BLUEPRINT_JSON_NAME = "unassisted_holdout_repair_seed_blueprint.json"


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def locate_v1148_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM}.json"
    return source


def default_v1148_plan_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1148"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-plan-v1148"
        / f"{UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM}.json"
    )


def load_seed_blueprint(plan_report: dict[str, Any], *, plan_path: str | Path | None = None, blueprint_path: str | Path | None = None) -> list[dict[str, Any]]:
    source = Path(blueprint_path) if blueprint_path is not None else None
    if source is None and plan_path is not None:
        candidate = Path(plan_path).parent / SEED_BLUEPRINT_JSON_NAME
        source = candidate if candidate.is_file() else None
    if source is not None and source.is_file():
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            return [dict(row) for row in payload if isinstance(row, dict)]
    return list_of_dicts(plan_report.get("repair_seed_blueprint_rows"))


def build_unassisted_holdout_repair_seed_corpus_v1149(
    plan_report: dict[str, Any],
    seed_blueprint_rows: list[dict[str, Any]],
    *,
    plan_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan_summary = as_dict(plan_report.get("summary"))
    examples = _example_rows(seed_blueprint_rows)
    holdout_prompts = _holdout_prompt_rows(examples)
    corpus_text = _corpus_text(examples)
    checks = _checks(plan_report, plan_summary, seed_blueprint_rows, examples, holdout_prompts)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    materialization = _materialization(status, examples, corpus_text, holdout_prompts)
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted holdout repair seed corpus v1149",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_unassisted_holdout_repair_plan": str(plan_path or ""),
        "source_summary": plan_summary,
        "rows": examples,
        "holdout_prompt_rows": holdout_prompts,
        "corpus_text": corpus_text if status == "pass" else "",
        "train_command_hint": _train_command_hint(),
        "check_rows": checks,
        "materialization": materialization,
        "summary": _summary(status, checks, materialization),
        "interpretation": _interpretation(status, materialization),
        "csv_fieldnames": [
            "example_id",
            "kind",
            "prompt",
            "completion",
            "text",
            "decoder_anchor",
            "training_only_context",
            "prompt_contains_target_terms",
        ],
    }


def write_unassisted_holdout_repair_seed_corpus_v1149_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    outputs = write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM,
        row_title="Seed Corpus Examples",
    )
    root = Path(out_dir)
    corpus_path = root / "unassisted_holdout_repair_seed_corpus.txt"
    jsonl_path = root / "unassisted_holdout_repair_seed_corpus.jsonl"
    holdout_path = root / "unassisted_holdout_repair_holdout_prompts.json"
    train_hint_path = root / "unassisted_holdout_repair_train_command_hint.json"
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


def _example_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        prompt = str(row.get("prompt") or "").rstrip()
        completion = str(row.get("completion") or "")
        target_terms = [str(term) for term in row.get("target_terms", [])]
        prompt_lower = prompt.lower()
        text = _join_prompt_completion(prompt, completion)
        examples.append(
            {
                "example_id": str(row.get("id") or f"repair-seed-{index:02d}"),
                "kind": str(row.get("kind") or "repair_seed"),
                "prompt": prompt,
                "completion": completion,
                "text": text,
                "target_terms": target_terms,
                "decoder_anchor": row.get("decoder_anchor") is True,
                "decoder_anchor_boundary": row.get("decoder_anchor_boundary") or "none",
                "training_only_context": row.get("decoder_anchor_boundary") == "training_only_context_not_eval",
                "prompt_contains_target_terms": any(term.lower() in prompt_lower for term in target_terms),
                "source": row.get("source"),
                "variant_index": index,
            }
        )
    return examples


def _holdout_prompt_rows(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    seen: set[str] = set()
    for example in examples:
        prompt = str(example.get("prompt") or "")
        if example.get("training_only_context") or example.get("prompt_contains_target_terms") or prompt in seen:
            continue
        seen.add(prompt)
        rows.append(
            {
                "case_id": f"unassisted-holdout-{len(rows) + 1:02d}",
                "prompt": prompt,
                "expected_terms": ["fixed", "loss"],
                "max_new_tokens": 8,
                "temperature": 0.2,
                "top_k": 5,
            }
        )
    return rows


def _corpus_text(examples: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(row.get("text") or "") for row in examples if row.get("text")) + ("\n" if examples else "")


def _join_prompt_completion(prompt: str, completion: str) -> str:
    if not prompt:
        return completion.strip()
    if completion.startswith(" ") or prompt.endswith(" "):
        return f"{prompt}{completion}"
    return f"{prompt} {completion}"


def _checks(
    plan_report: dict[str, Any],
    plan_summary: dict[str, Any],
    seed_blueprint_rows: list[dict[str, Any]],
    examples: list[dict[str, Any]],
    holdout_prompts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decoder_anchor_count = sum(1 for row in examples if row.get("decoder_anchor") is True)
    pair_count = sum(1 for row in examples if "fixed" in row.get("target_terms", []) and "loss" in row.get("target_terms", []))
    corpus_chars = len(_corpus_text(examples))
    return [
        _check("v1148_plan_passed", plan_report.get("status") == "pass", plan_report.get("status"), "v1148 plan must pass"),
        _check("v1148_plan_ready", plan_summary.get("unassisted_holdout_repair_plan_ready") is True, plan_summary.get("unassisted_holdout_repair_plan_ready"), "v1148 plan ready flag must be true"),
        _check("v1148_next_step_matches_seed_corpus", plan_summary.get("next_step") == "materialize_unassisted_holdout_repair_seed_corpus", plan_summary.get("next_step"), "v1148 must point to seed corpus materialization"),
        _check("seed_blueprint_present", len(seed_blueprint_rows) >= 8, len(seed_blueprint_rows), "seed blueprint must have enough examples"),
        _check("examples_materialized", len(examples) == len(seed_blueprint_rows), {"examples": len(examples), "blueprint": len(seed_blueprint_rows)}, "all blueprint rows must become examples"),
        _check("pair_examples_present", pair_count >= 5, pair_count, "corpus must include multiple fixed/loss pair examples"),
        _check("decoder_anchor_free", decoder_anchor_count == 0, decoder_anchor_count, "seed corpus must not contain decoder-anchor examples"),
        _check("target_free_holdout_prompts_present", len(holdout_prompts) >= 4, len(holdout_prompts), "materialization must produce target-free holdout prompts"),
        _check("corpus_non_empty", corpus_chars > 120, corpus_chars, "materialized corpus must be non-empty and trainable"),
        _check("promotion_boundary_kept", plan_summary.get("promotion_ready") is False, plan_summary.get("promotion_ready"), "seed corpus is not promotion evidence"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _materialization(status: str, examples: list[dict[str, Any]], corpus_text: str, holdout_prompts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "example_count": len(examples) if status == "pass" else 0,
        "unique_prompt_count": len({str(row.get("prompt") or "") for row in examples}) if status == "pass" else 0,
        "pair_example_count": sum(1 for row in examples if "loss" in row.get("target_terms", [])) if status == "pass" else 0,
        "target_free_holdout_prompt_count": len(holdout_prompts) if status == "pass" else 0,
        "training_only_context_count": sum(1 for row in examples if row.get("training_only_context")) if status == "pass" else 0,
        "decoder_anchor_example_count": 0,
        "corpus_char_count": len(corpus_text) if status == "pass" else 0,
        "promotion_ready": False,
        "proposed_next_artifact": "unassisted_holdout_repair_training_run_v1150" if status == "pass" else "",
        "next_step": "run_unassisted_holdout_repair_training" if status == "pass" else "repair_unassisted_holdout_repair_seed_corpus_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], materialization: dict[str, Any]) -> dict[str, Any]:
    return {
        "unassisted_holdout_repair_seed_corpus_ready": status == "pass" and materialization.get("ready") is True,
        "example_count": materialization.get("example_count"),
        "unique_prompt_count": materialization.get("unique_prompt_count"),
        "pair_example_count": materialization.get("pair_example_count"),
        "target_free_holdout_prompt_count": materialization.get("target_free_holdout_prompt_count"),
        "training_only_context_count": materialization.get("training_only_context_count"),
        "decoder_anchor_example_count": materialization.get("decoder_anchor_example_count"),
        "corpus_char_count": materialization.get("corpus_char_count"),
        "model_quality_claim": "seed_corpus_only",
        "promotion_ready": False,
        "proposed_next_artifact": materialization.get("proposed_next_artifact"),
        "next_step": materialization.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "unassisted_holdout_repair_seed_corpus_ready"
    return "fix_unassisted_holdout_repair_seed_corpus"


def _interpretation(status: str, materialization: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Seed corpus inputs are incomplete.", "next_action": "repair seed corpus inputs"}
    return {
        "model_quality_claim": "seed_corpus_only",
        "reason": "The v1148 blueprint has been materialized into trainable text plus unchanged target-free holdout prompts, but no checkpoint has been trained yet.",
        "next_action": materialization.get("next_step"),
    }


def _train_command_hint() -> dict[str, Any]:
    return {
        "script": "scripts/train.py",
        "prepared_data": "unassisted_holdout_repair_seed_corpus.txt",
        "suggested_args": {
            "tokenizer": "char",
            "batch_size": 8,
            "block_size": 24,
            "max_iters": 50,
            "eval_interval": 10,
            "eval_iters": 2,
            "learning_rate": 0.01,
            "train_ratio": 0.85,
            "n_layer": 1,
            "n_head": 1,
            "n_embd": 16,
            "dropout": 0.0,
            "seed": 1149,
            "device": "cpu",
        },
    }


def _jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


__all__ = [
    "SEED_BLUEPRINT_JSON_NAME",
    "UNASSISTED_HOLDOUT_REPAIR_SEED_CORPUS_V1149_STEM",
    "build_unassisted_holdout_repair_seed_corpus_v1149",
    "default_v1148_plan_path",
    "load_seed_blueprint",
    "locate_v1148_plan",
    "read_json_report",
    "resolve_exit_code",
    "write_unassisted_holdout_repair_seed_corpus_v1149_outputs",
]
