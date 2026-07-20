from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.generation_profiles import DEFAULT_GENERATION_PROFILE_ID, NEWLINE_SUPPRESSION_PROFILE_ID
from minigpt.report_utils import list_of_dicts, utc_now
from minigpt.server_contracts import parse_generation_request
from minigpt.server_generator import MiniGPTGenerator


PAIR_GENERATION_PROFILE_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_generation_profile_replay.json"
PAIR_GENERATION_PROFILE_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_generation_profile_replay.csv"
PAIR_GENERATION_PROFILE_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_generation_profile_replay.txt"
PAIR_GENERATION_PROFILE_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_generation_profile_replay.md"
PAIR_GENERATION_PROFILE_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_generation_profile_replay.html"

DEFAULT_PROFILE_IDS = (DEFAULT_GENERATION_PROFILE_ID, NEWLINE_SUPPRESSION_PROFILE_ID)
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("source report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_generation_profile_replay(
    source_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    variant_limit: int = 3,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    terms = _terms(source_report)
    training_rows = _training_rows(source_report, variant_limit=variant_limit)
    generator = generate_func or _cached_generator(device=device)
    case_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for variant_index, training_row in enumerate(training_rows):
        for term_index, term in enumerate(terms):
            for profile_id in profiles:
                row = _run_case(
                    training_row,
                    term,
                    profile_id=profile_id,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    device=device,
                    generation_seed=_generation_seed(source_report, training_row, term, variant_index, term_index),
                    generate_func=generator,
                )
                case_rows.append(row)
                if row.get("status") != "pass":
                    issues.append(_issue_from_row(row))
    variant_rows = _variant_rows(case_rows, terms)
    profile_rows = _profile_rows(case_rows, variant_rows)
    summary = _summary(profile_rows, variant_rows, terms, training_rows)
    decision = _decision(summary)
    status = "pass" if not issues else "fail"
    if status == "fail":
        decision = "fix_generation_profile_pair_replay_execution"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair generation profile replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_branch_retention_sweep": "" if source_path is None else str(source_path),
        "out_dir": str(out_dir),
        "settings": {
            "profiles": list(profiles),
            "variant_limit": variant_limit,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "replay named generation profiles over archived fixed/loss branch-retention checkpoints without retraining",
        },
        "terms": terms,
        "case_rows": case_rows,
        "variant_rows": variant_rows,
        "profile_rows": profile_rows,
        "summary": summary,
        "interpretation": _interpretation(decision, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_case(
    training_row: dict[str, Any],
    term: dict[str, Any],
    *,
    profile_id: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
    generation_seed: int,
    generate_func: GenerateFunc,
) -> dict[str, Any]:
    checkpoint = Path(str(training_row.get("checkpoint_path", "")))
    tokenizer = Path(str(training_row.get("tokenizer_path") or checkpoint.parent / "tokenizer.json"))
    request = {
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "prompt": str(term.get("scaffold_prompt") or f"{term.get('term')}:"),
        "expected_term": str(term.get("term")),
        "profile_id": profile_id,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": generation_seed,
        "device": device,
    }
    response: dict[str, Any] = {}
    error = ""
    if not checkpoint.is_file():
        error = "checkpoint missing"
    elif not tokenizer.is_file():
        error = "tokenizer missing"
    else:
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
        "pair_id": training_row.get("pair_id"),
        "variant_id": training_row.get("variant_id"),
        "branch_retention_run_id": training_row.get("branch_retention_run_id"),
        "profile_id": profile_id,
        "term": expected,
        "prompt": request["prompt"],
        "generation_seed": generation_seed,
        "checkpoint_path": str(checkpoint),
        "checkpoint_exists": checkpoint.is_file(),
        "tokenizer_path": str(tokenizer),
        "tokenizer_exists": tokenizer.is_file(),
        "generated": generated,
        "continuation": continuation,
        "generated_preview": generated.replace("\n", "\\n")[:120],
        "continuation_preview": continuation.replace("\n", "\\n")[:120],
        "continuation_hit": _term_hit(continuation, expected),
        "newline_cleanup_hit": _term_hit(continuation.replace("\n", "").replace("\r", ""), expected),
        "blocked_token_count": response.get("blocked_token_count", 0),
    }


def _cached_generator(*, device: str) -> GenerateFunc:
    cache: dict[tuple[str, str], MiniGPTGenerator] = {}

    def generate(request: dict[str, Any]) -> dict[str, Any]:
        checkpoint = str(request["checkpoint_path"])
        tokenizer = str(request["tokenizer_path"])
        key = (checkpoint, tokenizer)
        if key not in cache:
            cache[key] = MiniGPTGenerator(checkpoint, tokenizer, device=device)
        parsed = parse_generation_request(
            {
                "prompt": request["prompt"],
                "max_new_tokens": request["max_new_tokens"],
                "temperature": request["temperature"],
                "top_k": request["top_k"],
                "seed": request["seed"],
                "generation_profile": request["profile_id"],
            }
        )
        return cache[key].generate(parsed).to_dict()

    return generate


def _terms(source: dict[str, Any]) -> list[dict[str, Any]]:
    targets = list_of_dicts(source.get("targets"))
    if not targets:
        return []
    terms = []
    for item in list_of_dicts(targets[0].get("terms")):
        term = str(item.get("term", "")).strip()
        if term:
            terms.append(
                {
                    "case": item.get("case"),
                    "term": term,
                    "scaffold_prompt": item.get("scaffold_prompt") or f"{term}:",
                    "source_hit_rate": item.get("source_hit_rate"),
                }
            )
    return terms


def _training_rows(source: dict[str, Any], *, variant_limit: int) -> list[dict[str, Any]]:
    rows = [row for row in list_of_dicts(source.get("training_rows")) if row.get("checkpoint_path")]
    return rows[: max(0, variant_limit)]


def _generation_seed(
    source: dict[str, Any],
    training_row: dict[str, Any],
    term: dict[str, Any],
    variant_index: int,
    term_index: int,
) -> int:
    variant_id = str(training_row.get("variant_id"))
    term_name = str(term.get("term"))
    for row in list_of_dicts(source.get("probe_rows")):
        if str(row.get("variant_id")) == variant_id and str(row.get("term")) == term_name:
            return _int(row.get("generation_seed"), 0)
    base_seed = _int(training_row.get("seed"), 0)
    return base_seed + (variant_index * 100) + term_index


def _variant_rows(case_rows: list[dict[str, Any]], terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    profile_ids = sorted({str(row.get("profile_id")) for row in case_rows})
    variant_ids = []
    for row in case_rows:
        variant_id = str(row.get("variant_id"))
        if variant_id not in variant_ids:
            variant_ids.append(variant_id)
    expected_terms = [str(term.get("term")) for term in terms]
    for variant_id in variant_ids:
        for profile_id in profile_ids:
            scoped = [row for row in case_rows if row.get("variant_id") == variant_id and row.get("profile_id") == profile_id]
            hit_terms = [str(row.get("term")) for row in scoped if row.get("continuation_hit")]
            missed_terms = [term for term in expected_terms if term not in hit_terms]
            rows.append(
                {
                    "variant_id": variant_id,
                    "profile_id": profile_id,
                    "term_count": len(expected_terms),
                    "hit_terms": hit_terms,
                    "missed_terms": missed_terms,
                    "hit_count": len(hit_terms),
                    "pair_full_hit": len(hit_terms) == len(expected_terms) and bool(expected_terms),
                }
            )
    return rows


def _profile_rows(case_rows: list[dict[str, Any]], variant_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for profile_id in sorted({str(row.get("profile_id")) for row in case_rows}):
        scoped_cases = [row for row in case_rows if row.get("profile_id") == profile_id]
        scoped_variants = [row for row in variant_rows if row.get("profile_id") == profile_id]
        rows.append(
            {
                "profile_id": profile_id,
                "case_count": len(scoped_cases),
                "continuation_hit_count": sum(1 for row in scoped_cases if row.get("continuation_hit")),
                "newline_cleanup_hit_count": sum(1 for row in scoped_cases if row.get("newline_cleanup_hit")),
                "pair_full_variant_count": sum(1 for row in scoped_variants if row.get("pair_full_hit")),
                "variant_count": len(scoped_variants),
                "blocked_token_count_total": sum(_int(row.get("blocked_token_count"), 0) for row in scoped_cases),
            }
        )
    return rows


def _summary(
    profile_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    terms: list[dict[str, Any]],
    training_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    default_profile = _profile_row(profile_rows, DEFAULT_GENERATION_PROFILE_ID)
    suppression_profile = _profile_row(profile_rows, NEWLINE_SUPPRESSION_PROFILE_ID)
    return {
        "variant_count": len(training_rows),
        "term_count": len(terms),
        "profile_count": len(profile_rows),
        "default_pair_full_variant_count": default_profile.get("pair_full_variant_count", 0),
        "suppression_pair_full_variant_count": suppression_profile.get("pair_full_variant_count", 0),
        "default_continuation_hit_count": default_profile.get("continuation_hit_count", 0),
        "suppression_continuation_hit_count": suppression_profile.get("continuation_hit_count", 0),
        "suppression_hit_delta": _int(suppression_profile.get("continuation_hit_count"), 0) - _int(default_profile.get("continuation_hit_count"), 0),
        "suppression_pair_full_delta": _int(suppression_profile.get("pair_full_variant_count"), 0) - _int(default_profile.get("pair_full_variant_count"), 0),
        "pair_full_rows": [row for row in variant_rows if row.get("pair_full_hit")],
    }


def _decision(summary: dict[str, Any]) -> str:
    pair_delta = _int(summary.get("suppression_pair_full_delta"), 0)
    hit_delta = _int(summary.get("suppression_hit_delta"), 0)
    if pair_delta > 0:
        return "generation_profile_improves_pair_coexistence"
    if hit_delta > 0:
        return "generation_profile_partial_pair_surface_only"
    return "generation_profile_no_pair_coexistence_gain"


def _interpretation(decision: str, summary: dict[str, Any]) -> dict[str, Any]:
    if decision == "generation_profile_improves_pair_coexistence":
        reason = "The suppression profile increased the number of variants where fixed/loss both appear."
        next_action = "Promote the profile into the next pair benchmark before retraining."
    elif decision == "generation_profile_partial_pair_surface_only":
        reason = "The suppression profile helped individual continuations but did not create full fixed/loss coexistence."
        next_action = "Keep the profile as decode-surface hygiene and continue with pair-training changes."
    else:
        reason = "The suppression profile did not improve fixed/loss continuation hits on archived pair-retention checkpoints."
        next_action = "Treat newline suppression as loss-alias cleanup only; the next model-capability step should train for pair coexistence."
    return {
        "model_quality_claim": "not_claimed",
        "reason": reason,
        "next_action": next_action,
        "summary": summary,
    }


def _profile_row(rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id:
            return row
    return {}


def _term_hit(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _issue_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "generation_case_failed",
        "variant_id": row.get("variant_id"),
        "profile_id": row.get("profile_id"),
        "term": row.get("term"),
        "detail": row.get("error"),
    }


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "DEFAULT_PROFILE_IDS",
    "PAIR_GENERATION_PROFILE_REPLAY_CSV_FILENAME",
    "PAIR_GENERATION_PROFILE_REPLAY_HTML_FILENAME",
    "PAIR_GENERATION_PROFILE_REPLAY_JSON_FILENAME",
    "PAIR_GENERATION_PROFILE_REPLAY_MARKDOWN_FILENAME",
    "PAIR_GENERATION_PROFILE_REPLAY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_generation_profile_replay",
    "read_json_report",
    "resolve_exit_code",
]
