from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison import (
    TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay import (
    build_model_capability_route_promotion_bounded_real_replay,
    locate_route_promotion_bounded_benchmark_dry_run,
    locate_route_promotion_bounded_benchmark_suite,
    locate_route_promotion_bounded_benchmark_suite_review,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.json"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_CSV_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.csv"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_TEXT_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.txt"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_MARKDOWN_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.md"
)
TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_HTML_FILENAME = (
    "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay.html"
)


def locate_decoder_budget_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / TARGET_ONLY_MEMORY_DECODER_BUDGET_REPLAY_COMPARISON_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder-budget holdout replay input must be a JSON object")
    return dict(payload)


def build_decoder_budget_holdout_replay(
    decoder_budget_replay_report: dict[str, Any],
    suite_review_report: dict[str, Any],
    benchmark_suite_report: dict[str, Any],
    dry_run_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    decoder_budget_replay_path: str | Path | None = None,
    suite_review_path: str | Path | None = None,
    benchmark_suite_path: str | Path | None = None,
    dry_run_path: str | Path | None = None,
    generator_runner: Any | None = None,
    title: str = "MiniGPT bounded objective loss signal bridge target-only memory decoder-budget holdout replay",
    generated_at: str | None = None,
) -> dict[str, Any]:
    base = build_model_capability_route_promotion_bounded_real_replay(
        suite_review_report,
        benchmark_suite_report,
        dry_run_report,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        suite_review_path=suite_review_path,
        benchmark_suite_path=benchmark_suite_path,
        dry_run_path=dry_run_path,
        generator_runner=generator_runner,
        title=title,
        generated_at=generated_at or utc_now(),
    )
    return _adapt_holdout_report(
        base,
        decoder_budget_replay_report,
        decoder_budget_replay_path=decoder_budget_replay_path,
        title=title,
    )


def resolve_exit_code(report: dict[str, Any], *, require_execution_pass: bool, require_holdout_pass: bool = False) -> int:
    if require_execution_pass and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_holdout_pass and summary.get("promotion_ready") is not True:
        return 1
    return 0


def _adapt_holdout_report(
    base: dict[str, Any],
    decoder_budget_replay_report: dict[str, Any],
    *,
    decoder_budget_replay_path: str | Path | None,
    title: str,
) -> dict[str, Any]:
    source_summary = as_dict(decoder_budget_replay_report.get("summary"))
    source_checks = _source_checks(decoder_budget_replay_report, source_summary)
    base_checks = [dict(row) for row in list_of_dicts(base.get("check_rows"))]
    check_rows = base_checks + source_checks
    issues = [row for row in check_rows if row.get("status") != "pass"]
    status = "pass" if not issues else "fail"
    replay_rows = list_of_dicts(base.get("replay_rows"))
    hit_summary = _hit_summary(replay_rows)
    summary = _summary(status, as_dict(base.get("summary")), source_summary, hit_summary, failed_check_count=len(issues))
    report = dict(base)
    report.update(
        {
            "title": title,
            "status": status,
            "decision": _decision(status, summary),
            "failed_count": len(issues),
            "issues": issues,
            "source_decoder_budget_replay": str(decoder_budget_replay_path or ""),
            "source_decoder_budget_replay_summary": source_summary,
            "check_rows": check_rows,
            "summary": summary,
            "interpretation": _interpretation(status, summary),
        }
    )
    return report


def _source_checks(source: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("decoder_budget_replay_passed", source.get("status") == "pass", source.get("status"), "decoder-budget replay must pass structurally"),
        _check(
            "decoder_budget_replay_ready",
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_ready") is True,
            summary.get("bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_replay_comparison_ready"),
            "decoder-budget replay comparison must be ready",
        ),
        _check(
            "source_objective_contract_recovered",
            summary.get("objective_contract_recovered") is True,
            summary.get("objective_contract_recovered"),
            "source replay must recover the original objective contract before holdout",
        ),
        _check(
            "source_next_step_requires_holdout",
            summary.get("next_step") == "run_unchanged_bounded_suite_holdout_replay",
            summary.get("next_step"),
            "source replay must explicitly require unchanged holdout replay",
        ),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _hit_summary(replay_rows: list[dict[str, Any]]) -> dict[str, int]:
    any_hit_count = sum(1 for row in replay_rows if row.get("hit_terms"))
    return {
        "any_hit_case_count": any_hit_count,
        "zero_hit_case_count": len(replay_rows) - any_hit_count,
    }


def _summary(
    status: str,
    base_summary: dict[str, Any],
    source_summary: dict[str, Any],
    hit_summary: dict[str, int],
    failed_check_count: int,
) -> dict[str, Any]:
    holdout_ready = status == "pass" and base_summary.get("model_route_quality_ready") is True
    promotion_ready = holdout_ready and source_summary.get("objective_contract_recovered") is True
    return {
        "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_ready": status == "pass",
        "source_objective_contract_recovered": source_summary.get("objective_contract_recovered") is True,
        "holdout_model_route_quality_ready": base_summary.get("model_route_quality_ready") is True if status == "pass" else False,
        "case_count": base_summary.get("case_count"),
        "executed_case_count": base_summary.get("executed_case_count"),
        "passed_case_count": base_summary.get("passed_case_count"),
        "failed_case_count": base_summary.get("failed_case_count"),
        "any_hit_case_count": hit_summary["any_hit_case_count"],
        "zero_hit_case_count": hit_summary["zero_hit_case_count"],
        "pass_rate": base_summary.get("pass_rate"),
        "promotion_ready": promotion_ready,
        "model_quality_claim": _model_quality_claim(status, promotion_ready),
        "next_step": _next_step(status, promotion_ready, hit_summary),
        "failed_check_count": failed_check_count,
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_inputs"
    if summary.get("promotion_ready") is True:
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_passed_review_required"
    if int(summary.get("any_hit_case_count") or 0) > 0:
        return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_partial_model_gap"
    return "bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_holdout_replay_zero_hit_model_gap"


def _model_quality_claim(status: str, promotion_ready: bool) -> str:
    if status != "pass":
        return "not_claimed"
    if promotion_ready:
        return "bounded_holdout_suite_passed_after_budget_recovery"
    return "objective_contract_recovered_holdout_failed"


def _next_step(status: str, promotion_ready: bool, hit_summary: dict[str, int]) -> str:
    if status != "pass":
        return "repair_decoder_budget_holdout_replay_inputs"
    if promotion_ready:
        return "review_holdout_replay_before_route_promotion"
    if hit_summary["any_hit_case_count"] > 0:
        return "diagnose_holdout_prompt_generalization_gap_before_more_training"
    return "inspect_checkpoint_or_suite_alignment_before_more_training"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "Holdout replay could not verify its inputs or execute the unchanged suite.",
            "next_action": summary.get("next_step"),
        }
    if summary.get("promotion_ready") is True:
        return {
            "model_quality_claim": summary.get("model_quality_claim"),
            "reason": "The decoder-budget recovery also passes the unchanged bounded holdout suite; route promotion still requires review.",
            "next_action": summary.get("next_step"),
        }
    return {
        "model_quality_claim": summary.get("model_quality_claim"),
        "reason": "The objective contract recovered under the audited decoder budget, but the unchanged bounded holdout suite still exposes a model gap.",
        "next_action": summary.get("next_step"),
    }


__all__ = [
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_CSV_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_HTML_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_JSON_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_MARKDOWN_FILENAME",
    "TARGET_ONLY_MEMORY_DECODER_BUDGET_HOLDOUT_REPLAY_TEXT_FILENAME",
    "build_decoder_budget_holdout_replay",
    "locate_decoder_budget_replay_comparison",
    "locate_route_promotion_bounded_benchmark_dry_run",
    "locate_route_promotion_bounded_benchmark_suite",
    "locate_route_promotion_bounded_benchmark_suite_review",
    "read_json_report",
    "resolve_exit_code",
]
