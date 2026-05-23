from __future__ import annotations

from typing import Any

from minigpt.maintenance_policy_common import HIGH_RISK_FLAGS, allowed_text, risk_flags, unique_strings
from minigpt.report_utils import list_of_dicts as _list_of_dicts, string_list as _string_list, utc_now


DEFAULT_GOVERNANCE_PAUSE_DAYS = 3

GOVERNANCE_STABILIZATION_ACTIONS = {"keep", "watch", "merge", "cut"}
GOVERNANCE_VALUE_STATUSES = {"core", "supporting", "watch"}
GOVERNANCE_DUPLICATE_RISKS = {"low", "medium", "high"}
GOVERNANCE_GUARDRAILS = {"keep-core", "route-to-existing", "freeze-new-fields", "consolidate-first"}

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
        "value_status": "core",
        "duplicate_risk": "low",
        "recent_expansion": "stable",
        "current_guardrail": "route-to-existing",
        "guardrail_detail": "Only add dataset fields when they change comparison, registry, or model-card decisions.",
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
        "value_status": "core",
        "duplicate_risk": "medium",
        "recent_expansion": "moderate",
        "current_guardrail": "keep-core",
        "guardrail_detail": "Prefer real checkpoint deltas over more scorecard display variants.",
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
        "value_status": "supporting",
        "duplicate_risk": "medium",
        "recent_expansion": "moderate",
        "current_guardrail": "route-to-existing",
        "guardrail_detail": "Keep registry/model-card facts as projections of source evidence, not new source chains.",
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
        "value_status": "core",
        "duplicate_risk": "medium",
        "recent_expansion": "heavy",
        "current_guardrail": "route-to-existing",
        "guardrail_detail": "Route release-readiness drift into existing gate/readiness outputs before adding dashboards.",
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
        "value_status": "core",
        "duplicate_risk": "low",
        "recent_expansion": "moderate",
        "current_guardrail": "keep-core",
        "guardrail_detail": "Executable CI checks remain valuable; narrative-only projections should merge elsewhere.",
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
        "value_status": "watch",
        "duplicate_risk": "high",
        "recent_expansion": "heavy",
        "current_guardrail": "freeze-new-fields",
        "guardrail_detail": "After v382-v396 CI-reason carryover, avoid new reason projections unless they change automation decisions.",
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
        "value_status": "watch",
        "duplicate_risk": "high",
        "recent_expansion": "heavy",
        "current_guardrail": "freeze-new-fields",
        "guardrail_detail": "Do not add more narrative projections until existing maturity/portfolio chains are summarized.",
    },
]


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


def _normalize_governance_chain(item: dict[str, Any], index: int) -> dict[str, Any]:
    action = str(item.get("action") or "watch").strip().lower().replace("_", "-")
    if action not in GOVERNANCE_STABILIZATION_ACTIONS:
        action = "watch"
    consumer = str(item.get("consumer") or item.get("consumers") or "").strip()
    evidence = str(item.get("evidence") or "").strip()
    review_reason = str(item.get("review_reason") or item.get("reason") or "").strip()
    expansion_rule = str(item.get("expansion_rule") or item.get("rule") or "").strip()
    next_action = str(item.get("next_action") or item.get("recommendation") or "").strip()
    value_status = allowed_text(item.get("value_status"), GOVERNANCE_VALUE_STATUSES, "watch" if action == "watch" else "core")
    duplicate_risk = allowed_text(item.get("duplicate_risk"), GOVERNANCE_DUPLICATE_RISKS, "medium" if action == "watch" else "low")
    recent_expansion = str(item.get("recent_expansion") or "").strip()
    current_guardrail = allowed_text(
        item.get("current_guardrail"),
        GOVERNANCE_GUARDRAILS,
        "consolidate-first" if action in {"merge", "cut"} else "route-to-existing",
    )
    guardrail_detail = str(item.get("guardrail_detail") or "").strip()
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
        "value_status": value_status,
        "duplicate_risk": duplicate_risk,
        "recent_expansion": recent_expansion,
        "current_guardrail": current_guardrail,
        "guardrail_detail": guardrail_detail,
    }


def _governance_summary(chains: list[dict[str, Any]], pause_days: int) -> dict[str, Any]:
    chain_count = len(chains)
    action_counts = {action: sum(1 for item in chains if item.get("action") == action) for action in sorted(GOVERNANCE_STABILIZATION_ACTIONS)}
    missing_consumer = sum(1 for item in chains if not item.get("has_consumer"))
    missing_evidence = sum(1 for item in chains if not item.get("has_evidence"))
    missing_review_reason = sum(1 for item in chains if not item.get("review_reason"))
    missing_expansion_rule = sum(1 for item in chains if not item.get("expansion_rule"))
    value_counts = {status: sum(1 for item in chains if item.get("value_status") == status) for status in sorted(GOVERNANCE_VALUE_STATUSES)}
    risk_counts = {risk: sum(1 for item in chains if item.get("duplicate_risk") == risk) for risk in sorted(GOVERNANCE_DUPLICATE_RISKS)}
    freeze_new_fields = sum(1 for item in chains if item.get("current_guardrail") == "freeze-new-fields")
    heavy_recent_expansion = sum(1 for item in chains if str(item.get("recent_expansion")).lower() == "heavy")
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
        "core_value_count": value_counts.get("core", 0),
        "supporting_value_count": value_counts.get("supporting", 0),
        "watch_value_count": value_counts.get("watch", 0),
        "low_duplicate_risk_count": risk_counts.get("low", 0),
        "medium_duplicate_risk_count": risk_counts.get("medium", 0),
        "high_duplicate_risk_count": risk_counts.get("high", 0),
        "heavy_recent_expansion_count": heavy_recent_expansion,
        "freeze_new_fields_count": freeze_new_fields,
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
    ambiguous_keyword_hits = unique_strings(
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
    text = " ".join([title, str(item.get("description") or ""), str(item.get("category") or "")]).lower()
    matched_chain = _match_governance_chain(target, text, chains)
    flags = risk_flags(item)
    high_risk = bool(set(flags) & set(HIGH_RISK_FLAGS))
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
        "risk_flags": flags,
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
    if summary.get("freeze_new_fields_count", 0):
        recommendations.append("Freeze new fields for chains marked freeze-new-fields; prefer consolidation, summaries, or real benchmark work.")
    if summary.get("high_duplicate_risk_count", 0):
        recommendations.append("Treat high duplicate-risk governance chains as monitoring targets before adding more downstream projections.")
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


__all__ = [
    "DEFAULT_GOVERNANCE_CHAINS",
    "DEFAULT_GOVERNANCE_PAUSE_DAYS",
    "GOVERNANCE_DUPLICATE_RISKS",
    "GOVERNANCE_GUARDRAILS",
    "GOVERNANCE_STABILIZATION_ACTIONS",
    "GOVERNANCE_VALUE_STATUSES",
    "build_governance_stabilization_review",
]
