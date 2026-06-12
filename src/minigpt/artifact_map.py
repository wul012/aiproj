from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import utc_now

DEFAULT_LIMIT = 12


def build_artifact_map_report(root: str | Path = ".", *, limit: int = DEFAULT_LIMIT, generated_at: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    evidence_root = project_root / "f"
    rows = _artifact_rows(evidence_root, limit=limit)
    missing_summary = [row for row in rows if not row["has_summary"]]
    missing_screenshot = [row for row in rows if int(row["screenshot_count"]) == 0]
    status = "pass" if not missing_summary and not missing_screenshot else "watch"
    return {
        "schema_version": 1,
        "title": "MiniGPT versioned artifact map v1134",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": "versioned_artifact_map_ready",
        "summary": {
            "status": status,
            "decision": "versioned_artifact_map_ready",
            "evidence_root": "f",
            "scanned_version_count": len(rows),
            "ready_version_count": len(rows) - len(set(row["version"] for row in missing_summary + missing_screenshot)),
            "missing_summary_count": len(missing_summary),
            "missing_screenshot_count": len(missing_screenshot),
            "limit": limit,
            "artifact_map_ready": True,
        },
        "rows": rows,
        "recommendations": [
            "Use this map before reviewing a version so screenshots, summaries, and machine-readable artifacts are found together.",
            "Keep JSON as the machine-readable source and screenshot as the browser-readability proof.",
            "Update docs/artifact-map.md when the evidence directory policy changes.",
        ],
        "csv_fieldnames": [
            "version",
            "evidence_dir",
            "has_summary",
            "screenshot_count",
            "report_dir_count",
            "json_count",
            "csv_count",
            "markdown_count",
            "html_count",
            "status",
            "recommendation",
        ],
    }


def write_artifact_map_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(
        report,
        out_dir,
        stem="versioned_artifact_map_v1134",
        row_title="Versioned Artifact Map",
    )


def resolve_exit_code(report: dict[str, Any], *, require_ready: bool = False, require_complete: bool = False) -> int:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    if require_ready and summary.get("artifact_map_ready") is not True:
        return 1
    if require_complete and report.get("status") != "pass":
        return 1
    return 0


def _artifact_rows(evidence_root: Path, *, limit: int) -> list[dict[str, Any]]:
    if not evidence_root.is_dir():
        return []
    versions = sorted(
        [path for path in evidence_root.iterdir() if path.is_dir() and path.name.isdigit()],
        key=lambda path: int(path.name),
        reverse=True,
    )[:limit]
    return [_version_row(path) for path in versions]


def _version_row(version_dir: Path) -> dict[str, Any]:
    explanation_dir = version_dir / "解释"
    image_dir = version_dir / "图片"
    has_summary = (explanation_dir / "说明.md").is_file()
    screenshot_count = len(list(image_dir.glob("*"))) if image_dir.is_dir() else 0
    report_dirs = [path for path in explanation_dir.iterdir() if path.is_dir()] if explanation_dir.is_dir() else []
    json_count = _count_files(report_dirs, "*.json")
    csv_count = _count_files(report_dirs, "*.csv")
    markdown_count = _count_files(report_dirs, "*.md")
    html_count = _count_files(report_dirs, "*.html")
    status = "pass" if has_summary and screenshot_count > 0 else "watch"
    return {
        "version": f"v{version_dir.name}",
        "evidence_dir": version_dir.as_posix(),
        "has_summary": has_summary,
        "screenshot_count": screenshot_count,
        "report_dir_count": len(report_dirs),
        "json_count": json_count,
        "csv_count": csv_count,
        "markdown_count": markdown_count,
        "html_count": html_count,
        "status": status,
        "recommendation": "ready" if status == "pass" else "add missing summary or screenshot",
    }


def _count_files(directories: list[Path], pattern: str) -> int:
    total = 0
    for directory in directories:
        total += len(list(directory.glob(pattern)))
    return total


__all__ = [
    "DEFAULT_LIMIT",
    "build_artifact_map_report",
    "resolve_exit_code",
    "write_artifact_map_outputs",
]
