from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, utc_now


BOUNDARY_SMOKE_JSON_FILENAME = "baseline_candidate_threshold_boundary_smoke.json"
BOUNDARY_SMOKE_TEXT_FILENAME = "baseline_candidate_threshold_boundary_smoke.txt"
BOUNDARY_SMOKE_MARKDOWN_FILENAME = "baseline_candidate_threshold_boundary_smoke.md"
BOUNDARY_SMOKE_HTML_FILENAME = "baseline_candidate_threshold_boundary_smoke.html"


def build_baseline_candidate_threshold_boundary_smoke_summary(
    *,
    smoke_summary_path: str | Path,
    smoke_result: dict[str, Any],
    matrix_report: dict[str, Any] | None,
    matrix_outputs: dict[str, str] | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    matrix = as_dict(matrix_report)
    boundary = as_dict(matrix.get("threshold_boundary"))
    smoke_status = "pass" if int(smoke_result.get("returncode") or 0) == 0 else "fail"
    matrix_status = str(matrix.get("status") or "not_run")
    boundary_status = str(boundary.get("status") or "not_run")
    status = "pass" if smoke_status == "pass" and matrix_status == "pass" else "fail"
    if status != "pass":
        decision = "fix_live_threshold_boundary"
    elif boundary_status == "pass":
        decision = "live_threshold_boundary_ready"
    else:
        decision = "live_threshold_boundary_review"
    return {
        "schema_version": 1,
        "title": "MiniGPT baseline-candidate threshold boundary smoke",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "source_smoke_summary": str(smoke_summary_path),
        "smoke": {
            "status": smoke_status,
            "returncode": int(smoke_result.get("returncode") or 0),
            "command_text": smoke_result.get("command_text", ""),
            "stdout": smoke_result.get("stdout", ""),
            "stderr": smoke_result.get("stderr", ""),
        },
        "matrix": {
            "status": matrix_status,
            "decision": matrix.get("decision"),
            "threshold_count": matrix.get("threshold_count"),
            "accept_count": matrix.get("accept_count"),
            "reject_count": matrix.get("reject_count"),
            "handoff_check_failure_count": matrix.get("handoff_check_failure_count"),
            "outputs": dict(matrix_outputs or {}),
        },
        "threshold_boundary": boundary,
        "boundary": {
            "model_quality_claim": "not_claimed",
            "reason": "Live boundary smoke runs a tiny CPU comparison and threshold sweep to verify the pipeline; it is not robust model quality evidence.",
        },
    }


def render_baseline_candidate_threshold_boundary_smoke_text(report: dict[str, Any]) -> str:
    smoke = as_dict(report.get("smoke"))
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("source_smoke_summary", report.get("source_smoke_summary")),
        ("smoke_status", smoke.get("status")),
        ("smoke_returncode", smoke.get("returncode")),
        ("matrix_status", matrix.get("status")),
        ("matrix_decision", matrix.get("decision")),
        ("threshold_count", matrix.get("threshold_count")),
        ("accept_count", matrix.get("accept_count")),
        ("reject_count", matrix.get("reject_count")),
        ("handoff_check_failure_count", matrix.get("handoff_check_failure_count")),
        ("threshold_boundary_status", boundary.get("status")),
        ("threshold_boundary_decision", boundary.get("decision")),
        ("strictest_accepting_threshold", boundary.get("strictest_accepting_threshold")),
        ("first_rejecting_threshold", boundary.get("first_rejecting_threshold")),
        ("is_monotonic_acceptance", boundary.get("is_monotonic_acceptance")),
        ("transition_count", boundary.get("transition_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_threshold_boundary_smoke_markdown(report: dict[str, Any]) -> str:
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Threshold Boundary Smoke",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Smoke status: `{as_dict(report.get('smoke')).get('status')}`",
            f"- Matrix status: `{matrix.get('status')}`",
            f"- Accept count: `{matrix.get('accept_count')}`",
            f"- Reject count: `{matrix.get('reject_count')}`",
            f"- Boundary decision: `{boundary.get('decision')}`",
            f"- Strictest accepting threshold: `{boundary.get('strictest_accepting_threshold')}`",
            f"- First rejecting threshold: `{boundary.get('first_rejecting_threshold')}`",
            f"- Monotonic acceptance: `{boundary.get('is_monotonic_acceptance')}`",
            "",
        ]
    )


def render_baseline_candidate_threshold_boundary_smoke_html(report: dict[str, Any]) -> str:
    smoke = as_dict(report.get("smoke"))
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate threshold boundary smoke</title>
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
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate threshold boundary smoke</h1>
<section>
<h2>Summary</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(_compact_decision(report.get('decision')))}</strong></div>
<div class="metric"><span>Smoke</span><strong>{html_escape(smoke.get('status'))}</strong></div>
<div class="metric"><span>Matrix</span><strong>{html_escape(matrix.get('status'))}</strong></div>
<div class="metric"><span>Thresholds</span><strong>{html_escape(matrix.get('threshold_count'))}</strong></div>
<div class="metric"><span>Accept count</span><strong>{html_escape(matrix.get('accept_count'))}</strong></div>
<div class="metric"><span>Reject count</span><strong>{html_escape(matrix.get('reject_count'))}</strong></div>
<div class="metric"><span>Boundary</span><strong>{html_escape(boundary.get('status'))}</strong></div>
<div class="metric"><span>Strictest accept</span><strong>{html_escape(_display_value(boundary.get('strictest_accepting_threshold')))}</strong></div>
<div class="metric"><span>First reject</span><strong>{html_escape(_display_value(boundary.get('first_rejecting_threshold')))}</strong></div>
<div class="metric"><span>Monotonic</span><strong>{html_escape(boundary.get('is_monotonic_acceptance'))}</strong></div>
</div>
</section>
</main>
</body>
</html>
"""


def _compact_decision(value: Any) -> str:
    text = str(value or "")
    if text.startswith("live_threshold_boundary_"):
        return text.removeprefix("live_threshold_boundary_")
    if text.startswith("fix_live_threshold_boundary"):
        return "fix"
    return text


def _display_value(value: Any) -> Any:
    return "none" if value is None else value


def write_baseline_candidate_threshold_boundary_smoke_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / BOUNDARY_SMOKE_JSON_FILENAME,
        "text": root / BOUNDARY_SMOKE_TEXT_FILENAME,
        "markdown": root / BOUNDARY_SMOKE_MARKDOWN_FILENAME,
        "html": root / BOUNDARY_SMOKE_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_threshold_boundary_smoke_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_threshold_boundary_smoke_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_threshold_boundary_smoke_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


__all__ = [
    "BOUNDARY_SMOKE_HTML_FILENAME",
    "BOUNDARY_SMOKE_JSON_FILENAME",
    "BOUNDARY_SMOKE_MARKDOWN_FILENAME",
    "BOUNDARY_SMOKE_TEXT_FILENAME",
    "build_baseline_candidate_threshold_boundary_smoke_summary",
    "render_baseline_candidate_threshold_boundary_smoke_html",
    "render_baseline_candidate_threshold_boundary_smoke_markdown",
    "render_baseline_candidate_threshold_boundary_smoke_text",
    "write_baseline_candidate_threshold_boundary_smoke_outputs",
]
