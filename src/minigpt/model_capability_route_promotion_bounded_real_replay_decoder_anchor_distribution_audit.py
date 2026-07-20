from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_failure_diagnostic import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_FAILURE_DIAGNOSTIC_JSON_FILENAME,
)
from minigpt.model_capability_route_promotion_bounded_real_replay_decoder_anchor_seed_revision import (
    MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME,
)
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import check_entry as _check


MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_JSON_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.json"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_CSV_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.csv"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_TEXT_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.txt"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_MARKDOWN_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.md"
MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_HTML_FILENAME = "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit.html"


def locate_decoder_anchor_seed_revision(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_SEED_REVISION_JSON_FILENAME
    return source


def locate_decoder_anchor_failure_diagnostic(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_FAILURE_DIAGNOSTIC_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("decoder anchor distribution audit input must be a JSON object")
    return dict(payload)


def build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit(
    decoder_anchor_seed_revision: dict[str, Any],
    decoder_anchor_failure_diagnostic: dict[str, Any],
    *,
    corpus_path: str | Path,
    seed_revision_path: str | Path | None = None,
    diagnostic_path: str | Path | None = None,
    title: str = "MiniGPT model capability route promotion bounded real replay decoder anchor distribution audit",
    generated_at: str | None = None,
) -> dict[str, Any]:
    corpus = Path(corpus_path).read_text(encoding="utf-8-sig") if Path(corpus_path).is_file() else ""
    seed_summary = as_dict(decoder_anchor_seed_revision.get("summary"))
    diagnostic_summary = as_dict(decoder_anchor_failure_diagnostic.get("summary"))
    examples = list_of_dicts(decoder_anchor_seed_revision.get("seed_examples"))
    bucket_rows = _bucket_rows(examples)
    revision_rows = _revision_rows(examples)
    case_rows = _case_rows(examples)
    risks = _risks(bucket_rows, diagnostic_summary)
    checks = _checks(decoder_anchor_seed_revision, decoder_anchor_failure_diagnostic, corpus, examples, bucket_rows)
    issues = [row for row in checks if row["status"] != "pass"]
    status = "pass" if not issues else "fail"
    audit = _audit(status, examples, bucket_rows, revision_rows, case_rows, risks, corpus, diagnostic_summary)
    return {
        "schema_version": 1,
        "title": title,
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, audit),
        "failed_count": len(issues),
        "issues": issues,
        "source_decoder_anchor_seed_revision": str(seed_revision_path or ""),
        "source_decoder_anchor_failure_diagnostic": str(diagnostic_path or ""),
        "source_corpus": str(corpus_path),
        "source_summaries": {"seed_revision": seed_summary, "failure_diagnostic": diagnostic_summary},
        "bucket_rows": bucket_rows,
        "revision_rows": revision_rows,
        "case_rows": case_rows,
        "risk_rows": risks,
        "check_rows": checks,
        "distribution_audit": audit,
        "summary": _summary(status, checks, audit),
        "interpretation": _interpretation(status, audit),
    }


def resolve_exit_code(report: dict[str, Any], *, require_audit_ready: bool) -> int:
    return 1 if require_audit_ready and report.get("status") != "pass" else 0


def _bucket(revision_type: str) -> str:
    if revision_type == "unanchored_direct_answer":
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
        subset = [row for row in examples if _bucket(str(row.get("revision_type") or "")) == bucket]
        rows.append(
            {
                "bucket": bucket,
                "count": len(subset),
                "share": round(len(subset) / total, 4) if total else 0.0,
                "avg_prompt_chars": _avg(len(str(row.get("prompt") or "")) for row in subset),
                "avg_completion_chars": _avg(len(str(row.get("completion") or "")) for row in subset),
            }
        )
    return rows


def _revision_rows(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(examples)
    rows = []
    for revision_type in sorted({str(row.get("revision_type") or "") for row in examples}):
        subset = [row for row in examples if str(row.get("revision_type") or "") == revision_type]
        rows.append({"revision_type": revision_type, "bucket": _bucket(revision_type), "count": len(subset), "share": round(len(subset) / total, 4) if total else 0.0})
    return rows


def _case_rows(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for case_id in sorted({str(row.get("case_id") or "") for row in examples}):
        subset = [row for row in examples if str(row.get("case_id") or "") == case_id]
        rows.append(
            {
                "case_id": case_id,
                "example_count": len(subset),
                "carry_forward_count": sum(1 for row in subset if _bucket(str(row.get("revision_type") or "")) == "carry_forward"),
                "direct_answer_count": sum(1 for row in subset if _bucket(str(row.get("revision_type") or "")) == "direct_answer"),
                "decoder_bridge_count": sum(1 for row in subset if _bucket(str(row.get("revision_type") or "")) == "decoder_bridge"),
            }
        )
    return rows


def _risks(bucket_rows: list[dict[str, Any]], diagnostic_summary: dict[str, Any]) -> list[dict[str, Any]]:
    by_bucket = {str(row.get("bucket")): row for row in bucket_rows}
    direct_share = float(by_bucket.get("direct_answer", {}).get("share") or 0.0)
    bridge_share = float(by_bucket.get("decoder_bridge", {}).get("share") or 0.0)
    carry_share = float(by_bucket.get("carry_forward", {}).get("share") or 0.0)
    case_count = int(diagnostic_summary.get("case_count") or 0)
    zero_hit_count = int(diagnostic_summary.get("zero_hit_case_count") or 0)
    risks = []
    if direct_share < 0.2:
        risks.append({"risk_id": "direct_answer_underweighted", "severity": "high", "actual": direct_share, "threshold": 0.2, "detail": "Unanchored direct-answer rows are too sparse for a zero-hit replay failure."})
    if carry_share > 0.5:
        risks.append({"risk_id": "carry_forward_dominates_seed", "severity": "medium", "actual": carry_share, "threshold": 0.5, "detail": "Carry-forward rows dominate the decoder-anchor corpus."})
    if bridge_share < 0.25:
        risks.append({"risk_id": "bridge_examples_underweighted", "severity": "medium", "actual": bridge_share, "threshold": 0.25, "detail": "Bridge rows are too sparse to train forced-prefix completion reliably."})
    if case_count and zero_hit_count == case_count:
        risks.append({"risk_id": "all_replay_cases_zero_hit", "severity": "high", "actual": zero_hit_count, "threshold": case_count, "detail": "All bounded replay cases produced zero required-term hits."})
    return risks


def _checks(seed: dict[str, Any], diagnostic: dict[str, Any], corpus: str, examples: list[dict[str, Any]], bucket_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _check("decoder_anchor_seed_passed", seed.get("status") == "pass", seed.get("status"), "decoder anchor seed revision must pass"),
        _check("decoder_anchor_failure_diagnostic_passed", diagnostic.get("status") == "pass", diagnostic.get("status"), "decoder anchor failure diagnostic must pass"),
        _check("seed_examples_present", bool(examples), len(examples), "seed examples must be present"),
        _check("bucket_rows_present", bool(bucket_rows), len(bucket_rows), "bucket rows must be computed"),
        _check("corpus_present", bool(corpus.strip()), len(corpus), "corpus must be readable"),
    ]


def _audit(
    status: str,
    examples: list[dict[str, Any]],
    bucket_rows: list[dict[str, Any]],
    revision_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    corpus: str,
    diagnostic_summary: dict[str, Any],
) -> dict[str, Any]:
    by_bucket = {str(row.get("bucket")): row for row in bucket_rows}
    return {
        "ready": status == "pass",
        "example_count": len(examples),
        "corpus_chars": len(corpus),
        "case_count": len(case_rows),
        "revision_type_count": len(revision_rows),
        "carry_forward_share": by_bucket.get("carry_forward", {}).get("share", 0.0),
        "direct_answer_share": by_bucket.get("direct_answer", {}).get("share", 0.0),
        "decoder_bridge_share": by_bucket.get("decoder_bridge", {}).get("share", 0.0),
        "zero_hit_case_count": diagnostic_summary.get("zero_hit_case_count"),
        "risk_count": len(risks),
        "rebalanced_seed_needed": bool(risks),
        "proposed_next_artifact": "model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_seed_revision",
        "next_step": "build_decoder_anchor_rebalanced_seed_revision" if status == "pass" else "repair_decoder_anchor_distribution_audit_inputs",
    }


def _summary(status: str, checks: list[dict[str, Any]], audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "decoder_anchor_distribution_audit_ready": status == "pass" and audit.get("ready") is True,
        "example_count": audit.get("example_count"),
        "corpus_chars": audit.get("corpus_chars"),
        "case_count": audit.get("case_count"),
        "revision_type_count": audit.get("revision_type_count"),
        "carry_forward_share": audit.get("carry_forward_share"),
        "direct_answer_share": audit.get("direct_answer_share"),
        "decoder_bridge_share": audit.get("decoder_bridge_share"),
        "zero_hit_case_count": audit.get("zero_hit_case_count"),
        "risk_count": audit.get("risk_count"),
        "rebalanced_seed_needed": audit.get("rebalanced_seed_needed"),
        "proposed_next_artifact": audit.get("proposed_next_artifact"),
        "next_step": audit.get("next_step"),
        "failed_check_count": sum(1 for row in checks if row["status"] != "pass"),
    }


def _decision(status: str, audit: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit"
    if audit.get("rebalanced_seed_needed") is True:
        return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_needs_rebalance"
    return "model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_balanced"


def _interpretation(status: str, audit: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {"model_quality_claim": "not_claimed", "reason": "Distribution audit inputs are incomplete.", "next_action": "repair audit inputs"}
    if audit.get("rebalanced_seed_needed") is True:
        return {"model_quality_claim": "not_improved", "reason": "Seed distribution is not balanced for the observed zero-hit decoder failure.", "next_action": audit.get("next_step")}
    return {"model_quality_claim": "not_claimed", "reason": "Distribution looks balanced; inspect decoding or capacity next.", "next_action": audit.get("next_step")}


def _avg(values: Any) -> float:
    items = list(values)
    return round(sum(items) / len(items), 2) if items else 0.0


__all__ = [
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_CSV_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_HTML_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_JSON_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_MARKDOWN_FILENAME",
    "MODEL_CAPABILITY_ROUTE_PROMOTION_BOUNDED_REAL_REPLAY_DECODER_ANCHOR_DISTRIBUTION_AUDIT_TEXT_FILENAME",
    "build_model_capability_route_promotion_bounded_real_replay_decoder_anchor_distribution_audit",
    "locate_decoder_anchor_failure_diagnostic",
    "locate_decoder_anchor_seed_revision",
    "read_json_report",
    "resolve_exit_code",
]
