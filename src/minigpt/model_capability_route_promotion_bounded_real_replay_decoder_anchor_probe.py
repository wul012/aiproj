from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_prompt_aligned_failure_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe.html"

GeneratorRunner = Callable[[dict[str, Any], dict[str, Any], str | Path, str | Path, str], dict[str, Any]]

ANCHOR_PROFILES = [
    {"profile_id": "prefix_f", "anchor": "f", "max_new_tokens": 20, "seed_offset": 1100, "description": "Give only the first character of fixed."},
    {"profile_id": "prefix_fixed_space", "anchor": "fixed ", "max_new_tokens": 18, "seed_offset": 1200, "description": "Give the first full term and ask the model to complete loss."},
    {"profile_id": "prefix_fixed_l", "anchor": "fixed l", "max_new_tokens": 16, "seed_offset": 1300, "description": "Give fixed and the first character of loss."},
]


def locate_prompt_aligned_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def locate_failure_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_PROMPT_ALIGNED_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor probe input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe(
    prompt_aligned_replay: dict[str, Any],
    failure_diagnostic: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    replay_path: str | Path | None = None,
    failure_diagnostic_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor probe",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    replay_rows = list_of_dicts(prompt_aligned_replay.get("replay_rows"))
    diagnostic_summary = as_dict(failure_diagnostic.get("summary"))
    probe_rows, probe_errors = _run_probe_rows(replay_rows, checkpoint, tokenizer, device, generator_runner or _generate_probe)
    checks = _checks(prompt_aligned_replay, failure_diagnostic, checkpoint, tokenizer, replay_rows, probe_rows, probe_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    probe = _probe(status, probe_rows, diagnostic_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, probe),
        "failed_count": len(issues),
        "issues": issues,
        "source_prompt_aligned_replay": str(replay_path or ""),
        "source_failure_diagnostic": str(failure_diagnostic_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "anchor_profiles": ANCHOR_PROFILES,
        "probe_rows": probe_rows,
        "probe_errors": probe_errors,
        "check_rows": checks,
        "probe": probe,
        "summary": _summary(status, checks, probe),
        "interpretation": _interpretation(status, probe),
    }


def resolve_exit_code(report: dict[str, Any], *, require_probe_ready: bool, require_anchor_success: bool = False) -> int:
    if require_probe_ready and report.get("status") != "pass":
        return 1
    if require_anchor_success and as_dict(report.get("summary")).get("anchor_completion_success") is not True:
        return 1
    return 0


def _run_probe_rows(
    replay_rows: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for replay_row in replay_rows:
        for profile in ANCHOR_PROFILES:
            try:
                response = runner(replay_row, profile, checkpoint, tokenizer, device)
                rows.append(_probe_row(replay_row, profile, response))
            except Exception as exc:  # pragma: no cover - fake runner tests cover success path.
                errors.append({"case_id": replay_row.get("case_id"), "profile_id": profile.get("profile_id"), "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_probe(row: dict[str, Any], profile: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    seed = int(row.get("seed") or 0) + int(profile.get("seed_offset") or 0)
    request = GenerationRequest(
        prompt=f"{row.get('prompt', '')}{profile.get('anchor', '')}",
        max_new_tokens=int(profile.get("max_new_tokens") or 16),
        temperature=float(row.get("temperature") or 0.2),
        top_k=None if row.get("top_k") in {None, "", 0, "0"} else int(row.get("top_k")),
        seed=seed,
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _probe_row(replay_row: dict[str, Any], profile: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    expected_terms = [str(term) for term in replay_row.get("expected_terms", [])]
    anchor = str(profile.get("anchor") or "")
    continuation = str(response.get("continuation") or "")
    combined = f"{anchor}{continuation}"
    assisted_hits = _hits(expected_terms, combined)
    new_text_hits = _hits(expected_terms, continuation)
    completion_hits = [term for term in expected_terms if term.lower() not in anchor.lower() and term in assisted_hits]
    return {
        "case_id": str(replay_row.get("case_id") or ""),
        "profile_id": str(profile.get("profile_id") or ""),
        "anchor": anchor,
        "continuation": continuation,
        "combined": combined,
        "expected_terms": expected_terms,
        "anchor_assisted_hit_terms": assisted_hits,
        "new_text_hit_terms": new_text_hits,
        "completion_hit_terms": completion_hits,
        "anchor_assisted_pass": bool(expected_terms) and len(assisted_hits) == len(expected_terms),
        "new_text_pass": bool(expected_terms) and len(new_text_hits) == len(expected_terms),
        "completion_pass": bool(expected_terms) and all(term.lower() in anchor.lower() or term in completion_hits for term in expected_terms),
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
    diagnostic: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    replay_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    probe_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("prompt_aligned_replay_passed", replay.get("status") == "pass", replay.get("status"), "prompt-aligned replay must pass execution"),
        _check("failure_diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "failure diagnostic must pass"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("failed_replay_rows_present", bool(replay_rows), len(replay_rows), "probe must have replay rows"),
        _check("all_probe_rows_executed", len(probe_rows) == len(replay_rows) * len(ANCHOR_PROFILES), len(probe_rows), "probe must execute every case/profile pair"),
        _check("no_probe_errors", not probe_errors, len(probe_errors), "probe should not raise generation errors"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _probe(status: str, rows: list[dict[str, Any]], diagnostic_summary: dict[str, Any]) -> dict[str, Any]:
    anchor_pass_rows = [row for row in rows if row.get("anchor_assisted_pass") is True]
    completion_pass_rows = [row for row in rows if row.get("completion_pass") is True]
    new_text_pass_rows = [row for row in rows if row.get("new_text_pass") is True]
    return {
        "ready": status == "pass",
        "profile_count": len(ANCHOR_PROFILES),
        "case_count": int(diagnostic_summary.get("case_count") or 0),
        "probe_row_count": len(rows),
        "anchor_assisted_pass_count": len(anchor_pass_rows),
        "completion_pass_count": len(completion_pass_rows),
        "new_text_pass_count": len(new_text_pass_rows),
        "anchor_completion_success": bool(completion_pass_rows),
        "new_text_success": bool(new_text_pass_rows),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_policy" if completion_pass_rows else "model_capability_route_promotion_bounded_real_replay_capacity_or_objective_revision",
        "next_step": "build_decoder_anchor_policy" if completion_pass_rows else "revise_capacity_or_training_objective",
    }


def _summary(status: str, checks: list[dict[str, Any]], probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_probe_ready": status == "pass" and probe.get("ready") is True,
        "profile_count": probe.get("profile_count"),
        "case_count": probe.get("case_count"),
        "probe_row_count": probe.get("probe_row_count"),
        "anchor_assisted_pass_count": probe.get("anchor_assisted_pass_count"),
        "completion_pass_count": probe.get("completion_pass_count"),
        "new_text_pass_count": probe.get("new_text_pass_count"),
        "anchor_completion_success": probe.get("anchor_completion_success"),
        "new_text_success": probe.get("new_text_success"),
        "proposed_next_artifact": probe.get("proposed_next_artifact"),
        "next_step": probe.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, probe: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe"
    if probe.get("anchor_completion_success") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_found_completion_signal"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe_no_completion_signal"


def _interpretation(status: str, probe: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Decoder anchor probe inputs or execution failed.", "next_action": "repair decoder anchor probe inputs"}
    if probe.get("anchor_completion_success") is True:
        return {"model_quality_claim": "anchor_assisted_only", "reason": "Anchored prompts can recover at least one required term completion, but this is not unassisted bounded replay success.", "next_action": probe.get("next_step")}
    return {"model_quality_claim": "not_improved", "reason": "Even anchored prompts did not complete required terms.", "next_action": probe.get("next_step")}


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_PROBE_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_probe",
    "locate_failure_diagnostic",
    "locate_prompt_aligned_replay",
    "read_json_report",
    "resolve_exit_code",
]
