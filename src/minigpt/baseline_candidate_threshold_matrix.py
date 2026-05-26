from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from minigpt.baseline_candidate_eval_loop import (
    build_baseline_candidate_eval_loop_report,
    resolve_baseline_candidate_eval_loop_smoke_summary,
    write_baseline_candidate_eval_loop_outputs,
)
from minigpt.baseline_candidate_handoff import build_baseline_candidate_handoff, write_baseline_candidate_handoff_outputs
from minigpt.baseline_candidate_handoff_check import (
    build_baseline_candidate_handoff_check,
    embed_baseline_candidate_handoff_check,
    write_baseline_candidate_handoff_check_outputs,
)
from minigpt.report_utils import as_dict, html_escape, string_list, utc_now


MATRIX_JSON_FILENAME = "baseline_candidate_threshold_matrix.json"
MATRIX_TEXT_FILENAME = "baseline_candidate_threshold_matrix.txt"
MATRIX_MARKDOWN_FILENAME = "baseline_candidate_threshold_matrix.md"
MATRIX_HTML_FILENAME = "baseline_candidate_threshold_matrix.html"
DEFAULT_THRESHOLDS = (0.0, 0.5, 1.0)


def parse_thresholds(value: str | Iterable[float]) -> list[float]:
    if isinstance(value, str):
        stripped = value.strip()
        if ":" in stripped and "," not in stripped:
            thresholds = _parse_threshold_range(stripped)
        else:
            parts = [part.strip() for part in stripped.split(",")]
            thresholds = [float(part) for part in parts if part]
    else:
        thresholds = [float(item) for item in value]
    if not thresholds:
        raise ValueError("at least one threshold is required")
    return thresholds


def build_baseline_candidate_threshold_matrix(
    smoke_summary_path: str | Path,
    out_dir: str | Path,
    *,
    thresholds: str | Iterable[float] = DEFAULT_THRESHOLDS,
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary_path = resolve_baseline_candidate_eval_loop_smoke_summary(smoke_summary_path)
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    threshold_values = parse_thresholds(thresholds)
    rows = [
        _build_threshold_row(
            summary_path,
            root / _threshold_slug(threshold),
            threshold=float(threshold),
            generated_at=generated_at,
        )
        for threshold in threshold_values
    ]
    accept_count = sum(1 for row in rows if row.get("loop_decision") == "accept_candidate")
    reject_count = sum(1 for row in rows if row.get("loop_decision") == "reject_candidate")
    check_failure_count = sum(1 for row in rows if row.get("handoff_check_status") != "pass")
    threshold_boundary = summarize_threshold_boundary(rows)
    status = "pass" if rows and check_failure_count == 0 else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT baseline-candidate threshold matrix",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "threshold_matrix_ready" if status == "pass" else "fix_threshold_matrix",
        "source_smoke_summary": str(summary_path),
        "threshold_count": len(rows),
        "accept_count": accept_count,
        "reject_count": reject_count,
        "handoff_check_failure_count": check_failure_count,
        "threshold_boundary": threshold_boundary,
        "rows": rows,
        "boundary": {
            "model_quality_claim": "not_claimed",
            "reason": "Threshold matrix evidence reuses tiny CPU smoke output to cover acceptance/rejection gates; it is not robust model improvement evidence.",
        },
    }


