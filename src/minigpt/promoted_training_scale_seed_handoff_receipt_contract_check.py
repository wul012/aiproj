from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.promoted_training_scale_seed_handoff_receipt_contract import (
    CONTRACT_SUMMARY_HTML_FILENAME,
    CONTRACT_SUMMARY_JSON_FILENAME,
    CONTRACT_SUMMARY_MARKDOWN_FILENAME,
    CONTRACT_SUMMARY_TEXT_FILENAME,
    build_promoted_training_scale_seed_handoff_receipt_contract_summary,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_html,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown,
    render_promoted_training_scale_seed_handoff_receipt_contract_summary_text,
)
from minigpt.report_utils import html_escape, string_list


CONTRACT_SUMMARY_CHECK_JSON_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.json"
CONTRACT_SUMMARY_CHECK_TEXT_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.txt"
CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.md"
CONTRACT_SUMMARY_CHECK_HTML_FILENAME = "promoted_training_scale_seed_handoff_receipt_contract_summary_check.html"

SUMMARY_COMPARE_KEYS = (
    "contract_summary_version",
    "status",
    "decision",
    "checker_exit_code",
    "handoff_report_path",
    "receipt_schema_version",
    "schema_v3_ready",
    "schema_v4_ready",
    "assurance_status",
    "embedded_receipt_check_status",
    "embedded_receipt_check_sidecar_status",
    "main_embedded_receipt_check_status",
    "receipt_check_output_json_exists",
    "receipt_check_output_text_exists",
    "suite_design_scopes",
    "ci_boundary_plan_check_scopes",
    "issue_count",
    "issues",
)


def check_promoted_training_scale_seed_handoff_receipt_contract_summary(
    summary_path: str | Path,
    *,
    handoff_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_summary_path = resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(summary_path)
    actual = load_promoted_training_scale_seed_handoff_receipt_contract_summary(resolved_summary_path)
    source_path = Path(handoff_path) if handoff_path is not None else _handoff_path_from_summary(actual)
    issues: list[str] = []
    expected: dict[str, Any] = {}
    if source_path is None:
        issues.append("handoff report path is required for receipt contract summary check")
    else:
        try:
            expected = build_promoted_training_scale_seed_handoff_receipt_contract_summary(source_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(f"could not rebuild receipt contract summary from handoff path: {exc}")
    if expected:
        issues.extend(_compare_summary_fields(expected, actual))
        sidecars = _check_summary_sidecars(resolved_summary_path.parent, expected)
    else:
        sidecars = _missing_sidecars(resolved_summary_path.parent)
    issues.extend(string_list(sidecars.get("issues")))
    status = "pass" if not issues else "fail"
    decision = str((expected or actual).get("decision") or "")
    return {
        "summary_check_version": 1,
        "status": status,
        "decision": decision,
        "checker_exit_code": 0 if status == "pass" and decision == "continue" else 1,
        "summary_path": str(resolved_summary_path),
        "handoff_path": str(source_path) if source_path is not None else None,
        "actual_summary_status": actual.get("status"),
        "expected_summary_status": expected.get("status") if expected else None,
        "actual_schema_version": actual.get("receipt_schema_version"),
        "expected_schema_version": expected.get("receipt_schema_version") if expected else None,
        "sidecar_status": sidecars.get("status"),
        "sidecar_issue_count": sidecars.get("issue_count"),
        "sidecar_issues": sidecars.get("issues"),
        "text_path": sidecars.get("text_path"),
        "text_exists": sidecars.get("text_exists"),
        "markdown_path": sidecars.get("markdown_path"),
        "markdown_exists": sidecars.get("markdown_exists"),
        "html_path": sidecars.get("html_path"),
        "html_exists": sidecars.get("html_exists"),
        "issue_count": len(issues),
        "issues": issues,
        "actual_summary": actual,
        "expected_summary": expected,
    }


def load_promoted_training_scale_seed_handoff_receipt_contract_summary(path: str | Path) -> dict[str, Any]:
    payload = json.loads(
        resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path).read_text(
            encoding="utf-8-sig"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("receipt contract summary must be a JSON object")
    return dict(payload)


def resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / CONTRACT_SUMMARY_JSON_FILENAME
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check: dict[str, Any]) -> str:
    rows = [
        ("receipt_contract_summary_check_status", check.get("status")),
        ("receipt_contract_summary_check_decision", check.get("decision")),
        ("receipt_contract_summary_check_checker_exit_code", check.get("checker_exit_code")),
        ("receipt_contract_summary_check_actual_status", check.get("actual_summary_status")),
        ("receipt_contract_summary_check_expected_status", check.get("expected_summary_status")),
        ("receipt_contract_summary_check_actual_schema_version", check.get("actual_schema_version")),
        ("receipt_contract_summary_check_expected_schema_version", check.get("expected_schema_version")),
        ("receipt_contract_summary_check_sidecar_status", check.get("sidecar_status")),
        ("receipt_contract_summary_check_issue_count", check.get("issue_count")),
        ("receipt_contract_summary_check_issues", json.dumps(check.get("issues"), ensure_ascii=False)),
    ]
    return "\n".join(f"{key}={value}" for key, value in rows) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check: dict[str, Any]) -> str:
    lines = [
        "# Promoted Seed Handoff Receipt Contract Summary Check",
        "",
        f"- Status: `{check.get('status')}`",
        f"- Decision: `{check.get('decision')}`",
        f"- Actual summary status: `{check.get('actual_summary_status')}`",
        f"- Expected summary status: `{check.get('expected_summary_status')}`",
        f"- Sidecar status: `{check.get('sidecar_status')}`",
        f"- Issue count: `{check.get('issue_count')}`",
        "",
        "## Sidecars",
        "",
        f"- Text exists: `{check.get('text_exists')}`",
        f"- Markdown exists: `{check.get('markdown_exists')}`",
        f"- HTML exists: `{check.get('html_exists')}`",
        "",
        "## Issues",
        "",
    ]
    issues = string_list(check.get("issues"))
    if not issues:
        lines.append("- none")
    else:
        lines.extend(f"- {issue}" for issue in issues)
    return "\n".join(lines) + "\n"


def render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check: dict[str, Any]) -> str:
    issues = string_list(check.get("issues"))
    issue_items = "\n".join(f"<li>{html_escape(issue)}</li>" for issue in issues) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>MiniGPT receipt contract summary check</title>
