from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now
from minigpt.report_check_common import resolve_exit_code_strict as resolve_exit_code


PAIR_REFRESH_FORCED_CHOICE_JSON_FILENAME = "model_capability_required_term_pair_refresh_forced_choice.json"
PAIR_REFRESH_FORCED_CHOICE_CSV_FILENAME = "model_capability_required_term_pair_refresh_forced_choice.csv"
PAIR_REFRESH_FORCED_CHOICE_TEXT_FILENAME = "model_capability_required_term_pair_refresh_forced_choice.txt"
PAIR_REFRESH_FORCED_CHOICE_MARKDOWN_FILENAME = "model_capability_required_term_pair_refresh_forced_choice.md"
PAIR_REFRESH_FORCED_CHOICE_HTML_FILENAME = "model_capability_required_term_pair_refresh_forced_choice.html"

ScoreFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_pair_refresh_forced_choice_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    direct = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    if direct.is_file():
        return direct
    matches = sorted(source.rglob(PAIR_COEXISTENCE_REFRESH_JSON_FILENAME)) if source.is_dir() else []
    if matches:
        return matches[0]
    return direct


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair refresh forced-choice source must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_refresh_forced_choice(
    refresh_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    device: str = "cpu",
    generated_at: str | None = None,
    score_func: ScoreFunc | None = None,
) -> dict[str, Any]:
    training = as_dict(refresh_report.get("training"))
    replay = as_dict(refresh_report.get("replay_report"))
    checkpoint_path = str(training.get("checkpoint_path") or "")
    tokenizer_path = str(training.get("tokenizer_path") or "")
    terms = _terms(replay)
    candidates = [str(term.get("term")) for term in terms if str(term.get("term") or "")]
    issues = _input_issues(training, checkpoint_path, tokenizer_path, terms, score_func=score_func)

    score_rows: list[dict[str, Any]] = []
    if not issues:
        scorer = score_func or _score_candidate_with_checkpoint
        for term in terms:
            prompt_term = str(term.get("term"))
            prompt = str(term.get("scaffold_prompt") or f"{prompt_term}:")
            for candidate in candidates:
                context = {
                    "checkpoint_path": checkpoint_path,
                    "tokenizer_path": tokenizer_path,
                    "device": device,
                    "prompt_term": prompt_term,
                    "prompt": prompt,
                    "candidate_term": candidate,
                    "is_expected_candidate": candidate == prompt_term,
                }
                score_rows.append(_score_row(scorer, context))

    prompt_rows = _prompt_rows(score_rows)
    summary = _summary(prompt_rows, score_rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair refresh forced-choice",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_coexistence_refresh": "" if source_path is None else str(source_path),
        "out_dir": str(out_dir),
        "settings": {
            "device": device,
            "experiment_boundary": "teacher-forced fixed/loss candidate scoring over one refresh checkpoint; no retraining",
        },
        "training": {
            "checkpoint_path": checkpoint_path,
            "tokenizer_path": tokenizer_path,
            "checkpoint_exists": Path(checkpoint_path).is_file(),
            "tokenizer_exists": Path(tokenizer_path).is_file(),
        },
        "score_rows": score_rows,
        "prompt_rows": prompt_rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def _terms(replay: dict[str, Any]) -> list[dict[str, Any]]:
    terms = list_of_dicts(replay.get("terms"))
    if terms:
        return terms
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in list_of_dicts(replay.get("case_rows")):
        term = str(row.get("term") or "").strip()
        if term and term not in seen:
            seen.add(term)
            rows.append({"term": term, "scaffold_prompt": row.get("prompt") or f"{term}:"})
    return rows


def _input_issues(
    training: dict[str, Any],
    checkpoint_path: str,
    tokenizer_path: str,
    terms: list[dict[str, Any]],
    *,
    score_func: ScoreFunc | None,
) -> list[str]:
    issues: list[str] = []
    if not training:
        issues.append("refresh report has no training object")
    if len(terms) < 2:
        issues.append("refresh report has fewer than two terms to compare")
    if score_func is None:
        if not checkpoint_path or not Path(checkpoint_path).is_file():
            issues.append("checkpoint_path is missing or does not exist")
        if not tokenizer_path or not Path(tokenizer_path).is_file():
            issues.append("tokenizer_path is missing or does not exist")
    return issues


def _score_row(scorer: ScoreFunc, context: dict[str, Any]) -> dict[str, Any]:
    try:
        score = scorer(context)
        status = str(score.get("status") or "pass")
        error = str(score.get("error") or "")
    except Exception as exc:  # pragma: no cover - defensive report boundary
        score = {}
        status = "fail"
        error = f"{type(exc).__name__}: {exc}"
    return {
        **context,
        **score,
        "status": status,
        "error": error,
    }


def _score_candidate_with_checkpoint(context: dict[str, Any]) -> dict[str, Any]:
    import torch
    from torch.nn import functional as F

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    device = torch.device(str(context.get("device") or "cpu"))
    checkpoint = torch.load(context["checkpoint_path"], map_location=device, weights_only=False)
    tokenizer = load_tokenizer(context["tokenizer_path"])
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
    return {
        "status": "pass",
        "token_count": len(candidate_ids),
        "candidate_token_ids": candidate_ids,
        "total_nll": total_nll,
        "avg_nll": round(total_nll / len(candidate_ids), 6),
        "first_token_rank": first_rank,
        "first_token_logprob": round(logprobs[0], 6) if logprobs else None,
    }


def _rank_token(log_probs: Any, token_id: int) -> int:
    target = float(log_probs[token_id].item())
    return int((log_probs > target).sum().item()) + 1


def _empty_score(candidate_ids: list[int]) -> dict[str, Any]:
    return {
        "status": "fail",
        "error": "empty prompt or candidate token ids",
        "token_count": len(candidate_ids),
        "candidate_token_ids": candidate_ids,
        "total_nll": None,
        "avg_nll": None,
        "first_token_rank": None,
        "first_token_logprob": None,
    }


def _prompt_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in score_rows:
        grouped.setdefault(str(row.get("prompt_term") or ""), []).append(row)
    rows: list[dict[str, Any]] = []
    for prompt_term, group in sorted(grouped.items()):
        expected = next((row for row in group if row.get("is_expected_candidate")), None)
        best = _best_candidate(group)
        expected_avg = float(expected.get("avg_nll")) if expected and expected.get("avg_nll") is not None else None
        best_avg = float(best.get("avg_nll")) if best.get("avg_nll") is not None else None
        rows.append(
            {
                "prompt_term": prompt_term,
                "prompt": group[0].get("prompt"),
                "expected_term": expected.get("candidate_term") if expected else None,
                "best_candidate_term": best.get("candidate_term"),
                "expected_is_best": bool(expected and best and expected.get("candidate_term") == best.get("candidate_term")),
                "expected_rank": _candidate_rank(group, str(expected.get("candidate_term") or "")) if expected else None,
                "expected_avg_nll": expected_avg,
                "best_avg_nll": best_avg,
                "expected_margin_vs_best": round(expected_avg - best_avg, 6)
                if expected_avg is not None and best_avg is not None
                else None,
                "candidate_count": len(group),
            }
        )
    return rows


def _best_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passing = [row for row in rows if row.get("status") == "pass"]
    if not passing:
        return {}
    return min(passing, key=lambda row: (float(row.get("avg_nll") or 999999.0), str(row.get("candidate_term") or "")))


def _candidate_rank(rows: list[dict[str, Any]], candidate: str) -> int | None:
    ranked = sorted(
        [row for row in rows if row.get("status") == "pass"],
        key=lambda row: (float(row.get("avg_nll") or 999999.0), str(row.get("candidate_term") or "")),
    )
    for index, row in enumerate(ranked, start=1):
        if str(row.get("candidate_term") or "") == candidate:
            return index
    return None


def _summary(prompt_rows: list[dict[str, Any]], score_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_best_count = sum(1 for row in prompt_rows if row.get("expected_is_best"))
    best_by_prompt = {
        str(row.get("prompt_term")): row.get("best_candidate_term")
        for row in prompt_rows
        if str(row.get("prompt_term") or "")
    }
    collapse_candidate = _collapse_candidate(best_by_prompt)
    return {
        "prompt_count": len(prompt_rows),
        "score_row_count": len(score_rows),
        "expected_best_count": expected_best_count,
        "expected_best_rate": round(expected_best_count / len(prompt_rows), 4) if prompt_rows else 0.0,
        "forced_choice_full_match": bool(prompt_rows) and expected_best_count == len(prompt_rows),
        "best_candidate_by_prompt": best_by_prompt,
        "collapse_candidate": collapse_candidate,
        "preference_collapse_observed": bool(collapse_candidate),
    }


def _collapse_candidate(best_by_prompt: dict[str, Any]) -> str:
    values = [str(value) for value in best_by_prompt.values() if value]
    return values[0] if values and len(set(values)) == 1 else ""


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_refresh_forced_choice"
    if summary.get("forced_choice_full_match"):
        return "required_term_pair_refresh_forced_choice_internal_match"
    if summary.get("preference_collapse_observed"):
        return "required_term_pair_refresh_forced_choice_preference_collapse"
    if int(summary.get("expected_best_count") or 0) > 0:
        return "required_term_pair_refresh_forced_choice_partial"
    return "required_term_pair_refresh_forced_choice_not_recovered"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The refresh forced-choice source is not scoreable."
        next_action = "repair checkpoint/tokenizer inputs before comparing candidates"
    elif summary.get("forced_choice_full_match"):
        reason = "Teacher-forced scoring prefers the expected fixed/loss continuation for every prompt."
        next_action = "treat the remaining free-generation miss as a decoding or rollout problem"
    elif summary.get("preference_collapse_observed"):
        reason = f"Teacher-forced scoring collapses both prompts to {summary.get('collapse_candidate')}."
        next_action = "avoid more simple corpus weighting and inspect objective/capacity or constrained decoding"
    elif int(summary.get("expected_best_count") or 0) > 0:
        reason = "Only one prompt prefers its expected continuation under teacher-forced scoring."
        next_action = "focus on the prompt whose expected candidate loses under scoring"
    else:
        reason = "Neither prompt prefers its expected continuation under teacher-forced scoring."
        next_action = "treat the checkpoint as internally misaligned before further generation sweeps"
    return {
        "model_quality_claim": "diagnostic_only" if status == "pass" else "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_REFRESH_FORCED_CHOICE_CSV_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_HTML_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_JSON_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_MARKDOWN_FILENAME",
    "PAIR_REFRESH_FORCED_CHOICE_TEXT_FILENAME",
    "build_model_capability_required_term_pair_refresh_forced_choice",
    "locate_pair_refresh_forced_choice_source",
    "read_json_report",
    "resolve_exit_code",
]
