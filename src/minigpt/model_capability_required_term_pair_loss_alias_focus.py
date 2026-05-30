from __future__ import annotations

from pathlib import Path
from typing import Any

from minigpt.model_capability_required_term_micro_training import GenerateFunc, TrainFunc, _train_micro_checkpoint
from minigpt.model_capability_required_term_pair_continuation_span_objective import refresh_training_artifact_status
from minigpt.model_capability_required_term_pair_loss_alias_stability import (
    REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME,
    read_json_report,
)
from minigpt.model_capability_required_term_pair_loss_alias_focus_components import (
    case_from_row as _case_from_row,
    case_lines as _case_lines,
    clean_seeds as _clean_seeds,
    focus_decision as _focus_decision,
    focus_metric_decision as _focus_metric_decision,
    focus_surface_decision as _focus_surface_decision,
    preview as _preview,
    sorted_cases as _sorted_cases,
)
from minigpt.model_capability_required_term_pair_loss_alias_metrics import required_term_hit_metrics
from minigpt.report_utils import as_dict, list_of_dicts, utc_now


REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_JSON_FILENAME = "model_capability_required_term_pair_loss_alias_focus.json"
REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_TEXT_FILENAME = "model_capability_required_term_pair_loss_alias_focus.txt"
REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_MARKDOWN_FILENAME = "model_capability_required_term_pair_loss_alias_focus.md"
REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_HTML_FILENAME = "model_capability_required_term_pair_loss_alias_focus.html"
REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_CORPUS_FILENAME = "required_term_pair_loss_alias_focus_corpus.txt"


def locate_model_capability_required_term_pair_loss_alias_focus_source(path: str | Path) -> Path:
    source = Path(path)
    if source.is_dir():
        source = source / REQUIRED_TERM_PAIR_LOSS_ALIAS_STABILITY_JSON_FILENAME
    return source


def build_model_capability_required_term_pair_loss_alias_focus(
    stability_report: dict[str, Any],
    *,
    out_dir: str | Path,
    source_path: str | Path | None = None,
    seeds: tuple[int, ...] | list[int] = (515,),
    base_repeat: int = 180,
    focus_repeat: int = 180,
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
    device: str = "cpu",
    generated_at: str | None = None,
    train_func: TrainFunc | None = None,
    generate_func: GenerateFunc | None = None,
) -> dict[str, Any]:
    root = Path(out_dir)
    clean_seeds = _clean_seeds(seeds)
    support_cases = select_loss_alias_support_cases(stability_report)
    focus_cases = select_loss_alias_focus_cases(stability_report)
    issues = _input_issues(stability_report, clean_seeds, support_cases, focus_cases)
    seed_reports: list[dict[str, Any]] = []
    if not issues:
        for index, seed in enumerate(clean_seeds):
            seed_reports.append(
                _run_focus_seed(
                    support_cases,
                    focus_cases,
                    out_dir=root / "seed-runs" / f"seed-{seed}",
                    seed=seed,
                    base_repeat=base_repeat,
                    focus_repeat=focus_repeat,
                    bridge_repeat=bridge_repeat,
                    max_iters=max_iters,
                    eval_iters=eval_iters,
                    batch_size=batch_size,
                    block_size=block_size,
                    n_layer=n_layer,
                    n_head=n_head,
                    n_embd=n_embd,
                    learning_rate=learning_rate,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    device=device,
                    train_func=train_func,
                    generate_func=generate_func,
                )
            )
            if seed_reports[index].get("status") != "pass":
                issues.append(f"seed {seed} loss-alias focus run did not pass structurally")

    seed_rows = summarize_loss_alias_focus_seed_rows(clean_seeds, seed_reports)
    summary = summarize_loss_alias_focus(seed_rows, support_cases, focus_cases)
    status = "pass" if not issues else "fail"
    return {
        "schema_version": 1,
        "title": "MiniGPT model capability required-term pair loss-alias focus",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": _decision(status, summary),
        "failed_count": len(issues),
        "issues": issues,
        "source_required_term_pair_loss_alias_stability": str(source_path) if source_path else None,
        "out_dir": str(root),
        "settings": {
            "seeds": clean_seeds,
            "base_repeat": max(1, int(base_repeat)),
            "focus_repeat": max(1, int(focus_repeat)),
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
            "device": device,
            "experiment_boundary": "boost only the loss alias rows missed by v515 before recombining fixed and loss",
        },
        "support_cases": support_cases,
        "focus_cases": focus_cases,
        "seed_rows": seed_rows,
        "seed_reports": seed_reports,
        "summary": summary,
        "interpretation": {
            "model_quality_claim": _model_quality_claim(summary),
            "reason": _reason(status, summary),
            "next_action": _next_action(status, summary),
        },
    }


