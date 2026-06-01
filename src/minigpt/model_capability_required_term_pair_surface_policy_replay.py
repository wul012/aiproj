from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_aligned_candidate_seed_stability import (
    PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_surface_policy_plan import (
    PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import parse_generation_request
from minigpt.server_generator import MiniGPTGenerator


PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME = "model_capability_required_term_pair_surface_policy_replay.json"
PAIR_SURFACE_POLICY_REPLAY_CSV_FILENAME = "model_capability_required_term_pair_surface_policy_replay.csv"
PAIR_SURFACE_POLICY_REPLAY_TEXT_FILENAME = "model_capability_required_term_pair_surface_policy_replay.txt"
PAIR_SURFACE_POLICY_REPLAY_MARKDOWN_FILENAME = "model_capability_required_term_pair_surface_policy_replay.md"
PAIR_SURFACE_POLICY_REPLAY_HTML_FILENAME = "model_capability_required_term_pair_surface_policy_replay.html"

DEFAULT_TARGET_TERMS = ("fixed", "loss")
GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_surface_policy_replay_stability_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_ALIGNED_CANDIDATE_SEED_STABILITY_JSON_FILENAME
    return source


def locate_surface_policy_replay_plan_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_SURFACE_POLICY_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("surface policy replay input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_surface_policy_replay(
    stability_report: dict[str, Any],
    policy_plan: dict[str, Any],
    *,
    out_dir: str | Path,
    stability_source_path: str | Path | None = None,
    policy_plan_source_path: str | Path | None = None,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    seed_sources = _seed_sources(stability_report)
    policy_rows = [row for row in list_of_dicts(policy_plan.get("policy_rows")) if row.get("included_in_replay")]
    issues = _issues(stability_report, policy_plan, seed_sources, policy_rows)
    generator = generate_func or _cached_generator(device=device)
    case_rows = []
    if not issues:
        for seed_source in seed_sources:
            for policy in policy_rows:
                for term in DEFAULT_TARGET_TERMS:
                    case_rows.append(
                        _run_case(
                            seed_source,
                            policy,
                            term,
                            max_new_tokens=max_new_tokens,
                            temperature=temperature,
                            top_k=top_k,
                            device=device,
                            generate_func=generator,
                        )
                    )
    policy_summaries = _policy_summaries(case_rows)
    seed_summaries = _seed_summaries(case_rows)
    summary = _summary(case_rows, policy_summaries, seed_summaries)
    status = "pass" if not issues and not any(row.get("status") != "pass" for row in case_rows) else "fail"
    if status == "fail" and not issues:
        issues = [{"id": "surface_policy_case_failed", "detail": "one or more replay cases failed"}]
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair surface policy replay",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(out_dir),
        "source_stability_path": str(stability_source_path or ""),
        "source_policy_plan_path": str(policy_plan_source_path or ""),
        "settings": {
            "target_terms": list(DEFAULT_TARGET_TERMS),
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "replay planned generation-surface policies over existing dual-boundary checkpoints without retraining",
        },
        "case_rows": case_rows,
        "policy_summaries": policy_summaries,
        "seed_summaries": seed_summaries,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _seed_sources(stability_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for report in list_of_dicts(stability_report.get("seed_reports")):
        settings = as_dict(report.get("settings"))
        training = as_dict(report.get("training"))
        seed = int(settings.get("seed") or 0)
        if seed:
            rows.append(
                {
                    "seed": seed,
                    "checkpoint_path": training.get("checkpoint_path"),
                    "tokenizer_path": training.get("tokenizer_path"),
                    "checkpoint_exists": training.get("checkpoint_exists"),
                    "tokenizer_exists": training.get("tokenizer_exists"),
                }
            )
    return rows


def _issues(
    stability_report: dict[str, Any],
    policy_plan: dict[str, Any],
    seed_sources: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if stability_report.get("status") != "pass":
        issues.append({"id": "bad_stability_source", "detail": "source stability report is not pass"})
    if policy_plan.get("status") != "pass":
        issues.append({"id": "bad_policy_plan_source", "detail": "source policy plan is not pass"})
    if not seed_sources:
        issues.append({"id": "missing_seed_sources", "detail": "stability report has no embedded seed reports"})
    if not policy_rows:
        issues.append({"id": "missing_replay_policies", "detail": "policy plan has no included replay policies"})
    return issues


def _run_case(
    seed_source: dict[str, Any],
    policy: dict[str, Any],
    term: str,
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: str,
    generate_func: GenerateFunc,
) -> dict[str, Any]:
    checkpoint = Path(str(seed_source.get("checkpoint_path") or ""))
    tokenizer = Path(str(seed_source.get("tokenizer_path") or checkpoint.parent / "tokenizer.json"))
    seed = int(seed_source.get("seed") or 0)
    policy_id = str(policy.get("policy_id") or "")
    prompt = _prompt(str(policy.get("prompt_template") or "{term}="), term)
    request = {
        "checkpoint_path": str(checkpoint),
        "tokenizer_path": str(tokenizer),
        "prompt": prompt,
        "expected_term": term,
        "policy_id": policy_id,
        "generation_profile": policy.get("generation_profile") or "default",
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": seed + _term_offset(term) + _policy_offset(policy_id),
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
    continuation_hit = _term_hit(continuation, term)
    return {
        "status": "pass" if not error else "fail",
        "error": error,
        "seed": seed,
        "policy_id": policy_id,
        "profile_id": policy.get("generation_profile") or "default",
        "leakage_level": policy.get("leakage_level"),
        "term": term,
        "prompt": prompt,
        "generation_seed": request["seed"],
        "checkpoint_path": str(checkpoint),
        "checkpoint_exists": checkpoint.is_file(),
        "tokenizer_path": str(tokenizer),
        "tokenizer_exists": tokenizer.is_file(),
        "generated": generated,
        "continuation": continuation,
        "generated_preview": generated.replace("\n", "\\n")[:120],
        "continuation_preview": continuation.replace("\n", "\\n")[:120],
        "continuation_hit": continuation_hit,
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
                "generation_profile": request["generation_profile"],
            }
        )
        return cache[key].generate(parsed).to_dict()

    return generate


def _policy_summaries(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for policy_id in sorted({str(row.get("policy_id")) for row in case_rows}):
        scoped = [row for row in case_rows if row.get("policy_id") == policy_id]
        seed_count = len({row.get("seed") for row in scoped})
        pair_full_seed_count = 0
        for seed in sorted({int(row.get("seed") or 0) for row in scoped}):
            seed_rows = [row for row in scoped if int(row.get("seed") or 0) == seed]
            hit_terms = {str(row.get("term")) for row in seed_rows if row.get("continuation_hit")}
            if all(term in hit_terms for term in DEFAULT_TARGET_TERMS):
                pair_full_seed_count += 1
        rows.append(
            {
                "policy_id": policy_id,
                "seed_count": seed_count,
                "hit_case_count": sum(1 for row in scoped if row.get("continuation_hit")),
                "case_count": len(scoped),
                "pair_full_seed_count": pair_full_seed_count,
                "stable_pair_full": bool(seed_count) and pair_full_seed_count == seed_count,
            }
        )
    return rows


def _seed_summaries(case_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for seed in sorted({int(row.get("seed") or 0) for row in case_rows}):
        scoped = [row for row in case_rows if int(row.get("seed") or 0) == seed]
        policy_full = []
        for policy_id in sorted({str(row.get("policy_id")) for row in scoped}):
            policy_rows = [row for row in scoped if row.get("policy_id") == policy_id]
            hit_terms = {str(row.get("term")) for row in policy_rows if row.get("continuation_hit")}
            if all(term in hit_terms for term in DEFAULT_TARGET_TERMS):
                policy_full.append(policy_id)
        rows.append({"seed": seed, "pair_full_policy_ids": policy_full, "pair_full_policy_count": len(policy_full)})
    return rows


def _summary(
    case_rows: list[dict[str, Any]],
    policy_summaries: list[dict[str, Any]],
    seed_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    stable_policies = [row.get("policy_id") for row in policy_summaries if row.get("stable_pair_full")]
    return {
        "case_count": len(case_rows),
        "seed_count": len(seed_summaries),
        "policy_count": len(policy_summaries),
        "stable_pair_full_policy_count": len(stable_policies),
        "stable_pair_full_policy_ids": stable_policies,
        "best_policy_id": _best_policy_id(policy_summaries),
        "seeds_with_any_pair_full_policy": sum(1 for row in seed_summaries if row.get("pair_full_policy_count")),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_surface_policy_replay"
    if summary.get("stable_pair_full_policy_count"):
        return "required_term_pair_surface_policy_replay_stable_pair_full_policy_found"
    if summary.get("seeds_with_any_pair_full_policy"):
        return "required_term_pair_surface_policy_replay_partial_policy_gain"
    return "required_term_pair_surface_policy_replay_no_gain"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "One or more replay cases failed."
        next_action = "repair replay execution before judging policy quality"
        claim = "not_claimed"
    elif summary.get("stable_pair_full_policy_count"):
        reason = "At least one replay policy produces fixed/loss pair-full across all tested seeds."
        next_action = "compare stable policy leakage and minimality before promotion"
        claim = "decode_surface_policy_candidate"
    elif summary.get("seeds_with_any_pair_full_policy"):
        reason = "At least one seed benefits from a replay policy, but no policy is stable across all seeds."
        next_action = "inspect partial policy gains and missed cases"
        claim = "decode_surface_policy_partial_signal"
    else:
        reason = "No planned policy repaired pair-full generation."
        next_action = "return to generation objective design rather than decoding policy"
        claim = "not_claimed"
    return {"model_quality_claim": claim, "reason": reason, "next_action": next_action}


def _prompt(template: str, term: str) -> str:
    other = "loss" if term == "fixed" else "fixed"
    return template.format(term=term, other_term=other)


def _best_policy_id(policy_summaries: list[dict[str, Any]]) -> str:
    if not policy_summaries:
        return ""
    ordered = sorted(policy_summaries, key=lambda row: (int(row.get("pair_full_seed_count") or 0), int(row.get("hit_case_count") or 0)), reverse=True)
    return str(ordered[0].get("policy_id") or "")


def _term_hit(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def _term_offset(term: str) -> int:
    return 0 if term == "fixed" else 1


def _policy_offset(policy_id: str) -> int:
    return sum(ord(char) for char in policy_id) % 97


__all__ = [
    "PAIR_SURFACE_POLICY_REPLAY_CSV_FILENAME",
    "PAIR_SURFACE_POLICY_REPLAY_HTML_FILENAME",
    "PAIR_SURFACE_POLICY_REPLAY_JSON_FILENAME",
    "PAIR_SURFACE_POLICY_REPLAY_MARKDOWN_FILENAME",
    "PAIR_SURFACE_POLICY_REPLAY_TEXT_FILENAME",
    "build_model_capability_required_term_pair_surface_policy_replay",
    "locate_surface_policy_replay_plan_source",
    "locate_surface_policy_replay_stability_source",
    "read_json_report",
    "resolve_exit_code",
]