def render_baseline_candidate_threshold_matrix_text(report: dict[str, Any]) -> str:
    threshold_boundary = as_dict(report.get("threshold_boundary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("source_smoke_summary", report.get("source_smoke_summary")),
        ("threshold_count", report.get("threshold_count")),
        ("accept_count", report.get("accept_count")),
        ("reject_count", report.get("reject_count")),
        ("handoff_check_failure_count", report.get("handoff_check_failure_count")),
        ("threshold_boundary_status", threshold_boundary.get("status")),
        ("threshold_boundary_decision", threshold_boundary.get("decision")),
        ("strictest_accepting_threshold", threshold_boundary.get("strictest_accepting_threshold")),
        ("first_rejecting_threshold", threshold_boundary.get("first_rejecting_threshold")),
        ("is_monotonic_acceptance", threshold_boundary.get("is_monotonic_acceptance")),
        ("transition_count", threshold_boundary.get("transition_count")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for row in _rows(report):
        lines.append(
            "row="
            + ",".join(
                [
                    f"threshold={row.get('threshold')}",
                    f"loop_decision={row.get('loop_decision')}",
                    f"handoff_ready={row.get('handoff_ready')}",
                    f"next_baseline_source={row.get('next_baseline_source')}",
                    f"expected_exit_code={row.get('expected_exit_code')}",
                    f"handoff_check_status={row.get('handoff_check_status')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_baseline_candidate_threshold_matrix_markdown(report: dict[str, Any]) -> str:
    threshold_boundary = as_dict(report.get("threshold_boundary"))
    table = [
        "| Threshold | Loop decision | Handoff ready | Next source | Exit | Check |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in _rows(report):
        table.append(
            "| "
            + " | ".join(
                [
                    str(row.get("threshold")),
                    str(row.get("loop_decision")),
                    str(row.get("handoff_ready")),
                    str(row.get("next_baseline_source")),
                    str(row.get("expected_exit_code")),
                    str(row.get("handoff_check_status")),
                ]
            )
            + " |"
        )
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Threshold Matrix",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Accept count: `{report.get('accept_count')}`",
            f"- Reject count: `{report.get('reject_count')}`",
            f"- Threshold boundary: `{threshold_boundary.get('decision')}`",
            f"- Strictest accepting threshold: `{threshold_boundary.get('strictest_accepting_threshold')}`",
            f"- First rejecting threshold: `{threshold_boundary.get('first_rejecting_threshold')}`",
            "",
            *table,
            "",
        ]
    )


def render_baseline_candidate_threshold_matrix_html(report: dict[str, Any]) -> str:
    threshold_boundary = as_dict(report.get("threshold_boundary"))
    row_html = "\n".join(
        "<tr>"
        f"<td>{html_escape(row.get('threshold'))}</td>"
        f"<td>{html_escape(row.get('loop_decision'))}</td>"
        f"<td>{html_escape(row.get('handoff_ready'))}</td>"
        f"<td>{html_escape(row.get('next_baseline_source'))}</td>"
        f"<td>{html_escape(row.get('expected_exit_code'))}</td>"
        f"<td>{html_escape(row.get('handoff_check_status'))}</td>"
        "</tr>"
        for row in _rows(report)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate threshold matrix</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f8f9f7; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d8ded7; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d8ded7; border-radius: 8px; padding: 10px; background: #fbfcfa; }}
.metric span {{ display: block; color: #607066; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: break-word; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border-bottom: 1px solid #d8ded7; padding: 10px; text-align: left; }}
th {{ color: #44534b; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate threshold matrix</h1>
<section>
<h2>Summary</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(report.get('decision'))}</strong></div>
<div class="metric"><span>Thresholds</span><strong>{html_escape(report.get('threshold_count'))}</strong></div>
<div class="metric"><span>Accept count</span><strong>{html_escape(report.get('accept_count'))}</strong></div>
<div class="metric"><span>Reject count</span><strong>{html_escape(report.get('reject_count'))}</strong></div>
<div class="metric"><span>Check failures</span><strong>{html_escape(report.get('handoff_check_failure_count'))}</strong></div>
<div class="metric"><span>Boundary status</span><strong>{html_escape(threshold_boundary.get('status'))}</strong></div>
<div class="metric"><span>Strictest accept</span><strong>{html_escape(threshold_boundary.get('strictest_accepting_threshold'))}</strong></div>
<div class="metric"><span>First reject</span><strong>{html_escape(threshold_boundary.get('first_rejecting_threshold'))}</strong></div>
<div class="metric"><span>Monotonic</span><strong>{html_escape(threshold_boundary.get('is_monotonic_acceptance'))}</strong></div>
</div>
</section>
<section>
<h2>Rows</h2>
<table>
<thead><tr><th>Threshold</th><th>Loop decision</th><th>Ready</th><th>Next source</th><th>Exit</th><th>Check</th></tr></thead>
<tbody>
{row_html}
</tbody>
</table>
</section>
</main>
</body>
</html>
"""


def write_baseline_candidate_threshold_matrix_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / MATRIX_JSON_FILENAME,
        "text": root / MATRIX_TEXT_FILENAME,
        "markdown": root / MATRIX_MARKDOWN_FILENAME,
        "html": root / MATRIX_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_threshold_matrix_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_threshold_matrix_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_threshold_matrix_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _build_threshold_row(
    summary_path: Path,
    variant_dir: Path,
    *,
    threshold: float,
    generated_at: str | None,
) -> dict[str, Any]:
    loop_dir = variant_dir / "loop"
    handoff_dir = variant_dir / "handoff"
    check_dir = variant_dir / "handoff-check"
    command_result = {
        "name": "existing_tiny_scorecard_comparison_smoke_summary",
        "status": "pass",
        "returncode": 0,
        "source_summary": str(summary_path),
        "command": [],
        "command_text": "",
        "stdout": "",
        "stderr": "",
    }
    loop = build_baseline_candidate_eval_loop_report(
        summary_path,
        command_result=command_result,
        min_overall_score_delta=threshold,
        generated_at=generated_at,
    )
    expected_exit_code = 0 if loop.get("decision") == "accept_candidate" else 2
    loop["execution"] = {
        "source_mode": "reuse_summary",
        "fail_on_reject": True,
        "expected_exit_code": expected_exit_code,
        "gate_mode": "strict",
    }
    loop_outputs = write_baseline_candidate_eval_loop_outputs(loop, loop_dir)
    handoff = build_baseline_candidate_handoff(loop_outputs["json"], generated_at=generated_at)
    handoff_outputs = write_baseline_candidate_handoff_outputs(handoff, handoff_dir)
    check = build_baseline_candidate_handoff_check(handoff_outputs["json"], generated_at=generated_at)
    check_outputs = write_baseline_candidate_handoff_check_outputs(check, check_dir)
    handoff = embed_baseline_candidate_handoff_check(handoff, check, check_outputs)
    handoff_outputs = write_baseline_candidate_handoff_outputs(handoff, handoff_dir)
    next_baseline = as_dict(handoff.get("next_baseline"))
    delta = as_dict(handoff.get("delta"))
    guardrails = as_dict(handoff.get("guardrails"))
    return {
        "threshold": threshold,
        "variant_dir": str(variant_dir),
        "loop_report": loop_outputs["json"],
        "handoff_report": handoff_outputs["json"],
        "handoff_check_report": check_outputs["json"],
        "loop_decision": loop.get("decision"),
        "handoff_decision": handoff.get("decision"),
        "handoff_ready": handoff.get("handoff_ready"),
        "next_baseline_name": next_baseline.get("name"),
        "next_baseline_source": next_baseline.get("source"),
        "overall_score_delta": delta.get("overall_score_delta"),
        "min_overall_score_delta": delta.get("min_overall_score_delta"),
        "expected_exit_code": expected_exit_code,
        "handoff_check_status": check.get("status"),
        "handoff_check_failed_count": check.get("failed_count"),
        "rejected_reasons": string_list(guardrails.get("rejected_reasons")),
    }


def summarize_threshold_boundary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    sorted_rows = sorted([dict(row) for row in rows], key=lambda row: float(row.get("threshold") or 0.0))
    accepting = [float(row.get("threshold") or 0.0) for row in sorted_rows if row.get("loop_decision") == "accept_candidate"]
    rejecting = [float(row.get("threshold") or 0.0) for row in sorted_rows if row.get("loop_decision") == "reject_candidate"]
    transitions = _threshold_transitions(sorted_rows)
    monotonic = _is_monotonic_acceptance(sorted_rows)
    has_accept = bool(accepting)
    has_reject = bool(rejecting)
    status = "pass" if has_accept and has_reject and monotonic else "review"
    strictest_accepting = max(accepting) if accepting else None
    first_rejecting = min(rejecting) if rejecting else None
    if status == "pass":
        decision = "accept_reject_boundary_observed"
    elif not has_accept:
        decision = "no_accepting_threshold"
    elif not has_reject:
        decision = "no_rejecting_threshold"
    else:
        decision = "non_monotonic_threshold_outcomes"
    return {
        "status": status,
        "decision": decision,
        "has_accept": has_accept,
        "has_reject": has_reject,
        "is_monotonic_acceptance": monotonic,
        "transition_count": len(transitions),
        "strictest_accepting_threshold": strictest_accepting,
        "first_rejecting_threshold": first_rejecting,
        "accepting_thresholds": accepting,
        "rejecting_thresholds": rejecting,
        "transitions": transitions,
    }


def _parse_threshold_range(value: str) -> list[float]:
    parts = [part.strip() for part in value.split(":")]
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("threshold range must use start:stop:step")
    try:
        start, stop, step = (Decimal(part) for part in parts)
    except InvalidOperation as exc:
        raise ValueError("threshold range values must be numeric") from exc
    if step <= 0:
        raise ValueError("threshold range step must be positive")
    if stop < start:
        raise ValueError("threshold range stop must be greater than or equal to start")
    thresholds: list[float] = []
    current = start
    max_iterations = 1000
    while current <= stop:
        thresholds.append(float(current))
        current += step
        if len(thresholds) > max_iterations:
            raise ValueError("threshold range is too large")
    if thresholds and thresholds[-1] != float(stop):
        thresholds.append(float(stop))
    return thresholds


def _threshold_transitions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for row in rows:
        if previous is not None and previous.get("loop_decision") != row.get("loop_decision"):
            transitions.append(
                {
                    "from_threshold": previous.get("threshold"),
                    "from_decision": previous.get("loop_decision"),
                    "to_threshold": row.get("threshold"),
                    "to_decision": row.get("loop_decision"),
                }
            )
        previous = row
    return transitions


def _is_monotonic_acceptance(rows: list[dict[str, Any]]) -> bool:
    seen_reject = False
    for row in rows:
        decision = row.get("loop_decision")
        if decision == "reject_candidate":
            seen_reject = True
        if decision == "accept_candidate" and seen_reject:
            return False
    return True


def _threshold_slug(threshold: float) -> str:
    text = f"{threshold:g}".replace("-", "neg").replace(".", "p")
    return f"threshold-{text}"


def _rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("rows")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


__all__ = [
    "DEFAULT_THRESHOLDS",
    "MATRIX_HTML_FILENAME",
    "MATRIX_JSON_FILENAME",
    "MATRIX_MARKDOWN_FILENAME",
    "MATRIX_TEXT_FILENAME",
    "build_baseline_candidate_threshold_matrix",
    "parse_thresholds",
    "render_baseline_candidate_threshold_matrix_html",
    "render_baseline_candidate_threshold_matrix_markdown",
    "render_baseline_candidate_threshold_matrix_text",
    "summarize_threshold_boundary",
    "write_baseline_candidate_threshold_matrix_outputs",
]
