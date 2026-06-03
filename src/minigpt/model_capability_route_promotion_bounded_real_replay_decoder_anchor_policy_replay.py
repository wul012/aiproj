from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay.html"

GeneratorRunner = Callable[[dict[str, Any], dict[str, Any] | None, str | Path, str | Path, str], dict[str, Any]]


def locate_prompt_aligned_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_decoder_anchor_policy(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor policy replay input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay(
    prompt_aligned_replay: dict[str, Any],
    decoder_anchor_policy: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    replay_path: str | Path | None = None,
    policy_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor policy replay",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    replay_rows = list_of_dicts(prompt_aligned_replay.get("replay_rows"))
    policy_rows = list_of_dicts(decoder_anchor_policy.get("policy_rows"))
    policy_by_case = {str(row.get("case_id")): row for row in policy_rows}
    replayed_rows, replay_errors = _run_policy_replay(replay_rows, policy_by_case, checkpoint, tokenizer, device, generator_runner or _generate_policy_case)
    checks = _checks(prompt_aligned_replay, decoder_anchor_policy, checkpoint, tokenizer, replay_rows, policy_rows, replayed_rows, replay_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    replay = _replay(status, replayed_rows, policy_rows)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, replay),
        "failed_count": len(issues),
        "issues": issues,
        "source_prompt_aligned_replay": str(replay_path or ""),
        "source_decoder_anchor_policy": str(policy_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "policy_rows": policy_rows,
        "replay_rows": replayed_rows,
        "replay_errors": replay_errors,
        "check_rows": checks,
        "policy_replay": replay,
        "summary": _summary(status, checks, replay),
        "interpretation": _interpretation(status, replay),
    }


def resolve_exit_code(report: dict[str, Any], *, require_replay_ready: bool, require_policy_case_pass: bool = False) -> int:
    if require_replay_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_policy_case_pass and int(summary.get("policy_applied_pass_count") or 0) < 1:
        return 1
    return 0


def _run_policy_replay(
    replay_rows: list[dict[str, Any]],
    policy_by_case: dict[str, dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row in replay_rows:
        case_id = str(row.get("case_id") or "")
        policy = policy_by_case.get(case_id)
        try:
            response = runner(row, policy, checkpoint, tokenizer, device)
            rows.append(_policy_replay_row(row, policy, response))
        except Exception as exc:  # pragma: no cover
            errors.append({"case_id": case_id, "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_policy_case(row: dict[str, Any], policy: dict[str, Any] | None, checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    anchor = str(as_dict(policy).get("anchor") or "")
    request = GenerationRequest(
        prompt=f"{row.get('prompt', '')}{anchor}",
        max_new_tokens=int(row.get("max_new_tokens") or 24),
        temperature=float(row.get("temperature") or 0.2),
        top_k=None if row.get("top_k") in {None, "", 0, "0"} else int(row.get("top_k")),
        seed=None if row.get("seed") in {None, ""} else int(row.get("seed")),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _policy_replay_row(row: dict[str, Any], policy: dict[str, Any] | None, response: dict[str, Any]) -> dict[str, Any]:
    policy = as_dict(policy)
    anchor = str(policy.get("anchor") or "")
    continuation = str(response.get("continuation") or "")
    combined = f"{anchor}{continuation}"
    expected_terms = [str(term) for term in row.get("expected_terms", [])]
    combined_hits = _hits(expected_terms, combined)
    new_text_hits = _hits(expected_terms, continuation)
    return {
        "case_id": str(row.get("case_id") or ""),
        "policy_applied": bool(policy),
        "profile_id": policy.get("profile_id", ""),
        "anchor": anchor,
        "continuation": continuation,
        "combined": combined,
        "expected_terms": expected_terms,
        "combined_hit_terms": combined_hits,
        "new_text_hit_terms": new_text_hits,
        "missed_terms": [term for term in expected_terms if term not in combined_hits],
        "case_pass": bool(expected_terms) and len(combined_hits) == len(expected_terms),
        "new_text_pass": bool(expected_terms) and len(new_text_hits) == len(expected_terms),
        "seed": response.get("seed"),
        "max_new_tokens": response.get("max_new_tokens"),
        "temperature": response.get("temperature"),
        "top_k": response.get("top_k"),
    }


def _hits(expected_terms: list[str], text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in expected_terms if term.lower() in lowered]


def _checks(
    replay: dict[str, Any],
    policy: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    source_rows: list[dict[str, Any]],
    policy_rows: list[dict[str, Any]],
    replayed_rows: list[dict[str, Any]],
    replay_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("prompt_aligned_replay_passed", replay.get("status") == "pass", replay.get("status"), "source replay execution must pass"),
        _check("decoder_anchor_policy_passed", policy.get("status") == "pass", policy.get("status"), "decoder anchor policy must pass"),
        _check("decoder_anchor_policy_ready", as_dict(policy.get("summary")).get("decoder_anchor_policy_ready") is True, as_dict(policy.get("summary")).get("decoder_anchor_policy_ready"), "policy summary must be ready"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("source_rows_present", bool(source_rows), len(source_rows), "source replay rows must be present"),
        _check("policy_rows_present", bool(policy_rows), len(policy_rows), "policy must contain at least one row"),
        _check("all_cases_replayed", len(replayed_rows) == len(source_rows), len(replayed_rows), "policy replay should replay every source case"),
        _check("no_replay_errors", not replay_errors, len(replay_errors), "policy replay should not raise generation errors"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _replay(status: str, rows: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row for row in rows if row.get("case_pass") is True]
    policy_applied = [row for row in rows if row.get("policy_applied") is True]
    policy_applied_passed = [row for row in policy_applied if row.get("case_pass") is True]
    return {
        "ready": status == "pass",
        "case_count": len(rows),
        "passed_case_count": len(passed),
        "failed_case_count": len(rows) - len(passed),
        "policy_case_count": len(policy_rows),
        "policy_applied_case_count": len(policy_applied),
        "policy_applied_pass_count": len(policy_applied_passed),
        "pass_rate": round(len(passed) / len(rows), 4) if rows else 0.0,
        "policy_replay_success": bool(policy_applied_passed),
        "promotion_ready": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_review",
        "next_step": "review_decoder_anchor_policy_replay" if status == "pass" else "repair_decoder_anchor_policy_replay_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], replay: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_policy_replay_ready": status == "pass" and replay.get("ready") is True,
        "case_count": replay.get("case_count"),
        "passed_case_count": replay.get("passed_case_count"),
        "failed_case_count": replay.get("failed_case_count"),
        "policy_case_count": replay.get("policy_case_count"),
        "policy_applied_case_count": replay.get("policy_applied_case_count"),
        "policy_applied_pass_count": replay.get("policy_applied_pass_count"),
        "pass_rate": replay.get("pass_rate"),
        "policy_replay_success": replay.get("policy_replay_success"),
        "promotion_ready": replay.get("promotion_ready"),
        "proposed_next_artifact": replay.get("proposed_next_artifact"),
        "next_step": replay.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, replay: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay"
    if replay.get("policy_replay_success") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_reproduced_partial_signal"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay_no_signal"


def _interpretation(status: str, replay: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Policy replay inputs or execution failed.", "next_action": "repair policy replay inputs"}
    if replay.get("policy_replay_success") is True:
        return {"model_quality_claim": "anchor_assisted_only", "reason": "Policy replay reproduced a partial anchored case, but uncovered cases remain and promotion stays blocked.", "next_action": replay.get("next_step")}
    return {"model_quality_claim": "not_improved", "reason": "Policy replay did not reproduce the anchor-assisted signal.", "next_action": replay.get("next_step")}


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_POLICY_REPLAY_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy_replay",
    "locate_decoder_anchor_policy",
    "locate_prompt_aligned_replay",
    "read_json_report",
    "resolve_exit_code",
]
