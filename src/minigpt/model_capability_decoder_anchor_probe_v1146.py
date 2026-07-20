from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, read_json_object, utc_now
from minigpt.server_contracts import GenerationRequest
from minigpt.server_generator import MiniGPTGenerator
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code

DECODER_ANCHOR_PROBE_V1146_STEM = "model_capability_decoder_anchor_probe_v1146"

GeneratorRunner = Callable[[dict[str, Any], str | Path, str | Path, str], dict[str, Any]]


def read_json_report(path: str | Path, *, description: str = "JSON report") -> dict[str, Any]:
    return read_json_object(path, description=description)


def resolve_v1145_checkpoint_paths(
    report: dict[str, Any],
    *,
    report_path: str | Path | None = None,
    checkpoint_override: str | Path | None = None,
    tokenizer_override: str | Path | None = None,
) -> dict[str, Any]:
    training = as_dict(report.get("training_signal"))
    reported_checkpoint = Path(checkpoint_override or str(training.get("checkpoint_path") or ""))
    reported_tokenizer = Path(tokenizer_override or str(training.get("tokenizer_path") or ""))
    resolved_checkpoint = reported_checkpoint
    resolved_tokenizer = reported_tokenizer
    used_archive_relative_fallback = False
    if (not resolved_checkpoint.is_file() or not resolved_tokenizer.is_file()) and report_path is not None:
        base = Path(report_path).parent / "real-loss-signal-training-run"
        fallback_checkpoint = base / "checkpoint.pt"
        fallback_tokenizer = base / "tokenizer.json"
        if fallback_checkpoint.is_file() and fallback_tokenizer.is_file():
            resolved_checkpoint = fallback_checkpoint
            resolved_tokenizer = fallback_tokenizer
            used_archive_relative_fallback = True
    return {
        "reported_checkpoint": str(reported_checkpoint),
        "reported_tokenizer": str(reported_tokenizer),
        "reported_checkpoint_exists": reported_checkpoint.is_file(),
        "reported_tokenizer_exists": reported_tokenizer.is_file(),
        "checkpoint": str(resolved_checkpoint),
        "tokenizer": str(resolved_tokenizer),
        "checkpoint_exists": resolved_checkpoint.is_file(),
        "tokenizer_exists": resolved_tokenizer.is_file(),
        "used_archive_relative_fallback": used_archive_relative_fallback,
    }


def build_decoder_anchor_probe_v1146(
    loss_signal_distribution_report: dict[str, Any],
    *,
    checkpoint_path: str | Path,
    tokenizer_path: str | Path,
    device: str = "cpu",
    source_report_path: str | Path | None = None,
    path_resolution: dict[str, Any] | None = None,
    generator_runner: GeneratorRunner | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    cases = _probe_cases()
    rows, errors = _run_cases(cases, checkpoint_path, tokenizer_path, device, generator_runner or _generate_case)
    checks = _checks(loss_signal_distribution_report, checkpoint_path, tokenizer_path, rows, errors)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    summary = _summary(status, rows, issues)
    return {
        "schema_version": 1,
        "title": "MiniGPT decoder anchor probe v1146",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_loss_signal_bridge_decoder_anchor_distribution": str(source_report_path or ""),
        "path_resolution": path_resolution or {},
        "checkpoint": str(checkpoint_path),
        "tokenizer": str(tokenizer_path),
        "device": device,
        "rows": rows,
        "probe_errors": errors,
        "check_rows": checks,
        "summary": summary,
        "recommendations": _recommendations(status, summary),
        "csv_fieldnames": [
            "case_id",
            "prompt",
            "continuation",
            "combined",
            "expected_fragment",
            "fragment_hit",
            "anchor_assisted_loss_hit",
            "generation_error",
        ],
    }


def write_decoder_anchor_probe_v1146_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem=DECODER_ANCHOR_PROBE_V1146_STEM,
        row_title="Decoder Anchor Probe Rows",
    )


def _probe_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "fixed-space-loss", "prompt": "fixed ", "expected_fragment": "loss", "max_new_tokens": 8, "top_k": 5, "seed": 2004},
        {"case_id": "lo-to-loss", "prompt": "lo", "expected_fragment": "loss", "max_new_tokens": 8, "top_k": 5, "seed": 2005},
        {"case_id": "los-to-loss", "prompt": "los", "expected_fragment": "loss", "max_new_tokens": 8, "top_k": 5, "seed": 2006},
        {"case_id": "fixed-retention", "prompt": "fixed", "expected_fragment": "fixed", "max_new_tokens": 8, "top_k": 5, "seed": 2003},
        {"case_id": "fi-to-loss-association", "prompt": "fi", "expected_fragment": "loss", "max_new_tokens": 8, "top_k": 5, "seed": 2001},
    ]