def select_loss_alias_support_cases(stability_report: dict[str, Any]) -> list[dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for report in list_of_dicts(stability_report.get("seed_reports")):
        for row in list_of_dicts(report.get("case_rows")):
            case = _case_from_row(row)
            if case:
                cases.setdefault(str(case["case_id"]), case)
    return _sorted_cases(cases.values())


def select_loss_alias_focus_cases(stability_report: dict[str, Any]) -> list[dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    for report in list_of_dicts(stability_report.get("seed_reports")):
        seed = as_dict(report.get("settings")).get("generation_seed")
        for row in list_of_dicts(report.get("case_rows")):
            if int(row.get("generation_hit_count") or 0) > 0:
                continue
            case = _case_from_row(row)
            if not case:
                continue
            existing = cases.setdefault(str(case["case_id"]), {**case, "missed_seed_count": 0, "missed_seeds": []})
            existing["missed_seed_count"] = int(existing.get("missed_seed_count") or 0) + 1
            existing.setdefault("missed_seeds", []).append(seed)
    return _sorted_cases(cases.values())


def build_loss_alias_focus_corpus(
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
    *,
    base_repeat: int,
    focus_repeat: int,
    bridge_repeat: int,
) -> str:
    lines = [
        "MiniGPT required-term pair loss-alias focus corpus.",
        "All support prompts map to loss, with extra density for v515 missed rows.",
    ]
    for _ in range(max(1, int(base_repeat))):
        for case in support_cases:
            lines.extend(_case_lines(case, "support"))
    for _ in range(max(1, int(focus_repeat))):
        for case in focus_cases:
            lines.extend(_case_lines(case, "focus"))
    prompts = [str(case.get("prompt") or "") for case in support_cases if case.get("prompt")]
    for _ in range(max(0, int(bridge_repeat))):
        if prompts:
            lines.append("focused loss alias bridge " + " ".join(f"{prompt}loss" for prompt in prompts))
    return "\n".join(lines) + "\n"


def summarize_loss_alias_focus_seed_rows(seeds: list[int], reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed, report in zip(seeds, reports):
        summary = as_dict(report.get("summary"))
        rows.append(
            {
                "seed": seed,
                "status": report.get("status"),
                "focus_hit_case_count": summary.get("focus_hit_case_count"),
                "focus_case_count": summary.get("focus_case_count"),
                "support_hit_case_count": summary.get("support_hit_case_count"),
                "support_case_count": summary.get("support_case_count"),
                "focus_full_coverage": summary.get("focus_full_coverage"),
                "support_full_coverage": summary.get("support_full_coverage"),
                "focus_normalized_hit_case_count": summary.get("focus_normalized_hit_case_count"),
                "support_normalized_hit_case_count": summary.get("support_normalized_hit_case_count"),
                "focus_normalized_full_coverage": summary.get("focus_normalized_full_coverage"),
                "support_normalized_full_coverage": summary.get("support_normalized_full_coverage"),
                "focus_newline_cleanup_hit_case_count": summary.get("focus_newline_cleanup_hit_case_count"),
                "support_newline_cleanup_hit_case_count": summary.get("support_newline_cleanup_hit_case_count"),
                "focus_newline_cleanup_full_coverage": summary.get("focus_newline_cleanup_full_coverage"),
                "support_newline_cleanup_full_coverage": summary.get("support_newline_cleanup_full_coverage"),
                "newline_cleanup_gain_count": summary.get("newline_cleanup_gain_count"),
                "normalization_gain_count": summary.get("normalization_gain_count"),
                "checkpoint_exists": summary.get("checkpoint_exists"),
                "out_dir": report.get("out_dir"),
            }
        )
    return rows


def summarize_loss_alias_focus(
    seed_rows: list[dict[str, Any]],
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
) -> dict[str, Any]:
    seed_count = len(seed_rows)
    pass_count = sum(1 for row in seed_rows if row.get("status") == "pass")
    focus_full_count = sum(1 for row in seed_rows if row.get("focus_full_coverage"))
    support_full_count = sum(1 for row in seed_rows if row.get("support_full_coverage"))
    focus_normalized_full_count = sum(1 for row in seed_rows if row.get("focus_normalized_full_coverage"))
    support_normalized_full_count = sum(1 for row in seed_rows if row.get("support_normalized_full_coverage"))
    focus_newline_cleanup_full_count = sum(1 for row in seed_rows if row.get("focus_newline_cleanup_full_coverage"))
    support_newline_cleanup_full_count = sum(1 for row in seed_rows if row.get("support_newline_cleanup_full_coverage"))
    newline_cleanup_gain_count = sum(int(row.get("newline_cleanup_gain_count") or 0) for row in seed_rows)
    normalization_gain_count = sum(int(row.get("normalization_gain_count") or 0) for row in seed_rows)
    strict_decision = _focus_decision(seed_count, pass_count, focus_full_count, support_full_count)
    return {
        "loss_alias_focus_decision": strict_decision,
        "loss_alias_focus_surface_decision": _focus_surface_decision(
            strict_decision,
            seed_count,
            focus_newline_cleanup_full_count,
            support_newline_cleanup_full_count,
            newline_cleanup_gain_count,
        ),
        "loss_alias_focus_metric_decision": _focus_metric_decision(
            strict_decision,
            seed_count,
            focus_normalized_full_count,
            support_normalized_full_count,
            normalization_gain_count,
        ),
        "seed_count": seed_count,
        "pass_count": pass_count,
        "support_case_count": len(support_cases),
        "focus_case_count": len(focus_cases),
        "focus_full_seed_count": focus_full_count,
        "support_full_seed_count": support_full_count,
        "stable_focus_full_coverage": seed_count > 0 and focus_full_count == seed_count,
        "stable_support_full_coverage": seed_count > 0 and support_full_count == seed_count,
        "focus_normalized_full_seed_count": focus_normalized_full_count,
        "support_normalized_full_seed_count": support_normalized_full_count,
        "stable_focus_normalized_full_coverage": seed_count > 0 and focus_normalized_full_count == seed_count,
        "stable_support_normalized_full_coverage": seed_count > 0 and support_normalized_full_count == seed_count,
        "focus_newline_cleanup_full_seed_count": focus_newline_cleanup_full_count,
        "support_newline_cleanup_full_seed_count": support_newline_cleanup_full_count,
        "stable_focus_newline_cleanup_full_coverage": seed_count > 0 and focus_newline_cleanup_full_count == seed_count,
        "stable_support_newline_cleanup_full_coverage": seed_count > 0 and support_newline_cleanup_full_count == seed_count,
        "newline_cleanup_gain_count": newline_cleanup_gain_count,
        "normalization_gain_count": normalization_gain_count,
        "checkpoint_seed_count": sum(1 for row in seed_rows if row.get("checkpoint_exists")),
    }


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _run_focus_seed(
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
    *,
    out_dir: Path,
    seed: int,
    base_repeat: int,
    focus_repeat: int,
    bridge_repeat: int,
    max_iters: int,
    eval_iters: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    learning_rate: float,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
    train_func: TrainFunc | None,
    generate_func: GenerateFunc | None,
) -> dict[str, Any]:
    corpus_text = build_loss_alias_focus_corpus(
        support_cases,
        focus_cases,
        base_repeat=base_repeat,
        focus_repeat=focus_repeat,
        bridge_repeat=bridge_repeat,
    )
    corpus_path = out_dir / REQUIRED_TERM_PAIR_LOSS_ALIAS_FOCUS_CORPUS_FILENAME
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding="utf-8")
    training = _train_micro_checkpoint(
        {
            "corpus_path": str(corpus_path),
            "train_dir": str(out_dir / "loss-alias-focus-run"),
            "max_iters": max_iters,
            "eval_iters": eval_iters,
            "batch_size": batch_size,
            "block_size": block_size,
            "n_layer": n_layer,
            "n_head": n_head,
            "n_embd": n_embd,
            "learning_rate": learning_rate,
            "seed": seed,
            "device": device,
            "sample_prompt": str(focus_cases[0].get("prompt") if focus_cases else "loss:"),
        },
        train_func,
    )
    if training.get("status") != "pass":
        training = refresh_training_artifact_status(training)
    generation_rows = _generation_rows(support_cases, focus_cases, training, seed, max_new_tokens, temperature, top_k, device, generate_func)
    summary = _seed_summary(support_cases, focus_cases, generation_rows, training)
    status = "pass" if training.get("status") == "pass" else "fail"
    return {
        "schema_version": 1,
        "status": status,
        "out_dir": str(out_dir),
        "settings": {"generation_seed": seed},
        "corpus": {"path": str(corpus_path), "char_count": len(corpus_text), "line_count": len(corpus_text.splitlines())},
        "training": training,
        "generation_rows": generation_rows,
        "summary": summary,
    }


def _generation_rows(
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
    training: dict[str, Any],
    seed: int,
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: str,
    generate_func: GenerateFunc | None,
) -> list[dict[str, Any]]:
    if training.get("status") != "pass":
        return []
    focus_ids = {str(case.get("case_id")) for case in focus_cases}
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(support_cases):
        prompt = str(case.get("prompt") or "")
        expected = str(case.get("expected_term") or "loss")
        request = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "seed": seed + index,
            "checkpoint_path": training.get("checkpoint_path"),
            "tokenizer_path": training.get("tokenizer_path"),
            "device": device,
        }
        response = _generate(request, generate_func)
        continuation = str(response.get("continuation") or "")
        generated = str(response.get("generated") or "")
        if not continuation and generated.startswith(prompt):
            continuation = generated[len(prompt) :]
        strict_hit = expected.casefold() in continuation.casefold()
        hit_metrics = required_term_hit_metrics(continuation, expected, strict_hit=strict_hit)
        rows.append(
            {
                **case,
                "is_focus_case": str(case.get("case_id")) in focus_ids,
                "generation_seed": request["seed"],
                "generated": generated,
                "continuation": continuation,
                "continuation_hit": strict_hit,
                "strict_hit": hit_metrics["strict_hit"],
                "newline_cleanup_hit": hit_metrics["newline_cleanup_hit"],
                "newline_cleanup_gain": hit_metrics["newline_cleanup_gain"],
                "newline_cleanup_continuation_preview": _preview(hit_metrics["newline_cleanup_continuation"]),
                "normalized_hit": hit_metrics["normalized_hit"],
                "normalization_gain": hit_metrics["normalization_gain"],
                "normalized_continuation_preview": _preview(hit_metrics["normalized_continuation"]),
                "continuation_preview": _preview(continuation),
            }
        )
    return rows


def _seed_summary(
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
    generation_rows: list[dict[str, Any]],
    training: dict[str, Any],
) -> dict[str, Any]:
    support_hits = sum(1 for row in generation_rows if row.get("continuation_hit"))
    focus_hits = sum(1 for row in generation_rows if row.get("is_focus_case") and row.get("continuation_hit"))
    support_newline_cleanup_hits = sum(1 for row in generation_rows if row.get("newline_cleanup_hit"))
    focus_newline_cleanup_hits = sum(1 for row in generation_rows if row.get("is_focus_case") and row.get("newline_cleanup_hit"))
    support_normalized_hits = sum(1 for row in generation_rows if row.get("normalized_hit"))
    focus_normalized_hits = sum(1 for row in generation_rows if row.get("is_focus_case") and row.get("normalized_hit"))
    return {
        "support_case_count": len(support_cases),
        "focus_case_count": len(focus_cases),
        "support_hit_case_count": support_hits,
        "focus_hit_case_count": focus_hits,
        "support_full_coverage": bool(support_cases) and support_hits == len(support_cases),
        "focus_full_coverage": bool(focus_cases) and focus_hits == len(focus_cases),
        "support_newline_cleanup_hit_case_count": support_newline_cleanup_hits,
        "focus_newline_cleanup_hit_case_count": focus_newline_cleanup_hits,
        "support_newline_cleanup_full_coverage": bool(support_cases) and support_newline_cleanup_hits == len(support_cases),
        "focus_newline_cleanup_full_coverage": bool(focus_cases) and focus_newline_cleanup_hits == len(focus_cases),
        "newline_cleanup_gain_count": sum(1 for row in generation_rows if row.get("newline_cleanup_gain")),
        "support_normalized_hit_case_count": support_normalized_hits,
        "focus_normalized_hit_case_count": focus_normalized_hits,
        "support_normalized_full_coverage": bool(support_cases) and support_normalized_hits == len(support_cases),
        "focus_normalized_full_coverage": bool(focus_cases) and focus_normalized_hits == len(focus_cases),
        "normalization_gain_count": sum(1 for row in generation_rows if row.get("normalization_gain")),
        "training_status": training.get("status"),
        "checkpoint_exists": bool(training.get("checkpoint_exists")),
    }


def _generate(request: dict[str, Any], generate_func: GenerateFunc | None) -> dict[str, Any]:
    if generate_func is not None:
        return generate_func(request)
    from minigpt.server_contracts import GenerationRequest
    from minigpt.server_generator import MiniGPTGenerator

    return MiniGPTGenerator(request["checkpoint_path"], request["tokenizer_path"], device=str(request.get("device") or "cpu")).generate(
        GenerationRequest(
            prompt=str(request["prompt"]),
            max_new_tokens=int(request["max_new_tokens"]),
            temperature=float(request["temperature"]),
            top_k=request.get("top_k"),
            seed=int(request["seed"]),
        )
    ).to_dict()


def _input_issues(
    stability_report: dict[str, Any],
    seeds: list[int],
    support_cases: list[dict[str, Any]],
    focus_cases: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not stability_report:
        issues.append("source loss-alias stability report is missing or invalid")
    if stability_report and stability_report.get("status") != "pass":
        issues.append("source loss-alias stability report is not pass")
    if not seeds:
        issues.append("loss-alias focus seed list is empty")
    if not support_cases:
        issues.append("source loss-alias stability report has no support cases")
    if not focus_cases:
        issues.append("source loss-alias stability report has no missed focus cases")
    return issues


def _decision(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "fix_required_term_pair_loss_alias_focus"
    if summary.get("stable_support_full_coverage"):
        return "required_term_pair_loss_alias_focus_support_full_hit"
    if summary.get("stable_focus_full_coverage"):
        return "required_term_pair_loss_alias_focus_repaired"
    if int(summary.get("focus_full_seed_count") or 0) > 0:
        return "required_term_pair_loss_alias_focus_seed_dependent"
    if summary.get("stable_support_newline_cleanup_full_coverage"):
        return "required_term_pair_loss_alias_focus_newline_cleanup_support_signal"
    if summary.get("stable_focus_newline_cleanup_full_coverage"):
        return "required_term_pair_loss_alias_focus_newline_cleanup_focus_signal"
    if int(summary.get("newline_cleanup_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_focus_newline_cleanup_partial_signal"
    if summary.get("stable_support_normalized_full_coverage"):
        return "required_term_pair_loss_alias_focus_normalized_support_signal"
    if summary.get("stable_focus_normalized_full_coverage"):
        return "required_term_pair_loss_alias_focus_normalized_focus_signal"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "required_term_pair_loss_alias_focus_normalized_partial_signal"
    return "required_term_pair_loss_alias_focus_no_repair"


def _model_quality_claim(summary: dict[str, Any]) -> str:
    if summary.get("stable_support_full_coverage"):
        return "tiny_loss_alias_focused_support_full_signal"
    if summary.get("stable_focus_full_coverage"):
        return "tiny_loss_alias_focused_repair_signal"
    if int(summary.get("focus_full_seed_count") or 0) > 0:
        return "tiny_loss_alias_focused_seed_dependent_signal"
    if summary.get("stable_support_newline_cleanup_full_coverage"):
        return "tiny_loss_alias_focused_newline_cleanup_support_signal"
    if summary.get("stable_focus_newline_cleanup_full_coverage"):
        return "tiny_loss_alias_focused_newline_cleanup_repair_signal"
    if int(summary.get("newline_cleanup_gain_count") or 0) > 0:
        return "tiny_loss_alias_focused_newline_cleanup_partial_signal"
    if summary.get("stable_support_normalized_full_coverage"):
        return "tiny_loss_alias_focused_normalized_support_signal"
    if summary.get("stable_focus_normalized_full_coverage"):
        return "tiny_loss_alias_focused_normalized_repair_signal"
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "tiny_loss_alias_focused_normalized_partial_signal"
    return "not_claimed"


def _reason(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "The focused loss-alias repair could not be run cleanly."
    if summary.get("stable_support_full_coverage"):
        return "The focused corpus recovered every support loss alias case for every tested seed."
    if summary.get("stable_focus_full_coverage"):
        return "The focused corpus repaired every previously missed loss alias row for every tested seed."
    if int(summary.get("focus_full_seed_count") or 0) > 0:
        return "The focused corpus repaired missed rows for at least one seed, but not stably."
    if summary.get("stable_support_newline_cleanup_full_coverage"):
        return "Strict hits still failed, but every support loss alias appears after removing only newline separators."
    if summary.get("stable_focus_newline_cleanup_full_coverage"):
        return "Strict hits still failed, but every focused missed row appears after removing only newline separators."
    if int(summary.get("newline_cleanup_gain_count") or 0) > 0:
        return "Strict hits still failed, but newline cleanup reveals at least one line-broken required term."
    if summary.get("stable_support_normalized_full_coverage"):
        return "Strict hits still failed, but every support loss alias contains the required term after normalization."
    if summary.get("stable_focus_normalized_full_coverage"):
        return "Strict hits still failed, but every focused missed row contains the required term after normalization."
    if int(summary.get("normalization_gain_count") or 0) > 0:
        return "Strict hits still failed, but normalization reveals at least one formatting-separated required term."
    return "The focused corpus completed but did not repair the missed loss alias rows."


def _next_action(status: str, summary: dict[str, Any]) -> str:
    if status != "pass":
        return "repair focused loss-alias inputs before another training run"
    if summary.get("stable_support_full_coverage"):
        return "add fixed aliases back and test pair coexistence"
    if summary.get("stable_focus_full_coverage"):
        return "repeat focused repair with another seed before pair recombination"
    if summary.get("stable_support_newline_cleanup_full_coverage") or summary.get("stable_focus_newline_cleanup_full_coverage"):
        return "treat line-broken required-term output as a decode-surface issue before changing training again"
    if summary.get("stable_support_normalized_full_coverage") or summary.get("stable_focus_normalized_full_coverage"):
        return "carry strict and normalized hit metrics together before another training change"
    return "inspect focused corpus ordering and generation previews before adding capacity"
