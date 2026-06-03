from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic.html"


def locate_prompt_aligned_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_prompt_aligned_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_CHECKPOINT_COMPARISON_JSON_FILENAME
    return source


def locate_prompt_aligned_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_SEED_REVISION_JSON_FILENAME
    return source


def locate_prompt_aligned_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("prompt-aligned failure diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic(
    prompt_aligned_replay: dict[str, Any],
    prompt_aligned_comparison: dict[str, Any],
    prompt_aligned_seed_revision: dict[str, Any],
    prompt_aligned_training_run: dict[str, Any],
    *,
    corpus_path: str | Path,
    replay_path: str | Path | None = None,
    comparison_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay prompt-aligned failure diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    corpus = Path(corpus_path).read_text(encoding="utf-8-sig") if Path(corpus_path).is_file() else ""
    replay_summary = as_dict(prompt_aligned_replay.get("summary"))
    comparison_summary = as_dict(prompt_aligned_comparison.get("summary"))
    seed_summary = as_dict(prompt_aligned_seed_revision.get("summary"))
    training_summary = as_dict(prompt_aligned_training_run.get("summary"))
    seed_text = "\n".join(str(row.get("text", "")) for row in list_of_dicts(prompt_aligned_seed_revision.get("seed_examples")))
    case_rows = [_case_diagnostic(row, seed_text, corpus) for row in list_of_dicts(prompt_aligned_replay.get("replay_rows"))]
    root_causes = _root_causes(case_rows, comparison_summary, seed_summary, training_summary)
    checks = _checks(prompt_aligned_replay, prompt_aligned_comparison, prompt_aligned_seed_revision, prompt_aligned_training_run, corpus, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes, comparison_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_prompt_aligned_replay": str(replay_path or ""),
        "source_prompt_aligned_comparison": str(comparison_path or ""),
        "source_prompt_aligned_seed_revision": str(seed_revision_path or ""),
        "source_prompt_aligned_training_run": str(training_run_path or ""),
        "source_corpus": str(corpus_path),
        "source_summaries": {
            "replay": replay_summary,
            "comparison": comparison_summary,
            "seed_revision": seed_summary,
            "training_run": training_summary,
        },
        "case_diagnostics": case_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "diagnostic": diagnostic,
        "summary": _summary(status, checks, diagnostic),
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    return 1 if require_diagnostic_ready and report.get("status") != "pass" else 0


def _case_diagnostic(row: dict[str, Any], seed_text: str, corpus: str) -> dict[str, Any]:
    prompt = str(row.get("prompt") or "")
    continuation = str(row.get("continuation") or "")
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    prompt_in_seed = bool(prompt and prompt in seed_text)
    prompt_in_corpus = bool(prompt and prompt in corpus)
    term_seed_count = _term_count(seed_text, expected_terms)
    term_corpus_count = _term_count(corpus, expected_terms)
    zero_hit = not hit_terms
    fragment_like = _fragment_like(continuation, expected_terms)
    return {
        "case_id": str(row.get("case_id") or ""),
        "case_pass": row.get("case_pass") is True,
        "prompt_in_seed": prompt_in_seed,
        "prompt_in_corpus": prompt_in_corpus,
        "expected_terms": expected_terms,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "zero_hit": zero_hit,
        "fragment_like_generation": fragment_like,
        "term_seed_count": term_seed_count,
        "term_corpus_count": term_corpus_count,
        "continuation_preview": continuation[:120],
        "diagnosis": _diagnosis(prompt_in_corpus, zero_hit, fragment_like, term_corpus_count),
        "recommended_action": _recommended_action(prompt_in_corpus, zero_hit, fragment_like),
    }


def _term_count(text: str, terms: list[str]) -> dict[str, int]:
    lowered = text.lower()
    return {term: lowered.count(term.lower()) for term in terms}


def _fragment_like(continuation: str, expected_terms: list[str]) -> bool:
    lowered = continuation.lower()
    if any(term.lower() in lowered for term in expected_terms):
        return False
    letters = sum(1 for char in lowered if "a" <= char <= "z")
    spaces = lowered.count(" ")
    return letters > 0 and spaces >= max(2, letters // 4)


def _diagnosis(prompt_in_corpus: bool, zero_hit: bool, fragment_like: bool, term_corpus_count: dict[str, int]) -> str:
    if not zero_hit:
        return "partial_term_expression"
    if not prompt_in_corpus:
        return "prompt_not_represented_in_training_corpus"
    if fragment_like:
        return "character_fragmentation_without_term_anchoring"
    if all(count > 0 for count in term_corpus_count.values()):
        return "terms_present_but_not_decoded"
    return "terms_underrepresented"


def _recommended_action(prompt_in_corpus: bool, zero_hit: bool, fragment_like: bool) -> str:
    if not prompt_in_corpus:
        return "repair_prompt_corpus_alignment"
    if zero_hit and fragment_like:
        return "run_decoder_anchor_or_forced_prefix_probe"
    if zero_hit:
        return "add_output_anchor_examples"
    return "preserve_partial_hit_and_probe_missing_term"


def _root_causes(
    case_rows: list[dict[str, Any]],
    comparison_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    training_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    causes = []
    failed = [row for row in case_rows if row.get("case_pass") is not True]
    exact_prompt_count = int(seed_summary.get("exact_prompt_answer_count") or 0)
    if failed and exact_prompt_count and all(row.get("prompt_in_corpus") is True for row in case_rows):
        causes.append({"cause_id": "exact_prompts_present_but_generation_unanchored", "severity": "high", "evidence": exact_prompt_count, "detail": "The corpus contains exact prompts, but replay still misses fixed/loss."})
    zero_hit_count = sum(1 for row in case_rows if row.get("zero_hit") is True)
    if zero_hit_count:
        causes.append({"cause_id": "zero_required_term_hits", "severity": "high", "evidence": zero_hit_count, "detail": "Replay continuations did not contain any expected required terms."})
    fragment_count = sum(1 for row in case_rows if row.get("fragment_like_generation") is True)
    if fragment_count:
        causes.append({"cause_id": "character_fragmentation_dominates_generation", "severity": "medium", "evidence": fragment_count, "detail": "Continuations contain scattered character fragments instead of complete required terms."})
    if comparison_summary.get("prompt_aligned_checkpoint_regressed") is True and training_summary.get("final_val_loss") is not None:
        causes.append({"cause_id": "loss_reduction_did_not_transfer_to_replay", "severity": "medium", "evidence": training_summary.get("final_val_loss"), "detail": "The prompt-aligned run trained successfully, but replay still regressed against baseline."})
    return causes


def _checks(
    replay: dict[str, Any],
    comparison: dict[str, Any],
    seed: dict[str, Any],
    training: dict[str, Any],
    corpus: str,
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("prompt_aligned_replay_passed", replay.get("status") == "pass", replay.get("status"), "prompt-aligned replay execution must pass"),
        _check("prompt_aligned_comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "prompt-aligned comparison must pass"),
        _check("promotion_blocked", as_dict(comparison.get("summary")).get("promotion_ready") is False, as_dict(comparison.get("summary")).get("promotion_ready"), "diagnostic should run only on blocked promotion evidence"),
        _check("seed_revision_passed", seed.get("status") == "pass", seed.get("status"), "prompt-aligned seed revision must pass"),
        _check("training_run_passed", training.get("status") == "pass", training.get("status"), "prompt-aligned training run must pass"),
        _check("corpus_present", bool(corpus.strip()), len(corpus), "prompt-aligned corpus must be readable"),
        _check("case_diagnostics_present", bool(case_rows), len(case_rows), "diagnostic must inspect replay cases"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], comparison_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "case_count": len(case_rows),
        "failed_case_count": sum(1 for row in case_rows if row.get("case_pass") is not True),
        "zero_hit_case_count": sum(1 for row in case_rows if row.get("zero_hit") is True),
        "fragment_like_case_count": sum(1 for row in case_rows if row.get("fragment_like_generation") is True),
        "prompt_in_corpus_count": sum(1 for row in case_rows if row.get("prompt_in_corpus") is True),
        "pass_rate_delta": comparison_summary.get("pass_rate_delta"),
        "root_cause_count": len(root_causes),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe",
        "next_step": "run_decoder_anchor_or_forced_prefix_probe" if status == "pass" else "repair_prompt_aligned_failure_diagnostic_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "prompt_aligned_failure_diagnostic_ready": status == "pass" and diagnostic.get("ready") is True,
        "case_count": diagnostic.get("case_count"),
        "failed_case_count": diagnostic.get("failed_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "fragment_like_case_count": diagnostic.get("fragment_like_case_count"),
        "prompt_in_corpus_count": diagnostic.get("prompt_in_corpus_count"),
        "pass_rate_delta": diagnostic.get("pass_rate_delta"),
        "root_cause_count": diagnostic.get("root_cause_count"),
        "proposed_next_artifact": diagnostic.get("proposed_next_artifact"),
        "next_step": diagnostic.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Prompt-aligned failure diagnostic inputs are incomplete.", "next_action": "repair diagnostic inputs"}
    return {
        "model_quality_claim": "not_improved",
        "reason": "Exact prompts are present, but replay output still fragments before emitting required terms.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic",
    "locate_prompt_aligned_comparison",
    "locate_prompt_aligned_replay",
    "locate_prompt_aligned_seed_revision",
    "locate_prompt_aligned_training_run",
    "read_json_report",
    "resolve_exit_code",
]