def _run_cases(
    cases: list[dict[str, Any]],
    checkpoint: str | Path,
    tokenizer: str | Path,
    device: str,
    runner: GeneratorRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for case in cases:
        try:
            response = runner(case, checkpoint, tokenizer, device)
            rows.append(_row(case, response))
        except Exception as exc:  # pragma: no cover - defensive CLI boundary.
            errors.append({"case_id": case.get("case_id"), "error": type(exc).__name__, "message": str(exc)})
    return rows, errors


def _generate_case(case: dict[str, Any], checkpoint: str | Path, tokenizer: str | Path, device: str) -> dict[str, Any]:
    request = GenerationRequest(
        prompt=str(case.get("prompt") or ""),
        max_new_tokens=int(case.get("max_new_tokens") or 8),
        temperature=0.2,
        top_k=int(case.get("top_k") or 5),
        seed=int(case.get("seed") or 0),
    )
    return MiniGPTGenerator(checkpoint, tokenizer, device=device).generate(request).to_dict()


def _row(case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    prompt = str(case.get("prompt") or "")
    continuation = str(response.get("continuation") or "")
    generated = str(response.get("generated") or "")
    combined = generated if generated else f"{prompt}{continuation}"
    expected = str(case.get("expected_fragment") or "")
    lowered = combined.lower()
    prompt_lowered = prompt.lower()
    return {
        "case_id": case.get("case_id"),
        "prompt": prompt,
        "generated": generated,
        "continuation": continuation,
        "combined": combined,
        "expected_fragment": expected,
        "fragment_hit": bool(expected) and expected.lower() in lowered,
        "anchor_assisted_loss_hit": "loss" in lowered and "loss" not in prompt_lowered,
        "generation_error": response.get("generation_error", ""),
        "seed": response.get("seed"),
        "max_new_tokens": response.get("max_new_tokens"),
        "top_k": response.get("top_k"),
    }


def _checks(
    source: dict[str, Any],
    checkpoint: str | Path,
    tokenizer: str | Path,
    rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = as_dict(source.get("summary"))
    fragment_hits = sum(1 for row in rows if row.get("fragment_hit") is True)
    loss_hits = sum(1 for row in rows if row.get("anchor_assisted_loss_hit") is True)
    return [
        _check("v1145_report_passed", source.get("status") == "pass", source.get("status"), "v1145 loss signal bridge report must pass"),
        _check("v1145_report_ready", summary.get("loss_signal_bridge_decoder_anchor_distribution_ready") is True, summary.get("loss_signal_bridge_decoder_anchor_distribution_ready"), "v1145 ready flag must be true"),
        _check("v1145_next_step_matches_probe", summary.get("next_step") == "run_decoder_anchor_probe_against_v1145_checkpoint", summary.get("next_step"), "v1145 must point to this probe"),
        _check("checkpoint_exists", Path(checkpoint).is_file(), str(checkpoint), "resolved checkpoint must exist"),
        _check("tokenizer_exists", Path(tokenizer).is_file(), str(tokenizer), "resolved tokenizer must exist"),
        _check("all_probe_cases_executed", len(rows) == 5, len(rows), "v1146 must execute five local anchor cases"),
        _check("no_generation_errors", not errors and all(not row.get("generation_error") for row in rows), len(errors), "probe generation should not raise errors"),
        _check("fragment_hit_threshold", fragment_hits >= 4, fragment_hits, "at least four local anchor fragments should be recovered"),
        _check("loss_anchor_hit_threshold", loss_hits >= 3, loss_hits, "at least three probes should recover a loss fragment with anchor assistance"),
        _check("promotion_boundary_kept", True, False, "decoder anchor fragment signal is not promotion evidence"),
    ]


def _summary(status: str, rows: list[dict[str, Any]], issues: list[dict[str, Any]]) -> dict[str, Any]:
    fragment_hits = sum(1 for row in rows if row.get("fragment_hit") is True)
    loss_hits = sum(1 for row in rows if row.get("anchor_assisted_loss_hit") is True)
    return {
        "decoder_anchor_probe_ready": status == "pass",
        "probe_case_count": len(rows),
        "fragment_hit_count": fragment_hits,
        "anchor_assisted_loss_hit_count": loss_hits,
        "fragment_hit_rate": round(fragment_hits / len(rows), 4) if rows else 0.0,
        "anchor_assisted_loss_hit_rate": round(loss_hits / len(rows), 4) if rows else 0.0,
        "model_quality_claim": "decoder_anchor_fragment_signal_only",
        "promotion_ready": False,
        "unassisted_success_claim": False,
        "next_step": "compare_decoder_anchor_probe_with_unassisted_holdout_replay",
        "failed_check_count": len(issues),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status == "pass" and int(summary.get("anchor_assisted_loss_hit_count") or 0) >= 3:
        return "model_capability_decoder_anchor_probe_found_fragment_signal"
    return "fix_model_capability_decoder_anchor_probe"


def _recommendations(status: str, summary: dict[str, Any]) -> list[str]:
    if status == "pass":
        return [
            "Treat v1146 as anchor-assisted fragment evidence only.",
            "Compare this checkpoint against unassisted holdout replay before claiming broader model improvement.",
        ]
    return [
        "Repair checkpoint resolution, v1145 readiness, or local anchor prompt behavior before continuing.",
        "Do not use a failed decoder-anchor probe as model promotion evidence.",
    ]


__all__ = [
    "DECODER_ANCHOR_PROBE_V1146_STEM",
    "build_decoder_anchor_probe_v1146",
    "read_json_report",
    "resolve_exit_code",
    "resolve_v1145_checkpoint_paths",
    "write_decoder_anchor_probe_v1146_outputs",
]
