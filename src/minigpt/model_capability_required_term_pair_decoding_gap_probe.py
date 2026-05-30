from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_decoding_gap_probe_components import (
    default_decoding_gap_profiles,
    select_decoding_gap_targets,
    summarize_decoding_gap_profiles,
    summarize_required_term_pair_decoding_gap_probe,
)
from minigpt.model_capability_required_term_pair_generation_gap import (
    REQUIRED_TERM_PAIR_GENERATION_GAP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import utc_now


REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_JSON_FILENAME = "model_capability_required_term_pair_decoding_gap_probe.json"
REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_TEXT_FILENAME = "model_capability_required_term_pair_decoding_gap_probe.txt"
REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_MARKDOWN_FILENAME = "model_capability_required_term_pair_decoding_gap_probe.md"
REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_HTML_FILENAME = "model_capability_required_term_pair_decoding_gap_probe.html"

GenerationFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_pair_decoding_gap_probe_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_GENERATION_GAP_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_decoding_gap_probe(
    generation_gap_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    forced_choice_report: dict[str, Any] | None = None,
    forced_choice_path: str | Path | None = None,
    profiles: list[dict[str, Any]] | None = None,
    variant_limit: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerationFunc | None = None,
) -> dict[str, Any]:
    forced_path = forced_choice_path or generation_gap_report.get("source_required_term_pair_forced_choice_diagnostic")
    forced_report = forced_choice_report or _read_source_report(forced_path)
    profile_rows = profiles or default_decoding_gap_profiles()
    targets = select_decoding_gap_targets(generation_gap_report, forced_report, variant_limit=variant_limit)
    issues = _input_issues(generation_gap_report, forced_report, forced_path, targets)
    probe_rows = _run_decoding_probes(targets, profile_rows, device=device, generate_func=generate_func) if not issues else []
    profile_summaries = summarize_decoding_gap_profiles(targets, profile_rows, probe_rows)
    summary = summarize_required_term_pair_decoding_gap_probe(targets, profile_rows, probe_rows, profile_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair decoding gap probe",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_generation_gap": str(source_path) if source_path else None,
        "source_required_term_pair_forced_choice_diagnostic": str(forced_path) if forced_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "variant_limit": variant_limit,
            "device": device,
            "experiment_boundary": "generation-side probing only; no checkpoint training",
        },
        "profiles": profile_rows,
        "targets": targets,
        "probe_rows": probe_rows,
        "profile_summaries": profile_summaries,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_decoding_probes(
    targets: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    *,
    device: str,
    generate_func: GenerationFunc | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    generator = generate_func or _generate_with_checkpoint
    for target in targets:
        for profile in profiles:
            for prompt in target.get("prompts") or []:
                request = {
                    "variant_id": target.get("variant_id"),
                    "variant_label": target.get("variant_label"),
                    "run_id": target.get("run_id"),
                    "pair_id": target.get("pair_id"),
                    "checkpoint_path": target.get("checkpoint_path"),
                    "tokenizer_path": target.get("tokenizer_path"),
                    "device": device,
                    "profile_id": profile.get("profile_id"),
                    "prompt": f"{prompt.get('prompt_term')}:",
                    "prompt_term": prompt.get("prompt_term"),
                    "expected_term": prompt.get("expected_term"),
                    "max_new_tokens": profile.get("max_new_tokens"),
                    "temperature": profile.get("temperature"),
                    "top_k": profile.get("top_k"),
                    "seed": profile.get("seed"),
                }
                response = generator(request)
                continuation = str(response.get("continuation") or "")
                generated = str(response.get("generated") or "")
                expected = str(request.get("expected_term") or "")
                rows.append(
                    {
                        **request,
                        "generated": generated,
                        "continuation": continuation,
                        "continuation_preview": continuation[:80],
                        "generated_preview": generated[:120],
                        "continuation_hit": expected in continuation,
                        "generated_hit": expected in generated,
                    }
                )
    return rows


def _generate_with_checkpoint(request: dict[str, Any]) -> dict[str, Any]:
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    generator = MiniGPTGenerator(
        str(request.get("checkpoint_path") or ""),
        str(request.get("tokenizer_path") or ""),
        str(request.get("device") or "cpu"),
    )
    response = generator.generate(
        GenerationRequest(
            prompt=str(request.get("prompt") or ""),
            max_new_tokens=int(request.get("max_new_tokens") or 12),
            temperature=float(request.get("temperature") or 0.2),
            top_k=int(request["top_k"]) if request.get("top_k") is not None else None,
            seed=int(request["seed"]) if request.get("seed") is not None else None,
        )
    )
    return response.to_dict()


def _read_source_report(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        return read_json_report(Path(path))
    except (OSError, ValueError):
        return {}


def _input_issues(
    generation_gap_report: dict[str, Any],
    forced_choice_report: dict[str, Any],
    forced_path: str | Path | None,
    targets: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not generation_gap_report:
        issues.append("source generation-gap report is missing or invalid")
    if generation_gap_report and generation_gap_report.get("status") != "pass":
        issues.append("source generation-gap report is not pass")
    if not forced_path:
        issues.append("source generation-gap report does not point to a forced-choice diagnostic")
    if forced_path and not forced_choice_report:
        issues.append("source forced-choice diagnostic report could not be read")
    if forced_choice_report and forced_choice_report.get("status") != "pass":
        issues.append("source forced-choice diagnostic report is not pass")
    if not targets:
        issues.append("source generation-gap report has no forced-generation gap target with checkpoint")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_decoding_gap_probe"
    decision = str(summary.get("decoding_gap_probe_decision") or "")
    if decision == "decoding_gap_probe_generation_expression_found":
        return "required_term_pair_decoding_gap_expression_found"
    if decision == "decoding_gap_probe_partial_expression_only":
        return "required_term_pair_decoding_gap_partial_only"
    return "required_term_pair_decoding_gap_not_expressed"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("profile_full_hit_count") or 0) > 0:
        return "generation_expression_observed_under_profile"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The generation-gap target or checkpoint metadata was not scoreable."
    if int(summary.get("profile_full_hit_count") or 0) > 0:
        return "At least one decoding profile expressed every expected prompt continuation for the gap target."
    if int(summary.get("continuation_hit_count") or 0) > 0:
        return "Some decoding probes expressed expected terms, but no profile expressed the full pair."
    return "The tested decoding profiles did not express the forced-choice internal signal."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair source checkpoint links before generation-side probing"
    if int(summary.get("profile_full_hit_count") or 0) > 0:
        return "compare the successful decoding profile against default generation settings"
    return "inspect first-token rank and sampled path before adding more training variants"
