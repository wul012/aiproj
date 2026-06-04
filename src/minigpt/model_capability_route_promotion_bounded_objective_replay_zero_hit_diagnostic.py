from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import (
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_seed import (
    BOUNDED_OBJECTIVE_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_training_run import (
    BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.json"
BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.csv"
BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.txt"
BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.md"
BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic.html"


def locate_objective_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_objective_seed(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_SEED_JSON_FILENAME
    return source


def locate_objective_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective zero-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic(
    replay_comparison: dict[str, Any],
    objective_seed: dict[str, Any],
    objective_training_run: dict[str, Any],
    *,
    corpus_path: str | Path,
    replay_comparison_path: str | Path | None = None,
    objective_seed_path: str | Path | None = None,
    objective_training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective replay zero-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    corpus = Path(corpus_path).read_text(encoding="utf-8-sig") if Path(corpus_path).is_file() else ""
    replay_summary = as_dict(replay_comparison.get("summary"))
    seed_summary = as_dict(objective_seed.get("summary"))
    training_summary = as_dict(objective_training_run.get("summary"))
    case_rows = [_case_diagnostic(row, corpus) for row in list_of_dicts(replay_comparison.get("replay_rows"))]
    root_causes = _root_causes(case_rows, seed_summary, training_summary)
    checks = _checks(replay_comparison, objective_seed, objective_training_run, replay_summary, seed_summary, training_summary, corpus, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes, training_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_objective_seed": str(objective_seed_path or ""),
        "source_objective_training_run": str(objective_training_run_path or ""),
        "source_corpus": str(corpus_path),
        "source_summaries": {
            "replay_comparison": replay_summary,
            "objective_seed": seed_summary,
            "objective_training_run": training_summary,
        },
        "case_diagnostics": case_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "diagnostic": diagnostic,
        "summary": _summary(status, checks, diagnostic),
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_diagnostic_ready: bool) -> int:
    if require_diagnostic_ready and report.get("status") != "pass":
        return 1
    return 0


def _case_diagnostic(row: dict[str, Any], corpus: str) -> dict[str, Any]:
    prompt = str(row.get("prompt") or "")
    continuation = str(row.get("continuation") or "")
    required_terms = [str(term).lower() for term in row.get("required_terms", ["fixed", "loss"])]
    prompt_in_corpus = bool(prompt and prompt in corpus)
    term_corpus_count = {term: corpus.lower().count(term) for term in required_terms}
    near_miss_terms = _near_miss_terms(continuation, required_terms)
    return {
        "case_id": str(row.get("case_id") or ""),
        "case_pass": row.get("case_pass") is True,
        "prompt_in_corpus": prompt_in_corpus,
        "zero_hit": row.get("any_hit") is not True,
        "near_miss_terms": near_miss_terms,
        "term_corpus_count": term_corpus_count,
        "hit_terms": row.get("hit_terms", []),
        "missed_terms": row.get("missed_terms", []),
        "continuation_preview": continuation[:120],
        "diagnosis": _diagnosis(prompt_in_corpus, near_miss_terms, row),
        "recommended_action": _recommended_action(near_miss_terms),
    }


def _near_miss_terms(continuation: str, terms: list[str]) -> list[str]:
    words = re.findall(r"[a-zA-Z]+", continuation.lower())
    near = []
    for term in terms:
        if any(_levenshtein(word, term) == 1 for word in words):
            near.append(term)
    return near


def _levenshtein(left: str, right: str) -> int:
    if abs(len(left) - len(right)) > 1:
        return 2
    previous = list(range(len(right) + 1))
    for i, char_left in enumerate(left, start=1):
        current = [i]
        for j, char_right in enumerate(right, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_left != char_right)))
        previous = current
    return previous[-1]


def _diagnosis(prompt_in_corpus: bool, near_miss_terms: list[str], row: dict[str, Any]) -> str:
    if row.get("case_pass") is True:
        return "case_passed"
    if not prompt_in_corpus:
        return "prompt_not_present_in_objective_corpus"
    if near_miss_terms:
        return "near_miss_character_substitution_without_exact_term"
    if row.get("any_hit") is not True:
        return "zero_required_term_generation"
    return "partial_required_term_generation"


def _recommended_action(near_miss_terms: list[str]) -> str:
    if near_miss_terms:
        return "probe_decoder_anchor_and_exact_prefix_bias"
    return "add_output_position_anchor_or_capacity_probe"


def _root_causes(case_rows: list[dict[str, Any]], seed_summary: dict[str, Any], training_summary: dict[str, Any]) -> list[dict[str, Any]]:
    causes = []
    zero_hit_count = sum(1 for row in case_rows if row.get("zero_hit") is True)
    near_miss_count = sum(1 for row in case_rows if row.get("near_miss_terms"))
    prompt_in_corpus_count = sum(1 for row in case_rows if row.get("prompt_in_corpus") is True)
    if zero_hit_count:
        causes.append({"cause_id": "objective_replay_zero_required_term_hits", "severity": "high", "evidence": zero_hit_count, "detail": "All replay rows missed fixed/loss despite a trained checkpoint."})
    if near_miss_count:
        causes.append({"cause_id": "near_miss_character_substitution", "severity": "high", "evidence": near_miss_count, "detail": "Continuations are close to required terms, for example wixed, but do not exactly hit them."})
    if prompt_in_corpus_count == len(case_rows) and case_rows:
        causes.append({"cause_id": "direct_prompts_present_but_generation_unanchored", "severity": "medium", "evidence": prompt_in_corpus_count, "detail": "The direct objective prompts are present in corpus, so the failure is not a missing-prompt corpus gap."})
    if float(training_summary.get("train_loss_delta") or 0.0) < 0 and seed_summary.get("direct_example_count"):
        causes.append({"cause_id": "loss_reduction_did_not_transfer_to_exact_generation", "severity": "medium", "evidence": training_summary.get("train_loss_delta"), "detail": "Training loss dropped on direct examples, but generation did not recover exact required terms."})
    return causes


def _checks(
    replay: dict[str, Any],
    seed: dict[str, Any],
    training: dict[str, Any],
    replay_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    training_summary: dict[str, Any],
    corpus: str,
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("replay_comparison_passed", replay.get("status") == "pass", replay.get("status"), "objective replay comparison must pass"),
        _check("replay_comparison_ready", replay_summary.get("bounded_objective_replay_comparison_ready") is True, replay_summary.get("bounded_objective_replay_comparison_ready"), "objective replay comparison must be ready"),
        _check("objective_not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "diagnostic should run on unrecovered objective evidence"),
        _check("zero_hit_present", int(replay_summary.get("zero_hit_case_count") or 0) > 0, replay_summary.get("zero_hit_case_count"), "diagnostic needs zero-hit evidence"),
        _check("objective_seed_passed", seed.get("status") == "pass", seed.get("status"), "objective seed must pass"),
        _check("objective_seed_ready", seed_summary.get("bounded_objective_seed_ready") is True, seed_summary.get("bounded_objective_seed_ready"), "objective seed must be ready"),
        _check("training_run_passed", training.get("status") == "pass", training.get("status"), "objective training run must pass"),
        _check("training_run_ready", training_summary.get("bounded_objective_training_ready") is True, training_summary.get("bounded_objective_training_ready"), "objective training run must be ready"),
        _check("corpus_present", bool(corpus.strip()), len(corpus), "objective seed corpus must be readable"),
        _check("case_diagnostics_present", bool(case_rows), len(case_rows), "diagnostic must inspect replay rows"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], training_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "case_count": len(case_rows),
        "zero_hit_case_count": sum(1 for row in case_rows if row.get("zero_hit") is True),
        "near_miss_case_count": sum(1 for row in case_rows if row.get("near_miss_terms")),
        "prompt_in_corpus_count": sum(1 for row in case_rows if row.get("prompt_in_corpus") is True),
        "root_cause_count": len(root_causes),
        "final_train_loss": training_summary.get("final_train_loss"),
        "final_val_loss": training_summary.get("final_val_loss"),
        "train_loss_delta": training_summary.get("train_loss_delta"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_decoder_anchor_probe",
        "next_step": "run_bounded_objective_decoder_anchor_probe" if status == "pass" else "repair_bounded_objective_zero_hit_diagnostic_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_zero_hit_diagnostic_ready": status == "pass" and diagnostic.get("ready") is True,
        "case_count": diagnostic.get("case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "near_miss_case_count": diagnostic.get("near_miss_case_count"),
        "prompt_in_corpus_count": diagnostic.get("prompt_in_corpus_count"),
        "root_cause_count": diagnostic.get("root_cause_count"),
        "train_loss_delta": diagnostic.get("train_loss_delta"),
        "proposed_next_artifact": diagnostic.get("proposed_next_artifact"),
        "next_step": diagnostic.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic_ready"
    return "fix_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Zero-hit diagnostic inputs are incomplete.", "next_action": "repair zero-hit diagnostic inputs"}
    return {
        "model_quality_claim": "not_improved_diagnosed",
        "reason": "Direct prompts are present and training loss fell, but replay still has zero exact required-term hits.",
        "next_action": diagnostic.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic",
    "locate_objective_replay_comparison",
    "locate_objective_seed",
    "locate_objective_training_run",
    "read_json_report",
    "resolve_exit_code",
]
