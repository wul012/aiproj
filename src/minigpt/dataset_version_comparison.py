from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    list_of_strs as _list_of_strs,
    markdown_cell as _md,
    number_or_default,
    utc_now,
    write_json_payload,
)


@dataclass(frozen=True)
class DatasetVersionSummary:
    name: str
    path: str
    dataset_id: str | None
    dataset_name: str | None
    dataset_version: str | None
    created_at: str | None
    fingerprint: str | None
    short_fingerprint: str | None
    source_count: int
    included_source_count: int
    skipped_source_count: int
    char_count: int
    line_count: int
    unique_char_count: int
    quality_status: str | None
    warning_count: int
    issue_count: int
    duplicate_line_count: int
    dedupe_policy: str
    source_order_digest: str | None
    source_root_count: int
    output_name: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_dataset_version(path: str | Path, name: str | None = None) -> DatasetVersionSummary:
    source = _resolve_dataset_version_path(path)
    payload = _read_json(source)
    dataset = _dict(payload.get("dataset"))
    stats = _dict(payload.get("stats"))
    quality = _dict(payload.get("quality"))
    preparation = _dict(payload.get("preparation"))
    snapshot = _dict(payload.get("snapshot"))
    fingerprint = _as_str(stats.get("fingerprint"))
    short_fingerprint = _as_str(stats.get("short_fingerprint") or (fingerprint[:12] if fingerprint else None))
    dedupe_policy = _as_str(snapshot.get("dedupe_policy") or ("exact-source-content" if preparation.get("dedupe_exact_sources") else "none"))
    return DatasetVersionSummary(
        name=name or source.parent.name,
        path=str(source),
        dataset_id=_as_str(dataset.get("id")),
        dataset_name=_as_str(dataset.get("name")),
        dataset_version=_as_str(dataset.get("version")),
        created_at=_as_str(payload.get("created_at")),
        fingerprint=fingerprint,
        short_fingerprint=short_fingerprint,
        source_count=_as_int(stats.get("source_count")),
        included_source_count=_as_int(stats.get("included_source_count") or stats.get("source_count")),
        skipped_source_count=_as_int(stats.get("skipped_source_count")),
        char_count=_as_int(stats.get("char_count")),
        line_count=_as_int(stats.get("line_count")),
        unique_char_count=_as_int(stats.get("unique_char_count")),
        quality_status=_as_str(quality.get("status")),
        warning_count=_as_int(quality.get("warning_count")),
        issue_count=_as_int(quality.get("issue_count")),
        duplicate_line_count=_as_int(quality.get("duplicate_line_count")),
        dedupe_policy=dedupe_policy or "none",
        source_order_digest=_as_str(snapshot.get("source_order_digest")),
        source_root_count=len(_list_of_strs(preparation.get("source_roots"))),
        output_name=_as_str(preparation.get("output_name")),
    )


def build_dataset_version_comparison(
    paths: list[str | Path],
    *,
    names: list[str] | None = None,
    baseline: str | int | None = None,
    generated_at: str | None = None,
    title: str = "MiniGPT dataset version comparison",
) -> dict[str, Any]:
    if not paths:
        raise ValueError("At least one dataset version path or directory is required")
    if names is not None and len(names) != len(paths):
        raise ValueError("names length must match paths length")
    versions = [
        summarize_dataset_version(path, name=None if names is None else names[index])
        for index, path in enumerate(paths)
    ]
    baseline_version = _select_baseline(versions, baseline)
    deltas = [_baseline_delta(version, baseline_version) for version in versions]
    summary = _comparison_summary(versions, baseline_version, deltas)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "version_count": len(versions),
        "baseline": baseline_version.to_dict(),
        "versions": [version.to_dict() for version in versions],
        "baseline_deltas": deltas,
        "summary": summary,
        "recommendations": _recommendations(versions, summary),
    }


