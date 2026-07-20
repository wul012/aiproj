from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_loss_alias_focus import REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
from minigpt.model_capability_required_term_pair_loss_alias_metrics import required_term_hit_metrics
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_JSON_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_probe.json"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_TEXT_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_probe.txt"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_probe.md"
)
REQUIRED_TERM_PAIR_LOSS_ALIAS_NEWLINE_SUPPRESSION_HTML_FILENAME = (
    "model_capability_required_term_pair_loss_alias_newline_suppression_probe.html"
)


GenerateFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_loss_alias_newline_suppression_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_model_capability_required_term_pair_loss_alias_newline_suppression_probe(
    focus_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    issues = _input_issues(focus_report)
    profiles = _profiles()
    rows = [] if issues else _probe_rows(focus_report, profiles, generate_func)
    profile_rows = _profile_rows(rows, profiles)
    summary = _summary(rows, profile_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias newline suppression probe",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_loss_alias_focus": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "profiles": profiles,
        "profile_rows": profile_rows,
        "case_rows": rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def _profiles() -> list[dict[str, Any]]:
    return [
        {"profile_id": "baseline_rerun", "exclude_token_texts": []},
        {"profile_id": "suppress_newline_tokens", "exclude_token_texts": ["\n", "\r"]},
    ]


def _input_issues(focus_report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not focus_report:
        issues.append("source loss-alias focus report is missing or invalid")
    elif focus_report.get("status") != "pass":
        issues.append("source loss-alias focus report is not pass")
    seed_reports = list_of_dicts(focus_report.get("seed_reports")) if focus_report else []
    if focus_report and not seed_reports:
        issues.append("source loss-alias focus report has no seed reports")
    if focus_report and not any(list_of_dicts(report.get("generation_rows")) for report in seed_reports):
        issues.append("source loss-alias focus report has no generation rows")
    return issues


def _probe_rows(
    focus_report: dict[str, Any],
    profiles: list[dict[str, Any]],
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    settings = as_dict(focus_report.get("settings"))
    rows: list[dict[str, Any]] = []
    for seed_report in list_of_dicts(focus_report.get("seed_reports")):
        training = as_dict(seed_report.get("training"))
        for source_row in list_of_dicts(seed_report.get("generation_rows")):
            for profile in profiles:
                request = _request(settings, training, source_row, profile)
                response = _generate(request, generate_func)
                continuation = _continuation(request["prompt"], response)
                expected = str(source_row.get("expected_term") or "loss")
                strict_hit = expected.casefold() in continuation.casefold()
                hit_metrics = required_term_hit_metrics(continuation, expected, strict_hit=strict_hit)
                rows.append(
                    {
                        "profile_id": profile["profile_id"],
                        "seed": as_dict(seed_report.get("settings")).get("generation_seed"),
                        "case_id": source_row.get("case_id"),
                        "case_type": source_row.get("case_type"),
                        "alias_group": source_row.get("alias_group"),
                        "prompt": request["prompt"],
                        "expected_term": expected,
                        "is_focus_case": bool(source_row.get("is_focus_case")),
                        "generation_seed": request["seed"],
                        "source_strict_hit": bool(source_row.get("strict_hit") or source_row.get("continuation_hit")),
                        "source_newline_cleanup_hit": bool(source_row.get("newline_cleanup_hit")),
                        "source_normalized_hit": bool(source_row.get("normalized_hit")),
                        "strict_hit": hit_metrics["strict_hit"],
                        "newline_cleanup_hit": hit_metrics["newline_cleanup_hit"],
                        "normalized_hit": hit_metrics["normalized_hit"],
                        "strict_gain": hit_metrics["strict_hit"] and not bool(source_row.get("strict_hit") or source_row.get("continuation_hit")),
                        "excluded_token_count": response.get("excluded_token_count"),
                        "excluded_token_texts": response.get("excluded_token_texts", request["exclude_token_texts"]),
                        "continuation_preview": _preview(continuation),
                    }
                )
    return rows


def _request(
    settings: dict[str, Any],
    training: dict[str, Any],
    source_row: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    return {
        "prompt": str(source_row.get("prompt") or ""),
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
        "max_new_tokens": int(settings.get("max_new_tokens") or 12),
        "temperature": float(settings.get("temperature") or 0.2),
        "top_k": settings.get("top_k"),
        "seed": int(source_row.get("generation_seed") or 0),
        "device": str(settings.get("device") or "cpu"),
        "exclude_token_texts": list(profile.get("exclude_token_texts") or []),
    }


def _generate(request: dict[str, Any], generate_func: GenerateFunc | None) -> dict[str, Any]:
    if generate_func is not None:
        return generate_func(request)
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    response = MiniGPTGenerator(request["checkpoint_path"], request["tokenizer_path"], device=str(request.get("device") or "cpu")).generate(
        GenerationRequest(
            prompt=str(request["prompt"]),
            max_new_tokens=int(request["max_new_tokens"]),
            temperature=float(request["temperature"]),
            top_k=request.get("top_k"),
            seed=int(request["seed"]),
            blocked_token_texts=tuple(str(text) for text in list(request.get("exclude_token_texts") or [])),
        )
    )
    payload = response.to_dict()
    payload["excluded_token_count"] = payload.get("blocked_token_count", 0)
    payload["excluded_token_texts"] = payload.get("blocked_token_texts", [])
    return payload


def _continuation(prompt: str, response: dict[str, Any]) -> str:
    continuation = str(response.get("continuation") or "")
    generated = str(response.get("generated") or "")
    if not continuation and generated.startswith(prompt):
        continuation = generated[len(prompt) :]
    return continuation


def _profile_rows(rows: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profile_rows: list[dict[str, Any]] = []
    for profile in profiles:
        profile_id = str(profile.get("profile_id"))
        profile_cases = [row for row in rows if row.get("profile_id") == profile_id]
        focus_cases = [row for row in profile_cases if row.get("is_focus_case")]
        strict_hits = sum(1 for row in profile_cases if row.get("strict_hit"))
        focus_strict_hits = sum(1 for row in focus_cases if row.get("strict_hit"))
        strict_gains = sum(1 for row in profile_cases if row.get("strict_gain"))
        profile_rows.append(
            {
                "profile_id": profile_id,
                "case_count": len(profile_cases),
                "focus_case_count": len(focus_cases),
                "strict_hit_count": strict_hits,
                "focus_strict_hit_count": focus_strict_hits,
                "strict_full_coverage": bool(profile_cases) and strict_hits == len(profile_cases),
                "focus_strict_full_coverage": bool(focus_cases) and focus_strict_hits == len(focus_cases),
                "strict_gain_count": strict_gains,
                "exclude_token_texts": profile.get("exclude_token_texts"),
            }
        )
    return profile_rows


def _summary(rows: list[dict[str, Any]], profile_rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = _profile(profile_rows, "baseline_rerun")
    suppressed = _profile(profile_rows, "suppress_newline_tokens")
    return {
        "newline_suppression_decision": _suppression_decision(baseline, suppressed),
        "profile_count": len(profile_rows),
        "case_count": max((int(row.get("case_count") or 0) for row in profile_rows), default=0),
        "baseline_strict_hit_count": baseline.get("strict_hit_count"),
        "baseline_strict_full_coverage": baseline.get("strict_full_coverage"),
        "suppressed_strict_hit_count": suppressed.get("strict_hit_count"),
        "suppressed_strict_full_coverage": suppressed.get("strict_full_coverage"),
        "suppressed_focus_strict_hit_count": suppressed.get("focus_strict_hit_count"),
        "suppressed_focus_strict_full_coverage": suppressed.get("focus_strict_full_coverage"),
        "suppressed_strict_gain_count": suppressed.get("strict_gain_count"),
        "excluded_token_texts": suppressed.get("exclude_token_texts"),
        "strict_recovery_case_count": sum(1 for row in rows if row.get("profile_id") == "suppress_newline_tokens" and row.get("strict_gain")),
    }


def _profile(profile_rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in profile_rows:
        if row.get("profile_id") == profile_id:
            return row
    return {}


def _suppression_decision(baseline: dict[str, Any], suppressed: dict[str, Any]) -> str:
    if suppressed.get("strict_full_coverage") and not baseline.get("strict_full_coverage"):
        return "loss_alias_newline_suppression_strict_full_recovery"
    if int(suppressed.get("strict_gain_count") or 0) > 0:
        return "loss_alias_newline_suppression_strict_partial_recovery"
    if baseline.get("strict_full_coverage"):
        return "loss_alias_newline_suppression_baseline_already_full"
    return "loss_alias_newline_suppression_no_strict_recovery"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_newline_suppression_probe"
    if summary.get("suppressed_strict_full_coverage"):
        return "required_term_pair_loss_alias_newline_suppression_strict_recovery"
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_newline_suppression_partial_recovery"
    return "required_term_pair_loss_alias_newline_suppression_no_recovery"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("suppressed_strict_full_coverage"):
        return "tiny_loss_alias_decoding_newline_suppression_recovers_strict_surface"
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "tiny_loss_alias_decoding_newline_suppression_partial_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source focus report could not be probed."
    if summary.get("suppressed_strict_full_coverage"):
        return "Masking newline tokens during decoding recovers strict loss hits for every probed loss-alias row."
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "Masking newline tokens recovers at least one strict loss hit, but not full coverage."
    return "Masking newline tokens did not recover strict loss hits."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair source focus evidence before another decoding probe"
    if summary.get("suppressed_strict_full_coverage"):
        return "compare newline-suppressed decoding against a fresh training run before changing the corpus"
    if int(summary.get("suppressed_strict_gain_count") or 0) > 0:
        return "inspect remaining prompts before treating suppression as a general decode fix"
    return "return to data or training changes because newline suppression did not help"


def _preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\r", "\\r")
    return text if len(text) <= limit else text[: limit - 3] + "..."
