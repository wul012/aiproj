from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    markdown_cell,
    utc_now,
    write_json_payload,
    write_output_bundle,
)

DEFAULT_FINAL_EVIDENCE_PATH = Path("docs") / "aiproj-track-final-evidence.md"


@dataclass(frozen=True)
class TrackEvidenceDoc:
    track_id: str
    path: str
    expected_terms: tuple[str, ...]


TRACK_EVIDENCE_DOCS = (
    TrackEvidenceDoc(
        "A0",
        "docs/aiproj-track-a0-census.md",
        ("archive + `runs/` inventory", "f/1260", "no training"),
    ),
    TrackEvidenceDoc(
        "A1",
        "docs/aiproj-track-a1-static-analysis.md",
        ("scripts/check_static_analysis.py", "scripts/check_type_analysis.py", "f/1261", "f/1262"),
    ),
    TrackEvidenceDoc(
        "A2",
        "docs/aiproj-track-a2-coverage.md",
        ("fail_under = 88.98", "scripts/run_test_coverage.py", "coverage-floor.json"),
    ),
    TrackEvidenceDoc(
        "A3-honest-measurement",
        "docs/aiproj-track-a3-honest-measurement.md",
        ("scripts/check_model_capability_honest_measurement.py", "no-promotion", "tests/"),
    ),
    TrackEvidenceDoc(
        "A3-artifact-schema",
        "docs/aiproj-track-a3-artifact-schema-guard.md",
        ("scripts/check_artifact_schema_guard.py", "docs/artifact-schema-guard-registry.json", "f/1265"),
    ),
    TrackEvidenceDoc(
        "A4",
        "docs/aiproj-track-a4-code-health.md",
        ("scripts/check_file_size_ratchet.py", "docs/code-health/file-size-ratchet.json", "waiver"),
    ),
)

FINAL_EVIDENCE_TERMS = (
    "A0",
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "docs/aiproj-track-a0-census.md",
    "docs/aiproj-track-a1-static-analysis.md",
    "docs/aiproj-track-a2-coverage.md",
    "docs/aiproj-track-a3-honest-measurement.md",
    "docs/aiproj-track-a3-artifact-schema-guard.md",
    "docs/aiproj-track-a4-code-health.md",
    "docs/no-promotion-boundary.md",
    "https://github.com/wul012/aiproj/actions/runs/28846542546",
    "https://github.com/wul012/aiproj/actions/runs/28846544549",
)

NO_PROMOTION_TERMS = (
    "promotion_ready=False",
    "approved_for_promotion=False",
    "model_quality_claim",
    "lookup-only",
    "does not automatically mean",
)

DOC_INDEX_TERMS = (
    ("README.md", "docs/aiproj-track-final-evidence.md"),
    ("docs/README.md", "aiproj-track-final-evidence.md"),
    ("START_HERE.md", "docs/aiproj-track-final-evidence.md"),
    ("docs/script-entrypoints.md", "scripts/check_aiproj_track_closeout.py"),
)

CI_COMMAND_TERMS = (
    "scripts/check_static_analysis.py",
    "scripts/check_type_analysis.py",
    "scripts/check_model_capability_honest_measurement.py",
    "scripts/check_artifact_schema_guard.py",
    "scripts/check_file_size_ratchet.py",
    "scripts/check_aiproj_track_closeout.py",
    "scripts/run_test_coverage.py --out-dir runs/test-coverage-ci --fail-under 88.98",
)


