from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.eval_suite import PromptCase
from minigpt.model_capability_route_promotion_consumer_plan import MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_CSV_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_TEXT_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_HTML_FILENAME = "model_capability_route_promotion_bounded_benchmark_suite.html"


def locate_route_promotion_consumer_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_CONSUMER_PLAN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded benchmark suite input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_benchmark_suite(
    consumer_plan: dict[str, Any],
    *,
    consumer_plan_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded benchmark suite",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(consumer_plan.get("summary"))
    plan = as_dict(consumer_plan.get("consumer_plan"))
    checks = _checks(consumer_plan, summary, plan)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    suite = _suite(status, plan)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_consumer_plan": str(consumer_plan_path or ""),
        "source_plan_summary": summary,
        "check_rows": checks,
        "benchmark_suite": suite,
        "summary": _summary(status, checks, suite),
        "interpretation": _interpretation(status, suite),
    }


def resolve_exit_code(report: dict[str, Any], *, require_ready_suite: bool) -> int:
    return 1 if require_ready_suite and report.get("status") != "pass" else 0


def _checks(consumer_plan: dict[str, Any], summary: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _check("consumer_plan_passed", consumer_plan.get("status") == "pass", consumer_plan.get("status"), "consumer plan must pass"),
        _check(
            "consumer_plan_ready",
            consumer_plan.get("decision") == "model_capability_route_promotion_consumer_plan_ready",
            consumer_plan.get("decision"),
            "consumer plan decision must be ready",
        ),
        _check("route_objective_level_contrast", summary.get("route_id") == "objective_level_contrast", summary.get("route_id"), "suite supports objective_level_contrast route"),
        _check("bounded_scope", summary.get("allowed_scope") == "bounded_model_capability_governance_only", summary.get("allowed_scope"), "suite must stay bounded"),
        _check("next_artifact_matches", summary.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_benchmark_suite", summary.get("proposed_next_artifact"), "consumer plan must request this suite"),
        _check("plan_steps_present", int(summary.get("plan_step_count") or 0) >= 5, summary.get("plan_step_count"), "consumer plan should include enough execution steps"),
        _check("non_goals_present", len(plan.get("non_goals", [])) >= 3, len(plan.get("non_goals", [])), "consumer plan must carry non-goals"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _suite(status: str, plan: dict[str, Any]) -> dict[str, Any]:
    ready = status == "pass"
    cases = _cases() if ready else []
    return {
        "ready": ready,
        "suite_name": "route-promotion-objective-level-contrast-bounded-suite",
        "suite_version": "v803",
        "route_id": plan.get("route_id"),
        "consumer_name": plan.get("consumer_name"),
        "allowed_scope": plan.get("allowed_scope") if ready else "none",
        "boundary": plan.get("boundary") if ready else "",
        "model_quality_claim": plan.get("model_quality_claim") if ready else "not_claimed",
        "cases": cases,
        "scoring_contract": {
            "expected_terms": ["fixed", "loss"],
            "case_pass_condition": "generated_continuation_contains_both_expected_terms",
            "suite_pass_condition": "all_cases_pass_without_scope_or_boundary_widening",
            "minimum_case_count": 5,
        },
        "guardrails": [
            "do not reuse heldout pair prompt surfaces as training data",
            "do not treat constrained decoding as model-quality proof",
            "do not claim production model release readiness",
        ],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_benchmark_suite_review",
    }


def _cases() -> list[dict[str, Any]]:
    prompts = [
        ("objective-answer-direct", "任务：只输出两个英文关键词，表示本轮目标答案。\n答案：", "direct objective answer"),
        ("objective-answer-role", "目标：给出 paired required terms 的两个角色词。\n输出：", "role-labeled objective answer"),
        ("objective-answer-contrast", "对比任务：不要解释，只返回目标 pair tokens。\n结果：", "contrast objective answer"),
        ("objective-answer-jsonish", "请用 JSON 风格写出 answer_terms，包含两个英文词。\nanswer_terms:", "structured objective answer"),
        ("objective-answer-check", "自检：本题需要同时出现 fixed 与 loss。最终答案：", "self-check objective answer"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (name, prompt, expected_behavior) in enumerate(prompts, start=1):
        case = PromptCase(
            name=name,
            prompt=prompt,
            max_new_tokens=24,
            temperature=0.2,
            top_k=10,
            seed=900 + index,
            task_type="route-promotion-objective-level-contrast",
            difficulty="medium",
            expected_behavior=expected_behavior,
            tags=("route-promotion", "objective-level-contrast", "required-terms"),
        ).to_dict()
        rows.append({"case_id": name, "prompt_case": case, "expected_terms": ["fixed", "loss"], "required_term_count": 2})
    return rows


def _summary(status: str, checks: list[dict[str, Any]], suite: dict[str, Any]) -> dict[str, Any]:
    cases = list_of_dicts(suite.get("cases"))
    return {
        "bounded_benchmark_suite_ready": status == "pass" and suite.get("ready") is True,
        "suite_name": suite.get("suite_name"),
        "route_id": suite.get("route_id"),
        "consumer_name": suite.get("consumer_name"),
        "case_count": len(cases),
        "expected_terms": as_dict(suite.get("scoring_contract")).get("expected_terms"),
        "minimum_case_count": as_dict(suite.get("scoring_contract")).get("minimum_case_count"),
        "boundary": suite.get("boundary"),
        "model_quality_claim": suite.get("model_quality_claim"),
        "proposed_next_artifact": suite.get("proposed_next_artifact"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_benchmark_suite_ready"
    return "fix_model_capability_route_promotion_bounded_benchmark_suite"


def _interpretation(status: str, suite: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "The consumer plan cannot produce a bounded benchmark suite.", "next_action": "repair consumer plan"}
    return {
        "model_quality_claim": suite.get("model_quality_claim"),
        "reason": "The accepted route now has a bounded benchmark suite with explicit expected terms and guardrails.",
        "next_action": f"build {suite.get('proposed_next_artifact')}",
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_BENCHMARK_SUITE_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_benchmark_suite",
    "locate_route_promotion_consumer_plan",
    "read_json_report",
    "resolve_exit_code",
]
