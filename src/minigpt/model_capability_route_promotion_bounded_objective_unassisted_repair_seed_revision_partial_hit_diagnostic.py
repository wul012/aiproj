from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_replay_comparison import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_training_run import (
    BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_diagnostic_ready as resolve_exit_code


BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.json"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.csv"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.txt"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.md"
BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME = "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic.html"


def locate_seed_revision_replay_comparison(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_REPLAY_COMPARISON_JSON_FILENAME
    return source


def locate_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_JSON_FILENAME
    return source


def locate_seed_revision_training_run(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_TRAINING_RUN_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("bounded objective unassisted repair seed revision partial-hit diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic(
    replay_comparison: dict[str, Any],
    seed_revision: dict[str, Any],
    training_run: dict[str, Any],
    *,
    corpus_path: str | Path,
    replay_comparison_path: str | Path | None = None,
    seed_revision_path: str | Path | None = None,
    training_run_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded objective unassisted repair seed revision partial-hit diagnostic",
    generated_at: str | None = None,
) -> dict[str, Any]:
    replay_summary = as_dict(replay_comparison.get("summary"))
    seed_summary = as_dict(seed_revision.get("summary"))
    training_summary = as_dict(training_run.get("summary"))
    replay_rows = list_of_dicts(replay_comparison.get("replay_rows"))
    corpus_text = Path(corpus_path).read_text(encoding="utf-8").lower()
    case_rows = [_case_diagnostic(row, corpus_text) for row in replay_rows]
    root_causes = _root_causes(case_rows, replay_summary, seed_summary, training_summary, corpus_text)
    checks = _checks(replay_comparison, replay_summary, seed_revision, seed_summary, training_run, training_summary, case_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    diagnostic = _diagnostic(status, case_rows, root_causes)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, diagnostic),
        "failed_count": len(issues),
        "issues": issues,
        "source_replay_comparison": str(replay_comparison_path or ""),
        "source_seed_revision": str(seed_revision_path or ""),
        "source_training_run": str(training_run_path or ""),
        "source_corpus": str(corpus_path),
        "replay_summary": replay_summary,
        "seed_revision_summary": seed_summary,
        "training_summary": training_summary,
        "case_diagnostics": case_rows,
        "root_causes": root_causes,
        "check_rows": checks,
        "diagnostic": diagnostic,
        "summary": _summary(status, case_rows, root_causes, diagnostic),
        "interpretation": _interpretation(status, diagnostic, root_causes),
    }


def _case_diagnostic(row: dict[str, Any], corpus_text: str) -> dict[str, Any]:
    required_terms = [str(term).lower() for term in row.get("required_terms") or []]
    hit_terms = [str(term).lower() for term in row.get("hit_terms") or []]
    missed_terms = [str(term).lower() for term in row.get("missed_terms") or []]
    continuation = str(row.get("continuation") or "")
    return {
        "case_id": str(row.get("case_id") or ""),
        "prompt": row.get("prompt"),
        "continuation": continuation,
        "required_terms": required_terms,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "case_pass": row.get("case_pass") is True,
        "any_hit": row.get("any_hit") is True,
        "partial_hit": bool(hit_terms) and bool(missed_terms),
        "zero_hit": not hit_terms,
        "missed_terms_present_in_corpus": [term for term in missed_terms if term in corpus_text],
        "continuation_preview": continuation[:80],
    }


def _root_causes(
    case_rows: list[dict[str, Any]],
    replay_summary: dict[str, Any],
    seed_summary: dict[str, Any],
    training_summary: dict[str, Any],
    corpus_text: str,
) -> list[dict[str, Any]]:
    causes: list[dict[str, Any]] = []
    missed_terms = sorted({term for row in case_rows for term in row["missed_terms"]})
    hit_terms = sorted({term for row in case_rows for term in row["hit_terms"]})
    partial_rows = [row for row in case_rows if row["partial_hit"]]
    zero_rows = [row for row in case_rows if row["zero_hit"]]
    if partial_rows:
        causes.append(_cause("first_term_only_uptake", "high", f"{len(partial_rows)} cases hit a required term but still missed another term.", [row["case_id"] for row in partial_rows]))
    loss_missing = "loss" in missed_terms and "fixed" in hit_terms
    if loss_missing:
        detail = "`fixed` appears in replay continuations, but `loss` remains missed even though it exists in the revised corpus."
        causes.append(_cause("loss_term_not_stabilized", "high", detail, [row["case_id"] for row in case_rows if "loss" in row["missed_terms"]]))
    if zero_rows:
        causes.append(_cause("prompt_surface_still_zero_hit", "medium", "At least one contract prompt surface still has no required-term hit.", [row["case_id"] for row in zero_rows]))
    if any(term in corpus_text for term in missed_terms):
        causes.append(_cause("corpus_contains_missed_terms", "medium", "The missed terms are present in the seed corpus, so this is an uptake/generation issue rather than missing raw data.", missed_terms))
    if int(replay_summary.get("passed_case_count") or 0) == 0:
        causes.append(_cause("no_case_passed_contract", "high", "No replay case satisfied all required terms, so promotion remains blocked.", []))
    if int(seed_summary.get("decoder_anchor_example_count") or 0) == 0 and training_summary.get("bounded_objective_unassisted_repair_seed_revision_training_ready") is True:
        causes.append(_cause("unassisted_path_confirmed", "low", "The checkpoint came from the no-anchor revised seed path; partial uptake is unassisted evidence.", []))
    return causes


def _checks(
    replay: dict[str, Any],
    replay_summary: dict[str, Any],
    seed: dict[str, Any],
    seed_summary: dict[str, Any],
    training: dict[str, Any],
    training_summary: dict[str, Any],
    case_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _check("replay_passed", replay.get("status") == "pass", replay.get("status"), "seed revision replay comparison must pass structurally"),
        _check("replay_ready", replay_summary.get("bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready") is True, replay_summary.get("bounded_objective_unassisted_repair_seed_revision_replay_comparison_ready"), "seed revision replay comparison must be ready"),
        _check("objective_not_recovered", replay_summary.get("objective_contract_recovered") is not True, replay_summary.get("objective_contract_recovered"), "diagnostic is only for unrecovered objective contracts"),
        _check("partial_hit_present", any(row["partial_hit"] for row in case_rows), sum(1 for row in case_rows if row["partial_hit"]), "at least one replay case must be a partial hit"),
        _check("seed_revision_ready", seed.get("status") == "pass" and seed_summary.get("bounded_objective_unassisted_repair_seed_revision_ready") is True, seed_summary.get("bounded_objective_unassisted_repair_seed_revision_ready"), "seed revision must be ready"),
        _check("training_ready", training.get("status") == "pass" and training_summary.get("bounded_objective_unassisted_repair_seed_revision_training_ready") is True, training_summary.get("bounded_objective_unassisted_repair_seed_revision_training_ready"), "seed revision training run must be ready"),
    ]


def _diagnostic(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    ready = status == "pass"
    return {
        "ready": ready,
        "route": "bounded_objective_unassisted_repair_seed_revision",
        "partial_hit_case_count": sum(1 for row in case_rows if row["partial_hit"]),
        "zero_hit_case_count": sum(1 for row in case_rows if row["zero_hit"]),
        "root_cause_count": len(root_causes),
        "decoder_anchor_used": False,
        "proposed_next_artifact": "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch" if ready else "",
        "next_step": "build_bounded_objective_unassisted_repair_seed_revision_curriculum_patch" if ready else "repair_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_inputs",
    }


def _summary(status: str, case_rows: list[dict[str, Any]], root_causes: list[dict[str, Any]], diagnostic: dict[str, Any]) -> dict[str, Any]:
    hit_terms = sorted({term for row in case_rows for term in row["hit_terms"]})
    missed_terms = sorted({term for row in case_rows for term in row["missed_terms"]})
    return {
        "bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready": status == "pass",
        "case_count": len(case_rows),
        "partial_hit_case_count": diagnostic.get("partial_hit_case_count"),
        "zero_hit_case_count": diagnostic.get("zero_hit_case_count"),
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "root_cause_count": len(root_causes),
        "decoder_anchor_used": False,
        "model_quality_claim": "partial_required_term_signal_diagnosed" if status == "pass" else "not_claimed",
        "proposed_next_artifact": diagnostic.get("proposed_next_artifact"),
        "next_step": diagnostic.get("next_step"),
    }


def _decision(status: str, diagnostic: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic"
    if int(diagnostic.get("partial_hit_case_count") or 0) > 0:
        return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic_ready"
    return "model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_no_partial_hit"


def _interpretation(status: str, diagnostic: dict[str, Any], root_causes: list[dict[str, Any]]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Partial-hit diagnostic inputs failed structural checks.", "next_action": diagnostic.get("next_step")}
    top = root_causes[0]["cause_id"] if root_causes else "partial_hit_without_root_cause"
    return {
        "model_quality_claim": "partial_required_term_signal_diagnosed",
        "reason": f"The revised no-anchor checkpoint partially learned the objective surface, but the dominant diagnostic is `{top}`.",
        "next_action": diagnostic.get("next_step"),
    }


def _cause(cause_id: str, severity: str, detail: str, evidence: list[Any]) -> dict[str, Any]:
    return {"cause_id": cause_id, "severity": severity, "detail": detail, "evidence": evidence}


__all__ = [
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_CSV_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_HTML_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_JSON_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_MARKDOWN_FILENAME",
    "BOUNDED_OBJECTIVE_UNASSISTED_REPAIR_SEED_REVISION_PARTIAL_HIT_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_partial_hit_diagnostic",
    "locate_seed_revision",
    "locate_seed_revision_replay_comparison",
    "locate_seed_revision_training_run",
    "read_json_report",
    "resolve_exit_code",
]
