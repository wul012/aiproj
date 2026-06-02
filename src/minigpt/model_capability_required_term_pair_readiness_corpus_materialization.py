from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_readiness_split_contract import (
    PAIR_READINESS_SPLIT_CONTRACT_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now, write_json_payload


PAIR_READINESS_CORPUS_MATERIALIZATION_JSON_FILENAME = "model_capability_required_term_pair_readiness_corpus_materialization.json"
PAIR_READINESS_CORPUS_MATERIALIZATION_CSV_FILENAME = "model_capability_required_term_pair_readiness_corpus_materialization.csv"
PAIR_READINESS_CORPUS_MATERIALIZATION_TEXT_FILENAME = "model_capability_required_term_pair_readiness_corpus_materialization.txt"
PAIR_READINESS_CORPUS_MATERIALIZATION_MARKDOWN_FILENAME = "model_capability_required_term_pair_readiness_corpus_materialization.md"
PAIR_READINESS_CORPUS_MATERIALIZATION_HTML_FILENAME = "model_capability_required_term_pair_readiness_corpus_materialization.html"
PAIR_READINESS_TRAINING_CORPUS_FILENAME = "pair_readiness_training_corpus.txt"
PAIR_READINESS_HELDOUT_EVAL_FIXTURE_FILENAME = "pair_readiness_heldout_eval_fixture.json"
PAIR_READINESS_READY_CONTRACT_DECISIONS = {
    "pair_readiness_split_contract_ready",
    "pair_readiness_loss_retention_contract_patch_ready",
    "pair_readiness_structured_template_contract_ready",
    "pair_readiness_fixed_recovery_contract_patch_ready",
    "pair_readiness_objective_structure_contract_ready",
    "pair_readiness_direct_prompt_bridge_contract_patch_ready",
    "pair_readiness_direct_completion_surface_contract_ready",
    "pair_readiness_pair_prompt_transfer_contract_patch_ready",
    "pair_readiness_fixed_preserving_transfer_contract_patch_ready",
    "pair_readiness_exact_surface_repair_contract_patch_ready",
    "pair_readiness_objective_level_contrast_contract_ready",
}
PAIR_READINESS_CONTRACT_JSON_FILENAMES = (
    PAIR_READINESS_SPLIT_CONTRACT_JSON_FILENAME,
    "model_capability_required_term_pair_readiness_loss_retention_contract_patch.json",
    "model_capability_required_term_pair_readiness_structured_template_contract.json",
    "model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.json",
    "model_capability_required_term_pair_readiness_objective_structure_contract.json",
    "model_capability_required_term_pair_readiness_direct_prompt_bridge_contract_patch.json",
    "model_capability_required_term_pair_readiness_direct_completion_surface_contract.json",
    "model_capability_required_term_pair_readiness_pair_prompt_transfer_contract_patch.json",
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_contract_patch.json",
    "model_capability_required_term_pair_readiness_exact_surface_repair_contract_patch.json",
    "model_capability_required_term_pair_readiness_objective_level_contrast_contract.json",
)


def locate_pair_readiness_corpus_materialization_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        for filename in PAIR_READINESS_CONTRACT_JSON_FILENAMES:
            candidate = source / filename
            if candidate.is_file():
                return candidate
        source = source / PAIR_READINESS_SPLIT_CONTRACT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair-readiness corpus materialization input must be a JSON object")
    return dict(payload)


def build_pair_readiness_corpus_materialization(
    contract_report: dict[str, Any],
    *,
    out_dir: str | Path,
    repeat: int,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    contract = as_dict(contract_report.get("contract"))
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    eval_probes = list_of_dicts(contract.get("evaluation_probes"))
    corpus_lines = _corpus_lines(training_rows, repeat)
    corpus_path = root / PAIR_READINESS_TRAINING_CORPUS_FILENAME
    fixture_path = root / PAIR_READINESS_HELDOUT_EVAL_FIXTURE_FILENAME
    checks = _checks(contract_report, contract, corpus_lines, repeat)
    failed = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed else "fail"
    fixture = _fixture(eval_probes, contract)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair-readiness corpus materialization",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed],
        "source_contract_path": str(source_path or ""),
        "source_contract": {
            "status": contract_report.get("status"),
            "decision": contract_report.get("decision"),
            "summary": as_dict(contract_report.get("summary")),
        },
        "settings": {"repeat": repeat},
        "materialized_paths": {
            "training_corpus": str(corpus_path),
            "heldout_eval_fixture": str(fixture_path),
        },
        "check_rows": checks,
        "training_corpus": {
            "line_count": len(corpus_lines),
            "char_count": len("\n".join(corpus_lines)),
            "preview": corpus_lines[:8],
        },
        "heldout_eval_fixture": fixture,
        "summary": _summary(corpus_lines, eval_probes, checks, status),
        "interpretation": _interpretation(status),
    }


def write_materialized_pair_readiness_inputs(report: dict[str, Any]) -> None:
    paths = as_dict(report.get("materialized_paths"))
    corpus_path = Path(str(paths.get("training_corpus")))
    fixture_path = Path(str(paths.get("heldout_eval_fixture")))
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_lines = _corpus_lines_from_report(report)
    corpus_path.write_text("\n".join(corpus_lines) + "\n", encoding="utf-8")
    write_json_payload(report.get("heldout_eval_fixture"), fixture_path)


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _corpus_lines(training_rows: list[str], repeat: int) -> list[str]:
    lines: list[str] = []
    for _ in range(max(0, repeat)):
        lines.extend(training_rows)
    return lines


def _corpus_lines_from_report(report: dict[str, Any]) -> list[str]:
    preview = [str(row) for row in as_dict(report.get("training_corpus")).get("preview", [])]
    repeat = int(as_dict(report.get("settings")).get("repeat") or 0)
    source = as_dict(report.get("heldout_eval_fixture")).get("training_rows")
    rows = [str(row) for row in source] if isinstance(source, list) else preview
    return _corpus_lines(rows, repeat)


def _fixture(eval_probes: list[dict[str, Any]], contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "pair_readiness_heldout_eval_fixture",
        "probes": eval_probes,
        "heldout_pair_probe": contract.get("heldout_pair_probe"),
        "promotion_requirement": contract.get("promotion_requirement"),
        "training_rows": contract.get("training_rows", []),
    }


def _checks(contract_report: dict[str, Any], contract: dict[str, Any], corpus_lines: list[str], repeat: int) -> list[dict[str, Any]]:
    heldout = str(contract.get("heldout_pair_probe") or "")
    training_rows = [str(row) for row in contract.get("training_rows", [])]
    return [
        _check("contract_passed", contract_report.get("status") == "pass", contract_report.get("status"), "source contract must pass"),
        _check(
            "contract_decision",
            contract_report.get("decision") in PAIR_READINESS_READY_CONTRACT_DECISIONS,
            contract_report.get("decision"),
            "materialization requires a ready pair-readiness contract",
        ),
        _check("repeat_positive", repeat > 0, repeat, "repeat must be positive"),
        _check("training_rows_present", len(training_rows) >= 8, len(training_rows), "training rows must be present"),
        _check("heldout_not_in_training_rows", heldout not in training_rows, heldout in training_rows, "heldout pair probe must not be a training row"),
        _check("heldout_not_in_corpus", heldout not in corpus_lines, heldout in corpus_lines, "heldout pair probe must not appear as a corpus line"),
    ]


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _summary(corpus_lines: list[str], eval_probes: list[dict[str, Any]], checks: list[dict[str, Any]], status: str) -> dict[str, Any]:
    return {
        "materialization_ready": status == "pass",
        "training_line_count": len(corpus_lines),
        "evaluation_probe_count": len(eval_probes),
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "pair_readiness_corpus_materialized"
    return "fix_pair_readiness_corpus_materialization"


def _interpretation(status: str) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The contract could not be materialized without leakage or missing rows.",
            "next_action": "repair materialization inputs before training",
        }
    return {
        "model_quality_claim": "data_artifact_only",
        "reason": "Training corpus and heldout eval fixture are materialized from a checked split contract.",
        "next_action": "train on the materialized corpus and replay heldout probes",
    }


__all__ = [
    "PAIR_READINESS_CORPUS_MATERIALIZATION_CSV_FILENAME",
    "PAIR_READINESS_CORPUS_MATERIALIZATION_HTML_FILENAME",
    "PAIR_READINESS_CORPUS_MATERIALIZATION_JSON_FILENAME",
    "PAIR_READINESS_CORPUS_MATERIALIZATION_MARKDOWN_FILENAME",
    "PAIR_READINESS_CORPUS_MATERIALIZATION_TEXT_FILENAME",
    "PAIR_READINESS_CONTRACT_JSON_FILENAMES",
    "PAIR_READINESS_HELDOUT_EVAL_FIXTURE_FILENAME",
    "PAIR_READINESS_READY_CONTRACT_DECISIONS",
    "PAIR_READINESS_TRAINING_CORPUS_FILENAME",
    "build_pair_readiness_corpus_materialization",
    "locate_pair_readiness_corpus_materialization_source",
    "read_json_report",
    "resolve_exit_code",
    "write_materialized_pair_readiness_inputs",
]
