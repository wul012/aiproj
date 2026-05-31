from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_refresh_forced_choice import (
    locate_pair_refresh_forced_choice_source,
    read_json_report,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import parse_generation_request
from minigpt.server_generator import MiniGPTGenerator


PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME = "model_capability_required_term_pair_constrained_decode_feasibility.json"
PAIR_CONSTRAINED_DECODE_FEASIBILITY_CSV_FILENAME = "model_capability_required_term_pair_constrained_decode_feasibility.csv"
PAIR_CONSTRAINED_DECODE_FEASIBILITY_TEXT_FILENAME = "model_capability_required_term_pair_constrained_decode_feasibility.txt"
PAIR_CONSTRAINED_DECODE_FEASIBILITY_MARKDOWN_FILENAME = "model_capability_required_term_pair_constrained_decode_feasibility.md"
PAIR_CONSTRAINED_DECODE_FEASIBILITY_HTML_FILENAME = "model_capability_required_term_pair_constrained_decode_feasibility.html"

DEFAULT_PROFILE_ID = "default"
BLOCK_COMPETING_INITIAL_PROFILE_ID = "block_competing_initial"
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_pair_constrained_decode_feasibility_source(path: str | Path) -> Path:
    return locate_pair_refresh_forced_choice_source(path)


def build_model_capability_required_term_pair_constrained_decode_feasibility(
    refresh_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    max_new_tokens: int = 12,
    temperature: float = 0.8,
    top_k: int = 2,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    training = as_dict(refresh_report.get("training"))
    replay = as_dict(refresh_report.get("replay_report"))
    checkpoint_path = str(training.get("checkpoint_path") or "")
    tokenizer_path = str(training.get("tokenizer_path") or "")
    terms = _terms(replay)
    issues = _input_issues(training, checkpoint_path, tokenizer_path, terms, generate_func=generate_func)
    generator = generate_func or _cached_generator(checkpoint_path, tokenizer_path, device=device)

    case_rows: list[dict[str, Any]] = []
    if not issues:
        for term in terms:
            for profile in _profiles_for_term(term, terms):
                row = _run_case(
                    term,
                    profile,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    device=device,
                    checkpoint_path=checkpoint_path,
                    tokenizer_path=tokenizer_path,
                    generate_func=generator,
                )
                case_rows.append(row)
                if row.get("status") != "pass":
                    issues.append(f"{row.get('term')} {row.get('profile_id')} generation failed: {row.get('error')}")

    profile_rows = _profile_rows(case_rows, terms)
    summary = _summary(profile_rows, case_rows, terms)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair constrained decode feasibility",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_coexistence_refresh": "" if source_path is None else str(source_path),
        "out_dir": str(out_dir),
        "settings": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "decode-only feasibility check; no retraining and no checkpoint mutation",
        },
        "training": {
            "checkpoint_path": checkpoint_path,
            "tokenizer_path": tokenizer_path,
            "checkpoint_exists": Path(checkpoint_path).is_file(),
            "tokenizer_exists": Path(tokenizer_path).is_file(),
        },
        "terms": terms,
        "case_rows": case_rows,
        "profile_rows": profile_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _terms(replay: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in list_of_dicts(replay.get("case_rows")):
        term = str(case.get("term") or "").strip()
        if not term or term in seen:
            continue
        seen.add(term)
        rows.append(
            {
                "term": term,
                "prompt": case.get("prompt") or f"{term}:",
                "generation_seed": int(case.get("generation_seed") or 0),
            }
        )
    return rows


def _input_issues(
    training: dict[str, Any],
    checkpoint_path: str,
    tokenizer_path: str,
    terms: list[dict[str, Any]],
    *,
    generate_func: GenerateFunc | None,
) -> list[str]:
    issues: list[str] = []
    if not training:
        issues.append("refresh report has no training object")
    if len(terms) < 2:
        issues.append("refresh report has fewer than two terms to constrain")
    if generate_func is None:
        if not checkpoint_path or not Path(checkpoint_path).is_file():
            issues.append("checkpoint_path is missing or does not exist")
        if not tokenizer_path or not Path(tokenizer_path).is_file():
            issues.append("tokenizer_path is missing or does not exist")
    return issues


def _profiles_for_term(term: dict[str, Any], terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    competitor = next((row for row in terms if row.get("term") != term.get("term")), {})
    competitor_term = str(competitor.get("term") or "")
    competitor_initial = competitor_term[:1]
    return [
        {"profile_id": DEFAULT_PROFILE_ID, "blocked_token_texts": (), "blocked_reason": "none"},
        {
            "profile_id": BLOCK_COMPETING_INITIAL_PROFILE_ID,
            "blocked_token_texts": (competitor_initial,) if competitor_initial else (),
            "blocked_reason": f"block competing initial for {competitor_term}",
        },
    ]


def _run_case(
    term: dict[str, Any],
    profile: dict[str, Any],
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
    checkpoint_path: str,
    tokenizer_path: str,
    generate_func: GenerateFunc,
) -> dict[str, Any]:
    request = {
        "prompt": str(term.get("prompt")),
        "expected_term": str(term.get("term")),
        "profile_id": profile.get("profile_id"),
        "blocked_token_texts": tuple(profile.get("blocked_token_texts") or ()),
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": int(term.get("generation_seed") or 0),
        "device": device,
        "checkpoint_path": checkpoint_path,
        "tokenizer_path": tokenizer_path,
    }
    response: dict[str, Any] = {}
    error = ""
    try:
        response = generate_func(request)
    except Exception as exc:  # pragma: no cover - defensive report boundary
        error = f"{type(exc).__name__}: {exc}"
    continuation = str(response.get("continuation", ""))
    generated = str(response.get("generated", ""))
    expected = str(term.get("term"))
    return {
        "status": "pass" if not error else "fail",
        "error": error,
        "profile_id": profile.get("profile_id"),
        "blocked_reason": profile.get("blocked_reason"),
        "blocked_token_texts": list(profile.get("blocked_token_texts") or ()),
        "blocked_token_count": response.get("blocked_token_count", 0),
        "term": expected,
        "prompt": request["prompt"],
        "generation_seed": request["seed"],
        "generated": generated,
        "continuation": continuation,
        "generated_preview": generated.replace("\n", "\\n")[:120],
        "continuation_preview": continuation.replace("\n", "\\n")[:120],
        "continuation_hit": expected.lower() in continuation.lower(),
    }


def _cached_generator(checkpoint_path: str, tokenizer_path: str, *, device: str) -> GenerateFunc:
    generator = MiniGPTGenerator(checkpoint_path, tokenizer_path, device=device)

    def generate(request: dict[str, Any]) -> dict[str, Any]:
        parsed = parse_generation_request(
            {
                "prompt": request["prompt"],
                "max_new_tokens": request["max_new_tokens"],
                "temperature": request["temperature"],
                "top_k": request["top_k"],
                "seed": request["seed"],
                "generation_profile": "default",
                "blocked_token_texts": list(request.get("blocked_token_texts") or []),
            }
        )
        return generator.generate(parsed).to_dict()

    return generate


def _profile_rows(case_rows: list[dict[str, Any]], terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected_terms = [str(term.get("term")) for term in terms]
    rows: list[dict[str, Any]] = []
    for profile_id in sorted({str(row.get("profile_id")) for row in case_rows}):
        scoped = [row for row in case_rows if str(row.get("profile_id")) == profile_id]
        hit_terms = [str(row.get("term")) for row in scoped if row.get("continuation_hit")]
        rows.append(
            {
                "profile_id": profile_id,
                "case_count": len(scoped),
                "hit_terms": hit_terms,
                "missed_terms": [term for term in expected_terms if term not in hit_terms],
                "hit_count": len(hit_terms),
                "pair_full_hit": bool(expected_terms) and len(hit_terms) == len(expected_terms),
                "blocked_token_count_total": sum(int(row.get("blocked_token_count") or 0) for row in scoped),
            }
        )
    return rows


def _summary(profile_rows: list[dict[str, Any]], case_rows: list[dict[str, Any]], terms: list[dict[str, Any]]) -> dict[str, Any]:
    default = _profile_row(profile_rows, DEFAULT_PROFILE_ID)
    constrained = _profile_row(profile_rows, BLOCK_COMPETING_INITIAL_PROFILE_ID)
    best = max(profile_rows, key=lambda row: (int(row.get("hit_count") or 0), bool(row.get("pair_full_hit")), str(row.get("profile_id") or "")), default={})
    fixed_default = _case_row(case_rows, DEFAULT_PROFILE_ID, "fixed")
    fixed_constrained = _case_row(case_rows, BLOCK_COMPETING_INITIAL_PROFILE_ID, "fixed")
    return {
        "term_count": len(terms),
        "profile_count": len(profile_rows),
        "default_hit_count": default.get("hit_count", 0),
        "constrained_hit_count": constrained.get("hit_count", 0),
        "hit_delta": int(constrained.get("hit_count") or 0) - int(default.get("hit_count") or 0),
        "default_pair_full": bool(default.get("pair_full_hit")),
        "constrained_pair_full": bool(constrained.get("pair_full_hit")),
        "best_profile_id": best.get("profile_id", ""),
        "best_hit_count": best.get("hit_count", 0),
        "fixed_default_hit": bool(fixed_default.get("continuation_hit")),
        "fixed_constrained_hit": bool(fixed_constrained.get("continuation_hit")),
    }


def _profile_row(rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id:
            return row
    return {}


def _case_row(rows: list[dict[str, Any]], profile_id: str, term: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id and row.get("term") == term:
            return row
    return {}


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_constrained_decode_feasibility"
    if summary.get("constrained_pair_full"):
        return "required_term_pair_constrained_decode_pair_full_feasible"
    if summary.get("fixed_constrained_hit") and not summary.get("fixed_default_hit"):
        return "required_term_pair_constrained_decode_fixed_recoverable"
    if int(summary.get("hit_delta") or 0) > 0:
        return "required_term_pair_constrained_decode_partial_gain"
    return "required_term_pair_constrained_decode_not_feasible"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The constrained decode source is not executable."
        next_action = "repair checkpoint/tokenizer inputs before testing decode constraints"
    elif summary.get("constrained_pair_full"):
        reason = "Blocking the competing initial recovers both fixed and loss continuations without retraining."
        next_action = "promote constrained decoding as a mitigation and test held-out equals prompts"
    elif summary.get("fixed_constrained_hit") and not summary.get("fixed_default_hit"):
        reason = "Blocking the competing initial recovers fixed, but pair-full is not fully proven."
        next_action = "turn the constraint into a named profile and replay held-out surfaces"
    elif int(summary.get("hit_delta") or 0) > 0:
        reason = "The constraint improves some continuations but does not recover the fixed/loss pair."
        next_action = "inspect which term remains missed before promoting a decode profile"
    else:
        reason = "The constraint does not improve fixed/loss continuation hits."
        next_action = "return to objective/capacity changes instead of decode-only mitigation"
    return {
        "model_quality_claim": "decode_feasibility_only" if status == "pass" else "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_CONSTRAINED_DECODE_FEASIBILITY_CSV_FILENAME",
    "PAIR_CONSTRAINED_DECODE_FEASIBILITY_HTML_FILENAME",
    "PAIR_CONSTRAINED_DECODE_FEASIBILITY_JSON_FILENAME",
    "PAIR_CONSTRAINED_DECODE_FEASIBILITY_MARKDOWN_FILENAME",
    "PAIR_CONSTRAINED_DECODE_FEASIBILITY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_constrained_decode_feasibility",
    "locate_pair_constrained_decode_feasibility_source",
    "read_json_report",
    "resolve_exit_code",
]
