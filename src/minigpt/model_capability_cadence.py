from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

DEFAULT_MAX_NON_CAPABILITY_RUN = 4
MODEL_TERMS = (
    "training run",
    "benchmark scorecard",
    "benchmark suite",
    "required term",
    "loss signal",
    "decoder",
    "unassisted repair",
    "exact surface",
    "capacity probe",
)
GOVERNANCE_TERMS = ("receipt", "contract check", "index", "review", "lookup-only", "publication")
MAINTENANCE_TERMS = ("readability", "docs", "template", "maintenance", "script layer")


def build_model_capability_cadence_report(
    root: str | Path = ".",
    *,
    max_non_capability_run: int = DEFAULT_MAX_NON_CAPABILITY_RUN,
    generated_at: str | None = None,
) -> dict[str, Any]:
    project_root = Path(root)
    sections = _latest_sections(project_root / "README.md")
    rows = [_classify_section(version, body) for version, body in sections]
    non_capability_run = _leading_non_capability_run(rows)
    status = "pass" if non_capability_run <= max_non_capability_run else "watch"
    next_action = "continue_current_plan" if status == "pass" else "schedule_model_capability_regression"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability cadence v1133",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "model_capability_cadence_ready",
        "summary": {
            "status": status,
            "decision": "model_capability_cadence_ready",
            "scanned_version_count": len(rows),
            "leading_non_capability_run": non_capability_run,
            "max_non_capability_run": max_non_capability_run,
            "latest_model_capability_version": _latest_capability_version(rows),
            "next_action": next_action,
            "cadence_ready": True,
        },
        "rows": rows,
        "recommendations": _recommendations(status, non_capability_run, max_non_capability_run),
        "csv_fieldnames": ["version", "category", "model_signal", "governance_signal", "maintenance_signal", "status", "recommendation"],
    }


def write_model_capability_cadence_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem="model_capability_cadence_v1133",
        row_title="Recent Version Cadence",
    )


def resolve_exit_code(report: dict[str, Any], *, require_ready: bool = False, require_within_cadence: bool = False) -> int:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    if require_ready and summary.get("cadence_ready") is not True:
        return 1
    if require_within_cadence and report.get("status") != "pass":
        return 1
    return 0


def _latest_sections(readme_path: Path, *, limit: int = 12) -> list[tuple[str, str]]:
    if not readme_path.is_file():
        return []
    text = readme_path.read_text(encoding="utf-8-sig")
    pattern = re.compile(r"^## Latest v(?P<version>[0-9]+) checkpoint\n(?P<body>.*?)(?=^## Latest v|\Z)", re.M | re.S)
    sections = [(match.group("version"), match.group("body")) for match in pattern.finditer(text)]
    return sections[:limit]


def _classify_section(version: str, body: str) -> dict[str, Any]:
    lower = body.lower()
    model_signal = _hits(lower, MODEL_TERMS)
    governance_signal = _hits(lower, GOVERNANCE_TERMS)
    maintenance_signal = _hits(lower, MAINTENANCE_TERMS)
    if model_signal and len(model_signal) >= len(governance_signal):
        category = "model-capability"
        recommendation = "keep as cadence anchor"
    elif maintenance_signal:
        category = "maintenance"
        recommendation = "batch with readability care and schedule model capability follow-up"
    elif governance_signal:
        category = "governance"
        recommendation = "keep lookup-only boundaries explicit"
    else:
        category = "unknown"
        recommendation = "review version category"
    return {
        "version": f"v{version}",
        "category": category,
        "model_signal": ", ".join(model_signal),
        "governance_signal": ", ".join(governance_signal),
        "maintenance_signal": ", ".join(maintenance_signal),
        "status": "pass" if category != "unknown" else "watch",
        "recommendation": recommendation,
    }


def _hits(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def _leading_non_capability_run(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        if row.get("category") == "model-capability":
            break
        count += 1
    return count


def _latest_capability_version(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("category") == "model-capability":
            return str(row.get("version"))
    return "not_found_in_recent_window"


def _recommendations(status: str, run: int, limit: int) -> list[str]:
    if status == "pass":
        return ["Current recent-version cadence still includes model capability evidence within the configured window."]
    return [
        f"Leading non-capability run is {run}, above the configured limit {limit}.",
        "Schedule a focused model capability regression after this maintenance batch.",
        "Candidate checks: holdout accuracy, required term coverage, loss signal bridge, unassisted repair, or decoder anchor distribution.",
    ]


__all__ = [
    "DEFAULT_MAX_NON_CAPABILITY_RUN",
    "build_model_capability_cadence_report",
    "resolve_exit_code",
    "write_model_capability_cadence_outputs",
]
