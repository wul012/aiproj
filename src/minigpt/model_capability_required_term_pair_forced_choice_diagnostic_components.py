from __future__ import annotations

from typing import Any

from minigpt.report_utils import list_of_dicts


def select_forced_choice_targets(report: dict[str, Any], *, pair_limit: int | None = 1) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for target in list_of_dicts(report.get("targets")):
        term_rows = list_of_dicts(target.get("terms"))
        term_names = [str(term) for term in target.get("term_names") or []]
        if len(term_rows) < 2 or len(term_names) < 2:
            continue
        targets.append(
            {
                "pair_id": str(target.get("pair_id") or f"pair-{len(targets) + 1}"),
                "term_names": term_names,
                "terms": term_rows,
                "focus_missed_term": target.get("focus_missed_term"),
                "source_hit_terms": [str(term) for term in target.get("source_hit_terms") or []],
            }
        )
    if pair_limit is not None and pair_limit >= 0:
        return targets[:pair_limit]
    return targets


def select_forced_choice_runs(report: dict[str, Any], *, run_limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list_of_dicts(report.get("training_rows")):
        if not row.get("checkpoint_exists"):
            continue
        checkpoint = str(row.get("checkpoint_path") or "")
        tokenizer = str(row.get("tokenizer_path") or "")
        if not checkpoint or not tokenizer:
            continue
        rows.append(
            {
                "run_id": row.get("branch_retention_run_id") or row.get("loss_branch_run_id") or row.get("contrast_free_run_id"),
                "pair_id": row.get("pair_id"),
                "variant_id": row.get("variant_id"),
                "variant_label": row.get("variant_label"),
                "checkpoint_path": checkpoint,
                "tokenizer_path": tokenizer,
                "checkpoint_exists": True,
            }
        )
    if run_limit is not None and run_limit >= 0:
        return rows[:run_limit]
    return rows


def summarize_forced_choice_prompt_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            str(row.get("run_id") or ""),
            str(row.get("variant_id") or ""),
            str(row.get("prompt_term") or ""),
        )
        grouped.setdefault(key, []).append(row)

    summaries: list[dict[str, Any]] = []
    for (_run_id, _variant_id, _prompt_term), group in sorted(grouped.items()):
        expected = next((row for row in group if row.get("is_expected_candidate")), None)
        best = _best_candidate(group)
        expected_rank = _candidate_rank(group, str(expected.get("candidate_term") or "")) if expected else None
        expected_avg = float(expected.get("avg_nll")) if expected and expected.get("avg_nll") is not None else None
        best_avg = float(best.get("avg_nll")) if best.get("avg_nll") is not None else None
        summaries.append(
            {
                "run_id": group[0].get("run_id"),
                "pair_id": group[0].get("pair_id"),
                "variant_id": group[0].get("variant_id"),
                "variant_label": group[0].get("variant_label"),
                "prompt_term": group[0].get("prompt_term"),
                "prompt": group[0].get("prompt"),
                "expected_term": expected.get("candidate_term") if expected else None,
                "best_candidate_term": best.get("candidate_term"),
                "expected_is_best": bool(expected and best and expected.get("candidate_term") == best.get("candidate_term")),
                "expected_rank": expected_rank,
                "expected_avg_nll": expected_avg,
                "best_avg_nll": best_avg,
                "expected_margin_vs_best": round(expected_avg - best_avg, 6)
                if expected_avg is not None and best_avg is not None
                else None,
                "candidate_count": len(group),
            }
        )
    return summaries


def summarize_forced_choice_variants(
    runs: list[dict[str, Any]],
    prompt_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in runs:
        run_id = str(run.get("run_id") or "")
        prompts = [row for row in prompt_summaries if str(row.get("run_id") or "") == run_id]
        expected_best_count = sum(1 for row in prompts if row.get("expected_is_best"))
        best_by_prompt = {
            str(row.get("prompt_term") or ""): row.get("best_candidate_term")
            for row in prompts
            if str(row.get("prompt_term") or "")
        }
        rows.append(
            {
                "run_id": run_id,
                "pair_id": run.get("pair_id"),
                "variant_id": run.get("variant_id"),
                "variant_label": run.get("variant_label"),
                "prompt_count": len(prompts),
                "expected_best_count": expected_best_count,
                "expected_best_rate": round(expected_best_count / len(prompts), 4) if prompts else 0.0,
                "forced_choice_full_match": bool(prompts) and expected_best_count == len(prompts),
                "best_candidate_by_prompt": best_by_prompt,
                "collapse_candidate": _collapse_candidate(best_by_prompt),
            }
        )
    return rows


def summarize_required_term_pair_forced_choice_diagnostic(
    targets: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    prompt_summaries: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_summary or {}
    full_match_count = sum(1 for row in variant_summaries if row.get("forced_choice_full_match"))
    expected_best_count = sum(1 for row in prompt_summaries if row.get("expected_is_best"))
    collapse_counts = _collapse_counts(variant_summaries)
    total_prompts = len(prompt_summaries)
    best = _best_variant(variant_summaries)
    return {
        "forced_choice_diagnostic_decision": _diagnostic_decision(targets, runs, score_rows, full_match_count, expected_best_count),
        "source_branch_retention_sweep_decision": source.get("branch_retention_sweep_decision"),
        "source_pair_full_hit_variant_count": int(source.get("pair_full_hit_variant_count") or 0),
        "target_count": len(targets),
        "run_count": len(runs),
        "score_row_count": len(score_rows),
        "prompt_summary_count": total_prompts,
        "expected_best_count": expected_best_count,
        "expected_best_rate": round(expected_best_count / total_prompts, 4) if total_prompts else 0.0,
        "forced_choice_full_match_variant_count": full_match_count,
        "collapse_candidate_counts": collapse_counts,
        "best_variant_id": best.get("variant_id"),
        "best_variant_expected_best_count": best.get("expected_best_count"),
        "best_variant_forced_choice_full_match": best.get("forced_choice_full_match"),
    }


def _best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return min(rows, key=lambda row: (float(row.get("avg_nll") or 999999.0), str(row.get("candidate_term") or "")))


def _candidate_rank(rows: list[dict[str, Any]], candidate: str) -> int | None:
    ranked = sorted(rows, key=lambda row: (float(row.get("avg_nll") or 999999.0), str(row.get("candidate_term") or "")))
    for index, row in enumerate(ranked, start=1):
        if str(row.get("candidate_term") or "") == candidate:
            return index
    return None


def _collapse_candidate(best_by_prompt: dict[str, Any]) -> str | None:
    values = [str(value) for value in best_by_prompt.values() if value]
    if values and len(set(values)) == 1:
        return values[0]
    return None


def _collapse_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        candidate = str(row.get("collapse_candidate") or "")
        if candidate:
            counts[candidate] = counts.get(candidate, 0) + 1
    return dict(sorted(counts.items()))


def _best_variant(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return max(
        rows,
        key=lambda row: (
            bool(row.get("forced_choice_full_match")),
            int(row.get("expected_best_count") or 0),
            str(row.get("variant_id") or ""),
        ),
    )


def _diagnostic_decision(
    targets: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    full_match_count: int,
    expected_best_count: int,
) -> str:
    if not targets:
        return "forced_choice_no_targets"
    if not runs:
        return "forced_choice_no_checkpoint_runs"
    if not score_rows:
        return "forced_choice_no_scores"
    if full_match_count > 0:
        return "forced_choice_full_match_observed"
    if expected_best_count > 0:
        return "forced_choice_partial_match_only"
    return "forced_choice_no_expected_preference"
