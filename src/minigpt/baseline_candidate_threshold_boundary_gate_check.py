from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import as_dict, html_escape, number_or_default, utc_now


GATE_CHECK_JSON_FILENAME = "baseline_candidate_threshold_boundary_gate_check.json"
GATE_CHECK_TEXT_FILENAME = "baseline_candidate_threshold_boundary_gate_check.txt"
GATE_CHECK_MARKDOWN_FILENAME = "baseline_candidate_threshold_boundary_gate_check.md"
GATE_CHECK_HTML_FILENAME = "baseline_candidate_threshold_boundary_gate_check.html"


def load_threshold_boundary_smoke_summary(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("threshold boundary smoke summary must be a JSON object")
    return payload


def build_threshold_boundary_gate_check(
    summary_path: str | Path,
    *,
    actual_exit_code: int,
    expected_exit_code: int | None = None,
    expected_diagnosis_decision: str | None = None,
    command_text: str = "",
    stdout_path: str = "",
    stderr_path: str = "",
    generated_at: str | None = None,
) -> dict[str, Any]:
    summary_file = Path(summary_path)
    load_error = ""
    try:
        summary = load_threshold_boundary_smoke_summary(summary_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        summary = {}
        load_error = f"{type(exc).__name__}: {exc}"
    execution = as_dict(summary.get("execution"))
    diagnosis = as_dict(summary.get("review_diagnosis"))
    boundary = as_dict(summary.get("threshold_boundary"))
    summary_expected_exit_code = int(number_or_default(execution.get("expected_exit_code"), -1, int))
    resolved_expected_exit_code = int(expected_exit_code if expected_exit_code is not None else summary_expected_exit_code)
    checks = [
        _check("summary_exists", summary_file.is_file(), True, summary_file.is_file(), f"summary={summary_file}"),
        _check(
            "summary_loads",
            not load_error,
            "loadable JSON object",
            load_error or "loaded",
            "Boundary smoke summary must be readable before checking the gate contract.",
        ),
        _check("summary_status_pass", summary.get("status") == "pass", True, summary.get("status"), "Boundary smoke summary must be structurally pass."),
        _check(
            "summary_expected_exit_matches",
            summary_expected_exit_code == resolved_expected_exit_code,
            resolved_expected_exit_code,
            summary_expected_exit_code,
            "execution.expected_exit_code must match the gate expectation.",
        ),
        _check(
            "actual_exit_matches_expected",
            int(actual_exit_code) == resolved_expected_exit_code,
            resolved_expected_exit_code,
            int(actual_exit_code),
            "Runner exit code must match the expected strict-gate result.",
        ),
    ]
    if expected_diagnosis_decision:
        checks.append(
            _check(
                "diagnosis_decision_matches",
                diagnosis.get("decision") == expected_diagnosis_decision,
                expected_diagnosis_decision,
                diagnosis.get("decision"),
                "review_diagnosis.decision must match the expected outcome.",
            )
        )
    failed_checks = [check for check in checks if check.get("status") != "pass"]
    status = "pass" if not failed_checks else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT baseline-candidate threshold boundary gate check",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "expected_exit_verified" if status == "pass" else "fix_threshold_boundary_gate",
        "source_summary": str(summary_file),
        "load_error": load_error,
        "actual_exit_code": int(actual_exit_code),
        "expected_exit_code": resolved_expected_exit_code,
        "summary_expected_exit_code": summary_expected_exit_code,
        "summary_status": summary.get("status"),
        "summary_decision": summary.get("decision"),
        "gate_mode": execution.get("gate_mode"),
        "diagnosis_status": diagnosis.get("status"),
        "diagnosis_decision": diagnosis.get("decision"),
        "boundary_status": boundary.get("status"),
        "boundary_decision": boundary.get("decision"),
        "check_count": len(checks),
        "failed_count": len(failed_checks),
        "checks": checks,
        "command": {
            "command_text": command_text,
            "stdout": stdout_path,
            "stderr": stderr_path,
        },
    }


def render_threshold_boundary_gate_check_text(report: dict[str, Any]) -> str:
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("source_summary", report.get("source_summary")),
        ("actual_exit_code", report.get("actual_exit_code")),
        ("expected_exit_code", report.get("expected_exit_code")),
        ("summary_expected_exit_code", report.get("summary_expected_exit_code")),
        ("gate_mode", report.get("gate_mode")),
        ("diagnosis_status", report.get("diagnosis_status")),
        ("diagnosis_decision", report.get("diagnosis_decision")),
        ("boundary_status", report.get("boundary_status")),
        ("boundary_decision", report.get("boundary_decision")),
        ("check_count", report.get("check_count")),
        ("failed_count", report.get("failed_count")),
    ]
    lines = [f"{key}={value}" for key, value in rows]
    for check in _checks(report):
        lines.append(
            "check="
            + ",".join(
                [
                    f"id={check.get('id')}",
                    f"status={check.get('status')}",
                    f"expected={check.get('expected')}",
                    f"actual={check.get('actual')}",
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_threshold_boundary_gate_check_markdown(report: dict[str, Any]) -> str:
    table = [
        "| Check | Status | Expected | Actual |",
        "| --- | --- | --- | --- |",
    ]
    for check in _checks(report):
        table.append(f"| {check.get('id')} | {check.get('status')} | {check.get('expected')} | {check.get('actual')} |")
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Threshold Boundary Gate Check",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Gate mode: `{report.get('gate_mode')}`",
            f"- Actual exit code: `{report.get('actual_exit_code')}`",
            f"- Expected exit code: `{report.get('expected_exit_code')}`",
            f"- Diagnosis: `{report.get('diagnosis_decision')}`",
            f"- Failed checks: `{report.get('failed_count')}`",
            "",
            *table,
            "",
        ]
    )


def render_threshold_boundary_gate_check_html(report: dict[str, Any]) -> str:
    row_html = "\n".join(
        "<tr>"
        f"<td>{html_escape(check.get('id'))}</td>"
        f"<td>{html_escape(check.get('status'))}</td>"
        f"<td>{html_escape(check.get('expected'))}</td>"
        f"<td>{html_escape(check.get('actual'))}</td>"
        "</tr>"
        for check in _checks(report)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT threshold boundary gate check</title>
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
</style>
</head>
<body>
<main>
<h1>MiniGPT threshold boundary gate check</h1>
<section>
<h2>Summary</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(report.get('decision'))}</strong></div>
<div class="metric"><span>Gate mode</span><strong>{html_escape(report.get('gate_mode'))}</strong></div>
<div class="metric"><span>Actual exit</span><strong>{html_escape(report.get('actual_exit_code'))}</strong></div>
<div class="metric"><span>Expected exit</span><strong>{html_escape(report.get('expected_exit_code'))}</strong></div>
<div class="metric"><span>Diagnosis</span><strong>{html_escape(report.get('diagnosis_decision'))}</strong></div>
<div class="metric"><span>Boundary</span><strong>{html_escape(report.get('boundary_decision'))}</strong></div>
<div class="metric"><span>Failed checks</span><strong>{html_escape(report.get('failed_count'))}</strong></div>
</div>
</section>
<section>
<h2>Checks</h2>
<table>
<thead><tr><th>Check</th><th>Status</th><th>Expected</th><th>Actual</th></tr></thead>
<tbody>
{row_html}
</tbody>
</table>
</section>
</main>
</body>
</html>
"""


def write_threshold_boundary_gate_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / GATE_CHECK_JSON_FILENAME,
        "text": root / GATE_CHECK_TEXT_FILENAME,
        "markdown": root / GATE_CHECK_MARKDOWN_FILENAME,
        "html": root / GATE_CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_threshold_boundary_gate_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_threshold_boundary_gate_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_threshold_boundary_gate_check_html(report), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _check(check_id: str, condition: bool, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "pass" if condition else "fail",
        "expected": expected,
        "actual": actual,
        "detail": detail,
    }


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("checks")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


__all__ = [
    "GATE_CHECK_HTML_FILENAME",
    "GATE_CHECK_JSON_FILENAME",
    "GATE_CHECK_MARKDOWN_FILENAME",
    "GATE_CHECK_TEXT_FILENAME",
    "build_threshold_boundary_gate_check",
    "load_threshold_boundary_smoke_summary",
    "render_threshold_boundary_gate_check_html",
    "render_threshold_boundary_gate_check_markdown",
    "render_threshold_boundary_gate_check_text",
    "write_threshold_boundary_gate_check_outputs",
]
