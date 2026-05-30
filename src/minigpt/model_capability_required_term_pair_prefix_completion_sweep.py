from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_decoding_path_trace import (
    REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_prefix_completion_sweep_components import (
    select_prefix_completion_targets,
    summarize_prefix_completion_probe_rows,
    summarize_required_term_pair_prefix_completion_sweep,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import utc_now


REQUIRED_TERM_PAIR_PREFIX_COMPLETION_SWEEP_JSON_FILENAME = "model_capability_required_term_pair_prefix_completion_sweep.json"
REQUIRED_TERM_PAIR_PREFIX_COMPLETION_SWEEP_TEXT_FILENAME = "model_capability_required_term_pair_prefix_completion_sweep.txt"
REQUIRED_TERM_PAIR_PREFIX_COMPLETION_SWEEP_MARKDOWN_FILENAME = "model_capability_required_term_pair_prefix_completion_sweep.md"
REQUIRED_TERM_PAIR_PREFIX_COMPLETION_SWEEP_HTML_FILENAME = "model_capability_required_term_pair_prefix_completion_sweep.html"

SweepFunc = Callable[[dict[str, Any]], list[dict[str, Any]]]


def locate_model_capability_required_term_pair_prefix_completion_sweep_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_DECODING_PATH_TRACE_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_prefix_completion_sweep(
    path_trace_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    variant_limit: int | None = 1,
    device: str = "cpu",
    generated_at: str | None = None,
    sweep_func: SweepFunc | None = None,
) -> dict[str, Any]:
    targets = select_prefix_completion_targets(path_trace_report, variant_limit=variant_limit)
    issues = _input_issues(path_trace_report, targets)
    rows = _sweep_targets(targets, device=device, sweep_func=sweep_func) if not issues else []
    probe_summaries = summarize_prefix_completion_probe_rows(rows)
    summary = summarize_required_term_pair_prefix_completion_sweep(targets, rows, probe_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair prefix completion sweep",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _report_decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_decoding_path_trace": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "variant_limit": variant_limit,
            "device": device,
            "experiment_boundary": "forced-prefix completion only; no checkpoint training",
        },
        "targets": targets,
        "prefix_rows": rows,
        "probe_summaries": probe_summaries,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _sweep_targets(targets: list[dict[str, Any]], *, device: str, sweep_func: SweepFunc | None) -> list[dict[str, Any]]:
    sweep = sweep_func or _sweep_with_checkpoint
    rows: list[dict[str, Any]] = []
    for target in targets:
        for probe in target.get("probes") or []:
            rows.extend(sweep({**probe, "device": device}))
    return rows


def _sweep_with_checkpoint(request: dict[str, Any]) -> list[dict[str, Any]]:
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
    expected = str(request.get("expected_term") or "")
    prompt_ids = tokenizer.encode(prompt)
    expected_ids = tokenizer.encode(expected)
    rows: list[dict[str, Any]] = []
    for prefix_len in range(1, len(expected_ids) + 1):
        forced_prefix = expected_ids[:prefix_len]
        max_new_tokens = max(0, int(request.get("max_new_tokens") or 12) - prefix_len)
        seed = request.get("seed")
        if seed is not None:
            torch.manual_seed(int(seed) + prefix_len)
            if device.type == "cuda":
                torch.cuda.manual_seed_all(int(seed) + prefix_len)
        idx = torch.tensor([prompt_ids[-model.config.block_size :] + forced_prefix], dtype=torch.long, device=device)
        with torch.no_grad():
            if max_new_tokens:
                idx = model.generate(
                    idx,
                    max_new_tokens=max_new_tokens,
                    temperature=float(request.get("temperature") or 0.2),
                    top_k=int(request["top_k"]) if request.get("top_k") is not None else None,
                )
        ids = idx[0].tolist()
        continuation_ids = ids[len(prompt_ids) :] if ids[: len(prompt_ids)] == prompt_ids else ids
        continuation = tokenizer.decode(continuation_ids)
        rows.append(
            {
                **request,
                "expected_token_count": len(expected_ids),
                "forced_prefix_token_count": prefix_len,
                "forced_prefix_text": tokenizer.decode(forced_prefix),
                "completion": continuation,
                "completion_preview": continuation[:100],
                "prefix_completion_hit": expected in continuation,
            }
        )
    return rows


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source decoding-path trace report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source decoding-path trace report is not pass")
    if not targets:
        issues.append("source decoding-path trace has no prefix completion target")
    return issues


def _report_decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_prefix_completion_sweep"
    decision = str(summary.get("prefix_completion_sweep_decision") or "")
    if decision == "prefix_completion_one_token_sufficient":
        return "required_term_pair_prefix_completion_one_token"
    if decision == "prefix_completion_requires_longer_prefix":
        return "required_term_pair_prefix_completion_long_prefix"
    if decision == "prefix_completion_partial_span_repair":
        return "required_term_pair_prefix_completion_partial"
    return "required_term_pair_prefix_completion_not_recovered"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("one_token_prefix_hit_probe_count") or 0) > 0:
        return "forced_prefix_completion_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source path trace did not provide prefix-completion targets."
    probe_count = int(summary.get("probe_summary_count") or 0)
    one_token_count = int(summary.get("one_token_prefix_hit_probe_count") or 0)
    full_prefix_count = int(summary.get("full_prefix_hit_probe_count") or 0)
    if probe_count and one_token_count == probe_count:
        return "At least one probe completes the expected term from a one-token forced prefix."
    if full_prefix_count == probe_count:
        return "All probes retain the expected term with a full prefix, but some require longer forced prefixes."
    if full_prefix_count > 0:
        return "Only part of the probe set retains the expected term under forced prefixes."
    return "Forced prefixes did not recover expected term completion."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair path trace inputs before prefix completion probing"
    if int(summary.get("span_completion_gap_probe_count") or 0) > 0:
        return "compare prefix completion with a tiny continuation-span objective before more decoding tweaks"
    return "use prefix completion evidence to design the smallest next training objective"