def write_dataset_version_comparison_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_dataset_version_comparison_csv(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    fieldnames = [
        "name",
        "dataset_id",
        "path",
        "short_fingerprint",
        "source_count",
        "included_source_count",
        "skipped_source_count",
        "char_count",
        "quality_status",
        "dedupe_policy",
        "source_order_digest",
        "baseline_name",
        "is_baseline",
        "fingerprint_changed",
        "dedupe_policy_changed",
        "source_order_changed",
        "source_count_delta",
        "included_source_count_delta",
        "skipped_source_count_delta",
        "char_count_delta",
        "warning_count_delta",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for version in _list_of_dicts(report.get("versions")):
            row = dict(version)
            row.update(deltas.get(version.get("path"), {}))
            writer.writerow({field: row.get(field) for field in fieldnames})


def render_dataset_version_comparison_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    lines = [
        f"# {report.get('title', 'MiniGPT dataset version comparison')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Baseline: `{baseline.get('name')}`",
        f"- Versions: `{report.get('version_count')}`",
        f"- Fingerprints: `{summary.get('fingerprint_count')}`",
        f"- Dedupe policies: `{summary.get('dedupe_policy_count')}`",
        "",
        "| Version | Dataset | Fingerprint | Sources | Included | Skipped | Chars | Dedupe | Changed |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for version in _list_of_dicts(report.get("versions")):
        delta = deltas.get(version.get("path"), {})
        changed = _change_label(delta)
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(version.get("name")),
                    _md(version.get("dataset_id")),
                    _md(version.get("short_fingerprint")),
                    _md(version.get("source_count")),
                    _md(version.get("included_source_count")),
                    _md(version.get("skipped_source_count")),
                    _md(version.get("char_count")),
                    _md(version.get("dedupe_policy")),
                    _md(changed),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _list_of_strs(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def render_dataset_version_comparison_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    baseline = _dict(report.get("baseline"))
    deltas = {row.get("path"): row for row in _list_of_dicts(report.get("baseline_deltas"))}
    stats = [
        ("Baseline", baseline.get("name")),
        ("Versions", report.get("version_count")),
        ("Fingerprints", summary.get("fingerprint_count")),
        ("Datasets", summary.get("dataset_id_count")),
        ("Dedupe policies", summary.get("dedupe_policy_count")),
        ("Changed fingerprints", summary.get("changed_fingerprint_count")),
        ("Changed dedupe", summary.get("changed_dedupe_policy_count")),
        ("Changed order", summary.get("changed_source_order_count")),
    ]
    rows = []
    for version in _list_of_dicts(report.get("versions")):
        delta = deltas.get(version.get("path"), {})
        changed = _change_label(delta)
        label_class = "baseline" if delta.get("is_baseline") else "changed" if changed != "none" else "same"
        rows.append(
            "<tr>"
            f"<td><strong>{_e(version.get('name'))}</strong><br><span>{_e(version.get('path'))}</span></td>"
            f"<td>{_e(version.get('dataset_id'))}<br><span>{_e(version.get('created_at'))}</span></td>"
            f"<td>{_e(version.get('short_fingerprint'))}<br><span>{_e(version.get('source_order_digest'))}</span></td>"
            f"<td>{_e(version.get('source_count'))}<br><span>{_e(_fmt_signed(delta.get('source_count_delta')))}</span></td>"
            f"<td>{_e(version.get('included_source_count'))}<br><span>{_e(_fmt_signed(delta.get('included_source_count_delta')))}</span></td>"
            f"<td>{_e(version.get('skipped_source_count'))}<br><span>{_e(_fmt_signed(delta.get('skipped_source_count_delta')))}</span></td>"
            f"<td>{_e(version.get('char_count'))}<br><span>{_e(_fmt_signed(delta.get('char_count_delta')))}</span></td>"
            f"<td>{_e(version.get('quality_status'))}<br><span>warn { _e(version.get('warning_count')) }</span></td>"
            f"<td>{_e(version.get('dedupe_policy'))}</td>"
            f'<td><span class="pill {label_class}">{_e(changed if not delta.get("is_baseline") else "baseline")}</span></td>'
            "</tr>"
        )
    recommendations = "".join(f"<li>{_e(item)}</li>" for item in _list_of_strs(report.get("recommendations")))
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT dataset version comparison'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT dataset version comparison'))}</h1><p>Baseline: {_e(baseline.get('name'))}; generated at {_e(report.get('generated_at'))}.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            '<section><h2>Dataset Versions</h2><table><thead><tr><th>Version</th><th>Dataset</th><th>Fingerprint</th><th>Sources</th><th>Included</th><th>Skipped</th><th>Chars</th><th>Quality</th><th>Dedupe</th><th>Change</th></tr></thead><tbody>',
            "".join(rows),
            "</tbody></table></section>",
            "<section><h2>Recommendations</h2><ul>" + recommendations + "</ul></section>",
            "<footer>Generated by MiniGPT dataset version comparison.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_dataset_version_comparison_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dataset_version_comparison_markdown(report), encoding="utf-8")


def write_dataset_version_comparison_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_dataset_version_comparison_html(report), encoding="utf-8")


