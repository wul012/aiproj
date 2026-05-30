from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from minigpt.model_capability_required_term_pair_coexistence_refresh import PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


PAIR_FIRST_TOKEN_PREFERENCE_JSON_FILENAME = "model_capability_required_term_pair_first_token_preference.json"
PAIR_FIRST_TOKEN_PREFERENCE_CSV_FILENAME = "model_capability_required_term_pair_first_token_preference.csv"
PAIR_FIRST_TOKEN_PREFERENCE_TEXT_FILENAME = "model_capability_required_term_pair_first_token_preference.txt"
PAIR_FIRST_TOKEN_PREFERENCE_MARKDOWN_FILENAME = "model_capability_required_term_pair_first_token_preference.md"
PAIR_FIRST_TOKEN_PREFERENCE_HTML_FILENAME = "model_capability_required_term_pair_first_token_preference.html"

ScoreFunc = Callable[[dict[str, Any]], dict[str, Any]]


def locate_pair_coexistence_refresh(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / PAIR_COEXISTENCE_REFRESH_JSON_FILENAME
    return source


def read_json_report(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("pair coexistence refresh report must be a JSON object")
    return dict(payload)


def build_model_capability_required_term_pair_first_token_preference(
    refresh_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    top_k: int = 8,
    device: str = "cpu",
    generated_at: str | None = None,
    score_func: ScoreFunc | None = None,
) -> dict[str, Any]:
    training = as_dict(refresh_report.get("training"))
    replay = as_dict(refresh_report.get("replay_report"))
    checkpoint_path = str(training.get("checkpoint_path") or "")
    tokenizer_path = str(training.get("tokenizer_path") or "")
    issues = _input_issues(training, checkpoint_path, tokenizer_path)
    rows: list[dict[str, Any]] = []
    if not issues:
        scorer = score_func or _score_first_token
        for term in _terms(replay):
            row = _score_row(
                scorer,
                term,
                checkpoint_path=checkpoint_path,
                tokenizer_path=tokenizer_path,
                top_k=top_k,
                device=device,
                replay_rows=list_of_dicts(replay.get("case_rows")),
            )
            rows.append(row)
            if row.get("status") != "pass":
                issues.append(f"first-token score failed for {term.get('term')}: {row.get('error')}")
    summary = _summary(rows)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT required-term pair first-token preference",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_pair_coexistence_refresh": "" if source_path is None else str(source_path),
        "out_dir": str(out_dir),
        "settings": {
            "top_k": top_k,
            "device": device,
            "experiment_boundary": "score first-token logits for v533 fixed/loss refresh without retraining",
        },
        "training": {
            "checkpoint_path": checkpoint_path,
            "tokenizer_path": tokenizer_path,
            "checkpoint_exists": Path(checkpoint_path).is_file(),
            "tokenizer_exists": Path(tokenizer_path).is_file(),
        },
        "rows": rows,
        "summary": summary,
        "interpretation": _interpretation(status, summary),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _score_row(
    scorer: ScoreFunc,
    term: dict[str, Any],
    *,
    checkpoint_path: str,
    tokenizer_path: str,
    top_k: int,
    device: str,
    replay_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt = str(term.get("scaffold_prompt") or f"{term.get('term')}:")
    expected_term = str(term.get("term"))
    context = {
        "checkpoint_path": checkpoint_path,
        "tokenizer_path": tokenizer_path,
        "prompt": prompt,
        "expected_term": expected_term,
        "top_k": top_k,
        "device": device,
    }
    try:
        scored = scorer(context)
    except Exception as exc:  # pragma: no cover - defensive report boundary
        return {
            "status": "fail",
            "error": f"{type(exc).__name__}: {exc}",
            "term": expected_term,
            "prompt": prompt,
        }
    top_tokens = list_of_dicts(scored.get("top_tokens"))
    expected_rank = _expected_rank(top_tokens, scored.get("expected_token_id"))
    observed = _observed_replay_row(replay_rows, expected_term)
    return {
        "status": "pass",
        "term": expected_term,
        "prompt": prompt,
        "expected_first_text": scored.get("expected_first_text"),
        "expected_token_id": scored.get("expected_token_id"),
        "expected_rank": expected_rank,
        "expected_probability": scored.get("expected_probability"),
        "top_token_id": top_tokens[0].get("token_id") if top_tokens else None,
        "top_token_text": top_tokens[0].get("token_text") if top_tokens else "",
        "top_probability": top_tokens[0].get("probability") if top_tokens else None,
        "expected_is_top": expected_rank == 1,
        "whitespace_prefix_is_top": str(top_tokens[0].get("token_text") if top_tokens else "").isspace(),
        "answer_prefix_is_top": str(top_tokens[0].get("token_text") if top_tokens else "") == "a",
        "top_tokens": top_tokens,
        "observed_replay_continuation": observed.get("continuation_preview"),
        "observed_replay_profile": observed.get("profile_id"),
    }


def _score_first_token(context: dict[str, Any]) -> dict[str, Any]:
    import torch

    from minigpt.model import GPTConfig, MiniGPT
    from minigpt.tokenizer import load_tokenizer

    device = torch.device(str(context.get("device") or "cpu"))
    checkpoint = torch.load(context["checkpoint_path"], map_location=device, weights_only=False)
    tokenizer = load_tokenizer(context["tokenizer_path"])
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    prompt_ids = tokenizer.encode(str(context["prompt"]))
    if not prompt_ids:
        raise ValueError("prompt produced no token ids")
    idx = torch.tensor([prompt_ids[-model.config.block_size :]], dtype=torch.long, device=device)
    with torch.no_grad():
        logits, _ = model(idx)
        probs = torch.softmax(logits[0, -1], dim=-1)
    top_values, top_indices = torch.topk(probs, min(int(context["top_k"]), probs.numel()))
    expected_first = str(context["expected_term"])[0]
    expected_ids = tokenizer.encode(expected_first)
    expected_id = expected_ids[0] if expected_ids else None
    expected_probability = float(probs[expected_id].item()) if expected_id is not None else 0.0
    return {
        "expected_first_text": expected_first,
        "expected_token_id": expected_id,
        "expected_probability": round(expected_probability, 8),
        "top_tokens": [
            {
                "rank": index + 1,
                "token_id": int(token_id.item()),
                "token_text": tokenizer.decode([int(token_id.item())]),
                "probability": round(float(value.item()), 8),
            }
            for index, (value, token_id) in enumerate(zip(top_values, top_indices))
        ],
    }


def _terms(replay: dict[str, Any]) -> list[dict[str, Any]]:
    terms = list_of_dicts(replay.get("terms"))
    if terms:
        return terms
    rows = []
    seen: set[str] = set()
    for row in list_of_dicts(replay.get("case_rows")):
        term = str(row.get("term", "")).strip()
        if term and term not in seen:
            seen.add(term)
            rows.append({"term": term, "scaffold_prompt": row.get("prompt") or f"{term}:"})
    return rows


def _input_issues(training: dict[str, Any], checkpoint_path: str, tokenizer_path: str) -> list[str]:
    issues: list[str] = []
    if not training:
        issues.append("refresh report has no training object")
    if not checkpoint_path or not Path(checkpoint_path).is_file():
        issues.append("checkpoint_path is missing or does not exist")
    if not tokenizer_path or not Path(tokenizer_path).is_file():
        issues.append("tokenizer_path is missing or does not exist")
    return issues


def _expected_rank(top_tokens: list[dict[str, Any]], expected_token_id: Any) -> int | None:
    for row in top_tokens:
        if row.get("token_id") == expected_token_id:
            return int(row.get("rank") or 0)
    return None


def _observed_replay_row(rows: list[dict[str, Any]], term: str) -> dict[str, Any]:
    for row in rows:
        if row.get("term") == term and row.get("profile_id") == "default":
            return row
    for row in rows:
        if row.get("term") == term:
            return row
    return {}


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_top_count = sum(1 for row in rows if row.get("expected_is_top"))
    whitespace_prefix_top_count = sum(1 for row in rows if row.get("whitespace_prefix_is_top"))
    answer_prefix_top_count = sum(1 for row in rows if row.get("answer_prefix_is_top"))
    ranked_count = sum(1 for row in rows if row.get("expected_rank") is not None)
    return {
        "term_count": len(rows),
        "expected_top_count": expected_top_count,
        "whitespace_prefix_top_count": whitespace_prefix_top_count,
        "answer_prefix_top_count": answer_prefix_top_count,
        "ranked_count": ranked_count,
        "expected_all_top": bool(rows) and expected_top_count == len(rows),
        "answer_prefix_drift_observed": answer_prefix_top_count > 0,
        "max_expected_rank": max((int(row.get("expected_rank") or 0) for row in rows), default=0),
    }


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_pair_first_token_preference_diagnostic"
    if summary.get("expected_all_top"):
        return "pair_first_token_expected_terms_top_ranked"
    if summary.get("whitespace_prefix_top_count"):
        return "pair_first_token_whitespace_prefix_drift_confirmed"
    if summary.get("answer_prefix_drift_observed"):
        return "pair_first_token_answer_prefix_drift_confirmed"
    return "pair_first_token_expected_terms_not_top_ranked"


def _interpretation(status: str, summary: dict[str, Any]) -> dict[str, Any]:
    if status != "pass":
        reason = "The first-token diagnostic could not score the refresh checkpoint."
        next_action = "repair the diagnostic input before changing training"
    elif summary.get("expected_all_top"):
        reason = "The expected first tokens are already top ranked, so the failure is likely later in generation."
        next_action = "inspect second-token and continuation dynamics"
    elif summary.get("whitespace_prefix_top_count"):
        reason = "At least one prompt ranks whitespace above the expected first token, matching the leading-space replay collapse."
        next_action = "remove leading-space answer rows or add colon-immediate fixed/loss rows before retraining"
    elif summary.get("answer_prefix_drift_observed"):
        reason = "At least one prompt ranks 'a' above the expected first token, matching the ans-prefix replay collapse."
        next_action = "remove answer-shaped corpus rows or add prompt-only direct rows before retraining"
    else:
        reason = "Expected first tokens are not top ranked, but the dominant token is not the answer prefix."
        next_action = "inspect top-token alternatives before changing corpus"
    return {
        "model_quality_claim": "not_claimed",
        "reason": reason,
        "next_action": next_action,
    }


__all__ = [
    "PAIR_FIRST_TOKEN_PREFERENCE_CSV_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_HTML_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_JSON_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_MARKDOWN_FILENAME",
    "PAIR_FIRST_TOKEN_PREFERENCE_TEXT_FILENAME",
    "build_model_capability_required_term_pair_first_token_preference",
    "locate_pair_coexistence_refresh",
    "read_json_report",
    "resolve_exit_code",
]
