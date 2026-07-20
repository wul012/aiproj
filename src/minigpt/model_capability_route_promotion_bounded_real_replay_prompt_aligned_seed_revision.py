from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_failure_alignment_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSONL_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.jsonl"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CORPUS_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_corpus.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision.html"


def locate_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def locate_failure_alignment_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_FAILURE_ALIGNMENT_DIAGNOSTIC_JSON_FILENAME
    return source


def locate_repair_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("prompt-aligned seed revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision(
    benchmark_suite_report: dict[str, Any],
    failure_alignment_diagnostic: dict[str, Any],
    repair_seed_revision: dict[str, Any],
    *,
    benchmark_suite_path: str | Path | None = None,
    diagnostic_path: str | Path | None = None,
    repair_seed_revision_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay prompt-aligned seed revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    suite = as_dict(benchmark_suite_report.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    diagnostic_summary = as_dict(failure_alignment_diagnostic.get("summary"))
    seed_summary = as_dict(repair_seed_revision.get("summary"))
    original_examples = list_of_dicts(repair_seed_revision.get("seed_examples"))
    seed_examples = [_carry_forward(row) for row in original_examples] + _prompt_examples(cases)
    checks = _checks(benchmark_suite_report, failure_alignment_diagnostic, repair_seed_revision, cases, seed_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    revision = _revision(status, original_examples, seed_examples, cases, diagnostic_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "source_failure_alignment_diagnostic": str(diagnostic_path or ""),
        "source_repair_seed_revision": str(repair_seed_revision_path or ""),
        "source_summaries": {"diagnostic": diagnostic_summary, "repair_seed_revision": seed_summary},
        "seed_examples": seed_examples,
        "check_rows": checks,
        "prompt_aligned_seed_revision": revision,
        "summary": _summary(status, checks, revision),
        "interpretation": _interpretation(status, revision),
    }


def resolve_exit_code(report: dict[str, Any], *, require_prompt_aligned_seed_ready: bool) -> int:
    return 1 if require_prompt_aligned_seed_ready and report.get("status") != "pass" else 0


def _carry_forward(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "example_id": f"prompt-aligned-carry-{row.get('example_id')}",
        "case_id": row.get("case_id"),
        "revision_type": "carry_forward_seed_revision",
        "prompt": row.get("prompt", ""),
        "completion": row.get("completion", ""),
        "text": row.get("text") or f"{row.get('prompt', '')}{row.get('completion', '')}",
        "required_terms": row.get("required_terms", ["fixed", "loss"]),
        "guardrail": "retain_revised_seed_signal",
    }


def _prompt_examples(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    for case in cases:
        case_id = str(case.get("case_id") or "")
        prompt = str(as_dict(case.get("prompt_case")).get("prompt") or "")
        examples.append(_example(case_id, "exact_benchmark_prompt_answer", prompt, "fixed loss"))
        examples.append(_example(case_id, "exact_benchmark_prompt_self_check", f"{prompt}\nSelf-check: include fixed and loss exactly.\nAnswer:", "fixed loss"))
    return examples


def _example(case_id: str, revision_type: str, prompt: str, completion: str) -> dict[str, Any]:
    return {
        "example_id": f"prompt-aligned-{case_id}-{revision_type}",
        "case_id": case_id,
        "revision_type": revision_type,
        "prompt": prompt,
        "completion": completion,
        "text": f"{prompt}{completion}",
        "required_terms": ["fixed", "loss"],
        "guardrail": "exact_benchmark_prompt_alignment",
    }


def _checks(
    suite: dict[str, Any],
    diagnostic: dict[str, Any],
    seed_revision: dict[str, Any],
    cases: list[dict[str, Any]],
    seed_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact_prompt_count = sum(1 for row in seed_examples if row.get("revision_type") == "exact_benchmark_prompt_answer")
    return [
        _check("benchmark_suite_passed", suite.get("status") == "pass", suite.get("status"), "benchmark suite must pass"),
        _check("diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "failure alignment diagnostic must pass"),
        _check("diagnostic_ready", as_dict(diagnostic.get("summary")).get("bounded_real_replay_failure_alignment_diagnostic_ready") is True, as_dict(diagnostic.get("summary")).get("bounded_real_replay_failure_alignment_diagnostic_ready"), "diagnostic summary must be ready"),
        _check("repair_seed_revision_passed", seed_revision.get("status") == "pass", seed_revision.get("status"), "repair seed revision must pass"),
        _check("cases_present", bool(cases), len(cases), "prompt-aligned seed must inspect benchmark cases"),
        _check("exact_prompt_examples_cover_cases", exact_prompt_count == len(cases), {"exact_prompt_examples": exact_prompt_count, "cases": len(cases)}, "each benchmark case needs one exact prompt answer example"),
        _check("seed_examples_have_text", all(str(row.get("text") or "").strip() for row in seed_examples), len(seed_examples), "every seed example must have text"),
    ]


def _revision(status: str, original_examples: list[dict[str, Any]], seed_examples: list[dict[str, Any]], cases: list[dict[str, Any]], diagnostic_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "original_example_count": len(original_examples),
        "added_example_count": max(0, len(seed_examples) - len(original_examples)),
        "example_count": len(seed_examples),
        "case_count": len(cases),
        "prompt_gap_count_from_diagnostic": diagnostic_summary.get("prompt_gap_count"),
        "exact_prompt_answer_count": sum(1 for row in seed_examples if row.get("revision_type") == "exact_benchmark_prompt_answer"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run",
        "next_step": "train_prompt_aligned_bounded_repair_seed" if status == "pass" else "repair_prompt_aligned_seed_revision",
    }


def _summary(status: str, checks: list[dict[str, Any]], revision: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_aligned_seed_revision_ready": status == "pass" and revision.get("ready") is True,
        "original_example_count": revision.get("original_example_count"),
        "added_example_count": revision.get("added_example_count"),
        "example_count": revision.get("example_count"),
        "case_count": revision.get("case_count"),
        "exact_prompt_answer_count": revision.get("exact_prompt_answer_count"),
        "proposed_next_artifact": revision.get("proposed_next_artifact"),
        "next_step": revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision"


def _interpretation(status: str, revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Prompt-aligned seed inputs are incomplete.", "next_action": "repair prompt-aligned seed inputs"}
    return {
        "model_quality_claim": "prompt_aligned_seed_only",
        "reason": "Exact benchmark prompts are now represented in the training seed; improvement still requires training and replay.",
        "next_action": revision.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CORPUS_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSONL_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision",
    "locate_benchmark_suite",
    "locate_failure_alignment_diagnostic",
    "locate_repair_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