def write_dataset_version_comparison_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "dataset_version_comparison.json",
        "csv": root / "dataset_version_comparison.csv",
        "markdown": root / "dataset_version_comparison.md",
        "html": root / "dataset_version_comparison.html",
    }
    write_dataset_version_comparison_json(report, paths["json"])
    write_dataset_version_comparison_csv(report, paths["csv"])
    write_dataset_version_comparison_markdown(report, paths["markdown"])
    write_dataset_version_comparison_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _resolve_dataset_version_path(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / "dataset_version.json"
    if not source.exists():
        raise FileNotFoundError(source)
    return source


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _select_baseline(versions: list[DatasetVersionSummary], baseline: str | int | None) -> DatasetVersionSummary:
    if baseline is None:
        return versions[0]
    if isinstance(baseline, int):
        if baseline < 0 or baseline >= len(versions):
            raise ValueError(f"baseline index out of range: {baseline}")
        return versions[baseline]
    wanted = baseline.strip()
    if not wanted:
        raise ValueError("baseline cannot be empty")
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(versions):
            return versions[index]
    for version in versions:
        if wanted in {version.name, version.path, Path(version.path).parent.name, str(version.dataset_id)}:
            return version
    raise ValueError(f"baseline did not match a version name, path, dataset id, or 1-based index: {baseline}")


def _baseline_delta(version: DatasetVersionSummary, baseline: DatasetVersionSummary) -> dict[str, Any]:
    return {
        "name": version.name,
        "path": version.path,
        "baseline_name": baseline.name,
        "is_baseline": version.path == baseline.path,
        "fingerprint_changed": _changed(version.fingerprint, baseline.fingerprint),
        "dedupe_policy_changed": _changed(version.dedupe_policy, baseline.dedupe_policy),
        "source_order_changed": _changed(version.source_order_digest, baseline.source_order_digest),
        "dataset_id_changed": _changed(version.dataset_id, baseline.dataset_id),
        "source_count_delta": version.source_count - baseline.source_count,
        "included_source_count_delta": version.included_source_count - baseline.included_source_count,
        "skipped_source_count_delta": version.skipped_source_count - baseline.skipped_source_count,
        "char_count_delta": version.char_count - baseline.char_count,
        "line_count_delta": version.line_count - baseline.line_count,
        "unique_char_count_delta": version.unique_char_count - baseline.unique_char_count,
        "warning_count_delta": version.warning_count - baseline.warning_count,
        "issue_count_delta": version.issue_count - baseline.issue_count,
    }


def _comparison_summary(
    versions: list[DatasetVersionSummary],
    baseline: DatasetVersionSummary,
    deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    dataset_ids = sorted({version.dataset_id for version in versions if version.dataset_id})
    fingerprints = sorted({version.short_fingerprint for version in versions if version.short_fingerprint})
    dedupe_policies = sorted({version.dedupe_policy for version in versions if version.dedupe_policy})
    quality_statuses = sorted({version.quality_status for version in versions if version.quality_status})
    return {
        "baseline_name": baseline.name,
        "baseline_dataset_id": baseline.dataset_id,
        "version_count": len(versions),
        "dataset_ids": dataset_ids,
        "dataset_id_count": len(dataset_ids),
        "fingerprints": fingerprints,
        "fingerprint_count": len(fingerprints),
        "dedupe_policies": dedupe_policies,
        "dedupe_policy_count": len(dedupe_policies),
        "quality_statuses": quality_statuses,
        "changed_fingerprint_count": sum(1 for row in deltas if row.get("fingerprint_changed")),
        "changed_dedupe_policy_count": sum(1 for row in deltas if row.get("dedupe_policy_changed")),
        "changed_source_order_count": sum(1 for row in deltas if row.get("source_order_changed")),
        "total_char_count": sum(version.char_count for version in versions),
        "total_skipped_source_count": sum(version.skipped_source_count for version in versions),
        "max_char_count": max((version.char_count for version in versions), default=0),
    }


def _recommendations(versions: list[DatasetVersionSummary], summary: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if summary.get("fingerprint_count", 0) > 1:
        recommendations.append("Dataset fingerprints differ; separate data changes from model or training changes in comparisons.")
    else:
        recommendations.append("All compared dataset versions share one fingerprint; model comparisons can treat corpus content as stable.")
    if summary.get("dedupe_policy_count", 0) > 1:
        recommendations.append("Dedupe policies differ; compare included/skipped source counts before using these versions as equivalent corpora.")
    if summary.get("total_skipped_source_count", 0) > 0:
        recommendations.append("At least one dataset version skipped sources; review snapshot skipped_sources before promotion.")
    if any(version.quality_status not in {"pass", None} for version in versions):
        recommendations.append("One or more dataset versions have non-pass quality status; resolve warnings before treating the dataset set as clean.")
    return recommendations


def _change_label(delta: dict[str, Any]) -> str:
    if delta.get("is_baseline"):
        return "baseline"
    labels = []
    if delta.get("fingerprint_changed"):
        labels.append("fingerprint")
    if delta.get("dedupe_policy_changed"):
        labels.append("dedupe")
    if delta.get("source_order_changed"):
        labels.append("source-order")
    if delta.get("char_count_delta"):
        labels.append("chars")
    return ", ".join(labels) if labels else "none"


def _changed(value: Any, baseline: Any) -> bool:
    return value is not None and baseline is not None and value != baseline


def _as_int(value: Any) -> int:
    return int(number_or_default(value, 0, int))


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _fmt_signed(value: Any) -> str:
    if value is None:
        return "missing"
    number = int(value)
    if number == 0:
        return "0"
    return f"{number:+d}"


def _style() -> str:
    return """<style>
:root { color-scheme: light; --ink:#172026; --muted:#54615a; --line:#d8ded5; --page:#f6f7f2; --panel:#fff; --green:#047857; --blue:#2563eb; --amber:#a16207; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:30px 36px 18px; background:var(--panel); border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; padding:18px 36px 0; }
.card, section { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px 16px; min-height:76px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
section { margin:18px 36px; padding:18px; overflow:auto; }
table { width:100%; border-collapse:collapse; min-width:1120px; font-size:13px; }
th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:#1f2937; background:#eef2e8; font-weight:700; }
.pill { display:inline-block; padding:4px 8px; border-radius:999px; color:#fff; font-size:12px; font-weight:700; }
.pill.baseline { background:var(--blue); }
.pill.changed { background:var(--amber); }
.pill.same { background:var(--green); }
li { margin:6px 0; }
footer { padding:12px 36px 28px; color:var(--muted); font-size:12px; }
</style>"""


def _stat(label: str, value: Any) -> str:
    return f'<div class="card"><div class="label">{_e(label)}</div><div class="value">{_e(value)}</div></div>'


__all__ = [
    "DatasetVersionSummary",
    "build_dataset_version_comparison",
    "render_dataset_version_comparison_html",
    "render_dataset_version_comparison_markdown",
    "summarize_dataset_version",
    "write_dataset_version_comparison_csv",
    "write_dataset_version_comparison_html",
    "write_dataset_version_comparison_json",
    "write_dataset_version_comparison_markdown",
    "write_dataset_version_comparison_outputs",
]
