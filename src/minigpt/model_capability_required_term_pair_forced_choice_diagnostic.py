from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_branch_retention_sweep import (
    REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_forced_choice_diagnostic_components import (
    select_forced_choice_runs,
    select_forced_choice_targets,
    summarize_forced_choice_prompt_rows,
    summarize_forced_choice_variants,
    summarize_required_term_pair_forced_choice_diagnostic,
)
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_forced_choice_diagnostic.json"
)
REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_forced_choice_diagnostic.txt"
)
REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_forced_choice_diagnostic.md"
)
REQUIRED_TERM_PAIR_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_forced_choice_diagnostic.html"
)

ForcedChoiceScoreFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_model_capability_required_term_pair_forced_choice_diagnostic_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_BRANCH_RETENTION_SWEEP_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_forced_choice_diagnostic(
    branch_retention_sweep: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    pair_limit: int | None = 1,
    run_limit: int | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    score_func: ForcedChoiceScoreFunc | None = None,
) -> dict[str, Any]:
    source_summary = as_dict(branch_retention_sweep.get("summary"))
    targets = select_forced_choice_targets(branch_retention_sweep, pair_limit=pair_limit)
    runs = select_forced_choice_runs(branch_retention_sweep, run_limit=run_limit)
    issues = _input_issues(branch_retention_sweep, targets, runs)

    score_rows: list[dict[str, Any]] = []
    if not issues:
        for target in targets:
            for run in [row for row in runs if str(row.get("pair_id") or "") == str(target.get("pair_id") or "")]:
                score_rows.extend(_score_run_choices(target, run, device=device, score_func=score_func))

    prompt_summaries = summarize_forced_choice_prompt_rows(score_rows)
    variant_summaries = summarize_forced_choice_variants(runs, prompt_summaries)
    summary = summarize_required_term_pair_forced_choice_diagnostic(
        targets,
        runs,
        score_rows,
        prompt_summaries,
        variant_summaries,
        source_summary=source_summary,
    )
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair forced-choice diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_branch_retention_sweep": str(source_path) if source_path else None,
        "out_dir": str(out_dir),
        "settings": {
            "pair_limit": pair_limit,
            "run_limit": run_limit,
            "device": device,
            "experiment_boundary": "teacher-forced scoring only; no new checkpoint training",
        },
        "source_baseline": _source_baseline(source_summary),
        "target_count": len(targets),
        "targets": targets,
        "run_count": len(runs),
        "runs": runs,
        "score_rows": score_rows,
        "prompt_summaries": prompt_summaries,
        "variant_summaries": variant_summaries,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _interpretation_reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _score_run_choices(
    target: dict[str, Any],
    run: dict[str, Any],
    *,
    device: str,
    score_func: ForcedChoiceScoreFunc | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scorer = score_func or _score_candidate_with_checkpoint
    term_names = [str(term) for term in target.get("term_names") or []]
    for prompt_row in list_of_dicts(target.get("terms")):
        prompt_term = str(prompt_row.get("term") or "")
        prompt = str(prompt_row.get("scaffold_prompt") or f"{prompt_term}:")
        for candidate in term_names:
            context = {
                "run_id": run.get("run_id"),
                "pair_id": target.get("pair_id"),
                "variant_id": run.get("variant_id"),
                "variant_label": run.get("variant_label"),
                "checkpoint_path": run.get("checkpoint_path"),
                "tokenizer_path": run.get("tokenizer_path"),
                "device": device,
                "prompt_term": prompt_term,
                "prompt": prompt,
                "candidate_term": candidate,
                "is_expected_candidate": candidate == prompt_term,
            }
            score = scorer(context)
            rows.append({**context, **score})
    return rows


def _score_candidate_with_checkpoint(context: dict[str, Any]) -> dict[str, Any]:
    import torch
    from torch.nn import functional as F

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    device = torch.device(str(context.get("device") or "cpu"))
    checkpoint_path = Path(str(context["checkpoint_path"]))
    tokenizer_path = Path(str(context["tokenizer_path"]))
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    model = MiniGPT(GPTConfig(**checkpoint["config"])).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt_ids = tokenizer.encode(str(context["prompt"]))
    candidate_ids = tokenizer.encode(str(context["candidate_term"]))
    if not prompt_ids or not candidate_ids:
        return _empty_score(candidate_ids)

    running = list(prompt_ids)
    logprobs: list[float] = []
    first_rank: int | None = None
    with torch.no_grad():
        for index, token_id in enumerate(candidate_ids):
            idx = torch.tensor([running[-model.config.block_size :]], dtype=torch.long, device=device)
            logits, _ = model(idx)
            log_probs = F.log_softmax(logits[0, -1], dim=-1)
            token_logprob = float(log_probs[int(token_id)].item())
            logprobs.append(token_logprob)
            if index == 0:
                first_rank = _rank_token(log_probs, int(token_id))
            running.append(int(token_id))

    total_nll = round(-sum(logprobs), 6)
    avg_nll = round(total_nll / len(logprobs), 6) if logprobs else None
    return {
        "status": "pass",
        "token_count": len(candidate_ids),
        "candidate_token_ids": candidate_ids,
        "total_nll": total_nll,
        "avg_nll": avg_nll,
        "first_token_rank": first_rank,
        "first_token_logprob": round(logprobs[0], 6) if logprobs else None,
    }


def _rank_token(log_probs: Any, token_id: int) -> int:
    target = float(log_probs[token_id].item())
    better = int((log_probs > target).sum().item())
    return better + 1


def _empty_score(candidate_ids: list[int]) -> dict[str, Any]:
    return {
        "status": "fail",
        "token_count": len(candidate_ids),
        "candidate_token_ids": candidate_ids,
        "total_nll": None,
        "avg_nll": None,
        "first_token_rank": None,
        "first_token_logprob": None,
    }


def _input_issues(report: dict[str, Any], targets: list[dict[str, Any]], runs: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not report:
        issues.append("source branch-retention sweep report is missing or invalid")
    if report and report.get("status") != "pass":
        issues.append("source branch-retention sweep report is not pass")
    if not targets:
        issues.append("source branch-retention sweep has no forced-choice target")
    if not runs:
        issues.append("source branch-retention sweep has no checkpoint runs to score")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_forced_choice_diagnostic"
    decision = str(summary.get("forced_choice_diagnostic_decision") or "")
    if decision == "forced_choice_full_match_observed":
        return "required_term_pair_forced_choice_internal_match"
    if decision == "forced_choice_partial_match_only":
        return "required_term_pair_forced_choice_partial"
    return "required_term_pair_forced_choice_not_recovered"


def _source_baseline(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_retention_sweep_decision": summary.get("branch_retention_sweep_decision"),
        "pair_full_hit_variant_count": summary.get("pair_full_hit_variant_count"),
        "best_variant_id": summary.get("best_variant_id"),
    }


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if int(summary.get("forced_choice_full_match_variant_count") or 0) > 0:
        return "forced_choice_internal_signal_only"
    return "not_claimed"


def _interpretation_reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The source branch-retention report was not scoreable."
    if int(summary.get("forced_choice_full_match_variant_count") or 0) > 0:
        return "At least one checkpoint internally preferred the expected term for every pair prompt."
    if int(summary.get("expected_best_count") or 0) > 0:
        return "Some prompts internally preferred the expected term, but no checkpoint matched the whole pair."
    return "Teacher-forced scoring did not prefer the expected branch for any prompt."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair scoreable checkpoint inputs before more model experiments"
    if int(summary.get("forced_choice_full_match_variant_count") or 0) > 0:
        return "compare forced-choice winners with generation decoding to isolate sampling/decoding loss"
    return "treat the issue as learned preference collapse and avoid more corpus weighting until model capacity or objective changes"
