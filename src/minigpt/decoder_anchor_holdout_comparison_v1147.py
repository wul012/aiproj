from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_decoder_anchor_probe_v1146 import (
    DECODER_ANCHOR_PROBE_V1146_STEM,
    resolve_v1145_checkpoint_paths,
)
from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, read_json_object, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code

DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM = "decoder_anchor_holdout_comparison_v1147"
EXPLAIN_DIR_NAME = "\u89e3\u91ca"

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def locate_v1146_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / f"{DECODER_ANCHOR_PROBE_V1146_STEM}.json"
    return source


def locate_v1145_report_from_v1146(v1146_report_path: str | Path) -> Path:
    path = Path(v1146_report_path).resolve()
    for parent in path.parents:
        if parent.name == "aiproj":
            return (
                parent
                / "f"
                / "1145"
                / EXPLAIN_DIR_NAME
                / "model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145"
                / "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json"
            )
    return (
        Path("f")
        / "1145"
        / EXPLAIN_DIR_NAME
        / "model-capability-loss-signal-bridge-decoder-anchor-distribution-v1145"
        / "model_capability_loss_signal_bridge_decoder_anchor_distribution_v1145.json"
    )


def resolve_comparison_paths(
    decoder_probe_report: dict[str, Any],
    *,
    decoder_probe_path: str | Path | None = None,
    loss_signal_report_path: str | Path | None = None,
    checkpoint_override: str | Path | None = None,
    tokenizer_override: str | Path | None = None,
) -> dict[str, Any]:
    source_loss_signal_path = _existing_or_none(loss_signal_report_path)
    if source_loss_signal_path is None:
        source_loss_signal_path = _existing_or_none(decoder_probe_report.get("source_loss_signal_bridge_decoder_anchor_distribution"))
    if source_loss_signal_path is None and decoder_probe_path is not None:
        source_loss_signal_path = _existing_or_none(locate_v1145_report_from_v1146(decoder_probe_path))

    reported_checkpoint = Path(checkpoint_override or decoder_probe_report.get("checkpoint") or "")
    reported_tokenizer = Path(tokenizer_override or decoder_probe_report.get("tokenizer") or "")
    checkpoint = reported_checkpoint
    tokenizer = reported_tokenizer
    used_v1145_archive_resolution = False

    if (not checkpoint.is_file() or not tokenizer.is_file()) and source_loss_signal_path is not None:
        source_loss_signal = read_json_report(source_loss_signal_path, description="v1145 loss signal bridge decoder anchor distribution")
        resolved = resolve_v1145_checkpoint_paths(
            source_loss_signal,
            report_path=source_loss_signal_path,
            checkpoint_override=checkpoint_override,
            tokenizer_override=tokenizer_override,
        )
        checkpoint = Path(str(resolved.get("checkpoint") or ""))
        tokenizer = Path(str(resolved.get("tokenizer") or ""))
        used_v1145_archive_resolution = True

    return {
        "source_loss_signal_report": "" if source_loss_signal_path is None else str(source_loss_signal_path),
        "reported_checkpoint": str(reported_checkpoint),
        "reported_tokenizer": str(reported_tokenizer),
        "reported_checkpoint_exists": reported_checkpoint.is_file(),
        "reported_tokenizer_exists": reported_tokenizer.is_file(),
        "checkpoint": str(checkpoint),
        "tokenizer": str(tokenizer),
        "checkpoint_exists": checkpoint.is_file(),
        "tokenizer_exists": tokenizer.is_file(),
        "used_v1145_archive_resolution": used_v1145_archive_resolution,
    }


def build_decoder_anchor_holdout_comparison_v1147(
    decoder_probe_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    device: str = "cpu",
    decoder_probe_path: str | Path | None = None,
    path_resolution: dict[str, Any] | None = None,
    generator_runner: GeneratorRunner | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    anchor_rows = list_of_dicts(decoder_probe_report.get("rows"))
    unassisted_rows, errors = _run_unassisted_cases(checkpoint_path, tokenizer_path, device, generator_runner or _generate_case)
    rows = _comparison_rows(anchor_rows, unassisted_rows)
    checks = _checks(decoder_probe_report, checkpoint_path, tokenizer_path, anchor_rows, unassisted_rows, errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, anchor_rows, unassisted_rows, issues)
    return {
        "schema_version": 1,
        "title": "MiniGPT decoder anchor vs unassisted holdout comparison v1147",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_probe": str(decoder_probe_path or ""),
        "path_resolution": path_resolution or {},
        "checkpoint": str(checkpoint_path),
        "tokenizer": str(tokenizer_path),
        "device": device,
        "rows": rows,
        "unassisted_errors": errors,
        "check_rows": checks,
        "summary": summary,
        "recommendations": _recommendations(status, summary),
        "csv_fieldnames": [
            "case_id",
            "anchor_prompt",
            "anchor_combined",
            "anchor_fragment_hit",
            "anchor_loss_hit",
            "unassisted_prompt",
            "unassisted_continuation",
            "unassisted_hit_terms",
            "unassisted_full_pair_hit",
            "fragment_lift",
        ],
    }


def write_decoder_anchor_holdout_comparison_v1147_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM,
        row_title="Anchor vs Unassisted Comparison Rows",
    )


