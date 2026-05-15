from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.report_utils import (
    as_dict as _dict,
    html_escape as _e,
    list_of_dicts as _list_of_dicts,
    markdown_cell as _md,
    string_list as _string_list,
    utc_now,
    write_csv_row,
    write_json_payload,
)

LOW_RISK_MAINTENANCE_CATEGORIES = {
    "report-utils",
    "utils-migration",
    "docs-only",
    "test-helper",
}

HIGH_RISK_FLAGS = {
    "behavior_change": "behavior changes should keep a focused version boundary",
    "schema_change": "schema or output contract changes should be reviewed independently",
    "service_change": "service/API changes should not hide inside a maintenance batch",
    "ui_change": "visible UI changes need their own evidence path",
    "large_module": "large modules should be split only after a scoped plan",
    "unclear_boundary": "unclear ownership needs review before batching",
}

DEFAULT_SINGLE_MODULE_UTILS_LIMIT = 3
DEFAULT_MIN_BATCH_ITEMS = 2


def build_maintenance_batching_report(
    history: list[dict[str, Any]],
    *,
    proposal_items: list[dict[str, Any]] | None = None,
    title: str = "MiniGPT maintenance batching policy",
    generated_at: str | None = None,
    single_module_limit: int = DEFAULT_SINGLE_MODULE_UTILS_LIMIT,
    min_batch_items: int = DEFAULT_MIN_BATCH_ITEMS,
) -> dict[str, Any]:
    releases = [_normalize_release_entry(item, index) for index, item in enumerate(_list_of_dicts(history), start=1)]
    runs = _single_module_utils_runs(releases)
    proposal = build_maintenance_proposal_decision(proposal_items or [], min_batch_items=min_batch_items)
    summary = _summary(releases, runs, single_module_limit)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "policy": {
            "single_module_utils_limit": int(single_module_limit),
            "min_batch_items": int(min_batch_items),
            "low_risk_categories": sorted(LOW_RISK_MAINTENANCE_CATEGORIES),
            "high_risk_flags": sorted(HIGH_RISK_FLAGS),
        },
        "summary": summary,
        "releases": releases,
        "single_module_utils_runs": runs,
        "proposal": proposal,
        "recommendations": _recommendations(summary, proposal),
    }


def build_maintenance_proposal_decision(
    items: list[dict[str, Any]],
    *,
    min_batch_items: int = DEFAULT_MIN_BATCH_ITEMS,
) -> dict[str, Any]:
    normalized = [_normalize_proposal_item(item, index) for index, item in enumerate(_list_of_dicts(items), start=1)]
    if not normalized:
        return {
            "decision": "not_applicable",
            "target_version_kind": "none",
            "item_count": 0,
            "batchable_count": 0,
            "split_count": 0,
            "items": [],
            "groups": [],
            "reasons": ["No proposal items were provided."],
        }

    split_items = [item for item in normalized if item["split_required"]]
    batchable = [item for item in normalized if item["batchable"]]
    groups = _category_groups(batchable)
    if split_items:
        decision = "split"
        target_kind = "focused"
        reasons = ["Split high-risk or unclear items into focused versions before batching the remaining maintenance work."]
    elif len(batchable) >= int(min_batch_items) and len(groups) == 1:
        decision = "batch"
        target_kind = "batched"
        reasons = ["Batch these related low-risk maintenance items into one version."]
    elif len(batchable) >= int(min_batch_items):
        decision = "batch_by_category"
        target_kind = "batched-groups"
        reasons = ["Batch low-risk items by category instead of mixing unrelated maintenance themes."]
    else:
        decision = "single_ok"
        target_kind = "focused"
        reasons = ["A single low-risk maintenance item can stay inside the next focused version."]

    return {
        "decision": decision,
        "target_version_kind": target_kind,
        "item_count": len(normalized),
        "batchable_count": len(batchable),
        "split_count": len(split_items),
        "items": normalized,
        "groups": groups,
        "reasons": reasons,
    }


def write_maintenance_batching_json(report: dict[str, Any], path: str | Path) -> None:
    write_json_payload(report, path)


