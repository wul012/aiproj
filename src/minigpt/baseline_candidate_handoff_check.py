from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.baseline_candidate_handoff import HANDOFF_JSON_FILENAME, build_baseline_candidate_handoff
from minigpt.report_utils import as_dict, html_escape, string_list, utc_now


HANDOFF_CHECK_JSON_FILENAME = "baseline_candidate_handoff_check.json"
HANDOFF_CHECK_TEXT_FILENAME = "baseline_candidate_handoff_check.txt"
HANDOFF_CHECK_MARKDOWN_FILENAME = "baseline_candidate_handoff_check.md"
HANDOFF_CHECK_HTML_FILENAME = "baseline_candidate_handoff_check.html"

CHECKED_FIELDS = (
    "status",
    "decision",
    "handoff_ready",
    "next_baseline",
    "baseline.checkpoint_exists",
    "candidate.checkpoint_exists",
    "guardrails.rejected_reasons",
    "execution.expected_exit_code",
)


def resolve_baseline_candidate_handoff(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / HANDOFF_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def load_baseline_candidate_handoff(path: str | Path) -> dict[str, Any]:
    resolved = resolve_baseline_candidate_handoff(path)
    payload = json.loads(resolved.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("baseline-candidate handoff must be a JSON object")
    payload = dict(payload)
    payload["_source_handoff_path"] = str(resolved)
    return payload


def build_baseline_candidate_handoff_check(
    handoff_path: str | Path,
    *,
    title: str = "MiniGPT baseline-candidate handoff check",
    generated_at: str | None = None,
) -> dict[str, Any]:
    handoff_file = resolve_baseline_candidate_handoff(handoff_path)
    actual = load_baseline_candidate_handoff(handoff_file)
    source_loop_report = _resolve_maybe_relative(actual.get("source_loop_report"), handoff_file.parent)
    issues: list[dict[str, Any]] = []
    expected: dict[str, Any] = {}
    if source_loop_report is None:
        issues.append(
            _issue(
                "source_loop_report_missing",
                "source_loop_report",
                "",
                actual.get("source_loop_report"),
                "handoff has no source_loop_report",
            )
        )
    elif not source_loop_report.is_file():
        issues.append(
            _issue(
                "source_loop_report_not_found",
                "source_loop_report",
                str(source_loop_report),
                actual.get("source_loop_report"),
                "source loop report is missing",
            )
        )
    else:
        try:
            expected = build_baseline_candidate_handoff(source_loop_report, generated_at=str(actual.get("generated_at") or ""))
        except Exception as exc:  # pragma: no cover - defensive contract reporting
            issues.append(
                _issue(
                    "expected_handoff_rebuild_failed",
                    "source_loop_report",
                    "rebuildable",
                    type(exc).__name__,
                    str(exc),
                )
            )
    if expected:
        for field in CHECKED_FIELDS:
            expected_value = _field(expected, field)
            actual_value = _field(actual, field)
            if actual_value != expected_value:
                issues.append(
                    _issue(
                        "handoff_field_mismatch",
                        field,
                        expected_value,
                        actual_value,
                        f"{field} differs from rebuilt handoff",
                    )
                )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "continue_with_valid_handoff" if status == "pass" else "fix_baseline_candidate_handoff_contract",
        "failed_count": len(issues),
        "issues": issues,
        "checked_fields": list(CHECKED_FIELDS),
        "source_handoff": str(handoff_file),
        "source_loop_report": "" if source_loop_report is None else str(source_loop_report),
        "handoff_decision": actual.get("decision"),
        "expected_decision": expected.get("decision"),
        "handoff_ready": actual.get("handoff_ready"),
        "expected_handoff_ready": expected.get("handoff_ready"),
    }


def render_baseline_candidate_handoff_check_text(report: dict[str, Any]) -> str:
    rows = [
        ("status", report.get("status")),
        ("decision", report.get("decision")),
        ("failed_count", report.get("failed_count")),
        ("source_handoff", report.get("source_handoff")),
        ("source_loop_report", report.get("source_loop_report")),
        ("handoff_decision", report.get("handoff_decision")),
        ("expected_decision", report.get("expected_decision")),
        ("handoff_ready", report.get("handoff_ready")),
        ("expected_handoff_ready", report.get("expected_handoff_ready")),
        ("issues", ",".join(str(issue.get("field")) for issue in _issues(report))),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_baseline_candidate_handoff_check_markdown(report: dict[str, Any]) -> str:
    issues = _issues(report)
    issue_lines = ["- none"] if not issues else [f"- `{issue.get('field')}`: {issue.get('detail')}" for issue in issues]
    return "\n".join(
        [
            "# MiniGPT Baseline-Candidate Handoff Check",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Decision: `{report.get('decision')}`",
            f"- Failed count: `{report.get('failed_count')}`",
            f"- Source handoff: `{report.get('source_handoff')}`",
            f"- Source loop report: `{report.get('source_loop_report')}`",
            f"- Handoff decision: `{report.get('handoff_decision')}`",
            f"- Expected decision: `{report.get('expected_decision')}`",
            "",
            "## Issues",
            "",
            *issue_lines,
            "",
        ]
    )


def render_baseline_candidate_handoff_check_html(report: dict[str, Any]) -> str:
    issues = _issues(report)
    issue_items = "\n".join(
        f"<li><strong>{html_escape(issue.get('field'))}</strong>: {html_escape(issue.get('detail'))}</li>"
        for issue in issues
    ) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT baseline-candidate handoff check</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f8f9f7; color: #17211d; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d8ded7; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d8ded7; border-radius: 8px; padding: 10px; background: #fbfcfa; }}
.metric span {{ display: block; color: #607066; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT baseline-candidate handoff check</h1>
<section>
<h2>Contract Status</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(report.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(report.get('decision'))}</strong></div>
<div class="metric"><span>Failed count</span><strong>{html_escape(report.get('failed_count'))}</strong></div>
<div class="metric"><span>Handoff decision</span><strong>{html_escape(report.get('handoff_decision'))}</strong></div>
<div class="metric"><span>Expected decision</span><strong>{html_escape(report.get('expected_decision'))}</strong></div>
<div class="metric"><span>Handoff ready</span><strong>{html_escape(report.get('handoff_ready'))}</strong></div>
<div class="metric"><span>Expected ready</span><strong>{html_escape(report.get('expected_handoff_ready'))}</strong></div>
<div class="metric"><span>Source handoff</span><strong>{html_escape(report.get('source_handoff'))}</strong></div>
<div class="metric"><span>Source loop report</span><strong>{html_escape(report.get('source_loop_report'))}</strong></div>
</div>
</section>
<section>
<h2>Issues</h2>
<ul>
{issue_items}
</ul>
</section>
</main>
</body>
</html>
"""


def write_baseline_candidate_handoff_check_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / HANDOFF_CHECK_JSON_FILENAME,
        "text": root / HANDOFF_CHECK_TEXT_FILENAME,
        "markdown": root / HANDOFF_CHECK_MARKDOWN_FILENAME,
        "html": root / HANDOFF_CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(render_baseline_candidate_handoff_check_text(report), encoding="utf-8")
    paths["markdown"].write_text(render_baseline_candidate_handoff_check_markdown(report), encoding="utf-8")
    paths["html"].write_text(render_baseline_candidate_handoff_check_html(report), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def embed_baseline_candidate_handoff_check(
    handoff: dict[str, Any],
    check: dict[str, Any],
    outputs: dict[str, str],
) -> dict[str, Any]:
    embedded = dict(handoff)
    embedded["handoff_check"] = {
        "schema_version": check.get("schema_version"),
        "status": check.get("status"),
        "decision": check.get("decision"),
        "failed_count": check.get("failed_count"),
        "source_handoff": check.get("source_handoff"),
        "source_loop_report": check.get("source_loop_report"),
        "handoff_decision": check.get("handoff_decision"),
        "expected_decision": check.get("expected_decision"),
        "handoff_ready": check.get("handoff_ready"),
        "expected_handoff_ready": check.get("expected_handoff_ready"),
    }
    embedded["handoff_check_outputs"] = dict(outputs)
    return embedded


def _issue(issue_id: str, field: str, expected: Any, actual: Any, detail: str) -> dict[str, Any]:
    return {
        "id": issue_id,
        "field": field,
        "expected": expected,
        "actual": actual,
        "detail": detail,
    }


def _field(payload: dict[str, Any], field: str) -> Any:
    value: Any = payload
    for part in field.split("."):
        value = as_dict(value).get(part)
    if field == "guardrails.rejected_reasons":
        return string_list(value)
    return value


def _issues(report: dict[str, Any]) -> list[dict[str, Any]]:
    value = report.get("issues")
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _resolve_maybe_relative(value: Any, base_dir: Path) -> Path | None:
    if value is None or value == "":
        return None
    path = Path(str(value))
    if path.is_absolute() or path.exists():
        return path
    return base_dir / path


__all__ = [
    "HANDOFF_CHECK_HTML_FILENAME",
    "HANDOFF_CHECK_JSON_FILENAME",
    "HANDOFF_CHECK_MARKDOWN_FILENAME",
    "HANDOFF_CHECK_TEXT_FILENAME",
    "build_baseline_candidate_handoff_check",
    "embed_baseline_candidate_handoff_check",
    "load_baseline_candidate_handoff",
    "render_baseline_candidate_handoff_check_html",
    "render_baseline_candidate_handoff_check_markdown",
    "render_baseline_candidate_handoff_check_text",
    "resolve_baseline_candidate_handoff",
    "write_baseline_candidate_handoff_check_outputs",
]
