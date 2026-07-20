from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.unassisted_holdout_repair_plan_v1148 import EXPLAIN_DIR_NAME
from minigpt.unassisted_holdout_repair_training_run_v1150 import TRAINING_HANDOFF_NAME
from minigpt.report_check_common import check_entry as _check


UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM = "unassisted_holdout_repair_replay_comparison_v1151"
GENERATION_ROWS_NAME = "unassisted_holdout_repair_replay_generation_rows_v1151.json"
GeneratorRunner = Callable[[dict[str, Any], Path, Path, str, int], dict[str, Any]]


def default_v1150_training_handoff_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1150"
        / EXPLAIN_DIR_NAME
        / "unassisted-holdout-repair-training-run-v1150"
        / TRAINING_HANDOFF_NAME
    )


def locate_v1150_training_handoff(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / TRAINING_HANDOFF_NAME
    return source


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def read_json_rows(path: str | Path, *, description: str = "JSON rows") -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise ValueError(f"{description} must be a JSON list")
    return [dict(row) for row in payload if isinstance(row, dict)]


def build_unassisted_holdout_repair_replay_comparison_v1151(
    training_handoff: dict[str, Any],
    *,
    holdout_prompts: list[dict[str, Any]] | None = None,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    handoff_path: str | Path | None = None,
    generator_runner: GeneratorRunner | None = None,
    precomputed_generations: list[dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else _resolve_handoff_artifact(training_handoff.get("checkpoint"), handoff_path, "checkpoint.pt")
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else _resolve_handoff_artifact(training_handoff.get("tokenizer"), handoff_path, "tokenizer.json")
    holdout_path = Path(str(training_handoff.get("holdout_prompts") or ""))
    prompts = holdout_prompts if holdout_prompts is not None else read_json_rows(holdout_path, description="v1149 holdout prompts")
    checks = _preflight_checks(training_handoff, prompts, checkpoint, tokenizer, holdout_path)
    preflight_issues = [row for row in checks if row["status"] != "pass"]
    generation_rows = [] if preflight_issues else _generation_rows(prompts, checkpoint, tokenizer, device, generator_runner, precomputed_generations)
    if not preflight_issues:
        checks.append(
            _check(
                "generation_count_matches_holdout",
                len(generation_rows) == len(prompts),
                {"generations": len(generation_rows), "prompts": len(prompts)},
                "each v1149 holdout prompt must produce one generation row",
            )
        )
    issues = [row for row in checks if row["status"] != "pass"]
    comparison = _comparison(generation_rows)
    status = "pass" if not issues else "fail"
    decision = _decision(status, comparison)
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted holdout repair replay comparison v1151",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "failed_count": len(issues),
        "issues": issues,
        "source_training_handoff": str(handoff_path or ""),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "source_holdout_prompts": str(holdout_path),
        "rows": generation_rows,
        "check_rows": checks,
        "comparison": comparison,
        "summary": _summary(status, checks, comparison),
        "interpretation": _interpretation(status, comparison),
        "csv_fieldnames": [
            "case_id",
            "prompt",
            "continuation",
            "expected_terms",
            "fixed_hit",
            "loss_hit",
            "full_pair_hit",
            "status",
        ],
    }


def write_unassisted_holdout_repair_replay_comparison_v1151_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    outputs = write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM,
        row_title="Replay Generations",
    )
    rows_path = Path(out_dir) / GENERATION_ROWS_NAME
    write_json_payload(list_of_dicts(report.get("rows")), rows_path)
    outputs["generation_rows"] = str(rows_path)
    return outputs


def resolve_exit_code(report: dict[str, Any], *, require_comparison_ready: bool = False, require_full_pair: bool = False) -> int:
    if require_comparison_ready and report.get("status") != "pass":
        return 1
    summary = as_dict(report.get("summary"))
    if require_full_pair and summary.get("all_full_pair_hit") is not True:
        return 1
    return 0


def _preflight_checks(
    training_handoff: dict[str, Any],
    prompts: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    holdout_path: Path,
) -> list[dict[str, Any]]:
    return [
        _check("training_handoff_passed", training_handoff.get("status") == "pass", training_handoff.get("status"), "v1150 training handoff must pass"),
        _check("handoff_next_step_matches_replay", training_handoff.get("next_step") == "run_unassisted_holdout_repair_replay_comparison", training_handoff.get("next_step"), "v1150 handoff must point to replay comparison"),
        _check("checkpoint_exists", checkpoint.is_file(), str(checkpoint), "v1150 checkpoint.pt must exist"),
        _check("tokenizer_exists", tokenizer.is_file(), str(tokenizer), "v1150 tokenizer.json must exist"),
        _check("holdout_prompts_exist", holdout_path.is_file() or bool(prompts), str(holdout_path), "v1149 holdout prompts must be available"),
        _check("holdout_prompt_count", len(prompts) >= 4, len(prompts), "replay should cover the target-free v1149 holdout prompts"),
        _check("holdout_prompts_target_free", _target_free(prompts), _target_prompt_hits(prompts), "holdout prompts must not contain expected terms before generation"),
        _check("promotion_boundary_kept", training_handoff.get("promotion_ready") is False, training_handoff.get("promotion_ready"), "v1151 replay is evidence, not automatic promotion"),
    ]


def _resolve_handoff_artifact(raw_path: Any, handoff_path: str | Path | None, filename: str) -> Path:
    direct = Path(str(raw_path or ""))
    if direct.is_file() or handoff_path is None:
        return direct
    archived = Path(handoff_path).parent / "run" / filename
    return archived if archived.is_file() else direct


def _generation_rows(
    prompts: list[dict[str, Any]],
    checkpoint: Path,
    tokenizer: Path,
    device: str,
    runner: GeneratorRunner | None,
    precomputed: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if precomputed is not None:
        return [_scored_generation(row, index) for index, row in enumerate(precomputed, start=1)]
    return [_scored_generation((runner or _generate_case)(row, checkpoint, tokenizer, device, index), index) for index, row in enumerate(prompts, start=1)]


def _generate_case(row: dict[str, Any], checkpoint: Path, tokenizer: Path, device: str, index: int) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(row.get("prompt") or ""),
        max_new_tokens=int(row.get("max_new_tokens") or 8),
        temperature=float(row.get("temperature") if row.get("temperature") is not None else 0.2),
        top_k=int(row.get("top_k")) if row.get("top_k") is not None else None,
        seed=int(row.get("seed") or (115100 + index)),
    )
    response = MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()
    response["case_id"] = row.get("case_id") or f"unassisted-holdout-{index:02d}"
    response["expected_terms"] = row.get("expected_terms") or ["fixed", "loss"]
    return response


def _scored_generation(row: dict[str, Any], index: int) -> dict[str, Any]:
    expected_terms = [str(term).lower() for term in row.get("expected_terms", ["fixed", "loss"])]
    continuation = str(row.get("continuation") or "")
    continuation_lower = continuation.lower()
    fixed_hit = "fixed" in continuation_lower
    loss_hit = "loss" in continuation_lower
    term_hits = {term: term in continuation_lower for term in expected_terms}
    full_pair_hit = all(term_hits.values()) if expected_terms else False
    any_hit = any(term_hits.values())
    return {
        "case_id": str(row.get("case_id") or f"unassisted-holdout-{index:02d}"),
        "prompt": str(row.get("prompt") or ""),
        "generated": str(row.get("generated") or ""),
        "continuation": continuation,
        "expected_terms": expected_terms,
        "term_hits": term_hits,
        "fixed_hit": fixed_hit,
        "loss_hit": loss_hit,
        "full_pair_hit": full_pair_hit,
        "status": "pass" if full_pair_hit else "partial" if any_hit else "fail",
    }


def _comparison(rows: list[dict[str, Any]]) -> dict[str, Any]:
    case_count = len(rows)
    fixed_count = sum(1 for row in rows if row.get("fixed_hit"))
    loss_count = sum(1 for row in rows if row.get("loss_hit"))
    full_pair_count = sum(1 for row in rows if row.get("full_pair_hit"))
    any_hit_count = sum(1 for row in rows if row.get("fixed_hit") or row.get("loss_hit"))
    all_full_pair = case_count > 0 and full_pair_count == case_count
    return {
        "case_count": case_count,
        "fixed_hit_case_count": fixed_count,
        "loss_hit_case_count": loss_count,
        "full_pair_case_count": full_pair_count,
        "any_hit_case_count": any_hit_count,
        "full_pair_rate": round(full_pair_count / case_count, 4) if case_count else 0.0,
        "all_full_pair_hit": all_full_pair,
        "partial_signal_visible": any_hit_count > 0 and not all_full_pair,
        "promotion_ready": False,
        "model_quality_claim": _model_quality_claim(all_full_pair, any_hit_count),
        "next_step": _next_step(all_full_pair, any_hit_count),
    }


def _summary(status: str, checks: list[dict[str, Any]], comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "unassisted_holdout_repair_replay_ready": status == "pass",
        "case_count": comparison.get("case_count"),
        "fixed_hit_case_count": comparison.get("fixed_hit_case_count"),
        "loss_hit_case_count": comparison.get("loss_hit_case_count"),
        "full_pair_case_count": comparison.get("full_pair_case_count"),
        "any_hit_case_count": comparison.get("any_hit_case_count"),
        "full_pair_rate": comparison.get("full_pair_rate"),
        "all_full_pair_hit": comparison.get("all_full_pair_hit"),
        "partial_signal_visible": comparison.get("partial_signal_visible"),
        "model_quality_claim": comparison.get("model_quality_claim") if status == "pass" else "not_claimed",
        "promotion_ready": False,
        "next_step": comparison.get("next_step") if status == "pass" else "repair_unassisted_holdout_repair_replay_inputs",
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, comparison: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_unassisted_holdout_repair_replay_comparison"
    if comparison.get("all_full_pair_hit") is True:
        return "unassisted_holdout_repair_replay_full_pair_recovered_candidate"
    if int(comparison.get("any_hit_case_count") or 0) > 0:
        return "unassisted_holdout_repair_replay_partial_signal"
    return "unassisted_holdout_repair_replay_zero_hit"


def _interpretation(status: str, comparison: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Replay inputs are incomplete.", "next_action": "repair replay inputs"}
    return {
        "model_quality_claim": comparison.get("model_quality_claim"),
        "reason": "This replay used the unchanged v1149 target-free holdout prompts against the v1150 checkpoint.",
        "next_action": comparison.get("next_step"),
    }


def _model_quality_claim(all_full_pair: bool, any_hit_count: int) -> str:
    if all_full_pair:
        return "bounded_holdout_replay_recovered_candidate"
    if any_hit_count > 0:
        return "bounded_holdout_replay_partial_signal"
    return "not_improved"


def _next_step(all_full_pair: bool, any_hit_count: int) -> str:
    if all_full_pair:
        return "repeat_unassisted_holdout_replay_across_seeds_before_promotion"
    if any_hit_count > 0:
        return "diagnose_unassisted_holdout_repair_partial_signal"
    return "diagnose_unassisted_holdout_repair_zero_hit"


def _target_free(prompts: list[dict[str, Any]]) -> bool:
    return not _target_prompt_hits(prompts)


def _target_prompt_hits(prompts: list[dict[str, Any]]) -> list[str]:
    hits = []
    for row in prompts:
        prompt = str(row.get("prompt") or "").lower()
        terms = [str(term).lower() for term in row.get("expected_terms", ["fixed", "loss"])]
        if any(term and term in prompt for term in terms):
            hits.append(str(row.get("case_id") or row.get("prompt") or "unknown"))
    return hits


__all__ = [
    "GENERATION_ROWS_NAME",
    "UNASSISTED_HOLDOUT_REPAIR_REPLAY_COMPARISON_V1151_STEM",
    "build_unassisted_holdout_repair_replay_comparison_v1151",
    "default_v1150_training_handoff_path",
    "locate_v1150_training_handoff",
    "read_json_report",
    "read_json_rows",
    "resolve_exit_code",
    "write_unassisted_holdout_repair_replay_comparison_v1151_outputs",
]
