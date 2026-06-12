from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import read_json_object, utc_now

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
REFACTOR_TERMS = ("dedup", "shared helper", "contract-preserving", "loader helper")
CADENCE_WATCH_STEM = "model_capability_cadence_watch_v1142"


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
    latest_version_number = int(str(rows[0].get("version", "v0")).removeprefix("v")) if rows else 0
    latest_refactor_version = _latest_category_version(rows, "refactor")
    latest_explanation_version = _latest_numbered_version(_explanation_paths(project_root))
    latest_evidence_version = _latest_evidence_version(project_root / "f")
    loop_due = _loop_execution_due(project_root)
    due = _due_items(
        non_capability_run=non_capability_run,
        max_non_capability_run=max_non_capability_run,
        latest_version_number=latest_version_number,
        latest_refactor_version=latest_refactor_version,
        latest_explanation_version=latest_explanation_version,
        latest_evidence_version=latest_evidence_version,
        loop_due=loop_due,
    )
    status = "pass" if non_capability_run <= max_non_capability_run else "watch"
    next_action = due[0]["action"] if due else ("continue_current_plan" if status == "pass" else "schedule_model_capability_regression")
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
            "latest_refactor_version": _format_version(latest_refactor_version),
            "versions_since_last_refactor": _versions_since(latest_version_number, latest_refactor_version),
            "latest_explanation_version": _format_version(latest_explanation_version),
            "versions_since_last_explanation": _versions_since(latest_version_number, latest_explanation_version),
            "latest_evidence_version": _format_version(latest_evidence_version),
            "versions_since_last_evidence": _versions_since(latest_version_number, latest_evidence_version),
            "due_count": len(due),
            "due_list": ", ".join(item["action"] for item in due) if due else "none",
            "next_action": next_action,
            "cadence_ready": True,
        },
        "rows": rows,
        "due": due,
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


def write_model_capability_cadence_watch_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    watch_report = {**report, "title": "MiniGPT model capability cadence watch v1142"}
    return write_readability_outputs(
        watch_report,
        out_dir,
        stem=CADENCE_WATCH_STEM,
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
    refactor_signal = _hits(lower, REFACTOR_TERMS)
    if refactor_signal:
        category = "refactor"
        recommendation = "counts as the latest contract-preserving maintenance slot"
    elif model_signal and len(model_signal) >= len(governance_signal):
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
        "refactor_signal": ", ".join(refactor_signal),
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


def _latest_category_version(rows: list[dict[str, Any]], category: str) -> int | None:
    for row in rows:
        if row.get("category") == category:
            return _version_number(row.get("version"))
    return None


def _latest_numbered_version(paths: list[Path]) -> int | None:
    versions: list[int] = []
    for path in paths:
        match = re.search(r"v(?P<version>[0-9]+)", path.name)
        if match:
            versions.append(int(match.group("version")))
    return max(versions) if versions else None


def _latest_evidence_version(root: Path) -> int | None:
    if not root.is_dir():
        return None
    versions = [int(path.name) for path in root.iterdir() if path.is_dir() and path.name.isdigit()]
    return max(versions) if versions else None


def _explanation_paths(root: Path) -> list[Path]:
    return [path for folder in root.glob("代码讲解记录_*") if folder.is_dir() for path in folder.glob("*.md")]


def _loop_execution_due(root: Path) -> bool:
    paths = list((root / "f" / "1141").glob("**/model_capability_regression_loop_trend_v1141.json"))
    if not paths:
        return False
    try:
        report = read_json_object(paths[0], description="model capability regression loop trend")
    except (OSError, ValueError):
        return False
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return summary.get("loop_closed") is True


def _due_items(
    *,
    non_capability_run: int,
    max_non_capability_run: int,
    latest_version_number: int,
    latest_refactor_version: int | None,
    latest_explanation_version: int | None,
    latest_evidence_version: int | None,
    loop_due: bool,
) -> list[dict[str, Any]]:
    due: list[dict[str, Any]] = []
    if loop_due:
        due.append(
            {
                "action": "run_selected_model_capability_regression_execution",
                "reason": "v1141 closed the v1135-v1139 preparation loop",
                "priority": "high",
            }
        )
    if non_capability_run > max_non_capability_run:
        due.append(
            {
                "action": "schedule_model_capability_regression",
                "reason": f"leading non-capability run {non_capability_run} exceeds limit {max_non_capability_run}",
                "priority": "high",
            }
        )
    if _versions_since(latest_version_number, latest_refactor_version) > 4:
        due.append({"action": "run_contract_preserving_refactor", "reason": "more than four versions since refactor", "priority": "medium"})
    if _versions_since(latest_version_number, latest_explanation_version) > 1:
        due.append({"action": "backfill_code_explanation", "reason": "latest explanation doc is behind current version", "priority": "medium"})
    if _versions_since(latest_version_number, latest_evidence_version) > 1:
        due.append({"action": "backfill_runtime_evidence", "reason": "latest f evidence folder is behind current version", "priority": "medium"})
    return due


def _versions_since(current: int, previous: int | None) -> int:
    if not current or previous is None:
        return 999
    return max(0, current - previous)


def _version_number(value: Any) -> int | None:
    match = re.match(r"v?(?P<version>[0-9]+)$", str(value))
    return int(match.group("version")) if match else None


def _format_version(value: int | None) -> str:
    return f"v{value}" if value is not None else "not_found"


def _recommendations(status: str, run: int, limit: int) -> list[str]:
    if status == "pass":
        return ["Current recent-version cadence still includes model capability evidence within the configured window."]
    return [
        f"Leading non-capability run is {run}, above the configured limit {limit}.",
        "Schedule a focused model capability regression after this maintenance batch.",
        "Candidate checks: holdout accuracy, required term coverage, loss signal bridge, unassisted repair, or decoder anchor distribution.",
    ]


__all__ = [
    "CADENCE_WATCH_STEM",
    "DEFAULT_MAX_NON_CAPABILITY_RUN",
    "build_model_capability_cadence_report",
    "resolve_exit_code",
    "write_model_capability_cadence_outputs",
    "write_model_capability_cadence_watch_outputs",
]
