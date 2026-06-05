from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison import (
    build_stagnation_aware_suffix_replay_comparison,
)
from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_run import (
    TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_contract import (
    BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator


TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.json"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.csv"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.txt"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.md"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison.html"
)


def locate_objective_contract(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_CONTRACT_JSON_FILENAME
    return source


def locate_stagnation_aware_suffix_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_STAGNATION_AWARE_SUFFIX_TRAINING_RUN_JSON_FILENAME
    return source


def locate_decoder_budget_audit(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_DECODER_BUDGET_AUDIT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder-budget replay comparison input must be a JSON object")
    return dict(payload)


def build_decoder_budget_replay_comparison(
    objective_contract_report: dict[str, Any],
    stagnation_aware_suffix_training_run_report: dict[str, Any],
    decoder_budget_audit_report: dict[str, Any],
    *,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    objective_contract_path: str | Path | None = None,
    stagnation_aware_suffix_training_run_path: str | Path | None = None,
    decoder_budget_audit_path: str | Path | None = None,
    generator_runner: Any | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory decoder-budget replay comparison",
    generated_at: str | None = None,
) -> dict[str, Any]:
    budget_summary = as_dict(decoder_budget_audit_report.get("summary"))
    max_new_tokens = int(budget_summary.get("recommended_max_new_tokens") or 11)
    runner = generator_runner or _budget_runner(max_new_tokens)
    report = build_stagnation_aware_suffix_replay_comparison(
        objective_contract_report,
        stagnation_aware_suffix_training_run_report,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        objective_contract_path=objective_contract_path,
        stagnation_aware_suffix_training_run_path=stagnation_aware_suffix_training_run_path,
        generator_runner=runner,
        title=title,
        generated_at=generated_at,
    )
    return _adapt_replay_report(report, decoder_budget_audit_report, decoder_budget_audit_path, max_new_tokens)


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool, require_objective_pass: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_objective_pass and summary.get("objective_contract_recovered") is not True:
        return 1
    return 0


def _budget_runner(max_new_tokens: int) -> Any:
    def run(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
        request = GenerationRequest(
            prompt=str(case.get("prompt") or ""),
            max_new_tokens=max_new_tokens,
            temperature=0.2,
            top_k=20,
            seed=1839,
        )
        return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()

    return run


def _adapt_replay_report(
    report: dict[str, Any],
    decoder_budget_audit_report: dict[str, Any],
    source_path: str | Path | None,
    max_new_tokens: int,
) -> dict[str, Any]:
    adapted = dict(report)
    budget_summary = as_dict(decoder_budget_audit_report.get("summary"))
    budget_checks = _budget_checks(decoder_budget_audit_report, budget_summary)
    base_checks = [dict(row) for row in report.get("check_rows", []) if isinstance(row, dict)]
    check_rows = base_checks + budget_checks
    issues = [row for row in check_rows if row.get("status") != "pass"]
    adapted["source_decoder_budget_audit"] = str(source_path or "")
    adapted["decoder_budget_audit_summary"] = budget_summary
    adapted["decoder_budget_max_new_tokens"] = max_new_tokens
    adapted["check_rows"] = check_rows
    adapted["issues"] = issues
    adapted["failed_count"] = len(issues)
    adapted["status"] = "pass" if not issues else "fail"
    adapted["decision"] = _decision(adapted["status"], as_dict(report.get("summary")))
    adapted["comparison"] = _comparison(as_dict(report.get("comparison")), max_new_tokens)
    adapted["summary"] = _summary(adapted["status"], as_dict(report.get("summary")), adapted["comparison"], budget_summary, max_new_tokens)
    adapted["interpretation"] = _interpretation(adapted["status"], adapted["comparison"])
    return adapted


def _budget_checks(budget_report: dict[str, Any], budget_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("decoder_budget_audit_passed", budget_report.get("status") == "pass", budget_report.get("status"), "decoder budget audit must pass structurally"),
        _check(
            "decoder_budget_audit_ready",
            budget_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready") is True,
            budget_summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_audit_ready"),
            "decoder budget audit must be ready",
        ),
        _check("recommended_budget_present", int(budget_summary.get("recommended_max_new_tokens") or 0) > 0, budget_summary.get("recommended_max_new_tokens"), "decoder budget audit must recommend max_new_tokens"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _comparison(base: dict[str, Any], max_new_tokens: int) -> dict[str, Any]:
    comparison = dict(base)
    comparison["route"] = "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget"
    comparison["decoder_budget_max_new_tokens"] = max_new_tokens
    comparison["next_step"] = _next_step(comparison.get("objective_contract_recovered") is True)
    return comparison


def _summary(
    status: str,
    base: dict[str, Any],
    comparison: dict[str, Any],
    budget_summary: dict[str, Any],
    max_new_tokens: int,
) -> dict[str, Any]:
    summary = dict(base)
    summary["bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_ready"] = (
        status == "pass" and base.get("bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_ready") is True
    )
    summary["route"] = comparison.get("route")
    summary["decoder_budget_max_new_tokens"] = max_new_tokens
    summary["source_recommended_max_new_tokens"] = budget_summary.get("recommended_max_new_tokens")
    summary["next_step"] = comparison.get("next_step")
    return summary


def _decision(status: str, base_summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison"
    if base_summary.get("objective_contract_recovered") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_contract_recovered_holdout_required"
    if int(base_summary.get("any_hit_case_count") or 0) > 0:
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_partial_required_term_hit"
    return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_zero_hit"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Decoder-budget replay inputs failed.", "next_action": "repair_decoder_budget_replay_inputs"}
    if comparison.get("objective_contract_recovered") is True:
        return {
            "model_quality_claim": "objective_contract_recovered_only",
            "reason": "The same checkpoint recovers the bounded objective contract when replay uses the audited 11-token budget; unchanged holdout remains required before promotion.",
            "next_action": "run_unchanged_bounded_suite_holdout_replay",
        }
    return {
        "model_quality_claim": "partial_required_term_signal",
        "reason": "The audited decoder budget replay still did not recover every contract case.",
        "next_action": comparison.get("next_step"),
    }


def _next_step(recovered: bool) -> str:
    if recovered:
        return "run_unchanged_bounded_suite_holdout_replay"
    return "review_decoder_budget_replay_failure_before_more_training"


__all__ = [
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_TEXT_FILENAME",
    "build_decoder_budget_replay_comparison",
    "locate_decoder_budget_audit",
    "locate_objective_contract",
    "locate_stagnation_aware_suffix_training_run",
    "read_json_report",
    "resolve_exit_code",
]