def write_maintenance_batching_csv(report: dict[str, Any], path: str | Path) -> None:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    row = {
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "entry_count": summary.get("entry_count"),
        "single_module_utils_count": summary.get("single_module_utils_count"),
        "batched_utils_count": summary.get("batched_utils_count"),
        "longest_single_module_utils_run": summary.get("longest_single_module_utils_run"),
        "single_module_utils_limit": _dict(report.get("policy")).get("single_module_utils_limit"),
        "proposal_decision": proposal.get("decision"),
        "proposal_target_version_kind": proposal.get("target_version_kind"),
        "proposal_item_count": proposal.get("item_count"),
    }
    write_csv_row(
        row,
        path,
        [
            "status",
            "decision",
            "entry_count",
            "single_module_utils_count",
            "batched_utils_count",
            "longest_single_module_utils_run",
            "single_module_utils_limit",
            "proposal_decision",
            "proposal_target_version_kind",
            "proposal_item_count",
        ],
    )


def render_maintenance_batching_markdown(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    lines = [
        f"# {report.get('title', 'MiniGPT maintenance batching policy')}",
        "",
        f"- Generated: `{report.get('generated_at')}`",
        f"- Status: `{summary.get('status')}`",
        f"- Decision: `{summary.get('decision')}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
    ]
    for key in [
        "entry_count",
        "single_module_utils_count",
        "batched_utils_count",
        "longest_single_module_utils_run",
        "single_module_utils_limit",
    ]:
        lines.append(f"| {_md(key)} | {_md(summary.get(key))} |")
    lines.extend(["", "## Single Module Utility Runs", "", "| Start | End | Length | Versions |", "| --- | --- | --- | --- |"])
    runs = _list_of_dicts(report.get("single_module_utils_runs"))
    if runs:
        for run in runs:
            versions = ", ".join(_string_list(run.get("versions")))
            lines.append(f"| {_md(run.get('start_version'))} | {_md(run.get('end_version'))} | {_md(run.get('length'))} | {_md(versions)} |")
    else:
        lines.append("|  |  | 0 |  |")
    lines.extend(["", "## Proposal", "", f"- Decision: `{proposal.get('decision')}`", f"- Target version kind: `{proposal.get('target_version_kind')}`", ""])
    for reason in _string_list(proposal.get("reasons")):
        lines.append(f"- {reason}")
    groups = _list_of_dicts(proposal.get("groups"))
    if groups:
        lines.extend(["", "| Category | Count | Items |", "| --- | --- | --- |"])
        for group in groups:
            lines.append(f"| {_md(group.get('category'))} | {_md(group.get('count'))} | {_md(', '.join(_string_list(group.get('items'))))} |")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in _string_list(report.get("recommendations")))
    return "\n".join(lines).rstrip() + "\n"


def write_maintenance_batching_markdown(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maintenance_batching_markdown(report), encoding="utf-8")


def render_maintenance_batching_html(report: dict[str, Any]) -> str:
    summary = _dict(report.get("summary"))
    proposal = _dict(report.get("proposal"))
    stats = [
        ("Status", summary.get("status")),
        ("Decision", summary.get("decision")),
        ("Entries", summary.get("entry_count")),
        ("Single utils", summary.get("single_module_utils_count")),
        ("Batched utils", summary.get("batched_utils_count")),
        ("Longest run", summary.get("longest_single_module_utils_run")),
        ("Proposal", proposal.get("decision")),
    ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="icon" href="data:,">',
            f"<title>{_e(report.get('title', 'MiniGPT maintenance batching policy'))}</title>",
            _style(),
            "</head>",
            "<body>",
            f"<header><h1>{_e(report.get('title', 'MiniGPT maintenance batching policy'))}</h1><p>Low-risk maintenance should be batched; high-risk changes keep focused evidence.</p></header>",
            '<section class="stats">' + "".join(_stat(label, value) for label, value in stats) + "</section>",
            _runs_section(_list_of_dicts(report.get("single_module_utils_runs"))),
            _proposal_section(proposal),
            _list_section("Recommendations", report.get("recommendations")),
            "<footer>Generated by MiniGPT maintenance batching policy.</footer>",
            "</body>",
            "</html>",
        ]
    )


def write_maintenance_batching_html(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_maintenance_batching_html(report), encoding="utf-8")


