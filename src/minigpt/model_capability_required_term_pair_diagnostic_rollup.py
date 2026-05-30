from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, utc_now


REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_JSON_FILENAME = "model_capability_required_term_pair_diagnostic_rollup.json"
REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_TEXT_FILENAME = "model_capability_required_term_pair_diagnostic_rollup.txt"
REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_MARKDOWN_FILENAME = "model_capability_required_term_pair_diagnostic_rollup.md"
REQUIRED_TERM_PAIR_DIAGNOSTIC_ROLLUP_HTML_FILENAME = "model_capability_required_term_pair_diagnostic_rollup.html"

REPORT_PATTERNS = {
    "forced_choice": "model_capability_required_term_pair_forced_choice_diagnostic.json",
    "generation_gap": "model_capability_required_term_pair_generation_gap.json",
    "decoding_gap": "model_capability_required_term_pair_decoding_gap_probe.json",
    "path_trace": "model_capability_required_term_pair_decoding_path_trace.json",
    "first_token_repair": "model_capability_required_term_pair_first_token_repair.json",
    "prefix_completion": "model_capability_required_term_pair_prefix_completion_sweep.json",
}


def collect_required_term_pair_diagnostic_reports(root: str | Path) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    base = Path(root)
    reports: dict[str, dict[str, Any]] = {}
    paths: dict[str, str] = {}
    for key, pattern in REPORT_PATTERNS.items():
        matches = sorted(base.rglob(pattern))
        if not matches:
            reports[key] = {}
            paths[key] = ""
            continue
        path = matches[-1]
        reports[key] = read_json_report(path)
        paths[key] = str(path)
    return reports, paths


