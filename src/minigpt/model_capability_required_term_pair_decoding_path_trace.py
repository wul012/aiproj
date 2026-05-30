from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_decoding_gap_probe import (
    REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_decoding_path_trace_components import (
    select_decoding_path_trace_targets,
    summarize_decoding_path_probe_rows,
    summarize_required_term_pair_decoding_path_trace,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import utc_now


REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_JSON_FILENAME = "model_capability_required_term_pair_decoding_path_trace.json"
REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_TEXT_FILENAME = "model_capability_required_term_pair_decoding_path_trace.txt"
REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_MARKDOWN_FILENAME = "model_capability_required_term_pair_decoding_path_trace.md"
REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_HTML_FILENAME = "model_capability_required_term_pair_decoding_path_trace.html"

TraceFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_pair_decoding_path_trace_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DECODING_GAP_PROBE_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_decoding_path_trace(
    decoding_gap_probe: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    variant_limit: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    trace_func: TraceFunc | None = None,
) -> dict[str, Any]:
    targets = select_decoding_path_trace_targets(decoding_gap_probe, variant_limit=variant_limit)
    issues = _input_issues(decoding_gap_probe, targets)
    probe_rows = _trace_targets(targets, device=device, trace_func=trace_func) if not issues else []
    probe_summaries = summarize_decoding_path_probe_rows(probe_rows)
    summary = summarize_required_term_pair_decoding_path_trace(targets, probe_rows, probe_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair decoding path trace",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_decoding_gap_probe": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "variant_limit": variant_limit,
            "device": device,
            "experiment_boundary": "sampling-path trace only; no checkpoint training",
        },
        "targets": targets,
        "probe_rows": probe_rows,
        "probe_summaries": probe_summaries,
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


def _trace_targets(targets: list[dict[str, Any]], *, device: str, trace_func: TraceFunc | None) -> list[dict[str, Any]]:
    tracer = trace_func or _trace_with_checkpoint
    rows: list[dict[str, Any]] = []
    for target in targets:
        for probe in target.get("probes") or []:
            request = {**probe, "device": device}
            rows.append({**probe, **tracer(request)})
    return rows


def _trace_with_checkpoint(request: dict[str, Any]) -> dict[str, Any]:
    import torch
    from torch.nn import functional as F

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    device = torch.device(str(request.get("device") or "cpu"))
    checkpoint = torch.load(Path(str(request["checkpoint_path"])), map_location=device, weights_only=False)
    tokenizer = load_tokenizer(Path(str(request["tokenizer_path"])))
    model = MiniGPT(GPTConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt = str(request.get("prompt") or f"{request.get('prompt_term')}:")
    expected = str(request.get("expected_term") or "")
    prompt_ids = tokenizer.encode(prompt)
    expected_ids = tokenizer.encode(expected)
    max_new_tokens = int(request.get("max_new_tokens") or 12)
    temperature = float(request.get("temperature") or 0.2)
    top_k = int(request["top_k"]) if request.get("top_k") is not None else None
    seed = request.get("seed")
    if seed is not None:
        torch.manual_seed(int(seed))
        if device.type == "cuda":
            torch.cuda.manual_seed_all(int(seed))

    running = list(prompt_ids[-model.config.block_size :])
    sampled_ids: list[int] = []
    steps: list[dict[str, Any]] = []
    expected_first = int(expected_ids[0]) if expected_ids else None
    first_rank: int | None = None
    first_logprob: float | None = None
    with torch.no_grad():
        for step in range(max_new_tokens):
            idx = torch.tensor([running[-model.config.block_size :]], dtype=torch.long, device=device)
            logits, _ = model(idx)
            logits = logits[0, -1] / temperature
            if top_k is not None:
                top_values, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits = logits.masked_fill(logits < top_values[-1], -float("inf"))
            log_probs = F.log_softmax(logits, dim=-1)
            probs = F.softmax(logits, dim=-1)
            token_id = int(torch.multinomial(probs, num_samples=1).item())
            if step == 0 and expected_first is not None:
                first_rank = _rank_token(log_probs, expected_first)
                first_logprob = round(float(log_probs[expected_first].item()), 6)
            sampled_ids.append(token_id)
            running.append(token_id)
            steps.append(
                {
                    "step": step,
                    "sampled_token_id": token_id,
                    "sampled_text": tokenizer.decode([token_id]),
                    "continuation_preview": tokenizer.decode(sampled_ids)[:80],
                }
            )

    continuation = tokenizer.decode(sampled_ids)
    first_sample = sampled_ids[0] if sampled_ids else None
    return {
        "continuation": continuation,
        "continuation_preview": continuation[:80],
        "first_expected_token_id": expected_first,
        "first_expected_token_text": tokenizer.decode([expected_first]) if expected_first is not None else "",
        "first_expected_token_rank": first_rank,
        "first_expected_token_logprob": first_logprob,
        "first_sample_token_id": first_sample,
        "first_sample_text": tokenizer.decode([first_sample]) if first_sample is not None else "",
        "first_sample_matches_expected_first_token": first_sample == expected_first,
        "expected_first_token_seen_step": _seen_step(sampled_ids, expected_first),
        "steps": steps,
    }


def _rank_token(log_probs: Any, token_id: int) -> int:
    target = float(log_probs[token_id].item())
    better = int((log_probs > target).sum().item())
    return better + 1


def _seen_step(sampled_ids: list[int], token_id: int | None) -> int | None:
    if token_id is None:
        return None
    for index, sampled in enumerate(sampled_ids):
        if int(sampled) == int(token_id):
            return index
    return None


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source decoding-gap probe report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source decoding-gap probe report is not pass")
    if not targets:
        issues.append("source decoding-gap probe has no traceable target")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_decoding_path_trace"
    decision = str(summary.get("decoding_path_trace_decision") or "")
    if decision == "decoding_path_trace_late_expression_after_first_miss":
        return "required_term_pair_decoding_path_late_expression"
    if decision == "decoding_path_trace_first_token_expression_observed":
        return "required_term_pair_decoding_path_first_token_expression"
    return "required_term_pair_decoding_path_first_token_miss"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("late_hit_after_first_miss_count") or 0) > 0:
        return "late_generation_expression_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source decoding-gap probe did not provide traceable rows."
    if int(summary.get("late_hit_after_first_miss_count") or 0) > 0:
        return "Some expected terms appear only after the first sampled token already missed the expected first token."
    if int(summary.get("first_sample_match_count") or 0) > 0:
        return "At least one probe sampled the expected first token immediately."
    return "The traced probes missed the expected first token at the first generation step."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair decoding-gap probe rows before path tracing"
    if int(summary.get("late_hit_after_first_miss_count") or 0) > 0:
        return "test constrained first-token repair before changing training data"
    return "inspect logits and tokenization around the first generation step"