def build_aiproj_track_closeout_report(
    final_evidence_path: str | Path = DEFAULT_FINAL_EVIDENCE_PATH,
    *,
    project_root: str | Path = ".",
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    evidence_path = _resolve_inside_root(final_evidence_path, root)
    checks = _build_checks(root, evidence_path)
    failed = [item for item in checks if item["status"] != "pass"]
    status = "pass" if not failed else "fail"
    decision = "aiproj_track_closeout_ready" if status == "pass" else "repair_aiproj_track_closeout"
    return {
        "schema_version": 1,
        "title": "MiniGPT aiproj production-excellence closeout",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "final_evidence_path": _relative_path(evidence_path, root),
        "summary": {
            "status": status,
            "decision": decision,
            "evidence_doc_count": len(TRACK_EVIDENCE_DOCS),
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_count": len(failed),
            "no_promotion_boundary_ready": _checks_with_prefix_pass(checks, "no_promotion:"),
            "final_evidence_ready": _checks_with_prefix_pass(checks, "final_evidence:"),
            "ci_closeout_gate_ready": _check_passed(checks, "ci:command:scripts/check_aiproj_track_closeout.py"),
        },
        "evidence_docs": [
            {"track_id": item.track_id, "path": item.path, "expected_terms": list(item.expected_terms)}
            for item in TRACK_EVIDENCE_DOCS
        ],
        "checks": checks,
        "recommendations": _recommendations(failed),
    }


def write_aiproj_track_closeout_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    def write_markdown(path: Path) -> None:
        path.write_text(render_aiproj_track_closeout_markdown(report), encoding="utf-8")

    def write_html(path: Path) -> None:
        path.write_text(render_aiproj_track_closeout_html(report), encoding="utf-8")

    return write_output_bundle(
        out_dir,
        {
            "json": "aiproj_track_closeout.json",
            "csv": "aiproj_track_closeout.csv",
            "markdown": "aiproj_track_closeout.md",
            "html": "aiproj_track_closeout.html",
        },
        {
            "json": lambda path: write_json_payload(report, path),
            "csv": lambda path: _write_csv(report, path),
            "markdown": write_markdown,
            "html": write_html,
        },
    )


def render_aiproj_track_closeout_markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# MiniGPT aiproj Production-Excellence Closeout",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Final evidence: `{report.get('final_evidence_path')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in (
        "evidence_doc_count",
        "check_count",
        "passed_check_count",
        "failed_check_count",
        "no_promotion_boundary_ready",
        "final_evidence_ready",
        "ci_closeout_gate_ready",
    ):
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(summary.get(key))} |")
    lines.extend(
        ["", "## Checks", "", "| ID | Target | Expected | Actual | Status |", "| --- | --- | --- | --- | --- |"]
    )
    for item in _checks(report):
        lines.append(
            "| "
            + " | ".join(
                markdown_cell(item.get(field)) for field in ("check_id", "target", "expected", "actual", "status")
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_aiproj_track_closeout_html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    rows = "".join(
        "<tr>"
        f"<td>{html_escape(item.get('check_id'))}</td>"
        f"<td>{html_escape(item.get('target'))}</td>"
        f"<td>{html_escape(item.get('expected'))}</td>"
        f"<td>{html_escape(item.get('actual'))}</td>"
        f"<td>{html_escape(item.get('status'))}</td>"
        "</tr>"
        for item in _checks(report)
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MiniGPT aiproj closeout</title><style>
body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f6f7f9;color:#172026;margin:0}}
main{{max-width:1120px;margin:auto;padding:28px}}header,.panel{{background:white;border:1px solid #d8dee4;border-radius:8px;padding:18px;margin-bottom:14px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}.stat{{background:#eef2f6;padding:12px;border-radius:6px}}
table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<header><h1>MiniGPT aiproj production-excellence closeout</h1><p>Status: <strong>{html_escape(report.get("status"))}</strong> | Decision: <code>{html_escape(report.get("decision"))}</code></p><p>Final evidence: <code>{html_escape(report.get("final_evidence_path"))}</code></p></header>
<section class="panel stats"><div class="stat">Checks<br><strong>{html_escape(summary.get("check_count"))}</strong></div><div class="stat">Failures<br><strong>{html_escape(summary.get("failed_check_count"))}</strong></div><div class="stat">No-promotion<br><strong>{html_escape(summary.get("no_promotion_boundary_ready"))}</strong></div><div class="stat">CI closeout<br><strong>{html_escape(summary.get("ci_closeout_gate_ready"))}</strong></div></section>
<section class="panel"><h2>Checks</h2><table><thead><tr><th>ID</th><th>Target</th><th>Expected</th><th>Actual</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table></section>
</main></body></html>"""


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    return 0 if not require_pass or report.get("status") == "pass" else 1


def _build_checks(root: Path, final_evidence_path: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for doc in TRACK_EVIDENCE_DOCS:
        path = _resolve_inside_root(doc.path, root)
        checks.append(_check(f"evidence_doc_exists:{doc.track_id}", doc.path, "file exists", path.is_file()))
        text = _read_text(path)
        for term in doc.expected_terms:
            checks.append(_check(f"evidence_doc_term:{doc.track_id}:{term}", doc.path, term, term in text))
    final_text = _read_text(final_evidence_path)
    checks.append(
        _check(
            "final_evidence:exists",
            _relative_path(final_evidence_path, root),
            "file exists",
            final_evidence_path.is_file(),
        )
    )
    for term in FINAL_EVIDENCE_TERMS:
        checks.append(
            _check(f"final_evidence:term:{term}", _relative_path(final_evidence_path, root), term, term in final_text)
        )
    no_promotion = root / "docs" / "no-promotion-boundary.md"
    no_promotion_text = _read_text(no_promotion)
    for term in NO_PROMOTION_TERMS:
        checks.append(
            _check(f"no_promotion:term:{term}", "docs/no-promotion-boundary.md", term, term in no_promotion_text)
        )
    for doc_path, term in DOC_INDEX_TERMS:
        text = _read_text(root / doc_path)
        checks.append(_check(f"doc_index:{doc_path}:{term}", doc_path, term, term in text))
    workflow_text = _read_text(root / ".github" / "workflows" / "ci.yml")
    for term in CI_COMMAND_TERMS:
        checks.append(_check(f"ci:command:{term}", ".github/workflows/ci.yml", term, term in workflow_text))
    return checks


def _check(check_id: str, target: str, expected: str, passed: bool) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "target": target,
        "expected": expected,
        "actual": "present" if passed else "missing",
        "status": "pass" if passed else "fail",
    }


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fieldnames = ["check_id", "target", "expected", "actual", "status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in _checks(report):
            writer.writerow({field: csv_cell(item.get(field)) for field in fieldnames})


def _checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get("checks"))


def _checks_with_prefix_pass(checks: list[dict[str, Any]], prefix: str) -> bool:
    items = [item for item in checks if str(item.get("check_id", "")).startswith(prefix)]
    return bool(items) and all(item.get("status") == "pass" for item in items)


def _check_passed(checks: list[dict[str, Any]], check_id: str) -> bool:
    return any(item.get("check_id") == check_id and item.get("status") == "pass" for item in checks)


def _recommendations(failed_checks: list[dict[str, Any]]) -> list[str]:
    if not failed_checks:
        return ["Keep A-track closeout evidence cited, indexed, and enforced before starting Stage 2 work."]
    return ["Repair missing A-track evidence citations, no-promotion wording, or CI closeout gate wiring."]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _resolve_inside_root(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes project root: {path}") from exc
    return resolved


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "DEFAULT_FINAL_EVIDENCE_PATH",
    "build_aiproj_track_closeout_report",
    "render_aiproj_track_closeout_html",
    "render_aiproj_track_closeout_markdown",
    "resolve_exit_code",
    "write_aiproj_track_closeout_outputs",
]
