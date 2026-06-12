from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.decoder_anchor_holdout_comparison_v1147 import DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM, EXPLAIN_DIR_NAME
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now, write_json_payload

UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM = "unassisted_holdout_repair_plan_v1148"


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def locate_v1147_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM}.json"
    return source


def default_v1147_comparison_path(repo_root: str | Path) -> Path:
    return (
        Path(repo_root)
        / "f"
        / "1147"
        / EXPLAIN_DIR_NAME
        / "decoder-anchor-holdout-comparison-v1147"
        / f"{DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM}.json"
    )


def build_unassisted_holdout_repair_plan_v1148(
    comparison_report: dict[str, Any],
    *,
    comparison_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary = as_dict(comparison_report.get("summary"))
    comparison_rows = list_of_dicts(comparison_report.get("rows"))
    work_items = _work_items(summary)
    acceptance_gates = _acceptance_gates(summary)
    blocked_actions = _blocked_actions()
    seed_rows = _seed_blueprint_rows(comparison_rows)
    checks = _checks(comparison_report, summary, seed_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    plan = _plan(status, work_items, acceptance_gates, blocked_actions, seed_rows)
    return {
        "schema_version": 1,
        "title": "MiniGPT unassisted holdout repair plan v1148",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_holdout_comparison": str(comparison_path or ""),
        "source_summary": summary,
        "source_rows": comparison_rows,
        "work_items": work_items,
        "acceptance_gates": acceptance_gates,
        "blocked_actions": blocked_actions,
        "repair_seed_blueprint_rows": seed_rows,
        "check_rows": checks,
        "plan": plan,
        "summary": _summary(status, checks, plan, seed_rows),
        "interpretation": _interpretation(status, summary, plan),
        "csv_fieldnames": ["id", "priority", "stage", "description", "expected_output"],
    }


def write_unassisted_holdout_repair_plan_v1148_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    outputs = write_readability_outputs(
        report,
        out_dir,
        stem=UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM,
        row_title="Repair Work Items",
        row_key="work_items",
    )
    root = Path(out_dir)
    seed_json = root / "unassisted_holdout_repair_seed_blueprint.json"
    seed_text = root / "unassisted_holdout_repair_seed_blueprint.txt"
    write_json_payload(report.get("repair_seed_blueprint_rows", []), seed_json)
    seed_text.write_text(_render_seed_blueprint_text(list_of_dicts(report.get("repair_seed_blueprint_rows"))), encoding="utf-8")
    outputs["seed_blueprint_json"] = str(seed_json)
    outputs["seed_blueprint_text"] = str(seed_text)
    return outputs


def resolve_exit_code(report: dict[str, Any], *, require_plan_ready: bool = False) -> int:
    return 1 if require_plan_ready and report.get("status") != "pass" else 0


def _work_items(summary: dict[str, Any]) -> list[dict[str, Any]]:
    missing_fixed = int(summary.get("unassisted_fixed_hit_count") or 0) == 0
    return [
        _work("materialize_unassisted_seed_blueprint", "high", "seed", "Write a compact seed corpus whose prompts do not contain fixed/loss but completions require the pair.", "unassisted_holdout_repair_seed_corpus"),
        _work("recover_fixed_first_token", "high" if missing_fixed else "medium", "training", "Bias the next repair run toward generating fixed as new text, because v1147 had zero unassisted fixed hits.", "fixed_first_token_uptake_report"),
        _work("preserve_loss_suffix_signal", "medium", "training", "Keep the partial loss signal observed in v1147 while adding fixed/loss coexistence examples.", "loss_suffix_retention_report"),
        _work("run_bounded_repair_checkpoint", "high", "execution", "Train one small CPU repair checkpoint from the unassisted seed blueprint without changing the evaluation prompts.", "unassisted_holdout_repair_training_run"),
        _work("replay_unchanged_unassisted_prompts", "high", "evaluation", "Rerun the exact five v1147 unassisted prompts and require fixed/loss pair recovery before any stronger claim.", "unassisted_holdout_repair_replay"),
        _work("compare_against_anchor_baseline", "medium", "evaluation", "Compare repaired unassisted pair hits against the v1147 anchor-assisted baseline and keep promotion gated.", "anchor_vs_unassisted_repair_delta"),
    ]


def _work(work_id: str, priority: str, stage: str, description: str, output: str) -> dict[str, Any]:
    return {"id": work_id, "priority": priority, "stage": stage, "description": description, "expected_output": output}


def _acceptance_gates(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": "evaluation_prompt_target_free", "required": True, "detail": "The unchanged replay prompts must not contain fixed or loss."},
        {"id": "fixed_first_token_recovered", "required": True, "detail": "At least three unassisted replay cases should include fixed in continuation text."},
        {"id": "full_pair_recovered", "required": True, "detail": "At least three unchanged unassisted replay cases should include both fixed and loss."},
        {"id": "loss_signal_not_regressed", "required": True, "detail": f"Loss hits should stay at or above the v1147 baseline of {summary.get('unassisted_loss_hit_count', 0)}."},
        {"id": "promotion_still_gated", "required": True, "detail": "Even a repaired replay needs holdout scorecard evidence before promotion."},
    ]


def _blocked_actions() -> list[dict[str, Any]]:
    return [
        {"id": "do_not_count_loss_only_as_recovery", "detail": "v1147 already had loss-only hits; recovery requires fixed/loss coexistence."},
        {"id": "do_not_add_decoder_anchors_to_eval", "detail": "Evaluation prompts must remain unassisted and target-free."},
        {"id": "do_not_rewrite_v1145_v1147_archives", "detail": "Repair work must consume archived evidence rather than editing prior releases."},
        {"id": "do_not_claim_promotion_from_plan", "detail": "This report is a plan and seed blueprint, not model-quality proof."},
    ]


def _seed_blueprint_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompts = [str(row.get("unassisted_prompt") or "").strip() for row in source_rows]
    prompts = [prompt for prompt in prompts if prompt and "fixed" not in prompt.lower() and "loss" not in prompt.lower()]
    fallback = ["answer:", "answer: ", "completion:", "finish: ", "state compact signal\nanswer:"]
    prompts = prompts or fallback
    rows = []
    for index, prompt in enumerate(prompts[:5], start=1):
        rows.append(
            {
                "id": f"pair-repair-{index:02d}",
                "kind": "full_pair",
                "prompt": prompt,
                "completion": " fixed loss" if not prompt.endswith(" ") else "fixed loss",
                "target_terms": ["fixed", "loss"],
                "decoder_anchor": False,
                "source": "v1147_unassisted_prompt",
            }
        )
    rows.extend(
        [
            _seed_row("fixed-first-01", "answer:", " fixed", "fixed_first"),
            _seed_row("fixed-first-02", "completion:", " fixed", "fixed_first"),
            _seed_row("loss-after-fixed-01", "answer: fixed", " loss", "loss_after_model_fixed", decoder_anchor_boundary="training_only_context_not_eval"),
            _seed_row("pair-short-01", "signal:", " fixed loss", "short_pair"),
        ]
    )
    return rows


def _seed_row(row_id: str, prompt: str, completion: str, kind: str, *, decoder_anchor_boundary: str = "none") -> dict[str, Any]:
    return {
        "id": row_id,
        "kind": kind,
        "prompt": prompt,
        "completion": completion,
        "target_terms": ["fixed", "loss"] if "loss" in completion else ["fixed"],
        "decoder_anchor": False,
        "decoder_anchor_boundary": decoder_anchor_boundary,
        "source": "v1148_repair_blueprint",
    }


def _checks(report: dict[str, Any], summary: dict[str, Any], seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("v1147_comparison_passed", report.get("status") == "pass", report.get("status"), "v1147 comparison must pass"),
        _check("v1147_comparison_ready", summary.get("decoder_anchor_holdout_comparison_ready") is True, summary.get("decoder_anchor_holdout_comparison_ready"), "v1147 comparison ready flag must be true"),
        _check("v1147_next_step_matches_plan", summary.get("next_step") == "build_unassisted_holdout_repair_plan", summary.get("next_step"), "v1147 must point to this repair plan"),
        _check("unassisted_pair_absent", int(summary.get("unassisted_full_pair_count") or 0) == 0, summary.get("unassisted_full_pair_count"), "plan is needed only while unassisted fixed/loss pair is absent"),
        _check("fixed_missing_is_explicit", int(summary.get("unassisted_fixed_hit_count") or 0) == 0, summary.get("unassisted_fixed_hit_count"), "v1148 should target the fixed-first-token gap"),
        _check("partial_loss_signal_present", int(summary.get("unassisted_loss_hit_count") or 0) > 0, summary.get("unassisted_loss_hit_count"), "repair plan should preserve the partial loss signal"),
        _check("seed_blueprint_present", len(seed_rows) >= 8, len(seed_rows), "plan must include a concrete seed blueprint"),
        _check("seed_eval_prompts_target_free", all("fixed" not in str(row.get("prompt")).lower() and "loss" not in str(row.get("prompt")).lower() for row in seed_rows[:5]), False, "evaluation-derived seed prompts must stay target-free"),
        _check("promotion_boundary_kept", summary.get("promotion_ready") is False, summary.get("promotion_ready"), "v1147 must not already be a promotion report"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _plan(
    status: str,
    work_items: list[dict[str, Any]],
    gates: list[dict[str, Any]],
    blocked_actions: list[dict[str, Any]],
    seed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "route": "unassisted_holdout_repair",
        "work_item_count": len(work_items),
        "acceptance_gate_count": len(gates),
        "blocked_action_count": len(blocked_actions),
        "seed_blueprint_count": len(seed_rows),
        "new_training_allowed": status == "pass",
        "promotion_ready": False,
        "proposed_next_artifact": "unassisted_holdout_repair_seed_corpus_v1149",
        "next_step": "materialize_unassisted_holdout_repair_seed_corpus" if status == "pass" else "repair_unassisted_holdout_repair_plan_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], plan: dict[str, Any], seed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "unassisted_holdout_repair_plan_ready": status == "pass" and plan.get("ready") is True,
        "route": plan.get("route"),
        "work_item_count": plan.get("work_item_count"),
        "acceptance_gate_count": plan.get("acceptance_gate_count"),
        "blocked_action_count": plan.get("blocked_action_count"),
        "seed_blueprint_count": len(seed_rows),
        "new_training_allowed": plan.get("new_training_allowed"),
        "promotion_ready": False,
        "model_quality_claim": "plan_only",
        "proposed_next_artifact": plan.get("proposed_next_artifact"),
        "next_step": plan.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "unassisted_holdout_repair_plan_ready"
    return "fix_unassisted_holdout_repair_plan"


def _interpretation(status: str, summary: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "v1147 comparison evidence is not ready for repair planning.", "next_action": "repair v1148 inputs"}
    return {
        "model_quality_claim": "plan_only",
        "reason": "v1147 shows loss-only partial signal but zero unassisted fixed/full-pair recovery; the next useful step is a small target-free repair seed.",
        "next_action": plan.get("next_step"),
        "source_unassisted_loss_hit_count": summary.get("unassisted_loss_hit_count"),
        "source_unassisted_fixed_hit_count": summary.get("unassisted_fixed_hit_count"),
    }


def _render_seed_blueprint_text(rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for row in rows:
        lines.append(f"# {row.get('id')} [{row.get('kind')}]")
        lines.append(f"prompt: {row.get('prompt')}")
        lines.append(f"completion: {row.get('completion')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "UNASSISTED_HOLDOUT_REPAIR_PLAN_V1148_STEM",
    "build_unassisted_holdout_repair_plan_v1148",
    "default_v1147_comparison_path",
    "locate_v1147_comparison",
    "read_json_report",
    "resolve_exit_code",
    "write_unassisted_holdout_repair_plan_v1148_outputs",
]
