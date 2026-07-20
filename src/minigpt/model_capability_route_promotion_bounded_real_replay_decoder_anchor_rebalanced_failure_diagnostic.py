from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_checkpoint_comparison import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic.html"


def locate_rebalanced_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_rebalanced_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_CHECKPOINT_COMPARISON_JSON_FILENAME
    return source


def locate_rebalanced_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME
    return source


def locate_rebalanced_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("rebalanced failure diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic(
    rebalanced_replay: dict[str, Any],
    rebalanced_comparison: dict[str, Any],
    rebalanced_seed_revision: dict[str, Any],
    rebalanced_training_run: dict[str, Any],
    *,
    corpus_path: str | Path,
    replay_path: str | Path | None = None,
    comparison_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced failure diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    corpus = Path(corpus_path).read_text(encoding="utf-8-sig") if Path(corpus_path).is_file() else ""
    replay_summary = as_dict(rebalanced_replay.get("summary"))
    comparison_summary = as_dict(rebalanced_comparison.get("summary"))
    seed_summary = as_dict(rebalanced_seed_revision.get("summary"))
    training_summary = as_dict(rebalanced_training_run.get("summary"))
    seed_text = "\n".join(str(row.get("text", "")) for row in list_of_dicts(rebalanced_seed_revision.get("seed_examples")))
    case_rows = [_case_diagnostic(row, seed_text, corpus) for row in list_of_dicts(rebalanced_replay.get("replay_rows"))]
    root_causes = _root_causes(case_rows, comparison_summary, seed_summary, training_summary)
    checks = _checks(rebalanced_replay, rebalanced_comparison, rebalanced_seed_revision, rebalanced_training_run, corpus, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes, comparison_summary, seed_summary, training_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_rebalanced_replay": str(replay_path or ""),
        "source_rebalanced_comparison": str(comparison_path or ""),
        "source_rebalanced_seed_revision": str(seed_revision_path or ""),
        "source_rebalanced_training_run": str(training_run_path or ""),
        "source_corpus": str(corpus_path),
        "source_summaries": {
            "replay": replay_summary,
            "comparison": comparison_summary,
            "rebalanced_seed_revision": seed_summary,
            "rebalanced_training_run": training_summary,
        },
        "case_diagnostics": case_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "diagnostic": diagnostic,
        "summary": _summary(status, checks, diagnostic),
        "interpretation": _interpretation(status, diagnostic),
    }


def _case_diagnostic(row: dict[str, Any], seed_text: str, corpus: str) -> dict[str, Any]:
    prompt = str(row.get("prompt") or "")
    continuation = str(row.get("continuation") or "")
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    hit_terms = [str(term) for term in row.get("hit_terms", [])]
    missed_terms = [str(term) for term in row.get("missed_terms", [])]
    prompt_in_seed = bool(prompt and prompt in seed_text)
    prompt_in_corpus = bool(prompt and prompt in corpus)
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
        "term_seed_count": _term_count(seed_text, expected_terms),
        "term_corpus_count": _term_count(corpus, expected_terms),
        "continuation_preview": continuation[:120],
        "diagnosis": _diagnosis(prompt_in_corpus, zero_hit, fragment_like),
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
    repeated = max((lowered.count(char) for char in set(lowered) if "a" <= char <= "z"), default=0)
    spaces = lowered.count(" ")
    return letters > 0 and (spaces >= 2 or repeated >= 4)


def _diagnosis(prompt_in_corpus: bool, zero_hit: bool, fragment_like: bool) -> str:
    if not zero_hit:
        return "partial_term_expression"
    if not prompt_in_corpus:
        return "prompt_not_represented_in_rebalanced_corpus"
    if fragment_like:
        return "rebalanced_training_still_fragmented"
    return "rebalanced_terms_present_but_not_decoded"


def _recommended_action(prompt_in_corpus: bool, zero_hit: bool, fragment_like: bool) -> str:
    if not prompt_in_corpus:
        return "repair_rebalanced_prompt_corpus_alignment"
    if zero_hit and fragment_like:
        return "run_rebalanced_decoder_profile_sweep_before_more_training"
    if zero_hit:
        return "probe_longer_or_greedy_decoding_before_more_training"
    return "preserve_partial_hit_and_probe_missing_term"


def _root_causes(case_rows: list[dict[str, Any]], comparison_summary: dict[str, Any], seed_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, Any]]:
    causes = []
    zero_hit_count = sum(1 for row in case_rows if row.get("zero_hit") is True)
    fragment_count = sum(1 for row in case_rows if row.get("fragment_like_generation") is True)
    distribution_repaired = float(seed_summary.get("direct_answer_share") or 0.0) >= 0.2 and float(seed_summary.get("carry_forward_share") or 1.0) <= 0.5
    if distribution_repaired and zero_hit_count == len(case_rows) and case_rows:
        causes.append({"cause_id": "rebalanced_distribution_repaired_but_replay_zero_hit", "severity": "high", "evidence": {"direct_share": seed_summary.get("direct_answer_share"), "carry_share": seed_summary.get("carry_forward_share")}, "detail": "The direct/carry distribution was repaired, but replay still produced zero required-term hits."})
    if zero_hit_count:
        causes.append({"cause_id": "zero_required_term_hits_after_rebalance", "severity": "high", "evidence": zero_hit_count, "detail": "All or some rebalanced replay cases still miss every required term."})
    if fragment_count:
        causes.append({"cause_id": "fragmented_generation_after_rebalance", "severity": "medium", "evidence": fragment_count, "detail": "The checkpoint emits fragments or repeated characters instead of complete fixed/loss terms."})
    if comparison_summary.get("rebalanced_checkpoint_recovered_over_decoder_anchor") is False and training_summary.get("final_val_loss") is not None:
        causes.append({"cause_id": "rebalanced_loss_did_not_recover_replay", "severity": "medium", "evidence": training_summary.get("final_val_loss"), "detail": "The rebalanced training run completed, but bounded replay did not recover over the decoder-anchor checkpoint."})
    return causes


