from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_decoding_path_trace import (
    REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_first_token_repair_components import (
    select_first_token_repair_targets,
    summarize_first_token_repair_profiles,
    summarize_required_term_pair_first_token_repair,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report as read_json_report
from minigpt.report_utils import utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code  # noqa: F401 (re-export)


REQUIRED_TERM_PAIR_FIRST_TOKEN_REPAIR_JSON_FILENAME = "model_capability_required_term_pair_first_token_repair.json"
REQUIRED_TERM_PAIR_FIRST_TOKEN_REPAIR_TEXT_FILENAME = "model_capability_required_term_pair_first_token_repair.txt"
REQUIRED_TERM_PAIR_FIRST_TOKEN_REPAIR_MARKDOWN_FILENAME = "model_capability_required_term_pair_first_token_repair.md"
REQUIRED_TERM_PAIR_FIRST_TOKEN_REPAIR_HTML_FILENAME = "model_capability_required_term_pair_first_token_repair.html"

RepairFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_pair_first_token_repair_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_first_token_repair(
    path_trace_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    variant_limit: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    repair_func: RepairFunc | None = None,
) -> dict[str, Any]:
    targets = select_first_token_repair_targets(path_trace_report, variant_limit=variant_limit)
    issues = _input_issues(path_trace_report, targets)
    repair_rows = _repair_targets(targets, device=device, repair_func=repair_func) if not issues else []
    profile_summaries = summarize_first_token_repair_profiles(targets, repair_rows)
    summary = summarize_required_term_pair_first_token_repair(targets, repair_rows, profile_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair first-token repair",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_decoding_path_trace": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "variant_limit": variant_limit,
            "device": device,
            "experiment_boundary": "constrained first-token repair only; no checkpoint training",
        },
        "targets": targets,
        "repair_rows": repair_rows,
        "profile_summaries": profile_summaries,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def _repair_targets(targets: list[dict[str, Any]], *, device: str, repair_func: RepairFunc | None) -> list[dict[str, Any]]:
    repair = repair_func or _repair_with_checkpoint
    rows: list[dict[str, Any]] = []
    for target in targets:
        for probe in target.get("probes") or []:
            request = {**probe, "device": device}
            result = repair(request)
            expected = str(probe.get("expected_term") or "")
            continuation = str(result.get("repaired_continuation") or "")
            rows.append(
                {
                    **probe,
                    **result,
                    "source_continuation_hit": bool(probe.get("continuation_hit")),
                    "repaired_continuation_hit": expected in continuation,
                    "repaired_generated_hit": expected in str(result.get("repaired_generated") or ""),
                    "repaired_continuation_preview": continuation[:100],
                }
            )
    return rows


def _repair_with_checkpoint(request: dict[str, Any]) -> dict[str, Any]:
    import torch

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    device = torch.device(str(request.get("device") or "cpu"))
    checkpoint = torch.load(Path(str(request["checkpoint_path"])), map_location=device, weights_only=False)
    tokenizer = load_tokenizer(Path(str(request["tokenizer_path"])))
    model = MiniGPT(GPTConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt = str(request.get("prompt") or f"{request.get('prompt_term')}:")
    prompt_ids = tokenizer.encode(prompt)
    forced_id = int(request["first_expected_token_id"])
    max_new_tokens = int(request.get("max_new_tokens") or 12)
    temperature = float(request.get("temperature") or 0.2)
    top_k = int(request["top_k"]) if request.get("top_k") is not None else None
    seed = request.get("seed")
    if seed is not None:
        torch.manual_seed(int(seed))
        if device.type == "cuda":
            torch.cuda.manual_seed_all(int(seed))

    idx = torch.tensor([prompt_ids[-model.config.block_size :] + [forced_id]], dtype=torch.long, device=device)
    remaining = max(0, max_new_tokens - 1)
    with torch.no_grad():
        if remaining:
            idx = model.generate(idx, max_new_tokens=remaining, temperature=temperature, top_k=top_k)
    generated_ids = idx[0].tolist()
    continuation_ids = generated_ids[len(prompt_ids) :] if generated_ids[: len(prompt_ids)] == prompt_ids else generated_ids
    generated = tokenizer.decode(generated_ids)
    continuation = tokenizer.decode(continuation_ids)
    return {
        "forced_first_token_id": forced_id,
        "forced_first_token_text": tokenizer.decode([forced_id]),
        "repaired_generated": generated,
        "repaired_continuation": continuation,
    }


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source decoding-path trace report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source decoding-path trace report is not pass")
    if not targets:
        issues.append("source decoding-path trace has no first-token repair target")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_first_token_repair"
    decision = str(summary.get("first_token_repair_decision") or "")
    if decision == "first_token_repair_full_expression_recovered":
        return "required_term_pair_first_token_repair_full_expression"
    if decision == "first_token_repair_improved_partial_expression":
        return "required_term_pair_first_token_repair_improved_partial"
    if decision == "first_token_repair_preserved_partial_expression":
        return "required_term_pair_first_token_repair_preserved_partial"
    return "required_term_pair_first_token_repair_not_expressed"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("repaired_profile_full_hit_count") or 0) > 0:
        return "constrained_generation_expression_only"
    if int(summary.get("improved_prompt_count") or 0) > 0:
        return "constrained_generation_partial_signal"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The decoding path trace did not provide repairable first-token misses."
    if int(summary.get("repaired_profile_full_hit_count") or 0) > 0:
        return "Forcing the expected first token recovers at least one full pair profile."
    if int(summary.get("improved_prompt_count") or 0) > 0:
        return "Forcing the expected first token improves at least one previously missed prompt."
    return "Forcing the expected first token did not improve continuation hits."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair path trace rows before constrained probing"
    if int(summary.get("repaired_profile_full_hit_count") or 0) > 0:
        return "compare constrained repair against a small first-token logit-bias profile"
    return "treat the issue as deeper continuation modeling rather than only first-token sampling"
