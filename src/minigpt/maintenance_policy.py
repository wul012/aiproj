from __future__ import annotations

from typing import Any

from minigpt.maintenance_pressure import (
    DEFAULT_MODULE_CRITICAL_LINES,
    DEFAULT_MODULE_TOP_N,
    DEFAULT_MODULE_WARNING_LINES,
    build_module_pressure_report,
)
from minigpt.maintenance_policy_artifacts import (
    render_maintenance_batching_html,
    render_maintenance_batching_markdown,
    render_module_pressure_html,
    render_module_pressure_markdown,
    write_maintenance_batching_csv,
    write_maintenance_batching_html,
    write_maintenance_batching_json,
    write_maintenance_batching_markdown,
    write_maintenance_batching_outputs,
    write_module_pressure_csv,
    write_module_pressure_html,
    write_module_pressure_json,
    write_module_pressure_markdown,
    write_module_pressure_outputs,
)
from minigpt.report_utils import (
    list_of_dicts as _list_of_dicts,
    string_list as _string_list,
    utc_now,
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