def _checks(replay: dict[str, Any], comparison: dict[str, Any], seed: dict[str, Any], training: dict[str, Any], corpus: str, case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparison_summary = as_dict(comparison.get("summary"))
    return [
        _check("rebalanced_replay_passed", replay.get("status") == "pass", replay.get("status"), "rebalanced replay execution must pass"),
        _check("rebalanced_comparison_passed", comparison.get("status") == "pass", comparison.get("status"), "rebalanced checkpoint comparison must pass"),
        _check("promotion_blocked", comparison_summary.get("promotion_ready") is False, comparison_summary.get("promotion_ready"), "diagnostic should run only on blocked promotion evidence"),
        _check("rebalanced_seed_passed", seed.get("status") == "pass", seed.get("status"), "rebalanced seed revision must pass"),
        _check("rebalanced_training_passed", training.get("status") == "pass", training.get("status"), "rebalanced training run must pass"),
        _check("corpus_present", bool(corpus.strip()), len(corpus), "rebalanced corpus must be readable"),
        _check("case_diagnostics_present", bool(case_rows), len(case_rows), "diagnostic must inspect replay cases"),
    ]


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], comparison_summary: dict[str, Any], seed_summary: dict[str, Any], training_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "case_count": len(case_rows),
        "failed_case_count": sum(1 for row in case_rows if row.get("case_pass") is not True),
        "zero_hit_case_count": sum(1 for row in case_rows if row.get("zero_hit") is True),
        "fragment_like_case_count": sum(1 for row in case_rows if row.get("fragment_like_generation") is True),
        "prompt_in_corpus_count": sum(1 for row in case_rows if row.get("prompt_in_corpus") is True),
        "direct_answer_share": seed_summary.get("direct_answer_share"),
        "carry_forward_share": seed_summary.get("carry_forward_share"),
        "final_val_loss": training_summary.get("final_val_loss"),
        "rebalanced_vs_baseline_pass_rate_delta": comparison_summary.get("rebalanced_vs_baseline_pass_rate_delta"),
        "rebalanced_vs_decoder_anchor_pass_rate_delta": comparison_summary.get("rebalanced_vs_decoder_anchor_pass_rate_delta"),
        "root_cause_count": len(root_causes),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep",
        "next_step": "run_rebalanced_decoder_profile_sweep_before_more_training" if status == "pass" else "repair_rebalanced_failure_diagnostic_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "rebalanced_failure_diagnostic_ready": status == "pass" and diagnostic.get("ready") is True,
        "case_count": diagnostic.get("case_count"),
        "failed_case_count": diagnostic.get("failed_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "fragment_like_case_count": diagnostic.get("fragment_like_case_count"),
        "prompt_in_corpus_count": diagnostic.get("prompt_in_corpus_count"),
        "direct_answer_share": diagnostic.get("direct_answer_share"),
        "carry_forward_share": diagnostic.get("carry_forward_share"),
        "final_val_loss": diagnostic.get("final_val_loss"),
        "rebalanced_vs_baseline_pass_rate_delta": diagnostic.get("rebalanced_vs_baseline_pass_rate_delta"),
        "rebalanced_vs_decoder_anchor_pass_rate_delta": diagnostic.get("rebalanced_vs_decoder_anchor_pass_rate_delta"),
        "root_cause_count": diagnostic.get("root_cause_count"),
        "proposed_next_artifact": diagnostic.get("proposed_next_artifact"),
        "next_step": diagnostic.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Rebalanced failure diagnostic inputs are incomplete.", "next_action": "repair diagnostic inputs"}
    return {
        "model_quality_claim": "not_improved",
        "reason": "Rebalanced training repaired data distribution but did not recover bounded replay required-term generation.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic",
    "locate_rebalanced_comparison",
    "locate_rebalanced_replay",
    "locate_rebalanced_seed_revision",
    "locate_rebalanced_training_run",
    "read_json_report",
    "resolve_exit_code",
]