def write_maintenance_batching_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": root / "maintenance_batching.json",
        "csv": root / "maintenance_batching.csv",
        "markdown": root / "maintenance_batching.md",
        "html": root / "maintenance_batching.html",
    }
    write_maintenance_batching_json(report, paths["json"])
    write_maintenance_batching_csv(report, paths["csv"])
    write_maintenance_batching_markdown(report, paths["markdown"])
    write_maintenance_batching_html(report, paths["html"])
    return {key: str(value) for key, value in paths.items()}


def _normalize_release_entry(item: dict[str, Any], index: int) -> dict[str, Any]:
    version = str(item.get("version") or item.get("tag") or f"entry-{index}")
    title = str(item.get("title") or item.get("name") or version)
    category = _category(item, title)
    modules = _modules(item)
    risk_flags = _risk_flags(item)
    low_risk_utils = _is_low_risk_utils(category, title)
    high_risk = bool(set(risk_flags) & set(HIGH_RISK_FLAGS))
    single_module_utils = low_risk_utils and not high_risk and len(modules) <= 1
    return {
        "version": version,
        "title": title,
        "category": category,
        "modules": modules,
        "module_count": len(modules),
        "risk_flags": risk_flags,
        "low_risk_utils": low_risk_utils,
        "single_module_utils": single_module_utils,
    }


def _normalize_proposal_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    name = str(item.get("name") or item.get("module") or item.get("path") or f"item-{index}")
    category = _category(item, name)
    risk_flags = _risk_flags(item)
    high_risk_flags = [flag for flag in risk_flags if flag in HIGH_RISK_FLAGS]
    split_reasons = [HIGH_RISK_FLAGS[flag] for flag in high_risk_flags]
    low_risk = category in LOW_RISK_MAINTENANCE_CATEGORIES
    split_required = bool(high_risk_flags) or bool(item.get("split_required"))
    batchable = low_risk and not split_required
    return {
        "name": name,
        "category": category,
        "risk_flags": risk_flags,
        "low_risk": low_risk,
        "batchable": batchable,
        "split_required": split_required,
        "split_reasons": split_reasons,
    }


def _summary(releases: list[dict[str, Any]], runs: list[dict[str, Any]], single_module_limit: int) -> dict[str, Any]:
    longest = max((int(run.get("length", 0)) for run in runs), default=0)
    single_count = sum(1 for item in releases if item.get("single_module_utils"))
    batched_count = sum(1 for item in releases if item.get("low_risk_utils") and int(item.get("module_count", 0)) >= 2)
    status = "warn" if longest > int(single_module_limit) else "pass"
    return {
        "status": status,
        "decision": "batch_next_related_work" if status == "warn" else "continue_with_policy",
        "entry_count": len(releases),
        "low_risk_utils_count": sum(1 for item in releases if item.get("low_risk_utils")),
        "single_module_utils_count": single_count,
        "batched_utils_count": batched_count,
        "longest_single_module_utils_run": longest,
        "single_module_utils_limit": int(single_module_limit),
    }