<style>
:root {{ font-family: Segoe UI, Arial, sans-serif; background: #f5f7f8; color: #172029; }}
body {{ margin: 0; padding: 28px; }}
main {{ max-width: 1040px; margin: 0 auto; }}
section {{ background: #fff; border: 1px solid #d7dee3; border-radius: 8px; padding: 16px; margin: 0 0 16px; }}
h1 {{ font-size: 28px; margin: 0 0 12px; letter-spacing: 0; }}
h2 {{ font-size: 18px; margin: 0 0 10px; letter-spacing: 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.metric {{ border: 1px solid #d7dee3; border-radius: 8px; padding: 10px; background: #fbfcfd; }}
.metric span {{ display: block; color: #5a6871; font-size: 12px; }}
.metric strong {{ display: block; margin-top: 6px; overflow-wrap: anywhere; }}
li {{ margin: 6px 0; }}
</style>
</head>
<body>
<main>
<h1>MiniGPT receipt contract summary check</h1>
<section>
<h2>Check</h2>
<div class="grid">
<div class="metric"><span>Status</span><strong>{html_escape(check.get('status'))}</strong></div>
<div class="metric"><span>Decision</span><strong>{html_escape(check.get('decision'))}</strong></div>
<div class="metric"><span>Actual</span><strong>{html_escape(check.get('actual_summary_status'))}</strong></div>
<div class="metric"><span>Expected</span><strong>{html_escape(check.get('expected_summary_status'))}</strong></div>
<div class="metric"><span>Sidecar</span><strong>{html_escape(check.get('sidecar_status'))}</strong></div>
<div class="metric"><span>Issues</span><strong>{html_escape(check.get('issue_count'))}</strong></div>
</div>
</section>
<section>
<h2>Sidecars</h2>
<ul>
<li>Text exists: {html_escape(check.get('text_exists'))}</li>
<li>Markdown exists: {html_escape(check.get('markdown_exists'))}</li>
<li>HTML exists: {html_escape(check.get('html_exists'))}</li>
</ul>
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


def write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs(
    check: dict[str, Any],
    out_dir: str | Path,
) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / CONTRACT_SUMMARY_CHECK_JSON_FILENAME,
        "text": root / CONTRACT_SUMMARY_CHECK_TEXT_FILENAME,
        "markdown": root / CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME,
        "html": root / CONTRACT_SUMMARY_CHECK_HTML_FILENAME,
    }
    paths["json"].write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths["text"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text(check),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown(check),
        encoding="utf-8",
    )
    paths["html"].write_text(
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html(check),
        encoding="utf-8",
    )
    return {key: str(value) for key, value in paths.items()}


def _handoff_path_from_summary(summary: dict[str, Any]) -> Path | None:
    value = summary.get("handoff_report_path")
    return Path(str(value)) if value else None


def _compare_summary_fields(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in SUMMARY_COMPARE_KEYS:
        expected_value = _stable_value(expected.get(key))
        actual_value = _stable_value(actual.get(key))
        if expected_value != actual_value:
            issues.append(f"summary.{key} expected {expected_value!r} but got {actual_value!r}")
    return issues


def _check_summary_sidecars(summary_dir: Path, expected: dict[str, Any]) -> dict[str, Any]:
    text_path = summary_dir / CONTRACT_SUMMARY_TEXT_FILENAME
    markdown_path = summary_dir / CONTRACT_SUMMARY_MARKDOWN_FILENAME
    html_path = summary_dir / CONTRACT_SUMMARY_HTML_FILENAME
    issues: list[str] = []
    _compare_file(text_path, render_promoted_training_scale_seed_handoff_receipt_contract_summary_text(expected), issues)
    _compare_file(
        markdown_path,
        render_promoted_training_scale_seed_handoff_receipt_contract_summary_markdown(expected),
        issues,
    )
    _compare_file(html_path, render_promoted_training_scale_seed_handoff_receipt_contract_summary_html(expected), issues)
    return _sidecar_payload(text_path, markdown_path, html_path, issues)


def _missing_sidecars(summary_dir: Path) -> dict[str, Any]:
    text_path = summary_dir / CONTRACT_SUMMARY_TEXT_FILENAME
    markdown_path = summary_dir / CONTRACT_SUMMARY_MARKDOWN_FILENAME
    html_path = summary_dir / CONTRACT_SUMMARY_HTML_FILENAME
    return _sidecar_payload(text_path, markdown_path, html_path, ["expected summary could not be rebuilt"])


def _compare_file(path: Path, expected_text: str, issues: list[str]) -> None:
    if not path.is_file():
        issues.append(f"{path.name} is missing")
        return
    try:
        actual = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        issues.append(f"{path.name} could not be read: {exc}")
        return
    if actual != expected_text:
        issues.append(f"{path.name} content does not match rebuilt contract summary")


def _sidecar_payload(text_path: Path, markdown_path: Path, html_path: Path, issues: list[str]) -> dict[str, Any]:
    return {
        "status": "pass" if not issues else "fail",
        "issue_count": len(issues),
        "issues": issues,
        "text_path": str(text_path),
        "text_exists": text_path.is_file(),
        "markdown_path": str(markdown_path),
        "markdown_exists": markdown_path.is_file(),
        "html_path": str(html_path),
        "html_exists": html_path.is_file(),
    }


def _stable_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return value


__all__ = [
    "CONTRACT_SUMMARY_CHECK_HTML_FILENAME",
    "CONTRACT_SUMMARY_CHECK_JSON_FILENAME",
    "CONTRACT_SUMMARY_CHECK_MARKDOWN_FILENAME",
    "CONTRACT_SUMMARY_CHECK_TEXT_FILENAME",
    "check_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "load_promoted_training_scale_seed_handoff_receipt_contract_summary",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_html",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_markdown",
    "render_promoted_training_scale_seed_handoff_receipt_contract_summary_check_text",
    "resolve_promoted_training_scale_seed_handoff_receipt_contract_summary_path",
    "write_promoted_training_scale_seed_handoff_receipt_contract_summary_check_outputs",
]
