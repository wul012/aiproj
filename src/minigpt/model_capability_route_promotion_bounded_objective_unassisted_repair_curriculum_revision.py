from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.html"


def locate_unassisted_repair_zero_hit_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_ZERO_HIT_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair curriculum revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision(
    zero_hit_diagnostic: dict[str, Any],
    *,
    zero_hit_diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair curriculum revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    diagnostic_summary = as_dict(zero_hit_diagnostic.get("summary"))
    diagnostic = as_dict(zero_hit_diagnostic.get("diagnostic"))
    root_causes = list_of_dicts(zero_hit_diagnostic.get("root_causes"))
    case_diagnostics = list_of_dicts(zero_hit_diagnostic.get("case_diagnostics"))
    revision_items = _revision_items(root_causes, case_diagnostics)
    acceptance_gates = _acceptance_gates()
    checks = _checks(zero_hit_diagnostic, diagnostic_summary, diagnostic, root_causes, case_diagnostics, revision_items)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    revision = _revision(status, revision_items, acceptance_gates)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_zero_hit_diagnostic": str(zero_hit_diagnostic_path or ""),
        "diagnostic_summary": diagnostic_summary,
        "diagnostic": diagnostic,
        "root_causes": root_causes,
        "case_diagnostics": case_diagnostics,
        "revision_items": revision_items if status == "pass" else [],
        "acceptance_gates": acceptance_gates if status == "pass" else [],
        "check_rows": checks,
        "curriculum_revision": revision,
        "summary": _summary(status, checks, revision),
        "interpretation": _interpretation(status, revision),
    }


def resolve_exit_code(report: dict[str, Any], *, require_revision_ready: bool) -> int:
    return 1 if require_revision_ready and report.get("status") != "pass" else 0


def _revision_items(root_causes: list[dict[str, Any]], case_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cause_ids = {str(row.get("cause_id") or "") for row in root_causes}
    items = [
        _item(
            "output_position_anchor_examples",
            "high",
            "Add examples where the answer appears immediately after the final answer marker, with no explanatory tokens before fixed loss.",
            "seed_revision",
        ),
        _item(
            "neutral_prompt_exact_completion_repetition",
            "high",
            "Repeat neutral prompts with the exact two-token completion so target terms are learned without appearing in the prompt.",
            "seed_revision",
        ),
        _item(
            "fragment_contrast_examples",
            "medium",
            "Add positive correction surfaces for observed fragments such as los, while keeping the training target as fixed loss.",
            "seed_revision",
        ),
        _item(
            "short_decoding_profile_probe",
            "medium",
            "After training, replay with short deterministic decoding before trying larger sampling changes.",
            "replay_revision",
        ),
        _item(
            "unchanged_contract_holdout",
            "high",
            "Keep the v836 objective contract unchanged so the revised seed cannot move the goalposts.",
            "holdout",
        ),
    ]
    if "direct_prompts_present_but_generation_unanchored" in cause_ids:
        items.append(_item("prompt_surface_balance", "medium", "Balance contract prompt surfaces and neutral prompt surfaces so one prompt form does not dominate.", "seed_revision"))
    if any(row.get("near_miss_terms") for row in case_diagnostics):
        items.append(_item("near_miss_fragment_tracking", "medium", "Track los/wixed-style fragments in the next replay comparison as diagnostic-only evidence.", "diagnostic"))
    return items


def _item(item_id: str, priority: str, action: str, stage: str) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "priority": priority,
        "stage": stage,
        "action": action,
        "decoder_anchor_allowed": False,
        "promotion_claim_allowed": False,
    }


def _acceptance_gates() -> list[dict[str, Any]]:
    return [
        _gate("seed_revision_ready", "revised seed must pass and keep decoder_anchor_example_count=0"),
        _gate("training_artifacts_ready", "revised training run must produce checkpoint, tokenizer, metrics, manifest, sample, and prepared corpus"),
        _gate("unassisted_replay_improves", "next replay must improve any_hit_case_count or pass_rate before further promotion review"),
        _gate("unchanged_contract_preserved", "v836 objective contract cases must remain unchanged"),
    ]


def _gate(gate_id: str, detail: str) -> dict[str, Any]:
    return {"gate_id": gate_id, "required": True, "detail": detail}


def _checks(
    diagnostic_report: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    diagnostic: dict[str, Any],
    root_causes: list[dict[str, Any]],
    case_diagnostics: list[dict[str, Any]],
    revision_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("diagnostic_passed", diagnostic_report.get("status") == "pass", diagnostic_report.get("status"), "zero-hit diagnostic must pass"),
        _check("diagnostic_ready", diagnostic_summary.get("bounded_objective_unassisted_repair_zero_hit_diagnostic_ready") is True, diagnostic_summary.get("bounded_objective_unassisted_repair_zero_hit_diagnostic_ready"), "unassisted zero-hit diagnostic must be ready"),
        _check("zero_hit_evidence_present", int(diagnostic_summary.get("zero_hit_case_count") or 0) > 0, diagnostic_summary.get("zero_hit_case_count"), "curriculum revision needs zero-hit evidence"),
        _check("root_causes_present", bool(root_causes), len(root_causes), "curriculum revision needs root causes"),
        _check("case_diagnostics_present", bool(case_diagnostics), len(case_diagnostics), "curriculum revision needs case diagnostics"),
        _check("diagnostic_routes_curriculum", diagnostic.get("proposed_next_artifact") == "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision", diagnostic.get("proposed_next_artifact"), "diagnostic must route to curriculum revision"),
        _check("revision_items_present", len(revision_items) >= 5, len(revision_items), "curriculum revision should include seed, replay, and holdout items"),
        _check("no_decoder_anchor_items", not any(row.get("decoder_anchor_allowed") for row in revision_items), len(revision_items), "curriculum revision must stay unassisted"),
    ]


def _revision(status: str, revision_items: list[dict[str, Any]], acceptance_gates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ready": status == "pass",
        "revision_item_count": len(revision_items) if status == "pass" else 0,
        "acceptance_gate_count": len(acceptance_gates) if status == "pass" else 0,
        "decoder_anchor_allowed": False,
        "promotion_claim_allowed": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision" if status == "pass" else "",
        "next_step": "build_bounded_objective_unassisted_repair_seed_revision" if status == "pass" else "repair_bounded_objective_unassisted_repair_curriculum_revision_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], revision: dict[str, Any]) -> dict[str, Any]:
    return {
        "bounded_objective_unassisted_repair_curriculum_revision_ready": status == "pass" and revision.get("ready") is True,
        "revision_item_count": revision.get("revision_item_count"),
        "acceptance_gate_count": revision.get("acceptance_gate_count"),
        "decoder_anchor_allowed": False,
        "promotion_claim_allowed": False,
        "proposed_next_artifact": revision.get("proposed_next_artifact"),
        "next_step": revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_ready"
    return "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision"


def _interpretation(status: str, revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Curriculum revision inputs are incomplete.", "next_action": "repair curriculum revision inputs"}
    return {
        "model_quality_claim": "curriculum_revision_only",
        "reason": "The zero-hit branch now has a revised data curriculum, but no new seed or checkpoint has been produced yet.",
        "next_action": revision.get("next_step"),
    }


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_CURRICULUM_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision",
    "locate_unassisted_repair_zero_hit_diagnostic",
    "read_json_report",
    "resolve_exit_code",
]
