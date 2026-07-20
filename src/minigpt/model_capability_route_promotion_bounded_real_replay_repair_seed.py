from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_repair_plan import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_seed_ready as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSONL_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.jsonl"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_CORPUS_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed_corpus.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_repair_seed.html"


def locate_route_promotion_bounded_real_replay_repair_plan(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_PLAN_JSON_FILENAME
    return source


def locate_route_promotion_bounded_real_replay(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("route promotion bounded real replay repair seed input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_repair_seed(
    repair_plan_report: dict[str, Any],
    real_replay_report: dict[str, Any],
    *,
    repair_plan_path: str | Path | None = None,
    real_replay_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay repair seed",
    generated_at: str | None = None,
) -> dict[str, Any]:
    plan_summary = as_dict(repair_plan_report.get("summary"))
    replay_rows = {str(row.get("case_id")): row for row in list_of_dicts(real_replay_report.get("replay_rows"))}
    repair_tasks = list_of_dicts(repair_plan_report.get("repair_tasks"))
    seed_examples = _seed_examples(repair_tasks, replay_rows)
    checks = _checks(repair_plan_report, real_replay_report, plan_summary, repair_tasks, seed_examples)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    seed = _seed(status, seed_examples, plan_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, seed),
        "failed_count": len(issues),
        "issues": issues,
        "source_repair_plan": str(repair_plan_path or ""),
        "source_real_replay": str(real_replay_path or ""),
        "seed_examples": seed_examples,
        "check_rows": checks,
        "repair_seed": seed,
        "summary": _summary(status, checks, seed),
        "interpretation": _interpretation(status, seed),
    }


def _seed_examples(repair_tasks: list[dict[str, Any]], replay_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for task in repair_tasks:
        case_id = str(task.get("case_id") or "")
        source_row = as_dict(replay_rows.get(case_id))
        prompt = str(source_row.get("prompt") or f"Repair case {case_id}: output both required terms.\nAnswer:")
        missed_terms = [str(term) for term in task.get("missed_terms", [])]
        examples.append(_example(task, prompt, "direct_case_answer", "fixed loss", missed_terms))
        examples.append(_example(task, f"{prompt}\nSelf-check: include both required terms exactly once.", "self_check_answer", "fixed loss", missed_terms))
    return examples


def _example(task: dict[str, Any], prompt: str, example_type: str, completion: str, missed_terms: list[str]) -> dict[str, Any]:
    text = f"{prompt}{completion}"
    return {
        "example_id": f"{task.get('task_id')}-{example_type}",
        "case_id": task.get("case_id"),
        "task_id": task.get("task_id"),
        "example_type": example_type,
        "prompt": prompt,
        "completion": completion,
        "text": text,
        "repair_type": task.get("repair_type"),
        "missed_terms": missed_terms,
        "required_terms": ["fixed", "loss"],
    }


def _checks(
    repair_plan_report: dict[str, Any],
    real_replay_report: dict[str, Any],
    plan_summary: dict[str, Any],
    repair_tasks: list[dict[str, Any]],
    seed_examples: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    task_ids = {row.get("task_id") for row in repair_tasks}
    seeded_task_ids = {row.get("task_id") for row in seed_examples}
    return [
        _check("repair_plan_passed", repair_plan_report.get("status") == "pass", repair_plan_report.get("status"), "repair plan must pass"),
        _check("repair_plan_ready", plan_summary.get("bounded_real_replay_repair_plan_ready") is True, plan_summary.get("bounded_real_replay_repair_plan_ready"), "repair plan must be ready"),
        _check("real_replay_passed", real_replay_report.get("status") == "pass", real_replay_report.get("status"), "real replay source must pass execution checks"),
        _check("repair_tasks_present", bool(repair_tasks), len(repair_tasks), "seed must have repair tasks"),
        _check("seed_examples_present", bool(seed_examples), len(seed_examples), "seed must generate examples"),
        _check("two_examples_per_task", len(seed_examples) == len(repair_tasks) * 2, {"examples": len(seed_examples), "tasks": len(repair_tasks)}, "seed should create two examples per repair task"),
        _check("all_tasks_seeded", task_ids == seeded_task_ids, {"tasks": sorted(str(item) for item in task_ids), "seeded": sorted(str(item) for item in seeded_task_ids)}, "every repair task must have seed examples"),
    ]


def _seed(status: str, examples: list[dict[str, Any]], plan_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "example_count": len(examples),
        "case_count": len({row.get("case_id") for row in examples}),
        "source_pass_rate": plan_summary.get("source_pass_rate"),
        "target_pass_rate": plan_summary.get("target_pass_rate"),
        "required_terms": ["fixed", "loss"],
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_repair_training_run",
        "next_step": "run_bounded_real_replay_repair_training" if status == "pass" else "repair_bounded_real_replay_seed",
    }


def _summary(status: str, checks: list[dict[str, Any]], seed: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_real_replay_repair_seed_ready": status == "pass" and seed.get("ready") is True,
        "example_count": seed.get("example_count"),
        "case_count": seed.get("case_count"),
        "source_pass_rate": seed.get("source_pass_rate"),
        "target_pass_rate": seed.get("target_pass_rate"),
        "proposed_next_artifact": seed.get("proposed_next_artifact"),
        "next_step": seed.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, seed: dict[str, Any]) -> str:
    if status == "pass" and seed.get("ready") is True:
        return "model_capability_route_promotion_bounded_real_replay_repair_seed_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_repair_seed"


def _interpretation(status: str, seed: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Repair seed inputs are not ready.", "next_action": "repair seed sources"}
    return {
        "model_quality_claim": "repair_seed_only",
        "reason": "The seed converts failed bounded replay cases into training text; it does not prove improvement until retrained and replayed.",
        "next_action": seed.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_CORPUS_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_JSONL_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_REPAIR_SEED_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_repair_seed",
    "locate_route_promotion_bounded_real_replay",
    "locate_route_promotion_bounded_real_replay_repair_plan",
    "read_json_report",
    "resolve_exit_code",
]