def _unassisted_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "answer-colon-pair", "prompt": "answer:", "expected_terms": ["fixed", "loss"], "seed": 4100},
        {"case_id": "answer-space-pair", "prompt": "answer: ", "expected_terms": ["fixed", "loss"], "seed": 4101},
        {"case_id": "completion-colon-pair", "prompt": "completion:", "expected_terms": ["fixed", "loss"], "seed": 4102},
        {"case_id": "finish-space-pair", "prompt": "finish: ", "expected_terms": ["fixed", "loss"], "seed": 4103},
        {"case_id": "compact-signal-answer-pair", "prompt": "state compact signal\nanswer:", "expected_terms": ["fixed", "loss"], "seed": 4104},
    ]


def _run_unassisted_cases(
    checkpoint: str | Path,
    tokenizer: str | Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for case in _unassisted_cases():
        try:
            response = runner(case, checkpoint, tokenizer, device)
            rows.append(_unassisted_row(case, response))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            errors.append({"case_id": case.get("case_id"), "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(case.get("prompt") or ""),
        max_new_tokens=8,
        temperature=0.2,
        top_k=5,
        seed=int(case.get("seed") or 0),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _unassisted_row(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    continuation = str(response.get("continuation") or "")
    expected_terms = [str(term) for term in case.get("expected_terms", [])]
    hit_terms = [term for term in expected_terms if term.lower() in continuation.lower()]
    missed_terms = [term for term in expected_terms if term not in hit_terms]
    return {
        "case_id": case.get("case_id"),
        "prompt": case.get("prompt"),
        "generated": response.get("generated"),
        "continuation": continuation,
        "expected_terms": expected_terms,
        "hit_terms": hit_terms,
        "missed_terms": missed_terms,
        "any_term_hit": bool(hit_terms),
        "full_pair_hit": bool(expected_terms) and not missed_terms,
        "generation_error": response.get("generation_error", ""),
        "seed": response.get("seed"),
    }


def _comparison_rows(anchor_rows: list[dict[str, Any]], unassisted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, unassisted in enumerate(unassisted_rows):
        anchor = anchor_rows[index] if index < len(anchor_rows) else {}
        rows.append(
            {
                "case_id": unassisted.get("case_id"),
                "anchor_case_id": anchor.get("case_id"),
                "anchor_prompt": anchor.get("prompt"),
                "anchor_combined": anchor.get("combined"),
                "anchor_fragment_hit": anchor.get("fragment_hit") is True,
                "anchor_loss_hit": anchor.get("anchor_assisted_loss_hit") is True,
                "unassisted_prompt": unassisted.get("prompt"),
                "unassisted_generated": unassisted.get("generated"),
                "unassisted_continuation": unassisted.get("continuation"),
                "unassisted_hit_terms": unassisted.get("hit_terms"),
                "unassisted_full_pair_hit": unassisted.get("full_pair_hit") is True,
                "fragment_lift": int(anchor.get("fragment_hit") is True) - int(unassisted.get("any_term_hit") is True),
            }
        )
    return rows


def _checks(
    source: dict[str, Any],
    checkpoint: str | Path,
    tokenizer: str | Path,
    anchor_rows: list[dict[str, Any]],
    unassisted_rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_summary = as_dict(source.get("summary"))
    unassisted_full_pairs = sum(1 for row in unassisted_rows if row.get("full_pair_hit") is True)
    anchor_fragment_hits = sum(1 for row in anchor_rows if row.get("fragment_hit") is True)
    unassisted_any_hits = sum(1 for row in unassisted_rows if row.get("any_term_hit") is True)
    return [
        _check("v1146_probe_passed", source.get("status") == "pass", source.get("status"), "v1146 decoder-anchor probe must pass first"),
        _check("v1146_next_step_matches_comparison", source_summary.get("next_step") == "compare_decoder_anchor_probe_with_unassisted_holdout_replay", source_summary.get("next_step"), "v1146 must point to this comparison"),
        _check("checkpoint_exists", Path(checkpoint).is_file(), str(checkpoint), "resolved checkpoint must exist"),
        _check("tokenizer_exists", Path(tokenizer).is_file(), str(tokenizer), "resolved tokenizer must exist"),
        _check("anchor_rows_present", len(anchor_rows) == 5, len(anchor_rows), "comparison expects the five v1146 anchor rows"),
        _check("unassisted_rows_executed", len(unassisted_rows) == 5, len(unassisted_rows), "comparison must run five unassisted holdout prompts"),
        _check("no_unassisted_generation_errors", not errors and all(not row.get("generation_error") for row in unassisted_rows), len(errors), "unassisted replay should not raise generation errors"),
        _check("anchor_outpaces_unassisted_any_hits", anchor_fragment_hits > unassisted_any_hits, {"anchor": anchor_fragment_hits, "unassisted": unassisted_any_hits}, "anchor-assisted fragment hits should exceed unassisted term hits"),
        _check("unassisted_pair_not_recovered", unassisted_full_pairs == 0, unassisted_full_pairs, "unassisted prompts should not yet recover the full fixed/loss pair"),
        _check("promotion_boundary_kept", True, False, "comparison is a bounded diagnostic, not a promotion gate"),
    ]


def _summary(status: str, anchor_rows: list[dict[str, Any]], unassisted_rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_fragment_hits = sum(1 for row in anchor_rows if row.get("fragment_hit") is True)
    anchor_loss_hits = sum(1 for row in anchor_rows if row.get("anchor_assisted_loss_hit") is True)
    unassisted_any_hits = sum(1 for row in unassisted_rows if row.get("any_term_hit") is True)
    unassisted_full_pairs = sum(1 for row in unassisted_rows if row.get("full_pair_hit") is True)
    unassisted_loss_hits = sum(1 for row in unassisted_rows if "loss" in row.get("hit_terms", []))
    unassisted_fixed_hits = sum(1 for row in unassisted_rows if "fixed" in row.get("hit_terms", []))
    return {
        "decoder_anchor_holdout_comparison_ready": status == "pass",
        "anchor_probe_case_count": len(anchor_rows),
        "anchor_fragment_hit_count": anchor_fragment_hits,
        "anchor_loss_hit_count": anchor_loss_hits,
        "unassisted_case_count": len(unassisted_rows),
        "unassisted_any_term_hit_count": unassisted_any_hits,
        "unassisted_fixed_hit_count": unassisted_fixed_hits,
        "unassisted_loss_hit_count": unassisted_loss_hits,
        "unassisted_full_pair_count": unassisted_full_pairs,
        "anchor_fragment_hit_rate": round(anchor_fragment_hits / len(anchor_rows), 4) if anchor_rows else 0.0,
        "unassisted_any_term_hit_rate": round(unassisted_any_hits / len(unassisted_rows), 4) if unassisted_rows else 0.0,
        "anchor_over_unassisted_hit_delta": anchor_fragment_hits - unassisted_any_hits,
        "model_quality_claim": "anchor_assisted_signal_exceeds_unassisted_holdout_replay",
        "promotion_ready": False,
        "unassisted_success_claim": False,
        "next_step": "build_unassisted_holdout_repair_plan",
        "failed_check_count": len(issues),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status == "pass" and int(summary.get("anchor_over_unassisted_hit_delta") or 0) > 0:
        return "decoder_anchor_signal_exceeds_unassisted_holdout_replay"
    return "fix_decoder_anchor_holdout_comparison"


def _recommendations(status: str, summary: dict[str, Any]) -> list[str]:
    if status == "pass":
        return [
            "Keep v1147 as a contrastive diagnostic: anchor-assisted fragments are stronger than unassisted holdout responses.",
            "Do not promote the checkpoint until an unassisted fixed/loss pair replay passes.",
            "Use the next version to plan or train a small unassisted holdout repair rather than adding another governance wrapper.",
        ]
    return [
        "Repair source v1146 readiness, archived checkpoint resolution, or generation execution before interpreting the comparison.",
        "If unassisted full-pair recovery appears, replace this diagnostic with a promotion-bound replay check.",
    ]


def _existing_or_none(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    return path if path.is_file() else None


__all__ = [
    "DECODER_ANCHOR_HOLDOUT_COMPARISON_V1147_STEM",
    "build_decoder_anchor_holdout_comparison_v1147",
    "locate_v1145_report_from_v1146",
    "locate_v1146_report",
    "read_json_report",
    "resolve_comparison_paths",
    "resolve_exit_code",
    "write_decoder_anchor_holdout_comparison_v1147_outputs",
]
