from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_repair_seed import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_strategy_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSONL_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.jsonl"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_CORPUS_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision_corpus.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_revision.html"


def locate_repair_strategy_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_STRATEGY_REVISION_JSON_FILENAME
    return source


def locate_repair_seed(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded real replay repair seed revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision(
    strategy_revision_report: dict[str, Any],
    repair_seed_report: dict[str, Any],
    *,
    strategy_revision_path: str | Path | None = None,
    repair_seed_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay repair seed revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    strategy_summary = as_dict(strategy_revision_report.get("summary"))
    seed_summary = as_dict(repair_seed_report.get("summary"))
    original_examples = list_of_dicts(repair_seed_report.get("seed_examples"))
    case_actions = list_of_dicts(strategy_revision_report.get("case_actions"))
    seed_examples = _seed_examples(original_examples, case_actions)
    checks = _checks(strategy_revision_report, repair_seed_report, strategy_summary, seed_summary, case_actions, seed_examples, original_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    revision = _revision(status, original_examples, seed_examples, case_actions, strategy_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, revision),
        "failed_count": len(issues),
        "issues": issues,
        "source_strategy_revision": str(strategy_revision_path or ""),
        "source_repair_seed": str(repair_seed_path or ""),
        "source_summaries": {"strategy_revision": strategy_summary, "repair_seed": seed_summary},
        "seed_examples": seed_examples,
        "case_actions": case_actions,
        "check_rows": checks,
        "repair_seed_revision": revision,
        "summary": _summary(status, checks, revision),
        "interpretation": _interpretation(status, revision),
    }


def resolve_exit_code(report: dict[str, Any], *, require_seed_revision_ready: bool) -> int:
    return 1 if require_seed_revision_ready and report.get("status") != "pass" else 0


def _seed_examples(original_examples: list[dict[str, Any]], case_actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = [_carry_forward_example(row) for row in original_examples]
    for action in case_actions:
        examples.extend(_case_action_examples(action))
    return examples


def _carry_forward_example(row: dict[str, Any]) -> dict[str, Any]:
    text = str(row.get("text") or f"{row.get('prompt', '')}{row.get('completion', '')}")
    return {
        "example_id": f"revision-carry-{row.get('example_id')}",
        "case_id": row.get("case_id"),
        "source_example_id": row.get("example_id"),
        "revision_type": "carry_forward_original_repair_seed",
        "prompt": row.get("prompt", ""),
        "completion": row.get("completion", ""),
        "text": text,
        "required_terms": row.get("required_terms", ["fixed", "loss"]),
        "guardrail": "retain_original_repair_signal",
    }


def _case_action_examples(action: dict[str, Any]) -> list[dict[str, Any]]:
    case_id = str(action.get("case_id") or "unknown-case")
    missed_terms = [str(item) for item in action.get("repair_missed_terms", [])]
    examples = []
    if action.get("severity") == "regression":
        examples.append(
            _example(
                case_id,
                "baseline_preservation",
                f"Baseline preservation for {case_id}: output the two route terms exactly.\nAnswer:",
                "fixed loss",
                "preserve_baseline_pass_before_accepting_repair_checkpoint",
            )
        )
    examples.append(
        _example(
            case_id,
            "missing_term_retention",
            f"Repair {case_id}: include missing terms {', '.join(missed_terms) or 'fixed, loss'} and answer directly.\nAnswer:",
            "fixed loss",
            "prove_failed_case_recovery_before_promotion",
        )
    )
    examples.append(
        _example(
            case_id,
            "contrastive_self_check",
            f"Self-check {case_id}: the continuation is valid only if it contains fixed and loss.\nAnswer:",
            "fixed loss",
            "require_replay_comparison_after_each_repair_training",
        )
    )
    return examples


def _example(case_id: str, revision_type: str, prompt: str, completion: str, guardrail: str) -> dict[str, Any]:
    return {
        "example_id": f"revision-{case_id}-{revision_type}",
        "case_id": case_id,
        "source_example_id": "",
        "revision_type": revision_type,
        "prompt": prompt,
        "completion": completion,
        "text": f"{prompt}{completion}",
        "required_terms": ["fixed", "loss"],
        "guardrail": guardrail,
    }


def _checks(
    strategy_revision: dict[str, Any],
    repair_seed: dict[str, Any],
    strategy_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    case_actions: list[dict[str, Any]],
    seed_examples: list[dict[str, Any]],
    original_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    regression_count = sum(1 for row in case_actions if row.get("severity") == "regression")
    preservation_count = sum(1 for row in seed_examples if row.get("revision_type") == "baseline_preservation")
    return [
        _check("strategy_revision_passed", strategy_revision.get("status") == "pass", strategy_revision.get("status"), "strategy revision must pass"),
        _check("strategy_revision_ready", strategy_summary.get("bounded_real_replay_repair_strategy_revision_ready") is True, strategy_summary.get("bounded_real_replay_repair_strategy_revision_ready"), "strategy revision must be ready"),
        _check("repair_seed_passed", repair_seed.get("status") == "pass", repair_seed.get("status"), "source repair seed must pass"),
        _check("repair_seed_ready", seed_summary.get("bounded_real_replay_repair_seed_ready") is True, seed_summary.get("bounded_real_replay_repair_seed_ready"), "source repair seed must be ready"),
        _check("case_actions_present", bool(case_actions), len(case_actions), "seed revision must inspect case actions"),
        _check("original_examples_carried", len(seed_examples) >= len(original_examples), {"original": len(original_examples), "revision": len(seed_examples)}, "seed revision must carry original examples forward"),
        _check("preservation_examples_for_regressions", preservation_count >= regression_count, {"preservation": preservation_count, "regressions": regression_count}, "each regression case should receive a baseline preservation example"),
        _check("seed_examples_have_text", all(str(row.get("text") or "").strip() for row in seed_examples), len(seed_examples), "every revised seed example must have training text"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _revision(
    status: str,
    original_examples: list[dict[str, Any]],
    seed_examples: list[dict[str, Any]],
    case_actions: list[dict[str, Any]],
    strategy_summary: dict[str, Any],
) -> dict[str, Any]:
    added_count = max(0, len(seed_examples) - len(original_examples))
    return {
        "ready": status == "pass",
        "original_example_count": len(original_examples),
        "added_example_count": added_count,
        "example_count": len(seed_examples),
        "case_count": len({row.get("case_id") for row in seed_examples if row.get("case_id")}),
        "baseline_preservation_example_count": sum(1 for row in seed_examples if row.get("revision_type") == "baseline_preservation"),
        "case_action_count": len(case_actions),
        "source_pass_rate_delta": strategy_summary.get("pass_rate_delta"),
        "required_guardrails": [
            "retain_original_repair_signal",
            "preserve_baseline_pass_before_accepting_repair_checkpoint",
            "require_replay_comparison_after_each_repair_training",
        ],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_repair_training_run_revision",
        "next_step": "train_bounded_real_replay_repair_seed_revision" if status == "pass" else "repair_bounded_real_replay_repair_seed_revision",
    }


def _summary(status: str, checks: list[dict[str, Any]], revision: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_repair_seed_revision_ready": status == "pass" and revision.get("ready") is True,
        "original_example_count": revision.get("original_example_count"),
        "added_example_count": revision.get("added_example_count"),
        "example_count": revision.get("example_count"),
        "case_count": revision.get("case_count"),
        "baseline_preservation_example_count": revision.get("baseline_preservation_example_count"),
        "case_action_count": revision.get("case_action_count"),
        "proposed_next_artifact": revision.get("proposed_next_artifact"),
        "next_step": revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, revision: dict[str, Any]) -> str:
    if status == "pass" and revision.get("ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_seed_revision_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_repair_seed_revision"


def _interpretation(status: str, revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Seed revision inputs are incomplete.", "next_action": "repair seed revision inputs"}
    return {
        "model_quality_claim": "revised_seed_only",
        "reason": "The revised seed adds baseline preservation and repair examples; improvement still requires training and replay comparison.",
        "next_action": revision.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_CORPUS_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_JSONL_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_repair_seed_revision",
    "locate_repair_seed",
    "locate_repair_strategy_revision",
    "read_json_report",
    "resolve_exit_code",
]
