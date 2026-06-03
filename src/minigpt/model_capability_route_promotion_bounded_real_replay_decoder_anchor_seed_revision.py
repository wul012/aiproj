from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSONL_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.jsonl"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CORPUS_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_corpus.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision.html"


def locate_prompt_aligned_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME
    return source


def locate_prompt_aligned_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_policy_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor seed revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision(
    prompt_aligned_seed_revision: dict[str, Any],
    prompt_aligned_replay: dict[str, Any],
    policy_replay: dict[str, Any],
    *,
    seed_revision_path: str | Path | None = None,
    replay_path: str | Path | None = None,
    policy_replay_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor seed revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    seed_summary = as_dict(prompt_aligned_seed_revision.get("summary"))
    replay_summary = as_dict(prompt_aligned_replay.get("summary"))
    policy_summary = as_dict(policy_replay.get("summary"))
    original_examples = list_of_dicts(prompt_aligned_seed_revision.get("seed_examples"))
    replay_rows = list_of_dicts(prompt_aligned_replay.get("replay_rows"))
    seed_examples = [_carry(row) for row in original_examples] + _anchor_examples(replay_rows)
    checks = _checks(prompt_aligned_seed_revision, prompt_aligned_replay, policy_replay, replay_rows, seed_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    revision = _revision(status, original_examples, seed_examples, replay_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_prompt_aligned_seed_revision": str(seed_revision_path or ""),
        "source_prompt_aligned_replay": str(replay_path or ""),
        "source_policy_replay": str(policy_replay_path or ""),
        "source_summaries": {"seed_revision": seed_summary, "prompt_aligned_replay": replay_summary, "policy_replay": policy_summary},
        "seed_examples": seed_examples,
        "check_rows": checks,
        "decoder_anchor_seed_revision": revision,
        "summary": _summary(status, checks, revision),
        "interpretation": _interpretation(status, revision),
    }


def resolve_exit_code(report: dict[str, Any], *, require_seed_ready: bool) -> int:
    return 1 if require_seed_ready and report.get("status") != "pass" else 0


def _carry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "example_id": f"decoder-anchor-carry-{row.get('example_id')}",
        "case_id": row.get("case_id"),
        "revision_type": "carry_forward_prompt_aligned_seed",
        "prompt": row.get("prompt", ""),
        "completion": row.get("completion", ""),
        "text": row.get("text") or f"{row.get('prompt', '')}{row.get('completion', '')}",
        "required_terms": row.get("required_terms", ["fixed", "loss"]),
        "guardrail": "retain_prompt_aligned_seed_signal",
    }


def _anchor_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    for row in rows:
        case_id = str(row.get("case_id") or "")
        prompt = str(row.get("prompt") or "")
        examples.extend(
            [
                _example(case_id, "unanchored_direct_answer", prompt, "fixed loss", "unanchored_exact_answer"),
                _example(case_id, "prefix_f_bridge", f"{prompt}f", "ixed loss", "first_character_bridge"),
                _example(case_id, "prefix_fixed_space_bridge", f"{prompt}fixed ", "loss", "first_term_to_second_term_bridge"),
                _example(case_id, "prefix_fixed_l_bridge", f"{prompt}fixed l", "oss", "second_term_prefix_bridge"),
            ]
        )
    return examples


def _example(case_id: str, revision_type: str, prompt: str, completion: str, guardrail: str) -> dict[str, Any]:
    return {
        "example_id": f"decoder-anchor-{case_id}-{revision_type}",
        "case_id": case_id,
        "revision_type": revision_type,
        "prompt": prompt,
        "completion": completion,
        "text": f"{prompt}{completion}",
        "required_terms": ["fixed", "loss"],
        "guardrail": guardrail,
    }


def _checks(seed: dict[str, Any], replay: dict[str, Any], policy_replay: dict[str, Any], replay_rows: list[dict[str, Any]], seed_examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("prompt_aligned_seed_passed", seed.get("status") == "pass", seed.get("status"), "prompt-aligned seed revision must pass"),
        _check("prompt_aligned_replay_passed", replay.get("status") == "pass", replay.get("status"), "prompt-aligned replay execution must pass"),
        _check("policy_replay_passed", policy_replay.get("status") == "pass", policy_replay.get("status"), "policy replay must pass"),
        _check("policy_replay_partial_signal_present", as_dict(policy_replay.get("summary")).get("policy_replay_success") is True, as_dict(policy_replay.get("summary")).get("policy_replay_success"), "seed revision expects a reproduced anchor signal"),
        _check("replay_rows_present", bool(replay_rows), len(replay_rows), "replay rows must provide prompts"),
        _check("seed_examples_have_text", all(str(row.get("text") or "").strip() for row in seed_examples), len(seed_examples), "all seed examples must have text"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _revision(status: str, original: list[dict[str, Any]], examples: list[dict[str, Any]], replay_rows: list[dict[str, Any]]) -> dict[str, Any]:
    added = max(0, len(examples) - len(original))
    return {
        "ready": status == "pass",
        "original_example_count": len(original),
        "added_example_count": added,
        "example_count": len(examples),
        "case_count": len(replay_rows),
        "bridge_example_count": sum(1 for row in examples if str(row.get("revision_type", "")).endswith("_bridge")),
        "unanchored_direct_example_count": sum(1 for row in examples if row.get("revision_type") == "unanchored_direct_answer"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_training_run",
        "next_step": "train_decoder_anchor_seed_revision" if status == "pass" else "repair_decoder_anchor_seed_revision",
    }


def _summary(status: str, checks: list[dict[str, Any]], revision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_seed_revision_ready": status == "pass" and revision.get("ready") is True,
        "original_example_count": revision.get("original_example_count"),
        "added_example_count": revision.get("added_example_count"),
        "example_count": revision.get("example_count"),
        "case_count": revision.get("case_count"),
        "bridge_example_count": revision.get("bridge_example_count"),
        "unanchored_direct_example_count": revision.get("unanchored_direct_example_count"),
        "proposed_next_artifact": revision.get("proposed_next_artifact"),
        "next_step": revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision"


def _interpretation(status: str, revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Decoder anchor seed revision inputs are incomplete.", "next_action": "repair seed revision"}
    return {
        "model_quality_claim": "training_data_revision_only",
        "reason": "The corpus now includes unanchored answers and decoder bridge completions; improvement still requires training and replay.",
        "next_action": revision.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CORPUS_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSONL_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision",
    "locate_policy_replay",
    "locate_prompt_aligned_replay",
    "locate_prompt_aligned_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
