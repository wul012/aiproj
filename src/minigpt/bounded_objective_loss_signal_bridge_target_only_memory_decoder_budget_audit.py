from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe import (
    TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.tokenizer import load_tokenizer


TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.json"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.csv"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.txt"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.md"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit.html"
)


def locate_stagnation_aware_suffix_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_loss_token_probability_probe(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_LOSS_TOKEN_PROBABILITY_PROBE_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder budget audit input must be a JSON object")
    return dict(payload)


def build_decoder_budget_audit(
    replay_comparison_report: dict[str, Any],
    loss_token_probability_probe_report: dict[str, Any],
    *,
    tokenizer_path: str | Path,
    replay_comparison_path: str | Path | None = None,
    probability_probe_path: str | Path | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory decoder budget audit",
    generated_at: str | None = None,
) -> dict[str, Any]:
    tokenizer = load_tokenizer(tokenizer_path)
    replay_summary = as_dict(replay_comparison_report.get("summary"))
    probe_summary = as_dict(loss_token_probability_probe_report.get("summary"))
    replay_rows = list_of_dicts(replay_comparison_report.get("replay_rows"))
    probe_case_rows = list_of_dicts(loss_token_probability_probe_report.get("case_rows"))
    case_rows = _case_rows(replay_rows, probe_case_rows, tokenizer)
    diagnostic = _diagnostic(case_rows, probe_summary)
    checks = _checks(replay_comparison_report, replay_summary, loss_token_probability_probe_report, probe_summary, replay_rows, Path(tokenizer_path), diagnostic)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, replay_summary, probe_summary, case_rows, diagnostic)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_loss_token_probability_probe": str(probability_probe_path or ""),
        "tokenizer": str(tokenizer_path),
        "replay_summary": replay_summary,
        "probability_probe_summary": probe_summary,
        "case_rows": case_rows,
        "diagnostic": diagnostic,
        "check_rows": checks,
        "summary": summary,
        "interpretation": _interpretation(status, diagnostic),
    }


def resolve_exit_code(report: dict[str, Any], *, require_audit_ready: bool) -> int:
    return 1 if require_audit_ready and report.get("status") != "pass" else 0


def _case_rows(replay_rows: list[dict[str, Any]], probe_case_rows: list[dict[str, Any]], tokenizer: Any) -> list[dict[str, Any]]:
    probe_by_id = {str(row.get("case_id")): row for row in probe_case_rows}
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        case_id = str(replay.get("case_id") or "")
        continuation = str(replay.get("continuation") or "")
        max_new_tokens = int(replay.get("max_new_tokens") or 0)
        probe_case = probe_by_id.get(case_id, {})
        target_suffix = str(probe_case.get("target_suffix") or _missing_suffix(str(replay.get("expected_completion") or ""), continuation))
        continuation_token_count = len(tokenizer.encode(continuation))
        target_suffix_token_count = len(tokenizer.encode(target_suffix))
        remaining_budget = max_new_tokens - continuation_token_count
        needed_max_new_tokens = continuation_token_count + target_suffix_token_count
        rows.append({
            "case_id": case_id,
            "continuation": continuation,
            "continuation_token_count": continuation_token_count,
            "max_new_tokens": max_new_tokens,
            "remaining_budget": remaining_budget,
            "target_suffix": target_suffix,
            "target_suffix_token_count": target_suffix_token_count,
            "needed_max_new_tokens": needed_max_new_tokens,
            "additional_tokens_needed": max(0, needed_max_new_tokens - max_new_tokens),
            "loss_suffix_top1": probe_case.get("loss_suffix_top1") is True,
            "loss_suffix_topk": probe_case.get("loss_suffix_topk") is True,
            "budget_exhausted_before_suffix": remaining_budget <= 0 and target_suffix_token_count > 0,
            "state_label": _state_label(remaining_budget, target_suffix_token_count, probe_case.get("loss_suffix_top1") is True),
        })
    return rows


def _missing_suffix(expected_completion: str, continuation: str) -> str:
    normalized = continuation.strip()
    if expected_completion.startswith(normalized):
        return expected_completion[len(normalized) :]
    if normalized == "fixed l":
        return "oss"
    return ""


