from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Sequence

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.model_capability_required_term_pair_fixed_retention_objective_comparison import TARGET_TERMS
from minigpt.report_utils import as_dict, number_or_none, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME = (
    "model_capability_required_term_pair_refresh_forced_choice_diagnostic.json"
)
PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_CSV_FILENAME = (
    "model_capability_required_term_pair_refresh_forced_choice_diagnostic.csv"
)
PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME = (
    "model_capability_required_term_pair_refresh_forced_choice_diagnostic.txt"
)
PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME = (
    "model_capability_required_term_pair_refresh_forced_choice_diagnostic.md"
)
PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME = (
    "model_capability_required_term_pair_refresh_forced_choice_diagnostic.html"
)

ForcedChoiceScoreFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_refresh_forced_choice_report(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("refresh forced-choice diagnostic input must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_refresh_forced_choice_diagnostic(
    reports: Sequence[dict[str, Any]],
    *,
    source_paths: Sequence[str | Path] | None = None,
    source_labels: Sequence[str] | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    score_func: ForcedChoiceScoreFunc | None = None,
) -> dict[str, Any]:
    source_rows = [
        _source_row(index, report, _source_path(source_paths, index), _source_label(source_labels, index, report))
        for index, report in enumerate(reports)
    ]
    issues = _input_issues(source_rows)
    score_rows: list[dict[str, Any]] = []
    if not issues:
        scorer = score_func or _cached_scorer(device=device)
        for source in source_rows:
            score_rows.extend(_score_source(source, scorer=scorer, device=device))
    prompt_summaries = _prompt_summaries(score_rows)
    source_summaries = _source_summaries(source_rows, prompt_summaries)
    summary = _summary(source_rows, prompt_summaries, source_summaries)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair refresh forced-choice diagnostic",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "settings": {"device": device, "candidate_terms": list(TARGET_TERMS), "experiment_boundary": "teacher-forced scoring only; no generation and no retraining"},
        "source_reports": source_rows,
        "score_rows": score_rows,
        "prompt_summaries": prompt_summaries,
        "source_summaries": source_summaries,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _source_path(paths: Sequence[str | Path] | None, index: int) -> str:
    if paths is None or index >= len(paths):
        return ""
    return str(paths[index])


def _source_label(labels: Sequence[str] | None, index: int, report: dict[str, Any]) -> str:
    if labels is not None and index < len(labels) and labels[index]:
        return str(labels[index])
    mode = str(as_dict(report.get("settings")).get("corpus_mode") or "")
    return mode or f"refresh-forced-choice-{index + 1}"


def _source_row(index: int, report: dict[str, Any], path: str, label: str) -> dict[str, Any]:
    summary = as_dict(report.get("summary"))
    settings = as_dict(report.get("settings"))
    training = as_dict(report.get("training"))
    return {
        "index": index,
        "source_label": label,
        "source_path": path,
        "status": report.get("status"),
        "decision": report.get("decision"),
        "corpus_mode": settings.get("corpus_mode"),
        "seed": settings.get("seed"),
        "training_status": summary.get("training_status"),
        "checkpoint_exists": bool(summary.get("checkpoint_exists")),
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
    }


def _input_issues(source_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not source_rows:
        issues.append("at least one refresh report is required")
    for row in source_rows:
        label = row.get("source_label")
        if row.get("status") != "pass":
            issues.append(f"{label} report status is not pass")
        if row.get("training_status") != "pass":
            issues.append(f"{label} training status is not pass")
        if not row.get("checkpoint_exists"):
            issues.append(f"{label} checkpoint is missing")
        if not row.get("checkpoint_path"):
            issues.append(f"{label} checkpoint path is missing")
        if not row.get("tokenizer_path"):
            issues.append(f"{label} tokenizer path is missing")
    return issues


def _score_source(source: dict[str, Any], *, scorer: ForcedChoiceScoreFunc, device: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prompt_term in TARGET_TERMS:
        prompt = f"{prompt_term}="
        for candidate in TARGET_TERMS:
            context = {
                "source_label": source.get("source_label"),
                "source_path": source.get("source_path"),
                "corpus_mode": source.get("corpus_mode"),
                "seed": source.get("seed"),
                "checkpoint_path": source.get("checkpoint_path"),
                "tokenizer_path": source.get("tokenizer_path"),
                "device": device,
                "prompt_term": prompt_term,
                "prompt": prompt,
                "candidate_term": candidate,
                "is_expected_candidate": candidate == prompt_term,
            }
            score = scorer(context)
            rows.append({**context, **score})
    return rows


def _cached_scorer(*, device: str) -> ForcedChoiceScoreFunc:
    cache: dict[tuple[str, str], Any] = {}

    def score(context: dict[str, Any]) -> dict[str, Any]:
        key = (str(context.get("checkpoint_path")), str(context.get("tokenizer_path")))
        if key not in cache:
            cache[key] = _load_model_and_tokenizer(context, device=device)
        return _score_with_loaded(context, cache[key], device=device)

    return score


def _load_model_and_tokenizer(context: dict[str, Any], *, device: str) -> tuple[Any, Any]:
    import torch

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    torch_device = torch.device(device)
    checkpoint = torch.load(Path(str(context["checkpoint_path"])), map_location=torch_device, weights_only=False)
    tokenizer = load_tokenizer(Path(str(context["tokenizer_path"])))
    model = MiniGPT(GPTConfig(**checkpoint["config"])).to(torch_device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, tokenizer


def _score_with_loaded(context: dict[str, Any], loaded: tuple[Any, Any], *, device: str) -> dict[str, Any]:
    import torch
    from torch.nn import functional as F

    model, tokenizer = loaded
    torch_device = torch.device(device)
    prompt_ids = tokenizer.encode(str(context["prompt"]))
    candidate_ids = tokenizer.encode(str(context["candidate_term"]))
    if not prompt_ids or not candidate_ids:
        return _empty_score(candidate_ids)
    running = list(prompt_ids)
    logprobs: list[float] = []
    first_rank: int | None = None
    with torch.no_grad():
        for index, token_id in enumerate(candidate_ids):
            idx = torch.tensor([running[-model.config.block_size :]], dtype=torch.long, device=torch_device)
            logits, _ = model(idx)
            log_probs = F.log_softmax(logits[0, -1], dim=-1)
            logprobs.append(float(log_probs[int(token_id)].item()))
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
    return int((log_probs > target).sum().item()) + 1


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


def _prompt_summaries(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in score_rows:
        groups.setdefault((str(row.get("source_label")), str(row.get("prompt_term"))), []).append(row)
    summaries: list[dict[str, Any]] = []
    for (source_label, prompt_term), rows in sorted(groups.items()):
        best = _best_score_row(rows)
        expected = next((row for row in rows if row.get("is_expected_candidate")), {})
        summaries.append(
            {
                "source_label": source_label,
                "prompt_term": prompt_term,
                "best_candidate": best.get("candidate_term"),
                "expected_candidate": prompt_term,
                "expected_best": best.get("candidate_term") == prompt_term,
                "expected_avg_nll": expected.get("avg_nll"),
                "best_avg_nll": best.get("avg_nll"),
                "expected_first_token_rank": expected.get("first_token_rank"),
            }
        )
    return summaries


def _best_score_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [row for row in rows if number_or_none(row.get("avg_nll")) is not None]
    if not scored:
        return {}
    return min(scored, key=lambda row: float(row.get("avg_nll")))


def _source_summaries(source_rows: list[dict[str, Any]], prompt_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for source in source_rows:
        label = str(source.get("source_label"))
        scoped = [row for row in prompt_summaries if row.get("source_label") == label]
        expected_best_terms = sorted(str(row.get("prompt_term")) for row in scoped if row.get("expected_best"))
        summaries.append(
            {
                "source_label": label,
                "corpus_mode": source.get("corpus_mode"),
                "expected_best_terms": expected_best_terms,
                "expected_best_count": len(expected_best_terms),
                "forced_choice_full_match": set(TARGET_TERMS).issubset(expected_best_terms),
            }
        )
    return summaries


def _summary(
    source_rows: list[dict[str, Any]],
    prompt_summaries: list[dict[str, Any]],
    source_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "source_report_count": len(source_rows),
        "prompt_summary_count": len(prompt_summaries),
        "source_summary_count": len(source_summaries),
        "expected_best_prompt_count": sum(1 for row in prompt_summaries if row.get("expected_best")),
        "fixed_prompt_expected_best_count": sum(1 for row in prompt_summaries if row.get("prompt_term") == "fixed" and row.get("expected_best")),
        "loss_prompt_expected_best_count": sum(1 for row in prompt_summaries if row.get("prompt_term") == "loss" and row.get("expected_best")),
        "forced_choice_full_match_source_count": sum(1 for row in source_summaries if row.get("forced_choice_full_match")),
        "best_internal_sources": [row.get("source_label") for row in source_summaries if row.get("forced_choice_full_match")],
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_refresh_forced_choice_inputs"
    if int(summary.get("forced_choice_full_match_source_count") or 0) > 0:
        return "refresh_forced_choice_internal_pair_match"
    if int(summary.get("expected_best_prompt_count") or 0) > 0:
        return "refresh_forced_choice_partial_internal_match"
    return "refresh_forced_choice_not_recovered"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        return {
            "model_quality_claim": "not_claimed",
            "reason": "The refresh reports are not scoreable.",
            "next_action": "repair forced-choice inputs before another objective design",
        }
    if int(summary.get("forced_choice_full_match_source_count") or 0) > 0:
        return {
            "model_quality_claim": "forced_choice_internal_signal_only",
            "reason": "At least one checkpoint internally prefers the expected term for both prompts.",
            "next_action": "compare internal preference with generation failures before more training",
        }
    if int(summary.get("expected_best_prompt_count") or 0) > 0:
        return {
            "model_quality_claim": "partial_internal_signal_only",
            "reason": "Some prompts internally prefer the expected term, but no checkpoint matches the pair.",
            "next_action": "use prompt-level internal preference to design the next objective",
        }
    return {
        "model_quality_claim": "not_claimed",
        "reason": "Teacher-forced scoring does not prefer the expected terms.",
        "next_action": "change objective shape rather than decoding settings",
    }


__all__ = [
    "PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_CSV_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_HTML_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_JSON_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_MARKDOWN_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_DIAGNOSTIC_TEXT_FILENAME",
    "build_model_capability_required_term_pair_refresh_forced_choice_diagnostic",
    "locate_refresh_forced_choice_report",
    "read_json_report",
    "resolve_exit_code",
]