def build_model_capability_required_term_pair_diagnostic_rollup(
    reports: dict[str, dict[str, Any]],
    *,
    out_dir: str | Path,
    source_paths: dict[str, str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    issues = _input_issues(reports)
    stage_rows = _stage_rows(reports, source_paths or {})
    summary = _summary(stage_rows, reports)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair diagnostic rollup",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "out_dir": str(out_dir),
        "stage_rows": stage_rows,
        "summary": summary,
        "next_experiment_plan": _next_experiment_plan(status, summary),
        "interpretation": {
            "model_quality_claim": "diagnostic_rollup_only",
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _input_issues(reports: dict[str, dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    for key in REPORT_PATTERNS:
        report = reports.get(key) or {}
        if not report:
            issues.append(f"missing {key} report")
        elif report.get("status") != "pass":
            issues.append(f"{key} report is not pass")
    return issues


def _stage_rows(reports: dict[str, dict[str, Any]], paths: dict[str, str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, label in [
        ("forced_choice", "internal forced-choice signal"),
        ("generation_gap", "internal/free-generation gap"),
        ("decoding_gap", "decoding profile partial expression"),
        ("path_trace", "first-token path trace"),
        ("first_token_repair", "constrained first-token repair"),
        ("prefix_completion", "prefix completion span check"),
    ]:
        report = reports.get(key) or {}
        summary = as_dict(report.get("summary"))
        rows.append(
            {
                "stage": key,
                "label": label,
                "status": report.get("status"),
                "decision": report.get("decision"),
                "source_path": paths.get(key, ""),
                "summary": summary,
            }
        )
    return rows


def _summary(stage_rows: list[dict[str, Any]], reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    forced = as_dict((reports.get("forced_choice") or {}).get("summary"))
    generation = as_dict((reports.get("generation_gap") or {}).get("summary"))
    decoding = as_dict((reports.get("decoding_gap") or {}).get("summary"))
    trace = as_dict((reports.get("path_trace") or {}).get("summary"))
    repair = as_dict((reports.get("first_token_repair") or {}).get("summary"))
    prefix = as_dict((reports.get("prefix_completion") or {}).get("summary"))
    return {
        "rollup_decision": _rollup_decision(generation, decoding, trace, repair, prefix),
        "stage_count": len(stage_rows),
        "passing_stage_count": sum(1 for row in stage_rows if row.get("status") == "pass"),
        "forced_choice_full_match_variant_count": forced.get("forced_choice_full_match_variant_count"),
        "forced_generation_gap_variant_count": generation.get("forced_generation_gap_variant_count"),
        "decoding_profile_full_hit_count": decoding.get("profile_full_hit_count"),
        "decoding_continuation_hit_count": decoding.get("continuation_hit_count"),
        "path_first_sample_match_count": trace.get("first_sample_match_count"),
        "path_late_hit_count": trace.get("late_hit_after_first_miss_count"),
        "first_token_repair_improved_prompt_count": repair.get("improved_prompt_count"),
        "first_token_repair_full_hit_count": repair.get("repaired_profile_full_hit_count"),
        "prefix_one_token_hit_probe_count": prefix.get("one_token_prefix_hit_probe_count"),
        "prefix_full_hit_probe_count": prefix.get("full_prefix_hit_probe_count"),
        "span_completion_gap_probe_count": prefix.get("span_completion_gap_probe_count"),
    }


def _rollup_decision(
    generation: dict[str, Any],
    decoding: dict[str, Any],
    trace: dict[str, Any],
    repair: dict[str, Any],
    prefix: dict[str, Any],
) -> str:
    if int(decoding.get("profile_full_hit_count") or 0) > 0:
        return "rollup_generation_profile_recovered"
    if int(prefix.get("span_completion_gap_probe_count") or 0) > 0:
        return "rollup_continue_with_span_objective"
    if int(repair.get("improved_prompt_count") or 0) > 0 or int(trace.get("late_hit_after_first_miss_count") or 0) > 0:
        return "rollup_continue_with_generation_side_probe"
    if int(generation.get("forced_generation_gap_variant_count") or 0) > 0:
        return "rollup_internal_signal_not_expressed"
    return "rollup_no_actionable_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_diagnostic_rollup"
    if summary.get("rollup_decision") == "rollup_continue_with_span_objective":
        return "required_term_pair_next_span_objective"
    return "required_term_pair_diagnostic_rollup_recorded"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "One or more required diagnostic source reports are missing or not pass."
    if summary.get("rollup_decision") == "rollup_continue_with_span_objective":
        return "Diagnostics show internal signal and partial generation, but prefix completion still has span gaps."
    return "Diagnostics are available as a read-only stage summary."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair missing diagnostic inputs before adding new experiments"
    if summary.get("rollup_decision") == "rollup_continue_with_span_objective":
        return "build the smallest continuation-span training objective for fixed/loss instead of more decoding tweaks"
    return "use the rollup as the checkpoint before selecting the next model-capability experiment"


def _next_experiment_plan(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "plan_id": "repair_diagnostic_inputs",
            "recommended": False,
            "reason": "rollup inputs are incomplete",
            "steps": ["restore missing v503-v508 diagnostic reports", "rerun the rollup before choosing a model experiment"],
            "minimum_success_criteria": ["all six diagnostic stages pass"],
            "excluded_options": [],
        }
    if summary.get("rollup_decision") != "rollup_continue_with_span_objective":
        return {
            "plan_id": "hold_model_experiment_selection",
            "recommended": False,
            "reason": "rollup does not yet isolate a span-completion target",
            "steps": ["review stage rows", "choose the next experiment from the strongest observed gap"],
            "minimum_success_criteria": ["next experiment has an explicit source metric and fixed prompt set"],
            "excluded_options": [],
        }
    return {
        "plan_id": "continuation_span_objective_fixed_loss",
        "recommended": True,
        "reason": "internal signal exists, decoding does not recover full profiles, and prefix completion still has span gaps",
        "target_terms": ["fixed", "loss"],
        "source_metrics": {
            "forced_choice_full_match_variant_count": summary.get("forced_choice_full_match_variant_count"),
            "decoding_profile_full_hit_count": summary.get("decoding_profile_full_hit_count"),
            "first_token_repair_improved_prompt_count": summary.get("first_token_repair_improved_prompt_count"),
            "prefix_one_token_hit_probe_count": summary.get("prefix_one_token_hit_probe_count"),
            "span_completion_gap_probe_count": summary.get("span_completion_gap_probe_count"),
        },
        "steps": [
            "build a tiny continuation-span corpus where prompts stop immediately before fixed/loss",
            "train a candidate from the current best symmetric-anchor checkpoint with a small repeatable budget",
            "evaluate free generation, first-token rank, and prefix-completion minimum-hit length with the same prompts",
            "accept only if full-profile hits improve without losing the existing loss one-token completion signal",
        ],
        "minimum_success_criteria": [
            "decoding_profile_full_hit_count increases above 0",
            "fixed minimum_hit_prefix_token_count drops below 4",
            "loss one-token prefix completion is retained",
            "all generated artifacts link back to the v509 source rollup",
        ],
        "excluded_options": [
            "adding more decoding profiles before changing the span objective",
            "claiming production model quality from forced-prefix evidence",
            "training on unrelated larger data without preserving the fixed/loss prompt set",
        ],
    }
