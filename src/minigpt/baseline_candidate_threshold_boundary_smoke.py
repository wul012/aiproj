from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, number_or_default, utc_now


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
    source_mode: str = "rerun_smoke",
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
    diagnosis = build_threshold_boundary_smoke_diagnosis(
        smoke_status=smoke_status,
        matrix=matrix,
        boundary=boundary,
    )
    return {
        "schema_version": 1,
        "title": "MiniGPT baseline-candidate threshold boundary smoke",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "source_mode": source_mode,
        "source_smoke_summary": str(smoke_summary_path),
        "smoke": {
            "status": smoke_status,
            "returncode": int(smoke_result.get("returncode") or 0),
            "source_mode": source_mode,
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
        "review_diagnosis": diagnosis,
        "boundary": {
            "model_quality_claim": "not_claimed",
            "reason": "Live boundary smoke runs a tiny CPU comparison and threshold sweep to verify the pipeline; it is not robust model quality evidence.",
        },
    }


def build_threshold_boundary_smoke_diagnosis(
    *,
    smoke_status: str,
    matrix: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    matrix_status = str(matrix.get("status") or "not_run")
    boundary_status = str(boundary.get("status") or "not_run")
    boundary_decision = str(boundary.get("decision") or "not_run")
    handoff_failures = int(number_or_default(matrix.get("handoff_check_failure_count"), 0, int))
    accept_count = int(number_or_default(matrix.get("accept_count"), 0, int))
    reject_count = int(number_or_default(matrix.get("reject_count"), 0, int))

    if smoke_status != "pass":
        issues.append(_diagnosis_issue("smoke_execution_failed", "blocker", "Tiny scorecard comparison smoke did not finish cleanly."))
        actions.append(_diagnosis_action("rerun_live_smoke", "Rerun the live smoke and inspect stdout/stderr before trusting threshold evidence."))
    if matrix_status != "pass":
        issues.append(_diagnosis_issue("threshold_matrix_not_ready", "blocker", "Threshold matrix was not generated successfully."))
        actions.append(_diagnosis_action("fix_threshold_matrix", "Fix matrix generation or handoff-check failures before reviewing candidate quality."))
    if handoff_failures:
        issues.append(_diagnosis_issue("handoff_check_failures", "blocker", f"{handoff_failures} threshold rows failed handoff contract checks."))
        actions.append(_diagnosis_action("inspect_handoff_checks", "Open the failed threshold handoff-check outputs and repair contract drift."))
    if boundary_status != "pass":
        if boundary_decision == "no_accepting_threshold":
            issues.append(_diagnosis_issue("no_accepting_threshold", "review", "Every tested threshold rejected the candidate."))
            actions.append(_diagnosis_action("increase_candidate_signal", "Try a stronger candidate run or broader data before promoting this candidate."))
            actions.append(_diagnosis_action("keep_current_baseline", "Keep the current baseline until a candidate has an accepting threshold."))
        elif boundary_decision == "no_rejecting_threshold":
            issues.append(_diagnosis_issue("no_rejecting_threshold", "review", "Every tested threshold accepted the candidate, so the rejection boundary is still unknown."))
            actions.append(_diagnosis_action("raise_threshold_sweep", "Add stricter thresholds to find the first rejecting boundary."))
        elif boundary_decision == "non_monotonic_threshold_outcomes":
            issues.append(_diagnosis_issue("non_monotonic_threshold_outcomes", "review", "Threshold decisions are not monotonic."))
            actions.append(_diagnosis_action("inspect_threshold_rows", "Inspect matrix rows for inconsistent loop decisions or stale source evidence."))
        else:
            issues.append(_diagnosis_issue(boundary_decision, "review", "Threshold boundary is not ready for promotion."))
            actions.append(_diagnosis_action("review_threshold_boundary", "Review the threshold boundary summary before using it in a gate."))
    if not issues:
        actions.append(_diagnosis_action("boundary_ready_for_review", "Use the observed accept/reject boundary as review evidence, not as a model-quality claim."))

    status = "pass" if not issues else ("fail" if any(issue.get("severity") == "blocker" for issue in issues) else "review")
    if status == "pass":
        decision = "threshold_boundary_ready"
    elif status == "fail":
        decision = "fix_live_threshold_boundary"
    elif boundary_decision == "no_accepting_threshold" or (accept_count == 0 and reject_count > 0):
        decision = "candidate_not_accepted"
    else:
        decision = "review_threshold_boundary"
    return {
        "status": status,
        "decision": decision,
        "issue_count": len(issues),
        "action_count": len(actions),
        "issues": issues,
        "actions": actions,
    }


def render_baseline_candidate_threshold_boundary_smoke_text(report: dict[str, Any]) -> str:
    smoke = as_dict(report.get("smoke"))
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    diagnosis = as_dict(report.get("review_diagnosis"))
    execution = as_dict(report.get("execution"))
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("source_mode", report.get("source_mode")),
        ("execution_gate_mode", execution.get("gate_mode")),
        ("execution_require_boundary_pass", execution.get("require_boundary_pass")),
        ("execution_require_diagnosis_pass", execution.get("require_diagnosis_pass")),
        ("execution_expected_exit_code", execution.get("expected_exit_code")),
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
        ("review_diagnosis_status", diagnosis.get("status")),
        ("review_diagnosis_decision", diagnosis.get("decision")),
        ("review_issue_count", diagnosis.get("issue_count")),
        ("review_action_count", diagnosis.get("action_count")),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_threshold_boundary_smoke_markdown(report: dict[str, Any]) -> str:
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    diagnosis = as_dict(report.get("review_diagnosis"))
    execution = as_dict(report.get("execution"))
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Threshold Boundary Smoke",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Source mode: `{report.get('source_mode')}`",
            f"- Gate mode: `{execution.get('gate_mode')}`",
            f"- Require diagnosis pass: `{execution.get('require_diagnosis_pass')}`",
            f"- Expected exit code: `{execution.get('expected_exit_code')}`",
            f"- Smoke status: `{as_dict(report.get('smoke')).get('status')}`",
            f"- Matrix status: `{matrix.get('status')}`",
            f"- Accept count: `{matrix.get('accept_count')}`",
            f"- Reject count: `{matrix.get('reject_count')}`",
            f"- Boundary decision: `{boundary.get('decision')}`",
            f"- Strictest accepting threshold: `{boundary.get('strictest_accepting_threshold')}`",
            f"- First rejecting threshold: `{boundary.get('first_rejecting_threshold')}`",
            f"- Monotonic acceptance: `{boundary.get('is_monotonic_acceptance')}`",
            f"- Review diagnosis: `{diagnosis.get('decision')}`",
            f"- Review issues: `{diagnosis.get('issue_count')}`",
            f"- Review actions: `{diagnosis.get('action_count')}`",
            "",
        ]
    )


