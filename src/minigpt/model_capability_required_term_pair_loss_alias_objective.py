from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc, _train_micro_checkpoint
from minigpt.model_capability_required_term_pair_continuation_span_heldout import (
    REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_JSON_FILENAME,
)
from minigpt.model_capability_required_term_pair_continuation_span_objective import refresh_training_artifact_status
from minigpt.model_capability_required_term_scaffold_probe import read_json_report
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_JSON_FILENAME = "model_capability_required_term_pair_loss_alias_objective.json"
REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_TEXT_FILENAME = "model_capability_required_term_pair_loss_alias_objective.txt"
REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_alias_objective.md"
REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_HTML_FILENAME = "model_capability_required_term_pair_loss_alias_objective.html"
REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_CORPUS_FILENAME = "required_term_pair_loss_alias_objective_corpus.txt"


def locate_model_capability_required_term_pair_loss_alias_objective_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_CONTINUATION_SPAN_HELDOUT_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_loss_alias_objective(
    heldout_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    repeat: int = 220,
    bridge_repeat: int = 4,
    max_iters: int = 900,
    eval_iters: int = 2,
    batch_size: int = 16,
    block_size: int = 16,
    n_layer: int = 1,
    n_head: int = 1,
    n_embd: int = 64,
    learning_rate: float = 0.02,
    max_new_tokens: int = 12,
    temperature: float = 0.2,
    top_k: int | None = 1,
    generation_seed: int = 514,
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    cases = select_loss_alias_objective_cases(heldout_report)
    issues = _input_issues(heldout_report, cases)
    corpus_text = build_loss_alias_objective_corpus(cases, repeat=repeat, bridge_repeat=bridge_repeat)
    corpus_path = root / REQUIRED_TERM_PAIR_LOSS_ALIAS_OBJECTIVE_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")

    training: dict[str, Any] = {"status": "skipped", "reason": "input issues prevented training"}
    if not issues:
        training = _train_micro_checkpoint(
            {
                "corpus_path": str(corpus_path),
                "train_dir": str(root / "loss-alias-run"),
                "max_iters": max_iters,
                "eval_iters": eval_iters,
                "batch_size": batch_size,
                "block_size": block_size,
                "n_layer": n_layer,
                "n_head": n_head,
                "n_embd": n_embd,
                "learning_rate": learning_rate,
                "seed": generation_seed,
                "device": device,
                "sample_prompt": _sample_prompt(cases),
            },
            train_func,
        )
        if training.get("status") != "pass":
            training = refresh_training_artifact_status(training)
        if training.get("status") != "pass":
            issues.append("loss-alias objective training command did not complete successfully")

    generation_rows = (
        _generation_rows(
            cases,
            training,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=generation_seed,
            device=device,
            generate_func=generate_func,
        )
        if not issues
        else []
    )
    case_rows = summarize_loss_alias_case_rows(cases, generation_rows)
    summary = summarize_loss_alias_objective(cases, generation_rows, case_rows, training)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias objective",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_continuation_span_heldout": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "target_term": "loss",
            "repeat": max(1, int(repeat)),
            "bridge_repeat": max(0, int(bridge_repeat)),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "generation_seed": generation_seed,
            "device": device,
            "experiment_boundary": "train only the v513 missing loss alias prompts before expanding model size",
        },
        "corpus": {
            "path": str(corpus_path),
            "char_count": len(corpus_text),
            "line_count": len(corpus_text.splitlines()),
        },
        "training": training,
        "cases": cases,
        "generation_rows": generation_rows,
        "case_rows": case_rows,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_loss_alias_objective_cases(heldout_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for case in list_of_dicts(heldout_report.get("case_rows")):
        expected = str(case.get("expected_term") or "").strip()
        prompt = str(case.get("prompt") or "").strip()
        case_id = str(case.get("case_id") or "").strip()
        if expected.casefold() != "loss" or not prompt or not case_id:
            continue
        rows.setdefault(
            case_id,
            {
                "case_id": case_id,
                "case_type": str(case.get("case_type") or "unknown"),
                "alias_group": str(case.get("alias_group") or "unknown"),
                "prompt": prompt,
                "expected_term": expected,
                "source_run_count": int(case.get("run_count") or 0),
                "source_hit_count": int(case.get("hit_count") or 0),
                "source_hit_rate": float(case.get("hit_rate") or 0.0),
            },
        )
    order = {"source": 0, "heldout": 1}
    return sorted(rows.values(), key=lambda row: (order.get(str(row.get("case_type")), 9), str(row.get("case_id"))))


def build_loss_alias_objective_corpus(cases: list[dict[str, Any]], *, repeat: int, bridge_repeat: int) -> str:
    repeat_count = max(1, int(repeat))
    bridge_count = max(0, int(bridge_repeat))
    lines = [
        "MiniGPT required-term pair loss-alias objective corpus.",
        "Each alias prompt maps to the exact required term loss.",
    ]
    for _ in range(repeat_count):
        for case in cases:
            prompt = str(case.get("prompt") or "")
            term = str(case.get("expected_term") or "loss")
            lines.append(f"{prompt}{term}")
            lines.append(f"{prompt} {term}")
            lines.append(f"alias {prompt} means {term}")
            lines.append(f"continue loss alias {prompt}{term}")
        prompts = [str(case.get("prompt") or "") for case in cases if case.get("prompt")]
        for _bridge in range(bridge_count):
            if prompts:
                lines.append("loss alias bridge " + " ".join(f"{prompt}loss" for prompt in prompts))
    return "\n".join(lines) + "\n"


def summarize_loss_alias_case_rows(cases: list[dict[str, Any]], generation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case.get("case_id") or "")
        group = [row for row in generation_rows if row.get("case_id") == case_id]
        hit_count = sum(1 for row in group if row.get("continuation_hit"))
        rows.append(
            {
                **case,
                "generation_count": len(group),
                "generation_hit_count": hit_count,
                "generation_hit_rate": round(hit_count / len(group), 4) if group else 0.0,
            }
        )
    return rows


def summarize_loss_alias_objective(
    cases: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> dict[str, Any]:
    source_rows = [row for row in case_rows if row.get("case_type") == "source"]
    heldout_rows = [row for row in case_rows if row.get("case_type") == "heldout"]
    hit_cases = [row for row in case_rows if int(row.get("generation_hit_count") or 0) > 0]
    heldout_hits = [row for row in heldout_rows if int(row.get("generation_hit_count") or 0) > 0]
    source_hits = [row for row in source_rows if int(row.get("generation_hit_count") or 0) > 0]
    return {
        "loss_alias_decision": _loss_alias_decision(training, case_rows, source_hits, heldout_hits),
        "case_count": len(cases),
        "source_case_count": len(source_rows),
        "heldout_case_count": len(heldout_rows),
        "generation_count": len(generation_rows),
        "generation_hit_case_count": len(hit_cases),
        "source_loss_hit": bool(source_hits),
        "heldout_loss_alias_hit_case_count": len(heldout_hits),
        "heldout_loss_alias_full_coverage": bool(heldout_rows) and len(heldout_hits) == len(heldout_rows),
        "all_loss_alias_full_coverage": bool(case_rows) and len(hit_cases) == len(case_rows),
        "training_status": training.get("status"),
        "training_returncode": training.get("returncode"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
        "tokenizer_exists": bool(training.get("tokenizer_exists")),
        "metrics_exists": bool(training.get("metrics_exists")),
        "train_config_exists": bool(training.get("train_config_exists")),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _input_issues(heldout_report: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not heldout_report:
        issues.append("source continuation-span heldout report is missing or invalid")
    if heldout_report and heldout_report.get("status") != "pass":
        issues.append("source continuation-span heldout report is not pass")
    if heldout_report and as_dict(heldout_report.get("summary")).get("heldout_hit_term_count") is None:
        issues.append("source continuation-span heldout report does not include alias matrix term coverage")
    if not cases:
        issues.append("source continuation-span heldout report has no loss alias cases")
    return issues


def _generation_rows(
    cases: list[dict[str, Any]],
    training: dict[str, Any],
    *,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    if training.get("status") != "pass":
        return []
    return [
        _generation_row(
            case,
            training,
            index=index,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            generation_seed=generation_seed,
            device=device,
            generate_func=generate_func,
        )
        for index, case in enumerate(cases)
    ]


def _generation_row(
    case: dict[str, Any],
    training: dict[str, Any],
    *,
    index: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    generation_seed: int,
    device: str,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    prompt = str(case.get("prompt") or "")
    expected = str(case.get("expected_term") or "loss")
    request = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "seed": generation_seed + index,
        "checkpoint_path": training.get("checkpoint_path"),
        "tokenizer_path": training.get("tokenizer_path"),
        "device": device,
    }
    response = _generate(request, generate_func)
    generated = str(response.get("generated") or "")
    continuation = str(response.get("continuation") or "")
    if not continuation and generated.startswith(prompt):
        continuation = generated[len(prompt) :]
    return {
        **case,
        "generation_seed": request["seed"],
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "generated": generated,
        "continuation": continuation,
        "continuation_hit": expected.casefold() in continuation.casefold(),
        "continuation_preview": _preview(continuation),
    }


def _generate(request: dict[str, Any], generate_func: GenerateFunc | None) -> dict[str, Any]:
    if generate_func is not None:
        return generate_func(request)
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    generator = MiniGPTGenerator(
        request["checkpoint_path"],
        request["tokenizer_path"],
        device=str(request.get("device") or "cpu"),
    )
    return generator.generate(
        GenerationRequest(
            prompt=str(request["prompt"]),
            max_new_tokens=int(request["max_new_tokens"]),
            temperature=float(request["temperature"]),
            top_k=request.get("top_k"),
            seed=int(request["seed"]),
        )
    ).to_dict()


def _loss_alias_decision(
    training: dict[str, Any],
    case_rows: list[dict[str, Any]],
    source_hits: list[dict[str, Any]],
    heldout_hits: list[dict[str, Any]],
) -> str:
    heldout_rows = [row for row in case_rows if row.get("case_type") == "heldout"]
    if training.get("status") != "pass":
        return "loss_alias_training_failed"
    if not case_rows:
        return "loss_alias_cases_missing"
    if heldout_rows and len(heldout_hits) == len(heldout_rows):
        return "loss_alias_heldout_full_hit"
    if heldout_hits:
        return "loss_alias_heldout_partial_hit"
    if source_hits:
        return "loss_alias_source_prompt_only"
    return "loss_alias_no_generation_signal"


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_objective"
    if summary.get("heldout_loss_alias_full_coverage"):
        return "required_term_pair_loss_alias_continuation_full_hit"
    if int(summary.get("heldout_loss_alias_hit_case_count") or 0) > 0:
        return "required_term_pair_loss_alias_continuation_partial_hit"
    if summary.get("source_loss_hit"):
        return "required_term_pair_loss_alias_source_only"
    return "required_term_pair_loss_alias_no_gain"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("heldout_loss_alias_full_coverage"):
        return "tiny_loss_alias_heldout_full_signal"
    if int(summary.get("heldout_loss_alias_hit_case_count") or 0) > 0:
        return "tiny_loss_alias_heldout_partial_signal"
    if summary.get("source_loss_hit"):
        return "tiny_loss_alias_source_prompt_signal_only"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The loss-alias objective could not be run cleanly."
    if summary.get("heldout_loss_alias_full_coverage"):
        return "The tiny loss-alias run emitted loss for every held-out loss alias prompt."
    if int(summary.get("heldout_loss_alias_hit_case_count") or 0) > 0:
        return "The tiny loss-alias run recovered at least one held-out loss alias prompt."
    if summary.get("source_loss_hit"):
        return "The tiny loss-alias run recovered the source loss prompt but not held-out loss aliases."
    return "The tiny loss-alias run completed, but loss aliases still did not emit the required term."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair loss-alias objective inputs before changing model capacity"
    if summary.get("heldout_loss_alias_full_coverage"):
        return "repeat the loss-alias objective across seeds before promoting the recovery"
    if int(summary.get("heldout_loss_alias_hit_case_count") or 0) > 0:
        return "stabilize the partial loss-alias signal across another seed"
    return "adjust alias corpus shape before larger model or data scaling"


def _sample_prompt(cases: list[dict[str, Any]]) -> str:
    for case in cases:
        prompt = str(case.get("prompt") or "")
        if prompt:
            return prompt
    return "loss:"


def _preview(value: Any, limit: int = 90) -> str:
    text = str(value or "").replace("\n", "\\n").replace("\t", "\\t")
    return text if len(text) <= limit else text[: limit - 1] + "..."
