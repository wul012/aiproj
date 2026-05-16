from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.dataset_card_artifacts import (
    render_dataset_card_html,
    render_dataset_card_markdown,
    write_dataset_card_html,
    write_dataset_card_json,
    write_dataset_card_markdown,
    write_dataset_card_outputs,
)
from minigpt.report_utils import (
    as_dict as _dict,
    utc_now,
)


DEFAULT_INTENDED_USE = [
    "Train and inspect tiny MiniGPT language-model experiments.",
    "Compare dataset versions, fingerprints, and quality warnings across runs.",
    "Support learning-oriented reproducibility reviews, not production data governance.",
]

DEFAULT_LIMITATIONS = [
    "Small local corpora may not represent broad language ability.",
    "Quality checks are lightweight heuristics and do not prove factual accuracy, consent, or safety.",
    "Source files and licenses must still be reviewed by the project owner before external sharing.",
]


def build_dataset_card(
    dataset_dir: str | Path,
    *,
    title: str = "MiniGPT dataset card",
    intended_use: list[str] | None = None,
    limitations: list[str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(dataset_dir)
    warnings: list[str] = []
    version = _read_json(root / "dataset_version.json", warnings)
    report = _read_json(root / "dataset_report.json", warnings)
    quality = _read_json(root / "dataset_quality.json", warnings)

    dataset = _dataset_section(version, root)
    summary = _summary_section(root, version, report, quality)
    provenance = _provenance_section(version, report)
    quality_section = _quality_section(quality)
    artifacts = _artifact_section(root)
    recommendations = _recommendations(summary, quality_section, artifacts, warnings)

    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "dataset_dir": str(root),
        "dataset": dataset,
        "summary": summary,
        "intended_use": intended_use or list(DEFAULT_INTENDED_USE),
        "limitations": limitations or list(DEFAULT_LIMITATIONS),
        "provenance": provenance,
        "quality": quality_section,
        "artifacts": artifacts,
        "recommendations": recommendations,
        "warnings": warnings,
    }


def _dataset_section(version: Any, root: Path) -> dict[str, Any]:
    dataset = _dict(_pick(version, "dataset"))
    name = dataset.get("name") or root.name
    version_id = dataset.get("version") or "unversioned"
    return {
        "name": name,
        "version": version_id,
        "id": dataset.get("id") or f"{name}@{version_id}",
        "description": dataset.get("description") or "",
    }


def _summary_section(root: Path, version: Any, report: Any, quality: Any) -> dict[str, Any]:
    stats = _dict(_pick(version, "stats"))
    version_quality = _dict(_pick(version, "quality"))
    outputs = _dict(_pick(version, "outputs"))
    fingerprint = (
        stats.get("fingerprint")
        or _pick(report, "fingerprint")
        or _pick(quality, "fingerprint")
    )
    quality_status = (
        version_quality.get("status")
        or _pick(quality, "status")
        or "missing"
    )
    warning_count = _first_number(version_quality.get("warning_count"), _pick(quality, "warning_count"))
    issue_count = _first_number(version_quality.get("issue_count"), _pick(quality, "issue_count"))
    text_output = outputs.get("text") or _pick(report, "output_text")
    return {
        "dataset_id": _pick(_dataset_section(version, root), "id"),
        "readiness_status": _readiness_status(quality_status, warning_count, issue_count),
        "quality_status": quality_status,
        "source_count": _first_number(stats.get("source_count"), _pick(report, "source_count"), _pick(quality, "source_count")),
        "char_count": _first_number(stats.get("char_count"), _pick(report, "char_count"), _pick(quality, "char_count")),
        "line_count": _first_number(stats.get("line_count"), _pick(report, "line_count"), _pick(quality, "line_count")),
        "unique_char_count": _first_number(stats.get("unique_char_count"), _pick(report, "unique_char_count"), _pick(quality, "unique_char_count")),
        "unique_char_ratio": _pick(quality, "unique_char_ratio"),
        "token_count_char_estimate": _first_number(stats.get("token_count_char_estimate"), _pick(report, "token_count_char_estimate")),
        "fingerprint": fingerprint,
        "short_fingerprint": stats.get("short_fingerprint") or (str(fingerprint)[:12] if fingerprint else None),
        "warning_count": warning_count,
        "issue_count": issue_count,
        "duplicate_line_count": _first_number(version_quality.get("duplicate_line_count"), _pick(quality, "duplicate_line_count")),
        "output_text": text_output,
        "output_text_exists": _path_exists(text_output),
        "version_manifest_exists": (root / "dataset_version.json").exists(),
        "report_exists": (root / "dataset_report.json").exists(),
        "quality_report_exists": (root / "dataset_quality.json").exists(),
        "version_html_exists": (root / "dataset_version.html").exists(),
    }


def _provenance_section(version: Any, report: Any) -> dict[str, Any]:
    preparation = _dict(_pick(version, "preparation"))
    outputs = _dict(_pick(version, "outputs"))
    version_sources = _list_of_dicts(_pick(version, "sources"))
    report_sources = _list_of_dicts(_pick(report, "sources"))
    return {
        "source_roots": _string_list(preparation.get("source_roots")),
        "recursive": preparation.get("recursive"),
        "output_name": preparation.get("output_name"),
        "output_text": outputs.get("text") or _pick(report, "output_text"),
        "sources": version_sources or report_sources,
    }


def _quality_section(quality: Any) -> dict[str, Any]:
    issues = _list_of_dicts(_pick(quality, "issues"))
    issue_codes = sorted({str(issue.get("code")) for issue in issues if issue.get("code")})
    severity_counts: dict[str, int] = {}
    for issue in issues:
        severity = str(issue.get("severity") or "unknown")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    return {
        "status": _pick(quality, "status") or "missing",
        "warning_count": _pick(quality, "warning_count"),
        "issue_count": _pick(quality, "issue_count"),
        "duplicate_line_count": _pick(quality, "duplicate_line_count"),
        "unique_char_ratio": _pick(quality, "unique_char_ratio"),
        "issue_codes": issue_codes,
        "severity_counts": severity_counts,
        "issues": issues[:24],
    }


def _artifact_section(root: Path) -> list[dict[str, Any]]:
    specs = [
        ("dataset_version", root / "dataset_version.json", "dataset version manifest"),
        ("dataset_version_html", root / "dataset_version.html", "browser dataset version report"),
        ("dataset_report", root / "dataset_report.json", "prepared dataset source report"),
        ("dataset_report_svg", root / "dataset_report.svg", "dataset source SVG summary"),
        ("dataset_quality", root / "dataset_quality.json", "dataset quality report"),
        ("dataset_quality_svg", root / "dataset_quality.svg", "dataset quality SVG summary"),
        ("corpus", root / "corpus.txt", "prepared training text"),
        ("dataset_card_json", root / "dataset_card.json", "machine-readable dataset card"),
        ("dataset_card_md", root / "dataset_card.md", "markdown dataset card"),
        ("dataset_card_html", root / "dataset_card.html", "browser dataset card"),
    ]
    return [
        {
            "key": key,
            "path": str(path),
            "exists": path.exists(),
            "description": description,
        }
        for key, path, description in specs
    ]


def _recommendations(
    summary: dict[str, Any],
    quality: dict[str, Any],
    artifacts: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    recs: list[str] = []
    if summary.get("readiness_status") == "ready":
        recs.append("Use this dataset card as the human-readable companion to dataset_version.json.")
    else:
        recs.append("Review dataset quality warnings before using this dataset for comparison runs.")
    if not summary.get("version_manifest_exists"):
        recs.append("Generate dataset_version.json so dataset identity and fingerprint are reproducible.")
    if not summary.get("quality_report_exists"):
        recs.append("Generate dataset_quality.json so warnings and duplicate-source checks are visible.")
    if _string_list(quality.get("issue_codes")):
        recs.append("Inspect quality issue codes: " + ", ".join(_string_list(quality.get("issue_codes"))) + ".")
    if not any(item.get("exists") and item.get("key") == "corpus" for item in artifacts):
        recs.append("Keep the prepared corpus path in outputs so training scripts can trace the data source.")
    if warnings:
        recs.append("Resolve missing or invalid dataset evidence files listed in warnings.")
    return recs


def _readiness_status(quality_status: Any, warning_count: Any, issue_count: Any) -> str:
    if quality_status == "pass":
        return "ready"
    if quality_status == "warn" or (warning_count or 0) or (issue_count or 0):
        return "review"
    return "incomplete"


def _read_json(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        warnings.append(f"missing: {path}")
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        warnings.append(f"{path} must contain a JSON object")
        return None
    return payload


def _path_exists(path: Any) -> bool:
    if path in (None, ""):
        return False
    return Path(str(path)).exists()


def _first_number(*values: Any) -> int | float | None:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
