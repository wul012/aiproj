from __future__ import annotations

import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.json"
)
TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.csv"
)
TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.txt"
)
TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.md"
)
TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe.html"
)

LossTokenScorer = Callable[[str, str], dict[str, Any]]


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def locate_replay_delta_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_DELTA_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("loss-token probability probe input must be a JSON object")
    return dict(payload)


def build_loss_token_probability_probe(
    objective_contract_report: dict[str, Any],
    replay_delta_diagnostic_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    device: str = "auto",
    top_k: int = 5,
    token_scorer: LossTokenScorer | None = None,
    objective_contract_path: str | Path | None = None,
    replay_delta_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory loss-token probability probe",
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract_summary = as_dict(objective_contract_report.get("summary"))
    delta_summary = as_dict(replay_delta_diagnostic_report.get("summary"))
    contract_cases = list_of_dicts(objective_contract_report.get("contract_cases"))
    checkpoint = Path(checkpoint_path)
    tokenizer = Path(tokenizer_path)
    scorer = token_scorer or _build_torch_scorer(checkpoint, tokenizer, device=device, top_k=top_k)
    probe_rows = _probe_rows(contract_cases, scorer)
    case_rows = _case_rows(probe_rows)
    diagnostic = _diagnostic(probe_rows, case_rows)
    checks = _checks(objective_contract_report, contract_summary, replay_delta_diagnostic_report, delta_summary, contract_cases, checkpoint, tokenizer, diagnostic)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, contract_summary, delta_summary, probe_rows, case_rows, diagnostic)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_objective_contract": str(objective_contract_path or ""),
        "source_replay_delta_diagnostic": str(replay_delta_diagnostic_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "device": device,
        "top_k": top_k,
        "contract_summary": contract_summary,
        "replay_delta_summary": delta_summary,
        "probe_rows": probe_rows,
        "case_rows": case_rows,
        "diagnostic": diagnostic,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_probe_ready: bool) -> int:
    return 1 if require_probe_ready and report.get("status") != "pass" else 0


def _probe_rows(contract_cases: list[dict[str, Any]], scorer: LossTokenScorer) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in contract_cases:
        case_id = str(case.get("case_id") or "")
        prompt = str(case.get("prompt") or "")
        expected_completion = str(case.get("expected_completion") or "fixed loss")
        fixed_l_prefix = "\nfixed l"
        target_suffix = _target_suffix(expected_completion, fixed_l_prefix)
        context = prompt + fixed_l_prefix
        for index, target_token in enumerate(target_suffix):
            score = scorer(context, target_token)
            target_probability = float(score.get("target_probability") or 0.0)
            target_rank = int(score.get("target_rank") or 0)
            rows.append({
                "case_id": case_id,
                "step_index": index,
                "prompt": prompt,
                "fixed_l_prefix": fixed_l_prefix,
                "context_suffix": context[-80:],
                "target_suffix": target_suffix,
                "target_token": target_token,
                "target_token_id": score.get("target_token_id"),
                "target_probability": target_probability,
                "target_rank": target_rank,
                "target_in_top_k": score.get("target_in_top_k") is True,
                "top_token": score.get("top_token"),
                "top_token_probability": score.get("top_token_probability"),
                "top_candidates": score.get("top_candidates", []),
                "state_label": _state_label(target_rank, target_probability, score.get("target_in_top_k") is True),
            })
            context += target_token
    return rows


def _target_suffix(expected_completion: str, fixed_l_prefix: str) -> str:
    normalized_prefix = fixed_l_prefix.strip()
    if expected_completion.startswith(normalized_prefix):
        return expected_completion[len(normalized_prefix) :]
    if expected_completion == "fixed loss":
        return "oss"
    return expected_completion[-3:] or "oss"