def _single_module_utils_runs(releases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    for release in releases:
        if release.get("single_module_utils"):
            current.append(release)
            continue
        if current:
            runs.append(_run_row(current))
            current = []
    if current:
        runs.append(_run_row(current))
    return runs


def _run_row(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "start_version": items[0].get("version"),
        "end_version": items[-1].get("version"),
        "length": len(items),
        "versions": [str(item.get("version")) for item in items],
        "titles": [str(item.get("title")) for item in items],
    }


def _recommendations(summary: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if summary.get("status") == "warn":
        recommendations.append("Batch the next related low-risk utility migrations instead of tagging each single-module move.")
    else:
        recommendations.append("Keep batching related low-risk maintenance and reserve single-version tags for meaningful behavior or evidence changes.")
    decision = proposal.get("decision")
    if decision == "batch":
        recommendations.append("The current proposal is suitable for one batched maintenance version.")
    elif decision == "batch_by_category":
        recommendations.append("Split the current proposal into category-based maintenance batches.")
    elif decision == "split":
        recommendations.append("Handle high-risk or unclear proposal items as focused versions before any cleanup batch.")
    return recommendations


def _category_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = {}
    for item in items:
        grouped.setdefault(str(item.get("category") or "unknown"), []).append(str(item.get("name")))
    return [{"category": category, "count": len(names), "items": names} for category, names in sorted(grouped.items())]


def _category(item: dict[str, Any], fallback_text: str) -> str:
    category = str(item.get("category") or "").strip().lower()
    if category:
        return category.replace("_", "-")
    text = fallback_text.lower().replace("_", "-")
    if "report-utils" in text or ("report" in text and "util" in text):
        return "report-utils"
    if "utils" in text and "migration" in text:
        return "utils-migration"
    if "doc" in text:
        return "docs-only"
    return "feature"


def _modules(item: dict[str, Any]) -> list[str]:
    modules = item.get("modules")
    if isinstance(modules, list):
        values = [str(value) for value in modules if str(value).strip()]
    elif item.get("module"):
        values = [str(item.get("module"))]
    else:
        values = []
    return values


def _risk_flags(item: dict[str, Any]) -> list[str]:
    flags = [flag.strip().lower().replace("-", "_") for flag in _string_list(item.get("risk_flags")) if flag.strip()]
    return sorted(set(flags))


def _is_low_risk_utils(category: str, title: str) -> bool:
    if category in LOW_RISK_MAINTENANCE_CATEGORIES:
        return True
    text = title.lower().replace("_", "-")
    return "utils migration" in text or "report-utils" in text or "report utility migration" in text


def _runs_section(runs: list[dict[str, Any]]) -> str:
    if not runs:
        return '<section><h2>Single Module Utility Runs</h2><p class="muted">No consecutive single-module utility runs detected.</p></section>'
    rows = [
        "<tr><th>Start</th><th>End</th><th>Length</th><th>Versions</th></tr>",
        *[
            f"<tr><td>{_e(run.get('start_version'))}</td><td>{_e(run.get('end_version'))}</td><td>{_e(run.get('length'))}</td><td>{_e(', '.join(_string_list(run.get('versions'))))}</td></tr>"
            for run in runs
        ],
    ]
    return "<section><h2>Single Module Utility Runs</h2><table>" + "".join(rows) + "</table></section>"


def _proposal_section(proposal: dict[str, Any]) -> str:
    groups = _list_of_dicts(proposal.get("groups"))
    group_rows = "".join(
        f"<tr><td>{_e(group.get('category'))}</td><td>{_e(group.get('count'))}</td><td>{_e(', '.join(_string_list(group.get('items'))))}</td></tr>"
        for group in groups
    )
    groups_html = ""
    if groups:
        groups_html = "<table><tr><th>Category</th><th>Count</th><th>Items</th></tr>" + group_rows + "</table>"
    reasons = _string_list(proposal.get("reasons"))
    reasons_html = "<p class=\"muted\">No proposal reasons.</p>"
    if reasons:
        reasons_html = "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in reasons) + "</ul>"
    return (
        "<section><h2>Proposal</h2>"
        f"<p><strong>{_e(proposal.get('decision'))}</strong> -> {_e(proposal.get('target_version_kind'))}</p>"
        + reasons_html
        + groups_html
        + "</section>"
    )


def _list_section(title: str, items: Any) -> str:
    values = _string_list(items)
    if not values:
        return f"<section><h2>{_e(title)}</h2><p class=\"muted\">None.</p></section>"
    return f"<section><h2>{_e(title)}</h2><ul>" + "".join(f"<li>{_e(item)}</li>" for item in values) + "</ul></section>"


def _stat(label: str, value: Any) -> str:
    return f'<article class="stat"><span>{_e(label)}</span><strong>{_e(value)}</strong></article>'


def _style() -> str:
    return """
<style>
:root { color-scheme: light; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172026; background: #f6f8fa; }
body { margin: 0; padding: 24px; }
header, section, footer { max-width: 1040px; margin: 0 auto 18px; }
header { padding: 18px 0 8px; border-bottom: 3px solid #1f7a5c; }
h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.stat { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 12px; min-height: 64px; }
.stat span { display: block; color: #5c6b73; font-size: 12px; margin-bottom: 8px; }
.stat strong { display: block; font-size: 18px; overflow-wrap: anywhere; }
section { background: #fff; border: 1px solid #d7dee5; border-radius: 8px; padding: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e5e9ef; text-align: left; vertical-align: top; }
th { background: #eef3f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.muted { color: #687782; }
footer { color: #687782; font-size: 12px; }
</style>
""".strip()