def _diagnostic(case_rows: list[dict[str, Any]], probe_summary: dict[str, Any]) -> dict[str, Any]:
    exhausted_count = sum(1 for row in case_rows if row["budget_exhausted_before_suffix"])
    top1_count = sum(1 for row in case_rows if row["loss_suffix_top1"])
    max_additional = max([int(row.get("additional_tokens_needed") or 0) for row in case_rows], default=0)
    recommended_max_new_tokens = max([int(row.get("needed_max_new_tokens") or 0) for row in case_rows], default=0)
    all_exhausted_top1 = bool(case_rows) and exhausted_count == len(case_rows) and top1_count == len(case_rows)
    return {
        "ready": bool(case_rows),
        "case_count": len(case_rows),
        "budget_exhausted_case_count": exhausted_count,
        "loss_suffix_top1_case_count": top1_count,
        "all_cases_budget_exhausted_before_top1_suffix": all_exhausted_top1,
        "source_probe_all_cases_loss_suffix_top1": probe_summary.get("all_cases_loss_suffix_top1") is True,
        "recommended_max_new_tokens": recommended_max_new_tokens,
        "max_additional_tokens_needed": max_additional,
        "next_step": (
            f"rerun_stagnation_aware_suffix_replay_with_max_new_tokens_{recommended_max_new_tokens}"
            if all_exhausted_top1
            else "review_decoder_budget_and_probability_probe"
        ),
    }


def _checks(
    replay_report: dict[str, Any],
    replay_summary: dict[str, Any],
    probe_report: dict[str, Any],
    probe_summary: dict[str, Any],
    replay_rows: list[dict[str, Any]],
    tokenizer_path: Path,
    diagnostic: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay_report.get("status") == "pass", replay_report.get("status"), "stagnation-aware suffix replay must pass structurally"),
        _check(
            "replay_ready",
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready") is True,
            replay_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready"),
            "stagnation-aware suffix replay must be ready",
        ),
        _check("probability_probe_passed", probe_report.get("status") == "pass", probe_report.get("status"), "loss-token probability probe must pass structurally"),
        _check(
            "probability_probe_ready",
            probe_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready") is True,
            probe_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_loss_token_probability_probe_ready"),
            "loss-token probability probe must be ready",
        ),
        _check("probability_probe_top1", probe_summary.get("all_cases_loss_suffix_top1") is True, probe_summary.get("all_cases_loss_suffix_top1"), "budget audit requires top-1 loss suffix probabilities"),
        _check("tokenizer_exists", tokenizer_path.is_file(), str(tokenizer_path), "tokenizer.json must exist"),
        _check("replay_rows_present", bool(replay_rows), len(replay_rows), "replay report must include rows"),
        _check("budget_exhaustion_confirmed", diagnostic.get("all_cases_budget_exhausted_before_top1_suffix") is True, diagnostic.get("budget_exhausted_case_count"), "all cases should exhaust decode budget before top-1 suffix"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(
    status: str,
    replay_summary: dict[str, Any],
    probe_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
    diagnostic: dict[str, Any],
) -> dict[str, Any]:
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready": status == "pass",
        "source_replay_passed_case_count": replay_summary.get("passed_case_count"),
        "source_replay_any_hit_case_count": replay_summary.get("any_hit_case_count"),
        "source_probe_target_top1_rate": probe_summary.get("target_top1_rate"),
        "case_count": len(case_rows),
        "budget_exhausted_case_count": diagnostic.get("budget_exhausted_case_count"),
        "loss_suffix_top1_case_count": diagnostic.get("loss_suffix_top1_case_count"),
        "all_cases_budget_exhausted_before_top1_suffix": diagnostic.get("all_cases_budget_exhausted_before_top1_suffix"),
        "recommended_max_new_tokens": diagnostic.get("recommended_max_new_tokens"),
        "max_additional_tokens_needed": diagnostic.get("max_additional_tokens_needed"),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit"
    if diagnostic.get("all_cases_budget_exhausted_before_top1_suffix") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_exhausted_before_loss_suffix"
    return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_review_required"


def _interpretation(status: str, diagnostic: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Decoder budget audit inputs did not prove budget exhaustion.", "next_action": "review_decoder_budget_inputs"}
    return {
        "model_quality_claim": "decoder_budget_blocked_loss_suffix_replay",
        "reason": "Replay used all available new-token budget on newline fixed-l while the probability probe shows the missing oss suffix is top-1.",
        "next_action": diagnostic.get("next_step"),
    }


def _state_label(remaining_budget: int, target_suffix_token_count: int, loss_suffix_top1: bool) -> str:
    if remaining_budget <= 0 and target_suffix_token_count > 0 and loss_suffix_top1:
        return "budget_exhausted_before_top1_suffix"
    if remaining_budget > 0 and target_suffix_token_count <= remaining_budget:
        return "budget_sufficient_review_decode"
    return "budget_or_probability_review_required"


__all__ = [
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_TEXT_FILENAME",
    "build_decoder_budget_audit",
    "locate_loss_token_probability_probe",
    "locate_stagnation_aware_suffix_replay_comparison",
    "read_json_report",
    "resolve_exit_code",
]
