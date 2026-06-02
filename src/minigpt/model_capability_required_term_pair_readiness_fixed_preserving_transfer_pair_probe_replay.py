from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_pair_generation_profile_replay import DEFAULT_PROFILE_IDS, GenerateFunc
from minigpt.model_capability_required_term_pair_readiness_direct_completion_pair_probe_replay import (
    PAIR_PROBE_PROMPT_SPECS,
    build_direct_completion_pair_probe_replay,
    read_json_report,
    resolve_exit_code as _replay_exit_code,
)
from minigpt.model_capability_required_term_pair_readiness_training_run import PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts


PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.json"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_CSV_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.csv"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_TEXT_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.txt"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.md"
)
PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_HTML_FILENAME = (
    "model_capability_required_term_pair_readiness_fixed_preserving_transfer_pair_probe_replay.html"
)


def locate_fixed_preserving_transfer_pair_probe_replay_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_READINESS_TRAINING_RUN_JSON_FILENAME
    return source


def build_fixed_preserving_transfer_pair_probe_replay(
    training_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    prompt_specs: tuple[dict[str, Any], ...] = PAIR_PROBE_PROMPT_SPECS,
    profiles: tuple[str, ...] = DEFAULT_PROFILE_IDS,
    device: str = "cpu",
    generated_at: str | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    source = Path(source_path).resolve() if source_path is not None else Path("selected-training-report.json").resolve()
    replay = build_direct_completion_pair_probe_replay(
        _synthetic_route_comparison(source),
        out_dir=out_dir,
        source_path=source,
        prompt_specs=prompt_specs,
        profiles=profiles,
        device=device,
        generated_at=generated_at,
        selected_training_report=training_report,
        generate_func=generate_func,
    )
    return _adapt_replay_report(replay, training_report, source)


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return _replay_exit_code(report, require_pass=require_pass)


def _synthetic_route_comparison(source: Path) -> dict[str, Any]:
    return {
        "status": "pass",
        "decision": "pair_readiness_direct_completion_route_candidate_found",
        "summary": {"selected_route": "direct-completion-surface"},
        "comparison_rows": [
            {
                "label": "direct-completion-surface",
                "path": str(source),
                "adapter_note": "synthetic row used only to reuse the existing pair-probe replay engine",
            }
        ],
    }


def _adapt_replay_report(replay: dict[str, Any], training_report: dict[str, Any], source: Path) -> dict[str, Any]:
    summary = as_dict(replay.get("summary"))
    adapted = dict(replay)
    adapted.update(
        {
            "title": "MiniGPT pair-readiness fixed-preserving transfer pair-probe replay",
            "decision": _decision(str(replay.get("status")), summary),
            "source_training_run": str(source),
            "source_replay_engine": "direct_completion_pair_probe_replay",
            "training_decision": training_report.get("decision"),
            "settings": _settings(replay),
            "interpretation": _interpretation(str(replay.get("status")), summary),
        }
    )
    return adapted


def _settings(replay: dict[str, Any]) -> dict[str, Any]:
    settings = as_dict(replay.get("settings"))
    return {
        **settings,
        "experiment_boundary": "replay the fixed-preserving transfer checkpoint on heldout pair prompt surfaces without retraining",
        "adapter_boundary": "reuses direct-completion pair-probe replay mechanics but reports fixed-preserving transfer route semantics",
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_readiness_fixed_preserving_transfer_pair_probe_replay"
    if summary.get("required_all_pair_full"):
        return "pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready"
    if summary.get("any_pair_full"):
        return "pair_readiness_fixed_preserving_transfer_pair_probe_replay_partial"
    return "pair_readiness_fixed_preserving_transfer_pair_probe_replay_not_ready"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The fixed-preserving transfer checkpoint could not be replayed on heldout pair probes.",
            "next_action": "repair checkpoint, tokenizer, or replay inputs before promotion checks",
        }
    if summary.get("required_all_pair_full"):
        return {
            "model_quality_claim": "pair_probe_replay_ready",
            "reason": "The exact heldout pair probe replayed pair-full on the fixed-preserving transfer checkpoint.",
            "next_action": "compare against prior routes and run stricter promotion guards before accepting the checkpoint",
        }
    if summary.get("any_pair_full"):
        return {
            "model_quality_claim": "pair_probe_replay_partial",
            "reason": "At least one pair prompt surface replayed pair-full, but a required prompt did not fully pass.",
            "next_action": "diagnose prompt-surface sensitivity before promotion",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "The fixed-preserving transfer checkpoint did not replay pair-full on heldout pair prompt surfaces.",
        "next_action": "compare the miss against v744 and repair the transfer corpus",
    }


def replay_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("replay_rows"))


__all__ = [
    "PAIR_PROBE_PROMPT_SPECS",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_CSV_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_HTML_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_JSON_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_MARKDOWN_FILENAME",
    "PAIR_READINESS_FIXED_PRESERVING_TRANSFER_PAIR_PROBE_REPLAY_TEXT_FILENAME",
    "build_fixed_preserving_transfer_pair_probe_replay",
    "locate_fixed_preserving_transfer_pair_probe_replay_source",
    "read_json_report",
    "replay_rows",
    "resolve_exit_code",
]