def render_baseline_candidate_threshold_boundary_smoke_html(report: dict[str, Any]) -> str:
    smoke = as_dict(report.get("smoke"))
    matrix = as_dict(report.get("matrix"))
    boundary = as_dict(report.get("threshold_boundary"))
    diagnosis = as_dict(report.get("review_diagnosis"))
    execution = as_dict(report.get("execution"))
    issue_html = _diagnosis_items_html(diagnosis.get("issues"), "No review issues.")
    action_html = _diagnosis_items_html(diagnosis.get("actions"), "No follow-up actions.")
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
<div class="metric"><span>Source mode</span><strong>{html_escape(report.get('source_mode'))}</strong></div>
<div class="metric"><span>Gate mode</span><strong>{html_escape(_display_value(execution.get('gate_mode')))}</strong></div>
<div class="metric"><span>Expected exit</span><strong>{html_escape(_display_value(execution.get('expected_exit_code')))}</strong></div>
<div class="metric"><span>Smoke</span><strong>{html_escape(smoke.get('status'))}</strong></div>
<div class="metric"><span>Matrix</span><strong>{html_escape(matrix.get('status'))}</strong></div>
<div class="metric"><span>Thresholds</span><strong>{html_escape(matrix.get('threshold_count'))}</strong></div>
<div class="metric"><span>Accept count</span><strong>{html_escape(matrix.get('accept_count'))}</strong></div>
<div class="metric"><span>Reject count</span><strong>{html_escape(matrix.get('reject_count'))}</strong></div>
<div class="metric"><span>Boundary</span><strong>{html_escape(boundary.get('status'))}</strong></div>
<div class="metric"><span>Diagnosis</span><strong>{html_escape(diagnosis.get('decision'))}</strong></div>
<div class="metric"><span>Strictest accept</span><strong>{html_escape(_display_value(boundary.get('strictest_accepting_threshold')))}</strong></div>
<div class="metric"><span>First reject</span><strong>{html_escape(_display_value(boundary.get('first_rejecting_threshold')))}</strong></div>
<div class="metric"><span>Monotonic</span><strong>{html_escape(boundary.get('is_monotonic_acceptance'))}</strong></div>
</div>
</section>
<section>
<h2>Diagnosis</h2>
<div class="grid">
<div class="metric"><span>Issue count</span><strong>{html_escape(diagnosis.get('issue_count'))}</strong></div>
<div class="metric"><span>Action count</span><strong>{html_escape(diagnosis.get('action_count'))}</strong></div>
</div>
<h3>Issues</h3>
{issue_html}
<h3>Actions</h3>
{action_html}
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


def _diagnosis_issue(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def _diagnosis_action(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _diagnosis_items_html(value: Any, empty_text: str) -> str:
    if not isinstance(value, list) or not value:
        return f"<p>{html_escape(empty_text)}</p>"
    rows = "\n".join(
        "<li>"
        f"<strong>{html_escape(as_dict(item).get('code'))}</strong>"
        f" - <span>{html_escape(as_dict(item).get('message'))}</span>"
        "</li>"
        for item in value
    )
    return f"<ul>{rows}</ul>"


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
    "build_threshold_boundary_smoke_diagnosis",
    "render_baseline_candidate_threshold_boundary_smoke_html",
    "render_baseline_candidate_threshold_boundary_smoke_markdown",
    "render_baseline_candidate_threshold_boundary_smoke_text",
    "write_baseline_candidate_threshold_boundary_smoke_outputs",
]
