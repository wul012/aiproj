from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_route_promotion_bounded_objective_replay_comparison import (
    BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_replay_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_probe.json"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_probe.csv"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_probe.txt"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_probe.md"
BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_decoder_anchor_probe.html"

GeneratorRunner = Callable[[dict[str, Any], dict[str, Any], str | Path, str | Path, str], dict[str, Any]]

ANCHOR_PROFILES = [
    {"profile_id": "prefix_f", "anchor": "f", "max_new_tokens": 12, "seed_offset": 1100, "description": "Give only the first character of fixed."},
    {"profile_id": "prefix_fixed_space", "anchor": "fixed ", "max_new_tokens": 12, "seed_offset": 1200, "description": "Give the first target term and ask for loss."},
    {"profile_id": "prefix_fixed_l", "anchor": "fixed l", "max_new_tokens": 12, "seed_offset": 1300, "description": "Give fixed and the first character of loss."},
]


def locate_objective_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_objective_zero_hit_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_REPLAY_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective decoder anchor probe input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe(
    replay_comparison: dict[str, Any],
    zero_hit_diagnostic: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    replay_comparison_path: str | Path | None = None,
    zero_hit_diagnostic_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective decoder anchor probe",
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else checkpoint.parent / "tokenizer.json"
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    replay_summary = as_dict(replay_comparison.get("summary"))
    diagnostic_summary = as_dict(zero_hit_diagnostic.get("summary"))
    probe_rows, probe_errors = _run_probe_rows(replay_rows, checkpoint, tokenizer, device, generator_runner or _generate_probe)
    checks = _checks(replay_comparison, zero_hit_diagnostic, checkpoint, tokenizer, replay_rows, probe_rows, probe_errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    probe = _probe(status, replay_rows, probe_rows, replay_summary, diagnostic_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, probe),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_zero_hit_diagnostic": str(zero_hit_diagnostic_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "anchor_profiles": ANCHOR_PROFILES,
        "source_summaries": {
            "replay_comparison": replay_summary,
            "zero_hit_diagnostic": diagnostic_summary,
        },
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
    seed = int(row.get("seed") or 1841) + int(profile.get("seed_offset") or 0)
    request = GenerationRequest(
        prompt=f"{row.get('prompt', '')}{profile.get('anchor', '')}",
        max_new_tokens=int(profile.get("max_new_tokens") or 12),
        temperature=0.2,
        top_k=20,
        seed=seed,
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _probe_row(replay_row: dict[str, Any], profile: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    required_terms = [str(term).lower() for term in replay_row.get("required_terms", ["fixed", "loss"])]
    anchor = str(profile.get("anchor") or "")
    continuation = str(response.get("continuation") or "")
    combined = f"{anchor}{continuation}"
    assisted_hits = _hits(required_terms, combined)
    new_text_hits = _hits(required_terms, continuation)
    completion_hits = [term for term in required_terms if term not in anchor.lower() and term in assisted_hits]
    return {
        "case_id": str(replay_row.get("case_id") or ""),
        "profile_id": str(profile.get("profile_id") or ""),
        "anchor": anchor,
        "continuation": continuation,
        "combined": combined,
        "required_terms": required_terms,
        "anchor_assisted_hit_terms": assisted_hits,
        "new_text_hit_terms": new_text_hits,
        "completion_hit_terms": completion_hits,
        "anchor_assisted_pass": bool(required_terms) and len(assisted_hits) == len(required_terms),
        "new_text_pass": bool(required_terms) and len(new_text_hits) == len(required_terms),
        "completion_pass": bool(required_terms) and all(term in anchor.lower() or term in completion_hits for term in required_terms),
        "seed": response.get("seed"),
        "max_new_tokens": response.get("max_new_tokens"),
        "temperature": response.get("temperature"),
        "top_k": response.get("top_k"),
    }


def _hits(required_terms: list[str], text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in required_terms if term in lowered]


def _checks(
    replay: dict[str, Any],
    diagnostic: dict[str, Any],
    checkpoint: Path,
    tokenizer: Path,
    replay_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    probe_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    replay_summary = as_dict(replay.get("summary"))
    diagnostic_summary = as_dict(diagnostic.get("summary"))
    return [
        _check("replay_comparison_passed", replay.get("status") == "pass", replay.get("status"), "objective replay comparison must pass"),
        _check("replay_comparison_ready", replay_summary.get("bounded_objective_replay_comparison_ready") is True, replay_summary.get("bounded_objective_replay_comparison_ready"), "objective replay comparison must be ready"),
        _check("objective_not_recovered", replay_summary.get("objective_contract_recovered") is False, replay_summary.get("objective_contract_recovered"), "anchor probe should run before objective recovery"),
        _check("zero_hit_diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "zero-hit diagnostic must pass"),
        _check("zero_hit_diagnostic_ready", diagnostic_summary.get("bounded_objective_zero_hit_diagnostic_ready") is True, diagnostic_summary.get("bounded_objective_zero_hit_diagnostic_ready"), "zero-hit diagnostic must be ready"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("replay_rows_present", bool(replay_rows), len(replay_rows), "probe must have objective replay rows"),
        _check("all_probe_rows_executed", len(probe_rows) == len(replay_rows) * len(ANCHOR_PROFILES), len(probe_rows), "probe must execute every case/profile pair"),
        _check("no_probe_errors", not probe_errors, len(probe_errors), "probe should not raise generation errors"),
    ]


def _probe(
    status: str,
    replay_rows: list[dict[str, Any]],
    probe_rows: list[dict[str, Any]],
    replay_summary: dict[str, Any],
    diagnostic_summary: dict[str, Any],
) -> dict[str, Any]:
    assisted_pass_rows = [row for row in probe_rows if row.get("anchor_assisted_pass") is True]
    completion_pass_rows = [row for row in probe_rows if row.get("completion_pass") is True]
    new_text_pass_rows = [row for row in probe_rows if row.get("new_text_pass") is True]
    return {
        "ready": status == "pass",
        "case_count": len(replay_rows),
        "profile_count": len(ANCHOR_PROFILES),
        "probe_row_count": len(probe_rows),
        "source_zero_hit_case_count": replay_summary.get("zero_hit_case_count"),
        "diagnosed_near_miss_case_count": diagnostic_summary.get("near_miss_case_count"),
        "anchor_assisted_pass_count": len(assisted_pass_rows),
        "completion_pass_count": len(completion_pass_rows),
        "new_text_pass_count": len(new_text_pass_rows),
        "anchor_completion_success": bool(completion_pass_rows),
        "new_text_success": bool(new_text_pass_rows),
        "promotion_ready": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_decoder_anchor_policy" if completion_pass_rows else "model_capability_route_promotion_bounded_objective_capacity_probe_plan",
        "next_step": "build_bounded_objective_decoder_anchor_policy" if completion_pass_rows else "plan_capacity_or_training_revision",
    }


def _summary(status: str, checks: list[dict[str, Any]], probe: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_decoder_anchor_probe_ready": status == "pass" and probe.get("ready") is True,
        "case_count": probe.get("case_count"),
        "profile_count": probe.get("profile_count"),
        "probe_row_count": probe.get("probe_row_count"),
        "source_zero_hit_case_count": probe.get("source_zero_hit_case_count"),
        "anchor_assisted_pass_count": probe.get("anchor_assisted_pass_count"),
        "completion_pass_count": probe.get("completion_pass_count"),
        "new_text_pass_count": probe.get("new_text_pass_count"),
        "anchor_completion_success": probe.get("anchor_completion_success"),
        "new_text_success": probe.get("new_text_success"),
        "promotion_ready": False,
        "proposed_next_artifact": probe.get("proposed_next_artifact"),
        "next_step": probe.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, probe: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_objective_decoder_anchor_probe"
    if probe.get("anchor_completion_success") is True:
        return "model_capability_route_promotion_bounded_objective_decoder_anchor_probe_found_completion_signal"
    return "model_capability_route_promotion_bounded_objective_decoder_anchor_probe_no_completion_signal"


def _interpretation(status: str, probe: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Decoder anchor probe inputs or execution failed.", "next_action": "repair bounded objective decoder anchor probe inputs"}
    if probe.get("anchor_completion_success") is True:
        return {
            "model_quality_claim": "decoder_anchor_signal_only",
            "reason": "Anchored prompts can complete fixed/loss, but this is assisted evidence and does not repair unassisted objective replay.",
            "next_action": probe.get("next_step"),
        }
    return {"model_quality_claim": "not_improved", "reason": "Even anchored prompts did not complete the required terms.", "next_action": probe.get("next_step")}


__all__ = [
    "ANCHOR_PROFILES",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_DECODER_ANCHOR_PROBE_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_decoder_anchor_probe",
    "locate_objective_replay_comparison",
    "locate_objective_zero_hit_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
