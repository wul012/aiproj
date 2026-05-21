from __future__ import annotations

from typing import Any

from minigpt.maintenance_pressure import (
    DEFAULT_MODULE_CRITICAL_LINES,
    DEFAULT_MODULE_TOP_N,
    DEFAULT_MODULE_WARNING_LINES,
    build_module_pressure_report,
)
from minigpt.maintenance_policy_artifacts import (
    render_governance_stabilization_html,
    render_governance_stabilization_markdown,
    render_maintenance_batching_html,
    render_maintenance_batching_markdown,
    render_module_pressure_html,
    render_module_pressure_markdown,
    write_governance_stabilization_csv,
    write_governance_stabilization_html,
    write_governance_stabilization_json,
    write_governance_stabilization_markdown,
    write_governance_stabilization_outputs,
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
DEFAULT_GOVERNANCE_PAUSE_DAYS = 3

GOVERNANCE_STABILIZATION_ACTIONS = {"keep", "watch", "merge", "cut"}

DEFAULT_GOVERNANCE_CHAINS = [
    {
        "id": "dataset-provenance",
        "name": "Dataset provenance and snapshot flow",
        "action": "keep",
        "consumer": "dataset comparison, run comparison, registry, model card",
        "evidence": "dataset_version.json, dataset snapshot summary, dedupe/source-order fields",
        "review_reason": "Data changes can invalidate model-quality comparisons, so this chain is a core boundary rather than decorative reporting.",
        "expansion_rule": "Merge new dataset-only signals into this chain unless they require a new training or release decision.",
        "next_action": "Keep as the data-boundary spine; do not add more display-only projections during the pause.",
    },
    {
        "id": "benchmark-history",
        "name": "Benchmark scorecard and history flow",
        "action": "keep",
        "consumer": "maturity narrative, project audit, release bundle, release gate, readiness dashboards",
        "evidence": "benchmark history ledger, comparison/decision artifacts, CI plan digest checks",
        "review_reason": "Repeated benchmark evidence is the closest current proxy for model-capability movement.",
        "expansion_rule": "Extend this chain only when a new benchmark signal changes promotion or release review.",
        "next_action": "Keep as model-capability review evidence while avoiding new threshold variants.",
    },
    {
        "id": "registry-model-card",
        "name": "Registry and model-card aggregation",
        "action": "keep",
        "consumer": "project audit, release bundle, model-family review",
        "evidence": "registry rows, leaderboards, model_card.json/md/html",
        "review_reason": "Reviewers need one project index and one project-level model summary before opening detailed artifacts.",
        "expansion_rule": "Add new run-level facts here only after they exist in the source chain and have a clear review consumer.",
        "next_action": "Keep as the project-level index and summary surface.",
    },
    {
        "id": "release-readiness",
        "name": "Release bundle, gate, and readiness flow",
        "action": "keep",
        "consumer": "release review, readiness comparison, registry readiness tracking",
        "evidence": "release bundle, release gate, readiness dashboard, readiness comparison",
        "review_reason": "Release-style decisions need a stable gate/readiness surface even when the model remains educational.",
        "expansion_rule": "Repair broken release contracts here; avoid adding new panels unless they change ship/review/block decisions.",
        "next_action": "Keep as release-style review; only fix broken contracts during the pause.",
    },
    {
        "id": "ci-coverage-hygiene",
        "name": "CI workflow and coverage hygiene",
        "action": "keep",
        "consumer": "GitHub Actions, project audit, maturity review, training portfolio comparison",
        "evidence": "source encoding, CI workflow hygiene, coverage gate reports",
        "review_reason": "This chain has already caught real CI and encoding regressions, so it protects the rest of the evidence system.",
        "expansion_rule": "Add only checks that catch executable regressions; do not add narrative-only CI status fields.",
        "next_action": "Keep because it catches real regressions and CI drift.",
    },
    {
        "id": "training-promotion",
        "name": "Training-scale promotion and handoff flow",
        "action": "watch",
        "consumer": "promoted comparison, promoted baseline, promoted seed handoff, automation receipts",
        "evidence": "promotion reports, clean-evidence gates, schema-v2 receipt checks",
        "review_reason": "This chain is useful but has the highest overlap risk because many promotion artifacts repeat clean/review/block fields.",
        "expansion_rule": "Prefer helper and artifact consolidation before adding another promotion-stage report.",
        "next_action": "Watch for overlap and repeated fields; consolidate helper/output duplication before adding new promotion variants.",
    },
    {
        "id": "maturity-portfolio",
        "name": "Maturity narrative and portfolio review flow",
        "action": "watch",
        "consumer": "portfolio comparison, project-level review, release context",
        "evidence": "maturity summary, maturity narrative, portfolio comparison review actions",
        "review_reason": "This is the executive summary layer, so duplicate detail here can quickly become maintenance noise.",
        "expansion_rule": "Merge narrative-only additions into existing summaries unless a new consumer needs separate machine-readable fields.",
        "next_action": "Watch as an executive summary layer; merge duplicate narrative-only fields into existing summaries.",
    },
]


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


def build_governance_stabilization_review(
    chains: list[dict[str, Any]] | None = None,
    *,
    proposed_items: list[dict[str, Any]] | None = None,
    title: str = "MiniGPT governance stabilization review",
    generated_at: str | None = None,
    pause_days: int = DEFAULT_GOVERNANCE_PAUSE_DAYS,
) -> dict[str, Any]:
    normalized = [
        _normalize_governance_chain(item, index)
        for index, item in enumerate(_list_of_dicts(chains if chains is not None else DEFAULT_GOVERNANCE_CHAINS), start=1)
    ]
    summary = _governance_summary(normalized, pause_days)
    routing = _route_governance_proposals(proposed_items or [], normalized)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "policy": {
            "pause_days": int(pause_days),
            "new_chain_pause": "active" if int(pause_days) > 0 else "inactive",
            "stabilization_ceiling": 7,
            "allowed_actions": sorted(GOVERNANCE_STABILIZATION_ACTIONS),
        },
        "summary": summary,
        "chains": normalized,
        "proposal_routing": routing,
        "recommendations": _governance_recommendations(summary, normalized, routing),
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


def _normalize_governance_chain(item: dict[str, Any], index: int) -> dict[str, Any]:
    action = str(item.get("action") or "watch").strip().lower().replace("_", "-")
    if action not in GOVERNANCE_STABILIZATION_ACTIONS:
        action = "watch"
    consumer = str(item.get("consumer") or item.get("consumers") or "").strip()
    evidence = str(item.get("evidence") or "").strip()
    review_reason = str(item.get("review_reason") or item.get("reason") or "").strip()
    expansion_rule = str(item.get("expansion_rule") or item.get("rule") or "").strip()
    next_action = str(item.get("next_action") or item.get("recommendation") or "").strip()
    necessary = action in {"keep", "watch"}
    has_consumer = bool(consumer)
    has_evidence = bool(evidence)
    return {
        "id": str(item.get("id") or f"chain-{index}"),
        "name": str(item.get("name") or item.get("title") or f"Governance chain {index}"),
        "action": action,
        "necessary": necessary,
        "has_consumer": has_consumer,
        "has_evidence": has_evidence,
        "consumer": consumer,
        "evidence": evidence,
        "review_reason": review_reason,
        "expansion_rule": expansion_rule,
        "next_action": next_action,
    }


def _governance_summary(chains: list[dict[str, Any]], pause_days: int) -> dict[str, Any]:
    chain_count = len(chains)
    action_counts = {action: sum(1 for item in chains if item.get("action") == action) for action in sorted(GOVERNANCE_STABILIZATION_ACTIONS)}
    missing_consumer = sum(1 for item in chains if not item.get("has_consumer"))
    missing_evidence = sum(1 for item in chains if not item.get("has_evidence"))
    missing_review_reason = sum(1 for item in chains if not item.get("review_reason"))
    missing_expansion_rule = sum(1 for item in chains if not item.get("expansion_rule"))
    consolidation_candidates = action_counts.get("merge", 0) + action_counts.get("cut", 0)
    status = (
        "review"
        if chain_count > 7
        or missing_consumer
        or missing_evidence
        or missing_review_reason
        or missing_expansion_rule
        or consolidation_candidates
        else "pass"
    )
    decision = "pause_new_governance_chains" if int(pause_days) > 0 else "continue_with_guardrails"
    if status == "review" and consolidation_candidates:
        decision = "pause_and_consolidate_governance_chains"
    elif status == "review":
        decision = "pause_and_review_governance_chains"
    return {
        "status": status,
        "decision": decision,
        "pause_days": int(pause_days),
        "chain_count": chain_count,
        "keep_count": action_counts.get("keep", 0),
        "watch_count": action_counts.get("watch", 0),
        "merge_count": action_counts.get("merge", 0),
        "cut_count": action_counts.get("cut", 0),
        "necessary_count": sum(1 for item in chains if item.get("necessary")),
        "missing_consumer_count": missing_consumer,
        "missing_evidence_count": missing_evidence,
        "missing_review_reason_count": missing_review_reason,
        "missing_expansion_rule_count": missing_expansion_rule,
        "consolidation_candidate_count": consolidation_candidates,
    }


def _route_governance_proposals(items: list[dict[str, Any]], chains: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [_normalize_governance_proposal(item, index, chains) for index, item in enumerate(_list_of_dicts(items), start=1)]
    if not normalized:
        return {
            "decision": "not_applicable",
            "item_count": 0,
            "merge_existing_count": 0,
            "review_count": 0,
            "new_chain_candidate_count": 0,
            "exact_match_count": 0,
            "keyword_match_count": 0,
            "ambiguous_keyword_match_count": 0,
            "keyword_hits": [],
            "ambiguous_keyword_hits": [],
            "items": [],
            "reasons": ["No governance expansion proposals were provided."],
        }
    review_count = sum(1 for item in normalized if item.get("route_decision") == "review")
    new_chain_candidate_count = sum(1 for item in normalized if item.get("route_decision") == "new_chain_candidate")
    merge_existing_count = sum(1 for item in normalized if item.get("route_decision") == "merge_existing")
    exact_match_count = sum(1 for item in normalized if item.get("match_basis") == "exact")
    keyword_match_count = sum(1 for item in normalized if item.get("match_basis") == "keyword")
    ambiguous_keyword_match_count = sum(1 for item in normalized if item.get("match_basis") == "ambiguous_keyword")
    keyword_hits = [str(item.get("matched_keyword") or "") for item in normalized if item.get("match_basis") == "keyword" and item.get("matched_keyword")]
    ambiguous_keyword_hits = _unique_strings(
        keyword
        for item in normalized
        if item.get("match_basis") == "ambiguous_keyword"
        for keyword in _string_list(item.get("matched_keywords"))
    )
    if new_chain_candidate_count:
        decision = "reject_new_chain_during_pause"
        reasons = ["At least one proposal cannot be routed to an existing chain during the pause window."]
    elif review_count:
        decision = "review_before_merge"
        reasons = ["Review high-risk or weakly matched proposals before changing governance artifacts."]
    else:
        decision = "merge_existing"
        reasons = ["All proposals can be merged into existing governance chains."]
    return {
        "decision": decision,
        "item_count": len(normalized),
        "merge_existing_count": merge_existing_count,
        "review_count": review_count,
        "new_chain_candidate_count": new_chain_candidate_count,
        "exact_match_count": exact_match_count,
        "keyword_match_count": keyword_match_count,
        "ambiguous_keyword_match_count": ambiguous_keyword_match_count,
        "keyword_hits": keyword_hits,
        "ambiguous_keyword_hits": ambiguous_keyword_hits,
        "items": normalized,
        "reasons": reasons,
    }


def _normalize_governance_proposal(item: dict[str, Any], index: int, chains: list[dict[str, Any]]) -> dict[str, Any]:
    title = str(item.get("title") or item.get("name") or f"proposal-{index}")
    target = str(item.get("target_chain") or item.get("chain") or item.get("suggested_chain") or "").strip()
    text = " ".join(
        [
            title,
            str(item.get("description") or ""),
            str(item.get("category") or ""),
        ]
    ).lower()
    matched_chain = _match_governance_chain(target, text, chains)
    risk_flags = _risk_flags(item)
    high_risk = bool(set(risk_flags) & set(HIGH_RISK_FLAGS))
    match_basis = matched_chain.get("match_basis", "") if matched_chain else ""
    matched_keyword = matched_chain.get("matched_keyword", "") if matched_chain else ""
    matched_chains = _string_list(matched_chain.get("matched_chains")) if matched_chain else []
    matched_keywords = _string_list(matched_chain.get("matched_keywords")) if matched_chain else []
    ambiguous_match = match_basis == "ambiguous_keyword"
    if matched_chain and not high_risk and not ambiguous_match:
        route_decision = "merge_existing"
        if match_basis == "keyword" and matched_keyword:
            reason = f"Merge into existing chain {matched_chain.get('id')} because keyword '{matched_keyword}' matched its routing map."
        else:
            reason = f"Merge into existing chain {matched_chain.get('id')} under its expansion rule."
    elif matched_chain:
        route_decision = "review"
        if ambiguous_match:
            reason = "Review before merging because keywords matched multiple governance chains: " + ", ".join(matched_chains) + "."
        elif match_basis == "keyword" and matched_keyword:
            reason = f"Review before merging into {matched_chain.get('id')} because keyword '{matched_keyword}' matched and risk flags are present."
        else:
            reason = f"Review before merging into {matched_chain.get('id')} because risk flags are present."
    else:
        route_decision = "new_chain_candidate"
        reason = "No existing governance chain matched this proposal during the pause window."
    return {
        "title": title,
        "target_chain": target,
        "suggested_chain": matched_chain.get("id") if matched_chain else "",
        "route_decision": route_decision,
        "risk_flags": risk_flags,
        "reason": reason,
        "expansion_rule": matched_chain.get("expansion_rule") if matched_chain else "",
        "match_basis": match_basis,
        "matched_keyword": matched_keyword,
        "matched_keywords": matched_keywords,
        "matched_chains": matched_chains,
        "matched_chain_count": len(matched_chains),
    }


def _match_governance_chain(target: str, text: str, chains: list[dict[str, Any]]) -> dict[str, Any] | None:
    target_lower = target.lower().replace("_", "-")
    for chain in chains:
        chain_id = str(chain.get("id") or "")
        if target_lower and target_lower == chain_id.lower():
            matched = dict(chain)
            matched["match_basis"] = "exact"
            matched["matched_keyword"] = ""
            matched["matched_keywords"] = []
            matched["matched_chains"] = [chain_id]
            return matched
    keyword_map = [
        ("dataset-provenance", ["dataset", "data", "corpus", "dedupe", "source"]),
        ("benchmark-history", ["benchmark", "scorecard", "rubric", "eval", "prompt"]),
        ("registry-model-card", ["registry", "model card", "model-card", "leaderboard"]),
        ("release-readiness", ["release", "readiness", "gate", "bundle"]),
        ("ci-coverage-hygiene", ["ci", "coverage", "workflow", "encoding", "github"]),
        ("training-promotion", ["promotion", "promoted", "handoff", "seed"]),
        ("maturity-portfolio", ["maturity", "portfolio", "narrative"]),
    ]
    keyword_matches: list[tuple[dict[str, Any], list[str]]] = []
    for chain_id, keywords in keyword_map:
        matched_keywords = [keyword for keyword in keywords if keyword in text]
        if matched_keywords:
            for chain in chains:
                if str(chain.get("id")) == chain_id:
                    keyword_matches.append((dict(chain), matched_keywords))
                    break
    if keyword_matches:
        matched = dict(keyword_matches[0][0])
        matched["match_basis"] = "keyword" if len(keyword_matches) == 1 else "ambiguous_keyword"
        matched["matched_keyword"] = keyword_matches[0][1][0]
        matched["matched_keywords"] = [keyword for _, keywords in keyword_matches for keyword in keywords]
        matched["matched_chains"] = [str(chain.get("id") or "") for chain, _ in keyword_matches]
        return matched
    return None


def _governance_recommendations(summary: dict[str, Any], chains: list[dict[str, Any]], routing: dict[str, Any]) -> list[str]:
    recommendations = [
        f"Pause new governance-chain creation for {summary.get('pause_days')} days and only accept CI fixes, bugs, or broken-contract repairs.",
        "Review each chain by consumer and evidence before adding new reports or projections.",
    ]
    if summary.get("chain_count", 0) >= 7:
        recommendations.append("Treat seven active chains as the current ceiling; new needs should first merge into an existing chain.")
    if summary.get("consolidation_candidate_count", 0):
        recommendations.append("Consolidate chains marked merge/cut before any new governance surface is added.")
    if summary.get("missing_review_reason_count", 0) or summary.get("missing_expansion_rule_count", 0):
        recommendations.append("Add review reasons and expansion rules before treating a governance chain as stable.")
    if routing.get("decision") == "merge_existing":
        recommendations.append("Route current proposals into existing governance chains instead of adding a new chain.")
    elif routing.get("decision") == "review_before_merge":
        recommendations.append("Review high-risk governance proposals before merging them into an existing chain.")
    elif routing.get("decision") == "reject_new_chain_during_pause":
        recommendations.append("Reject unmatched governance-chain proposals during the pause or rewrite them to target an existing chain.")
    watch_names = [str(item.get("name")) for item in chains if item.get("action") == "watch"]
    if watch_names:
        recommendations.append("Watch for overlap in: " + ", ".join(watch_names) + ".")
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


def _unique_strings(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def _is_low_risk_utils(category: str, title: str) -> bool:
    if category in LOW_RISK_MAINTENANCE_CATEGORIES:
        return True
    text = title.lower().replace("_", "-")
    return "utils migration" in text or "report-utils" in text or "report utility migration" in text
