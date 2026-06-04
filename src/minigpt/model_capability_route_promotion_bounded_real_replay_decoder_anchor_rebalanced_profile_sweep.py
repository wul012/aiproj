from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_benchmark_dry_run import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_benchmark_suite_review import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay import (
    build_model_capability_route_promotion_bounded_real_replay,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_failure_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep.html"

ProfileRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]

DEFAULT_REBALANCED_DECODER_PROFILES: tuple[dict[str, Any], ...] = (
    {"profile_id": "default_bounded", "label": "default bounded replay", "max_new_tokens": 24, "temperature": 0.2, "top_k": 10},
    {"profile_id": "greedy_short", "label": "near-greedy short replay", "max_new_tokens": 24, "temperature": 0.05, "top_k": 1},
    {"profile_id": "greedy_long", "label": "near-greedy long replay", "max_new_tokens": 64, "temperature": 0.05, "top_k": 1},
    {"profile_id": "longer_low_temp", "label": "longer low-temperature replay", "max_new_tokens": 64, "temperature": 0.2, "top_k": 10},
    {"profile_id": "wider_rescue", "label": "wider rescue replay", "max_new_tokens": 80, "temperature": 0.6, "top_k": 30},
)


def locate_benchmark_suite(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME
    return source


def locate_suite_review(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_REVIEW_JSON_FILENAME
    return source


def locate_dry_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_DRY_RUN_JSON_FILENAME
    return source


def locate_failure_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("rebalanced decoder profile sweep input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep(
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    failure_diagnostic: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    profiles: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    suite_review_path: str | Path | None = None,
    benchmark_suite_path: str | Path | None = None,
    dry_run_path: str | Path | None = None,
    failure_diagnostic_path: str | Path | None = None,
    generator_runner: ProfileRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced profile sweep",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    normalized_profiles = [_normalize_profile(row) for row in (profiles or DEFAULT_REBALANCED_DECODER_PROFILES)]
    runner = generator_runner or _cached_profile_runner(checkpoint, tokenizer, device)
    replay_reports = [
        _run_profile(profile, suite_review, benchmark_suite_report, dry_run_report, checkpoint, tokenizer, device, runner, suite_review_path, benchmark_suite_path, dry_run_path)
        for profile in normalized_profiles
    ]
    profile_rows = [_profile_row(report) for report in replay_reports]
    case_profile_rows = [row for report in replay_reports for row in _case_profile_rows(report)]
    checks = _checks(failure_diagnostic, checkpoint, tokenizer, normalized_profiles, replay_reports, benchmark_suite_report)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    sweep = _sweep_summary(status, profile_rows, case_profile_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, sweep),
        "failed_count": len(issues),
        "issues": issues,
        "source_suite_review": str(suite_review_path or ""),
        "source_benchmark_suite": str(benchmark_suite_path or ""),
        "source_dry_run": str(dry_run_path or ""),
        "source_failure_diagnostic": str(failure_diagnostic_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "profiles": normalized_profiles,
        "profile_rows": profile_rows,
        "case_profile_rows": case_profile_rows,
        "check_rows": checks,
        "sweep": sweep,
        "summary": _summary(status, checks, sweep),
        "interpretation": _interpretation(status, sweep),
    }


def resolve_exit_code(
    report: dict[str, Any],
    *,
    require_sweep_ready: bool,
    require_recovery: bool = False,
    require_promotion: bool = False,
) -> int:
    summary = as_dict(report.get("summary"))
    if require_sweep_ready and report.get("status") != "pass":
        return 1
    if require_recovery and summary.get("any_profile_recovered") is not True:
        return 1
    if require_promotion and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _run_profile(
    profile: dict[str, Any],
    suite_review: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: ProfileRunner,
    suite_review_path: str | Path | None,
    benchmark_suite_path: str | Path | None,
    dry_run_path: str | Path | None,
) -> dict[str, Any]:
    report = build_model_capability_route_promotion_bounded_real_replay(
        suite_review,
        _suite_with_profile(benchmark_suite_report, profile),
        dry_run_report,
        checkpoint_path=checkpoint,
        tokenizer_path=tokenizer,
        device=device,
        suite_review_path=suite_review_path,
        benchmark_suite_path=benchmark_suite_path,
        dry_run_path=dry_run_path,
        generator_runner=runner,
        title=f"MiniGPT rebalanced decoder profile sweep replay: {profile['profile_id']}",
    )
    report["profile"] = profile
    return report


def _suite_with_profile(benchmark_suite_report: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    profiled = deepcopy(benchmark_suite_report)
    suite = as_dict(profiled.get("benchmark_suite"))
    cases = list_of_dicts(suite.get("cases"))
    for case in cases:
        prompt_case = as_dict(case.get("prompt_case"))
        prompt_case["max_new_tokens"] = profile["max_new_tokens"]
        prompt_case["temperature"] = profile["temperature"]
        prompt_case["top_k"] = profile["top_k"]
        prompt_case["generation_profile"] = profile["profile_id"]
        case["prompt_case"] = prompt_case
    suite["cases"] = cases
    profiled["benchmark_suite"] = suite
    return profiled


def _cached_profile_runner(checkpoint: Path, tokenizer: Path, device: str) -> ProfileRunner:
    generator = MiniGPTGenerator(checkpoint, tokenizer, device=device)

    def runner(row: dict[str, Any], _checkpoint: str | Path, _tokenizer: str | Path, _device: str) -> dict[str, Any]:
        prompt_case = as_dict(row.get("prompt_case"))
        request = GenerationRequest(
            prompt=str(prompt_case.get("prompt") or ""),
            max_new_tokens=int(prompt_case.get("max_new_tokens") or 24),
            temperature=float(prompt_case.get("temperature") or 0.2),
            top_k=None if prompt_case.get("top_k") in {None, "", 0, "0"} else int(prompt_case.get("top_k")),
            seed=None if prompt_case.get("seed") in {None, ""} else int(prompt_case.get("seed")),
            generation_profile=str(prompt_case.get("generation_profile") or "default"),
        )
        return generator.generate(request).to_dict()

    return runner


def _normalize_profile(row: dict[str, Any]) -> dict[str, Any]:
    profile_id = str(row.get("profile_id") or "").strip()
    if not profile_id:
        raise ValueError("decoder profile must include profile_id")
    top_k = row.get("top_k")
    normalized_top_k = None if top_k in {None, "", 0, "0"} else int(top_k)
    max_new_tokens = int(row.get("max_new_tokens") or 0)
    temperature = float(row.get("temperature") or 0.0)
    if max_new_tokens < 1:
        raise ValueError(f"decoder profile {profile_id} must use max_new_tokens >= 1")
    if temperature < 0.05:
        raise ValueError(f"decoder profile {profile_id} must use temperature >= 0.05")
    if normalized_top_k is not None and normalized_top_k < 1:
        raise ValueError(f"decoder profile {profile_id} must use top_k >= 1 when provided")
    return {
        "profile_id": profile_id,
        "label": str(row.get("label") or profile_id),
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": normalized_top_k,
    }


def _profile_row(report: dict[str, Any]) -> dict[str, Any]:
    profile = as_dict(report.get("profile"))
    summary = as_dict(report.get("summary"))
    replay_rows = list_of_dicts(report.get("replay_rows"))
    zero_hit_count = sum(1 for row in replay_rows if not row.get("hit_terms"))
    fragment_like_count = sum(1 for row in replay_rows if _fragment_like(str(row.get("continuation") or ""), [str(term) for term in row.get("expected_terms", [])]))
    any_hit_count = sum(1 for row in replay_rows if row.get("hit_terms"))
    return {
        "profile_id": profile.get("profile_id"),
        "label": profile.get("label"),
        "status": report.get("status"),
        "decision": report.get("decision"),
        "max_new_tokens": profile.get("max_new_tokens"),
        "temperature": profile.get("temperature"),
        "top_k": profile.get("top_k"),
        "case_count": int(summary.get("case_count") or 0),
        "executed_case_count": int(summary.get("executed_case_count") or 0),
        "passed_case_count": int(summary.get("passed_case_count") or 0),
        "failed_case_count": int(summary.get("failed_case_count") or 0),
        "pass_rate": float(summary.get("pass_rate") or 0.0),
        "zero_hit_case_count": zero_hit_count,
        "fragment_like_case_count": fragment_like_count,
        "any_hit_case_count": any_hit_count,
        "model_route_quality_ready": summary.get("model_route_quality_ready") is True,
    }


def _case_profile_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    profile = as_dict(report.get("profile"))
    rows = []
    for row in list_of_dicts(report.get("replay_rows")):
        expected_terms = [str(term) for term in row.get("expected_terms", [])]
        hit_terms = [str(term) for term in row.get("hit_terms", [])]
        continuation = str(row.get("continuation") or "")
        rows.append(
            {
                "profile_id": profile.get("profile_id"),
                "case_id": row.get("case_id"),
                "case_pass": row.get("case_pass") is True,
                "hit_terms": hit_terms,
                "missed_terms": [str(term) for term in row.get("missed_terms", [])],
                "zero_hit": not hit_terms,
                "fragment_like_generation": _fragment_like(continuation, expected_terms),
                "continuation_preview": continuation[:160],
                "max_new_tokens": row.get("max_new_tokens"),
                "temperature": row.get("temperature"),
                "top_k": row.get("top_k"),
                "seed": row.get("seed"),
            }
        )
    return rows


def _checks(
    failure_diagnostic: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    profiles: list[dict[str, Any]],
    replay_reports: list[dict[str, Any]],
    benchmark_suite_report: dict[str, Any],
) -> list[dict[str, Any]]:
    diagnostic_summary = as_dict(failure_diagnostic.get("summary"))
    cases = list_of_dicts(as_dict(benchmark_suite_report.get("benchmark_suite")).get("cases"))
    return [
        _check("failure_diagnostic_passed", failure_diagnostic.get("status") == "pass", failure_diagnostic.get("status"), "failure diagnostic must pass before profile sweep"),
        _check("diagnostic_requests_profile_sweep", diagnostic_summary.get("next_step") == "run_rebalanced_decoder_profile_sweep_before_more_training", diagnostic_summary.get("next_step"), "diagnostic should route to this profile sweep"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "rebalanced checkpoint must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "rebalanced tokenizer must exist"),
        _check("profiles_present", bool(profiles), len(profiles), "profile sweep must include at least one decoder profile"),
        _check("cases_present", bool(cases), len(cases), "benchmark suite must provide bounded cases"),
        _check("all_profile_replays_passed", all(report.get("status") == "pass" for report in replay_reports), [report.get("status") for report in replay_reports], "all profile replays must execute successfully"),
        _check("all_profiles_execute_all_cases", all(int(as_dict(report.get("summary")).get("executed_case_count") or 0) == len(cases) for report in replay_reports), [as_dict(report.get("summary")).get("executed_case_count") for report in replay_reports], "every profile must execute every case"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _sweep_summary(status: str, profile_rows: list[dict[str, Any]], case_profile_rows: list[dict[str, Any]]) -> dict[str, Any]:
    default = next((row for row in profile_rows if row.get("profile_id") == "default_bounded"), profile_rows[0] if profile_rows else {})
    best = max(profile_rows, key=lambda row: (int(row.get("passed_case_count") or 0), int(row.get("any_hit_case_count") or 0), -int(row.get("fragment_like_case_count") or 0)), default={})
    default_pass_rate = float(default.get("pass_rate") or 0.0)
    best_pass_rate = float(best.get("pass_rate") or 0.0)
    any_profile_recovered = int(best.get("passed_case_count") or 0) > int(default.get("passed_case_count") or 0)
    promotion_ready = status == "pass" and best.get("model_route_quality_ready") is True
    return {
        "ready": status == "pass",
        "profile_count": len(profile_rows),
        "case_count": int(default.get("case_count") or 0),
        "case_profile_row_count": len(case_profile_rows),
        "default_profile_id": default.get("profile_id"),
        "default_passed_case_count": int(default.get("passed_case_count") or 0),
        "default_pass_rate": default_pass_rate,
        "best_profile_id": best.get("profile_id"),
        "best_passed_case_count": int(best.get("passed_case_count") or 0),
        "best_pass_rate": best_pass_rate,
        "best_any_hit_case_count": int(best.get("any_hit_case_count") or 0),
        "best_zero_hit_case_count": int(best.get("zero_hit_case_count") or 0),
        "best_fragment_like_case_count": int(best.get("fragment_like_case_count") or 0),
        "best_vs_default_pass_rate_delta": round(best_pass_rate - default_pass_rate, 4),
        "any_profile_recovered": any_profile_recovered,
        "any_profile_has_required_term_hit": any(int(row.get("any_hit_case_count") or 0) > 0 for row in profile_rows),
        "promotion_ready": promotion_ready,
        "next_step": _next_step(status, any_profile_recovered, promotion_ready),
    }


def _summary(status: str, checks: list[dict[str, Any]], sweep: dict[str, Any]) -> dict[str, Any]:
    return {
        "rebalanced_profile_sweep_ready": status == "pass" and sweep.get("ready") is True,
        "profile_count": sweep.get("profile_count"),
        "case_count": sweep.get("case_count"),
        "case_profile_row_count": sweep.get("case_profile_row_count"),
        "default_profile_id": sweep.get("default_profile_id"),
        "default_passed_case_count": sweep.get("default_passed_case_count"),
        "default_pass_rate": sweep.get("default_pass_rate"),
        "best_profile_id": sweep.get("best_profile_id"),
        "best_passed_case_count": sweep.get("best_passed_case_count"),
        "best_pass_rate": sweep.get("best_pass_rate"),
        "best_any_hit_case_count": sweep.get("best_any_hit_case_count"),
        "best_zero_hit_case_count": sweep.get("best_zero_hit_case_count"),
        "best_fragment_like_case_count": sweep.get("best_fragment_like_case_count"),
        "best_vs_default_pass_rate_delta": sweep.get("best_vs_default_pass_rate_delta"),
        "any_profile_recovered": sweep.get("any_profile_recovered"),
        "any_profile_has_required_term_hit": sweep.get("any_profile_has_required_term_hit"),
        "promotion_ready": sweep.get("promotion_ready"),
        "next_step": sweep.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, sweep: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep"
    if sweep.get("promotion_ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_promotable_profile_found"
    if sweep.get("any_profile_recovered") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_partial_recovery_found"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_no_recovery"


def _interpretation(status: str, sweep: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Profile sweep inputs or executions are incomplete.", "next_action": "repair sweep inputs"}
    if sweep.get("promotion_ready") is True:
        return {"model_quality_claim": "bounded_replay_passed_by_decoder_profile", "reason": "At least one profile passes every bounded replay case.", "next_action": sweep.get("next_step")}
    if sweep.get("any_profile_recovered") is True:
        return {"model_quality_claim": "decoder_profile_partial_recovery_only", "reason": "A profile improved over default replay but did not pass the full suite.", "next_action": sweep.get("next_step")}
    return {"model_quality_claim": "not_improved", "reason": "Changing decoding profile did not recover required-term replay.", "next_action": sweep.get("next_step")}


def _next_step(status: str, any_profile_recovered: bool, promotion_ready: bool) -> str:
    if status != "pass":
        return "repair_rebalanced_decoder_profile_sweep_inputs"
    if promotion_ready:
        return "review_best_decoder_profile_before_route_promotion"
    if any_profile_recovered:
        return "compare_partial_recovery_profile_against_baseline"
    return "route_to_objective_or_architecture_intervention"


def _fragment_like(continuation: str, expected_terms: list[str]) -> bool:
    lowered = continuation.lower()
    if any(term.lower() in lowered for term in expected_terms):
        return False
    letters = sum(1 for char in lowered if "a" <= char <= "z")
    repeated = max((lowered.count(char) for char in set(lowered) if "a" <= char <= "z"), default=0)
    spaces = lowered.count(" ")
    return letters > 0 and (spaces >= 2 or repeated >= 4)


__all__ = [
    "DEFAULT_REBALANCED_DECODER_PROFILES",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_PROFILE_SWEEP_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep",
    "locate_benchmark_suite",
    "locate_dry_run",
    "locate_failure_diagnostic",
    "locate_suite_review",
    "read_json_report",
    "resolve_exit_code",
]
