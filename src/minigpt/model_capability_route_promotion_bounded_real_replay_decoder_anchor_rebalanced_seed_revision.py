from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check
from minigpt.report_check_common import resolve_exit_code_seed_ready as resolve_exit_code


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSONL_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.jsonl"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_CORPUS_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_corpus.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision.html"


def locate_decoder_anchor_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME
    return source


def locate_decoder_anchor_distribution_audit(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor rebalanced seed revision input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision(
    decoder_anchor_seed_revision: dict[str, Any],
    decoder_anchor_distribution_audit: dict[str, Any],
    *,
    seed_revision_path: str | Path | None = None,
    distribution_audit_path: str | Path | None = None,
    carry_forward_per_case: int = 2,
    direct_rebalance_copies_per_case: int = 2,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced seed revision",
    generated_at: str | None = None,
) -> dict[str, Any]:
    seed_summary = as_dict(decoder_anchor_seed_revision.get("summary"))
    audit_summary = as_dict(decoder_anchor_distribution_audit.get("summary"))
    source_examples = list_of_dicts(decoder_anchor_seed_revision.get("seed_examples"))
    kept_examples, rebalance_rows = _rebalance(source_examples, carry_forward_per_case, direct_rebalance_copies_per_case)
    bucket_rows = _bucket_rows(kept_examples)
    checks = _checks(decoder_anchor_seed_revision, decoder_anchor_distribution_audit, source_examples, kept_examples, bucket_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    revision = _revision(status, source_examples, kept_examples, rebalance_rows, bucket_rows, audit_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_seed_revision": str(seed_revision_path or ""),
        "source_decoder_anchor_distribution_audit": str(distribution_audit_path or ""),
        "source_summaries": {"seed_revision": seed_summary, "distribution_audit": audit_summary},
        "seed_examples": kept_examples,
        "bucket_rows": bucket_rows,
        "rebalance_rows": rebalance_rows,
        "check_rows": checks,
        "decoder_anchor_rebalanced_seed_revision": revision,
        "summary": _summary(status, checks, revision),
        "interpretation": _interpretation(status, revision),
    }


def _rebalance(examples: list[dict[str, Any]], carry_forward_per_case: int, direct_copies_per_case: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for row in examples:
        by_case.setdefault(str(row.get("case_id") or ""), []).append(row)

    output: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    for case_id in sorted(by_case):
        rows = by_case[case_id]
        carry = [row for row in rows if _bucket(row) == "carry_forward"]
        direct = [row for row in rows if _bucket(row) == "direct_answer"]
        bridge = [row for row in rows if _bucket(row) == "decoder_bridge"]
        kept_carry = carry[: max(0, carry_forward_per_case)]
        output.extend(_clone(row, "keep", "carry_forward_cap") for row in kept_carry)
        output.extend(_clone(row, "keep", "direct_answer_preserve") for row in direct)
        output.extend(_clone(row, "keep", "decoder_bridge_preserve") for row in bridge)
        added_direct = _direct_rebalance_examples(case_id, direct, direct_copies_per_case)
        output.extend(added_direct)
        actions.append(
            {
                "case_id": case_id,
                "source_carry_forward_count": len(carry),
                "kept_carry_forward_count": len(kept_carry),
                "dropped_carry_forward_count": max(0, len(carry) - len(kept_carry)),
                "preserved_direct_answer_count": len(direct),
                "added_direct_answer_count": len(added_direct),
                "preserved_decoder_bridge_count": len(bridge),
            }
        )
    return output, actions


def _direct_rebalance_examples(case_id: str, direct_rows: list[dict[str, Any]], copies: int) -> list[dict[str, Any]]:
    if not direct_rows:
        return []
    base = direct_rows[0]
    prompt = str(base.get("prompt") or "")
    completion = str(base.get("completion") or "fixed loss")
    rows = []
    for index in range(max(0, copies)):
        rows.append(
            {
                "example_id": f"decoder-anchor-rebalanced-{case_id}-direct-weight-{index + 1}",
                "case_id": case_id,
                "revision_type": "rebalanced_unanchored_direct_answer",
                "prompt": prompt,
                "completion": completion,
                "text": f"{prompt}{completion}",
                "required_terms": base.get("required_terms", ["fixed", "loss"]),
                "guardrail": "increase_direct_answer_weight_without_promotion_claim",
                "rebalance_action": "add",
                "rebalance_reason": "direct_answer_underweighted",
            }
        )
    return rows


def _clone(row: dict[str, Any], action: str, reason: str) -> dict[str, Any]:
    clone = dict(row)
    clone["rebalance_action"] = action
    clone["rebalance_reason"] = reason
    return clone


def _bucket(row: dict[str, Any]) -> str:
    revision_type = str(row.get("revision_type") or "")
    if revision_type in {"unanchored_direct_answer", "rebalanced_unanchored_direct_answer"}:
        return "direct_answer"
    if revision_type.endswith("_bridge") or revision_type.startswith("prefix_"):
        return "decoder_bridge"
    if revision_type.startswith("carry_forward"):
        return "carry_forward"
    return "other"


def _bucket_rows(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(examples)
    rows = []
    for bucket in ["carry_forward", "direct_answer", "decoder_bridge", "other"]:
        subset = [row for row in examples if _bucket(row) == bucket]
        rows.append({"bucket": bucket, "count": len(subset), "share": round(len(subset) / total, 4) if total else 0.0})
    return rows


def _checks(seed: dict[str, Any], audit: dict[str, Any], source_examples: list[dict[str, Any]], output_examples: list[dict[str, Any]], bucket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_bucket = {str(row.get("bucket")): row for row in bucket_rows}
    direct_share = float(by_bucket.get("direct_answer", {}).get("share") or 0.0)
    carry_share = float(by_bucket.get("carry_forward", {}).get("share") or 0.0)
    bridge_share = float(by_bucket.get("decoder_bridge", {}).get("share") or 0.0)
    return [
        _check("decoder_anchor_seed_passed", seed.get("status") == "pass", seed.get("status"), "source decoder-anchor seed revision must pass"),
        _check("distribution_audit_passed", audit.get("status") == "pass", audit.get("status"), "distribution audit must pass"),
        _check("distribution_audit_requires_rebalance", as_dict(audit.get("summary")).get("rebalanced_seed_needed") is True, as_dict(audit.get("summary")).get("rebalanced_seed_needed"), "rebalance revision should follow an audit that requested rebalance"),
        _check("source_examples_present", bool(source_examples), len(source_examples), "source seed examples must be present"),
        _check("output_examples_present", bool(output_examples), len(output_examples), "rebalanced seed examples must be present"),
        _check("direct_answer_share_repaired", direct_share >= 0.2, direct_share, "direct answer share must reach the audit threshold"),
        _check("carry_forward_share_repaired", carry_share <= 0.5, carry_share, "carry-forward share must stay below the audit threshold"),
        _check("decoder_bridge_share_preserved", bridge_share >= 0.25, bridge_share, "decoder bridge share must remain above the audit threshold"),
        _check("seed_examples_have_text", all(str(row.get("text") or "").strip() for row in output_examples), len(output_examples), "all seed examples must have text"),
    ]


def _revision(status: str, source_examples: list[dict[str, Any]], output_examples: list[dict[str, Any]], rebalance_rows: list[dict[str, Any]], bucket_rows: list[dict[str, Any]], audit_summary: dict[str, Any]) -> dict[str, Any]:
    by_bucket = {str(row.get("bucket")): row for row in bucket_rows}
    return {
        "ready": status == "pass",
        "source_example_count": len(source_examples),
        "example_count": len(output_examples),
        "case_count": len(rebalance_rows),
        "carry_forward_count": by_bucket.get("carry_forward", {}).get("count", 0),
        "direct_answer_count": by_bucket.get("direct_answer", {}).get("count", 0),
        "decoder_bridge_count": by_bucket.get("decoder_bridge", {}).get("count", 0),
        "carry_forward_share": by_bucket.get("carry_forward", {}).get("share", 0.0),
        "direct_answer_share": by_bucket.get("direct_answer", {}).get("share", 0.0),
        "decoder_bridge_share": by_bucket.get("decoder_bridge", {}).get("share", 0.0),
        "dropped_carry_forward_count": sum(int(row.get("dropped_carry_forward_count") or 0) for row in rebalance_rows),
        "added_direct_answer_count": sum(int(row.get("added_direct_answer_count") or 0) for row in rebalance_rows),
        "source_distribution_risk_count": audit_summary.get("risk_count"),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_training_run",
        "next_step": "train_decoder_anchor_rebalanced_seed_revision" if status == "pass" else "repair_decoder_anchor_rebalanced_seed_revision",
    }


def _summary(status: str, checks: list[dict[str, Any]], revision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_rebalanced_seed_revision_ready": status == "pass" and revision.get("ready") is True,
        "source_example_count": revision.get("source_example_count"),
        "example_count": revision.get("example_count"),
        "case_count": revision.get("case_count"),
        "carry_forward_count": revision.get("carry_forward_count"),
        "direct_answer_count": revision.get("direct_answer_count"),
        "decoder_bridge_count": revision.get("decoder_bridge_count"),
        "carry_forward_share": revision.get("carry_forward_share"),
        "direct_answer_share": revision.get("direct_answer_share"),
        "decoder_bridge_share": revision.get("decoder_bridge_share"),
        "dropped_carry_forward_count": revision.get("dropped_carry_forward_count"),
        "added_direct_answer_count": revision.get("added_direct_answer_count"),
        "source_distribution_risk_count": revision.get("source_distribution_risk_count"),
        "proposed_next_artifact": revision.get("proposed_next_artifact"),
        "next_step": revision.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str) -> str:
    if status == "pass":
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision_ready"
    return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision"


def _interpretation(status: str, revision: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Rebalanced seed revision inputs are incomplete.", "next_action": "repair rebalanced seed revision"}
    return {
        "model_quality_claim": "training_data_revision_only",
        "reason": "The seed now caps carry-forward examples and upweights direct answers; capability still requires training and replay.",
        "next_action": revision.get("next_step"),
    }


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_CORPUS_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_JSONL_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_REBALANCED_SEED_REVISION_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision",
    "locate_decoder_anchor_distribution_audit",
    "locate_decoder_anchor_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
