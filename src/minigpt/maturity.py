from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    key: str
    title: str
    versions: tuple[int, ...]
    target_level: int
    evidence: str
    next_step: str


CAPABILITY_SPECS = (
    CapabilitySpec(
        "model_core",
        "Model Core",
        (1, 2, 3, 4, 5, 6, 7, 10),
        4,
        "Tokenizer, GPT blocks, training artifacts, BPE, attention, prediction, chat wrapper, model reports, and sampling controls.",
        "Train larger baselines and compare scale/quality changes on fixed benchmark prompts.",
    ),
    CapabilitySpec(
        "data_reproducibility",
        "Data And Reproducibility",
        (13, 14, 15, 16, 35, 36),
        4,
        "Dataset preparation, run manifests, dataset quality checks, eval suites, benchmark metadata, and dataset version manifests.",
        "Add dataset cards and stable train/validation/test split policies for larger corpora.",
    ),
    CapabilitySpec(
        "evaluation_benchmarks",
        "Evaluation Benchmarks",
        (16, 28, 35, 37, 43, 44, 45, 46, 47),
        4,
        "Fixed prompt eval, generation quality, baseline comparison, pair batch, pair trend, dashboard links, registry links, and delta leaders.",
        "Consolidate eval and pair outputs into one benchmark suite with task-level pass/fail scoring.",
    ),
    CapabilitySpec(
        "local_inference",
        "Local Inference And Playground",
        (11, 12, 38, 39, 40, 41, 42, 55, 56, 57, 58, 59, 60),
        5,
        "Static playground, local API, safety profiles, checkpoint selector, checkpoint comparison, side-by-side generation, saved pair artifacts, streaming, request history, row detail JSON, and request history summaries.",
        "Connect request history stability summaries to audit/release handoff when local serving evidence becomes release-relevant.",
    ),
    CapabilitySpec(
        "registry_reporting",
        "Registry And Reporting",
        (8, 9, 17, 18, 19, 20, 21, 22, 23, 24, 46, 47),
        5,
        "Dashboard, run comparison, registry HTML, saved views, annotations, leaderboards, experiment/model cards, and pair report registry views.",
        "Add drill-down exports for pair delta leaders by task type, difficulty, and checkpoint pair.",
    ),
    CapabilitySpec(
        "release_governance",
        "Release Governance",
        (25, 26, 27, 28, 29, 30, 31, 32, 33, 34),
        5,
        "Project audit, release bundle, release gate, generation quality policy, policy profiles, profile comparison, deltas, and configurable baselines.",
        "Keep release gates as a stable review layer instead of adding more profile variants.",
    ),
    CapabilitySpec(
        "documentation_evidence",
        "Documentation And Evidence",
        (1, 8, 13, 23, 32, 35, 45, 46, 47, 48),
        5,
        "Version tags, README history, code explanations, archived screenshots, browser checks, and maturity summary.",
        "Keep future code explanations tied to concrete evidence and summarize phases instead of expanding every small link change.",
    ),
    CapabilitySpec(
        "project_synthesis",
        "Project Synthesis",
        (23, 24, 25, 26, 27, 37, 46, 47, 48),
        4,
        "Experiment cards, model cards, audit/bundle/gate outputs, baseline comparison, registry pair report links, delta leaders, and maturity summary.",
        "Use the maturity summary to choose the next real capability: benchmark scoring, larger data, or serving hardening.",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_maturity_summary(
    project_root: str | Path,
    *,
    title: str = "MiniGPT project maturity summary",
    generated_at: str | None = None,
    registry_path: str | Path | None = None,
    request_history_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    published_versions = _discover_published_versions(root)
    archive_versions = _discover_archive_versions(root)
    explanation_versions = _discover_explanation_versions(root)
    registry = _read_json(Path(registry_path)) if registry_path is not None else _read_json(root / "runs" / "registry" / "registry.json")
    request_history_summary = (
        _read_json(Path(request_history_summary_path))
        if request_history_summary_path is not None
        else _read_json(root / "runs" / "request-history-summary" / "request_history_summary.json")
    )
    capabilities = [_capability_row(spec, published_versions) for spec in CAPABILITY_SPECS]
    summary = _summary(published_versions, archive_versions, explanation_versions, capabilities, registry, request_history_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "project_root": str(root),
        "summary": summary,
        "capabilities": capabilities,
        "phase_timeline": _phase_timeline(published_versions),
        "registry_context": _registry_context(registry),
        "request_history_context": _request_history_context(request_history_summary),
        "recommendations": _recommendations(capabilities, registry, request_history_summary),
    }


def write_maturity_summary_json(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def write_maturity_summary_csv(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "key",
        "title",
        "status",
        "maturity_level",
        "target_level",
        "score_percent",
        "covered_count",
        "target_count",
        "covered_versions",
        "missing_versions",
        "next_step",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in _list_of_dicts(summary.get("capabilities")):
            writer.writerow({field: _csv_value(row.get(field)) for field in fieldnames})


def render_maturity_summary_markdown(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    lines = [
        f"# {summary.get('title', 'MiniGPT project maturity summary')}",
        "",
        f"- Generated: `{summary.get('generated_at')}`",
        f"- Project root: `{summary.get('project_root')}`",
        "",
        "## Overview",
        "",
        *_markdown_table(
            [
                ("Current version", overview.get("current_version")),
                ("Published versions", overview.get("published_version_count")),
                ("Archive versions", overview.get("archive_version_count")),
                ("Explanation versions", overview.get("explanation_version_count")),
                ("Average maturity level", overview.get("average_maturity_level")),
                ("Overall status", overview.get("overall_status")),
                ("Registry runs", overview.get("registry_runs")),
                ("Request history status", overview.get("request_history_status")),
                ("Request history records", overview.get("request_history_records")),
            ]
        ),
        "",
        "## Capability Matrix",
        "",
        "| Area | Status | Level | Score | Evidence | Next step |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in _list_of_dicts(summary.get("capabilities")):
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(row.get("title")),
                    _md(row.get("status")),
                    _md(f"{row.get('maturity_level')}/{row.get('target_level')}"),
                    _md(f"{row.get('score_percent')}%"),
                    _md(row.get("evidence")),
                    _md(row.get("next_step")),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Phase Timeline", "", "| Versions | Phase | Status |", "| --- | --- | --- |"])
    for phase in _list_of_dicts(summary.get("phase_timeline")):
        lines.append(f"| {_md(phase.get('versions'))} | {_md(phase.get('title'))} | {_md(phase.get('status'))} |")
    request_history = _dict(summary.get("request_history_context"))
    lines.extend(
        [
            "",
            "## Request History Context",
            "",
            *_markdown_table(
                [
                    ("Available", request_history.get("available")),
                    ("Status", request_history.get("status")),
                    ("Records", request_history.get("total_log_records")),
                    ("Invalid", request_history.get("invalid_record_count")),
                    ("Timeout rate", request_history.get("timeout_rate")),
                    ("Bad request rate", request_history.get("bad_request_rate")),
                    ("Error rate", request_history.get("error_rate")),
                    ("Checkpoints", request_history.get("unique_checkpoint_count")),
                    ("Latest", request_history.get("latest_timestamp")),
                ]
            ),
        ]
    )
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(summary.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_maturity_summary_markdown(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_markdown(summary), encoding="utf-8")


def render_maturity_summary_html(summary: dict[str, Any]) -> str:
    overview = _dict(summary.get("summary"))
    registry = _dict(summary.get("registry_context"))
    request_history = _dict(summary.get("request_history_context"))
    stats = [
        ("Current", overview.get("current_version")),
        ("Versions", overview.get("published_version_count")),
        ("Archives", overview.get("archive_version_count")),
        ("Explanations", overview.get("explanation_version_count")),
        ("Maturity", overview.get("average_maturity_level")),
        ("Status", overview.get("overall_status")),
        ("Runs", overview.get("registry_runs")),
        ("Pair deltas", registry.get("pair_delta_cases")),
        ("Requests", request_history.get("total_log_records")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(summary.get('title', 'MiniGPT project maturity summary'))}</h1><p>{_e(summary.get('project_root'))}</p></header>",
            '<section class="stats">' + "".join(_card(label, value) for label, value in stats) + "</section>",
            _capability_section(_list_of_dicts(summary.get("capabilities"))),
            _timeline_section(_list_of_dicts(summary.get("phase_timeline"))),
            _registry_section(registry),
            _request_history_section(request_history),
            _recommendation_section(_string_list(summary.get("recommendations"))),
            "<footer>Generated by MiniGPT maturity summary exporter.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maturity_summary_html(summary: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maturity_summary_html(summary), encoding="utf-8")


def write_maturity_summary_outputs(summary: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maturity_summary.json",
        "csv": root / "maturity_summary.csv",
        "markdown": root / "maturity_summary.md",
        "html": root / "maturity_summary.html",
    }
    write_maturity_summary_json(summary, paths["json"])
    write_maturity_summary_csv(summary, paths["csv"])
    write_maturity_summary_markdown(summary, paths["markdown"])
    write_maturity_summary_html(summary, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _discover_published_versions(root: Path) -> list[int]:
    readme = root / "README.md"
    if not readme.exists():
        return []
    versions = {int(match.group(1)) for match in re.finditer(r"\bv(\d+)\.0\.0\b", readme.read_text(encoding="utf-8-sig"))}
    return sorted(versions)


def _discover_archive_versions(root: Path) -> list[int]:
    versions = set()
    for archive_root in [root / "a", root / "b"]:
        if not archive_root.exists():
            continue
        for child in archive_root.iterdir():
            if child.is_dir() and child.name.isdigit():
                versions.add(int(child.name))
    return sorted(versions)


def _discover_explanation_versions(root: Path) -> list[int]:
    versions = set()
    for path in root.glob("代码讲解记录*/*.md"):
        match = re.search(r"-v(\d+)-", path.name)
        if match:
            versions.add(int(match.group(1)))
    return sorted(versions)


def _capability_row(spec: CapabilitySpec, published_versions: list[int]) -> dict[str, Any]:
    published = set(published_versions)
    covered = [version for version in spec.versions if version in published]
    missing = [version for version in spec.versions if version not in published]
    ratio = len(covered) / len(spec.versions) if spec.versions else 0.0
    maturity_level = min(spec.target_level, max(1, round(ratio * spec.target_level))) if ratio else 0
    status = "pass" if ratio >= 0.9 else "warn" if ratio >= 0.5 else "fail"
    return {
        "key": spec.key,
        "title": spec.title,
        "status": status,
        "maturity_level": maturity_level,
        "target_level": spec.target_level,
        "score_percent": round(ratio * 100, 1),
        "covered_count": len(covered),
        "target_count": len(spec.versions),
        "covered_versions": covered,
        "missing_versions": missing,
        "evidence": spec.evidence,
        "next_step": spec.next_step,
    }


def _summary(
    published_versions: list[int],
    archive_versions: list[int],
    explanation_versions: list[int],
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    average = 0.0
    if capabilities:
        average = round(sum(float(item.get("maturity_level") or 0) for item in capabilities) / len(capabilities), 2)
    statuses = [str(item.get("status")) for item in capabilities]
    overall = "fail" if "fail" in statuses else "warn" if "warn" in statuses else "pass"
    return {
        "current_version": max(published_versions) if published_versions else None,
        "published_version_count": len(published_versions),
        "archive_version_count": len(archive_versions),
        "explanation_version_count": len(explanation_versions),
        "average_maturity_level": average,
        "overall_status": overall,
        "registry_runs": _pick(registry, "run_count"),
        "request_history_status": _nested_pick(request_history_summary, "summary", "status"),
        "request_history_records": _nested_pick(request_history_summary, "summary", "total_log_records"),
        "request_history_timeout_rate": _nested_pick(request_history_summary, "summary", "timeout_rate"),
        "request_history_error_rate": _nested_pick(request_history_summary, "summary", "error_rate"),
    }


def _phase_timeline(published_versions: list[int]) -> list[dict[str, Any]]:
    published = set(published_versions)
    phases = [
        ("v1-v12", "MiniGPT learning core", range(1, 13)),
        ("v13-v24", "Data, registry, and cards", range(13, 25)),
        ("v25-v34", "Release governance", range(25, 35)),
        ("v35-v47", "Evaluation benchmark and pair reports", range(35, 48)),
        ("v48-v60", "Project maturity and local inference hardening", range(48, 61)),
    ]
    rows = []
    for versions, title, version_range in phases:
        expected = list(version_range)
        covered = [version for version in expected if version in published]
        ratio = len(covered) / len(expected) if expected else 0
        rows.append(
            {
                "versions": versions,
                "title": title,
                "covered_count": len(covered),
                "target_count": len(expected),
                "status": "pass" if ratio >= 0.9 else "warn" if ratio > 0 else "pending",
            }
        )
    return rows


def _registry_context(registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(registry, dict):
        return {
            "available": False,
            "run_count": None,
            "pair_delta_cases": None,
            "pair_report_counts": {},
        }
    pair_delta = _dict(registry.get("pair_delta_summary"))
    return {
        "available": True,
        "run_count": registry.get("run_count"),
        "quality_counts": registry.get("quality_counts") if isinstance(registry.get("quality_counts"), dict) else {},
        "generation_quality_counts": registry.get("generation_quality_counts") if isinstance(registry.get("generation_quality_counts"), dict) else {},
        "pair_report_counts": registry.get("pair_report_counts") if isinstance(registry.get("pair_report_counts"), dict) else {},
        "pair_delta_cases": pair_delta.get("case_count"),
        "pair_delta_max_generated": pair_delta.get("max_abs_generated_char_delta"),
    }


def _request_history_context(request_history_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(request_history_summary, dict):
        return {
            "available": False,
            "status": None,
            "total_log_records": None,
            "timeout_rate": None,
            "bad_request_rate": None,
            "error_rate": None,
        }
    summary = _dict(request_history_summary.get("summary"))
    return {
        "available": True,
        "request_log": request_history_summary.get("request_log"),
        "status": summary.get("status"),
        "total_log_records": summary.get("total_log_records"),
        "invalid_record_count": summary.get("invalid_record_count"),
        "ok_count": summary.get("ok_count"),
        "timeout_count": summary.get("timeout_count"),
        "bad_request_count": summary.get("bad_request_count"),
        "error_count": summary.get("error_count"),
        "timeout_rate": summary.get("timeout_rate"),
        "bad_request_rate": summary.get("bad_request_rate"),
        "error_rate": summary.get("error_rate"),
        "stream_request_count": summary.get("stream_request_count"),
        "pair_request_count": summary.get("pair_request_count"),
        "unique_checkpoint_count": summary.get("unique_checkpoint_count"),
        "latest_timestamp": summary.get("latest_timestamp"),
    }


def _recommendations(
    capabilities: list[dict[str, Any]],
    registry: dict[str, Any] | None,
    request_history_summary: dict[str, Any] | None,
) -> list[str]:
    recs = [
        "Treat v48 as a phase summary: avoid continuing to split links/trends/dashboard unless the change improves evaluation quality.",
        "Next high-value step: consolidate eval suite, generation quality, pair batch, and pair delta leaders into one benchmark scoring suite.",
        "Use the maturity matrix to explain the project as a learning AI engineering artifact, not as a production-grade model service.",
    ]
    weak = [item for item in capabilities if item.get("status") != "pass"]
    if weak:
        recs.append("Revisit weaker areas first: " + ", ".join(str(item.get("title")) for item in weak[:3]) + ".")
    if not isinstance(registry, dict):
        recs.append("Generate a fresh registry before final portfolio review so the maturity summary can include live run counts.")
    if not isinstance(request_history_summary, dict):
        recs.append("Generate request_history_summary.json before local serving review so maturity context includes recent inference stability.")
    else:
        request_summary = _dict(request_history_summary.get("summary"))
        if request_summary.get("status") not in {"pass", "empty"}:
            recs.append("Review request history summary warnings before using the playground session as stable local inference evidence.")
    return recs


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else None


def _capability_section(rows: list[dict[str, Any]]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>"
            f"<td><strong>{_e(row.get('title'))}</strong><br><span>{_e(row.get('key'))}</span></td>"
            f"<td><span class=\"pill {_e(row.get('status'))}\">{_e(row.get('status'))}</span></td>"
            f"<td>{_e(row.get('maturity_level'))}/{_e(row.get('target_level'))}</td>"
            f"<td>{_e(row.get('score_percent'))}%<br><span>{_e(_version_list(row.get('covered_versions')))}</span></td>"
            f"<td>{_e(row.get('evidence'))}</td>"
            f"<td>{_e(row.get('next_step'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Capability Matrix</h2>'
        '<table><thead><tr><th>Area</th><th>Status</th><th>Level</th><th>Coverage</th><th>Evidence</th><th>Next Step</th></tr></thead><tbody>'
        + "".join(table_rows)
        + "</tbody></table></section>"
    )


def _timeline_section(rows: list[dict[str, Any]]) -> str:
    items = []
    for row in rows:
        items.append(
            "<tr>"
            f"<td>{_e(row.get('versions'))}</td>"
            f"<td>{_e(row.get('title'))}</td>"
            f"<td>{_e(row.get('covered_count'))}/{_e(row.get('target_count'))}</td>"
            f"<td>{_e(row.get('status'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Phase Timeline</h2>'
        '<table><thead><tr><th>Versions</th><th>Phase</th><th>Coverage</th><th>Status</th></tr></thead><tbody>'
        + "".join(items)
        + "</tbody></table></section>"
    )


def _registry_section(registry: dict[str, Any]) -> str:
    rows = [
        ("Available", registry.get("available")),
        ("Runs", registry.get("run_count")),
        ("Pair reports", _fmt_mapping(registry.get("pair_report_counts"))),
        ("Pair delta cases", registry.get("pair_delta_cases")),
        ("Max generated delta", registry.get("pair_delta_max_generated")),
        ("Quality counts", _fmt_mapping(registry.get("quality_counts"))),
        ("Generation quality", _fmt_mapping(registry.get("generation_quality_counts"))),
    ]
    return '<section class="panel"><h2>Registry Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _request_history_section(request_history: dict[str, Any]) -> str:
    rows = [
        ("Available", request_history.get("available")),
        ("Status", request_history.get("status")),
        ("Records", request_history.get("total_log_records")),
        ("Invalid", request_history.get("invalid_record_count")),
        ("OK", request_history.get("ok_count")),
        ("Timeout", request_history.get("timeout_count")),
        ("Bad request", request_history.get("bad_request_count")),
        ("Error", request_history.get("error_count")),
        ("Timeout rate", request_history.get("timeout_rate")),
        ("Error rate", request_history.get("error_rate")),
        ("Checkpoints", request_history.get("unique_checkpoint_count")),
        ("Latest", request_history.get("latest_timestamp")),
    ]
    return '<section class="panel"><h2>Request History Context</h2><table>' + "".join(
        f"<tr><th>{_e(label)}</th><td>{_e(value)}</td></tr>" for label, value in rows
    ) + "</table></section>"


def _recommendation_section(items: list[str]) -> str:
    return '<section class="panel"><h2>Recommendations</h2><ul>' + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul></section>"


def _style() -> str:
    return """<style>
:root { --ink:#111827; --muted:#4b5563; --line:#d8dee9; --page:#f7f7f2; --panel:#fff; --blue:#2563eb; --green:#047857; --amber:#b45309; --red:#b91c1c; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink); font-family:Arial, "Microsoft YaHei", sans-serif; line-height:1.45; }
header { padding:28px 32px 18px; background:#fff; border-bottom:1px solid var(--line); }
h1 { margin:0 0 8px; font-size:28px; letter-spacing:0; }
h2 { margin:0 0 12px; font-size:18px; }
p, span { color:var(--muted); }
.stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:12px; padding:18px 32px 4px; }
.card, .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; }
.card { padding:14px; min-height:84px; }
.label { color:var(--muted); font-size:12px; text-transform:uppercase; }
.value { margin-top:6px; font-size:20px; font-weight:700; overflow-wrap:anywhere; }
.panel { margin:18px 32px; padding:16px; overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:980px; }
th, td { padding:9px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { color:var(--muted); font-size:12px; text-transform:uppercase; }
.pill { display:inline-block; min-width:58px; padding:3px 8px; border-radius:999px; color:#fff; text-align:center; font-size:12px; font-weight:700; }
.pill.pass { background:var(--green); }
.pill.warn { background:var(--amber); }
.pill.fail { background:var(--red); }
ul { margin:0; padding-left:22px; }
li { margin:8px 0; }
footer { padding:20px 32px 34px; color:var(--muted); font-size:13px; }
@media (max-width:760px) { header, .stats { padding-left:16px; padding-right:16px; } .panel { margin-left:16px; margin-right:16px; } }
</style>"""


def _card(label: str, value: Any) -> str:
    return (
        '<div class="card">'
        f'<div class="label">{_e(label)}</div>'
        f'<div class="value">{_e("missing" if value is None else value)}</div>'
        "</div>"
    )


def _markdown_table(rows: list[tuple[Any, Any]]) -> list[str]:
    lines = ["| Key | Value |", "| --- | --- |"]
    lines.extend(f"| {_md(key)} | {_md(value)} |" for key, value in rows)
    return lines


def _version_list(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(f"v{item}" for item in value)


def _fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return "missing"
    return ", ".join(f"{key}:{value[key]}" for key in sorted(value))


def _csv_value(value: Any) -> Any:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return value


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _nested_pick(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)