def _case_rows(probe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in sorted({str(row.get("case_id")) for row in probe_rows}):
        case_steps = [row for row in probe_rows if row.get("case_id") == case_id]
        probabilities = [float(row.get("target_probability") or 0.0) for row in case_steps]
        ranks = [int(row.get("target_rank") or 0) for row in case_steps]
        product = math.prod(probabilities) if probabilities else 0.0
        rows.append({
            "case_id": case_id,
            "step_count": len(case_steps),
            "target_suffix": "".join(str(row.get("target_token") or "") for row in case_steps),
            "target_probability_product": product,
            "min_target_probability": min(probabilities) if probabilities else 0.0,
            "max_target_rank": max(ranks) if ranks else 0,
            "top1_step_count": sum(1 for rank in ranks if rank == 1),
            "topk_step_count": sum(1 for row in case_steps if row.get("target_in_top_k") is True),
            "loss_suffix_top1": bool(case_steps) and all(rank == 1 for rank in ranks),
            "loss_suffix_topk": bool(case_steps) and all(row.get("target_in_top_k") is True for row in case_steps),
        })
    return rows


def _diagnostic(probe_rows: list[dict[str, Any]], case_rows: list[dict[str, Any]]) -> dict[str, Any]:
    probabilities = [float(row.get("target_probability") or 0.0) for row in probe_rows]
    ranks = [int(row.get("target_rank") or 0) for row in probe_rows]
    target_top1_count = sum(1 for rank in ranks if rank == 1)
    target_topk_count = sum(1 for row in probe_rows if row.get("target_in_top_k") is True)
    all_cases_top1 = bool(case_rows) and all(row.get("loss_suffix_top1") is True for row in case_rows)
    all_cases_topk = bool(case_rows) and all(row.get("loss_suffix_topk") is True for row in case_rows)
    low_probability_step_count = sum(1 for probability in probabilities if probability < 0.05)
    ready = bool(probe_rows) and all(probability >= 0.0 for probability in probabilities)
    return {
        "ready": ready,
        "probe_step_count": len(probe_rows),
        "case_count": len(case_rows),
        "target_top1_step_count": target_top1_count,
        "target_topk_step_count": target_topk_count,
        "target_top1_rate": target_top1_count / len(probe_rows) if probe_rows else 0.0,
        "target_topk_rate": target_topk_count / len(probe_rows) if probe_rows else 0.0,
        "min_target_probability": min(probabilities) if probabilities else 0.0,
        "mean_target_probability": sum(probabilities) / len(probabilities) if probabilities else 0.0,
        "max_target_rank": max(ranks) if ranks else 0,
        "low_probability_step_count": low_probability_step_count,
        "all_cases_loss_suffix_top1": all_cases_top1,
        "all_cases_loss_suffix_topk": all_cases_topk,
        "next_step": _next_step(all_cases_top1, all_cases_topk, low_probability_step_count),
    }


def _checks(
    objective_contract: dict[str, Any],
    contract_summary: dict[str, Any],
    replay_delta: dict[str, Any],
    delta_summary: dict[str, Any],
    contract_cases: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    diagnostic: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _check("objective_contract_passed", objective_contract.get("status") == "pass", objective_contract.get("status"), "objective contract must pass structurally"),
        _check("objective_contract_ready", contract_summary.get("bounded_objective_contract_ready") is True, contract_summary.get("bounded_objective_contract_ready"), "objective contract must be ready"),
        _check("replay_delta_passed", replay_delta.get("status") == "pass", replay_delta.get("status"), "source replay delta diagnostic must pass structurally"),
        _check(
            "replay_delta_ready",
            delta_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready") is True,
            delta_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_delta_diagnostic_ready"),
            "source replay delta diagnostic must be ready",
        ),
        _check("replay_delta_no_contract_gain", delta_summary.get("no_contract_gain_confirmed") is True, delta_summary.get("no_contract_gain_confirmed"), "probability probe should follow a no-contract-gain replay delta"),
        _check("contract_cases_present", bool(contract_cases), len(contract_cases), "objective contract must expose contract cases"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "tokenizer.json must exist"),
        _check("probe_rows_scored", diagnostic.get("probe_step_count", 0) > 0, diagnostic.get("probe_step_count"), "probe must score at least one target token"),
    ]


def _summary(
    status: str,
    contract_summary: dict[str, Any],
    delta_summary: dict[str, Any],
    probe_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready": status == "pass",
        "source_contract_case_count": contract_summary.get("contract_case_count"),
        "source_replay_no_contract_gain_confirmed": delta_summary.get("no_contract_gain_confirmed"),
        "probe_step_count": len(probe_rows),
        "case_count": len(case_rows),
        "target_top1_step_count": diagnostic.get("target_top1_step_count"),
        "target_topk_step_count": diagnostic.get("target_topk_step_count"),
        "target_top1_rate": diagnostic.get("target_top1_rate"),
        "target_topk_rate": diagnostic.get("target_topk_rate"),
        "min_target_probability": diagnostic.get("min_target_probability"),
        "mean_target_probability": diagnostic.get("mean_target_probability"),
        "max_target_rank": diagnostic.get("max_target_rank"),
        "low_probability_step_count": diagnostic.get("low_probability_step_count"),
        "all_cases_loss_suffix_top1": diagnostic.get("all_cases_loss_suffix_top1"),
        "all_cases_loss_suffix_topk": diagnostic.get("all_cases_loss_suffix_topk"),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe"
    if diagnostic.get("all_cases_loss_suffix_top1") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_top1_but_decode_blocked"
    if diagnostic.get("all_cases_loss_suffix_topk") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_visible_not_top1"
    return "bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_loss_suffix_low_probability"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Loss-token probability probe inputs or scoring failed.", "next_action": "fix_loss_token_probability_probe_inputs"}
    return {
        "model_quality_claim": "loss_token_probability_probe_only",
        "reason": "The probe measures teacher-forced target-token probability after fixed-l; it is diagnostic evidence, not a replay pass.",
        "next_action": diagnostic.get("next_step"),
    }


def _next_step(all_top1: bool, all_topk: bool, low_probability_step_count: int) -> str:
    if all_top1:
        return "inspect_decoding_temperature_or_stop_condition_for_loss_suffix"
    if all_topk:
        return "test_greedy_or_low_temperature_loss_suffix_replay"
    if low_probability_step_count:
        return "add_targeted_oss_suffix_probability_repair_before_more_training"
    return "review_loss_suffix_probability_probe"


def _state_label(target_rank: int, target_probability: float, target_in_top_k: bool) -> str:
    if target_rank == 1:
        return "target_top1"
    if target_in_top_k:
        return "target_visible_in_top_k"
    if target_probability < 0.05:
        return "target_low_probability"
    return "target_not_top_k"


def _build_torch_scorer(checkpoint_path: Path, tokenizer_path: Path, *, device: str, top_k: int) -> LossTokenScorer:
    import torch
    from torch.nn import functional as F

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    selected_device = torch.device("cuda" if device == "auto" and torch.cuda.is_available() else ("cpu" if device == "auto" else device))
    checkpoint = torch.load(checkpoint_path, map_location=selected_device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    model = MiniGPT(GPTConfig(**checkpoint["config"])).to(selected_device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    def score(context: str, target_token: str) -> dict[str, Any]:
        token_ids = tokenizer.encode(context)
        target_ids = tokenizer.encode(target_token)
        if not token_ids:
            raise ValueError("probability probe context produced no token ids")
        if len(target_ids) != 1:
            raise ValueError(f"target token must encode to exactly one token id: {target_token!r}")
        idx = torch.tensor([token_ids[-model.config.block_size :]], dtype=torch.long, device=selected_device)
        with torch.no_grad():
            logits, _ = model(idx)
            probs = F.softmax(logits[:, -1, :], dim=-1)[0]
        target_id = int(target_ids[0])
        target_probability = float(probs[target_id].item())
        target_rank = int((probs > probs[target_id]).sum().item()) + 1
        top_values, top_indices = torch.topk(probs, min(top_k, probs.numel()))
        top_candidates = [
            {
                "rank": rank + 1,
                "token_id": int(token_id.item()),
                "token_text": tokenizer.decode([int(token_id.item())]),
                "probability": float(value.item()),
            }
            for rank, (value, token_id) in enumerate(zip(top_values, top_indices))
        ]
        top_token = top_candidates[0] if top_candidates else {}
        return {
            "target_token_id": target_id,
            "target_probability": target_probability,
            "target_rank": target_rank,
            "target_in_top_k": any(candidate["token_id"] == target_id for candidate in top_candidates),
            "top_token": top_token.get("token_text"),
            "top_token_probability": top_token.get("probability"),
            "top_candidates": top_candidates,
        }

    return score


__all__ = [
    "TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_TEXT_FILENAME",
    "build_loss_token_probability_probe",
    "locate_objective_contract",
    "locate_replay_delta_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
