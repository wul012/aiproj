from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import html
import json
from pathlib import Path
from typing import Any

from .data_prep import PreparedDataset


@dataclass(frozen=True)
class DatasetQualityIssue:
    severity: str
    code: str
    message: str
    path: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dataset_quality_report(
    dataset: PreparedDataset,
    *,
    min_total_chars: int = 200,
    min_source_chars: int = 20,
    low_unique_ratio: float = 0.08,
    duplicate_line_min_length: int = 10,
) -> dict[str, Any]:
    issues: list[DatasetQualityIssue] = []
    if dataset.char_count < min_total_chars:
        issues.append(
            DatasetQualityIssue(
                severity="warning",
                code="small_dataset",
                message=f"Dataset has {dataset.char_count} characters; consider using at least {min_total_chars}.",
                details={"char_count": dataset.char_count, "min_total_chars": min_total_chars},
            )
        )

    unique_ratio = 0.0 if dataset.char_count == 0 else dataset.unique_char_count / dataset.char_count
    if dataset.char_count > 0 and unique_ratio < low_unique_ratio:
        issues.append(
            DatasetQualityIssue(
                severity="warning",
                code="low_unique_ratio",
                message="Unique-character ratio is low; the corpus may contain too much repetition.",
                details={"unique_ratio": round(unique_ratio, 6), "threshold": low_unique_ratio},
            )
        )

    seen_sources: dict[str, str] = {}
    source_rows = []
    for source in dataset.sources:
        duplicate_of = seen_sources.get(source.sha256)
        if source.char_count == 0:
            issues.append(
                DatasetQualityIssue(
                    severity="warning",
                    code="empty_source",
                    message="Source is empty after normalization.",
                    path=source.path,
                )
            )
        elif source.char_count < min_source_chars:
            issues.append(
                DatasetQualityIssue(
                    severity="warning",
                    code="tiny_source",
                    message=f"Source has only {source.char_count} characters.",
                    path=source.path,
                    details={"char_count": source.char_count, "min_source_chars": min_source_chars},
                )
            )
        if duplicate_of is not None and source.char_count > 0:
            issues.append(
                DatasetQualityIssue(
                    severity="warning",
                    code="duplicate_source",
                    message="Source content duplicates another file.",
                    path=source.path,
                    details={"duplicate_of": duplicate_of, "sha256": source.sha256},
                )
            )
        elif source.char_count > 0:
            seen_sources[source.sha256] = source.path
        source_rows.append(
            {
                "path": source.path,
                "char_count": source.char_count,
                "line_count": source.line_count,
                "sha256": source.sha256,
                "duplicate_of": duplicate_of,
            }
        )

    duplicate_lines = _find_duplicate_lines(dataset.text, min_length=duplicate_line_min_length)
    for line, count in duplicate_lines[:8]:
        issues.append(
            DatasetQualityIssue(
                severity="info",
                code="repeated_line",
                message="A normalized line appears multiple times.",
                details={"count": count, "line": line},
            )
        )

    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    return {
        "schema_version": 1,
        "status": "warn" if warning_count else "pass",
        "fingerprint": sha256_text(dataset.text),
        "short_fingerprint": sha256_text(dataset.text)[:12],
        "char_count": dataset.char_count,
        "line_count": dataset.line_count,
        "unique_char_count": dataset.unique_char_count,
        "unique_char_ratio": round(unique_ratio, 6),
        "source_count": len(dataset.sources),
        "issue_count": len(issues),
        "warning_count": warning_count,
        "duplicate_line_count": len(duplicate_lines),
        "sources": source_rows,
        "issues": [issue.to_dict() for issue in issues],
    }


def write_dataset_quality_json(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def write_dataset_quality_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    issues = list(report.get("issues", []))
    width = 980
    row_h = 32
    height = 210 + max(1, min(len(issues), 8)) * row_h
    status_color = "#047857" if report.get("status") == "pass" else "#b45309"
    cards = [
        ("Status", report.get("status")),
        ("Fingerprint", report.get("short_fingerprint")),
        ("Sources", report.get("source_count")),
        ("Warnings", report.get("warning_count")),
        ("Unique ratio", report.get("unique_char_ratio")),
    ]
    card_svg = []
    for index, (label, value) in enumerate(cards):
        x = 28 + index * 184
        card_svg.append(f'<rect x="{x}" y="74" width="164" height="58" rx="8" fill="#ffffff" stroke="#d1d5db"/>')
        card_svg.append(f'<text x="{x + 12}" y="96" font-family="Arial" font-size="11" fill="#6b7280">{_e(label)}</text>')
        card_svg.append(f'<text x="{x + 12}" y="120" font-family="Arial" font-size="15" fill="{status_color if label == "Status" else "#111827"}">{_e(_clip(value, 18))}</text>')
    issue_rows = []
    for index, issue in enumerate(issues[:8]):
        y = 176 + index * row_h
        severity = str(issue.get("severity", "info"))
        color = "#b45309" if severity == "warning" else "#2563eb"
        issue_rows.append(f'<circle cx="40" cy="{y - 4}" r="5" fill="{color}"/>')
        issue_rows.append(
            f'<text x="56" y="{y}" font-family="Arial" font-size="13" fill="#111827">'
            f'{_e(issue.get("code"))}: {_e(_clip(issue.get("message"), 90))}</text>'
        )
    if not issue_rows:
        issue_rows.append('<text x="36" y="176" font-family="Arial" font-size="13" fill="#047857">No quality issues found.</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="28" y="36" font-family="Arial" font-size="22" fill="#111827">MiniGPT dataset quality</text>
  <text x="28" y="58" font-family="Arial" font-size="13" fill="#4b5563">Fingerprint and lightweight corpus quality checks.</text>
  {''.join(card_svg)}
  <text x="28" y="154" font-family="Arial" font-size="16" fill="#111827">Issues</text>
  {''.join(issue_rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_duplicate_lines(text: str, min_length: int) -> list[tuple[str, int]]:
    counts = Counter(line.strip() for line in text.splitlines() if len(line.strip()) >= min_length)
    return sorted(((line, count) for line, count in counts.items() if count > 1), key=lambda item: (-item[1], item[0]))


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
