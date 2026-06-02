from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_coexistence_corpus import (
    PAIR_COEXISTENCE_CORPUS_MODES,
    build_pair_coexistence_refresh_corpus,
    source_prompts,
)
from minigpt.model_capability_required_term_pair_minimal_prompt_objective_readiness import (
    PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, utc_now


PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_JSON_FILENAME = "model_capability_required_term_pair_minimal_prompt_corpus_contract.json"
PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_CSV_FILENAME = "model_capability_required_term_pair_minimal_prompt_corpus_contract.csv"
PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_TEXT_FILENAME = "model_capability_required_term_pair_minimal_prompt_corpus_contract.txt"
PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_MARKDOWN_FILENAME = "model_capability_required_term_pair_minimal_prompt_corpus_contract.md"
PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_HTML_FILENAME = "model_capability_required_term_pair_minimal_prompt_corpus_contract.html"

CONTEXTUAL_ANCHOR_PATTERNS = (
    "fixed=fixed|loss=loss",
    "loss=loss|fixed=fixed",
    "fixed=fixed loss=loss",
    "loss=loss fixed=fixed",
    "other_term",
    "{other_term}",
)


def locate_minimal_prompt_corpus_contract_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_MINIMAL_PROMPT_OBJECTIVE_READINESS_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("minimal prompt corpus contract input must be a JSON object")
    return dict(payload)


def build_minimal_prompt_corpus_contract(
    readiness: dict[str, Any],
    *,
    repeat: int = 2,
    bridge_repeat: int = 1,
    source_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    objective = as_dict(readiness.get("objective"))
    corpus_mode = str(objective.get("recommended_corpus_mode") or "")
    corpus_registered = corpus_mode in PAIR_COEXISTENCE_CORPUS_MODES
    corpus_text = build_pair_coexistence_refresh_corpus(repeat=repeat, bridge_repeat=bridge_repeat, corpus_mode=corpus_mode) if corpus_registered else ""
    fixed_prompt, loss_prompt = source_prompts(corpus_mode) if corpus_mode in PAIR_COEXISTENCE_CORPUS_MODES else ("", "")
    checks = _check_rows(readiness, objective, corpus_mode, corpus_text, fixed_prompt, loss_prompt)
    failed_checks = [row for row in checks if row.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    corpus = _corpus_summary(corpus_mode, corpus_text, fixed_prompt, loss_prompt, repeat, bridge_repeat)
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair minimal prompt corpus contract",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(failed_checks),
        "issues": [{"id": row["id"], "detail": row["detail"]} for row in failed_checks],
        "source_readiness_path": str(source_path or ""),
        "source_readiness": {
            "status": readiness.get("status"),
            "decision": readiness.get("decision"),
            "summary": as_dict(readiness.get("summary")),
        },
        "check_rows": checks,
        "corpus": corpus,
        "sample_lines": corpus_text.splitlines()[:20],
        "summary": _summary(status, checks, corpus),
        "interpretation": _interpretation(status, corpus),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _check_rows(
    readiness: dict[str, Any],
    objective: dict[str, Any],
    corpus_mode: str,
    corpus_text: str,
    fixed_prompt: str,
    loss_prompt: str,
) -> list[dict[str, Any]]:
    rows = [
        _check("readiness_passed", readiness.get("status") == "pass", readiness.get("status"), "readiness report must pass"),
        _check("objective_ready", objective.get("ready") is True, objective.get("ready"), "minimal prompt objective must be ready"),
        _check("corpus_mode_registered", corpus_mode in PAIR_COEXISTENCE_CORPUS_MODES, corpus_mode, "recommended corpus mode must be registered"),
        _check("source_prompts_are_minimal", (fixed_prompt, loss_prompt) == ("fixed=", "loss="), [fixed_prompt, loss_prompt], "source prompts must be fixed= and loss="),
        _check("fixed_target_present", "fixed=fixed" in corpus_text, "fixed=fixed" in corpus_text, "corpus must contain fixed=fixed direct row"),
        _check("loss_target_present", "loss=loss" in corpus_text, "loss=loss" in corpus_text, "corpus must contain loss=loss direct row"),
        _check("fixed_prefix_present", "fixed=fix" in corpus_text, "fixed=fix" in corpus_text, "corpus must contain fixed prefix spans"),
        _check("loss_prefix_present", "loss=los" in corpus_text, "loss=los" in corpus_text, "corpus must contain loss prefix spans"),
        _check("no_contextual_anchor_patterns", not _anchor_hits(corpus_text), _anchor_hits(corpus_text), "corpus contract must avoid answer-bearing paired prompt anchors"),
        _check("no_pair_id", "pair=01" not in corpus_text, "pair=01" in corpus_text, "minimal prompt corpus must not reintroduce numeric pair ids"),
    ]
    return rows


def _check(check_id: str, passed: bool, actual: Any, detail: str) -> dict[str, Any]:
    return {"id": check_id, "status": "pass" if passed else "fail", "actual": actual, "detail": detail}


def _anchor_hits(corpus_text: str) -> list[str]:
    return [pattern for pattern in CONTEXTUAL_ANCHOR_PATTERNS if pattern in corpus_text]


def _corpus_summary(
    corpus_mode: str,
    corpus_text: str,
    fixed_prompt: str,
    loss_prompt: str,
    repeat: int,
    bridge_repeat: int,
) -> dict[str, Any]:
    return {
        "corpus_mode": corpus_mode,
        "repeat": repeat,
        "bridge_repeat": bridge_repeat,
        "source_prompts": [fixed_prompt, loss_prompt],
        "char_count": len(corpus_text),
        "line_count": len(corpus_text.splitlines()),
        "fixed_direct_count": corpus_text.count("fixed=fixed"),
        "loss_direct_count": corpus_text.count("loss=loss"),
        "anchor_hits": _anchor_hits(corpus_text),
        "contains_pair_id": "pair=01" in corpus_text,
    }


def _summary(status: str, checks: list[dict[str, Any]], corpus: dict[str, Any]) -> dict[str, Any]:
    return {
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("status") == "pass"),
        "failed_check_count": sum(1 for row in checks if row.get("status") != "pass"),
        "contract_ready": status == "pass",
        "corpus_mode": corpus.get("corpus_mode", ""),
        "source_prompts": corpus.get("source_prompts", []),
        "line_count": corpus.get("line_count", 0),
        "anchor_hit_count": len(corpus.get("anchor_hits", [])),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "minimal_prompt_equals_surface_corpus_contract_ready"
    return "fix_minimal_prompt_equals_surface_corpus_contract"


def _interpretation(status: str, corpus: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The minimal-prompt corpus contract is not safe to train.",
            "next_action": "repair corpus registration or remove contextual anchor patterns",
        }
    return {
        "model_quality_claim": "corpus_contract_only",
        "reason": "The corpus exposes fixed= and loss= direct targets without the contextual answer-bearing surface used by the previous branch.",
        "next_action": f"run a real tiny checkpoint with corpus_mode={corpus.get('corpus_mode')}",
    }


__all__ = [
    "PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_CSV_FILENAME",
    "PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_HTML_FILENAME",
    "PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_JSON_FILENAME",
    "PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_MARKDOWN_FILENAME",
    "PAIR_MINIMAL_PROMPT_CORPUS_CONTRACT_TEXT_FILENAME",
    "build_minimal_prompt_corpus_contract",
    "locate_minimal_prompt_corpus_contract_source",
    "read_json_report",
    "resolve_exit_code",
]
